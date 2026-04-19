"""Publication helpers for reviewed memory candidates."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from garage_os.knowledge.experience_index import ExperienceIndex
from garage_os.knowledge.knowledge_store import KnowledgeStore
from garage_os.memory.candidate_store import CandidateStore
from garage_os.memory.conflict_detector import ConflictDetector
from garage_os.types import ExperienceRecord, KnowledgeEntry, KnowledgeType


class PublicationIdentityGenerator:
    """Decide deterministic publication id from candidate identity (F004 ADR-401).

    NFR-401: same input must yield same id across N calls (deterministic, no
    randomness, no side-effects). Default implementation passes the candidate
    id through verbatim, preserving F003 v1 published-data layout so that no
    on-disk migration is required when v1.1 ships.

    If a future cycle wants to switch to namespaced or hashed ids, only the
    two ``derive_*`` methods change; callers stay untouched.
    """

    def derive_knowledge_id(
        self, candidate_id: str, knowledge_type: KnowledgeType
    ) -> str:
        """Derive the formal KnowledgeEntry id for a candidate.

        ``knowledge_type`` is part of the contract so future strategies can
        namespace ids per type, but the v1.1 default ignores it.
        """
        return candidate_id

    def derive_experience_id(self, candidate_id: str) -> str:
        """Derive the formal ExperienceRecord id for a candidate."""
        return candidate_id


class KnowledgePublisher:
    """Publish accepted candidates into formal knowledge/experience stores."""

    # F004 §11.2.1: front_matter keys outside the KnowledgeEntry dataclass
    # that publisher must carry over from the existing entry on update,
    # otherwise KnowledgeStore.store rebuilds front_matter from dataclass
    # fields and silently drops the v1 supersede chain.
    PRESERVED_FRONT_MATTER_KEYS: tuple[str, ...] = (
        "supersedes",
        "related_decisions",
    )

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
        self._id_generator = PublicationIdentityGenerator()

    VALID_CONFLICT_STRATEGIES = {"coexist", "supersede", "abandon"}

    @staticmethod
    def _merge_unique(base: list[str], extra: list[str]) -> list[str]:
        """Merge ``extra`` into ``base`` preserving order and removing duplicates.

        Used to carry over v1 supersede / related_decisions history without
        losing newly-added entries from the current publication round.
        """
        seen = set(base)
        merged = list(base)
        for item in extra:
            if item not in seen:
                merged.append(item)
                seen.add(item)
        return merged

    def _validate_conflict_strategy(self, value: Optional[str]) -> None:
        """Reject invalid conflict_strategy values at the publish_candidate entry.

        F004 FR-402 / ADR-402: validation must happen before any business
        branch (action early-return, candidate retrieval, conflict detection),
        so callers learn about garbage strategy values immediately even when
        no similar published knowledge exists.

        ``None`` keeps the existing semantics: callers may omit the value when
        they know there is no conflict; the conflict-branch check still kicks
        in if similar entries are detected later.
        """
        if value is None:
            return
        if value not in self.VALID_CONFLICT_STRATEGIES:
            raise ValueError(
                f"Invalid conflict_strategy '{value}'. "
                f"Allowed: {sorted(self.VALID_CONFLICT_STRATEGIES)}"
            )

    def publish_candidate(
        self,
        candidate_id: str,
        action: str,
        confirmation_ref: str,
        edited_fields: Optional[dict[str, Any]] = None,
        conflict_strategy: Optional[str] = None,
    ) -> dict[str, Any]:
        """Publish a reviewed candidate when the action allows publication."""
        # F004 FR-402 / ADR-402: validate conflict_strategy at the entry,
        # before any early-return or storage I/O.
        self._validate_conflict_strategy(conflict_strategy)

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
            # F004 FR-401 / §11.2 path A: deterministic id + store-or-update
            # so repeated publication updates the existing record in place
            # instead of overwriting silently.
            record.record_id = self._id_generator.derive_experience_id(
                payload["candidate_id"]
            )
            existing_record = self._experience_index.retrieve(record.record_id)
            if existing_record is None:
                self._experience_index.store(record)
            else:
                # ExperienceIndex.update bumps updated_at and re-stores; created_at
                # is preserved by carrying it over from the existing record.
                record.created_at = existing_record.created_at
                self._experience_index.update(record)
            return {
                "published_id": record.record_id,
                "knowledge_type": None,
                "action": action,
            }

        # F004 FR-401 / §10.1 / §11.2 path B: build entry first so we can
        # derive the publication id and run self-conflict short-circuit.
        entry = self._to_knowledge_entry(payload, confirmation_ref)
        entry.id = self._id_generator.derive_knowledge_id(
            payload["candidate_id"], entry.type
        )

        conflict = self._conflict_detector.detect(
            title=str(payload.get("title", "")),
            tags=list(payload.get("tags", [])),
        )
        similar_entries = [str(item) for item in conflict.get("similar_entries", [])]
        # F004 §10.1.1 self-conflict short-circuit: ConflictDetector matches
        # by title/tags and may surface the entry we are about to update.
        # Strip ids equal to our own publication id before deciding whether
        # to require an explicit conflict_strategy from the caller.
        similar_entries = [item for item in similar_entries if item != entry.id]
        if similar_entries:
            if conflict_strategy is None:
                raise ValueError(
                    "Similar published knowledge detected; "
                    "caller must pass conflict_strategy=coexist|supersede|abandon "
                    "(FR-304 requires explicit user choice)."
                )
            # F004 FR-402: redundant strategy validation removed; entry-level
            # _validate_conflict_strategy already enforced the allowed set.
            if conflict_strategy == "abandon":
                return {
                    "published_id": None,
                    "knowledge_type": None,
                    "action": action,
                    "conflict_strategy": "abandon",
                }

        if similar_entries and conflict_strategy == "supersede":
            existing = list(entry.related_decisions)
            for target in similar_entries:
                if target == entry.id or target in existing:
                    continue
                existing.append(target)
            entry.related_decisions = existing
            entry.front_matter["related_decisions"] = list(existing)
            entry.front_matter["supersedes"] = list(similar_entries)

        # F004 FR-401 / FR-405 / §10.1 / §11.2.1: store-or-update decision
        # plus PRESERVED_FRONT_MATTER_KEYS carry-over so v1 supersede chain
        # and related_decisions survive v1.1 re-publication.
        existing_entry = self._knowledge_store.retrieve(entry.type, entry.id)
        if existing_entry is None:
            self._knowledge_store.store(entry)
        else:
            entry.related_decisions = self._merge_unique(
                list(existing_entry.related_decisions),
                list(entry.related_decisions),
            )
            for key in self.PRESERVED_FRONT_MATTER_KEYS:
                existing_value = existing_entry.front_matter.get(key)
                if not existing_value:
                    continue
                current_value = entry.front_matter.get(key) or []
                entry.front_matter[key] = self._merge_unique(
                    list(existing_value),
                    list(current_value),
                )
            entry.version = existing_entry.version
            self._knowledge_store.update(entry)
        return {
            "published_id": entry.id,
            "knowledge_type": entry.type,
            "action": action,
            "conflict_strategy": conflict_strategy if similar_entries else None,
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
        anchors = payload.get("source_evidence_anchors") or []
        first_anchor = anchors[0] if anchors else None
        front_matter = {
            "source_evidence_anchor": first_anchor,
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
            task_type=str(payload.get("task_type") or "skill_execution"),
            skill_ids=list(payload.get("skill_ids", [])),
            tech_stack=list(payload.get("tech_stack", [])),
            domain=str(payload.get("domain") or "general"),
            problem_domain=str(payload.get("problem_domain") or "unknown"),
            outcome=str(payload.get("outcome") or "success"),
            duration_seconds=int(payload.get("duration_seconds", 0) or 0),
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
