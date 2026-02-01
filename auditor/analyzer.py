"""Static analysis engine for skill packages."""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .mcp_patterns import MCP_PATTERNS
from .patterns import PATTERNS, Pattern
from .skill_patterns import SKILL_PATTERNS

logger = logging.getLogger(__name__)

SEVERITY_WEIGHTS: dict[str, int] = {
    "critical": 25,
    "high": 15,
    "medium": 5,
    "low": 1,
}

MAX_FILE_SIZE = 1_048_576  # 1 MB
TEXT_EXTENSIONS = {
    ".md", ".txt", ".sh", ".bash", ".py", ".js", ".ts", ".json", ".yaml",
    ".yml", ".toml", ".ini", ".cfg", ".conf", ".env", ".example", ".csv",
    ".html", ".css", ".xml", ".rb", ".pl", ".lua", ".rs", ".go", ".java",
    ".c", ".h", ".cpp", ".hpp", ".r", ".jl", "",
}

# Directories/files to skip during scanning (test fixtures, docs with examples)
SKIP_DIRS = {"tests", "test", "__tests__", "node_modules", ".git", "__pycache__", "audit-reports"}
SKIP_SUFFIXES = {"_test.py", "_test.sh", ".test.js", ".test.ts", ".spec.js", ".spec.ts"}


@dataclass
class Finding:
    """A single matched vulnerability pattern."""
    pattern_id: str
    name: str
    severity: str
    description: str
    file: str
    line_number: int
    line_content: str


@dataclass
class AuditReport:
    """Full audit report for a skill."""
    skill_path: str
    skill_slug: str
    findings: list[Finding] = field(default_factory=list)
    risk_score: int = 0
    files_scanned: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def result(self) -> str:
        """Return 'clean' or 'flagged'."""
        return "flagged" if self.findings else "clean"

    @property
    def max_severity(self) -> str | None:
        """Return the highest severity found."""
        order = ["critical", "high", "medium", "low"]
        for sev in order:
            if any(f.severity == sev for f in self.findings):
                return sev
        return None


def _is_text_file(path: Path) -> bool:
    """Heuristic check for text files."""
    return path.suffix.lower() in TEXT_EXTENSIONS


def _check_metadata(skill_path: Path) -> list[Finding]:
    """Check metadata-level issues (no regex needed)."""
    findings: list[Finding] = []

    # Missing LICENSE
    license_files = [f for f in skill_path.iterdir() if f.name.upper().startswith("LICENSE")]
    if not license_files:
        findings.append(Finding(
            pattern_id="META_001", name="Missing license", severity="low",
            description="No LICENSE file found.", file="", line_number=0, line_content="",
        ))

    # SKILL.md metadata check
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        findings.append(Finding(
            pattern_id="META_002", name="No SKILL.md", severity="low",
            description="SKILL.md is missing.", file="", line_number=0, line_content="",
        ))
    else:
        try:
            content = skill_md.read_text(errors="replace")
            if not content.startswith("---"):
                findings.append(Finding(
                    pattern_id="META_002", name="No SKILL.md metadata", severity="low",
                    description="SKILL.md has no frontmatter.", file="SKILL.md",
                    line_number=1, line_content=content[:80],
                ))
        except OSError:
            pass

    # Changelog
    changelog_names = {"CHANGELOG", "CHANGELOG.md", "changelog", "changelog.md", "CHANGES", "CHANGES.md"}
    if not any((skill_path / n).exists() for n in changelog_names):
        findings.append(Finding(
            pattern_id="META_004", name="No changelog", severity="low",
            description="No changelog found.", file="", line_number=0, line_content="",
        ))

    # Large files
    for root, _dirs, files in os.walk(skill_path):
        for fname in files:
            fpath = Path(root) / fname
            try:
                if fpath.stat().st_size > MAX_FILE_SIZE:
                    rel = str(fpath.relative_to(skill_path))
                    findings.append(Finding(
                        pattern_id="META_003", name="Large file in skill", severity="low",
                        description=f"File {rel} exceeds 1MB.",
                        file=rel, line_number=0, line_content="",
                    ))
            except OSError:
                pass

    return findings


def _compile_pattern_set(
    pattern_set: dict[str, list[Pattern]],
) -> list[tuple[str, Pattern, re.Pattern[str]]]:
    """Pre-compile all regex patterns from a pattern set."""
    compiled: list[tuple[str, Pattern, re.Pattern[str]]] = []
    for severity, patterns in pattern_set.items():
        for pat in patterns:
            if pat["regex"] == "__NO_FILE_MATCH__":
                continue
            try:
                compiled.append((severity, pat, re.compile(pat["regex"])))
            except re.error as exc:
                logger.warning("Invalid regex in %s: %s", pat["id"], exc)
    return compiled


_COMPILED: list[tuple[str, Pattern, re.Pattern[str]]] | None = None
_COMPILED_MCP: list[tuple[str, Pattern, re.Pattern[str]]] | None = None
_COMPILED_SKILL: list[tuple[str, Pattern, re.Pattern[str]]] | None = None


def _get_compiled() -> list[tuple[str, Pattern, re.Pattern[str]]]:
    global _COMPILED
    if _COMPILED is None:
        _COMPILED = _compile_pattern_set(PATTERNS)
    return _COMPILED


def _get_compiled_mcp() -> list[tuple[str, Pattern, re.Pattern[str]]]:
    global _COMPILED_MCP
    if _COMPILED_MCP is None:
        _COMPILED_MCP = _compile_pattern_set(MCP_PATTERNS)
    return _COMPILED_MCP


def _get_compiled_skill() -> list[tuple[str, Pattern, re.Pattern[str]]]:
    global _COMPILED_SKILL
    if _COMPILED_SKILL is None:
        _COMPILED_SKILL = _compile_pattern_set(SKILL_PATTERNS)
    return _COMPILED_SKILL


def detect_scan_type(path: str) -> str:
    """Detect the type of project at the given path.

    Args:
        path: Root directory to inspect.

    Returns:
        One of: 'skill', 'openskill', 'mcp', 'npm', 'pip'.
    """
    root = Path(path).resolve()
    skill_md = root / "SKILL.md"
    package_json = root / "package.json"
    pyproject = root / "pyproject.toml"
    setup_py = root / "setup.py"

    if skill_md.exists():
        try:
            content = skill_md.read_text(errors="replace")
            if "openskill" in content.lower() or "open-skill" in content.lower():
                return "openskill"
        except OSError:
            pass
        return "skill"

    if package_json.exists():
        try:
            import json as _json
            data = _json.loads(package_json.read_text(errors="replace"))
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            if any("modelcontextprotocol" in k or k == "mcp" for k in deps):
                return "mcp"
        except (OSError, ValueError):
            pass
        return "npm"

    if pyproject.exists() or setup_py.exists():
        return "pip"

    return "skill"


def _scan_files(
    root: Path,
    compiled_sets: list[list[tuple[str, Pattern, re.Pattern[str]]]],
    report: AuditReport,
) -> None:
    """Scan all text files under root against multiple compiled pattern sets."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            fpath = Path(dirpath) / fname
            if not _is_text_file(fpath):
                continue
            if any(fname.endswith(s) for s in SKIP_SUFFIXES):
                continue
            rel = str(fpath.relative_to(root))
            try:
                content = fpath.read_text(errors="replace")
            except OSError as exc:
                logger.warning("Cannot read %s: %s", rel, exc)
                continue

            report.files_scanned += 1

            for line_no, line in enumerate(content.splitlines(), start=1):
                for compiled in compiled_sets:
                    for severity, pat, regex in compiled:
                        if regex.search(line):
                            report.findings.append(Finding(
                                pattern_id=pat["id"],
                                name=pat["name"],
                                severity=severity,
                                description=pat["description"],
                                file=rel,
                                line_number=line_no,
                                line_content=line.strip()[:200],
                            ))


def analyze_mcp_server(path: str) -> AuditReport:
    """Perform static analysis on an MCP server directory.

    Args:
        path: Path to the MCP server's root directory.

    Returns:
        AuditReport with all findings and computed risk score.
    """
    root = Path(path).resolve()
    slug = root.name
    report = AuditReport(skill_path=str(root), skill_slug=slug)
    report.metadata["scan_type"] = "mcp"

    if not root.is_dir():
        logger.error("Path does not exist or is not a directory: %s", root)
        return report

    # Check for package.json version
    pkg_json = root / "package.json"
    if pkg_json.exists():
        try:
            import json as _json
            data = _json.loads(pkg_json.read_text(errors="replace"))
            if not data.get("version"):
                report.findings.append(Finding(
                    pattern_id="MCP_VER_001", name="No version specified",
                    severity="low", description="No version in package.json.",
                    file="package.json", line_number=0, line_content="",
                ))
        except (OSError, ValueError):
            pass
    else:
        report.findings.append(Finding(
            pattern_id="MCP_DOC_001", name="Missing tool documentation",
            severity="low", description="No package.json found for MCP server.",
            file="", line_number=0, line_content="",
        ))

    # Check for README
    if not any((root / n).exists() for n in ("README.md", "README", "readme.md")):
        report.findings.append(Finding(
            pattern_id="MCP_DOC_001", name="Missing tool documentation",
            severity="low", description="No README found.",
            file="", line_number=0, line_content="",
        ))

    compiled_base = _get_compiled()
    compiled_mcp = _get_compiled_mcp()
    _scan_files(root, [compiled_base, compiled_mcp], report)

    raw = sum(SEVERITY_WEIGHTS.get(f.severity, 0) for f in report.findings)
    report.risk_score = min(100, raw)

    logger.info(
        "MCP audit complete for %s: %d findings, risk_score=%d",
        slug, len(report.findings), report.risk_score,
    )
    return report


def analyze_skill(skill_path: str) -> AuditReport:
    """Perform static analysis on a skill directory.

    Args:
        skill_path: Path to the skill's root directory.

    Returns:
        AuditReport with all findings and computed risk score.
    """
    root = Path(skill_path).resolve()
    slug = root.name
    report = AuditReport(skill_path=str(root), skill_slug=slug)

    if not root.is_dir():
        logger.error("Skill path does not exist or is not a directory: %s", root)
        return report

    # Metadata checks
    report.findings.extend(_check_metadata(root))

    # Scan files with base patterns + extended skill patterns
    _scan_files(root, [_get_compiled(), _get_compiled_skill()], report)

    # Compute risk score (0–100)
    raw = sum(SEVERITY_WEIGHTS.get(f.severity, 0) for f in report.findings)
    report.risk_score = min(100, raw)

    logger.info(
        "Audit complete for %s: %d findings, risk_score=%d",
        slug, len(report.findings), report.risk_score,
    )
    return report
