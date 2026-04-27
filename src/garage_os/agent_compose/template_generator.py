"""F015 T1: ``template_generator`` — produce agent.md draft string in-memory.

Strictly follows F011 ``blog-writing-agent.md`` + ``code-review-agent.md``
schema (Cr-2 r2 收窄: garage-sample-agent.md 是 F008 简化样本, 不参考). The
7-section schema is:

1. frontmatter (``name`` + ``description`` containing 适用 / 不适用)
2. ``# <Title>`` heading derived from agent name
3. AI-generated comment line (RSK-D15-1: signal "draft, refine via hf-tdd")
4. ``## When to Use``  (from skill SKILL.md frontmatter description prefixes)
5. ``## How It Composes``  (lists each skill's role)
6. ``## Workflow``  (skill_ids in user-given order)
7. ``## Style Alignment``  (KnowledgeType.STYLE entries; omitted with --no-style)

Returns a ``str`` only — does not write to disk (INV-F15-2; only CLI promote
path writes packs/<target>/agents/<name>.md).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass
class _SkillSummary:
    """Internal: parsed SKILL.md frontmatter excerpt for a single skill."""

    skill_id: str
    description_summary: str
    """First non-empty section of the SKILL.md description, truncated per
    ADR-D15-3 切分 rule (≤ 80 chars or first 。/. terminator)."""


def _title_from_name(name: str) -> str:
    """Convert ``config-design-agent`` → ``Config Design Agent`` (Title Case)."""
    return " ".join(word.capitalize() for word in name.split("-"))


def _extract_skill_summary(description: str, max_chars: int = 80) -> str:
    """ADR-D15-3 + Ni-1 r2: take first non-empty section; truncate to first
    sentence terminator (Chinese 。 or English .) or ``max_chars``.

    Handles multi-line YAML ``description: |`` cases (e.g. hv-analysis).
    """
    if not description:
        return ""
    lines = [l.strip() for l in description.splitlines() if l.strip()]
    if not lines:
        return ""
    first = lines[0]
    # Try Chinese 。 first, then English .
    for terminator in ("。", "."):
        idx = first.find(terminator)
        if 0 < idx < max_chars:
            return first[: idx + 1]
    return first[:max_chars] if len(first) > max_chars else first


# ---------- Section renderers ----------


def _render_frontmatter(name: str, description: str) -> str:
    """Render YAML frontmatter block."""
    return f"---\nname: {name}\ndescription: {description}\n---\n"


def _render_header(name: str) -> str:
    """Render ``# Title`` + AI-generated draft notice (RSK-D15-1)."""
    title = _title_from_name(name)
    return (
        f"\n# {title}\n"
        "\n"
        "<!-- AI-generated draft from F015 agent compose; "
        "refine via `garage run hf-test-driven-dev`. -->\n"
    )


def _render_when_to_use(skills: list[_SkillSummary]) -> str:
    """Build ``## When to Use`` from skill summaries."""
    lines = ["", "## When to Use", ""]
    if not skills:
        lines.append("<!-- TODO: 描述适用场景 -->")
        lines.append("")
        lines.append("不适用: <!-- TODO: 描述边界 -->")
        lines.append("")
        return "\n".join(lines)
    lines.append("适用 (从 evidence skill summaries 拼装):")
    lines.append("")
    for s in skills:
        if s.description_summary:
            lines.append(f"- 任务包含 `{s.skill_id}` 场景: {s.description_summary}")
        else:
            lines.append(f"- 任务包含 `{s.skill_id}` 场景 <!-- TODO: 补充 -->")
    lines.append("")
    lines.append("不适用: <!-- TODO: 与相邻 agent 的边界 -->")
    lines.append("")
    return "\n".join(lines)


def _render_how_it_composes(skills: list[_SkillSummary]) -> str:
    """Build ``## How It Composes`` listing each skill's role."""
    lines = ["", "## How It Composes", ""]
    if not skills:
        lines.append("<!-- TODO: 描述各 skill 角色 -->")
        lines.append("")
        return "\n".join(lines)
    lines.append("从 skill_ids 顺序自动推导各 skill 角色 (启发式; 用户可改):")
    lines.append("")
    role_labels = ["基础工作流", "风格 / 后处理", "可选研究层", "辅助 skill", "辅助 skill", "辅助 skill"]
    for i, s in enumerate(skills):
        role = role_labels[i] if i < len(role_labels) else "辅助 skill"
        summary = s.description_summary or "<!-- 描述 -->"
        lines.append(f"{i + 1}. **{role}** (`{s.skill_id}`): {summary}")
    lines.append("")
    return "\n".join(lines)


def _render_workflow(skills: list[_SkillSummary]) -> str:
    """Build ``## Workflow`` listing skill_ids in user-given order."""
    lines = ["", "## Workflow", ""]
    if not skills:
        lines.append("<!-- TODO: 描述执行步骤 -->")
        lines.append("")
        return "\n".join(lines)
    lines.append("调用顺序 (按 --skills 给的次序; 用户可改):")
    lines.append("")
    for i, s in enumerate(skills, start=1):
        lines.append(f"{i}. 调 `{s.skill_id}` skill")
    lines.append("")
    return "\n".join(lines)


def _render_style_alignment(style_entries: list[tuple[str, str]] | None) -> str:
    """Build ``## Style Alignment`` from STYLE entries [(topic, id), ...].

    When ``style_entries`` is None (caller used ``--no-style``), section omitted.
    When list is empty, section uses placeholder TODO.
    """
    if style_entries is None:
        return ""  # --no-style: section omitted entirely
    lines = ["", "## Style Alignment", ""]
    if not style_entries:
        lines.append("<!-- TODO: 添加 KnowledgeType.STYLE entries 后, 自动补充 -->")
        lines.append("")
        return "\n".join(lines)
    lines.append("已识别的 STYLE entries (前 6 个; 多余 see `garage knowledge list --type style`):")
    lines.append("")
    for topic, eid in style_entries[:6]:
        lines.append(f"- `{eid}`: {topic}")
    lines.append("")
    return "\n".join(lines)


# ---------- Public render ----------


def auto_description(name: str, skill_ids: Iterable[str]) -> str:
    """Auto-generate a description with 适用 + 不适用 segments.

    Per CON-1504 + spec FR-1501: ≥ 50 chars; mentions composed skills.
    """
    skills = list(skill_ids)
    skill_list = ", ".join(skills) if skills else "(无 skills)"
    return (
        f"适用于以 {name} 为主旨的任务场景。组合 {skill_list} skill, 与用户的 "
        "KnowledgeType.STYLE 偏好对齐, 半自动产出对齐用户风格的产物。"
        "不适用于其它任务场景 — 详见 packs 中相邻 agent."
    )


def render(
    name: str,
    skill_summaries: list[_SkillSummary],
    *,
    description: str | None = None,
    style_entries: list[tuple[str, str]] | None = None,
) -> str:
    """Generate the agent.md draft string for a (name, skills, style) tuple.

    Args:
        name: kebab-case agent name
        skill_summaries: list of _SkillSummary (one per requested skill_id;
            missing skills should still appear with empty description_summary
            so users can manually fill in)
        description: optional override; if None, auto-generated via ``auto_description``
        style_entries: list of (topic, id) tuples; ``None`` → omit section
            (--no-style); empty list → placeholder TODO

    Returns:
        Full agent.md text (frontmatter + 7 sections per ADR-D15-2 schema).

    Constraints:
        - description ≥ 50 chars (CON-1504)
        - all 7 sections present (or omitted per design rules)
    """
    desc = description or auto_description(name, [s.skill_id for s in skill_summaries])
    sections = [
        _render_frontmatter(name, desc),
        _render_header(name),
        _render_when_to_use(skill_summaries),
        _render_how_it_composes(skill_summaries),
        _render_workflow(skill_summaries),
        _render_style_alignment(style_entries),
    ]
    return "".join(sections).rstrip() + "\n"


# Public re-export of internal type for ``composer.py`` consumption
SkillSummary = _SkillSummary
