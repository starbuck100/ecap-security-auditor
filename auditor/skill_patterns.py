"""Extended skill-specific vulnerability pattern definitions."""

from __future__ import annotations

from .patterns import Pattern

SKILL_PATTERNS: dict[str, list[Pattern]] = {
    "critical": [
        {
            "id": "SKILL_UNICODE_001",
            "name": "Hidden Unicode characters in SKILL.md",
            "regex": r"[\u200b\u200c\u200d\u200e\u200f\u202a-\u202e\u2060\u2066-\u2069\ufeff]",
            "description": "SKILL.md contains zero-width spaces, RTL overrides, or similar invisible Unicode.",
        },
        {
            "id": "SKILL_CRED_001",
            "name": "Instruction to read/send credentials",
            "regex": r"(?i)(read|send|exfiltrate|upload|post)\s+.{0,40}(credentials?|passwords?|tokens?|secrets?|api[_-]?keys?|ssh[_-]?keys?|private[_-]?keys?)",
            "description": "Instructions that direct the agent to access or transmit credentials.",
        },
        {
            "id": "SKILL_OVERRIDE_001",
            "name": "Override/must with security keywords",
            "regex": r"(?i)(always|must|override|bypass)\s+.{0,30}(security|permission|sandbox|restriction|policy|auth)",
            "description": "Combines override language with security-related terms.",
        },
        {
            "id": "SKILL_DESTRUCT_001",
            "name": "Destructive commands without safety flags",
            "regex": r"(?i)(rm\s+-rf|mkfs|dd\s+if=|format\s+[A-Z]:)(?!.*set\s+-euo\s+pipefail)",
            "description": "Bash script has destructive commands without set -euo pipefail.",
        },
    ],
    "high": [
        {
            "id": "SKILL_B64_001",
            "name": "Embedded Base64 strings in SKILL.md",
            "regex": r"[A-Za-z0-9+/]{50,}={0,2}",
            "description": "Long Base64-encoded string found — possible obfuscated payload.",
        },
        {
            "id": "SKILL_EXTURL_001",
            "name": "Hardcoded external URL data exfiltration",
            "regex": r"(?i)(curl|wget|fetch|requests?\.(get|post)|axios\.(get|post)|http\.request)\s*.*https?://(?!localhost|127\.0\.0\.1)",
            "description": "Script sends data to a hardcoded external URL.",
        },
        {
            "id": "SKILL_HOOK_001",
            "name": "Undocumented post-install hook",
            "regex": r"""(?i)["']?(postinstall|preinstall|install|prepare)["']?\s*:\s*["']""",
            "description": "Package has install hooks that may run arbitrary code.",
        },
        {
            "id": "SKILL_BINREQ_001",
            "name": "Excessive binary requirements",
            "regex": r"(?i)requires\s*[=:]\s*\[.*,.*,.*,.*,",
            "description": "Skill requires an unusually large number of system binaries.",
        },
    ],
    "medium": [
        {
            "id": "SKILL_SHEBANG_001",
            "name": "Script without shebang",
            "regex": r"__NO_FILE_MATCH__",
            "description": "Shell script lacks a shebang line.",
        },
        {
            "id": "SKILL_ENV_001",
            "name": "Undocumented required environment variable",
            "regex": r"\$\{?[A-Z][A-Z0-9_]{3,}\}?(?!.*#.*required|.*#.*env|.*documented)",
            "description": "References environment variables that may not be documented.",
        },
        {
            "id": "SKILL_SETE_001",
            "name": "Missing error handling in shell script",
            "regex": r"^#!/bin/(ba)?sh\s*$",
            "description": "Shell script lacks set -e or set -euo pipefail for error handling.",
        },
    ],
}
