"""F014 T1: ``RecallResult`` + ``WorkflowAdvisory`` data model (FR-1401 substrate)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class WorkflowAdvisory:
    """A single advisory: a (skills sequence) frequency hit in a (task_type,
    problem_domain) bucket.

    Im-3 r2 contract: ``avg_duration_seconds`` is **per-sequence mean** —
    mean of ``duration_seconds`` over the records whose ``skill_ids`` match
    this advisory's ``skills`` sequence (a subset of the bucket), not a
    bucket-wide mean.
    """

    skills: list[str]
    """ordered skill_ids sequence (e.g. ['hf-specify', 'hf-design', ...])"""

    count: int
    """frequency in bucket (records matching this skills sequence)"""

    avg_duration_seconds: float
    """per-sequence mean of duration_seconds (Im-3 r2)"""

    top_lessons: list[tuple[str, int]] = field(default_factory=list)
    """[(lesson, freq)] top 3 lessons_learned from records matching this sequence"""

    task_type: str | None = None

    problem_domain: str | None = None


@dataclass
class RecallResult:
    """Returned by ``PathRecaller.recall``.

    ``advisories`` is sorted by ``count`` descending and capped at the
    requested ``top_k`` (default 3). ``threshold_met`` indicates whether
    the matched bucket size reached the configured threshold (default 3);
    when False, ``advisories`` is empty regardless of bucket content.
    """

    advisories: list[WorkflowAdvisory] = field(default_factory=list)
    scanned_count: int = 0
    """total ExperienceRecord scanned across all buckets"""

    bucket_size: int = 0
    """records in the matched (task_type, problem_domain) bucket before threshold"""

    threshold_met: bool = False
    """bucket_size >= configured THRESHOLD (default 3)"""
