"""F013-A T3 tests: template_generator 6 sections + skill-anatomy compliance."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from garage_os.knowledge.experience_index import ExperienceIndex
from garage_os.knowledge.knowledge_store import KnowledgeStore
from garage_os.skill_mining.template_generator import (
    _render_frontmatter,
    _render_output_contract,
    _render_red_flags,
    _render_verification,
    _render_when_to_use,
    _render_workflow,
    render,
    render_minimal,
)
from garage_os.skill_mining.types import SkillSuggestion, SkillSuggestionStatus
from garage_os.storage.file_storage import FileStorage
from garage_os.types import ExperienceRecord, KnowledgeEntry, KnowledgeType


def _make_suggestion(
    evidence_entries: list[str] | None = None,
    evidence_records: list[str] | None = None,
) -> SkillSuggestion:
    now = datetime(2026, 4, 26, 12, 0, 0)
    return SkillSuggestion(
        id="sg-20260426-aabbcc",
        suggested_name="verdict-format",
        suggested_description=(
            "适用于审阅 review verdict 时按 5 段格式 (verdict / findings / "
            "recommendations / 通过条件 / 计数) 产出. 不适用于代码 review."
        ),
        problem_domain_key="review-verdict",
        tag_bucket=["5-section", "verdict-format"],
        evidence_entries=evidence_entries or [],
        evidence_records=evidence_records or [],
        suggested_pack="garage",
        score=1.5,
        status=SkillSuggestionStatus.PROPOSED,
        created_at=now,
        expires_at=now + timedelta(days=30),
    )


def _record(
    rid: str,
    *,
    task_type: str = "review",
    key_patterns: list[str] | None = None,
    lessons_learned: list[str] | None = None,
    pitfalls: list[str] | None = None,
    source_evidence_anchors: list[dict] | None = None,
) -> ExperienceRecord:
    return ExperienceRecord(
        record_id=rid,
        task_type=task_type,
        skill_ids=["hf-code-review"],
        tech_stack=["python"],
        domain="dev",
        problem_domain="review-verdict",
        outcome="success",
        duration_seconds=300,
        complexity="medium",
        session_id=f"ses-{rid}",
        key_patterns=key_patterns if key_patterns is not None else ["verdict-format"],
        lessons_learned=lessons_learned or [],
        pitfalls=pitfalls or [],
        source_evidence_anchors=source_evidence_anchors or [],
    )


def _entry(eid: str, type_: KnowledgeType = KnowledgeType.DECISION) -> KnowledgeEntry:
    return KnowledgeEntry(
        id=eid,
        type=type_,
        topic="review-verdict",
        date=datetime(2026, 4, 26),
        tags=["verdict-format", "5-section"],
        content="...",
    )


# T3.1
class TestRenderFrontmatter:
    def test_name_and_description(self) -> None:
        s = _make_suggestion()
        out = _render_frontmatter(s)
        assert out.startswith("---\n")
        assert "name: verdict-format" in out
        assert "description: 适用于" in out
        assert out.endswith("---\n")


# T3.2
class TestRenderWhenToUse:
    def test_from_task_types(self) -> None:
        records = [_record(f"r-{i}", task_type="review") for i in range(3)]
        out = _render_when_to_use(records)
        assert "## When to Use" in out
        assert "适用" in out
        assert "review" in out
        assert "不适用" in out

    def test_empty_evidence_falls_back_to_todo(self) -> None:
        out = _render_when_to_use([])
        assert "TODO" in out


# T3.3
class TestRenderWorkflow:
    def test_from_lessons_learned(self) -> None:
        records = [
            _record("r-1", lessons_learned=["先 read spec, 再 design"]),
            _record("r-2", lessons_learned=["每个 review 必引 line number"]),
        ]
        out = _render_workflow(records)
        assert "## Workflow" in out
        assert "先 read spec" in out
        assert "每个 review 必引" in out


# T3.4
class TestRenderOutputContract:
    def test_from_knowledge_types(self) -> None:
        entries = [_entry(f"e-{i}", KnowledgeType.DECISION) for i in range(2)] + [
            _entry("e-3", KnowledgeType.PATTERN)
        ]
        out = _render_output_contract(entries)
        assert "## Output Contract" in out
        assert "decision" in out
        assert "pattern" in out


# T3.5
class TestRenderRedFlags:
    def test_includes_pitfalls(self) -> None:
        records = [
            _record("r-1", pitfalls=["不要直接 commit promote 后的 SKILL.md"]),
            _record("r-2", pitfalls=["不要 reject 不写 reason"]),
        ]
        out = _render_red_flags(records)
        assert "## Red Flags" in out
        assert "不要直接 commit" in out
        assert "不要 reject" in out

    def test_empty_pitfalls_falls_back_todo(self) -> None:
        out = _render_red_flags([_record("r-1", pitfalls=[])])
        assert "TODO" in out


# T3.6
class TestRenderVerificationWithAnchor:
    def test_render_verification_with_evidence_anchor(self) -> None:
        records = [
            _record(
                "r-1",
                source_evidence_anchors=[{"commit_sha": "abc1234", "test_count": 12}],
            ),
            _record(
                "r-2",
                source_evidence_anchors=[{"commit_sha": "def5678", "test_count": 8}],
            ),
        ]
        out = _render_verification(records)
        assert "## Verification" in out
        assert "abc1234" in out
        assert "def5678" in out
        assert "10" in out  # avg 10


# T3.7
class TestRenderVerificationPlaceholder:
    def test_no_anchors_uses_todo(self) -> None:
        records = [_record("r-1", source_evidence_anchors=[])]
        out = _render_verification(records)
        assert "TODO" in out


# T3.8
class TestDescriptionMin50:
    def test_description_meets_50_char_min(self) -> None:
        s = _make_suggestion()
        # constraint: description ≥ 50 chars
        assert len(s.suggested_description) >= 50


# T3.9
class TestRenderTotalUnder300Lines:
    def test_full_render_under_300_lines(self, tmp_path: Path) -> None:
        garage_dir = tmp_path / ".garage"
        storage = FileStorage(garage_dir)
        ks = KnowledgeStore(storage)
        ei = ExperienceIndex(storage)

        # Seed
        for i in range(5):
            ei.store(_record(
                f"r-{i}",
                lessons_learned=[f"lesson {i}-a", f"lesson {i}-b"],
                pitfalls=[f"pitfall {i}"],
                source_evidence_anchors=[{"commit_sha": f"sha{i:04d}", "test_count": i}],
            ))
        for i in range(3):
            ks.store(_entry(f"e-{i}"))

        s = _make_suggestion(
            evidence_entries=[f"e-{i}" for i in range(3)],
            evidence_records=[f"r-{i}" for i in range(5)],
        )
        out = render(s, ks, ei)

        assert out.count("\n") <= 300


# T3.10
class TestRobustMinimalEvidence:
    def test_render_minimal_when_evidence_missing(self) -> None:
        s = _make_suggestion(evidence_entries=[], evidence_records=[])
        out = render_minimal(s)
        assert "## When to Use" in out
        assert "## Workflow" in out
        assert "## Output Contract" in out
        assert "## Red Flags" in out
        assert "## Verification" in out
        assert "TODO" in out

    def test_render_with_missing_referenced_evidence(self, tmp_path: Path) -> None:
        """Suggestion references e-1 but KS doesn't have it → render robust."""
        garage_dir = tmp_path / ".garage"
        storage = FileStorage(garage_dir)
        ks = KnowledgeStore(storage)
        ei = ExperienceIndex(storage)

        s = _make_suggestion(
            evidence_entries=["nonexistent-e"],
            evidence_records=["nonexistent-r"],
        )
        out = render(s, ks, ei)
        # Should still produce all 6 sections (just with TODO placeholders)
        assert "name: verdict-format" in out
        assert "## When to Use" in out
        assert "## Workflow" in out
        assert "## Output Contract" in out
        assert "## Red Flags" in out
        assert "## Verification" in out
