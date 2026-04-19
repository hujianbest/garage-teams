"""Tests for publishing reviewed memory candidates."""

from datetime import datetime

import pytest

from garage_os.knowledge.experience_index import ExperienceIndex
from garage_os.knowledge.knowledge_store import KnowledgeStore
from garage_os.storage.file_storage import FileStorage
from garage_os.types import KnowledgeType


@pytest.fixture
def temp_storage(tmp_path):
    """Create a temporary FileStorage instance."""
    return FileStorage(tmp_path)


@pytest.fixture
def candidate_store(temp_storage):
    """Create a CandidateStore instance with temporary storage."""
    from garage_os.memory.candidate_store import CandidateStore

    return CandidateStore(temp_storage)


@pytest.fixture
def knowledge_store(temp_storage):
    """Create a KnowledgeStore instance with temporary storage."""
    return KnowledgeStore(temp_storage)


@pytest.fixture
def experience_index(temp_storage):
    """Create an ExperienceIndex instance with temporary storage."""
    return ExperienceIndex(temp_storage)


@pytest.fixture
def publisher(candidate_store, knowledge_store, experience_index):
    """Create a publisher instance."""
    from garage_os.memory.publisher import KnowledgePublisher

    return KnowledgePublisher(
        candidate_store=candidate_store,
        knowledge_store=knowledge_store,
        experience_index=experience_index,
    )


@pytest.fixture
def confirmation_record():
    """Create a sample confirmation record."""
    return {
        "schema_version": "1",
        "batch_id": "batch-001",
        "resolution": "mixed",
        "actions": [
            {
                "candidate_id": "candidate-001",
                "action": "accept",
            }
        ],
        "resolved_at": datetime.now().isoformat(),
        "surface": "cli",
        "approver": "user",
    }


@pytest.fixture
def decision_candidate():
    """Create a decision candidate draft."""
    return {
        "schema_version": "1",
        "candidate_id": "candidate-001",
        "candidate_type": "decision",
        "session_id": "session-001",
        "source_artifacts": ["docs/designs/example.md"],
        "source_evidence_anchors": [
            {"kind": "artifact_excerpt", "ref": "docs/designs/example.md#decision"}
        ],
        "match_reasons": ["repeated_pattern:data-flow"],
        "status": "pending_review",
        "priority_score": 0.91,
        "title": "Use candidate batches",
        "summary": "Store candidates before publication.",
        "content": "Decision body",
        "tags": ["memory", "batching"],
    }


@pytest.fixture
def experience_summary_candidate():
    """Create an experience summary candidate draft."""
    return {
        "schema_version": "1",
        "candidate_id": "candidate-002",
        "candidate_type": "experience_summary",
        "session_id": "session-001",
        "source_artifacts": ["docs/designs/example.md"],
        "source_evidence_anchors": [
            {"kind": "session_metadata", "ref": "sessions/archived/session-001/session.json"}
        ],
        "match_reasons": ["skill_match:hf-design"],
        "status": "pending_review",
        "priority_score": 0.88,
        "title": "Experience summary",
        "summary": "Summarize the workflow experience.",
        "content": "Experience content",
        "task_type": "memory_pipeline",
        "skill_ids": ["hf-design"],
        "tech_stack": ["Python"],
        "domain": "garage_os",
        "problem_domain": "memory_pipeline",
        "outcome": "success",
        "duration_seconds": 120,
        "complexity": "medium",
        "recommendations": ["Keep candidate layers explicit"],
    }


class TestKnowledgePublisher:
    """Tests for publishing accepted candidates."""

    def test_detect_conflicts_returns_supersede_for_similar_knowledge(
        self,
        publisher,
        candidate_store,
        decision_candidate,
        knowledge_store,
    ) -> None:
        """Similar published knowledge should produce a supersede suggestion."""
        candidate_store.store_candidate(decision_candidate)
        published = publisher._to_knowledge_entry(  # noqa: SLF001 - test helper use
            decision_candidate,
            confirmation_ref=".garage/memory/confirmations/batch-001.json",
        )
        knowledge_store.store(published)

        conflict = publisher.detect_conflicts("candidate-001")

        assert conflict["strategy"] == "supersede"
        assert published.id in conflict["similar_entries"]

    def test_publish_decision_candidate_with_traceability(
        self,
        publisher,
        candidate_store,
        decision_candidate,
        confirmation_record,
        knowledge_store,
    ) -> None:
        """Accepted decision candidates should become knowledge entries with traceability."""
        candidate_store.store_candidate(decision_candidate)
        candidate_store.store_confirmation(confirmation_record)

        result = publisher.publish_candidate(
            candidate_id="candidate-001",
            action="accept",
            confirmation_ref=".garage/memory/confirmations/batch-001.json",
        )

        knowledge = knowledge_store.retrieve(result["knowledge_type"], result["published_id"])
        assert knowledge is not None
        assert knowledge.front_matter["confirmation_ref"] == ".garage/memory/confirmations/batch-001.json"
        assert knowledge.front_matter["published_from_candidate"] == "candidate-001"
        assert knowledge.front_matter["source_evidence_anchor"]["kind"] == "artifact_excerpt"

    def test_publish_experience_summary_candidate_to_experience_record(
        self,
        publisher,
        candidate_store,
        experience_summary_candidate,
        confirmation_record,
        experience_index,
    ) -> None:
        """Accepted experience summary candidates should publish into experience records."""
        candidate_store.store_candidate(experience_summary_candidate)
        confirmation_record["actions"][0]["candidate_id"] = "candidate-002"
        candidate_store.store_confirmation(confirmation_record)

        result = publisher.publish_candidate(
            candidate_id="candidate-002",
            action="accept",
            confirmation_ref=".garage/memory/confirmations/batch-001.json",
        )

        record = experience_index.retrieve(result["published_id"])
        assert record is not None
        assert record.confirmation_ref == ".garage/memory/confirmations/batch-001.json"
        assert record.published_from_candidate == "candidate-002"
        assert record.source_evidence_anchors[0]["kind"] == "session_metadata"

    def test_edit_accept_uses_edited_content(
        self,
        publisher,
        candidate_store,
        decision_candidate,
        confirmation_record,
        knowledge_store,
    ) -> None:
        """edit_accept should publish the edited payload and preserve confirmation link."""
        candidate_store.store_candidate(decision_candidate)
        candidate_store.store_confirmation(confirmation_record)

        edited = {
            "title": "Edited title",
            "summary": "Edited summary",
            "content": "Edited decision body",
            "tags": ["memory", "edited"],
        }
        result = publisher.publish_candidate(
            candidate_id="candidate-001",
            action="edit_accept",
            confirmation_ref=".garage/memory/confirmations/batch-001.json",
            edited_fields=edited,
        )

        knowledge = knowledge_store.retrieve(result["knowledge_type"], result["published_id"])
        assert knowledge is not None
        assert knowledge.topic == "Edited title"
        assert knowledge.content == "Edited decision body"
        assert knowledge.tags == ["memory", "edited"]
        assert knowledge.front_matter["confirmation_ref"] == ".garage/memory/confirmations/batch-001.json"

    def test_publish_orchestrator_output_end_to_end(
        self,
        publisher,
        candidate_store,
        knowledge_store,
        experience_index,
        temp_storage,
    ) -> None:
        """Publisher must accept candidates produced by the orchestrator without KeyError (CR1/CR2)."""
        from garage_os.memory.extraction_orchestrator import (
            ExtractionConfig,
            MemoryExtractionOrchestrator,
        )

        orchestrator = MemoryExtractionOrchestrator(
            temp_storage,
            candidate_store,
            ExtractionConfig(),
        )
        archived = {
            "session_id": "session-flow",
            "pack_id": "hf-design",
            "topic": "F003 design",
            "context": {
                "metadata": {
                    "problem_domain": "memory_pipeline",
                    "tags": ["workspace-first"],
                    "domain": "garage_os",
                }
            },
            "artifacts": [
                {
                    "path": "docs/designs/example.md",
                    "status": "approved",
                }
            ],
        }
        summary = orchestrator.extract_for_archived_session(archived)
        candidate_ids = summary["candidate_ids"]
        assert candidate_ids, "orchestrator should produce at least one candidate"

        for index, candidate_id in enumerate(candidate_ids):
            result = publisher.publish_candidate(
                candidate_id=candidate_id,
                action="accept",
                confirmation_ref=f".garage/memory/confirmations/{summary['batch_id']}.json",
                conflict_strategy="coexist" if index > 0 else None,
            )
            assert result["published_id"] is not None, (
                f"publish failed for candidate {candidate_id}"
            )

        published_decisions = knowledge_store.list_entries()
        for entry in published_decisions:
            assert entry.source_evidence_anchor is not None, (
                f"published entry {entry.id} missing source_evidence_anchor"
            )
            assert entry.confirmation_ref is not None
        experience_records = experience_index.list_records()
        for record in experience_records:
            assert record.source_evidence_anchors, (
                f"experience record {record.record_id} missing source_evidence_anchors"
            )

    def test_publish_supersede_records_relation_to_existing_entries(
        self,
        publisher,
        candidate_store,
        decision_candidate,
        confirmation_record,
        knowledge_store,
    ) -> None:
        """Explicit supersede strategy should record the relation (T6 / FR-304)."""
        candidate_store.store_candidate(decision_candidate)
        candidate_store.store_confirmation(confirmation_record)

        existing_entry = publisher._to_knowledge_entry(  # noqa: SLF001 - test helper use
            {**decision_candidate, "candidate_id": "existing-001"},
            confirmation_ref="prior",
        )
        existing_entry.id = "existing-001"
        knowledge_store.store(existing_entry)

        result = publisher.publish_candidate(
            candidate_id="candidate-001",
            action="accept",
            confirmation_ref=".garage/memory/confirmations/batch-001.json",
            conflict_strategy="supersede",
        )

        assert result["published_id"] is not None
        published = knowledge_store.retrieve(result["knowledge_type"], result["published_id"])
        assert published is not None
        assert "existing-001" in published.related_decisions

    def test_publish_requires_explicit_strategy_when_conflict_detected(
        self,
        publisher,
        candidate_store,
        decision_candidate,
        confirmation_record,
        knowledge_store,
    ) -> None:
        """Publisher must refuse silent supersede; caller must pass coexist/supersede/abandon (FR-304)."""
        candidate_store.store_candidate(decision_candidate)
        candidate_store.store_confirmation(confirmation_record)

        existing_entry = publisher._to_knowledge_entry(  # noqa: SLF001 - test helper use
            {**decision_candidate, "candidate_id": "existing-002"},
            confirmation_ref="prior",
        )
        existing_entry.id = "existing-002"
        knowledge_store.store(existing_entry)

        with pytest.raises(ValueError, match="conflict_strategy"):
            publisher.publish_candidate(
                candidate_id="candidate-001",
                action="accept",
                confirmation_ref=".garage/memory/confirmations/batch-001.json",
            )

    def test_publish_coexist_does_not_record_supersede_relation(
        self,
        publisher,
        candidate_store,
        decision_candidate,
        confirmation_record,
        knowledge_store,
    ) -> None:
        """Explicit coexist must publish without writing related_decisions back."""
        candidate_store.store_candidate(decision_candidate)
        candidate_store.store_confirmation(confirmation_record)

        existing_entry = publisher._to_knowledge_entry(  # noqa: SLF001 - test helper use
            {**decision_candidate, "candidate_id": "existing-003"},
            confirmation_ref="prior",
        )
        existing_entry.id = "existing-003"
        knowledge_store.store(existing_entry)

        result = publisher.publish_candidate(
            candidate_id="candidate-001",
            action="accept",
            confirmation_ref=".garage/memory/confirmations/batch-001.json",
            conflict_strategy="coexist",
        )

        assert result["published_id"] is not None
        published = knowledge_store.retrieve(result["knowledge_type"], result["published_id"])
        assert published is not None
        assert "existing-003" not in published.related_decisions

    def test_publish_abandon_skips_publication(
        self,
        publisher,
        candidate_store,
        decision_candidate,
        knowledge_store,
    ) -> None:
        """abandon must skip publication regardless of candidate type (T6 acceptance)."""
        candidate_store.store_candidate(decision_candidate)

        result = publisher.publish_candidate(
            candidate_id="candidate-001",
            action="abandon",
            confirmation_ref=".garage/memory/confirmations/batch-001.json",
        )

        assert result["published_id"] is None
        assert knowledge_store.list_entries() == []

    def test_publish_abandon_skips_experience_summary(
        self,
        publisher,
        candidate_store,
        experience_summary_candidate,
        experience_index,
    ) -> None:
        """abandon must skip experience publication too."""
        candidate_store.store_candidate(experience_summary_candidate)

        result = publisher.publish_candidate(
            candidate_id="candidate-002",
            action="abandon",
            confirmation_ref=".garage/memory/confirmations/batch-001.json",
        )

        assert result["published_id"] is None
        assert experience_index.list_records() == []

    def test_reject_or_defer_does_not_publish(
        self,
        publisher,
        candidate_store,
        decision_candidate,
        knowledge_store,
    ) -> None:
        """Reject/defer actions must not publish formal data."""
        candidate_store.store_candidate(decision_candidate)

        reject_result = publisher.publish_candidate(
            candidate_id="candidate-001",
            action="reject",
            confirmation_ref=".garage/memory/confirmations/batch-001.json",
        )
        defer_result = publisher.publish_candidate(
            candidate_id="candidate-001",
            action="defer",
            confirmation_ref=".garage/memory/confirmations/batch-001.json",
        )

        assert reject_result["published_id"] is None
        assert defer_result["published_id"] is None
        assert knowledge_store.list_entries() == []


class TestPublicationIdentityGenerator:
    """F004 T1: PublicationIdentityGenerator deterministic ID derivation (NFR-401, ADR-401)."""

    def test_publication_identity_generator_is_deterministic(self) -> None:
        """Same inputs must yield same outputs across N calls (NFR-401)."""
        from garage_os.memory.publisher import PublicationIdentityGenerator

        generator = PublicationIdentityGenerator()
        knowledge_results = {
            generator.derive_knowledge_id("candidate-001", KnowledgeType.DECISION)
            for _ in range(10)
        }
        experience_results = {
            generator.derive_experience_id("candidate-002") for _ in range(10)
        }
        assert len(knowledge_results) == 1
        assert len(experience_results) == 1

    def test_publication_identity_default_returns_candidate_id(self) -> None:
        """Default implementation must return candidate_id verbatim (ADR-401)."""
        from garage_os.memory.publisher import PublicationIdentityGenerator

        generator = PublicationIdentityGenerator()
        assert (
            generator.derive_knowledge_id("candidate-001", KnowledgeType.DECISION)
            == "candidate-001"
        )
        assert (
            generator.derive_knowledge_id("candidate-001", KnowledgeType.PATTERN)
            == "candidate-001"
        )
        assert (
            generator.derive_knowledge_id("candidate-001", KnowledgeType.SOLUTION)
            == "candidate-001"
        )
        assert generator.derive_experience_id("candidate-002") == "candidate-002"


class TestPublishCandidateEntryValidation:
    """F004 T1: publish_candidate entry-level conflict_strategy validation (FR-402, ADR-402)."""

    def test_publish_candidate_rejects_garbage_strategy_at_entry(
        self,
        publisher,
        candidate_store,
        decision_candidate,
    ) -> None:
        """Garbage strategy must raise at entry, even when no conflict exists (FR-402 verify 1)."""
        candidate_store.store_candidate(decision_candidate)

        with pytest.raises(ValueError) as excinfo:
            publisher.publish_candidate(
                candidate_id="candidate-001",
                action="accept",
                confirmation_ref=".garage/memory/confirmations/batch-001.json",
                conflict_strategy="garbageX",
            )
        assert "Allowed: ['abandon', 'coexist', 'supersede']" in str(excinfo.value)

    def test_publish_candidate_accepts_valid_strategy_without_conflict(
        self,
        publisher,
        candidate_store,
        decision_candidate,
        knowledge_store,
    ) -> None:
        """Valid strategy without conflict must publish normally (FR-402 verify 2)."""
        candidate_store.store_candidate(decision_candidate)

        result = publisher.publish_candidate(
            candidate_id="candidate-001",
            action="accept",
            confirmation_ref=".garage/memory/confirmations/batch-001.json",
            conflict_strategy="coexist",
        )
        assert result["published_id"] is not None
        assert knowledge_store.list_entries(), "expected entry to be published"

    def test_publish_candidate_none_strategy_passes_when_no_conflict(
        self,
        publisher,
        candidate_store,
        decision_candidate,
        knowledge_store,
    ) -> None:
        """None strategy must remain backward compatible when no conflict exists (FR-402 verify 3)."""
        candidate_store.store_candidate(decision_candidate)

        result = publisher.publish_candidate(
            candidate_id="candidate-001",
            action="accept",
            confirmation_ref=".garage/memory/confirmations/batch-001.json",
            conflict_strategy=None,
        )
        assert result["published_id"] is not None
        assert knowledge_store.list_entries()


class TestPublishCandidateRepublication:
    """F004 T2: store-or-update + supersede chain carry-over + self-conflict short-circuit
    (FR-401, FR-405, design §10.1, §10.1.1, §11.2, §11.2.1)."""

    def test_repeated_accept_uses_update_increments_version(
        self,
        publisher,
        candidate_store,
        decision_candidate,
        knowledge_store,
    ) -> None:
        """Same candidate accepted twice must yield one entry with version=2 (FR-401 verify 1)."""
        candidate_store.store_candidate(decision_candidate)

        first = publisher.publish_candidate(
            candidate_id="candidate-001",
            action="accept",
            confirmation_ref=".garage/memory/confirmations/batch-001.json",
        )
        assert first["published_id"] == "candidate-001"
        first_entry = knowledge_store.retrieve(KnowledgeType.DECISION, "candidate-001")
        assert first_entry is not None
        assert first_entry.version == 1

        second = publisher.publish_candidate(
            candidate_id="candidate-001",
            action="edit_accept",
            confirmation_ref=".garage/memory/confirmations/batch-002.json",
            edited_fields={"title": "Updated", "content": "Updated body"},
        )
        assert second["published_id"] == "candidate-001"
        all_entries = knowledge_store.list_entries(KnowledgeType.DECISION)
        assert len(all_entries) == 1, "expected exactly one entry id after re-publication"
        assert all_entries[0].id == "candidate-001"
        assert all_entries[0].version == 2

    def test_retrieve_after_repeated_accept_returns_latest_version(
        self,
        publisher,
        candidate_store,
        decision_candidate,
        knowledge_store,
    ) -> None:
        """KnowledgeStore.retrieve must return the latest version after re-publication (FR-401 verify 2)."""
        candidate_store.store_candidate(decision_candidate)

        publisher.publish_candidate(
            candidate_id="candidate-001",
            action="accept",
            confirmation_ref="cf-1",
        )
        publisher.publish_candidate(
            candidate_id="candidate-001",
            action="edit_accept",
            confirmation_ref="cf-2",
            edited_fields={"content": "Re-published content"},
        )

        latest = knowledge_store.retrieve(KnowledgeType.DECISION, "candidate-001")
        assert latest is not None
        assert latest.version == 2
        assert latest.content == "Re-published content"

    def test_repeated_publish_experience_summary_updates_index(
        self,
        publisher,
        candidate_store,
        experience_summary_candidate,
        experience_index,
    ) -> None:
        """experience_summary candidate re-publication keeps a single record_id and writes
        through ExperienceIndex.update path so updated_at progresses (FR-401 verify 3)."""
        candidate_store.store_candidate(experience_summary_candidate)

        first = publisher.publish_candidate(
            candidate_id="candidate-002",
            action="accept",
            confirmation_ref="cf-exp-1",
        )
        assert first["published_id"] == "candidate-002"
        first_record = experience_index.retrieve("candidate-002")
        assert first_record is not None
        first_updated_at = first_record.updated_at

        second = publisher.publish_candidate(
            candidate_id="candidate-002",
            action="edit_accept",
            confirmation_ref="cf-exp-2",
            edited_fields={"summary": "Updated experience summary"},
        )
        assert second["published_id"] == "candidate-002"

        records = experience_index.list_records()
        assert len(records) == 1, "expected exactly one experience record after re-publication"
        assert records[0].record_id == "candidate-002"
        # After publish_candidate goes through ExperienceIndex.update path,
        # updated_at must be at least as recent as the first publication.
        assert records[0].updated_at >= first_updated_at

    def test_repeated_publish_preserves_supersedes_chain_from_v1(
        self,
        publisher,
        candidate_store,
        decision_candidate,
        knowledge_store,
    ) -> None:
        """v1 entry's front_matter['supersedes'] must survive v1.1 re-publication (FR-405 + §11.2.1)."""
        candidate_store.store_candidate(decision_candidate)

        v1_entry = publisher._to_knowledge_entry(  # noqa: SLF001 - test scaffolding
            decision_candidate,
            confirmation_ref="v1-cf",
        )
        v1_entry.front_matter["supersedes"] = ["k-X", "k-Y"]
        knowledge_store.store(v1_entry)

        publisher.publish_candidate(
            candidate_id="candidate-001",
            action="edit_accept",
            confirmation_ref="cf-v1-1",
            edited_fields={"content": "v1.1 update"},
        )

        republished = knowledge_store.retrieve(KnowledgeType.DECISION, "candidate-001")
        assert republished is not None
        assert republished.version == 2
        carried = list(republished.front_matter.get("supersedes", []))
        for required in ("k-X", "k-Y"):
            assert required in carried, (
                f"expected supersede '{required}' to survive v1.1 re-publication; got {carried}"
            )

    def test_repeated_publish_preserves_related_decisions_from_v1(
        self,
        publisher,
        candidate_store,
        decision_candidate,
        knowledge_store,
    ) -> None:
        """v1 entry's related_decisions must survive v1.1 re-publication (FR-405 + §11.2.1)."""
        candidate_store.store_candidate(decision_candidate)

        v1_entry = publisher._to_knowledge_entry(  # noqa: SLF001
            decision_candidate,
            confirmation_ref="v1-cf",
        )
        v1_entry.related_decisions = ["k-Z"]
        v1_entry.front_matter["related_decisions"] = ["k-Z"]
        knowledge_store.store(v1_entry)

        publisher.publish_candidate(
            candidate_id="candidate-001",
            action="edit_accept",
            confirmation_ref="cf-v1-1",
            edited_fields={"content": "v1.1 update"},
        )

        republished = knowledge_store.retrieve(KnowledgeType.DECISION, "candidate-001")
        assert republished is not None
        assert "k-Z" in republished.related_decisions

    def test_repeated_publish_merges_v1_supersedes_with_new_supersede_target(
        self,
        publisher,
        candidate_store,
        decision_candidate,
        knowledge_store,
    ) -> None:
        """v1 supersede chain + v1.1 explicit strategy=supersede must merge, not replace.

        Locks the §11.2.1 _merge_unique semantics under the most adversarial
        path: v1 already supersede-d ['k-X', 'k-Y']; v1.1 re-publish hits a
        new conflict against 'existing-zzz' with strategy=supersede; the
        result must contain ['k-X', 'k-Y', 'existing-zzz'] (any order, no
        loss).
        """
        candidate_store.store_candidate(decision_candidate)

        # Seed v1 entry whose front_matter['supersedes'] already carries a
        # historical supersede chain. Use distinct title/tags so it does
        # not surface as a similar entry on its own (only the conflict
        # target below should match by title/tags).
        v1_entry = publisher._to_knowledge_entry(  # noqa: SLF001
            decision_candidate,
            confirmation_ref="v1-cf",
        )
        v1_entry.front_matter["supersedes"] = ["k-X", "k-Y"]
        knowledge_store.store(v1_entry)

        # Plant a real conflict target (different id, same title+tags).
        from datetime import datetime
        from garage_os.types import KnowledgeEntry

        other_target = KnowledgeEntry(
            id="existing-zzz",
            type=KnowledgeType.DECISION,
            topic=decision_candidate["title"],
            date=datetime.now(),
            tags=list(decision_candidate["tags"]),
            content="other entry forcing real conflict",
        )
        knowledge_store.store(other_target)

        publisher.publish_candidate(
            candidate_id="candidate-001",
            action="edit_accept",
            confirmation_ref="cf-v1-1",
            edited_fields={"content": "v1.1 carry-merged"},
            conflict_strategy="supersede",
        )

        republished = knowledge_store.retrieve(KnowledgeType.DECISION, "candidate-001")
        assert republished is not None
        carried = list(republished.front_matter.get("supersedes", []))
        for required in ("k-X", "k-Y", "existing-zzz"):
            assert required in carried, (
                f"expected merged supersede '{required}'; got {carried}"
            )

    def test_repeated_publish_experience_summary_preserves_created_at(
        self,
        publisher,
        candidate_store,
        experience_summary_candidate,
        experience_index,
    ) -> None:
        """Re-publication must preserve created_at while bumping updated_at
        (publisher.py § F004 path A explicit carry-over)."""
        candidate_store.store_candidate(experience_summary_candidate)

        publisher.publish_candidate(
            candidate_id="candidate-002",
            action="accept",
            confirmation_ref="cf-1",
        )
        first = experience_index.retrieve("candidate-002")
        assert first is not None
        original_created_at = first.created_at

        publisher.publish_candidate(
            candidate_id="candidate-002",
            action="edit_accept",
            confirmation_ref="cf-2",
            edited_fields={"summary": "Updated"},
        )
        latest = experience_index.retrieve("candidate-002")
        assert latest is not None
        assert latest.created_at == original_created_at
        assert latest.updated_at >= original_created_at

    def test_repeated_accept_short_circuits_self_conflict(
        self,
        publisher,
        candidate_store,
        decision_candidate,
        knowledge_store,
    ) -> None:
        """Re-accepting same candidate must not require --strategy (design §10.1.1).

        ConflictDetector matches the v1 entry by title/tags, but publisher
        must remove similar_entries elements equal to the new id before
        requiring conflict_strategy.
        """
        candidate_store.store_candidate(decision_candidate)

        publisher.publish_candidate(
            candidate_id="candidate-001",
            action="accept",
            confirmation_ref="cf-1",
        )

        # Re-accept must not raise even without explicit conflict_strategy.
        publisher.publish_candidate(
            candidate_id="candidate-001",
            action="edit_accept",
            confirmation_ref="cf-2",
            edited_fields={"content": "Self-conflict short-circuit body"},
        )

        latest = knowledge_store.retrieve(KnowledgeType.DECISION, "candidate-001")
        assert latest is not None
        assert latest.version == 2
        assert latest.content == "Self-conflict short-circuit body"
