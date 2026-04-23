"""F008 T4c: dogfood layout invariants (ADR-D8-2 candidate C).

Covers spec FR-805 acceptance #1-#4 + design ADR-D8-2 (`.agents/skills/`
removed + IDE 重定向 to dogfood install products) + INV-6 (.agents/skills/
absent) + INV-7 (IDE load chain) + INV-8 (dogfood paths in .gitignore).
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


class TestDogfoodLayout:
    """ADR-D8-2 candidate C: .agents/skills/ deleted + IDE 入口转向 dogfood 产物."""

    def test_agents_skills_removed_INV6(self) -> None:
        """INV-6 + spec § 4.2 红线 2: .agents/skills/ MUST NOT exist after T4a."""
        agents_skills = REPO_ROOT / ".agents" / "skills"
        assert not agents_skills.exists(), (
            f"FR-805 violated: {agents_skills} still exists; T4a should have "
            "rm -rf'd it per ADR-D8-2 candidate C."
        )

    def test_gitignore_excludes_dogfood_INV8(self) -> None:
        """INV-8: .gitignore MUST contain `.cursor/skills/` and `.claude/skills/`
        as exclusion patterns so dogfood products don't get committed."""
        gitignore_text = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
        assert ".cursor/skills/" in gitignore_text, (
            "INV-8 violated: .gitignore missing `.cursor/skills/` exclusion"
        )
        assert ".claude/skills/" in gitignore_text, (
            "INV-8 violated: .gitignore missing `.claude/skills/` exclusion"
        )

    def test_agents_md_skill_anatomy_path_红线_4(self) -> None:
        """spec § 4.2 红线 4: AGENTS.md MUST still reference docs/principles/
        skill-anatomy.md (the 5-minute cold-read entrypoint must not break)."""
        agents_md_text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        assert "docs/principles/skill-anatomy.md" in agents_md_text, (
            "Red line 4 violated: AGENTS.md no longer references "
            "docs/principles/skill-anatomy.md (5-minute cold-read chain broken)"
        )
        # And the file must actually exist on disk.
        assert (REPO_ROOT / "docs" / "principles" / "skill-anatomy.md").is_file(), (
            "Red line 4 violated: docs/principles/skill-anatomy.md missing on disk"
        )

    def test_agents_md_dogfood_onboarding_present(self) -> None:
        """T4b acceptance: AGENTS.md MUST contain `garage init --hosts cursor,claude`
        onboarding command for first-time-clone contributors (ADR-D8-2 candidate C)."""
        agents_md_text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        assert "garage init --hosts cursor,claude" in agents_md_text, (
            "ADR-D8-2 candidate C onboarding command not found in AGENTS.md"
        )

    def test_agents_md_packs_table_includes_coding_writing(self) -> None:
        """T4b acceptance #1: AGENTS.md Packs table MUST include packs/coding/
        and packs/writing/ rows (structural check — not just grep on '已落地')."""
        agents_md_text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        assert "packs/coding/" in agents_md_text, (
            "AGENTS.md Packs table missing packs/coding/ row"
        )
        assert "packs/writing/" in agents_md_text, (
            "AGENTS.md Packs table missing packs/writing/ row"
        )

    def test_skill_writing_principle_section_intact_防误改(self) -> None:
        """T4b: 防误改: ## Skill 写作原则 段落 MUST still exist (T4b only allowed
        local refresh of Packs section, not removal of other sections)."""
        agents_md_text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        assert "## Skill 写作原则" in agents_md_text, (
            "T4b violated 防误改: ## Skill 写作原则 section disappeared from AGENTS.md"
        )
