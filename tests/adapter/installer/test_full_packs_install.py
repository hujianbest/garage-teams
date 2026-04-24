"""F008 T4c: full-packs end-to-end integration test.

Covers spec FR-806 acceptance #1-#4 + INV-1 (total 29 skills) + INV-2
(family-asset uniqueness) + INV-4 (byte-level migration sample) + NFR-803
(<=5s wall-clock).

Strategy: link the real packs/ directory into a tmp workspace via symlink
(same pattern as tests/test_cli.py::TestInitWithHosts._link_packs), then
run install_packs() with all three first-class hosts. Assert manifest
shape + N derived from sum(pack.json.skills[]).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from garage_os.adapter.installer.manifest import read_manifest
from garage_os.adapter.installer.pack_discovery import discover_packs
from garage_os.adapter.installer.pipeline import install_packs

REPO_ROOT = Path(__file__).resolve().parents[3]
PACKS_ROOT = REPO_ROOT / "packs"

# F008 ADR-D8-1: family-level shared assets that must appear at most once
# under packs/. Skill-private references/<file>.md with the same basename
# do NOT count (those are skill-internal and can be duplicated).
FAMILY_ASSET_BASENAMES_AND_PATHS = {
    # 4 family shared docs (packs/coding/skills/docs/<file>)
    ("hf-command-entrypoints.md", Path("packs/coding/skills/docs")),
    ("hf-workflow-entrypoints.md", Path("packs/coding/skills/docs")),
    ("hf-workflow-shared-conventions.md", Path("packs/coding/skills/docs")),
    ("hf-worktree-isolation.md", Path("packs/coding/skills/docs")),
    # 6 templates (packs/coding/skills/templates/<file>)
    ("feature-readme-template.md", Path("packs/coding/skills/templates")),
    ("finalize-closeout-pack-template.md", Path("packs/coding/skills/templates")),
    ("task-board-template.md", Path("packs/coding/skills/templates")),
    ("task-progress-template.md", Path("packs/coding/skills/templates")),
    ("verification-record-template.md", Path("packs/coding/skills/templates")),
    # 5 principles (packs/coding/principles/<file>)
    ("skill-anatomy.md", Path("packs/coding/principles")),
    ("hf-sdd-tdd-skill-design.md", Path("packs/coding/principles")),
    ("architectural-health-during-tdd.md", Path("packs/coding/principles")),
    ("methodology-coherence.md", Path("packs/coding/principles")),
    ("sdd-artifact-layout.md", Path("packs/coding/principles")),
    # writing family-level prompts (packs/writing/prompts/<file>)
    ("横纵分析法.md", Path("packs/writing/prompts")),
}


def _link_packs(tmp_path: Path) -> None:
    """Symlink the real packs/ into tmp_path/packs (forward-compatible)."""
    link = tmp_path / "packs"
    if link.exists() or link.is_symlink():
        return
    link.symlink_to(PACKS_ROOT)


class TestFullPacksInstall:
    """End-to-end test: real packs/ installed into tmp workspace."""

    def test_four_packs_total_31_skills_INV1(self) -> None:
        """INV-1: sum(pack.json.skills[] for pack in [coding, garage, search, writing]) == 31.

        Bumped from 30 → 31 (post-PR#25 hotfix): packs/search/ 由用户在 main 直接落入
        (commit 322da15 ai weekly + 0f17188 ai daily skill), 但缺 pack.json/README, 导致
        discover_packs InvalidPackError 拒所有 garage init. 本 cycle 给 packs/search/ 补
        完整 pack metadata, 让 INV-1 升到 31, 同时打通 four-packs install 路径.
        """
        packs = discover_packs(PACKS_ROOT)
        # Index by pack_id for stable assertions regardless of pack order.
        by_id = {p.pack_id: p for p in packs}
        assert set(by_id) == {"coding", "garage", "search", "writing"}, (
            f"expected exactly 4 packs, got {sorted(by_id)}"
        )
        # Per task plan T1b/T2/T3 acceptance + coding v0.2.0 reverse-sync + search hotfix:
        assert len(by_id["coding"].skills) == 23
        assert len(by_id["garage"].skills) == 3
        assert len(by_id["search"].skills) == 1  # ai-weekly only
        assert len(by_id["writing"].skills) == 4
        # INV-1 hard gate (30 → 31 post-search hotfix).
        total = sum(len(p.skills) for p in packs)
        assert total == 31, f"INV-1 violated: total skills = {total} (want 31)"

    def test_family_asset_uniqueness_INV2(self) -> None:
        """INV-2 spec § 4.2 红线 1: each family-level asset appears at most once
        in its designated path under packs/. Skill-private references/<basename>.md
        are excluded by the path-narrowed enumeration."""
        for basename, asset_dir in FAMILY_ASSET_BASENAMES_AND_PATHS:
            target = REPO_ROOT / asset_dir / basename
            assert target.is_file(), (
                f"INV-2 enum requires {target.relative_to(REPO_ROOT)} to exist"
            )
            # And there must be no other copy in the same family-level path
            # (we accept skill-private duplicates by construction here).
            same_dir_matches = list((REPO_ROOT / asset_dir).glob(basename))
            assert len(same_dir_matches) == 1, (
                f"INV-2 violated for {basename}: found {same_dir_matches}"
            )

    def test_install_packs_three_hosts_FR806(self, tmp_path: Path) -> None:
        """FR-806 acceptance #1-#3: garage init --hosts all writes 31 skills × 3 hosts
        + 1 agent × 2 hosts (claude + opencode; cursor has no agent surface).
        """
        _link_packs(tmp_path)

        summary = install_packs(
            workspace_root=tmp_path,
            packs_root=tmp_path / "packs",
            hosts=["claude", "cursor", "opencode"],
        )

        # Per-host skill count == 31 (4 packs: coding 23 + garage 3 + search 1 + writing 4).
        for host_dir in [".claude/skills", ".cursor/skills", ".opencode/skills"]:
            host_root = tmp_path / host_dir
            assert host_root.is_dir(), f"{host_dir} not created"
            skill_subdirs = [d for d in host_root.iterdir() if d.is_dir()]
            assert len(skill_subdirs) == 31, (
                f"{host_dir} has {len(skill_subdirs)} skill dirs, expected 31"
            )

        # Manifest matches.
        manifest = read_manifest(tmp_path / ".garage")
        assert manifest is not None
        assert sorted(manifest.installed_hosts) == ["claude", "cursor", "opencode"]
        assert sorted(manifest.installed_packs) == ["coding", "garage", "search", "writing"]

        # 31 skills × 3 hosts = 93 skill files; 1 agent × 2 hosts (claude + opencode,
        # cursor adapter returns None for target_agent_path) = 2 agent files. Total 95.
        assert len(manifest.files) == 95, (
            f"manifest.files = {len(manifest.files)}, expected 95"
        )

        # Summary returned (skills counted per-write, hence × 3 here too).
        assert isinstance(summary.n_skills, int)
        assert summary.n_skills == 93  # 31 × 3
        assert summary.n_agents == 2  # 1 agent installed to claude + opencode

    def test_skill_byte_level_sample_INV4(self, tmp_path: Path) -> None:
        """INV-4 + CON-803: a sampled hf-* SKILL.md installed to .claude/skills/
        has its main body (after marker injection) byte-identical to the source
        (only diff = 2 lines of injected `installed_by:` + `installed_pack:`)."""
        _link_packs(tmp_path)

        install_packs(
            workspace_root=tmp_path,
            packs_root=tmp_path / "packs",
            hosts=["claude"],
        )

        installed = tmp_path / ".claude/skills/hf-specify/SKILL.md"
        source = REPO_ROOT / "packs/coding/skills/hf-specify/SKILL.md"
        assert installed.exists(), "hf-specify SKILL.md not installed"

        installed_text = installed.read_text(encoding="utf-8")
        source_text = source.read_text(encoding="utf-8")

        # Marker injection is in the front matter; the body after `---\n\n` MUST
        # be byte-identical (the marker only adds two lines inside the YAML
        # front matter block).
        installed_body = installed_text.split("---\n\n", 1)[-1]
        source_body = source_text.split("---\n\n", 1)[-1]
        assert installed_body == source_body, (
            "INV-4 violated: hf-specify SKILL.md body diverged after install"
        )

        # And the marker itself MUST be present.
        assert "installed_by: garage" in installed_text
        assert "installed_pack: coding" in installed_text

    def test_install_packs_under_5_seconds_NFR803(self, tmp_path: Path) -> None:
        """NFR-803: full-packs three-host install wall-clock should be ≤ 5s."""
        _link_packs(tmp_path)

        start = time.monotonic()
        install_packs(
            workspace_root=tmp_path,
            packs_root=tmp_path / "packs",
            hosts=["claude", "cursor", "opencode"],
        )
        elapsed = time.monotonic() - start

        assert elapsed <= 5.0, (
            f"NFR-803 violated: install_packs took {elapsed:.2f}s (limit 5.0s)"
        )
