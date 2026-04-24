"""F008 T4c: packs/garage/ extended (1 → 3 skill, version 0.1.0 → 0.2.0).

Covers spec FR-803 acceptance #1-#3 + design ADR-D8-5 (garage-sample-agent
preserved) + ADR-D8-6 (version bump rule).
"""

from __future__ import annotations

from pathlib import Path

from garage_os.adapter.installer.pack_discovery import discover_packs

REPO_ROOT = Path(__file__).resolve().parents[3]
PACKS_ROOT = REPO_ROOT / "packs"


class TestPacksGarageExtended:
    """T3 (garage扩容): packs/garage/ now ships 3 skills + 1 agent + version 0.2.0."""

    def test_garage_pack_has_3_skills_FR803(self) -> None:
        """FR-803 acceptance #1: pack.json skills[] = 3, set-equivalent to
        {garage-hello, find-skills, writing-skills}."""
        packs = discover_packs(PACKS_ROOT)
        garage = next((p for p in packs if p.pack_id == "garage"), None)
        assert garage is not None, "packs/garage/ pack not discovered"
        assert len(garage.skills) == 3, (
            f"garage skills[] length = {len(garage.skills)}, expected 3"
        )
        assert set(garage.skills) == {
            "find-skills",
            "garage-hello",
            "writing-skills",
        }, f"garage skills set mismatch: {set(garage.skills)}"

    def test_garage_pack_version_bumped_ADR_D8_6(self) -> None:
        """ADR-D8-6 + F011: packs/garage/ version 0.2.0 → 0.3.0 (F011 加 2 production agent)."""
        packs = discover_packs(PACKS_ROOT)
        garage = next((p for p in packs if p.pack_id == "garage"), None)
        assert garage is not None
        assert garage.version == "0.3.0", (
            f"garage pack version = {garage.version!r}, expected '0.3.0' per F011 (was '0.2.0' in F008)"
        )

    def test_garage_pack_agents_preserved_ADR_D8_5(self) -> None:
        """ADR-D8-5 + F011: garage-sample-agent.md preserved + F011 加 2 production agent
        (code-review-agent + blog-writing-agent), agents 数 1 → 3."""
        packs = discover_packs(PACKS_ROOT)
        garage = next((p for p in packs if p.pack_id == "garage"), None)
        assert garage is not None
        # F011: 3 agents (alphabetical: blog-writing-agent, code-review-agent, garage-sample-agent)
        assert sorted(garage.agents) == [
            "blog-writing-agent",
            "code-review-agent",
            "garage-sample-agent",
        ], (
            f"garage agents = {garage.agents}, expected 3 agents (F011 加 2 production agent + sample preserved)"
        )

    def test_writing_skills_subdir_complete_FR803(self) -> None:
        """FR-803 acceptance #3: writing-skills subdirectory cp -r 1:1 from
        upstream (含 examples/ + render-graphs.js + reference .md)."""
        ws_dir = PACKS_ROOT / "garage" / "skills" / "writing-skills"
        # SKILL.md is the entry.
        assert (ws_dir / "SKILL.md").is_file()
        # Reference docs.
        assert (ws_dir / "anthropic-best-practices.md").is_file()
        assert (ws_dir / "persuasion-principles.md").is_file()
        assert (ws_dir / "testing-skills-with-subagents.md").is_file()
        # Helper script (not executable per design § 17 deferred — that's a D9
        # candidate).
        assert (ws_dir / "render-graphs.js").is_file()
        assert (ws_dir / "graphviz-conventions.dot").is_file()
        # Examples subdir for testing patterns.
        assert (ws_dir / "examples").is_dir()
        # CLAUDE_MD_TESTING.md is the meta/教学 file kept whole per
        # ADR-D8-9 (14 host-specific term hits but exempt).
        assert (ws_dir / "examples" / "CLAUDE_MD_TESTING.md").is_file()
