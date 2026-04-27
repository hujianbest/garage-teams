"""F014 T2: ``PathRecaller`` — cluster ExperienceRecord by (task_type,
problem_domain) + count skill_ids sequences (FR-1401 + ADR-D14-4 Counter algorithm).

Read-only on ExperienceIndex (INV-F14-1).
Performance budget (CON-1403): 1000 records ≤ 2s on local SSD; algorithm
is O(N) filter + O(N) Counter + O(K log K) top-K sort.

Im-4 r2 ``--skill-id Z`` contract: take the sub-sequence after Z's first
occurrence in each record's ``skill_ids``. If Z is the last item or absent,
that record contributes nothing (skip).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from garage_os.knowledge.experience_index import ExperienceIndex
from garage_os.types import ExperienceRecord
from garage_os.workflow_recall.types import RecallResult, WorkflowAdvisory

DEFAULT_THRESHOLD = 3
"""Spec FR-1401: bucket needs ≥ 3 records to emit advisories."""

DEFAULT_WINDOW = 10
"""Spec FR-1401: take most-recent N records by created_at desc."""

DEFAULT_TOP_K = 3
"""Spec FR-1402: list top-3 sequences."""

DEFAULT_TOP_LESSONS = 3
"""Spec FR-1401: top 3 lessons_learned per advisory."""


@dataclass
class _Bucket:
    """In-memory bucket while clustering."""

    task_type: str | None
    problem_domain: str | None
    records: list[ExperienceRecord]


def _bucket_records(
    records: Iterable[ExperienceRecord],
    *,
    task_type: str | None,
    problem_domain: str | None,
    skill_id: str | None,
) -> list[ExperienceRecord]:
    """Filter records by hint criteria.

    The (task_type, problem_domain) pair scopes the bucket; ``skill_id``
    is applied later during sequence construction (Im-4 r2). Records where
    fields are None pass through (treated as wildcard match).
    """
    out: list[ExperienceRecord] = []
    for r in records:
        if task_type is not None and r.task_type != task_type:
            continue
        if problem_domain is not None and r.problem_domain != problem_domain:
            continue
        if skill_id is not None and skill_id not in (r.skill_ids or []):
            continue
        out.append(r)
    return out


def _take_subsequence(skills: list[str], skill_id: str | None) -> tuple[str, ...] | None:
    """Im-4 r2 contract: when ``--skill-id Z`` is given, take the sub-sequence
    after Z's first occurrence. Return ``None`` if Z is absent or is the
    last item (caller skips this record).
    """
    if skill_id is None:
        return tuple(skills)
    try:
        idx = skills.index(skill_id)
    except ValueError:
        return None  # Z not in this record's seq
    if idx + 1 >= len(skills):
        return None  # Z is last item; subseq empty → skip
    return tuple(skills[idx + 1:])


def recall(
    experience_index: ExperienceIndex,
    *,
    task_type: str | None = None,
    problem_domain: str | None = None,
    skill_id: str | None = None,
    top_k: int = DEFAULT_TOP_K,
    threshold: int = DEFAULT_THRESHOLD,
    window: int = DEFAULT_WINDOW,
) -> RecallResult:
    """Run a workflow recall pass over the ExperienceIndex.

    Args:
        experience_index: F004 store (read-only via list_records, INV-F14-1)
        task_type / problem_domain / skill_id: at least one MUST be non-None
            (CLI handler enforces this; library raises ValueError on empty hint)
        top_k: max advisories returned (default 3)
        threshold: bucket-size minimum (default 3); below → empty advisories
        window: take most-recent N records by created_at desc (default 10)

    Returns:
        RecallResult with advisories sorted by count desc.

    Raises:
        ValueError: when all three filter args are None (no scope).
    """
    if task_type is None and problem_domain is None and skill_id is None:
        raise ValueError("at least one of task_type / problem_domain / skill_id must be non-None")

    all_records = experience_index.list_records()
    bucket_records = _bucket_records(
        all_records,
        task_type=task_type,
        problem_domain=problem_domain,
        skill_id=skill_id,
    )
    bucket_size = len(bucket_records)

    if bucket_size < threshold:
        return RecallResult(
            advisories=[],
            scanned_count=len(all_records),
            bucket_size=bucket_size,
            threshold_met=False,
        )

    # Window: take most-recent N records by created_at desc
    bucket_records.sort(key=lambda r: r.created_at, reverse=True)
    window_records = bucket_records[:window]

    # Build (sequence, [matching records]) pairs; apply Im-4 sub-sequence rule
    seq_to_records: dict[tuple[str, ...], list[ExperienceRecord]] = {}
    for r in window_records:
        seq = _take_subsequence(r.skill_ids or [], skill_id)
        if seq is None:
            continue  # Im-4: skill_id absent or last → skip
        seq_to_records.setdefault(seq, []).append(r)

    # Counter top-K by record count per sequence
    counter = Counter({seq: len(recs) for seq, recs in seq_to_records.items()})
    top_sequences = counter.most_common(top_k)

    advisories: list[WorkflowAdvisory] = []
    for seq, count in top_sequences:
        seq_records = seq_to_records[seq]
        # Im-3 r2: per-sequence avg_duration_seconds (subset of bucket)
        avg_duration = (
            sum(r.duration_seconds for r in seq_records) / len(seq_records)
            if seq_records else 0.0
        )
        # Top lessons per sequence (also per-sequence, not bucket-wide)
        lesson_counter: Counter[str] = Counter()
        for r in seq_records:
            for lesson in (r.lessons_learned or []):
                lesson_counter[lesson] += 1
        top_lessons = lesson_counter.most_common(DEFAULT_TOP_LESSONS)

        advisories.append(WorkflowAdvisory(
            skills=list(seq),
            count=count,
            avg_duration_seconds=avg_duration,
            top_lessons=top_lessons,
            task_type=task_type,
            problem_domain=problem_domain,
        ))

    return RecallResult(
        advisories=advisories,
        scanned_count=len(all_records),
        bucket_size=bucket_size,
        threshold_met=True,
    )
