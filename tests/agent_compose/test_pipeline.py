"""F015 T3 tests: pipeline.compute_status_summary + AgentComposeStatus."""

from __future__ import annotations

from pathlib import Path

from garage_os.agent_compose.pipeline import (
    FIRST_CLASS_PACKS,
    AgentComposeStatus,
    compute_status_summary,
)


# T3.pipeline.1
class TestComputeStatusEmpty:
    def test_no_packs_root_returns_empty(self, tmp_path: Path) -> None:
        # packs_root does not exist
        result = compute_status_summary(tmp_path / "nonexistent")
        assert result.counts_by_pack == {}
        assert result.metadata_lines == []


# T3.pipeline.2
class TestComputeStatusGaragePack:
    def test_garage_pack_with_agents(self, tmp_path: Path) -> None:
        packs_root = tmp_path / "packs"
        agents_dir = packs_root / "garage" / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "agent-a.md").write_text("---\nname: agent-a\n---\n")
        (agents_dir / "agent-b.md").write_text("---\nname: agent-b\n---\n")
        (agents_dir / "agent-c.md").write_text("---\nname: agent-c\n---\n")

        result = compute_status_summary(packs_root)
        assert result.counts_by_pack["garage"] == 3
        assert "Agent compose: garage has 3 agents" in result.metadata_lines


# T3.pipeline.3
class TestComputeStatusEmptyAgentsDir:
    def test_empty_agents_dir_zero_count(self, tmp_path: Path) -> None:
        packs_root = tmp_path / "packs"
        agents_dir = packs_root / "garage" / "agents"
        agents_dir.mkdir(parents=True)
        # No .md files

        result = compute_status_summary(packs_root)
        assert result.counts_by_pack["garage"] == 0
        assert "Agent compose: garage has 0 agents" in result.metadata_lines


# T3.pipeline.4
class TestComputeStatusMissingAgentsDir:
    def test_pack_without_agents_dir_silently_skipped(self, tmp_path: Path) -> None:
        packs_root = tmp_path / "packs"
        (packs_root / "coding").mkdir(parents=True)
        # coding has no agents/ dir
        # garage has agents/
        (packs_root / "garage" / "agents").mkdir(parents=True)
        (packs_root / "garage" / "agents" / "x.md").write_text("---\nname: x\n---\n")

        result = compute_status_summary(packs_root)
        assert "garage" in result.counts_by_pack
        assert "coding" not in result.counts_by_pack  # silently skipped


# T3.pipeline.5
class TestFirstClassPacks:
    def test_first_class_pack_list(self) -> None:
        # Sentinel: ensure FIRST_CLASS_PACKS is the documented set
        assert "garage" in FIRST_CLASS_PACKS
        assert "coding" in FIRST_CLASS_PACKS
        assert "writing" in FIRST_CLASS_PACKS


# T3.pipeline.6
class TestMultiplePacks:
    def test_multiple_packs_all_listed(self, tmp_path: Path) -> None:
        packs_root = tmp_path / "packs"
        for pack_id, n_agents in [("garage", 3), ("coding", 1)]:
            agents_dir = packs_root / pack_id / "agents"
            agents_dir.mkdir(parents=True)
            for i in range(n_agents):
                (agents_dir / f"agent-{i}.md").write_text("---\nname: x\n---\n")

        result = compute_status_summary(packs_root)
        assert result.counts_by_pack == {"garage": 3, "coding": 1}
        assert any("garage has 3" in line for line in result.metadata_lines)
        assert any("coding has 1" in line for line in result.metadata_lines)
