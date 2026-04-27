"""F016 T1: ``templates.py`` — load STYLE template files from packs/garage/templates/.

Each STYLE template is a markdown file with structured ``- prefix: content``
lines per FR-1604. ``parse_style_template`` reads the file and returns a list
of ``(topic, content)`` tuples ready for ``KnowledgeStore.store``.
"""

from __future__ import annotations

import re
from pathlib import Path

# Match lines like:
#   - prefer-functional-python: Prefer functional patterns ...
# Captures (prefix=topic, content)
_STYLE_LINE_RE = re.compile(r"^\s*-\s+`?([a-z0-9-]+)`?:\s*(.+?)\s*$")

SUPPORTED_LANGUAGES = ("python", "typescript", "markdown")
"""Im-3 r2: lowercase only; reject other lang values at CLI layer."""


def template_path(packs_root: Path, lang: str) -> Path:
    """Return the path to a STYLE template for ``lang``."""
    return packs_root / "garage" / "templates" / "style-templates" / f"{lang}.md"


def parse_style_template(path: Path) -> list[tuple[str, str]]:
    """Parse a STYLE template; return list of (topic, content) tuples.

    Returns empty list when the file is missing, empty, or has no parseable
    lines. Lines that don't match the ``- prefix: content`` pattern are
    silently skipped (header / explanation prose).

    Args:
        path: Template file path

    Returns:
        list of (topic, content); topic is the kebab-case prefix, content is
        the human-readable description after the colon.
    """
    if not path.is_file():
        return []
    out: list[tuple[str, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    for line in text.splitlines():
        match = _STYLE_LINE_RE.match(line)
        if match:
            topic = match.group(1).strip()
            content = match.group(2).strip()
            if topic and content:
                out.append((topic, content))
    return out
