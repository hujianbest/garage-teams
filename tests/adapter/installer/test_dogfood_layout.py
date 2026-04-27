"""F008 T4c: dogfood layout invariants (ADR-D8-2 candidate C).

Covers spec FR-805 acceptance #1-#4 + design ADR-D8-2 (`.agents/skills/`
removed from git + IDE 重定向 to dogfood install products) + INV-6 (.agents/
skills/ not git-tracked) + INV-7 (IDE load chain) + INV-8 (dogfood paths in
.gitignore).

INV-6 was originally "directory absent on disk", but a follow-up cycle restored
``.agents/skills/`` as a tree of relative symlinks into ``packs/<pack-id>/skills/``
to support cloud-agent runtimes that hard-code the ``.agents/skills/<name>``
lookup path (see ``.agents/README.md`` and ``scripts/setup-agent-skills.sh``).
The original FR-805 intent — no duplicate skill content under git — is preserved
because ``.agents/skills/`` is git-ignored. INV-6 here checks the git-tracked
form, not the on-disk form.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


class TestDogfoodLayout:
    """ADR-D8-2 candidate C: .agents/skills/ not git-tracked + IDE 入口转向 dogfood 产物."""

    def test_agents_skills_removed_INV6(self) -> None:
        """INV-6 (revised) + spec § 4.2 红线 2: .agents/skills/ MUST NOT have any
        git-tracked entries (the on-disk form may exist as relative symlinks into
        packs/<pack-id>/skills/, regenerated locally by scripts/setup-agent-skills.sh
        and excluded from git via .gitignore).

        Original wording asserted directory absence; revised wording aligns with
        the actual FR-805 intent (no duplicate skill content committed) and keeps
        the cloud-agent skill mount point usable.
        """
        result = subprocess.run(
            ["git", "ls-files", ".agents/skills/"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=False,
        )
        tracked = [line for line in result.stdout.splitlines() if line.strip()]
        assert tracked == [], (
            "FR-805 violated: git-tracked entries found under .agents/skills/ — "
            "skill content MUST stay in packs/ (single source of truth). Tracked "
            f"entries: {tracked}"
        )

    def test_gitignore_excludes_dogfood_INV8(self) -> None:
        """INV-8: .gitignore MUST exclude dogfood install products so they don't
        get committed.

        Regression-gate carry-forward: the original wording was `.cursor/skills/` +
        `.claude/skills/` (only skills subdir), but dogfood `garage init --hosts
        cursor,claude` also creates `.claude/agents/` (agent surface) and
        `.garage/config/host-installer.json` (manifest). Widened to exclude
        `.cursor/` + `.claude/` whole dirs (skills/ implied), per design ADR-D8-2
        candidate C 精神. This test accepts either the narrow or wide form.
        """
        gitignore_text = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
        # Either narrow (.cursor/skills/) or wide (.cursor/) form satisfies INV-8.
        assert ".cursor/" in gitignore_text, (
            "INV-8 violated: .gitignore missing `.cursor/` (or `.cursor/skills/`) exclusion"
        )
        assert ".claude/" in gitignore_text, (
            "INV-8 violated: .gitignore missing `.claude/` (or `.claude/skills/`) exclusion"
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

    def test_agents_skills_mount_setup_script_exists(self) -> None:
        """Cloud-agent runtimes resolve skills under .agents/skills/<name>/SKILL.md.
        scripts/setup-agent-skills.sh MUST exist so contributors can regenerate
        the symlink mount after a fresh clone (paired with .gitignore exclusion
        of .agents/skills/).
        """
        setup_script = REPO_ROOT / "scripts" / "setup-agent-skills.sh"
        assert setup_script.is_file(), (
            "scripts/setup-agent-skills.sh missing; cloud-agent skill mount setup "
            "will be impossible after a fresh clone (.agents/skills/ is .gitignore-d)."
        )
        # Content sanity: the script must reference both packs/coding/skills and packs/garage/skills
        content = setup_script.read_text(encoding="utf-8")
        assert "packs/coding/skills" in content, "setup script must symlink coding pack"
        assert "packs/garage/skills" in content, "setup script must symlink garage pack"

    def test_workflow_recall_module_exists(self) -> None:
        """F014 T5 sentinel: workflow_recall package + CLI subcommand registered."""
        wr_dir = REPO_ROOT / "src" / "garage_os" / "workflow_recall"
        assert wr_dir.is_dir(), "F014: src/garage_os/workflow_recall/ missing"
        for module in ("__init__.py", "types.py", "cache.py", "path_recaller.py", "pipeline.py"):
            assert (wr_dir / module).is_file(), f"F014: workflow_recall/{module} missing"

    def test_agents_readme_explains_mount(self) -> None:
        """.agents/README.md MUST explain why .agents/skills/ exists as symlinks
        and how to regenerate it (companion doc to setup-agent-skills.sh).
        """
        readme = REPO_ROOT / ".agents" / "README.md"
        assert readme.is_file(), ".agents/README.md missing (mount-point doc)"
        content = readme.read_text(encoding="utf-8")
        for token in ("symlink", "packs/", "setup-agent-skills.sh"):
            assert token in content, (
                f".agents/README.md must mention '{token}' (mount-point intent doc)"
            )

    def test_skill_writing_principle_section_intact_防误改(self) -> None:
        """T4b: 防误改: ## Skill 写作原则 段落 MUST still exist (T4b only allowed
        local refresh of Packs section, not removal of other sections)."""
        agents_md_text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        assert "## Skill 写作原则" in agents_md_text, (
            "T4b violated 防误改: ## Skill 写作原则 section disappeared from AGENTS.md"
        )
