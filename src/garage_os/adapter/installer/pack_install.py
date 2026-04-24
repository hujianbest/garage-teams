"""F011 T4: `garage pack install <git-url>` + `garage pack ls` implementation.

Implements F011 spec FR-1106..1108 + design ADR-D11-4..7.

ADR-D11-4: Use ``subprocess.run(["git", "clone", "--depth=1", ...])`` rather than
GitPython / dulwich (CON-1104 zero-dep).

ADR-D11-5: pack.json schema_version unchanged; ``source_url`` is optional field
appended on install. F007 既有 packs (without source_url) remain valid.

ADR-D11-6: install lands at ``<workspace>/packs/<pack-id>/`` (filesystem
layout); user runs ``garage init --hosts ...`` separately to install into
host directories (no double-install, decoupled from F007 pipeline).

ADR-D11-7: ``garage pack ls`` output marker family with F007: ``Installed packs (N total):``
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import IO

from garage_os.adapter.installer.pack_discovery import (
    InvalidPackError,
    discover_packs,
)


class PackInstallError(Exception):
    """Raised when `garage pack install` fails (git clone / discover / write)."""


@dataclass
class PackInstallSummary:
    pack_id: str
    version: str
    source_url: str
    installed_path: Path


def install_pack_from_url(
    workspace_root: Path,
    git_url: str,
    *,
    stderr: IO[str] | None = None,
) -> PackInstallSummary:
    """Install a pack from a git URL (or file:// URL for testing).

    Steps:
    1. Shallow git clone --depth=1 to a temp dir
    2. Discover pack metadata in the cloned dir (verify pack.json)
    3. Copy pack contents to ``<workspace>/packs/<pack-id>/``
    4. Append ``source_url`` field to the installed pack.json

    Args:
        workspace_root: project root containing packs/
        git_url: git URL (https / ssh / file:// supported via standard git)
        stderr: stream for warnings

    Returns:
        PackInstallSummary

    Raises:
        PackInstallError: on git clone / discover / write failure
    """
    err = stderr if stderr is not None else sys.stderr

    # Step 1: shallow clone to temp
    with tempfile.TemporaryDirectory(prefix="garage-pack-clone-") as tmpdir:
        clone_dst = Path(tmpdir) / "clone"
        try:
            subprocess.run(
                ["git", "clone", "--depth=1", git_url, str(clone_dst)],
                check=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:
            raise PackInstallError(
                f"git command not found in PATH (ASM-1101 requires git): {exc}"
            ) from exc
        except subprocess.CalledProcessError as exc:
            raise PackInstallError(
                f"git clone failed for {git_url}: {exc.stderr.strip()}"
            ) from exc

        # Step 2: discover (treat clone_dst as a single pack root)
        pack_json_path = clone_dst / "pack.json"
        if not pack_json_path.is_file():
            raise PackInstallError(
                f"No pack.json found at root of {git_url}; expected single-pack repo (CON-D11-1)"
            )
        try:
            # Use _load_pack indirectly via discover_packs on parent
            # Easier: inline the validation
            raw = json.loads(pack_json_path.read_text(encoding="utf-8"))
            pack_id = raw.get("pack_id")
            version = raw.get("version", "0.0.0")
            if not pack_id or not isinstance(pack_id, str):
                raise PackInstallError(
                    f"pack.json missing or invalid 'pack_id': {git_url}"
                )
        except (json.JSONDecodeError, OSError) as exc:
            raise PackInstallError(
                f"Failed to parse pack.json from {git_url}: {exc}"
            ) from exc

        # Step 3: copy to workspace_root/packs/<pack-id>/
        packs_dir = workspace_root / "packs"
        packs_dir.mkdir(parents=True, exist_ok=True)
        installed_path = packs_dir / pack_id
        if installed_path.exists():
            raise PackInstallError(
                f"Pack '{pack_id}' already installed at {installed_path}; "
                "remove first or use 'garage pack update' (D-1011 candidate)"
            )

        # shutil.copytree, but skip .git/ to keep things clean
        def _ignore_git(_src: str, names: list[str]) -> list[str]:
            return [n for n in names if n == ".git"]

        shutil.copytree(clone_dst, installed_path, ignore=_ignore_git)

        # Step 4: append source_url to installed pack.json (FR-1108 backward compat)
        installed_pack_json = installed_path / "pack.json"
        installed_raw = json.loads(installed_pack_json.read_text(encoding="utf-8"))
        installed_raw["source_url"] = git_url
        installed_pack_json.write_text(
            json.dumps(installed_raw, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        # Verify with discover_packs that it's a valid pack
        try:
            discover_packs(packs_dir)
        except InvalidPackError as exc:
            # Roll back the install
            shutil.rmtree(installed_path)
            raise PackInstallError(
                f"Installed pack failed validation, rolled back: {exc}"
            ) from exc

        return PackInstallSummary(
            pack_id=pack_id,
            version=str(version),
            source_url=git_url,
            installed_path=installed_path,
        )


def list_installed_packs(workspace_root: Path) -> list[dict[str, str]]:
    """Return list of installed packs with id / version / source_url (or 'local').

    Used by ``garage pack ls`` (FR-1107).
    """
    packs_dir = workspace_root / "packs"
    if not packs_dir.is_dir():
        return []

    packs = discover_packs(packs_dir)
    out: list[dict[str, str]] = []
    for p in packs:
        # Read pack.json to get source_url (Pack dataclass doesn't expose it)
        pj = packs_dir / p.pack_id / "pack.json"
        try:
            raw = json.loads(pj.read_text(encoding="utf-8"))
            source = raw.get("source_url", "local")
        except (OSError, json.JSONDecodeError):
            source = "local"
        out.append(
            {
                "pack_id": p.pack_id,
                "version": p.version,
                "source_url": source,
            }
        )
    return sorted(out, key=lambda d: d["pack_id"])
