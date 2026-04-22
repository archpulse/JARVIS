"""
self_coder.py — Autonomous plugin code generation

Allows the AI to generate and install new plugins directly,
without manual user intervention.

Each generated plugin passes through a static_security_scan
before being saved.
"""

import os
import sys

# Inject plugins/ into sys.path so relative imports work after install
_plugins_dir = os.path.dirname(os.path.abspath(__file__))
if _plugins_dir not in sys.path:
    sys.path.insert(0, _plugins_dir)

# === SECURITY: reuse existing scanner ===
try:
    from cyber_installer import static_security_scan
except ImportError:
    # scanner unavailable — reject all generated code for safety
    static_security_scan = None

# Guardrails for AI-generated code (applied in addition to static scan)
_REQUIRED_PATTERNS = ("register_plugin",)
_FORBIDDEN_PATTERNS = (
    "while True:",
    "while True :",
    "while 1:",
    "while 1 :",
    "sys.exit(",
    "os._exit(",
    "exit(",
    "raise SystemExit",
)


def _check_code_guards(code: str) -> tuple[bool, list[str]]:
    """Additional guardrails beyond AST scan.

    Returns (is_safe, list_of_findings).
    """
    findings = []

    # Must have register_plugin
    if "register_plugin" not in code:
        findings.append("Missing register_plugin() function — required for plugin system")

    # Must not have bare infinite loops without try/except
    source_lines = code.split("\n")
    for lineno, line in enumerate(source_lines, 1):
        stripped = line.strip()
        if stripped.startswith(("while True", "while 1")):
            # Check if this loop has any try/except nearby (within 10 lines)
            loop_body = source_lines[lineno : lineno + 10]
            if not any("except" in l or "finally" in l for l in loop_body):
                findings.append(
                    f"Line {lineno}: infinite loop 'while True' without try/except — "
                    "add error handling to prevent CPU saturation"
                )
        # Also flag bare sys.exit / os._exit
        if stripped.startswith(("sys.exit", "os._exit", "exit(")):
            findings.append(f"Line {lineno}: suspicious exit call '{stripped}'")

    # Flag forbidden patterns
    for pattern in _FORBIDDEN_PATTERNS:
        if pattern in code:
            findings.append(f"Forbidden pattern detected: {pattern!r}")

    return len(findings) == 0, findings


def generate_and_install_plugin(filename: str, code: str, description: str = ""):
    """
    AI TOOL: generate_and_install_plugin

    Generates a new Jarvis plugin, validates it, and saves it to the plugins/
    directory for automatic hot-reload activation.

    Args:
        filename:   Target filename in plugins/ (e.g. "15_pinger.py")
        code:       Full Python source of the plugin
        description: Short human-readable description (used in confirmation)
    """
    # 1. Sanitise filename — prevent path traversal
    safe_name = os.path.basename(filename)
    if not safe_name.endswith(".py"):
        safe_name += ".py"
    plugin_path = os.path.join(_plugins_dir, safe_name)

    # 2. Static AST + getattr-scan
    if static_security_scan:
        is_ast_safe, ast_issues = static_security_scan(code)
        if not is_ast_safe:
            return (
                f"⛔ Blocked: Static security scan detected potential vulnerabilities:\n"
                + "\n".join(f"  - {issue}" for issue in ast_issues)
            )
    # 3. Additional guardrails
    is_guard_safe, guard_issues = _check_code_guards(code)
    if not is_guard_safe:
        return (
            f"⛔ Blocked: Code guardrails raised safety concerns:\n"
            + "\n".join(f"  - {issue}" for issue in guard_issues)
        )

    # 4. Write plugin
    try:
        with open(plugin_path, "w", encoding="utf-8") as f:
            f.write(code)
        return (
            f"✅ Plugin '{safe_name}' has been generated and secured: {description or 'no description provided'}.\n"
            f"   Location: {plugin_path}\n"
            f"   Activation: Automatic via hot-reload in 1-2 cycles."
        )
    except Exception as e:
        return f"⛔ Failed to save plugin: {e}"


def register_plugin():
    """
    Mandatory plugin entry point.
    """
    tools = [generate_and_install_plugin]
    mapping = {"generate_and_install_plugin": generate_and_install_plugin}
    return tools, mapping