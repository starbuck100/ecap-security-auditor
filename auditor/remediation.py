"""Remediation templates for security findings."""

from __future__ import annotations

REMEDIATION: dict[str, dict[str, object]] = {
    "INJECT_001": {
        "summary": "Do not pipe downloaded content to a shell",
        "fix": "Download to a file first, inspect it, then execute:\n  curl -o script.sh https://example.com/script.sh\n  cat script.sh  # review\n  bash script.sh",
        "references": ["CWE-78", "CWE-94"],
    },
    "INJECT_002": {
        "summary": "Remove eval and parse output safely",
        "fix": "Replace eval $(cmd) with safe parsing:\nwhile IFS='=' read -r k v; do\n  case \"$k\" in\n    EXPECTED_KEY) [[ \"$v\" =~ ^[0-9]+$ ]] && printf -v \"$k\" '%s' \"$v\" ;;\n  esac\ndone < <(cmd)",
        "references": ["CWE-78", "CWE-94"],
    },
    "TMPFILE_001": {
        "summary": "Use mktemp for temporary files",
        "fix": "Replace /tmp/predictable.txt with:\n  tmpfile=$(mktemp /tmp/myapp.XXXXXX)\n  trap 'rm -f \"$tmpfile\"' EXIT",
        "references": ["CWE-377", "CWE-379"],
    },
    "TMPFILE_SEC_001": {
        "summary": "Use mktemp with restrictive permissions and cleanup",
        "fix": "umask 077\ntmpfile=$(mktemp)\ntrap 'rm -f \"$tmpfile\"' EXIT\n# Use $tmpfile instead of /tmp/hardcoded",
        "references": ["CWE-377", "CWE-379", "CWE-367"],
    },
    "DATA_LEAK_001": {
        "summary": "Avoid piping sensitive data to stdout",
        "fix": "Write encoded output to a file with restrictive permissions instead:\n  base64 screenshot.png > /tmp/$(mktemp).b64\nOr pipe directly to the consuming process without stdout.",
        "references": ["CWE-532", "CWE-200"],
    },
    "DOS_INPUT_001": {
        "summary": "Add upper bounds to user-controlled loops",
        "fix": "Validate and cap the iteration count:\n  max_iter=100\n  count=${1:-10}\n  (( count > max_iter )) && count=$max_iter\n  for i in $(seq 1 \"$count\"); do ...",
        "references": ["CWE-400", "CWE-770"],
    },
    "SANDBOX_DIS_001": {
        "summary": "Do not disable security sandboxes",
        "fix": "Remove --no-sandbox, --disable-web-security, and similar flags.\nIf running in a container, configure the container to support sandboxing instead.",
        "references": ["CWE-693", "CWE-284"],
    },
    "NOERR_001": {
        "summary": "Add error handling to shell scripts",
        "fix": "Add at the top of the script:\n  set -euo pipefail\nThis ensures the script exits on errors, unset variables, and pipe failures.",
        "references": ["CWE-755"],
    },
    "SKILL_SETE_001": {
        "summary": "Add set -e or set -euo pipefail",
        "fix": "Add after the shebang line:\n  set -euo pipefail\nThis prevents silent failures and uninitialized variable usage.",
        "references": ["CWE-755"],
    },
    "SUDO_001": {
        "summary": "Avoid sudo in skill scripts",
        "fix": "Skills should not require root privileges. If elevated access is needed,\ndocument it clearly and let the user/orchestrator handle privilege escalation.",
        "references": ["CWE-250", "CWE-269"],
    },
    "EXFIL_001": {
        "summary": "Do not send secrets via HTTP requests",
        "fix": "Never include environment variable secrets in HTTP request bodies.\nUse a secrets manager or vault, and rotate any exposed credentials immediately.",
        "references": ["CWE-200", "CWE-522"],
    },
    "DESTRUCT_001": {
        "summary": "Restrict deletion scope and add safety checks",
        "fix": "Never use rm -rf on broad paths. Use:\n  target=\"./specific-dir\"\n  [[ -d \"$target\" ]] && rm -rf \"$target\"\nAlways use a variable with explicit path validation.",
        "references": ["CWE-73"],
    },
    "DEP_MISSING_001": {
        "summary": "Document and check binary dependencies",
        "fix": "Add a dependency check at script start:\n  for cmd in jq ffmpeg bc; do\n    command -v \"$cmd\" >/dev/null || { echo \"Missing: $cmd\" >&2; exit 1; }\n  done\nAlso list requirements in SKILL.md.",
        "references": ["CWE-440"],
    },
}
