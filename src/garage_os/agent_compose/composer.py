"""F015 T2: ``AgentComposer`` — main compose logic.

Reads SKILL.md frontmatter from ``packs/<id>/skills/<skill>/SKILL.md`` (any
pack — auto-discovered) + ``KnowledgeStore.list_entries(knowledge_type=
KnowledgeType.STYLE)`` → assembles into ``ComposeResult`` with full draft.

Read-only on the source data (INV-F15-1). Writing the draft to packs/ is the
CLI promote path's responsibility (T3, FR-1503), not this module.

Im-1 r2 双层 missing 语义:
- Library (this module): even when ``missing_skills > 0``, returns full draft
  with placeholder content for missing skills (useful for future callers /
  partial preview workflows)
- CLI (T3): strict — exit 1 + no write when ``missing_skills > 0``
"""

from __future__ import annotations

import re
from pathlib import Path

from garage_os.knowledge.knowledge_store import KnowledgeStore
from garage_os.types import KnowledgeType
from garage_os.agent_compose.template_generator import (
    SkillSummary,
    auto_description,
    render,
)
from garage_os.agent_compose.types import AgentDraft, ComposeResult

KEBAB_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
"""kebab-case agent name validator (CON-1504 + spec FR-1501 验证 c)."""

_FRONTMATTER_DESCRIPTION_RE = re.compile(
    r"^description:\s*(.+?)(?=\n[a-zA-Z_]+:|\n---|\Z)",
    re.MULTILINE | re.DOTALL,
)
"""Match ``description: ...`` block in YAML frontmatter; supports both single-line
and multi-line (``description: |`` style)."""


def _parse_skill_description(skill_md_path: Path) -> str:
    """Read SKILL.md frontmatter and extract the ``description`` field value.

    Returns empty string if the file is missing, has no frontmatter, or has no
    description field. Multi-line ``description: |`` block is preserved.
    """
    if not skill_md_path.is_file():
        return ""
    try:
        text = skill_md_path.read_text(encoding="utf-8")
    except OSError:
        return ""
    if not text.startswith("---\n"):
        return ""
    end = text.find("\n---\n", 4)
    if end == -1:
        return ""
    frontmatter = text[4:end]
    m = _FRONTMATTER_DESCRIPTION_RE.search(frontmatter)
    if not m:
        return ""
    desc_block = m.group(1).strip()
    # If it's a YAML pipe block (``description: |``), the body lines are
    # leading-indented; treat the first non-pipe line as the value.
    if desc_block.startswith("|"):
        # YAML | block: skip the first line (just "|") and dedent
        lines = desc_block.split("\n")[1:]
        return "\n".join(line.lstrip() for line in lines)
    return desc_block


def _find_skill_md(packs_root: Path, skill_id: str) -> Path | None:
    """Search packs/*/skills/<skill_id>/SKILL.md across all packs."""
    for pack_dir in packs_root.iterdir():
        if not pack_dir.is_dir():
            continue
        candidate = pack_dir / "skills" / skill_id / "SKILL.md"
        if candidate.is_file():
            return candidate
    return None


def _collect_style_entries(
    knowledge_store: KnowledgeStore,
    *,
    include_style: bool,
) -> tuple[list[tuple[str, str]] | None, int]:
    """Return ([(topic, id), ...], count) or (None, 0) when ``include_style=False``.

    Per FR-1502 + Mi-2 r2: uses ``list_entries(knowledge_type=KnowledgeType.STYLE)``
    full signature.
    """
    if not include_style:
        return None, 0
    try:
        entries = knowledge_store.list_entries(knowledge_type=KnowledgeType.STYLE)
    except Exception:
        return [], 0
    return [(e.topic, e.id) for e in entries], len(entries)


def compose(
    name: str,
    skill_ids: list[str],
    *,
    packs_root: Path,
    knowledge_store: KnowledgeStore,
    target_pack: str = "garage",
    description: str | None = None,
    include_style: bool = True,
) -> ComposeResult:
    """Compose an agent.md draft.

    Args:
        name: kebab-case agent name (raises ``ValueError`` if invalid)
        skill_ids: list of skill_ids to compose (raises ``ValueError`` if empty)
        packs_root: ``packs/`` directory (used to find SKILL.md and validate target_pack)
        knowledge_store: F004 KnowledgeStore for STYLE entries
        target_pack: destination pack id (default 'garage')
        description: optional override for frontmatter description (≥ 50 chars
            recommended; not strictly enforced here, only by CLI gate)
        include_style: whether to include "## Style Alignment" section

    Returns:
        ComposeResult with draft (always populated, even on missing skills) +
        missing_skills + style_count + target_pack_exists.

    Raises:
        ValueError: when ``name`` is not kebab-case or ``skill_ids`` is empty.
    """
    if not skill_ids:
        raise ValueError("skill_ids must contain at least one skill")
    if not KEBAB_NAME_RE.match(name):
        raise ValueError(
            f"agent name '{name}' is not kebab-case (a-z, 0-9, hyphen only)"
        )

    target_pack_exists = (packs_root / target_pack).is_dir()

    skill_summaries: list[SkillSummary] = []
    missing: list[str] = []
    for sid in skill_ids:
        skill_md = _find_skill_md(packs_root, sid)
        if skill_md is None:
            missing.append(sid)
            skill_summaries.append(SkillSummary(skill_id=sid, description_summary=""))
            continue
        desc = _parse_skill_description(skill_md)
        # Take first line / sentence summary
        from garage_os.agent_compose.template_generator import _extract_skill_summary
        summary = _extract_skill_summary(desc)
        skill_summaries.append(SkillSummary(skill_id=sid, description_summary=summary))

    style_entries, style_count = _collect_style_entries(
        knowledge_store, include_style=include_style
    )

    desc_text = description or auto_description(name, skill_ids)
    body = render(
        name,
        skill_summaries,
        description=desc_text,
        style_entries=style_entries,
    )

    draft = AgentDraft(
        name=name,
        description=desc_text,
        target_pack=target_pack,
        body=body,
    )
    return ComposeResult(
        draft=draft,
        missing_skills=missing,
        style_count=style_count,
        target_pack_exists=target_pack_exists,
    )
