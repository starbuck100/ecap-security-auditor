"""MCP Server vulnerability pattern definitions."""

from __future__ import annotations

from .patterns import Pattern

MCP_PATTERNS: dict[str, list[Pattern]] = {
    "critical": [
        {
            "id": "MCP_INJECT_001",
            "name": "Hidden instructions in tool description",
            "regex": r"(?i)(ignore\s+previous|you\s+must|system\s*:|<\s*system\s*>|BEGIN\s+SYSTEM)",
            "description": "Tool description contains hidden prompt injection instructions.",
        },
        {
            "id": "MCP_SHELL_001",
            "name": "Unsandboxed shell access in tool",
            "regex": r"""(?i)(child_process|\.exec\s*\(|\.spawn\s*\(|\.execSync|\.spawnSync|Deno\.run|subprocess\.run|os\.system|os\.popen)""",
            "description": "Tool provides shell execution without apparent sandboxing.",
        },
        {
            "id": "MCP_EXFIL_001",
            "name": "Credential parameter sent to external URL",
            "regex": r"(?i)(token|credential|secret|password|api[_-]?key)\b.*\b(fetch|axios|got|request|http\.request|urllib|requests\.(get|post))",
            "description": "Tool takes credential-like parameters and makes external HTTP requests.",
        },
        {
            "id": "MCP_TRANSPORT_001",
            "name": "Dangerous stdio transport command",
            "regex": r"""(?i)(command|cmd)\s*[=:]\s*['"]?(bash\s+-c|sh\s+-c|eval\s|cmd\s*/c)""",
            "description": "stdio transport uses shell wrapper (bash -c, sh -c, eval).",
        },
    ],
    "high": [
        {
            "id": "MCP_PERM_001",
            "name": "Unrestricted filesystem access",
            "regex": r"""(?i)(readFile|writeFile|fs\.(read|write|unlink|rmdir|mkdir)|open\s*\()\s*.*(?!.*sandbox)""",
            "description": "Tool has broad filesystem read/write without path restrictions.",
        },
        {
            "id": "MCP_ALLOWALL_001",
            "name": "Permissive allow-all flag",
            "regex": r"(?i)(--allow-all|--allow-read=\.|--allow-write=\.|--no-sandbox|--disable-security)",
            "description": "Server launched with overly permissive security flags.",
        },
        {
            "id": "MCP_UNICODE_001",
            "name": "Unicode tricks in tool name/description",
            "regex": r"[\u200b\u200c\u200d\u200e\u200f\u202a-\u202e\u2060\u2066-\u2069\ufeff]",
            "description": "Zero-width or bidirectional override characters in tool metadata.",
        },
        {
            "id": "MCP_HTTP_001",
            "name": "MCP server listening on HTTP",
            "regex": r"""(?i)(listen|createServer|app\.listen|server\.listen)\s*\(.*\b(http(?!s)|port\s*[=:]\s*\d+)(?!.*https)""",
            "description": "MCP server uses HTTP instead of HTTPS for transport.",
        },
    ],
    "medium": [
        {
            "id": "MCP_VALID_001",
            "name": "Missing input validation for tool parameters",
            "regex": r"""(?i)(inputSchema|parameters)\s*[=:]\s*\{[^}]*type\s*[=:]\s*['"]string['"][^}]*(?!pattern|minLength|maxLength|enum)""",
            "description": "Tool parameters accept arbitrary strings without validation constraints.",
        },
        {
            "id": "MCP_RATE_001",
            "name": "No rate limiting configured",
            "regex": r"__NO_FILE_MATCH__",
            "description": "Server has no apparent rate limiting configuration.",
        },
        {
            "id": "MCP_DEP_001",
            "name": "Unpinned dependencies",
            "regex": r"""['"]([@a-z][a-z0-9/_.-]*)['"]\s*:\s*['"]\s*(\*|\^|~|>=|latest)\s*""",
            "description": "Dependencies use unpinned or loose version ranges.",
        },
        {
            "id": "MCP_AUTH_001",
            "name": "Missing CORS or auth configuration",
            "regex": r"__NO_FILE_MATCH__",
            "description": "Server lacks CORS headers or authentication middleware.",
        },
    ],
    "low": [
        {
            "id": "MCP_DOC_001",
            "name": "Missing tool documentation",
            "regex": r"__NO_FILE_MATCH__",
            "description": "Tool or server lacks adequate documentation.",
        },
        {
            "id": "MCP_VER_001",
            "name": "No version specified",
            "regex": r"__NO_FILE_MATCH__",
            "description": "No version information found in server metadata.",
        },
        {
            "id": "MCP_TODO_001",
            "name": "TODO/FIXME in MCP server code",
            "regex": r"(?i)(TODO|FIXME|HACK|XXX)\s*:",
            "description": "Unfinished work markers in server code.",
        },
    ],
}
