"""Report formatting for audit results."""

from __future__ import annotations

import json
import logging
from collections import OrderedDict
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .analyzer import AuditReport, Finding
from .remediation import REMEDIATION

logger = logging.getLogger(__name__)


def _consolidate_findings(findings: list[Finding]) -> list[dict[str, Any]]:
    """Group findings by pattern_id, preserving order of first occurrence."""
    groups: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for f in findings:
        if f.pattern_id not in groups:
            groups[f.pattern_id] = {
                "pattern_id": f.pattern_id,
                "name": f.name,
                "severity": f.severity,
                "description": f.description,
                "count": 0,
                "locations": [],
            }
        groups[f.pattern_id]["count"] += 1
        groups[f.pattern_id]["locations"].append({
            "file": f.file,
            "line": f.line_number,
            "content": f.line_content,
        })
    return list(groups.values())


def to_dict(report: AuditReport) -> dict[str, Any]:
    """Convert an AuditReport to a plain dict with consolidated findings."""
    consolidated = _consolidate_findings(report.findings)
    total_occurrences = sum(g["count"] for g in consolidated)
    return {
        "skill_path": report.skill_path,
        "skill_slug": report.skill_slug,
        "files_scanned": report.files_scanned,
        "findings_count": len(consolidated),
        "total_occurrences": total_occurrences,
        "risk_score": report.risk_score,
        "result": report.result,
        "max_severity": report.max_severity,
        "metadata": report.metadata,
        "findings": consolidated,
    }


def to_json(report: AuditReport, indent: int = 2) -> str:
    """Format an AuditReport as JSON string."""
    return json.dumps(to_dict(report), indent=indent, ensure_ascii=False)


def to_markdown(report: AuditReport) -> str:
    """Format an AuditReport as human-readable Markdown with consolidation."""
    consolidated = _consolidate_findings(report.findings)
    total_occurrences = sum(g["count"] for g in consolidated)

    lines: list[str] = []
    lines.append(f"# Audit Report: {report.skill_slug}")
    lines.append("")
    lines.append(f"- **Path:** `{report.skill_path}`")
    lines.append(f"- **Files scanned:** {report.files_scanned}")
    lines.append(f"- **Unique findings:** {len(consolidated)}")
    lines.append(f"- **Total occurrences:** {total_occurrences}")
    lines.append(f"- **Risk score:** {report.risk_score}/100")
    lines.append(f"- **Result:** {report.result}")
    if report.max_severity:
        lines.append(f"- **Max severity:** {report.max_severity}")
    lines.append("")

    if not consolidated:
        lines.append("✅ No issues found.")
        return "\n".join(lines)

    by_sev: dict[str, list[dict]] = {}
    for g in consolidated:
        by_sev.setdefault(g["severity"], []).append(g)

    for sev in ("critical", "high", "medium", "low"):
        items = by_sev.get(sev, [])
        if not items:
            continue
        icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}[sev]
        lines.append(f"## {icon} {sev.upper()} ({len(items)} unique, {sum(i['count'] for i in items)} occurrences)")
        lines.append("")
        for g in items:
            lines.append(f"### [{g['pattern_id']}] {g['name']} ({g['count']}x)")
            lines.append(f"{g['description']}")
            lines.append("")

            # Remediation
            rem = REMEDIATION.get(g["pattern_id"])
            if rem:
                lines.append(f"**Remediation:** {rem['summary']}")
                lines.append(f"```")
                lines.append(str(rem["fix"]))
                lines.append(f"```")
                if rem.get("references"):
                    lines.append(f"References: {', '.join(rem['references'])}")
                lines.append("")

            lines.append("**Locations:**")
            for loc in g["locations"]:
                loc_str = f"`{loc['file']}:{loc['line']}`" if loc["file"] else "(metadata)"
                lines.append(f"- {loc_str}")
                if loc["content"]:
                    lines.append(f"  `{loc['content'][:120]}`")
            lines.append("")

    return "\n".join(lines)


def save_report(report: AuditReport, report_dir: str) -> Path:
    """Save report as both JSON and Markdown files."""
    out = Path(report_dir)
    out.mkdir(parents=True, exist_ok=True)

    json_path = out / f"{report.skill_slug}.json"
    md_path = out / f"{report.skill_slug}.md"

    json_path.write_text(to_json(report), encoding="utf-8")
    md_path.write_text(to_markdown(report), encoding="utf-8")

    logger.info("Reports saved: %s, %s", json_path, md_path)
    return json_path


def prepare_api_payload(report: AuditReport) -> dict[str, Any]:
    """Prepare payload for future POST /api/v1/reports/security endpoint."""
    consolidated = _consolidate_findings(report.findings)
    total_occurrences = sum(g["count"] for g in consolidated)
    return {
        "skill_slug": report.skill_slug,
        "risk_score": report.risk_score,
        "result": report.result,
        "max_severity": report.max_severity,
        "findings_count": len(consolidated),
        "total_occurrences": total_occurrences,
        "findings": consolidated,
    }
