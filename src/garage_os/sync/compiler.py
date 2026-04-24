"""F010 sync compiler: top-N knowledge + recent experience → CompiledSection.

Implements FR-1007 + ADR-D10-4 (constants) + ADR-D10-5 (markdown structure).

Key design decisions (ADR-D10-4):
- KNOWLEDGE_TOP_N = 12 (4 per kind: decision / solution / pattern)
- EXPERIENCE_TOP_M = 5 (recent records)
- SIZE_BUDGET_BYTES = 16384 (~3.2x Claude Code's recommended 5KB; gives long-form
  knowledge entries headroom while staying within typical host conversation context window)
- Ranking: decision > solution > pattern; same-kind by mtime DESC; experience separately by mtime DESC
- Truncation: per-entry ≤ 200 char; total ≤ budget; emit stderr warn on truncation
- Empty kinds omitted (no `### Recent Patterns` section if 0 patterns)

Scaling complexity (ADR-D10-4 r3 Consequences): top-N + top-M are constants;
sync compiler processing time independent of total knowledge base size (200+ entries
still selects only 17). NFR-1004 ≤ 5s budget remains slack at scale.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import IO

from garage_os.knowledge.experience_index import ExperienceIndex
from garage_os.knowledge.knowledge_store import KnowledgeStore
from garage_os.storage.file_storage import FileStorage
from garage_os.types import ExperienceRecord, KnowledgeEntry, KnowledgeType

# F010 ADR-D10-4 constants
KNOWLEDGE_TOP_N: int = 12  # 4 per kind × 3 kinds
EXPERIENCE_TOP_M: int = 5
SIZE_BUDGET_BYTES: int = 16384  # 16 KB
MAX_ENTRY_CHARS: int = 200  # per-entry truncation
PER_KIND_TOP: int = 4  # 4 each of decision / solution / pattern (12 total)


@dataclass
class CompiledSection:
    """Output of compile_garage_section."""

    body_markdown: str  # Garage section body (without HTML markers)
    knowledge_count: int
    experience_count: int
    knowledge_kinds: list[str] = field(default_factory=list)
    size_bytes: int = 0
    truncated_count: int = 0  # entries dropped due to budget

    @property
    def is_empty(self) -> bool:
        return self.knowledge_count == 0 and self.experience_count == 0


def compile_garage_section(
    workspace_root: Path,
    *,
    stderr: IO[str] | None = None,
    knowledge_top_n: int = KNOWLEDGE_TOP_N,
    experience_top_m: int = EXPERIENCE_TOP_M,
    size_budget_bytes: int = SIZE_BUDGET_BYTES,
) -> CompiledSection:
    """Compile top-N knowledge + recent experience into a Garage markdown section.

    Args:
        workspace_root: project root containing .garage/
        stderr: stream for budget-truncation warnings (default sys.stderr)
        knowledge_top_n: total knowledge entries cap (default 12, 4 per kind)
        experience_top_m: experience records cap (default 5)
        size_budget_bytes: total body byte budget (default 16384)

    Returns:
        CompiledSection with markdown body + counts + size + truncation info.
        is_empty=True when .garage/knowledge/ and .garage/experience/ both empty.
    """
    err = stderr if stderr is not None else sys.stderr
    garage_dir = workspace_root / ".garage"
    storage = FileStorage(garage_dir)
    knowledge_store = KnowledgeStore(storage)
    experience_index = ExperienceIndex(storage)

    # Per-kind top selection (ADR-D10-4 ranking)
    selected_knowledge: dict[str, list[KnowledgeEntry]] = {
        "decision": _top_n_by_type(knowledge_store, KnowledgeType.DECISION, PER_KIND_TOP),
        "solution": _top_n_by_type(knowledge_store, KnowledgeType.SOLUTION, PER_KIND_TOP),
        "pattern": _top_n_by_type(knowledge_store, KnowledgeType.PATTERN, PER_KIND_TOP),
    }
    selected_experience: list[ExperienceRecord] = _top_m_experience(
        experience_index, experience_top_m
    )

    # Render markdown sections per kind (skip empty kinds)
    sections: list[str] = []
    knowledge_count = 0
    experience_count = 0
    knowledge_kinds: list[str] = []
    truncated = 0
    accumulated_bytes = 0

    # ADR-D10-5 ordering: decision > solution > pattern > experience
    kind_order = ["decision", "solution", "pattern"]
    kind_titles = {
        "decision": "Recent Decisions",
        "solution": "Recent Solutions",
        "pattern": "Recent Patterns",
    }

    for kind in kind_order:
        entries = selected_knowledge[kind]
        if not entries:
            continue
        # Render this kind's section
        section_lines = [f"### {kind_titles[kind]} ({len(entries)})", ""]
        added_in_kind = 0
        for entry in entries:
            entry_md = _render_knowledge_entry_markdown(entry)
            entry_size = len(entry_md.encode("utf-8"))
            # Budget gate: if adding this entry breaks budget, truncate
            if accumulated_bytes + entry_size > size_budget_bytes:
                truncated += len(entries) - added_in_kind
                break
            section_lines.append(entry_md)
            accumulated_bytes += entry_size
            added_in_kind += 1
        if added_in_kind > 0:
            sections.append("\n".join(section_lines))
            knowledge_count += added_in_kind
            knowledge_kinds.append(kind)

    # Experience section
    if selected_experience:
        section_lines = [f"### Recent Experiences ({len(selected_experience)})", ""]
        added_exp = 0
        for record in selected_experience:
            record_md = _render_experience_record_markdown(record)
            record_size = len(record_md.encode("utf-8"))
            if accumulated_bytes + record_size > size_budget_bytes:
                truncated += len(selected_experience) - added_exp
                break
            section_lines.append(record_md)
            accumulated_bytes += record_size
            added_exp += 1
        if added_exp > 0:
            sections.append("\n".join(section_lines))
            experience_count = added_exp

    if truncated > 0:
        print(
            f"Truncated {truncated} entries due to size budget ({size_budget_bytes} bytes)",
            file=err,
        )

    # Build full body (header + sections + footer)
    header = (
        "## Garage Knowledge Context\n\n"
        "> 本段由 `garage sync` 自动写入. 不要手动编辑 marker 之间内容; "
        "编辑请用 `garage knowledge add` / `garage memory review`.\n"
    )
    footer = (
        f"\n---\n\n"
        f"_Synced at {_now_iso()} by `garage sync` "
        f"({knowledge_count} knowledge + {experience_count} experience, "
        f"{accumulated_bytes}B / {size_budget_bytes}B budget)_\n"
    )

    if knowledge_count == 0 and experience_count == 0:
        body = header + "\n_No Garage knowledge or experience yet. Use `garage knowledge add` to start._\n" + footer
    else:
        body = header + "\n" + "\n\n".join(sections) + footer

    return CompiledSection(
        body_markdown=body,
        knowledge_count=knowledge_count,
        experience_count=experience_count,
        knowledge_kinds=knowledge_kinds,
        size_bytes=len(body.encode("utf-8")),
        truncated_count=truncated,
    )


def _top_n_by_type(
    store: KnowledgeStore, ktype: KnowledgeType, n: int
) -> list[KnowledgeEntry]:
    """Get top-N knowledge entries of a kind, sorted by date DESC."""
    entries = store.list_entries(knowledge_type=ktype)
    # Sort by date DESC (most recent first)
    entries.sort(key=lambda e: e.date, reverse=True)
    return entries[:n]


def _top_m_experience(
    index: ExperienceIndex, m: int
) -> list[ExperienceRecord]:
    """Get top-M experience records by record_id DESC (proxy for mtime since
    record_id is timestamp-prefixed in F003 convention)."""
    records = index.list_records()
    # Sort by record_id DESC (record_id contains ISO timestamp prefix per F003)
    records.sort(key=lambda r: r.record_id, reverse=True)
    return records[:m]


def _render_knowledge_entry_markdown(entry: KnowledgeEntry) -> str:
    """Render one knowledge entry as a markdown bullet (≤ MAX_ENTRY_CHARS chars total)."""
    summary = _truncate_to(entry.content.strip().split("\n")[0], MAX_ENTRY_CHARS)
    date_str = entry.date.strftime("%Y-%m-%d") if isinstance(entry.date, datetime) else str(entry.date)
    source = entry.source_session or entry.source_artifact or "n/a"
    return (
        f"- **{entry.topic}** ({date_str})  \n"
        f"  {summary}  \n"
        f"  Source: {source}"
    )


def _render_experience_record_markdown(record: ExperienceRecord) -> str:
    """Render one experience record as a markdown bullet."""
    takeaway = "; ".join(record.lessons_learned[:2]) if record.lessons_learned else record.problem_domain or record.task_type
    takeaway = _truncate_to(takeaway, MAX_ENTRY_CHARS)
    return (
        f"- **{record.task_type}** ({record.outcome})  \n"
        f"  {takeaway}  \n"
        f"  Pack: {','.join(record.skill_ids[:2]) if record.skill_ids else 'n/a'}"
    )


def _truncate_to(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1] + "…"


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0, tzinfo=None).isoformat() + "Z"
