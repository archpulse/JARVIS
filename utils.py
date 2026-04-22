import os
import re
import shutil
import subprocess
import sys
import time

def get_output_device_index(p):
    """Find the best output device index (PipeWire/Pulse preferred)."""
    try:
        for i in range(p.get_device_count()):
            try:
                info = p.get_device_info_by_index(i)
                name = info.get("name", "").lower()
                if info["maxOutputChannels"] > 0:
                    if "pipewire" in name or "pulse" in name:
                        return i
            except (OSError, KeyError):
                continue

        for i in range(p.get_device_count()):
            try:
                info = p.get_device_info_by_index(i)
                if info["maxOutputChannels"] > 0:
                    return i
            except (OSError, KeyError):
                continue
        return None
    except OSError:
        return None

def get_input_device_index(p):
    """Find the best input device index (PipeWire/Pulse/Default preferred)."""
    try:
        for i in range(p.get_device_count()):
            try:
                info = p.get_device_info_by_index(i)
                name = info.get("name", "").lower()
                if info["maxInputChannels"] > 0:
                    if "pipewire" in name or "pulse" in name or "default" in name:
                        return i
            except (OSError, KeyError):
                continue

        for i in range(p.get_device_count()):
            try:
                info = p.get_device_info_by_index(i)
                if info["maxInputChannels"] > 0:
                    return i
            except (OSError, KeyError):
                continue
        return None
    except OSError:
        return None

def detect_language_from_transcript(text: str) -> str:
    """Detect language (EN, RU, UA, JA) from text transcript."""
    if not text:
        return "EN"
    text = text.strip()
    text_lower = text.lower()

    for ch in text:
        code = ord(ch)
        if (0x3040 <= code <= 0x30FF) or (0x4E00 <= code <= 0x9FFF):
            return "JA"

    if re.search(r"\b(доброго|привiт|привіт|дякую|будь ласка|що|це|чому)\b", text_lower):
        return "UA"
    if re.search(r"[іїєґІЇЄҐ]", text):
        return "UA"
    if re.search(r"[ыъэёЫЪЭЁ]", text):
        return "RU"
    if re.search(r"[А-Яа-яЁё]", text):
        return "RU"
    return "EN"

def is_install_confirmation(text: str) -> bool:
    """Check if text confirms a plugin installation."""
    if not text:
        return False
    normalized = text.strip().lower()
    confirmation_patterns = [
        r"^(да|ага|угу|так|yes)$",
        r"\b(подтверждаю установку|устанавливай|ставь плагин|скачивай|підтверджую|встановлюй|confirm|install it|go ahead|do it)\b",
    ]
    return any(re.search(pattern, normalized) for pattern in confirmation_patterns)

def is_explicit_plugin_install_request(text: str) -> bool:
    """Check if text is an explicit request to install a plugin."""
    if not text:
        return False
    normalized = " ".join(text.strip().lower().split())
    plugin_words = ["plugin", "plugins", "skill", "skills", "module", "modules", "плагин", "плагины", "плагіна", "плагіни", "модуль", "модулі", "скилл", "скилы"]
    action_patterns = [
        r"\b(install|add|find|search|look for|download|get me)\b",
        r"\b(установи|установить|добавь|найди|ищи|скачай)\b",
        r"\b(встанови|встановити|додай|знайди|шукай|скачай)\b",
    ]
    if not any(word in normalized for word in plugin_words):
        return False
    return any(re.search(pattern, normalized) for pattern in action_patterns)

def command_exists(name: str) -> bool:
    """Check if a shell command exists."""
    return shutil.which(name) is not None

def run_command(args, timeout=6):
    """Run a shell command and return the result."""
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)

def is_explicit_web_search_request(text: str) -> bool:
    """Check if text is an explicit request for web search."""
    normalized = " ".join((text or "").strip().lower().split())
    if not normalized:
        return False
    patterns = [
        r"\b(search the internet|search online|look it up|web search|google it)\b",
        r"\b(поищи в интернете|найди в интернете|поищи онлайн|загугли|найди в сети)\b",
        r"\b(пошукай в інтернеті|знайди в інтернеті|загугли|знайди в мережі)\b",
    ]
    return any(re.search(pattern, normalized) for pattern in patterns)

def is_meta_model_text(text: str) -> bool:
    """Check if text is 'meta' talk from the model about its own rules/actions."""
    normalized = " ".join((text or "").strip().lower().split())
    if not normalized:
        return False
    meta_markers = [
        "initiating plugin search", "re-evaluating", "adapting to system constraints",
        "interpreting explicit request", "following rule", "rule 2", "rule 4", "rule 5", "rule 6",
        "i am commencing the plugin search", "I have started searching for plugins", "I am going to",
        "internal", "system flagged", "system incorrectly labeled", "i've hit a snag", "i'm wrestling with the system",
    ]
    if normalized.startswith("**") and normalized.endswith("**"):
        return True
    return any(marker in normalized for marker in meta_markers)

def localized_text(lang: str, ru: str, ua: str = None, en: str = None, ja: str = None) -> str:
    """Helper for localized strings."""
    if lang == "UA": return ua or ru
    if lang == "JA": return ja or en or ru
    if lang == "EN": return en or ru
    return ru

def extract_plugin_search_query(text: str) -> str:
    """Clean up text to extract a plugin search query."""
    normalized = " ".join((text or "").strip().lower().split())
    if not normalized: return ""
    for filler in ["пожалуйста", "будь ласка", "please", "hey jarvis", "jarvis"]:
        normalized = normalized.replace(filler, " ")
    normalized = " ".join(normalized.split())
    removals = [
        r"\b(install|add|find|search|look for|download|get me)\b",
        r"\b(plugin|plugins|skill|skills|module|modules)\b",
        r"\b(установи|установить|добавь|найди|ищи|скачай)\b",
        r"\b(плагин|плагины|модуль|модули|скилл|скилы)\b",
        r"\b(встанови|встановити|додай|знайди|шукай|скачай)\b",
        r"\b(плагіна|плагіни|модуль|модулі)\b",
    ]
    query = normalized
    for pattern in removals:
        query = re.sub(pattern, " ", query)
    query = re.sub(r"[.,-]+", " ", query)
    query = re.sub(r"\s+", " ", query).strip(" .,-")
    return query or normalized

def extract_plugin_prompt_text(search_result: str) -> str:
    """Extract candidate name from search result for confirmation prompt."""
    text = str(search_result or "")
    candidate_match = re.search(r"Candidate:\s*(.+)", text)
    repo_name = candidate_match.group(1).strip() if candidate_match else ""
    if repo_name:
        return f"Install plugin {repo_name}?"
    return "Install the discovered plugin?"

def build_plugin_install_outcome_message(result: str, lang: str) -> str:
    """Build localized outcome message for plugin installation."""
    result = str(result or "").strip()
    if lang == "RU":
        return f"I have installed the plugin. {result}" if "SUCCESS" in result else f"Plugin installation failed. Reason: {result}"
    if lang == "UA":
        return f"I have installed the plugin. {result}" if "SUCCESS" in result else f"Plugin installation failed. Reason: {result}"
    if lang == "JA":
        return f"プラグインをインストールしました。{result}" if "SUCCESS" in result else f"プラグインはインストールされませんでした。理由: {result}"
    return f"I installed the plugin. {result}" if "SUCCESS" in result else f"I did not install the plugin. Reason: {result}"

def is_screen_request(text: str) -> bool:
    """Detect direct screen-analysis requests."""
    normalized = " ".join((text or "").strip().lower().split())
    if not normalized: return False
    patterns = [
        r"\bчто\s+у\s+меня\s+на\s+экране\b", r"\bчто\s+на\s+экране\b",
        r"\bпосмотри\s+(?:на\s+)?экран\b", r"\bсмотри\s+(?:на\s+)?экран\b",
        r"\bпосмотри\s+на\s+это\b", r"\blook\s+at\s+this\b",
        r"\bdebug\s+this\s+error\b", r"\bwhat(?:'s| is)\s+on\s+my\s+screen\b",
        r"\blook\s+at\s+my\s+screen\b", r"\bwhat\s+is\s+on\s+my\s+screen\b",
    ]
    return any(re.search(pattern, normalized) for pattern in patterns)

def run_command(args, timeout=6):
    """Run a system command safely with timeout and error handling."""
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutError:
        return subprocess.CompletedProcess(args, returncode=-1, stdout="", stderr="Timeout")
    except Exception as e:
        return subprocess.CompletedProcess(args, returncode=-1, stdout="", stderr=str(e))
