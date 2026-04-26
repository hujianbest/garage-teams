"""F013-A T1 tests: SuggestionStore CRUD + 5 status subdirs + atomic write + mv."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from garage_os.skill_mining.suggestion_store import (
    SUGGESTIONS_DIR_NAME,
    SuggestionStore,
)
from garage_os.skill_mining.types import SkillSuggestion, SkillSuggestionStatus


def _make_suggestion(
    sg_id: str = "sg-20260426-aabbcc",
    status: SkillSuggestionStatus = SkillSuggestionStatus.PROPOSED,
) -> SkillSuggestion:
    now = datetime(2026, 4, 26, 12, 0, 0)
    return SkillSuggestion(
        id=sg_id,
        suggested_name="verdict-format",
        suggested_description=(
            "适用于审阅 review verdict 时按 5 段格式 (verdict / findings / "
            "recommendations / 通过条件 / 计数) 产出. 不适用于代码 review."
        ),
        problem_domain_key="review-verdict",
        tag_bucket=["5-section", "verdict-format"],
        evidence_entries=["k-001", "k-002"],
        evidence_records=["r-001", "r-002", "r-003"],
        suggested_pack="garage",
        score=1.234,
        status=status,
        created_at=now,
        expires_at=now + timedelta(days=30),
    )


class TestCreateProposed:
    """T1.1: write to proposed/ subdir."""

    def test_create_proposed_writes_to_proposed_subdir(self, tmp_path: Path) -> None:
        store = SuggestionStore(tmp_path / ".garage")
        suggestion = _make_suggestion()
        target = store.write(suggestion)

        expected = tmp_path / ".garage" / SUGGESTIONS_DIR_NAME / "proposed" / "sg-20260426-aabbcc.json"
        assert target == expected
        assert target.is_file()
        # Round-trip
        loaded = store.load(SkillSuggestionStatus.PROPOSED, suggestion.id)
        assert loaded is not None
        assert loaded.suggested_name == "verdict-format"


class TestIdGeneration:
    """T1.2: id format sg-yyyymmdd-6hex."""

    def test_id_generation_format(self) -> None:
        ts = datetime(2026, 4, 26, 9, 30, 0)
        sg_id = SuggestionStore.generate_id(ts)
        assert sg_id.startswith("sg-20260426-")
        # 6 hex chars after the date
        suffix = sg_id.rsplit("-", 1)[1]
        assert len(suffix) == 6
        assert all(c in "0123456789abcdef" for c in suffix)

    def test_id_generation_uses_now_by_default(self) -> None:
        sg_id = SuggestionStore.generate_id()
        assert sg_id.startswith("sg-")
        # date portion is current
        today = datetime.now().strftime("%Y%m%d")
        assert today in sg_id


class TestLoadMissing:
    """T1.3: load returns None for missing."""

    def test_load_returns_none_for_missing(self, tmp_path: Path) -> None:
        store = SuggestionStore(tmp_path / ".garage")
        result = store.load(SkillSuggestionStatus.PROPOSED, "sg-nonexistent")
        assert result is None


class TestMoveToStatus:
    """T1.4: move uses os.rename (atomic single syscall in spirit)."""

    def test_move_to_status_relocates_file(self, tmp_path: Path) -> None:
        store = SuggestionStore(tmp_path / ".garage")
        suggestion = _make_suggestion(status=SkillSuggestionStatus.PROPOSED)
        store.write(suggestion)

        # Verify proposed file exists
        proposed_path = tmp_path / ".garage" / SUGGESTIONS_DIR_NAME / "proposed" / f"{suggestion.id}.json"
        assert proposed_path.is_file()

        # Move
        moved = store.move_to_status(suggestion.id, SkillSuggestionStatus.PROMOTED)
        assert moved is not None
        assert moved.status == SkillSuggestionStatus.PROMOTED

        # Old gone, new exists
        assert not proposed_path.is_file()
        promoted_path = tmp_path / ".garage" / SUGGESTIONS_DIR_NAME / "promoted" / f"{suggestion.id}.json"
        assert promoted_path.is_file()


class TestListByStatus:
    """T1.5: list filtered by status."""

    def test_list_by_status_filters(self, tmp_path: Path) -> None:
        store = SuggestionStore(tmp_path / ".garage")
        sg1 = _make_suggestion(sg_id="sg-20260426-111111", status=SkillSuggestionStatus.PROPOSED)
        sg2 = _make_suggestion(sg_id="sg-20260426-222222", status=SkillSuggestionStatus.PROMOTED)
        sg3 = _make_suggestion(sg_id="sg-20260426-333333", status=SkillSuggestionStatus.PROPOSED)
        store.write(sg1)
        store.write(sg2)
        store.write(sg3)

        proposed = store.list_by_status(SkillSuggestionStatus.PROPOSED)
        promoted = store.list_by_status(SkillSuggestionStatus.PROMOTED)
        assert len(proposed) == 2
        assert len(promoted) == 1
        assert {s.id for s in proposed} == {"sg-20260426-111111", "sg-20260426-333333"}


class TestLazyMkdir:
    """T1.6: 5 subdirs created lazily on first write."""

    def test_5_subdirs_lazy_mkdir_on_first_write(self, tmp_path: Path) -> None:
        garage_dir = tmp_path / ".garage"
        store = SuggestionStore(garage_dir)
        # Before write: no skill-suggestions dir
        assert not (garage_dir / SUGGESTIONS_DIR_NAME).exists()

        # First write creates all 5 status subdirs
        store.write(_make_suggestion())

        root = garage_dir / SUGGESTIONS_DIR_NAME
        for status in ("proposed", "accepted", "promoted", "rejected", "expired"):
            assert (root / status).is_dir(), f"{status}/ should be created"


class TestAtomicWrite:
    """T1.7: atomic write — partial file not visible on IO error."""

    def test_atomic_write_no_partial_file_on_failure(self, tmp_path: Path) -> None:
        store = SuggestionStore(tmp_path / ".garage")
        suggestion = _make_suggestion()
        target_path = (
            tmp_path / ".garage" / SUGGESTIONS_DIR_NAME / "proposed" / f"{suggestion.id}.json"
        )

        # Mock os.replace to raise mid-rename → partial tempfile should NOT
        # be visible at the target path
        with patch("garage_os.skill_mining.suggestion_store.os.replace") as mock_replace:
            mock_replace.side_effect = OSError("simulated atomic rename failure")
            with pytest.raises(OSError):
                store.write(suggestion)

        # Target path should not exist (atomic semantics)
        assert not target_path.exists()


class TestRoundTripSerialization:
    """T1.8: write + load = byte-equivalent fields (datetime ISO, list, etc.)."""

    def test_round_trip_serialization(self, tmp_path: Path) -> None:
        store = SuggestionStore(tmp_path / ".garage")
        original = _make_suggestion()
        original.promoted_to_path = "packs/garage/skills/verdict-format/SKILL.md"
        original.rejected_reason = None
        original.extra = {"reviewer_notes": "test"}

        store.write(original)
        loaded = store.load(SkillSuggestionStatus.PROPOSED, original.id)

        assert loaded is not None
        assert loaded.id == original.id
        assert loaded.suggested_name == original.suggested_name
        assert loaded.suggested_description == original.suggested_description
        assert loaded.problem_domain_key == original.problem_domain_key
        assert loaded.tag_bucket == original.tag_bucket
        assert loaded.evidence_entries == original.evidence_entries
        assert loaded.evidence_records == original.evidence_records
        assert loaded.suggested_pack == original.suggested_pack
        assert loaded.score == original.score
        assert loaded.status == original.status
        assert loaded.created_at == original.created_at
        assert loaded.expires_at == original.expires_at
        assert loaded.promoted_to_path == original.promoted_to_path
        assert loaded.rejected_reason == original.rejected_reason
        assert loaded.extra == original.extra
