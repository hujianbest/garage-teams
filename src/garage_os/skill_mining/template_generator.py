"""F013-A T3: ``TemplateGenerator`` — produce SKILL.md draft string in-memory.

Strictly follows ``docs/principles/skill-anatomy.md`` 6-section structure
(Im-4 r2: frontmatter + When to Use + Workflow + Output Contract + Red Flags
+ Verification). Returns a ``str`` only — does not write any file (INV-F13-1
+ Cr-4 r2: ``promote`` is the sole writer).

Constraints:
- description ≥ 50 chars (skill-anatomy principle 1)
- total output ≤ 300 lines (skill-anatomy principle 6 main file budget)
"""

from __future__ import annotations

from collections import Counter
from typing import Iterable

from garage_os.knowledge.experience_index import ExperienceIndex
from garage_os.knowledge.knowledge_store import KnowledgeStore
from garage_os.skill_mining.types import SkillSuggestion
from garage_os.types import ExperienceRecord, KnowledgeEntry


def _render_frontmatter(suggestion: SkillSuggestion) -> str:
    return (
        "---\n"
        f"name: {suggestion.suggested_name}\n"
        f"description: {suggestion.suggested_description}\n"
        "---\n"
    )


def _render_header(suggestion: SkillSuggestion) -> str:
    return (
        f"# {suggestion.suggested_name}\n"
        "\n"
        "<!-- AI-generated skeleton from F013-A skill mining; refine via "
        "`garage run hf-test-driven-dev`. -->\n"
    )


def _render_when_to_use(records: list[ExperienceRecord]) -> str:
    """Build `## When to Use` from record `task_type` + `key_patterns`."""
    if not records:
        return (
            "## When to Use\n\n"
            "适用: <!-- TODO: 描述适用场景, 参考 evidence records -->\n\n"
            "不适用: <!-- TODO: 边界条件 -->\n"
        )
    task_types = sorted({r.task_type for r in records if r.task_type})
    pattern_counter = Counter()
    for r in records:
        for p in (r.key_patterns or []):
            pattern_counter[p] += 1
    top_patterns = [p for p, _ in pattern_counter.most_common(5)]
    lines = ["## When to Use", ""]
    if task_types:
        lines.append("适用 (从 evidence 中识别):")
        lines.append("")
        for tt in task_types:
            lines.append(f"- 任务类型 `{tt}`")
        if top_patterns:
            lines.append(f"- 包含模式: {', '.join(f'`{p}`' for p in top_patterns)}")
        lines.append("")
    lines.append("不适用: <!-- TODO: 与相邻 skill 的边界 -->")
    lines.append("")
    return "\n".join(lines)


def _render_workflow(records: list[ExperienceRecord]) -> str:
    """Build `## Workflow` from record `lessons_learned` + `key_patterns`."""
    if not records:
        return "## Workflow\n\n<!-- TODO: 列出执行步骤 -->\n"
    lessons: list[str] = []
    for r in records:
        for ll in (r.lessons_learned or []):
            if ll and ll not in lessons:
                lessons.append(ll)
    lines = ["## Workflow", ""]
    if lessons:
        lines.append("从 evidence 中归纳的执行要点 (refine via hf-test-driven-dev):")
        lines.append("")
        for i, lesson in enumerate(lessons[:8], start=1):
            lines.append(f"{i}. {lesson}")
    else:
        lines.append("<!-- TODO: 描述执行步骤 -->")
    lines.append("")
    return "\n".join(lines)


def _render_output_contract(entries: list[KnowledgeEntry]) -> str:
    """Build `## Output Contract` from knowledge entry `type` + `tags`."""
    if not entries:
        return "## Output Contract\n\n<!-- TODO: 列出产出物结构 -->\n"
    type_counter = Counter(e.type.value for e in entries)
    tag_counter = Counter()
    for e in entries:
        for t in (e.tags or []):
            tag_counter[t] += 1
    lines = ["## Output Contract", ""]
    lines.append("从 evidence 中识别的产出类型 + tags:")
    lines.append("")
    for t, n in type_counter.most_common(3):
        lines.append(f"- 类型 `{t}` × {n}")
    top_tags = [t for t, _ in tag_counter.most_common(6)]
    if top_tags:
        lines.append(f"- 常见 tags: {', '.join(f'`{t}`' for t in top_tags)}")
    lines.append("")
    return "\n".join(lines)


def _render_red_flags(records: list[ExperienceRecord]) -> str:
    """Build `## Red Flags` from record `pitfalls[]`."""
    pitfalls: list[str] = []
    for r in records:
        for p in (r.pitfalls or []):
            if p and p not in pitfalls:
                pitfalls.append(p)
    lines = ["## Red Flags", ""]
    if pitfalls:
        lines.append("从 evidence 中归纳的 pitfalls:")
        lines.append("")
        for p in pitfalls[:6]:
            lines.append(f"- {p}")
    else:
        lines.append("<!-- TODO: 列出常见错误判断 -->")
    lines.append("")
    return "\n".join(lines)


def _render_verification(records: list[ExperienceRecord]) -> str:
    """Build `## Verification` from `source_evidence_anchors[]`."""
    commit_shas: list[str] = []
    test_counts: list[int] = []
    for r in records:
        for anchor in (r.source_evidence_anchors or []):
            if not isinstance(anchor, dict):
                continue
            sha = anchor.get("commit_sha")
            if sha and sha not in commit_shas:
                commit_shas.append(str(sha))
            tc = anchor.get("test_count")
            if isinstance(tc, int):
                test_counts.append(tc)
    lines = ["## Verification", ""]
    if commit_shas or test_counts:
        if commit_shas:
            lines.append("Evidence anchors (commit SHA):")
            for sha in commit_shas[:5]:
                lines.append(f"- {sha}")
        if test_counts:
            avg = sum(test_counts) // len(test_counts)
            lines.append(f"- 平均测试数: {avg} (samples: {len(test_counts)})")
    else:
        lines.append(
            "<!-- TODO: 填 commit SHA / 测试数 (从 evidence anchor schema 取得后) -->"
        )
    lines.append("")
    return "\n".join(lines)


def render(
    suggestion: SkillSuggestion,
    knowledge_store: KnowledgeStore,
    experience_index: ExperienceIndex,
) -> str:
    """Generate the SKILL.md draft string for a SkillSuggestion.

    Reads referenced KnowledgeEntry + ExperienceRecord from the stores
    (read-only, INV-F13-3). Output line count <= 300 (truncated if exceeded
    via fallback minimal template).
    """
    entries: list[KnowledgeEntry] = []
    for eid in suggestion.evidence_entries:
        try:
            e = knowledge_store.retrieve(eid)
        except Exception:
            e = None
        if e is not None:
            entries.append(e)
    records: list[ExperienceRecord] = []
    for rid in suggestion.evidence_records:
        try:
            r = experience_index.retrieve(rid)
        except Exception:
            r = None
        if r is not None:
            records.append(r)

    sections: list[str] = [
        _render_frontmatter(suggestion),
        _render_header(suggestion),
        _render_when_to_use(records),
        _render_workflow(records),
        _render_output_contract(entries),
        _render_red_flags(records),
        _render_verification(records),
    ]
    output = "\n".join(sections)

    # CON: ≤ 300 lines (skill-anatomy principle 6 main file budget)
    line_count = output.count("\n")
    if line_count > 300:
        # Truncate with explicit warning instead of bloat
        lines = output.splitlines()[:295]
        lines.append("")
        lines.append("<!-- TRUNCATED: original draft exceeded 300-line budget; "
                     "refine manually via hf-test-driven-dev -->")
        output = "\n".join(lines) + "\n"

    return output


def render_minimal(suggestion: SkillSuggestion) -> str:
    """Robust fallback when evidence is missing or stores are unavailable.

    Used by ``garage skill suggest --id`` when the suggestion file references
    entries / records that have since been deleted.
    """
    return (
        _render_frontmatter(suggestion)
        + "\n"
        + _render_header(suggestion)
        + "\n"
        "## When to Use\n\n"
        "<!-- TODO: 描述适用场景 -->\n\n"
        "不适用: <!-- TODO: 与相邻 skill 的边界 -->\n\n"
        "## Workflow\n\n"
        "<!-- TODO: 描述执行步骤 -->\n\n"
        "## Output Contract\n\n"
        "<!-- TODO: 列出产出物结构 -->\n\n"
        "## Red Flags\n\n"
        "<!-- TODO: 列出常见错误判断 -->\n\n"
        "## Verification\n\n"
        "<!-- TODO: 填 commit SHA / 测试数 -->\n"
    )
