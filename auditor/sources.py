"""Source URL generation for scanned items."""

from __future__ import annotations


def get_source_url(slug: str, scan_type: str) -> str:
    """Generate source URL for a scanned item.

    Args:
        slug: Package/skill/server identifier.
        scan_type: One of 'skill', 'mcp', 'npm', 'pip', 'openskill'.

    Returns:
        URL string, or empty string if scan_type is unknown.
    """
    urls: dict[str, str] = {
        "skill": f"https://www.clawhub.ai/skill/{slug}",
        "openskill": f"https://www.clawhub.ai/skill/{slug}",
        "mcp": f"https://smithery.ai/server/{slug}",
        "npm": f"https://www.npmjs.com/package/{slug}",
        "pip": f"https://pypi.org/project/{slug}",
    }
    return urls.get(scan_type, "")
