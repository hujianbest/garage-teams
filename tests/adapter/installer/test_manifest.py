"""Tests for garage_os.adapter.installer.manifest (F007 T3 / FR-705 / NFR-703).

Acceptance:

- MANIFEST_SCHEMA_VERSION = 1 exposed
- Manifest round-trips: write then read returns equivalent object
- ``installed_hosts`` / ``installed_packs`` ASCII-sorted in serialized form
- ``files[]`` sorted by (src, dst)
- ``installed_at`` is ISO-8601 string
- ``content_hash`` is SHA-256 hex (64 chars)
- Paths serialize as POSIX (forward slashes), regardless of OS
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from garage_os.adapter.installer.manifest import (
    MANIFEST_FILENAME,
    MANIFEST_SCHEMA_VERSION,
    Manifest,
    ManifestFileEntry,
    read_manifest,
    write_manifest,
)


def _make_entry(
    src: str = "packs/garage/skills/garage-hello/SKILL.md",
    dst: str = ".claude/skills/garage-hello/SKILL.md",
    host: str = "claude",
    pack_id: str = "garage",
    content_hash: str = "0" * 64,
) -> ManifestFileEntry:
    return ManifestFileEntry(
        src=src, dst=dst, host=host, pack_id=pack_id, content_hash=content_hash
    )


class TestSchemaVersion:
    def test_constant_is_one(self) -> None:
        assert MANIFEST_SCHEMA_VERSION == 1


class TestManifestRoundTrip:
    def test_write_then_read_equivalent(self, tmp_path: Path) -> None:
        garage_dir = tmp_path / ".garage"
        (garage_dir / "config").mkdir(parents=True)
        manifest = Manifest(
            schema_version=1,
            installed_hosts=["claude", "cursor"],
            installed_packs=["garage"],
            installed_at=datetime(2026, 4, 19, 12, 0, 0).isoformat(),
            files=[_make_entry()],
        )
        write_manifest(garage_dir, manifest)
        reloaded = read_manifest(garage_dir)
        assert reloaded == manifest

    def test_read_missing_returns_none(self, tmp_path: Path) -> None:
        garage_dir = tmp_path / ".garage"
        garage_dir.mkdir()
        assert read_manifest(garage_dir) is None


class TestSerializationStability:
    def test_installed_hosts_sorted_in_json(self, tmp_path: Path) -> None:
        garage_dir = tmp_path / ".garage"
        (garage_dir / "config").mkdir(parents=True)
        # Construct in non-sorted order; serialized form must be sorted.
        manifest = Manifest(
            schema_version=1,
            installed_hosts=["cursor", "claude"],
            installed_packs=["zeta", "alpha"],
            installed_at="2026-04-19T12:00:00",
            files=[],
        )
        write_manifest(garage_dir, manifest)
        raw = json.loads((garage_dir / "config" / MANIFEST_FILENAME).read_text())
        assert raw["installed_hosts"] == ["claude", "cursor"]
        assert raw["installed_packs"] == ["alpha", "zeta"]

    def test_files_sorted_by_src_dst(self, tmp_path: Path) -> None:
        garage_dir = tmp_path / ".garage"
        (garage_dir / "config").mkdir(parents=True)
        e1 = _make_entry(
            src="packs/garage/skills/z/SKILL.md",
            dst=".claude/skills/z/SKILL.md",
        )
        e2 = _make_entry(
            src="packs/garage/skills/a/SKILL.md",
            dst=".claude/skills/a/SKILL.md",
        )
        manifest = Manifest(
            schema_version=1,
            installed_hosts=["claude"],
            installed_packs=["garage"],
            installed_at="2026-04-19T12:00:00",
            files=[e1, e2],  # intentionally reverse-sorted
        )
        write_manifest(garage_dir, manifest)
        raw = json.loads((garage_dir / "config" / MANIFEST_FILENAME).read_text())
        srcs = [f["src"] for f in raw["files"]]
        assert srcs == sorted(srcs)


class TestPosixPathSerialization:
    def test_dst_uses_forward_slashes(self, tmp_path: Path) -> None:
        # NFR-703: regardless of OS, manifest serializes POSIX paths.
        garage_dir = tmp_path / ".garage"
        (garage_dir / "config").mkdir(parents=True)
        # Even if dst is built via Path() that may use OS-native separators,
        # serialization must always produce '/'-style strings.
        dst_native = str(Path(".claude") / "skills" / "garage-hello" / "SKILL.md")
        manifest = Manifest(
            schema_version=1,
            installed_hosts=["claude"],
            installed_packs=["garage"],
            installed_at="2026-04-19T12:00:00",
            files=[_make_entry(dst=dst_native)],
        )
        write_manifest(garage_dir, manifest)
        raw = json.loads((garage_dir / "config" / MANIFEST_FILENAME).read_text())
        assert "\\" not in raw["files"][0]["dst"]
        assert raw["files"][0]["dst"].count("/") >= 2


class TestErrorHandling:
    def test_read_invalid_json_raises(self, tmp_path: Path) -> None:
        garage_dir = tmp_path / ".garage"
        (garage_dir / "config").mkdir(parents=True)
        (garage_dir / "config" / MANIFEST_FILENAME).write_text(
            "{ broken json", encoding="utf-8"
        )
        with pytest.raises(ValueError):
            read_manifest(garage_dir)
