"""F016 T1: ``MemoryStatus`` + ``IngestSummary`` data model (FR-1601 + FR-1602)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class MemoryStatus:
    """Returned by ``memory_activation.status_summary`` for ``garage memory status``.

    Per FR-1601 + Cr-5 r2: ``last_extraction`` is computed via
    ``max(record.created_at for record in ExperienceIndex.list_records())``,
    or ``None`` when no records exist (i.e. "never").
    """

    extraction_enabled: bool

    knowledge_entry_count: int
    """Total KnowledgeEntry, includes STYLE (Im-1 r2)."""

    experience_record_count: int

    candidate_count: int
    """Pending candidates awaiting review (F003 candidate_store status='proposed')."""

    last_extraction: datetime | None
    """Latest ``ExperienceRecord.created_at`` across all records, None if empty."""


@dataclass
class IngestSummary:
    """Returned by ``ingest.ingest_*`` library functions.

    ``written`` counts new records / entries actually written to disk
    (post-dedup). ``skipped`` counts items deduped or unparseable. ``dry_run``
    is True if the call was ``--dry-run`` (in which case nothing was written
    regardless of ``written``).
    """

    source: str
    """e.g. 'reviews' / 'git-log' / 'style-template:python'."""

    written: int
    skipped: int
    dry_run: bool = False
    errors: list[str] | None = None
