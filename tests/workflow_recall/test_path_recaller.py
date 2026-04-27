"""F014 T2 tests: PathRecaller clustering + Counter + threshold + Im-4 sub-sequence."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from garage_os.knowledge.experience_index import ExperienceIndex
from garage_os.storage.file_storage import FileStorage
from garage_os.types import ExperienceRecord
from garage_os.workflow_recall.path_recaller import (
    DEFAULT_THRESHOLD,
    DEFAULT_TOP_K,
    DEFAULT_WINDOW,
    _take_subsequence,
    recall,
)


def _record(
    rid: str,
    *,
    task_type: str = "implement",
    problem_domain: str = "cli-design",
    skill_ids: list[str] | None = None,
    duration_seconds: int = 3600,
    lessons_learned: list[str] | None = None,
    session_id: str = "ses-001",
    created_at: datetime | None = None,
) -> ExperienceRecord:
    return ExperienceRecord(
        record_id=rid,
        task_type=task_type,
        skill_ids=skill_ids if skill_ids is not None
            else ["hf-specify", "hf-design", "hf-tasks", "hf-test-driven-dev"],
        tech_stack=["python"],
        domain="dev",
        problem_domain=problem_domain,
        outcome="success",
        duration_seconds=duration_seconds,
        complexity="medium",
        session_id=session_id,
        lessons_learned=lessons_learned or ["先 read spec 再 design"],
        created_at=created_at or datetime(2026, 4, 26, 12, 0, 0),
    )


def _setup(tmp_path: Path) -> ExperienceIndex:
    return ExperienceIndex(FileStorage(tmp_path / ".garage"))


# T2.1
class TestBelowThreshold:
    def test_below_threshold_returns_empty(self, tmp_path: Path) -> None:
        ei = _setup(tmp_path)
        for i in range(2):
            ei.store(_record(f"r-{i}"))
        result = recall(ei, problem_domain="cli-design")
        assert result.advisories == []
        assert result.threshold_met is False
        assert result.bucket_size == 2
        assert result.scanned_count == 2


# T2.2
class TestAtThreshold:
    def test_at_threshold_returns_advisory(self, tmp_path: Path) -> None:
        ei = _setup(tmp_path)
        for i in range(3):
            ei.store(_record(f"r-{i}", session_id=f"ses-{i}"))
        result = recall(ei, problem_domain="cli-design")
        assert result.threshold_met is True
        assert len(result.advisories) == 1
        adv = result.advisories[0]
        assert adv.count == 3
        assert adv.skills == ["hf-specify", "hf-design", "hf-tasks", "hf-test-driven-dev"]


# T2.3
class TestGroupingByTaskTypeAndProblemDomain:
    def test_filter_by_task_type(self, tmp_path: Path) -> None:
        ei = _setup(tmp_path)
        for i in range(3):
            ei.store(_record(f"r-{i}", task_type="implement", session_id=f"ses-i-{i}"))
        for i in range(3):
            ei.store(_record(f"r-r-{i}", task_type="review", session_id=f"ses-r-{i}"))
        result = recall(ei, task_type="implement")
        assert result.bucket_size == 3
        assert result.advisories[0].count == 3

    def test_filter_by_problem_domain(self, tmp_path: Path) -> None:
        ei = _setup(tmp_path)
        for i in range(3):
            ei.store(_record(f"r-{i}", problem_domain="cli-design", session_id=f"ses-{i}"))
        for i in range(3):
            ei.store(_record(f"r-r-{i}", problem_domain="review-verdict", session_id=f"ses-r-{i}"))
        result = recall(ei, problem_domain="review-verdict")
        assert result.bucket_size == 3


# T2.4
class TestTopK:
    def test_top_k_default_3(self) -> None:
        assert DEFAULT_TOP_K == 3

    def test_top_k_override(self, tmp_path: Path) -> None:
        ei = _setup(tmp_path)
        # Create 4 distinct sequences, each with 3 records
        for j in range(4):
            for i in range(3):
                ei.store(_record(
                    f"r-{j}-{i}",
                    skill_ids=[f"skill-{j}", "hf-specify"],
                    session_id=f"ses-{j}-{i}",
                ))
        result = recall(ei, problem_domain="cli-design", top_k=2)
        assert len(result.advisories) == 2


# T2.5
class TestWindow:
    def test_window_default_10(self) -> None:
        assert DEFAULT_WINDOW == 10

    def test_window_takes_most_recent(self, tmp_path: Path) -> None:
        ei = _setup(tmp_path)
        # 12 records: oldest 9 with seq A, newest 3 with seq B
        for i in range(9):
            ei.store(_record(
                f"r-old-{i}",
                skill_ids=["a", "b"],
                session_id=f"ses-old-{i}",
                created_at=datetime(2026, 1, 1) + timedelta(days=i),
            ))
        for i in range(3):
            ei.store(_record(
                f"r-new-{i}",
                skill_ids=["x", "y"],
                session_id=f"ses-new-{i}",
                created_at=datetime(2026, 4, 26) + timedelta(hours=i),
            ))
        # Window=10 means newest 10 records taken: 3 new + 7 old
        result = recall(ei, problem_domain="cli-design", window=10, top_k=2)
        # Expected: top sequence is "a, b" (7 hits) > "x, y" (3 hits)
        assert result.advisories[0].skills == ["a", "b"]
        assert result.advisories[0].count == 7
        assert result.advisories[1].skills == ["x", "y"]
        assert result.advisories[1].count == 3


# T2.6
class TestSkillIdSubsequenceAfterFirst:
    """Im-4 r2: --skill-id Z 取 Z 第一次出现位置之后的子序列."""

    def test_skill_id_subsequence_extracted(self, tmp_path: Path) -> None:
        ei = _setup(tmp_path)
        for i in range(3):
            ei.store(_record(
                f"r-{i}",
                skill_ids=["hf-specify", "hf-design", "hf-tasks", "hf-test-driven-dev"],
                session_id=f"ses-{i}",
            ))
        result = recall(ei, problem_domain="cli-design", skill_id="hf-design")
        assert len(result.advisories) == 1
        assert result.advisories[0].skills == ["hf-tasks", "hf-test-driven-dev"]
        assert result.advisories[0].count == 3


# T2.7
class TestSkillIdAtLastPositionSkipped:
    """Im-4 r2: Z 是序列最后一项 → 该 record 贡献空, 跳过."""

    def test_skill_id_at_last_position_skipped(self, tmp_path: Path) -> None:
        ei = _setup(tmp_path)
        for i in range(3):
            ei.store(_record(
                f"r-{i}",
                skill_ids=["hf-specify", "hf-design", "hf-tasks", "hf-test-driven-dev"],
                session_id=f"ses-{i}",
            ))
        # hf-test-driven-dev is the last item; subseq is empty → all 3 records skipped
        result = recall(ei, problem_domain="cli-design", skill_id="hf-test-driven-dev")
        # bucket_size==3 (filter by problem_domain + skill_id-in-seq), but no sequences emitted
        assert result.advisories == []
        assert result.threshold_met is True  # bucket met threshold but no seq survived


# T2.8
class TestSkillIdNotInRecord:
    """Im-4 r2: Z 不在 record 序列中 → 跳过."""

    def test_skill_id_not_in_record_filtered_out(self, tmp_path: Path) -> None:
        ei = _setup(tmp_path)
        for i in range(3):
            ei.store(_record(
                f"r-{i}",
                skill_ids=["a", "b"],  # no "hf-design"
                session_id=f"ses-{i}",
            ))
        result = recall(ei, problem_domain="cli-design", skill_id="hf-design")
        # _bucket_records filter: skill_id not in skill_ids → 0 records pass
        assert result.bucket_size == 0
        assert result.threshold_met is False


# T2.9
class TestPerSequenceAvgDuration:
    """Im-3 r2: avg_duration_seconds is per-sequence mean, not bucket-wide."""

    def test_avg_duration_per_sequence(self, tmp_path: Path) -> None:
        ei = _setup(tmp_path)
        # 3 records seq A, durations [3000, 4000, 5000] → avg 4000
        for i, dur in enumerate([3000, 4000, 5000]):
            ei.store(_record(
                f"r-a-{i}",
                skill_ids=["a", "b"],
                duration_seconds=dur,
                session_id=f"ses-a-{i}",
            ))
        # 3 records seq B, durations [1000, 2000, 3000] → avg 2000
        for i, dur in enumerate([1000, 2000, 3000]):
            ei.store(_record(
                f"r-b-{i}",
                skill_ids=["x", "y"],
                duration_seconds=dur,
                session_id=f"ses-b-{i}",
            ))
        result = recall(ei, problem_domain="cli-design", top_k=2)
        # Each advisory has its own avg
        avg_a = next(a.avg_duration_seconds for a in result.advisories if a.skills == ["a", "b"])
        avg_b = next(a.avg_duration_seconds for a in result.advisories if a.skills == ["x", "y"])
        assert avg_a == 4000.0
        assert avg_b == 2000.0


# T2.10
class TestPerSequenceTopLessons:
    """Im-3 r2: top_lessons also per-sequence."""

    def test_top_lessons_per_sequence(self, tmp_path: Path) -> None:
        ei = _setup(tmp_path)
        for i in range(3):
            ei.store(_record(
                f"r-a-{i}",
                skill_ids=["a", "b"],
                lessons_learned=["lesson-A"],
                session_id=f"ses-a-{i}",
            ))
        for i in range(3):
            ei.store(_record(
                f"r-b-{i}",
                skill_ids=["x", "y"],
                lessons_learned=["lesson-B"],
                session_id=f"ses-b-{i}",
            ))
        result = recall(ei, problem_domain="cli-design", top_k=2)
        adv_a = next(a for a in result.advisories if a.skills == ["a", "b"])
        adv_b = next(a for a in result.advisories if a.skills == ["x", "y"])
        assert adv_a.top_lessons == [("lesson-A", 3)]
        assert adv_b.top_lessons == [("lesson-B", 3)]


# T2.11
class TestReadOnlyOnExperienceIndex:
    """INV-F14-1 sentinel: PathRecaller does not mutate ExperienceIndex."""

    def test_recall_does_not_mutate_records(self, tmp_path: Path) -> None:
        ei = _setup(tmp_path)
        for i in range(5):
            ei.store(_record(f"r-{i}", session_id=f"ses-{i}"))
        before = [r.record_id for r in ei.list_records()]
        recall(ei, problem_domain="cli-design")
        after = [r.record_id for r in ei.list_records()]
        assert before == after  # no records added/removed/reordered


# T2.12
class TestEmptyFilterRaises:
    def test_all_filters_none_raises(self, tmp_path: Path) -> None:
        ei = _setup(tmp_path)
        with pytest.raises(ValueError, match="at least one of"):
            recall(ei)


# T2.13 (helper test)
class TestTakeSubsequenceHelper:
    def test_no_skill_id_returns_full_seq(self) -> None:
        assert _take_subsequence(["a", "b", "c"], None) == ("a", "b", "c")

    def test_skill_id_in_middle(self) -> None:
        assert _take_subsequence(["a", "b", "c"], "b") == ("c",)

    def test_skill_id_at_last_returns_none(self) -> None:
        assert _take_subsequence(["a", "b", "c"], "c") is None

    def test_skill_id_at_first(self) -> None:
        assert _take_subsequence(["a", "b", "c"], "a") == ("b", "c")

    def test_skill_id_not_in_seq_returns_none(self) -> None:
        assert _take_subsequence(["a", "b", "c"], "z") is None
