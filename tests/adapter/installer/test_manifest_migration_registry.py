"""F012-E T5 tests: VersionManager registration (F009 carry-forward, FR-1214 + ADR-D12-6 r2)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# Import manifest first to trigger module-level @register_migration(1, 2)
from garage_os.adapter.installer import manifest as manifest_module
from garage_os.adapter.installer.manifest import (
    MANIFEST_SCHEMA_VERSION,
    Manifest,
    _migrate_v1_to_v2_dict_form,
    migrate_v1_to_v2,
    read_manifest,
    write_manifest,
)
from garage_os.platform.version_manager import (
    VersionManager,
    _MIGRATION_REGISTRY,
)


def _get_supported_versions() -> list[int]:
    return list(VersionManager.SUPPORTED_VERSIONS)


class TestVersionManagerRegistry:
    """FR-1214 + ADR-D12-6 r2: registry contains (1, 2) entry."""

    def test_registry_has_1_to_2_entry(self) -> None:
        assert (1, 2) in _MIGRATION_REGISTRY

    def test_registered_function_is_dict_wrapper(self) -> None:
        registered = _MIGRATION_REGISTRY[(1, 2)]
        assert registered is _migrate_v1_to_v2_dict_form

    def test_supported_versions_includes_2(self) -> None:
        """SUPPORTED_VERSIONS = [1, 2] per ADR-D12-6 r2 + M-1 fix."""
        supported = _get_supported_versions()
        assert 1 in supported
        assert 2 in supported


class TestDictWrapperEquivalence:
    """ADR-D12-6 r2: double-source equivalence (dict-form vs dataclass-form)
    for schema_version + files[].scope. dst differs (fast-path uses workspace_root,
    dict-form leaves as-is); equivalence checked at schema field layer only.
    """

    def test_dict_form_sets_schema_2(self) -> None:
        v1_dict = {
            "schema_version": 1,
            "installed_hosts": ["claude"],
            "installed_packs": ["test-pack"],
            "installed_at": "2026-04-25T00:00:00",
            "files": [
                {
                    "src": "packs/test-pack/skills/x/SKILL.md",
                    "dst": ".claude/skills/x/SKILL.md",
                    "host": "claude",
                    "pack_id": "test-pack",
                    "content_hash": "abc",
                }
            ],
        }
        out = _migrate_v1_to_v2_dict_form(v1_dict)
        assert out["schema_version"] == 2
        assert out["files"][0]["scope"] == "project"
        # dst untouched in dict-form (per ADR-D12-6 r2 trade-off)
        assert out["files"][0]["dst"] == ".claude/skills/x/SKILL.md"
        # Other fields preserved
        assert out["installed_hosts"] == ["claude"]
        assert out["installed_packs"] == ["test-pack"]

    def test_existing_scope_preserved(self) -> None:
        v1_dict = {
            "schema_version": 1,
            "installed_hosts": [], "installed_packs": [], "installed_at": "x",
            "files": [
                {"src": "a", "dst": "b", "host": "claude", "pack_id": "p",
                 "content_hash": "h", "scope": "user"},  # already has scope
            ],
        }
        out = _migrate_v1_to_v2_dict_form(v1_dict)
        # Pre-existing scope preserved (not overwritten)
        assert out["files"][0]["scope"] == "user"

    def test_dataclass_and_dict_forms_agree_on_schema_fields(
        self, tmp_path: Path
    ) -> None:
        """Both forms produce schema_version=2 + scope='project' for plain v1 input."""
        # Dataclass form
        v1_manifest = Manifest(
            schema_version=1,
            installed_hosts=["claude"],
            installed_packs=["test"],
            installed_at="2026-04-25T00:00:00",
            files=[
                manifest_module.ManifestFileEntry(
                    src="packs/test/skills/x/SKILL.md",
                    dst=".claude/skills/x/SKILL.md",
                    host="claude",
                    pack_id="test",
                    content_hash="abc",
                ),
            ],
        )
        v2_dataclass = migrate_v1_to_v2(v1_manifest, tmp_path)
        # Equivalent dict-form input
        v1_dict = {
            "schema_version": 1,
            "installed_hosts": ["claude"],
            "installed_packs": ["test"],
            "installed_at": "2026-04-25T00:00:00",
            "files": [
                {
                    "src": "packs/test/skills/x/SKILL.md",
                    "dst": ".claude/skills/x/SKILL.md",
                    "host": "claude",
                    "pack_id": "test",
                    "content_hash": "abc",
                }
            ],
        }
        v2_dict = _migrate_v1_to_v2_dict_form(v1_dict)
        # Schema layer agreement
        assert v2_dataclass.schema_version == v2_dict["schema_version"]
        assert v2_dataclass.installed_hosts == v2_dict["installed_hosts"]
        assert v2_dataclass.installed_packs == v2_dict["installed_packs"]
        assert v2_dataclass.installed_at == v2_dict["installed_at"]
        assert v2_dataclass.files[0].scope == v2_dict["files"][0]["scope"]
        # dst differs (dataclass form: workspace_root-prefixed absolute; dict form: relative)
        # — this is documented trade-off, ignore in equivalence check


class TestF009ReadManifestUnchanged:
    """CON-1202: F009 既有 read_manifest fast-path 行为字节级不变."""

    def test_read_v1_still_auto_migrates_to_v2(self, tmp_path: Path) -> None:
        """F009 既有 schema 1 manifest 读出来仍是 schema 2 (read_manifest 内部 migrate)."""
        garage_dir = tmp_path / ".garage"
        config_dir = garage_dir / "config"
        config_dir.mkdir(parents=True)
        v1_payload = {
            "schema_version": 1,
            "installed_hosts": ["claude"],
            "installed_packs": ["test"],
            "installed_at": "2026-04-25T00:00:00",
            "files": [
                {
                    "src": "packs/test/skills/x/SKILL.md",
                    "dst": ".claude/skills/x/SKILL.md",
                    "host": "claude", "pack_id": "test",
                    "content_hash": "abc",
                }
            ],
        }
        (config_dir / "host-installer.json").write_text(
            json.dumps(v1_payload, indent=2), encoding="utf-8",
        )

        manifest = read_manifest(garage_dir)
        assert manifest is not None
        assert manifest.schema_version == 2
        assert manifest.files[0].scope == "project"
        # dst absolute-prefixed (F009 fast-path with workspace_root)
        assert manifest.files[0].dst.endswith("/.claude/skills/x/SKILL.md")


class TestSentinelVersionConstant:
    """F009 既有 sentinel test still pass (carry-forward)."""

    def test_manifest_schema_version_constant(self) -> None:
        assert MANIFEST_SCHEMA_VERSION == 2
