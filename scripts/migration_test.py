#!/usr/bin/env python3
"""
Garage Agent OS – Migration Test Script (T20).

Standalone script that validates migration-critical scenarios:
  1. Simulated new environment – clone to tmp_path, verify all features
  2. Path portability – Path objects behave across OS formats
  3. Legacy data loading – v1 schema data loads via VersionManager
  4. Empty repository initialisation – full .garage/ bootstrap

Usage:
    python scripts/migration_test.py
    uv run python scripts/migration_test.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path, PurePosixPath, PureWindowsPath

# Ensure the project src is importable
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _PROJECT_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from garage_os.platform.version_manager import (
    CompatibilityStatus,
    VersionManager,
    VersionInfo,
    VersionError,
)
from garage_os.storage.file_storage import FileStorage
from garage_os.storage.atomic_writer import AtomicWriter

import yaml


# ---------------------------------------------------------------------------
# Reference .garage/ skeleton
# ---------------------------------------------------------------------------

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


def _init_garage(root: Path) -> Path:
    """Create a full .garage/ structure under *root*."""
    garage = root / ".garage"
    for d in _GARAGE_DIRS:
        (garage / d).mkdir(parents=True, exist_ok=True)
    for relpath, content in _GARAGE_FILES.items():
        fp = garage / relpath
        if isinstance(content, dict):
            _write_json(fp, content)
        else:
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(content, encoding="utf-8")
    for gd in ["sessions/active", "sessions/archived",
                "experience/patterns", "experience/records",
                "knowledge/decisions", "knowledge/patterns", "knowledge/solutions"]:
        (garage / gd / ".gitkeep").touch()
    return garage


class _Reporter:
    """Tiny test runner with coloured output."""

    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0
        self.errors: list[str] = []

    def ok(self, msg: str) -> None:
        self.passed += 1
        print(f"  \033[32m✓\033[0m {msg}")

    def fail(self, msg: str, detail: str = "") -> None:
        self.failed += 1
        self.errors.append(f"{msg}: {detail}")
        print(f"  \033[31m✗\033[0m {msg}")
        if detail:
            print(f"    {detail}")

    def check(self, condition: bool, msg: str, detail: str = "") -> None:
        if condition:
            self.ok(msg)
        else:
            self.fail(msg, detail)

    def summary(self) -> bool:
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Results: {self.passed}/{total} passed, {self.failed} failed")
        if self.errors:
            print("\nFailures:")
            for e in self.errors:
                print(f"  - {e}")
        print(f"{'='*60}")
        return self.failed == 0


# ---------------------------------------------------------------------------
# Test suites
# ---------------------------------------------------------------------------

def test_simulated_new_environment(r: _Reporter) -> None:
    """1) Simulate cloning repo to a fresh tmp_path."""
    print("\n[1] Simulated New Environment")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # Initialise .garage
        garage = _init_garage(root)
        r.check(garage.exists(), ".garage/ directory created")

        # FileStorage works in fresh root
        storage = FileStorage(garage)
        storage.write_json("sessions/active/migration-test.json", {
            "schema_version": 1,
            "task": "T20",
            "status": "running",
        })
        data = storage.read_json("sessions/active/migration-test.json")
        r.check(data is not None and data["task"] == "T20",
                "FileStorage CRUD in fresh env")

        # VersionManager detects v1
        vm = VersionManager()
        version = vm.detect_version(garage / "config" / "platform.json")
        r.check(version.major == 1, "VersionManager detects v1 platform.json")

        data, result = vm.load_with_compatibility(garage / "config" / "platform.json")
        r.check(result.status == CompatibilityStatus.COMPATIBLE,
                "v1 platform.json is COMPATIBLE")

        # AtomicWriter works
        target = root / "atomic" / "test.json"
        checksum = AtomicWriter.write_json(target, {"key": "value"})
        r.check(len(checksum) == 64, "AtomicWriter produces 64-char checksum")
        r.check(AtomicWriter.verify_checksum(target, checksum),
                "AtomicWriter checksum verifies")

        # Write YAML contract
        _write_yaml(garage / "contracts" / "test-iface.yaml", {
            "schema_version": 1,
            "interface": "test-iface",
            "methods": [],
        })
        version = vm.detect_version(garage / "contracts" / "test-iface.yaml")
        r.check(version.major == 1, "VersionManager detects v1 YAML contract")


def test_path_portability(r: _Reporter) -> None:
    """2) Verify Path objects across OS formats."""
    print("\n[2] Path Portability")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        storage = FileStorage(root)

        # POSIX-style relative path
        storage.write_json("config/platform.json", {"ok": True})
        r.check(storage.read_json("config/platform.json") == {"ok": True},
                "POSIX-style relative path works")

        # Forward-slash paths work on all OS
        storage.write_json("a/b/c/deep.json", {"deep": True})
        r.check(storage.read_json("a/b/c/deep.json") == {"deep": True},
                "Deep nested path works")

        # PurePosixPath construction
        posix = PurePosixPath("some/dir/file.json")
        full = root / posix
        full.parent.mkdir(parents=True, exist_ok=True)
        _write_json(full, {"posix": True})
        r.check(full.exists() and json.loads(full.read_text())["posix"],
                "PurePosixPath constructs valid path")

        # PureWindowsPath
        win = PureWindowsPath("some\\dir\\file.json")
        r.check("file.json" in str(win), "PureWindowsPath stringifies correctly")

        # Path.name
        r.check(Path("config/platform.json").name == "platform.json",
                "Path.name extracts filename")
        r.check(Path("tools/registered-tools.yaml").suffix == ".yaml",
                "Path.suffix detects .yaml")

        # Path traversal rejection
        try:
            storage.read_json("../etc/passwd")
            r.fail("Path traversal should be rejected")
        except ValueError:
            r.ok("Path traversal ../ is rejected")

        try:
            storage.write_json("..\\etc\\passwd", {"bad": True})
            r.fail("Windows path traversal should be rejected")
        except ValueError:
            r.ok("Path traversal ..\\ is rejected")


def test_legacy_data_loading(r: _Reporter) -> None:
    """3) Create v1 schema data, verify VersionManager loads it."""
    print("\n[3] Legacy Data Loading (v1 schema)")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        vm = VersionManager(platform_version="0.1.0")

        # v1 platform config
        config = _GARAGE_FILES["config/platform.json"]
        fp = _write_json(root / "platform.json", config)
        data, result = vm.load_with_compatibility(fp)
        r.check(result.status == CompatibilityStatus.COMPATIBLE,
                "v1 platform.json COMPATIBLE")
        r.check(data["platform_name"] == "Garage Agent OS",
                "v1 platform data fully loaded")

        # v1 host-adapter
        adapter = _GARAGE_FILES["config/host-adapter.json"]
        fp = _write_json(root / "host-adapter.json", adapter)
        data, result = vm.load_with_compatibility(fp)
        r.check(result.status == CompatibilityStatus.COMPATIBLE,
                "v1 host-adapter.json COMPATIBLE")
        r.check(data["host_type"] == "claude-code",
                "v1 host-adapter data loaded correctly")

        # v1 knowledge index with entries
        index = {
            "schema_version": 1,
            "entries": [
                {"id": "k001", "type": "decision", "path": "knowledge/decisions/adr-001.md"},
                {"id": "k002", "type": "pattern", "path": "knowledge/patterns/logging.md"},
            ],
        }
        fp = _write_json(root / "index.json", index)
        data, result = vm.load_with_compatibility(fp)
        r.check(len(data["entries"]) == 2, "v1 knowledge index entries preserved")

        # v1 YAML contract
        contract = {
            "schema_version": 1,
            "interface": "test-contract",
            "methods": [{"name": "do_work"}],
        }
        fp = _write_yaml(root / "contract.yaml", contract)
        data, result = vm.load_with_compatibility(fp)
        r.check(data["interface"] == "test-contract",
                "v1 YAML contract loaded correctly")

        # Integer schema_version
        fp = _write_json(root / "int_ver.json", {"schema_version": 1})
        version = vm.detect_version(fp)
        r.check(version == VersionInfo(1, 0, 0),
                "Integer schema_version 1 parsed as 1.0.0")

        # String schema_version
        fp = _write_json(root / "str_ver.json", {"schema_version": "1.0.0"})
        version = vm.detect_version(fp)
        r.check(version == VersionInfo(1, 0, 0),
                "String schema_version '1.0.0' parsed as 1.0.0")

        # v0 backward compatible
        fp = _write_json(root / "v0.json", {"schema_version": 0, "legacy": True})
        data, result = vm.load_with_compatibility(fp)
        r.check(result.status == CompatibilityStatus.BACKWARD_COMPATIBLE,
                "v0 schema is BACKWARD_COMPATIBLE")
        r.check(data["legacy"] is True, "v0 data still loads")

        # v99 incompatible
        fp = _write_json(root / "v99.json", {"schema_version": 99, "feature": "quantum"})
        try:
            vm.load_with_compatibility(fp)
            r.fail("v99 should raise VersionError")
        except VersionError:
            r.ok("v99 raises VersionError (incompatible)")


def test_empty_repo_init(r: _Reporter) -> None:
    """4) Bootstrap full .garage/ structure from scratch."""
    print("\n[4] Empty Repository Initialisation")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        garage = _init_garage(root)

        # All directories exist
        all_dirs_ok = True
        for d in _GARAGE_DIRS:
            if not (garage / d).is_dir():
                all_dirs_ok = False
                r.fail(f"Missing directory: {d}")
        r.check(all_dirs_ok, "All .garage/ subdirectories created")

        # Key config files exist
        key_files = [
            "config/platform.json",
            "config/host-adapter.json",
            "knowledge/.metadata/index.json",
            "README.md",
        ]
        all_files_ok = True
        for f in key_files:
            if not (garage / f).exists():
                all_files_ok = False
                r.fail(f"Missing file: {f}")
        r.check(all_files_ok, "All key config files created")

        # .gitkeep files
        gitkeep_dirs = [
            "sessions/active", "sessions/archived",
            "experience/patterns", "experience/records",
            "knowledge/decisions", "knowledge/patterns", "knowledge/solutions",
        ]
        gitkeep_ok = all(
            (garage / gd / ".gitkeep").exists() for gd in gitkeep_dirs
        )
        r.check(gitkeep_ok, "All .gitkeep files present")

        # VersionManager validates all JSON configs
        vm = VersionManager()
        configs_valid = True
        for json_file in ["config/platform.json", "config/host-adapter.json",
                          "knowledge/.metadata/index.json"]:
            fp = garage / json_file
            version = vm.detect_version(fp)
            result = vm.check_compatibility(version)
            if result.status != CompatibilityStatus.COMPATIBLE:
                configs_valid = False
                r.fail(f"{json_file} not COMPATIBLE", str(result.status))
        r.check(configs_valid, "All initialised configs pass VersionManager check")

        # Functional: can write and read data
        storage = FileStorage(garage)
        storage.write_json("sessions/active/init-test.json", {
            "schema_version": 1, "task": "bootstrap",
        })
        r.check(
            storage.read_json("sessions/active/init-test.json")["task"] == "bootstrap",
            "FileStorage works on initialised structure",
        )

        # Idempotent: second init does not corrupt
        storage.write_json("knowledge/solutions/existing.json", {"answer": 42})
        _init_garage(root)  # second init
        r.check(
            storage.read_json("knowledge/solutions/existing.json")["answer"] == 42,
            "Re-initialisation preserves existing data",
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print("=" * 60)
    print("Garage Agent OS – Migration Test Script (T20)")
    print("=" * 60)

    r = _Reporter()
    test_simulated_new_environment(r)
    test_path_portability(r)
    test_legacy_data_loading(r)
    test_empty_repo_init(r)

    success = r.summary()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
