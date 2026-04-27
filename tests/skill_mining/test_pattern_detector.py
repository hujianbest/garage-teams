"""F013-A T2 tests: PatternDetector clustering + scoring + threshold + dual-source key."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from garage_os.knowledge.experience_index import ExperienceIndex
from garage_os.knowledge.knowledge_store import KnowledgeStore
from garage_os.skill_mining.pattern_detector import (
    DEFAULT_THRESHOLD,
    already_covered_by_skill,
    cluster_items,
    compute_score,
    detect_and_write,
    extract_problem_domain_key,
    extract_tag_bucket,
)
from garage_os.skill_mining.suggestion_store import SuggestionStore
from garage_os.skill_mining.types import SkillSuggestion, SkillSuggestionStatus
from garage_os.storage.file_storage import FileStorage
from garage_os.types import ExperienceRecord, KnowledgeEntry, KnowledgeType


def _record(
    rid: str,
    *,
    problem_domain: str = "review-verdict",
    key_patterns: list[str] | None = None,
    session_id: str = "ses-001",
    created_at: datetime | None = None,
) -> ExperienceRecord:
    return ExperienceRecord(
        record_id=rid,
        task_type="review",
        skill_ids=["hf-code-review"],
        tech_stack=["python"],
        domain="dev",
        problem_domain=problem_domain,
        outcome="success",
        duration_seconds=300,
        complexity="medium",
        session_id=session_id,
        key_patterns=key_patterns if key_patterns is not None else ["verdict-format", "5-section"],
        created_at=created_at or datetime(2026, 4, 26, 12, 0, 0),
    )


def _entry(
    eid: str,
    *,
    front_matter_domain: str | None = "review-verdict",
    topic: str = "review-verdict design",
    tags: list[str] | None = None,
    source_session: str = "ses-002",
    date: datetime | None = None,
) -> KnowledgeEntry:
    fm: dict = {}
    if front_matter_domain:
        fm["problem_domain"] = front_matter_domain
    return KnowledgeEntry(
        id=eid,
        type=KnowledgeType.DECISION,
        topic=topic,
        date=date or datetime(2026, 4, 26, 12, 0, 0),
        tags=tags if tags is not None else ["verdict-format", "5-section"],
        content="...",
        source_session=source_session,
        front_matter=fm,
    )


# T2.1
class TestExtractProblemDomainKey:
    def test_experience_record_top_level(self) -> None:
        r = _record("r-1", problem_domain="cli-design")
        assert extract_problem_domain_key(r) == "cli-design"

    def test_knowledge_entry_front_matter(self) -> None:
        e = _entry("e-1", front_matter_domain="cli-design")
        assert extract_problem_domain_key(e) == "cli-design"

    def test_knowledge_entry_topic_fallback(self) -> None:
        e = _entry("e-1", front_matter_domain=None, topic="cli-design notes")
        assert extract_problem_domain_key(e) == "cli-design"

    def test_skip_entry_with_no_domain_key(self) -> None:
        e = _entry("e-1", front_matter_domain=None, topic="")
        assert extract_problem_domain_key(e) is None

    def test_skip_record_with_no_domain_key(self) -> None:
        r = _record("r-1", problem_domain="")
        assert extract_problem_domain_key(r) is None


# T2.5
class TestClusterByDomainAndTagBucket:
    def test_cluster_groups_by_domain_and_first_two_tags(self) -> None:
        items = [
            _record("r-1", session_id="s-1"),
            _record("r-2", session_id="s-2"),
            _entry("e-1", source_session="s-3"),
        ]
        clusters = cluster_items(items)
        assert len(clusters) == 1  # all share same (domain, tag_bucket)
        c = clusters[0]
        assert c.problem_domain_key == "review-verdict"
        assert c.tag_bucket == ("5-section", "verdict-format")  # alpha-sorted
        assert len(c.session_ids) == 3
        assert sorted(c.record_ids) == ["r-1", "r-2"]
        assert c.entry_ids == ["e-1"]

    def test_skipped_items_do_not_form_cluster(self) -> None:
        items = [
            _entry("e-1", front_matter_domain=None, topic=""),
            _record("r-1"),
        ]
        clusters = cluster_items(items)
        # Only the record-based bucket exists
        assert len(clusters) == 1
        assert clusters[0].entry_ids == []
        assert clusters[0].record_ids == ["r-1"]


# T2.6
class TestThresholdDefault:
    def test_threshold_is_5(self) -> None:
        assert DEFAULT_THRESHOLD == 5


# T2.7
class TestDedupSessionId:
    def test_session_id_dedup_in_cluster(self) -> None:
        items = [
            _record("r-1", session_id="s-1"),
            _record("r-2", session_id="s-1"),  # dup session
            _record("r-3", session_id="s-2"),
        ]
        clusters = cluster_items(items)
        assert clusters[0].session_ids == {"s-1", "s-2"}
        assert len(clusters[0].record_ids) == 3  # all evidence kept


# T2.8
class TestAlreadyCoveredBySkill:
    def test_existing_skill_covers_substring(self, tmp_path: Path) -> None:
        # Create a fake packs/garage/skills/verdict-format/SKILL.md
        skill_dir = tmp_path / "garage" / "skills" / "verdict-format"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: verdict-format\ndescription: ...\n---\n# Verdict\n",
            encoding="utf-8",
        )
        from garage_os.skill_mining.pattern_detector import ClusterEvidence

        c = ClusterEvidence(
            problem_domain_key="verdict-format",
            tag_bucket=("5-section",),
            entry_ids=[],
            record_ids=[],
            session_ids={"s-1"},
            max_timestamp=datetime(2026, 4, 26),
        )
        assert already_covered_by_skill(c, tmp_path) is True

    def test_no_match_returns_false(self, tmp_path: Path) -> None:
        from garage_os.skill_mining.pattern_detector import ClusterEvidence

        c = ClusterEvidence(
            problem_domain_key="totally-new-domain",
            tag_bucket=(),
            entry_ids=[],
            record_ids=[],
            session_ids={"s-1"},
            max_timestamp=datetime(2026, 4, 26),
        )
        assert already_covered_by_skill(c, tmp_path) is False


# T2.9
class TestScoreFormula:
    def test_score_components(self) -> None:
        from garage_os.skill_mining.pattern_detector import ClusterEvidence

        c = ClusterEvidence(
            problem_domain_key="d",
            tag_bucket=(),
            entry_ids=["e-1", "e-2"],
            record_ids=["r-1", "r-2", "r-3"],
            session_ids={"s-1", "s-2", "s-3"},
            max_timestamp=datetime(2026, 4, 26),
        )
        # N = 5, sessions = 3, days_since_epoch = (2026-04-26 - 1970-01-01).days
        import math
        expected = (
            math.log10(5 + 1)
            + 0.3 * 3
            + 0.5 * ((c.max_timestamp - datetime(1970, 1, 1)).days / 1000)
        )
        assert compute_score(c) == pytest.approx(expected)


# T2.10 + T2.11 + T2.12 (end-to-end detect_and_write)
class TestDetectAndWrite:
    def _setup(self, tmp_path: Path) -> tuple[KnowledgeStore, ExperienceIndex, SuggestionStore, Path]:
        garage_dir = tmp_path / ".garage"
        storage = FileStorage(garage_dir)
        ks = KnowledgeStore(storage)
        ei = ExperienceIndex(storage)
        ss = SuggestionStore(garage_dir)
        packs_root = tmp_path / "packs"
        return ks, ei, ss, packs_root

    def test_writes_when_threshold_reached(self, tmp_path: Path) -> None:
        ks, ei, ss, packs_root = self._setup(tmp_path)
        # 5 records with distinct session ids, same (domain, tag-bucket)
        for i in range(5):
            ei.store(_record(f"r-{i}", session_id=f"ses-{i}"))
        new = detect_and_write(ks, ei, ss, packs_root)
        assert len(new) == 1
        assert new[0].status == SkillSuggestionStatus.PROPOSED
        assert len(new[0].evidence_records) == 5

    def test_skips_when_below_threshold(self, tmp_path: Path) -> None:
        ks, ei, ss, packs_root = self._setup(tmp_path)
        for i in range(3):
            ei.store(_record(f"r-{i}", session_id=f"ses-{i}"))
        new = detect_and_write(ks, ei, ss, packs_root)
        assert new == []

    def test_existing_proposed_no_dup(self, tmp_path: Path) -> None:
        ks, ei, ss, packs_root = self._setup(tmp_path)
        for i in range(5):
            ei.store(_record(f"r-{i}", session_id=f"ses-{i}"))
        # First pass writes 1
        first = detect_and_write(ks, ei, ss, packs_root)
        assert len(first) == 1
        # Add 5 more records same domain+tags; second pass should NOT generate new
        for i in range(5, 10):
            ei.store(_record(f"r-{i}", session_id=f"ses-{i}"))
        second = detect_and_write(ks, ei, ss, packs_root)
        assert len(second) == 0

    def test_skip_already_covered_skill(self, tmp_path: Path) -> None:
        ks, ei, ss, packs_root = self._setup(tmp_path)
        # Create a fake skill that covers the cluster
        skill_dir = packs_root / "garage" / "skills" / "review-verdict-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: review-verdict-skill\ndescription: ...\n---\n",
            encoding="utf-8",
        )
        for i in range(5):
            ei.store(_record(f"r-{i}", session_id=f"ses-{i}"))
        new = detect_and_write(ks, ei, ss, packs_root)
        assert new == []  # silently skipped (covered)

    def test_kb_and_ei_read_only_no_mutation(self, tmp_path: Path) -> None:
        """T2.12 sentinel: pattern_detector must not mutate KS or EI."""
        ks, ei, ss, packs_root = self._setup(tmp_path)
        for i in range(5):
            ei.store(_record(f"r-{i}", session_id=f"ses-{i}"))

        # Snapshot KS + EI byte hashes (use list_records / list_entries)
        before_records = [r.record_id for r in ei.list_records()]
        before_entries = [e.id for e in ks.list_entries()]

        detect_and_write(ks, ei, ss, packs_root)

        after_records = [r.record_id for r in ei.list_records()]
        after_entries = [e.id for e in ks.list_entries()]

        assert before_records == after_records
        assert before_entries == after_entries
