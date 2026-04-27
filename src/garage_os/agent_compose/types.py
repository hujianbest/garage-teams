"""F015 T1: ``AgentDraft`` + ``ComposeResult`` data model (FR-1501 substrate)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AgentDraft:
    """An in-memory agent.md draft (FR-1501 output type).

    The ``body`` field is the full agent.md text (frontmatter + 7 sections per
    ADR-D15-2 schema referencing F011's blog-writing-agent + code-review-agent
    structure; ``garage-sample-agent`` is intentionally excluded from the
    template reference set per Cr-2 r2).
    """

    name: str
    """kebab-case agent name (e.g. 'config-design-agent')."""

    description: str
    """≥ 50 chars, contains 适用 + 不适用 (CON-1504; mirrors skill-anatomy 原则 1)."""

    target_pack: str
    """destination pack id (default 'garage')."""

    body: str
    """full agent.md draft string (frontmatter + 7 sections)."""


@dataclass
class ComposeResult:
    """Library-layer compose result (FR-1501 + Im-1 r2 双层 missing 语义).

    Even when ``missing_skills`` is non-empty, ``draft`` is still populated with
    placeholder content for missing skills — useful for diagnostic / partial-
    preview workflows. The CLI layer (FR-1503) is stricter: any ``missing_skills``
    causes ``exit 1`` without writing to disk.
    """

    draft: AgentDraft

    missing_skills: list[str] = field(default_factory=list)
    """skill_ids not found in any packs/<id>/skills/<skill>/SKILL.md."""

    style_count: int = 0
    """number of STYLE entries pulled from KnowledgeStore (FR-1502)."""

    target_pack_exists: bool = False
    """whether packs/<target_pack>/ exists on disk (CLI uses this for exit 1 gating)."""
