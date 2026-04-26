"""F013-A T1: ``SkillSuggestion`` data model + status enum (FR-1301..1305 substrate)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SkillSuggestionStatus(str, Enum):
    """Status enum for ``SkillSuggestion`` (ADR-D13-2: 5 status subdirs)."""

    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    PROMOTED = "promoted"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class SkillSuggestion:
    """A candidate skill the system identified from repeated KnowledgeEntry +
    ExperienceRecord patterns.

    Persisted as JSON under ``.garage/skill-suggestions/<status>/<id>.json``
    (5 status subdirs per ADR-D13-2). Status transitions use ``os.rename`` to
    move the file across subdirs (single atomic syscall).

    Field constraints (spec FR-1303 + FR-1304):
    - ``suggested_description`` ≥ 50 chars (skill-anatomy principle 1)
    - ``rejected_reason`` ≤ 500 chars (RSK-1305)
    - ``tag_bucket`` len ≤ 2, alpha-sorted (FR-1301 cluster rule)
    - ``id`` format: ``sg-<yyyymmdd>-<6 hex>``
    """

    id: str
    suggested_name: str
    suggested_description: str
    problem_domain_key: str
    tag_bucket: list[str]
    evidence_entries: list[str]
    evidence_records: list[str]
    suggested_pack: str
    score: float
    status: SkillSuggestionStatus
    created_at: datetime
    expires_at: datetime
    promoted_to_path: str | None = None
    rejected_reason: str | None = None
    extra: dict = field(default_factory=dict)
