import ast
import difflib
import hashlib
import json
import os
import re
import time
from datetime import date

import requests
from google import genai

MAX_PLUGIN_SIZE = 20_000
REQUEST_TIMEOUT = 4
MAX_SEARCH_RESULTS = 3
AI_SECURITY_MODELS = [
    "gemini-3.1-flash-lite-preview",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash-lite-preview-09-2025",
    "gemini-2.5-flash",
]
MAX_DAILY_PLUGIN_REVIEWS = 25
LIMITS_FILE = os.path.join(os.path.dirname(__file__), ".plugin_review_limits.json")
FORBIDDEN_IMPORT_ROOTS = {
    "subprocess",
    "shutil",
    "socket",
    "ctypes",
    "multiprocessing",
    "signal",
}
FORBIDDEN_IMPORT_EXACT = set()
FORBIDDEN_CALLS = {
    "eval",
    "exec",
    "compile",
    "__import__",
}
FORBIDDEN_ATTR_CALLS = {
    "os.system",
    "os.popen",
    "os.remove",
    "os.unlink",
    "os.rmdir",
    "os.removedirs",
    "os.rename",
    "os.replace",
    "os.chmod",
    "os.chown",
    "pathlib.Path.unlink",
    "pathlib.Path.rmdir",
    "shutil.rmtree",
    "subprocess.run",
    "subprocess.Popen",
    "subprocess.call",
}
CONFIRM_TTL_SECONDS = 180
_CONFIRMED_PULLS = {}
_PENDING_PLUGIN_CHOICES = []
_AI_REVIEW_CACHE = {}
_http = requests.Session()
_http.headers.update(
    {
        "User-Agent": "AxinixAI-PluginInstaller/1.0",
        "Accept": "application/vnd.github+json",
    }
)
IGNORED_QUERY_TOKENS = {
    "plugin",
    "plugins",
    "axinix",
    "pycroft",
    "axinix",
    "install",
    "installer",
    "github",
}


def _full_attr_name(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


def static_security_scan(code: str):
    if len(code) > MAX_PLUGIN_SIZE:
        return False, [f"File is too large (>{MAX_PLUGIN_SIZE} bytes)."]

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return False, [f"Syntax error: {exc}"]

    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if (
                    alias.name in FORBIDDEN_IMPORT_EXACT
                    or root in FORBIDDEN_IMPORT_ROOTS
                ):
                    findings.append(f"Forbidden import: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            root = module.split(".")[0]
            if module in FORBIDDEN_IMPORT_EXACT or root in FORBIDDEN_IMPORT_ROOTS:
                findings.append(f"Forbidden from-import: {module}")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
                findings.append(f"Forbidden call: {node.func.id}()")
            elif isinstance(node.func, ast.Attribute):
                full_name = _full_attr_name(node.func)
                if full_name in FORBIDDEN_ATTR_CALLS:
                    findings.append(f"Forbidden call: {full_name}()")

    return len(findings) == 0, findings


def _load_daily_review_state():
    today = date.today().isoformat()
    default_state = {"date": today, "count": 0}
    if not os.path.exists(LIMITS_FILE):
        return default_state
    try:
        with open(LIMITS_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, json.JSONDecodeError):
        return default_state
    if state.get("date") != today:
        return default_state
    return {"date": today, "count": int(state.get("count", 0))}


def _save_daily_review_state(state):
    try:
        with open(LIMITS_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f)
    except OSError:
        pass


def _remaining_daily_reviews():
    state = _load_daily_review_state()
    return max(0, MAX_DAILY_PLUGIN_REVIEWS - state["count"])


def _consume_daily_review_slot():
    state = _load_daily_review_state()
    if state["count"] >= MAX_DAILY_PLUGIN_REVIEWS:
        return False, 0
    state["count"] += 1
    _save_daily_review_state(state)
    return True, max(0, MAX_DAILY_PLUGIN_REVIEWS - state["count"])


def _ai_security_review(code: str):
    code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()
    cached = _AI_REVIEW_CACHE.get(code_hash)
    if cached is not None:
        return cached

    allowed, remaining_after = _consume_daily_review_slot()
    if not allowed:
        result = (
            False,
            [
                "Daily AI plugin review limit reached.",
                f"Maximum {MAX_DAILY_PLUGIN_REVIEWS} security reviews/installations per day.",
                "Try again tomorrow.",
            ],
        )
        _AI_REVIEW_CACHE[code_hash] = result
        return result

    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not api_key:
        result = (
            False,
            ["GOOGLE_API_KEY is missing, so AI security review is unavailable."],
        )
        _AI_REVIEW_CACHE[code_hash] = result
        return result

    prompt = (
        "You are a strict Python plugin security reviewer. "
        "Review the code for malicious or risky behavior such as command execution, "
        "filesystem writes outside plugin scope, network exfiltration, persistence tricks, "
        "dynamic imports, hidden payloads, credential theft, crypto mining, obfuscation, "
        "privilege escalation, or attempts to bypass static checks.\n"
        "Reply in exactly this format:\n"
        "VERDICT: SAFE or UNSAFE\n"
        "REASON: one short sentence\n"
        "FINDINGS:\n"
        "- finding 1\n"
        "- finding 2\n"
        "Keep findings concise. If safe, include only low-risk notes or say none.\n\n"
        f"Code:\n```python\n{code}\n```"
    )

    client = genai.Client(api_key=api_key, http_options={"api_version": "v1beta"})
    text = ""
    used_model = ""
    last_error = None
    for model_name in AI_SECURITY_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            text = (getattr(response, "text", "") or "").strip()
            used_model = model_name
            break
        except Exception as exc:
            last_error = exc
            continue

    if not used_model:
        result = (False, [f"AI security review failed: {last_error}"])
        _AI_REVIEW_CACHE[code_hash] = result
        return result

    verdict_match = re.search(r"VERDICT:\s*(SAFE|UNSAFE)", text, re.IGNORECASE)
    reason_match = re.search(r"REASON:\s*(.+)", text)
    findings = re.findall(r"^\s*-\s+(.+)$", text, re.MULTILINE)

    verdict = verdict_match.group(1).upper() if verdict_match else "UNSAFE"
    reason = (
        reason_match.group(1).strip()
        if reason_match
        else "AI reviewer did not return a clean verdict."
    )
    normalized_findings = [reason]
    normalized_findings.extend(findings[:5])
    normalized_findings.append(
        f"AI review used {used_model}. Remaining daily reviews: {remaining_after}."
    )

    result = (verdict == "SAFE", normalized_findings)
    _AI_REVIEW_CACHE[code_hash] = result
    return result


def _normalize_raw_url(raw_url: str):
    return raw_url.strip()


def _cleanup_expired_confirmations():
    now = time.time()
    expired = [
        url for url, ts in _CONFIRMED_PULLS.items() if now - ts > CONFIRM_TTL_SECONDS
    ]
    for url in expired:
        _CONFIRMED_PULLS.pop(url, None)


def _preview_text(text: str, limit: int = 700):
    collapsed = " ".join((text or "").split())
    return collapsed[:limit] if len(collapsed) > limit else collapsed


def _tokenize_search_text(text: str):
    return [token for token in re.findall(r"[a-z0-9]+", (text or "").lower()) if token]


def _meaningful_query_tokens(query: str):
    return [
        token
        for token in _tokenize_search_text(query)
        if token not in IGNORED_QUERY_TOKENS and len(token) > 1
    ]


def _repo_match_score(repo: dict, query_tokens):
    if not query_tokens:
        return 0.0

    haystack = _tokenize_search_text(repo.get("name", "")) + _tokenize_search_text(
        repo.get("description", "")
    )
    score = 0.0

    for query_token in query_tokens:
        best_similarity = 0.0
        for candidate in haystack:
            if candidate == query_token:
                best_similarity = 1.0
                break
            if query_token in candidate or candidate in query_token:
                best_similarity = max(best_similarity, 0.92)
                continue
            best_similarity = max(
                best_similarity,
                difflib.SequenceMatcher(None, query_token, candidate).ratio(),
            )
        if best_similarity >= 0.84:
            score += best_similarity * 3
        elif best_similarity >= 0.70:
            score += best_similarity * 1.5

    score += min(repo.get("stargazers_count", 0), 20) * 0.03
    return score


def _github_search(search_url: str):
    try:
        response = _http.get(search_url, timeout=REQUEST_TIMEOUT)
        if response.status_code != 200:
            return []
        payload = response.json()
    except (requests.RequestException, ValueError):
        return []
    return payload.get("items", [])


def _pending_filename(raw_url: str):
    return os.path.basename((raw_url or "").split("?")[0]) or "plugin.py"


def _set_pending_plugin_choices(choices):
    _PENDING_PLUGIN_CHOICES.clear()
    _PENDING_PLUGIN_CHOICES.extend(choices)


def _resolve_pending_plugin(selection: str = ""):
    if not _PENDING_PLUGIN_CHOICES:
        return None

    normalized_selection = (selection or "").strip().lower()
    if not normalized_selection:
        return _PENDING_PLUGIN_CHOICES[0]

    for candidate in _PENDING_PLUGIN_CHOICES:
        repo_name = candidate["repo_name"].lower()
        raw_url = candidate["raw_url"].lower()
        filename = candidate["filename"].lower()
        if (
            normalized_selection == raw_url
            or normalized_selection == repo_name
            or normalized_selection == filename
            or normalized_selection in repo_name
            or normalized_selection in filename
        ):
            return candidate

    selection_tokens = _meaningful_query_tokens(normalized_selection)
    if not selection_tokens:
        return _PENDING_PLUGIN_CHOICES[0]

    ranked = sorted(
        _PENDING_PLUGIN_CHOICES,
        key=lambda candidate: _repo_match_score(
            {
                "name": candidate["repo_name"],
                "description": candidate["filename"],
                "stargazers_count": candidate.get("stars", 0),
            },
            selection_tokens,
        ),
        reverse=True,
    )
    best = ranked[0]
    if (
        _repo_match_score(
            {
                "name": best["repo_name"],
                "description": best["filename"],
                "stargazers_count": best.get("stars", 0),
            },
            selection_tokens,
        )
        >= 1.5
    ):
        return best
    return None


def _readme_preview(repo_name: str):
    try:
        readme_url = f"https://api.github.com/repos/{repo_name}/readme"
        headers = {"Accept": "application/vnd.github.raw"}
        response = _http.get(readme_url, headers=headers, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200 and response.text:
            return _preview_text(response.text)
    except requests.RequestException:
        pass
    return "README not available."


def _resolve_plugin_raw_url(repo_name: str, branch: str):
    tree_url = (
        f"https://api.github.com/repos/{repo_name}/git/trees/{branch}?recursive=1"
    )
    try:
        response = _http.get(tree_url, timeout=REQUEST_TIMEOUT)
        if response.status_code != 200:
            return None
        tree_data = response.json()
    except (requests.RequestException, ValueError):
        return None
    py_files = [
        item["path"]
        for item in tree_data.get("tree", [])
        if item.get("path", "").endswith(".py")
    ]
    if not py_files:
        return None
    best_path = py_files[0]
    return f"https://raw.githubusercontent.com/{repo_name}/{branch}/{best_path}"


def search_github_plugins(query: str):
    """
    AI DESCRIPTION: Finds top plugin candidates by metadata only (description + README preview).
    SECURITY WORKFLOW:
    1) Use this function first.
    2) Summarize candidates for the user and ask explicit confirmation.
    3) Only after "yes" call confirm_plugin_pull(raw_url, True), then fetch_plugin_code(raw_url).
    """
    try:
        core_query = " ".join(query.strip().lower().split())
        if not core_query:
            return "No search keyword provided."

        query_tokens = _meaningful_query_tokens(core_query)
        search_urls = [
            (
                "https://api.github.com/search/repositories"
                f"?q={core_query}+topic:axinix-plugin+in:name,description&sort=stars&order=desc&per_page=8"
            ),
            (
                "https://api.github.com/search/repositories"
                f"?q={core_query}+axinix+in:name,description&sort=updated&order=desc&per_page=8"
            ),
            (
                "https://api.github.com/search/repositories"
                "?q=topic:axinix-plugin&sort=updated&order=desc&per_page=20"
            ),
        ]

        repos_by_name = {}
        for search_url in search_urls:
            for repo in _github_search(search_url):
                repos_by_name[repo["full_name"]] = repo

        if not repos_by_name:
            return f"No plugins found for the query: '{core_query}'."

        ranked_repos = sorted(
            repos_by_name.values(),
            key=lambda repo: (
                _repo_match_score(repo, query_tokens),
                repo.get("stargazers_count", 0),
                repo.get("updated_at", ""),
            ),
            reverse=True,
        )

        results = []
        pending_choices = []
        for repo in ranked_repos:
            if len(results) >= MAX_SEARCH_RESULTS:
                break
            if query_tokens and _repo_match_score(repo, query_tokens) < 1.5:
                continue
            repo_name = repo["full_name"]
            desc = repo.get("description", "No description")
            branch = repo.get("default_branch", "main")
            stars = repo.get("stargazers_count", 0)
            updated = repo.get("updated_at", "unknown")
            raw_url = _resolve_plugin_raw_url(repo_name, branch)
            if not raw_url:
                continue
            pending_choices.append(
                {
                    "repo_name": repo_name,
                    "raw_url": raw_url,
                    "filename": _pending_filename(raw_url),
                    "stars": stars,
                }
            )
            results.append(
                "\n".join(
                    [
                        f"Candidate: {repo_name}",
                        f"Description: {desc}",
                        f"Stars: {stars}",
                        f"Updated: {updated}",
                        f"RAW_URL: {raw_url}",
                    ]
                )
            )

        if results:
            _set_pending_plugin_choices(pending_choices)
            return (
                f"Top plugin candidates for '{core_query}' (metadata-only prefilter):\n\n"
                + "\n\n".join(results)
                + "\n\nSECURITY PROTOCOL:\n"
                + "1) Compare candidates with the user's intent.\n"
                + "2) Ask explicit confirmation before any download.\n"
                + "3) If the user says a generic yes, install the top pending candidate.\n"
                + "4) If the user names a specific candidate, use that selection."
                + f"\n5) Daily AI security review limit: {MAX_DAILY_PLUGIN_REVIEWS} installs/checks."
            )
        return f"No good plugin matches found for '{core_query}', although tagged repositories exist."
    except requests.RequestException as e:
        return f"GitHub API search error: {e}"


def confirm_plugin_pull(raw_url: str = "", user_approved: bool = False):
    """
    AI DESCRIPTION: Must be called only after explicit user confirmation to download plugin code.
    """
    _cleanup_expired_confirmations()
    normalized = _normalize_raw_url(raw_url)
    if not normalized:
        pending = _resolve_pending_plugin()
        if pending:
            normalized = pending["raw_url"]
    if not normalized:
        return "ERROR: No pending plugin candidate to confirm."
    if not user_approved:
        return "CANCELLED: User did not approve plugin download."
    _CONFIRMED_PULLS[normalized] = time.time()
    return (
        f"CONFIRMED: Download is allowed for {normalized} "
        f"for the next {CONFIRM_TTL_SECONDS} seconds."
    )


def install_pending_plugin(user_approved: bool, selection: str = ""):
    """
    AI DESCRIPTION: Use this right after the user confirms plugin installation.
    If the user says only "yes", call install_pending_plugin(user_approved=True).
    If the user names one of the last candidates, pass it as selection.
    """
    if not user_approved:
        return "CANCELLED: User did not approve plugin installation."

    pending = _resolve_pending_plugin(selection)
    if not pending:
        return (
            "ERROR: No pending plugin candidate matched the confirmation. "
            "Search again or ask the user which candidate to install."
        )

    return install_plugin(
        raw_url=pending["raw_url"],
        filename=pending["filename"],
        user_approved=True,
    )


def fetch_plugin_code(raw_url: str):
    """
    AI DESCRIPTION: Downloads source code only after explicit confirm_plugin_pull approval.
    CRITICAL:
    1) NEVER read the retrieved code out loud to the user.
    2) Call this only after user confirmation has been recorded via confirm_plugin_pull.
    """
    _cleanup_expired_confirmations()
    normalized = _normalize_raw_url(raw_url)
    if normalized not in _CONFIRMED_PULLS:
        return (
            "CONFIRMATION_REQUIRED: Download is blocked. Ask the user for explicit approval, "
            "then call confirm_plugin_pull(raw_url, user_approved=True) before fetch_plugin_code."
        )
    try:
        response = _http.get(normalized, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            code = response.text
            is_safe, findings = static_security_scan(code)
            if not is_safe:
                return "REJECTED: Static security scan failed.\n" + "\n".join(
                    f"- {item}" for item in findings
                )
            ai_safe, ai_findings = _ai_security_review(code)
            if not ai_safe:
                return "REJECTED: AI security review failed.\n" + "\n".join(
                    f"- {item}" for item in ai_findings
                )
            _CONFIRMED_PULLS.pop(normalized, None)
            return f"FETCH_OK:\n{code}"
        return f"Failed to download. HTTP Status: {response.status_code}"
    except requests.RequestException as e:
        return f"Download error: {e}"


def approve_and_save_plugin(code: str, filename: str):
    """
    AI DESCRIPTION: Saves plugin code after static policy validation.
    This function writes the approved code to the user's local plugins directory.
    """
    try:
        is_safe, findings = static_security_scan(code)
        if not is_safe:
            return "ERROR: Plugin rejected by static security policy.\n" + "\n".join(
                f"- {item}" for item in findings
            )

        if not filename.endswith(".py"):
            filename += ".py"

        # Security: prevent directory traversal attacks (e.g., passing "../../etc/passwd")
        safe_filename = os.path.basename(filename)
        plugins_dir = "plugins"
        filepath = os.path.join(plugins_dir, safe_filename)
        os.makedirs(plugins_dir, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)

        return (
            f"SUCCESS: Plugin '{safe_filename}' installed to {filepath}. "
            "Hot reload can activate it immediately if the live session reconnects successfully."
        )
    except Exception as e:
        return f"Error saving plugin: {e}"


def install_plugin(raw_url: str, filename: str = None, user_approved: bool = False):
    """
    AI DESCRIPTION: One-shot install pipeline for a vetted plugin URL.
    SECURITY: Requires explicit user_approved=True. Performs confirmation, fetch,
    static scan, and persistence. Returns SUCCESS/ERROR message for speech UI.
    """

    normalized = _normalize_raw_url(raw_url)
    if not normalized:
        return "ERROR: raw_url is required."

    # Enforce explicit approval
    if not user_approved:
        return (
            "CONFIRMATION_REQUIRED: Call again with user_approved=True after the user "
            "explicitly says yes."
        )

    # Record approval window, then fetch
    _cleanup_expired_confirmations()
    _CONFIRMED_PULLS[normalized] = time.time()

    fetch_result = fetch_plugin_code(normalized)
    if not isinstance(fetch_result, str):
        return "ERROR: Unexpected fetch result."

    if fetch_result.startswith("CONFIRMATION_REQUIRED"):
        return fetch_result

    if not fetch_result.startswith("FETCH_OK:\n"):
        return fetch_result  # propagate rejection or download error

    code = fetch_result[len("FETCH_OK:\n") :]

    # Default filename from URL if not provided
    if not filename:
        filename = os.path.basename(normalized.split("?")[0]) or "plugin.py"

    save_result = approve_and_save_plugin(code, filename)
    return save_result


# Update the registration so the AI model sees all the tools
def register_plugin():
    """
    Mandatory entry point for the plugin loader.
    """
    tools = [
        search_github_plugins,
        confirm_plugin_pull,
        fetch_plugin_code,
        approve_and_save_plugin,
        install_pending_plugin,
        install_plugin,
    ]
    mapping = {
        "search_github_plugins": search_github_plugins,
        "confirm_plugin_pull": confirm_plugin_pull,
        "fetch_plugin_code": fetch_plugin_code,
        "approve_and_save_plugin": approve_and_save_plugin,
        "install_pending_plugin": install_pending_plugin,
        "install_plugin": install_plugin,
    }
    return tools, mapping
