"""F015 T1 tests: template_generator + multi-line description split + 7-section schema."""

from __future__ import annotations

from garage_os.agent_compose.template_generator import (
    SkillSummary,
    _extract_skill_summary,
    _title_from_name,
    auto_description,
    render,
)


# T1.1
class TestTitleFromName:
    def test_kebab_to_title(self) -> None:
        assert _title_from_name("config-design-agent") == "Config Design Agent"

    def test_single_word(self) -> None:
        assert _title_from_name("agent") == "Agent"


# T1.2 — multi-line description split (Ni-1 r2)
class TestExtractSkillSummary:
    def test_single_line_within_max(self) -> None:
        desc = "适用于 CLI 设计任务"
        assert _extract_skill_summary(desc) == "适用于 CLI 设计任务"

    def test_chinese_period_truncates(self) -> None:
        desc = "适用于设计任务。不适用于其它场景"
        assert _extract_skill_summary(desc) == "适用于设计任务。"

    def test_english_period_truncates(self) -> None:
        desc = "Suitable for X. Not suitable for Y"
        assert _extract_skill_summary(desc) == "Suitable for X."

    def test_multi_line_yaml_pipe(self) -> None:
        # Simulates `description: |` style (e.g. hv-analysis)
        desc = "\n".join([
            "",
            "  适用于深度研究任务。",
            "  使用横纵分析法。",
        ])
        # First non-empty line is "适用于深度研究任务。"; truncated at 。
        assert _extract_skill_summary(desc) == "适用于深度研究任务。"

    def test_empty_returns_empty(self) -> None:
        assert _extract_skill_summary("") == ""
        assert _extract_skill_summary("   \n  \n   ") == ""

    def test_max_chars_truncates(self) -> None:
        desc = "a" * 100
        assert _extract_skill_summary(desc, max_chars=80) == "a" * 80


# T1.3 — auto_description
class TestAutoDescription:
    def test_includes_适用_and_不适用(self) -> None:
        desc = auto_description("config-design-agent", ["hf-specify", "hf-design"])
        assert "适用于" in desc
        assert "不适用" in desc
        assert "hf-specify" in desc
        assert "hf-design" in desc

    def test_min_50_chars(self) -> None:
        desc = auto_description("x", ["s"])
        assert len(desc) >= 50

    def test_empty_skills(self) -> None:
        desc = auto_description("test-agent", [])
        assert "(无 skills)" in desc
        assert len(desc) >= 50


# T1.4 — render: 7-section schema (CON-1504)
class TestRenderFullSchema:
    def test_frontmatter_present(self) -> None:
        skills = [SkillSummary("hf-specify", "适用于规格起草")]
        out = render("test-agent", skills)
        assert out.startswith("---\n")
        assert "name: test-agent" in out
        assert "description:" in out
        # frontmatter delimiter
        assert "\n---\n" in out

    def test_title_heading(self) -> None:
        skills = [SkillSummary("hf-specify", "适用于规格起草")]
        out = render("config-design-agent", skills)
        assert "# Config Design Agent" in out

    def test_ai_generated_comment(self) -> None:
        skills = [SkillSummary("hf-specify", "适用于规格起草")]
        out = render("test-agent", skills)
        assert "AI-generated draft" in out
        assert "hf-test-driven-dev" in out

    def test_when_to_use_section(self) -> None:
        skills = [SkillSummary("hf-specify", "适用于规格起草")]
        out = render("test-agent", skills)
        assert "## When to Use" in out
        assert "hf-specify" in out
        assert "适用于规格起草" in out

    def test_how_it_composes_section(self) -> None:
        skills = [
            SkillSummary("hf-specify", "summary-1"),
            SkillSummary("hf-design", "summary-2"),
        ]
        out = render("test-agent", skills)
        assert "## How It Composes" in out
        # Roles auto-assigned from role_labels
        assert "基础工作流" in out
        assert "风格 / 后处理" in out

    def test_workflow_section(self) -> None:
        skills = [
            SkillSummary("hf-specify", "x"),
            SkillSummary("hf-design", "y"),
        ]
        out = render("test-agent", skills)
        assert "## Workflow" in out
        # Skills appear in order
        idx_specify = out.find("`hf-specify`", out.find("## Workflow"))
        idx_design = out.find("`hf-design`", out.find("## Workflow"))
        assert idx_specify < idx_design

    def test_style_alignment_with_entries(self) -> None:
        skills = [SkillSummary("hf-specify", "x")]
        styles = [("prefer functional Python", "k-001"), ("type hints required", "k-002")]
        out = render("test-agent", skills, style_entries=styles)
        assert "## Style Alignment" in out
        assert "k-001" in out
        assert "prefer functional Python" in out
        assert "k-002" in out

    def test_style_alignment_empty_uses_todo(self) -> None:
        skills = [SkillSummary("hf-specify", "x")]
        out = render("test-agent", skills, style_entries=[])
        assert "## Style Alignment" in out
        assert "TODO" in out

    def test_style_alignment_omitted_with_no_style(self) -> None:
        """--no-style flag → style_entries=None → section omitted entirely."""
        skills = [SkillSummary("hf-specify", "x")]
        out = render("test-agent", skills, style_entries=None)
        assert "## Style Alignment" not in out


# T1.5 — description override
class TestRenderDescriptionOverride:
    def test_user_provided_description_used(self) -> None:
        skills = [SkillSummary("hf-specify", "x")]
        custom = "适用于自定义场景。不适用于其它场景, 用户提供的描述。"
        out = render("test-agent", skills, description=custom)
        assert custom in out


# T1.6 — empty skills (placeholder behavior)
class TestRenderEmptySkills:
    def test_empty_skills_uses_todo(self) -> None:
        out = render("test-agent", [])
        assert "## When to Use" in out
        assert "TODO" in out
        assert "## How It Composes" in out
        assert "## Workflow" in out
