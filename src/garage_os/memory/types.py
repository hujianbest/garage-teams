"""Core types for Garage memory candidate storage."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


ALLOWED_CANDIDATE_TYPES = {
    "decision",
    "pattern",
    "solution",
    "experience_summary",
}

PENDING_REVIEW_STATUSES = {"pending_review"}
MAX_PENDING_REVIEW_CANDIDATES = 5


@dataclass
class CandidateDraft:
    """Candidate draft persisted before formal publication."""

    candidate_id: str
    candidate_type: str
    session_id: str
    source_artifacts: list[str]
    match_reasons: list[str]
    status: str
    priority_score: float
    title: str
    summary: str
    content: str
    schema_version: str = "1"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CandidateDraft":
        """Build and validate a draft from a raw mapping."""
        candidate_type = data["candidate_type"]
        if candidate_type not in ALLOWED_CANDIDATE_TYPES:
            raise ValueError(
                f"Invalid candidate_type '{candidate_type}'. "
                f"Allowed values: {sorted(ALLOWED_CANDIDATE_TYPES)}"
            )

        return cls(
            schema_version=str(data.get("schema_version", "1")),
            candidate_id=data["candidate_id"],
            candidate_type=candidate_type,
            session_id=data["session_id"],
            source_artifacts=list(data.get("source_artifacts", [])),
            match_reasons=list(data.get("match_reasons", [])),
            status=data.get("status", "pending_review"),
            priority_score=float(data.get("priority_score", 0.0)),
            title=data["title"],
            summary=data["summary"],
            content=data["content"],
        )

    def to_front_matter(self) -> dict[str, Any]:
        """Convert to front matter payload."""
        return {
            "schema_version": self.schema_version,
            "candidate_id": self.candidate_id,
            "candidate_type": self.candidate_type,
            "session_id": self.session_id,
            "source_artifacts": self.source_artifacts,
            "match_reasons": self.match_reasons,
            "status": self.status,
            "priority_score": self.priority_score,
            "title": self.title,
            "summary": self.summary,
        }

    @classmethod
    def from_front_matter(
        cls,
        front_matter: dict[str, Any],
        content: str,
    ) -> "CandidateDraft":
        """Convert front matter + body back to a draft."""
        payload = dict(front_matter)
        payload["content"] = content
        return cls.from_dict(payload)


@dataclass
class CandidateBatch:
    """A batch of extracted candidates awaiting review."""

    batch_id: str
    session_id: str
    status: str
    trigger: str
    candidate_ids: list[str]
    truncated_count: int
    evaluation_summary: str
    created_at: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CandidateBatch":
        """Build and validate a batch from a raw mapping."""
        candidate_ids = list(data.get("candidate_ids", []))
        status = data.get("status", "pending_review")
        if status in PENDING_REVIEW_STATUSES and len(candidate_ids) > MAX_PENDING_REVIEW_CANDIDATES:
            raise ValueError(
                f"Pending-review batches must contain at most "
                f"{MAX_PENDING_REVIEW_CANDIDATES} candidates"
            )

        return cls(
            batch_id=data["batch_id"],
            session_id=data["session_id"],
            status=status,
            trigger=data["trigger"],
            candidate_ids=candidate_ids,
            truncated_count=int(data.get("truncated_count", 0)),
            evaluation_summary=data["evaluation_summary"],
            created_at=data["created_at"],
            metadata=dict(data.get("metadata", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable mapping."""
        return {
            "batch_id": self.batch_id,
            "session_id": self.session_id,
            "status": self.status,
            "trigger": self.trigger,
            "candidate_ids": self.candidate_ids,
            "truncated_count": self.truncated_count,
            "evaluation_summary": self.evaluation_summary,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


@dataclass
class ConfirmationRecord:
    """Review resolution for a candidate batch."""

    batch_id: str
    resolution: str
    actions: list[dict[str, Any]]
    resolved_at: str
    surface: str
    approver: str
    schema_version: str = "1"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConfirmationRecord":
        """Build a confirmation record from a raw mapping."""
        return cls(
            schema_version=str(data.get("schema_version", "1")),
            batch_id=data["batch_id"],
            resolution=data["resolution"],
            actions=list(data.get("actions", [])),
            resolved_at=data["resolved_at"],
            surface=data["surface"],
            approver=data["approver"],
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable mapping."""
        return {
            "schema_version": self.schema_version,
            "batch_id": self.batch_id,
            "resolution": self.resolution,
            "actions": self.actions,
            "resolved_at": self.resolved_at,
            "surface": self.surface,
            "approver": self.approver,
        }

