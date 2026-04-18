"""Publication helpers for reviewed memory candidates."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from garage_os.knowledge.experience_index import ExperienceIndex
from garage_os.knowledge.knowledge_store import KnowledgeStore
from garage_os.memory.candidate_store import CandidateStore
from garage_os.memory.conflict_detector import ConflictDetector
from garage_os.types import ExperienceRecord, KnowledgeEntry, KnowledgeType


class KnowledgePublisher:
    """Publish accepted candidates into formal knowledge/experience stores."""

    def __init__(
        self,
        candidate_store: CandidateStore,
        knowledge_store: KnowledgeStore,
        experience_index: ExperienceIndex,
    ) -> None:
        self._candidate_store = candidate_store
        self._knowledge_store = knowledge_store
        self._experience_index = experience_index
        self._conflict_detector = ConflictDetector(knowledge_store)

    def publish_candidate(
        self,
        candidate_id: str,
        action: str,
        confirmation_ref: str,
        edited_fields: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Publish a reviewed candidate when the action allows publication."""
        if action in {"reject", "defer", "batch_reject", "abandon"}:
            return {"published_id": None, "knowledge_type": None, "action": action}

        candidate = self._candidate_store.retrieve_candidate(candidate_id)
        if candidate is None:
            raise ValueError(f"Candidate not found: {candidate_id}")

        payload = dict(candidate)
        if action == "edit_accept" and edited_fields:
            payload.update(edited_fields)

        candidate_type = payload["candidate_type"]
        if candidate_type == "experience_summary":
            record = self._to_experience_record(payload, confirmation_ref)
            self._experience_index.store(record)
            return {
                "published_id": record.record_id,
                "knowledge_type": None,
                "action": action,
            }

        conflict = self._conflict_detector.detect(
            title=str(payload.get("title", "")),
            tags=list(payload.get("tags", [])),
        )
        supersede_targets: list[str] = []
        if conflict.get("strategy") == "supersede":
            supersede_targets = [str(item) for item in conflict.get("similar_entries", [])]

        entry = self._to_knowledge_entry(payload, confirmation_ref)
        if supersede_targets:
            existing = list(entry.related_decisions)
            for target in supersede_targets:
                if target == entry.id or target in existing:
                    continue
                existing.append(target)
            entry.related_decisions = existing
            entry.front_matter["related_decisions"] = list(existing)
            entry.front_matter["supersedes"] = list(supersede_targets)
        self._knowledge_store.store(entry)
        return {
            "published_id": entry.id,
            "knowledge_type": entry.type,
            "action": action,
        }

    def detect_conflicts(self, candidate_id: str) -> dict[str, Any]:
        """Return conflict suggestions for a candidate before publication."""
        candidate = self._candidate_store.retrieve_candidate(candidate_id)
        if candidate is None:
            raise ValueError(f"Candidate not found: {candidate_id}")
        return self._conflict_detector.detect(
            title=str(candidate.get("title", "")),
            tags=list(candidate.get("tags", [])),
        )

    def _to_knowledge_entry(
        self,
        payload: dict[str, Any],
        confirmation_ref: str,
    ) -> KnowledgeEntry:
        """Convert a candidate payload to a formal knowledge entry."""
        candidate_type = payload["candidate_type"]
        knowledge_type = {
            "decision": KnowledgeType.DECISION,
            "pattern": KnowledgeType.PATTERN,
            "solution": KnowledgeType.SOLUTION,
        }[candidate_type]
        now = datetime.now()
        front_matter = {
            "source_evidence_anchor": payload.get("source_evidence_anchors", [{}])[0]
            if payload.get("source_evidence_anchors")
            else None,
            "confirmation_ref": confirmation_ref,
            "published_from_candidate": payload["candidate_id"],
        }
        return KnowledgeEntry(
            id=payload["candidate_id"],
            type=knowledge_type,
            topic=payload["title"],
            date=now,
            tags=list(payload.get("tags", [])),
            content=payload["content"],
            source_session=payload["session_id"],
            source_artifact=(payload.get("source_artifacts") or [None])[0],
            source_evidence_anchor=front_matter["source_evidence_anchor"],
            confirmation_ref=confirmation_ref,
            published_from_candidate=payload["candidate_id"],
            front_matter=front_matter,
        )

    def _to_experience_record(
        self,
        payload: dict[str, Any],
        confirmation_ref: str,
    ) -> ExperienceRecord:
        """Convert an experience summary candidate to an ExperienceRecord."""
        now = datetime.now()
        source_evidence_anchors = list(payload.get("source_evidence_anchors", []))
        return ExperienceRecord(
            record_id=payload["candidate_id"],
            task_type=payload["task_type"],
            skill_ids=list(payload.get("skill_ids", [])),
            tech_stack=list(payload.get("tech_stack", [])),
            domain=payload["domain"],
            problem_domain=payload["problem_domain"],
            outcome=payload["outcome"],
            duration_seconds=int(payload["duration_seconds"]),
            complexity=payload.get("complexity", "medium"),
            session_id=payload["session_id"],
            artifacts=list(payload.get("source_artifacts", [])),
            key_patterns=list(payload.get("match_reasons", [])),
            recommendations=list(payload.get("recommendations", [])),
            source_evidence_anchors=source_evidence_anchors,
            confirmation_ref=confirmation_ref,
            published_from_candidate=payload["candidate_id"],
            created_at=now,
            updated_at=now,
        )
