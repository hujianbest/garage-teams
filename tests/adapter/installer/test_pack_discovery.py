"""Tests for garage_os.adapter.installer.pack_discovery (F007 T3 / FR-701).

Acceptance per task plan T3:

- discover_packs(empty dir) → []
- discover_packs(packs/garage/) → 1 Pack with 1 skill + 1 agent
- pack.json missing or invalid JSON → InvalidPackError
- pack.json.skills[] inconsistent with disk → PackManifestMismatchError
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from garage_os.adapter.installer.pack_discovery import (
    InvalidPackError,
    Pack,
    PackManifestMismatchError,
    discover_packs,
)


def _write_pack_json(pack_dir: Path, **overrides: object) -> None:
    base = {
        "schema_version": 1,
        "pack_id": pack_dir.name,
        "version": "0.1.0",
        "description": "test pack",
        "skills": [],
        "agents": [],
    }
    base.update(overrides)
    (pack_dir / "pack.json").write_text(
        json.dumps(base, indent=2), encoding="utf-8"
    )


def _write_skill(pack_dir: Path, skill_id: str) -> None:
    skill_dir = pack_dir / "skills" / skill_id
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {skill_id}\ndescription: test\n---\n\n# {skill_id}\n",
        encoding="utf-8",
    )


def _write_agent(pack_dir: Path, agent_id: str) -> None:
    agents_dir = pack_dir / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    (agents_dir / f"{agent_id}.md").write_text(
        f"# {agent_id}\n\nMinimal agent.\n", encoding="utf-8"
    )


class TestDiscoverPacks:
    def test_empty_packs_root_returns_empty(self, tmp_path: Path) -> None:
        packs_root = tmp_path / "packs"
        packs_root.mkdir()
        assert discover_packs(packs_root) == []

    def test_missing_packs_root_returns_empty(self, tmp_path: Path) -> None:
        packs_root = tmp_path / "no-such-dir"
        # FR-704 acceptance #3 spec / D7 §14: missing packs/ is non-fatal.
        assert discover_packs(packs_root) == []

    def test_single_pack_with_one_skill_one_agent(self, tmp_path: Path) -> None:
        packs_root = tmp_path / "packs"
        garage = packs_root / "garage"
        garage.mkdir(parents=True)
        _write_pack_json(garage, skills=["garage-hello"], agents=["sample"])
        _write_skill(garage, "garage-hello")
        _write_agent(garage, "sample")

        packs = discover_packs(packs_root)
        assert len(packs) == 1
        pack = packs[0]
        assert isinstance(pack, Pack)
        assert pack.pack_id == "garage"
        assert pack.version == "0.1.0"
        assert pack.schema_version == 1
        assert pack.skills == ["garage-hello"]
        assert pack.agents == ["sample"]

    def test_two_packs_returned_in_pack_id_sorted_order(self, tmp_path: Path) -> None:
        packs_root = tmp_path / "packs"
        for pid in ("zeta", "alpha"):
            pack_dir = packs_root / pid
            pack_dir.mkdir(parents=True)
            _write_pack_json(pack_dir)
        result = discover_packs(packs_root)
        assert [p.pack_id for p in result] == ["alpha", "zeta"]


class TestPackJsonValidation:
    def test_missing_pack_json_raises(self, tmp_path: Path) -> None:
        packs_root = tmp_path / "packs"
        broken = packs_root / "broken"
        broken.mkdir(parents=True)
        with pytest.raises(InvalidPackError) as exc_info:
            discover_packs(packs_root)
        assert "broken" in str(exc_info.value)

    def test_invalid_json_raises(self, tmp_path: Path) -> None:
        packs_root = tmp_path / "packs"
        broken = packs_root / "broken"
        broken.mkdir(parents=True)
        (broken / "pack.json").write_text("{ this is not json", encoding="utf-8")
        with pytest.raises(InvalidPackError):
            discover_packs(packs_root)

    def test_pack_id_not_matching_dir_name_raises(self, tmp_path: Path) -> None:
        packs_root = tmp_path / "packs"
        pack_dir = packs_root / "actual-name"
        pack_dir.mkdir(parents=True)
        _write_pack_json(pack_dir, pack_id="claimed-name")
        with pytest.raises(InvalidPackError) as exc_info:
            discover_packs(packs_root)
        assert "actual-name" in str(exc_info.value)
        assert "claimed-name" in str(exc_info.value)


class TestManifestMismatch:
    def test_skills_list_inconsistent_with_disk_raises(self, tmp_path: Path) -> None:
        packs_root = tmp_path / "packs"
        pack_dir = packs_root / "garage"
        pack_dir.mkdir(parents=True)
        # Manifest claims skill "ghost" exists, but disk has nothing.
        _write_pack_json(pack_dir, skills=["ghost"])
        with pytest.raises(PackManifestMismatchError) as exc_info:
            discover_packs(packs_root)
        assert "ghost" in str(exc_info.value)

    def test_agents_list_inconsistent_with_disk_raises(self, tmp_path: Path) -> None:
        packs_root = tmp_path / "packs"
        pack_dir = packs_root / "garage"
        pack_dir.mkdir(parents=True)
        _write_pack_json(pack_dir, agents=["ghost-agent"])
        with pytest.raises(PackManifestMismatchError) as exc_info:
            discover_packs(packs_root)
        assert "ghost-agent" in str(exc_info.value)

    def test_disk_skill_not_in_manifest_raises(self, tmp_path: Path) -> None:
        packs_root = tmp_path / "packs"
        pack_dir = packs_root / "garage"
        pack_dir.mkdir(parents=True)
        _write_pack_json(pack_dir, skills=[])  # claims none
        _write_skill(pack_dir, "actual-skill")  # disk has one
        with pytest.raises(PackManifestMismatchError):
            discover_packs(packs_root)
