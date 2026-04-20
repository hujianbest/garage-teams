"""
Tests for VersionManager – Platform Contract & Version Management (T17).

Test design seeds:
  1. Version detection: load a v1-format file → correctly identified
  2. Backward compatibility: old-schema data → loads without error
  3. Version incompatibility: unsupported future version → clear error
  4. Upgrade path: v1 → v2 migration (reserved empty method)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from garage_os.platform.version_manager import (
    CompatibilityStatus,
    VersionError,
    VersionInfo,
    VersionManager,
    register_migration,
    _MIGRATION_REGISTRY,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def vm() -> VersionManager:
    """A default VersionManager instance."""
    return VersionManager(platform_version="0.1.0")


@pytest.fixture
def tmp_contracts(tmp_path: Path) -> Path:
    """Create a temporary .garage/contracts directory with sample files."""
    contracts_dir = tmp_path / "contracts"
    contracts_dir.mkdir()
    return contracts_dir


def _write_json(path: Path, data: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def _write_yaml(path: Path, data: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh)
    return path


# ===========================================================================
# 1. Version detection
# ===========================================================================

class TestDetectVersion:
    """Seed 1 – Loading a v1-format file should be correctly identified."""

    def test_detect_json_v1(self, vm: VersionManager, tmp_contracts: Path):
        """Detect schema_version from a JSON v1 contract file."""
        f = _write_json(
            tmp_contracts / "platform.json",
            {"schema_version": 1, "platform_name": "Garage Agent OS"},
        )
        version = vm.detect_version(f)
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0

    def test_detect_yaml_v1(self, vm: VersionManager, tmp_contracts: Path):
        """Detect schema_version from a YAML v1 contract file."""
        f = _write_yaml(
            tmp_contracts / "session.yaml",
            {"schema_version": 1, "methods": [{"name": "create"}]},
        )
        version = vm.detect_version(f)
        assert version.major == 1

    def test_detect_missing_file(self, vm: VersionManager, tmp_path: Path):
        """Raise FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            vm.detect_version(tmp_path / "nonexistent.json")

    def test_detect_missing_version_field(
        self, vm: VersionManager, tmp_contracts: Path
    ):
        """Raise ValueError when schema_version field is absent."""
        f = _write_json(tmp_contracts / "bad.json", {"data": "no version"})
        with pytest.raises(ValueError, match="schema_version"):
            vm.detect_version(f)

    def test_detect_unsupported_format(
        self, vm: VersionManager, tmp_contracts: Path
    ):
        """Raise ValueError for unsupported file formats."""
        f = tmp_contracts / "contract.toml"
        f.write_text('schema_version = 1', encoding="utf-8")
        with pytest.raises(ValueError, match="Unsupported file format"):
            vm.detect_version(f)

    def test_detect_string_version(
        self, vm: VersionManager, tmp_contracts: Path
    ):
        """Detect version when schema_version is a full semver string."""
        f = _write_json(
            tmp_contracts / "semver.json",
            {"schema_version": "1.2.3"},
        )
        version = vm.detect_version(f)
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3


# ===========================================================================
# 2. Backward compatibility
# ===========================================================================

class TestBackwardCompatibility:
    """Seed 2 – Old schema data should load without error."""

    def test_old_version_backward_compatible(self, vm: VersionManager):
        """A version lower than supported range is backward-compatible."""
        old_version = VersionInfo(major=0, minor=9, patch=0)
        result = vm.check_compatibility(old_version)
        assert result.status == CompatibilityStatus.BACKWARD_COMPATIBLE

    def test_load_backward_compatible_file(
        self, vm: VersionManager, tmp_contracts: Path
    ):
        """Loading a v0 file should not raise – backward compatible."""
        f = _write_json(
            tmp_contracts / "old.json",
            {"schema_version": 0, "legacy": True},
        )
        data, result = vm.load_with_compatibility(f)
        assert data["legacy"] is True
        assert result.status == CompatibilityStatus.BACKWARD_COMPATIBLE


# ===========================================================================
# 3. Version incompatibility
# ===========================================================================

class TestVersionIncompatibility:
    """Seed 3 – Unsupported future version → clear error."""

    def test_future_version_incompatible(self, vm: VersionManager):
        """A version newer than max supported is incompatible."""
        future = VersionInfo(major=99, minor=0, patch=0)
        result = vm.check_compatibility(future)
        assert result.status == CompatibilityStatus.INCOMPATIBLE
        assert any("newer" in issue for issue in result.issues)

    def test_load_incompatible_file_raises(
        self, vm: VersionManager, tmp_contracts: Path
    ):
        """Loading an incompatible file should raise VersionError."""
        f = _write_json(
            tmp_contracts / "future.json",
            {"schema_version": 99, "feature": "quantum"},
        )
        with pytest.raises(VersionError):
            vm.load_with_compatibility(f)

    def test_incompatible_error_message(
        self, vm: VersionManager, tmp_contracts: Path
    ):
        """Error message should mention the version mismatch."""
        f = _write_json(
            tmp_contracts / "v5.json",
            {"schema_version": 5, "data": "stuff"},
        )
        with pytest.raises(VersionError, match="newer"):
            vm.load_with_compatibility(f)


# ===========================================================================
# 4. Upgrade path / migration
# ===========================================================================

class TestMigration:
    """Seed 4 – v1→v2 migration (reserved empty method)."""

    def test_migrate_same_version_is_noop(self, vm: VersionManager):
        """Migrating from v1 to v1 should return data unchanged."""
        data = {"schema_version": 1, "key": "value"}
        result = vm.migrate(data, "1", "1")
        assert result == data

    def test_migrate_unregistered_path_raises(self, vm: VersionManager):
        """Migrating between unregistered versions should raise."""
        data = {"schema_version": 1}
        # Ensure v1→v3 is not registered
        _MIGRATION_REGISTRY.pop((1, 3), None)
        with pytest.raises(VersionError, match="No migration path"):
            vm.migrate(data, "1", "3")

    def test_v1_to_v2_migration_registered(self, vm: VersionManager):
        """Register a v1→v2 migration and verify it runs correctly."""
        # Register a migration for the test
        _MIGRATION_REGISTRY[(1, 2)] = lambda d: {**d, "new_field": "migrated"}

        data = {"schema_version": 1, "old_field": "data"}
        result = vm.migrate(data, "1", "2")

        assert result["schema_version"] == 2
        assert result["old_field"] == "data"
        assert result["new_field"] == "migrated"

        # Clean up
        _MIGRATION_REGISTRY.pop((1, 2), None)

    def test_register_migration_decorator(self, vm: VersionManager):
        """The @register_migration decorator works correctly."""

        @register_migration(2, 3)
        def v2_to_v3(data: dict) -> dict:
            data["v3_feature"] = True
            return data

        data = {"schema_version": 2, "content": "hello"}
        result = vm.migrate(data, "2", "3")

        assert result["schema_version"] == 3
        assert result["v3_feature"] is True
        assert result["content"] == "hello"

        # Clean up
        _MIGRATION_REGISTRY.pop((2, 3), None)


# ===========================================================================
# VersionInfo parsing
# ===========================================================================

class TestVersionInfoParsing:
    """Unit tests for VersionInfo.parse()."""

    def test_parse_integer(self):
        info = VersionInfo.parse("1")
        assert info.major == 1
        assert info.minor == 0
        assert info.patch == 0

    def test_parse_short(self):
        info = VersionInfo.parse("2.1")
        assert info.major == 2
        assert info.minor == 1
        assert info.patch == 0

    def test_parse_full_semver(self):
        info = VersionInfo.parse("0.1.0")
        assert info.major == 0
        assert info.minor == 1
        assert info.patch == 0

    def test_parse_with_label(self):
        info = VersionInfo.parse("1.2.3-beta")
        assert info.major == 1
        assert info.minor == 2
        assert info.patch == 3
        assert info.label == "beta"

    def test_str_roundtrip(self):
        info = VersionInfo.parse("1.2.3")
        assert str(info) == "1.2.3"

    def test_comparison(self):
        v1 = VersionInfo.parse("1.0.0")
        v2 = VersionInfo.parse("2.0.0")
        assert v1 < v2
        assert v2 > v1
        assert v1 != v2
        assert v1 == VersionInfo(major=1, minor=0, patch=0)


# ===========================================================================
# Helpers / integration
# ===========================================================================

class TestHelpers:
    """Helper methods on VersionManager."""

    def test_get_supported_versions(self, vm: VersionManager):
        versions = vm.get_supported_versions()
        assert "1" in versions

    def test_current_schema_version(self):
        vm = VersionManager()
        assert vm.CURRENT_SCHEMA_VERSION == 1

    def test_custom_supported_versions(self):
        vm = VersionManager(supported_versions=[1, 2, 3])
        assert vm.get_supported_versions() == ["1", "2", "3"]

    def test_compatible_exact_match(self, vm: VersionManager):
        """v1 file vs platform that supports v1 → COMPATIBLE."""
        result = vm.check_compatibility(VersionInfo.parse("1"))
        assert result.status == CompatibilityStatus.COMPATIBLE
        assert result.issues == []

    def test_load_real_platform_config(self):
        """Integration: detect version of the actual platform.json."""
        project_root = Path("/mnt/e/workspace/Garage")
        platform_json = project_root / ".garage" / "config" / "platform.json"
        if platform_json.exists():
            vm = VersionManager()
            version = vm.detect_version(platform_json)
            assert version.major == 1
            data, result = vm.load_with_compatibility(platform_json)
            assert result.status == CompatibilityStatus.COMPATIBLE
            assert data["platform_name"] == "Garage Agent OS"


# ---------------------------------------------------------------------------
# F007 CON-703: host-installer.json schema_version is recognized
# ---------------------------------------------------------------------------


class TestHostInstallerSchemaRegistered:
    """F007 CON-703 + design D7 §11.2:

    The install manifest at ``.garage/config/host-installer.json`` carries
    ``schema_version=1`` and must be recognized by VersionManager so future
    upgrades have a planned migration path.

    Implementation note: VersionManager is path-based, not name-based; so
    "registration" here means: a manifest written by
    ``garage_os.adapter.installer.manifest.write_manifest`` produces a file
    that VersionManager can detect & classify as COMPATIBLE.
    """

    def test_host_installer_schema_recognized(self, tmp_path: Path, vm: VersionManager) -> None:
        from garage_os.adapter.installer.manifest import (
            MANIFEST_SCHEMA_VERSION,
            Manifest,
            write_manifest,
        )

        garage_dir = tmp_path / ".garage"
        manifest = Manifest(
            schema_version=MANIFEST_SCHEMA_VERSION,
            installed_hosts=["claude"],
            installed_packs=["garage"],
            installed_at="2026-04-19T12:00:00",
            files=[],
        )
        write_manifest(garage_dir, manifest)

        manifest_path = garage_dir / "config" / "host-installer.json"
        assert manifest_path.is_file()

        # detect_version must read schema_version=1 successfully.
        version = vm.detect_version(manifest_path)
        assert version.major == MANIFEST_SCHEMA_VERSION

        # check_compatibility must classify as COMPATIBLE.
        result = vm.check_compatibility(version)
        assert result.status == CompatibilityStatus.COMPATIBLE

    def test_manifest_constant_pinned_to_one(self) -> None:
        # Sentinel: bumping MANIFEST_SCHEMA_VERSION must be a deliberate act.
        # If this fails, also update VersionManager.SUPPORTED_VERSIONS and
        # write a migration in _MIGRATION_REGISTRY (per CON-703).
        from garage_os.adapter.installer.manifest import MANIFEST_SCHEMA_VERSION

        assert MANIFEST_SCHEMA_VERSION == 1
