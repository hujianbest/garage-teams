"""F015 T2 tests: AgentComposer compose() + missing skill semantics + STYLE entries."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from garage_os.agent_compose.composer import (
    KEBAB_NAME_RE,
    _find_skill_md,
    _parse_skill_description,
    compose,
)
from garage_os.knowledge.knowledge_store import KnowledgeStore
from garage_os.storage.file_storage import FileStorage
from garage_os.types import KnowledgeEntry, KnowledgeType


# Helper: create a minimal SKILL.md
def _write_skill_md(packs_root: Path, pack_id: str, skill_id: str, description: str) -> Path:
    skill_dir = packs_root / pack_id / "skills" / skill_id
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(
        f"---\nname: {skill_id}\ndescription: {description}\n---\n\n# {skill_id}\n",
        encoding="utf-8",
    )
    return skill_md


def _setup(tmp_path: Path) -> tuple[Path, KnowledgeStore]:
    packs_root = tmp_path / "packs"
    packs_root.mkdir()
    (packs_root / "garage").mkdir()
    storage = FileStorage(tmp_path / ".garage")
    ks = KnowledgeStore(storage)
    return packs_root, ks


# T2.1
class TestKebabValidation:
    def test_kebab_name_re(self) -> None:
        assert KEBAB_NAME_RE.match("config-design-agent") is not None
        assert KEBAB_NAME_RE.match("agent") is not None
        assert KEBAB_NAME_RE.match("a-1-b") is not None

    def test_invalid_kebab(self) -> None:
        # Underscore, capitals, leading/trailing hyphen all rejected
        assert KEBAB_NAME_RE.match("Config-Design") is None
        assert KEBAB_NAME_RE.match("config_design") is None
        assert KEBAB_NAME_RE.match("-leading") is None
        assert KEBAB_NAME_RE.match("trailing-") is None
        assert KEBAB_NAME_RE.match("") is None


# T2.2
class TestParseSkillDescription:
    def test_single_line_description(self, tmp_path: Path) -> None:
        skill_md = _write_skill_md(tmp_path, "garage", "test-skill", "适用于测试场景")
        assert _parse_skill_description(skill_md) == "适用于测试场景"

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        assert _parse_skill_description(tmp_path / "nonexistent.md") == ""

    def test_no_frontmatter_returns_empty(self, tmp_path: Path) -> None:
        path = tmp_path / "x.md"
        path.write_text("# No frontmatter\nbody", encoding="utf-8")
        assert _parse_skill_description(path) == ""

    def test_multi_line_yaml_pipe(self, tmp_path: Path) -> None:
        path = tmp_path / "y.md"
        path.write_text(
            "---\n"
            "name: hv-analysis\n"
            "description: |\n"
            "  适用于深度研究任务。\n"
            "  使用横纵分析法。\n"
            "---\n"
            "# Body\n",
            encoding="utf-8",
        )
        result = _parse_skill_description(path)
        assert "适用于深度研究任务。" in result


# T2.3
class TestFindSkillMd:
    def test_find_skill_in_garage_pack(self, tmp_path: Path) -> None:
        packs_root, _ = _setup(tmp_path)
        skill_md = _write_skill_md(packs_root, "garage", "find-skills", "x")
        assert _find_skill_md(packs_root, "find-skills") == skill_md

    def test_find_skill_in_coding_pack(self, tmp_path: Path) -> None:
        packs_root, _ = _setup(tmp_path)
        (packs_root / "coding").mkdir()
        skill_md = _write_skill_md(packs_root, "coding", "hf-specify", "x")
        assert _find_skill_md(packs_root, "hf-specify") == skill_md

    def test_find_missing_returns_none(self, tmp_path: Path) -> None:
        packs_root, _ = _setup(tmp_path)
        assert _find_skill_md(packs_root, "nonexistent") is None


# T2.4 — Happy path
class TestComposeHappyPath:
    def test_compose_with_2_skills_and_1_style_entry(self, tmp_path: Path) -> None:
        packs_root, ks = _setup(tmp_path)
        _write_skill_md(packs_root, "garage", "hf-specify", "适用于规格起草。详见上游。")
        _write_skill_md(packs_root, "garage", "hf-design", "适用于设计起草。")
        ks.store(KnowledgeEntry(
            id="k-001",
            type=KnowledgeType.STYLE,
            topic="prefer functional Python",
            date=datetime(2026, 4, 26, 10, 0, 0),
            tags=["python"],
            content="prefer functional",
        ))

        result = compose(
            name="config-design-agent",
            skill_ids=["hf-specify", "hf-design"],
            packs_root=packs_root,
            knowledge_store=ks,
        )
        assert result.missing_skills == []
        assert result.style_count == 1
        assert result.target_pack_exists is True
        assert result.draft.name == "config-design-agent"
        assert "## When to Use" in result.draft.body
        assert "## Style Alignment" in result.draft.body
        assert "k-001" in result.draft.body
        assert "prefer functional Python" in result.draft.body
        assert "hf-specify" in result.draft.body
        assert "hf-design" in result.draft.body


# T2.5 — missing skills (Im-1 r2 双层语义)
class TestMissingSkillSemantics:
    def test_library_returns_partial_draft_on_missing(self, tmp_path: Path) -> None:
        packs_root, ks = _setup(tmp_path)
        _write_skill_md(packs_root, "garage", "hf-specify", "x")

        result = compose(
            name="test-agent",
            skill_ids=["hf-specify", "nonexistent-skill"],
            packs_root=packs_root,
            knowledge_store=ks,
        )
        # Library: still produces draft (Im-1 r2)
        assert result.missing_skills == ["nonexistent-skill"]
        assert "nonexistent-skill" in result.draft.body  # placeholder retained
        assert "hf-specify" in result.draft.body


# T2.6 — empty skills validation
class TestEmptySkillsValidation:
    def test_raises_on_empty_skill_ids(self, tmp_path: Path) -> None:
        packs_root, ks = _setup(tmp_path)
        with pytest.raises(ValueError, match="at least one skill"):
            compose(
                name="x",
                skill_ids=[],
                packs_root=packs_root,
                knowledge_store=ks,
            )


# T2.7 — invalid kebab name validation
class TestInvalidNameValidation:
    def test_raises_on_invalid_kebab(self, tmp_path: Path) -> None:
        packs_root, ks = _setup(tmp_path)
        with pytest.raises(ValueError, match="kebab-case"):
            compose(
                name="Config_Design",  # underscore + caps
                skill_ids=["hf-specify"],
                packs_root=packs_root,
                knowledge_store=ks,
            )


# T2.8 — target pack not exists
class TestTargetPackNotExists:
    def test_target_pack_exists_false(self, tmp_path: Path) -> None:
        packs_root, ks = _setup(tmp_path)
        _write_skill_md(packs_root, "garage", "hf-specify", "x")

        result = compose(
            name="x",
            skill_ids=["hf-specify"],
            packs_root=packs_root,
            knowledge_store=ks,
            target_pack="nonexistent-pack",
        )
        assert result.target_pack_exists is False
        # Library still generates draft (Im-1 r2)
        assert result.draft is not None


# T2.9 — STYLE not included
class TestStyleExclusion:
    def test_no_style_omits_section(self, tmp_path: Path) -> None:
        packs_root, ks = _setup(tmp_path)
        _write_skill_md(packs_root, "garage", "hf-specify", "x")
        ks.store(KnowledgeEntry(
            id="k-001",
            type=KnowledgeType.STYLE,
            topic="topic-x",
            date=datetime(2026, 4, 26, 10, 0, 0),
            tags=[],
            content="x",
        ))

        result = compose(
            name="x",
            skill_ids=["hf-specify"],
            packs_root=packs_root,
            knowledge_store=ks,
            include_style=False,
        )
        assert result.style_count == 0
        assert "## Style Alignment" not in result.draft.body


# T2.10 — STYLE empty (placeholder)
class TestStyleEmpty:
    def test_empty_style_uses_todo(self, tmp_path: Path) -> None:
        packs_root, ks = _setup(tmp_path)
        _write_skill_md(packs_root, "garage", "hf-specify", "x")
        # No STYLE entries

        result = compose(
            name="x",
            skill_ids=["hf-specify"],
            packs_root=packs_root,
            knowledge_store=ks,
            include_style=True,
        )
        assert result.style_count == 0
        assert "## Style Alignment" in result.draft.body
        assert "TODO" in result.draft.body


# T2.11 — description override
class TestDescriptionOverride:
    def test_user_description_used(self, tmp_path: Path) -> None:
        packs_root, ks = _setup(tmp_path)
        _write_skill_md(packs_root, "garage", "hf-specify", "x")
        custom = "适用于自定义场景。不适用于其它场景, 用户提供的描述。"
        result = compose(
            name="x",
            skill_ids=["hf-specify"],
            packs_root=packs_root,
            knowledge_store=ks,
            description=custom,
        )
        assert custom in result.draft.body
        assert result.draft.description == custom


# T2.12 — multi-line skill description (hv-analysis style)
class TestMultiLineSkillDescription:
    def test_multi_line_yaml_pipe_description_truncated(self, tmp_path: Path) -> None:
        packs_root, ks = _setup(tmp_path)
        skill_dir = packs_root / "writing" / "skills" / "hv-analysis"
        skill_dir.mkdir(parents=True)
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            "---\n"
            "name: hv-analysis\n"
            "description: |\n"
            "  适用于深度研究任务。\n"
            "  使用横纵分析法。\n"
            "---\n"
            "# Body\n",
            encoding="utf-8",
        )
        result = compose(
            name="x",
            skill_ids=["hv-analysis"],
            packs_root=packs_root,
            knowledge_store=ks,
        )
        # Should find skill and pick first line summary
        assert result.missing_skills == []
        assert "适用于深度研究任务。" in result.draft.body
