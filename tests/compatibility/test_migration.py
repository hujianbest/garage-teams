"""
Migration & compatibility tests – Garage Agent OS T20.

Covers four migration-critical dimensions:
  1. Simulated new environment  – tmp_path clone scenario
  2. Path portability           – Path objects across OS formats
  3. Legacy data loading        – v1 schema data via VersionManager
  4. Empty repo initialisation  – full .garage/ structure bootstrap
"""

from __future__ import annotations

import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath

import pytest
import yaml

from garage_os.platform.version_manager import (
    CompatibilityStatus,
    VersionManager,
    VersionInfo,
    VersionError,
    register_migration,
    _MIGRATION_REGISTRY,
)
from garage_os.storage.file_storage import FileStorage
from garage_os.storage.atomic_writer import AtomicWriter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_json(path: Path, data: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def _write_yaml(path: Path, data: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh)
    return path


# Reference .garage/ skeleton (relative dirs and files that must exist)
_GARAGE_DIRS = [
    "config",
    "config/tools",
    "contracts",
    "experience",
    "experience/patterns",
    "experience/records",
    "knowledge",
    "knowledge/.metadata",
    "knowledge/decisions",
    "knowledge/patterns",
    "knowledge/solutions",
    "sessions",
    "sessions/active",
    "sessions/archived",
]

_GARAGE_FILES: dict[str, str | dict] = {
    "README.md": "# Garage Internal Surface\n",
    "config/platform.json": {
        "schema_version": 1,
        "platform_name": "Garage Agent OS",
        "stage": 1,
        "storage_mode": "artifact-first",
        "host_type": "claude-code",
        "session_timeout_seconds": 7200,
        "max_active_sessions": 1,
        "knowledge_indexing": "manual",
    },
    "config/host-adapter.json": {
        "schema_version": 1,
        "host_type": "claude-code",
        "interaction_mode": "file-system",
        "capabilities": {
            "session_state_api": False,
            "file_read_write": True,
            "memory_auto_load": True,
            "subprocess": True,
        },
    },
    "knowledge/.metadata/index.json": {
        "schema_version": 1,
        "entries": [],
    },
}


# ===========================================================================
# 1. Simulated new environment
# ===========================================================================

class TestSimulatedNewEnvironment:
    """Simulate cloning the repo to a fresh environment (tmp_path) and
    verify that all Garage OS functionality works correctly."""

    def test_file_storage_in_fresh_root(self, tmp_path: Path):
        """FileStorage should work in a brand-new tmp directory."""
        storage = FileStorage(tmp_path / "data")
        storage.write_json("test.json", {"hello": "world"})
        assert storage.read_json("test.json") == {"hello": "world"}

    def test_version_manager_on_cloned_config(self, tmp_path: Path):
        """A 'cloned' platform.json in tmp_path should be detected as v1."""
        garage_dir = tmp_path / ".garage"
        config_dir = garage_dir / "config"
        config_dir.mkdir(parents=True)

        _write_json(config_dir / "platform.json", _GARAGE_FILES["config/platform.json"])

        vm = VersionManager(platform_version="0.1.0")
        version = vm.detect_version(config_dir / "platform.json")
        assert version.major == 1

        data, result = vm.load_with_compatibility(config_dir / "platform.json")
        assert result.status == CompatibilityStatus.COMPATIBLE
        assert data["platform_name"] == "Garage Agent OS"

    def test_atomic_write_in_fresh_env(self, tmp_path: Path):
        """AtomicWriter should function correctly in a temp directory."""
        target = tmp_path / "output" / "file.json"
        checksum = AtomicWriter.write_json(target, {"key": "value"})
        assert len(checksum) == 64
        assert AtomicWriter.read_json(target) == {"key": "value"}
        assert AtomicWriter.verify_checksum(target, checksum)

    def test_full_workflow_in_tmp(self, tmp_path: Path):
        """End-to-end: initialise .garage, write config, detect version, load."""
        garage = tmp_path / ".garage"
        for d in _GARAGE_DIRS:
            (garage / d).mkdir(parents=True, exist_ok=True)

        # Write key config files
        for relpath, content in _GARAGE_FILES.items():
            fp = garage / relpath
            if isinstance(content, dict):
                _write_json(fp, content)
            else:
                fp.parent.mkdir(parents=True, exist_ok=True)
                fp.write_text(content, encoding="utf-8")

        # Add gitkeep files
        for gitkeep_dir in ["sessions/active", "sessions/archived"]:
            (garage / gitkeep_dir / ".gitkeep").touch()

        # Verify structure
        assert (garage / "config" / "platform.json").exists()
        assert (garage / "config" / "host-adapter.json").exists()
        assert (garage / "knowledge" / ".metadata" / "index.json").exists()
        assert (garage / "sessions" / "active" / ".gitkeep").exists()

        # Use VersionManager
        vm = VersionManager()
        version = vm.detect_version(garage / "config" / "platform.json")
        assert version.major == 1

        data, result = vm.load_with_compatibility(garage / "config" / "platform.json")
        assert result.status == CompatibilityStatus.COMPATIBLE
        assert data["schema_version"] == 1

    def test_file_storage_crud_in_simulated_env(self, tmp_path: Path):
        """Full CRUD cycle in a simulated cloned environment."""
        storage = FileStorage(tmp_path / ".garage")

        # Create
        storage.write_json("sessions/active/session-001.json", {
            "schema_version": 1,
            "task": "T20 migration test",
            "status": "active",
        })

        # Read
        data = storage.read_json("sessions/active/session-001.json")
        assert data["task"] == "T20 migration test"

        # Update
        storage.write_json("sessions/active/session-001.json", {
            **data,
            "status": "completed",
        })
        updated = storage.read_json("sessions/active/session-001.json")
        assert updated["status"] == "completed"

        # Delete
        assert storage.delete("sessions/active/session-001.json")
        assert storage.read_json("sessions/active/session-001.json") is None


# ===========================================================================
# 2. Path portability
# ===========================================================================

class TestPathPortability:
    """Verify Path objects behave correctly across OS formats."""

    def test_posix_style_relative_path(self, tmp_path: Path):
        """FileStorage should handle POSIX-style relative paths."""
        storage = FileStorage(tmp_path)
        storage.write_json("config/platform.json", {"schema_version": 1})
        assert storage.read_json("config/platform.json") == {"schema_version": 1}

    def test_windows_style_path_segments(self, tmp_path: Path):
        """FileStorage should handle paths with forward slashes (works on all OS)."""
        storage = FileStorage(tmp_path)
        rel = "config/tools/registered-tools.json"
        storage.write_json(rel, {"tools": []})
        data = storage.read_json(rel)
        assert data["tools"] == []

    def test_path_object_resolution(self, tmp_path: Path):
        """Path objects should resolve correctly regardless of construction."""
        posix = PurePosixPath("config/platform.json")
        full_path = tmp_path / posix
        full_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(full_path, {"ok": True})

        # Read via Path object
        assert json.loads(full_path.read_text(encoding="utf-8"))["ok"] is True

    def test_mixed_path_construction(self, tmp_path: Path):
        """Mixing Path / str should produce valid results."""
        storage = FileStorage(tmp_path)
        storage.write_json("a/b/c.json", {"nested": True})

        # Verify via Path object
        p = tmp_path / "a" / "b" / "c.json"
        assert p.exists()
        assert json.loads(p.read_text(encoding="utf-8"))["nested"] is True

    def test_pure_path_conversions(self):
        """PurePosixPath and PureWindowsPath convert to string correctly."""
        posix_path = PurePosixPath("some/nested/dir/file.json")
        assert "some" in str(posix_path)
        assert "file.json" in str(posix_path)

        win_path = PureWindowsPath("some\\nested\\dir\\file.json")
        assert "file.json" in str(win_path)

    def test_path_name_extraction(self):
        """Path.name should return the filename regardless of separator style."""
        assert Path("config/platform.json").name == "platform.json"
        assert Path("config/tools/registered-tools.yaml").name == "registered-tools.yaml"

    def test_path_suffix_detection(self):
        """Path.suffix should work for version detection file-type checks."""
        assert Path("platform.json").suffix == ".json"
        assert Path("session.yaml").suffix == ".yaml"
        assert Path("contract.yml").suffix == ".yml"
        assert Path("readme.md").suffix == ".md"

    def test_path_parent_traversal(self, tmp_path: Path):
        """Path.parent should navigate upward correctly."""
        deep = tmp_path / "a" / "b" / "c"
        assert deep.parent == tmp_path / "a" / "b"
        assert deep.parent.parent == tmp_path / "a"
        assert deep.parent.parent.parent == tmp_path

    def test_file_storage_rejects_traversal(self, tmp_path: Path):
        """FileStorage must reject path traversal on all OS."""
        storage = FileStorage(tmp_path)
        with pytest.raises(ValueError, match="Path traversal"):
            storage.read_json("../etc/passwd")
        with pytest.raises(ValueError, match="Path traversal"):
            storage.write_json("..\\windows\\system32\\config.json", {"bad": True})


# ===========================================================================
# 3. Legacy data loading (v1 schema)
# ===========================================================================

class TestLegacyDataLoading:
    """Create v1 schema data and verify VersionManager loads it correctly."""

    @pytest.fixture
    def vm(self) -> VersionManager:
        return VersionManager(platform_version="0.1.0")

    def test_load_v1_platform_config(self, vm: VersionManager, tmp_path: Path):
        """Load a v1 platform.json and verify all fields."""
        config = {
            "schema_version": 1,
            "platform_name": "Garage Agent OS",
            "stage": 1,
            "storage_mode": "artifact-first",
            "host_type": "claude-code",
            "session_timeout_seconds": 7200,
            "max_active_sessions": 1,
            "knowledge_indexing": "manual",
        }
        fp = _write_json(tmp_path / "platform.json", config)
        data, result = vm.load_with_compatibility(fp)
        assert result.status == CompatibilityStatus.COMPATIBLE
        assert data["platform_name"] == "Garage Agent OS"
        assert data["schema_version"] == 1

    def test_load_v1_host_adapter(self, vm: VersionManager, tmp_path: Path):
        """Load a v1 host-adapter.json."""
        adapter_config = {
            "schema_version": 1,
            "host_type": "claude-code",
            "interaction_mode": "file-system",
            "capabilities": {
                "session_state_api": False,
                "file_read_write": True,
                "memory_auto_load": True,
                "subprocess": True,
            },
        }
        fp = _write_json(tmp_path / "host-adapter.json", adapter_config)
        data, result = vm.load_with_compatibility(fp)
        assert result.status == CompatibilityStatus.COMPATIBLE
        assert data["host_type"] == "claude-code"
        assert data["capabilities"]["file_read_write"] is True

    def test_load_v1_knowledge_index(self, vm: VersionManager, tmp_path: Path):
        """Load a v1 knowledge index."""
        index = {
            "schema_version": 1,
            "entries": [
                {"id": "k001", "type": "decision", "path": "knowledge/decisions/adr-001.md"},
                {"id": "k002", "type": "pattern", "path": "knowledge/patterns/logging.md"},
            ],
        }
        fp = _write_json(tmp_path / "index.json", index)
        data, result = vm.load_with_compatibility(fp)
        assert result.status == CompatibilityStatus.COMPATIBLE
        assert len(data["entries"]) == 2

    def test_load_v1_yaml_contract(self, vm: VersionManager, tmp_path: Path):
        """Load a v1 YAML contract file."""
        contract = {
            "schema_version": 1,
            "interface": "test-interface",
            "methods": [
                {"name": "do_stuff", "params": [], "returns": {"type": "bool"}},
            ],
        }
        fp = _write_yaml(tmp_path / "contract.yaml", contract)
        data, result = vm.load_with_compatibility(fp)
        assert result.status == CompatibilityStatus.COMPATIBLE
        assert data["interface"] == "test-interface"

    def test_detect_v1_integer_version(self, vm: VersionManager, tmp_path: Path):
        """Detect version when schema_version is an integer (not string)."""
        fp = _write_json(tmp_path / "int_version.json", {"schema_version": 1})
        version = vm.detect_version(fp)
        assert version == VersionInfo(major=1, minor=0, patch=0)

    def test_detect_v1_string_version(self, vm: VersionManager, tmp_path: Path):
        """Detect version when schema_version is a semver string."""
        fp = _write_json(tmp_path / "str_version.json", {"schema_version": "1.0.0"})
        version = vm.detect_version(fp)
        assert version == VersionInfo(major=1, minor=0, patch=0)

    def test_backward_compatible_v0_data(self, vm: VersionManager, tmp_path: Path):
        """v0 (pre-release) data should load as backward-compatible."""
        legacy = {
            "schema_version": 0,
            "platform_name": "Legacy Garage",
            "legacy_field": True,
        }
        fp = _write_json(tmp_path / "legacy.json", legacy)
        data, result = vm.load_with_compatibility(fp)
        assert result.status == CompatibilityStatus.BACKWARD_COMPATIBLE
        assert data["legacy_field"] is True

    def test_incompatible_future_version(self, vm: VersionManager, tmp_path: Path):
        """v99 data should be rejected as incompatible."""
        future = {"schema_version": 99, "feature": "quantum-entangle"}
        fp = _write_json(tmp_path / "future.json", future)
        with pytest.raises(VersionError):
            vm.load_with_compatibility(fp)


# ===========================================================================
# 4. Empty repository initialisation
# ===========================================================================

class TestEmptyRepoInit:
    """Bootstrap a complete .garage/ structure from scratch."""

    def test_init_creates_all_directories(self, tmp_path: Path):
        """Initialisation should create every required .garage/ subdirectory."""
        garage = tmp_path / ".garage"
        for d in _GARAGE_DIRS:
            (garage / d).mkdir(parents=True, exist_ok=True)

        for d in _GARAGE_DIRS:
            assert (garage / d).is_dir(), f"Missing directory: {d}"

    def test_init_creates_all_config_files(self, tmp_path: Path):
        """Initialisation should create all default config files."""
        garage = tmp_path / ".garage"
        config_dir = garage / "config"
        config_dir.mkdir(parents=True)

        for relpath, content in _GARAGE_FILES.items():
            fp = garage / relpath
            if isinstance(content, dict):
                _write_json(fp, content)
            else:
                fp.parent.mkdir(parents=True, exist_ok=True)
                fp.write_text(content, encoding="utf-8")

        # Verify JSON configs have valid schema_version
        vm = VersionManager()
        for json_file in ["config/platform.json", "config/host-adapter.json",
                          "knowledge/.metadata/index.json"]:
            fp = garage / json_file
            assert fp.exists(), f"Missing file: {json_file}"
            version = vm.detect_version(fp)
            assert version.major == 1

    def test_init_creates_gitkeep_files(self, tmp_path: Path):
        """Empty directories should have .gitkeep files."""
        garage = tmp_path / ".garage"
        for d in _GARAGE_DIRS:
            (garage / d).mkdir(parents=True, exist_ok=True)

        gitkeep_dirs = [
            "sessions/active",
            "sessions/archived",
            "experience/patterns",
            "experience/records",
            "knowledge/decisions",
            "knowledge/patterns",
            "knowledge/solutions",
        ]
        for gd in gitkeep_dirs:
            (garage / gd / ".gitkeep").touch()

        for gd in gitkeep_dirs:
            assert (garage / gd / ".gitkeep").exists(), f"Missing .gitkeep in {gd}"

    def test_init_structure_is_functional(self, tmp_path: Path):
        """The initialised .garage/ should be fully usable for storage."""
        garage = tmp_path / ".garage"
        for d in _GARAGE_DIRS:
            (garage / d).mkdir(parents=True, exist_ok=True)

        for relpath, content in _GARAGE_FILES.items():
            fp = garage / relpath
            if isinstance(content, dict):
                _write_json(fp, content)
            else:
                fp.parent.mkdir(parents=True, exist_ok=True)
                fp.write_text(content, encoding="utf-8")

        # FileStorage can use the initialised garage
        storage = FileStorage(garage)
        storage.write_json("sessions/active/test-session.json", {
            "schema_version": 1,
            "task": "T20",
        })
        assert storage.read_json("sessions/active/test-session.json")["task"] == "T20"

        # Write a contract
        storage.write_text(
            "contracts/test-interface.yaml",
            "interface: test-interface\nversion: '1'\n",
        )
        assert storage.read_text("contracts/test-interface.yaml") is not None

    def test_init_idempotent(self, tmp_path: Path):
        """Running initialisation twice should not corrupt existing data."""
        garage = tmp_path / ".garage"

        # First init
        for d in _GARAGE_DIRS:
            (garage / d).mkdir(parents=True, exist_ok=True)
        _write_json(garage / "config" / "platform.json", _GARAGE_FILES["config/platform.json"])

        # Simulate user data
        storage = FileStorage(garage)
        storage.write_json("knowledge/solutions/sol-001.json", {"answer": 42})

        # Second init (idempotent)
        for d in _GARAGE_DIRS:
            (garage / d).mkdir(parents=True, exist_ok=True)
        _write_json(garage / "config" / "platform.json", _GARAGE_FILES["config/platform.json"])

        # User data must survive
        assert storage.read_json("knowledge/solutions/sol-001.json")["answer"] == 42

    def test_init_verifiable_with_version_manager(self, tmp_path: Path):
        """VersionManager can detect and validate all initialised config files."""
        garage = tmp_path / ".garage"
        for d in _GARAGE_DIRS:
            (garage / d).mkdir(parents=True, exist_ok=True)

        for relpath, content in _GARAGE_FILES.items():
            fp = garage / relpath
            if isinstance(content, dict):
                _write_json(fp, content)
            else:
                fp.parent.mkdir(parents=True, exist_ok=True)
                fp.write_text(content, encoding="utf-8")

        vm = VersionManager()
        config_files = [
            "config/platform.json",
            "config/host-adapter.json",
            "knowledge/.metadata/index.json",
        ]
        for cf in config_files:
            version = vm.detect_version(garage / cf)
            result = vm.check_compatibility(version)
            assert result.status == CompatibilityStatus.COMPATIBLE, (
                f"{cf} not compatible: {result.status}"
            )
