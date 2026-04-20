"""Inject Garage install marker fields into SKILL.md / agent.md front matter.

Implements F007 FR-708 + design D7 §10.4 / ADR-D7-2.

Two source kinds:

- ``"skill"``: source MUST already have YAML front matter (per
  ``docs/principles/skill-anatomy.md`` SKILL.md must declare ``name`` +
  ``description``); missing front matter is a hard error
  (``MalformedFrontmatterError``).
- ``"agent"``: source MAY lack front matter; if missing, inject a minimal
  one with just the marker fields. If present, append the marker fields
  the same way as for skills.

Idempotency contract (T3 测试种子关键边界 5):

- Re-injecting an already-marked source MUST be a byte-level no-op. This
  guarantees ``garage init`` can be re-run safely without the marker fields
  stacking up.

Implementation note:
    We avoid full YAML parse/dump because that would re-quote / reorder
    arbitrary keys and break SHA-256 stability under FR-705 / NFR-702.
    Instead we operate on the front matter text block directly: split on
    the first two ``---`` delimiters, append two key-value lines if absent,
    rejoin. Existing field values (including any ``installed_by`` field
    set to a different value) are left untouched on re-injection — see
    ``_lines_already_have_marker``.
"""

from __future__ import annotations

from typing import Literal

SourceKind = Literal["skill", "agent"]

FRONTMATTER_DELIMITER = "---"
MARKER_BY = "installed_by: garage"
MARKER_PACK_PREFIX = "installed_pack: "


class MalformedFrontmatterError(ValueError):
    """Raised for SKILL.md sources that lack required YAML front matter."""


def inject(content: str, pack_id: str, source_kind: SourceKind) -> str:
    """Return ``content`` with Garage install marker fields ensured.

    Args:
        content: Source file body (UTF-8 text).
        pack_id: pack id to record in ``installed_pack``.
        source_kind: ``"skill"`` or ``"agent"`` per FR-708 / D7 §10.4.

    Raises:
        MalformedFrontmatterError: when ``source_kind == "skill"`` and the
            source does not start with a YAML front matter block.
    """
    head, body, has_frontmatter = _split_frontmatter(content)

    if not has_frontmatter:
        if source_kind == "skill":
            raise MalformedFrontmatterError(
                f"SKILL.md source has no YAML front matter; pack_id={pack_id!r}. "
                "SKILL.md must declare 'name' and 'description' per "
                "docs/principles/skill-anatomy.md."
            )
        # agent path: synthesize a minimal front matter block.
        return _build_minimal_frontmatter(pack_id) + content

    # head is the front matter body (between the two ---), body is the rest.
    if _lines_already_have_marker(head, pack_id):
        return content
    new_head = _ensure_marker_lines(head, pack_id)
    return f"---\n{new_head}\n---\n{body}"


def extract_marker(content: str) -> dict[str, str] | None:
    """Return the installed_by/installed_pack fields if present, else None."""
    head, _body, has_frontmatter = _split_frontmatter(content)
    if not has_frontmatter:
        return None
    by_value: str | None = None
    pack_value: str | None = None
    for line in head.splitlines():
        stripped = line.strip()
        if stripped.startswith("installed_by:"):
            by_value = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("installed_pack:"):
            pack_value = stripped.split(":", 1)[1].strip()
    if by_value is None and pack_value is None:
        return None
    result: dict[str, str] = {}
    if by_value is not None:
        result["installed_by"] = by_value
    if pack_value is not None:
        result["installed_pack"] = pack_value
    return result


def _split_frontmatter(content: str) -> tuple[str, str, bool]:
    """Split ``content`` into (frontmatter_text, body, has_frontmatter).

    Front matter is recognized as a block bounded by two ``---`` lines, the
    first of which must be the very first line of the file.
    """
    if not content.startswith(FRONTMATTER_DELIMITER + "\n"):
        return "", content, False
    rest = content[len(FRONTMATTER_DELIMITER) + 1 :]  # skip "---\n"
    end_marker = f"\n{FRONTMATTER_DELIMITER}\n"
    end_idx = rest.find(end_marker)
    if end_idx == -1:
        # No closing delimiter → treat as no front matter rather than swallow body.
        return "", content, False
    head = rest[:end_idx]
    body = rest[end_idx + len(end_marker) :]
    return head, body, True


def _lines_already_have_marker(head: str, pack_id: str) -> bool:
    """True iff both marker fields are present with matching pack_id."""
    has_by = False
    has_pack = False
    expected_pack_line = f"installed_pack: {pack_id}"
    for line in head.splitlines():
        stripped = line.strip()
        if stripped == MARKER_BY:
            has_by = True
        elif stripped == expected_pack_line:
            has_pack = True
    return has_by and has_pack


def _ensure_marker_lines(head: str, pack_id: str) -> str:
    """Append marker lines to front matter body if missing, preserving order."""
    lines = head.splitlines()
    have_by = any(line.strip() == MARKER_BY for line in lines)
    have_pack = any(
        line.strip().startswith(MARKER_PACK_PREFIX) for line in lines
    )
    if not have_by:
        lines.append(MARKER_BY)
    if not have_pack:
        lines.append(f"{MARKER_PACK_PREFIX}{pack_id}")
    return "\n".join(lines)


def _build_minimal_frontmatter(pack_id: str) -> str:
    """For agent.md sources lacking front matter."""
    return (
        f"---\n"
        f"{MARKER_BY}\n"
        f"{MARKER_PACK_PREFIX}{pack_id}\n"
        f"---\n"
    )
