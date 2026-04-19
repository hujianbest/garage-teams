"""Install manifest persistence: ``.garage/config/host-installer.json``.

Implements F007 FR-705 + design D7 §8.3 / §11.2 / NFR-703 / CON-703.

The manifest is the **idempotency credential** for ``garage init`` re-runs:
each entry records (src, dst, host, pack_id, content_hash) so the pipeline
can decide whether a target file is "still Garage-owned" (hash matches),
"locally modified" (hash differs), or "newly added by user" (no entry).

Stability invariants for clean ``git diff``:

- ``installed_hosts`` and ``installed_packs`` are written ASCII-sorted
- ``files[]`` is written sorted by (src, dst)
- All path strings serialize as POSIX forward slashes regardless of OS
- ``schema_version`` field is reserved for VersionManager (CON-703); T5
  registers ``host-installer.json`` so future migrations can be planned.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Optional


MANIFEST_SCHEMA_VERSION = 1
MANIFEST_FILENAME = "host-installer.json"
CONFIG_SUBDIR = "config"


@dataclass
class ManifestFileEntry:
    """One file installed by Garage into a host directory.

    Fields:
        src: project-relative POSIX path to the source under ``packs/``
        dst: project-relative POSIX path to the installed file
        host: host id (e.g. ``"claude"``)
        pack_id: pack id this file came from
        content_hash: SHA-256 hex of the bytes actually written to ``dst``
                      (i.e. after marker injection, not the raw source)
    """

    src: str
    dst: str
    host: str
    pack_id: str
    content_hash: str


@dataclass
class Manifest:
    """Top-level structure persisted to ``.garage/config/host-installer.json``."""

    schema_version: int
    installed_hosts: list[str]
    installed_packs: list[str]
    installed_at: str  # ISO-8601
    files: list[ManifestFileEntry] = field(default_factory=list)


def write_manifest(garage_dir: Path, manifest: Manifest) -> Path:
    """Persist ``manifest`` to ``garage_dir/config/host-installer.json``.

    Returns the file path written. Sorts list-valued fields and converts
    paths to POSIX form for cross-platform stability (NFR-703).
    """
    config_dir = garage_dir / CONFIG_SUBDIR
    config_dir.mkdir(parents=True, exist_ok=True)
    target = config_dir / MANIFEST_FILENAME

    payload = _to_serializable(manifest)
    target.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return target


def read_manifest(garage_dir: Path) -> Optional[Manifest]:
    """Load manifest from ``garage_dir/config/host-installer.json``, or None.

    Returns None if the file does not exist (i.e. first-time install).
    Raises ValueError on JSON parse failure.
    """
    target = garage_dir / CONFIG_SUBDIR / MANIFEST_FILENAME
    if not target.is_file():
        return None
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Failed to parse {target}: {exc}"
        ) from exc
    return _from_dict(raw)


def _to_serializable(manifest: Manifest) -> dict[str, Any]:
    """Convert Manifest to JSON-serializable dict with stability invariants."""
    files_sorted = sorted(
        manifest.files, key=lambda e: (e.src, e.dst)
    )
    return {
        "schema_version": manifest.schema_version,
        "installed_hosts": sorted(manifest.installed_hosts),
        "installed_packs": sorted(manifest.installed_packs),
        "installed_at": manifest.installed_at,
        "files": [
            {
                "src": _to_posix(e.src),
                "dst": _to_posix(e.dst),
                "host": e.host,
                "pack_id": e.pack_id,
                "content_hash": e.content_hash,
            }
            for e in files_sorted
        ],
    }


def _from_dict(raw: dict[str, Any]) -> Manifest:
    return Manifest(
        schema_version=int(raw.get("schema_version", MANIFEST_SCHEMA_VERSION)),
        installed_hosts=sorted(raw.get("installed_hosts", [])),
        installed_packs=sorted(raw.get("installed_packs", [])),
        installed_at=str(raw.get("installed_at", "")),
        files=sorted(
            [
                ManifestFileEntry(
                    src=str(f["src"]),
                    dst=str(f["dst"]),
                    host=str(f["host"]),
                    pack_id=str(f["pack_id"]),
                    content_hash=str(f["content_hash"]),
                )
                for f in raw.get("files", [])
            ],
            key=lambda e: (e.src, e.dst),
        ),
    )


def _to_posix(path_str: str) -> str:
    """Convert any OS-native path string to POSIX form (forward slashes)."""
    # PurePosixPath cannot accept '\' on its own, so normalize first.
    return PurePosixPath(*Path(path_str).parts).as_posix()
