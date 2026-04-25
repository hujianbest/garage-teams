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


# ============================================================
# F012-A — uninstall_pack (T1)
# ============================================================


@dataclass
class UninstallSummary:
    """F012-A FR-1201: returned by uninstall_pack."""

    pack_id: str
    n_files_removed: int
    n_hosts_affected: int
    removed_paths: list[str]
    skipped: bool = False  # True when --dry-run or interactive cancel


def uninstall_pack(
    workspace_root: Path,
    pack_id: str,
    *,
    dry_run: bool = False,
    yes: bool = False,
    stderr: IO[str] | None = None,
    stdin: IO[str] | None = None,
    stdout: IO[str] | None = None,
) -> UninstallSummary:
    """F012-A FR-1201..1203: reverse of install_pack_from_url + garage init.

    Three-step transaction (ADR-D12-2 r2):
      1. Plan phase (read-only): list files to remove from host-installer.json files[]
      2. Confirm phase: print plan + interactive prompt (unless --yes / --dry-run)
      3. Execute phase: delete files + sidecars + empty parent dirs + packs/<id>/ + manifest update

    Touch boundary (CON-1205 + HYP-1206 + INV-F12-9): only touches packs/<id>/,
    .garage/config/host-installer.json, and host directory mapped files. Never reads
    or writes sync-manifest.json, knowledge/, experience/, sessions/, contracts/,
    platform.json, or host-adapter.json.
    """
    import sys
    from garage_os.adapter.installer.manifest import (
        Manifest,
        ManifestFileEntry,
        read_manifest,
        write_manifest,
    )

    err = stderr if stderr is not None else sys.stderr
    src_in = stdin if stdin is not None else sys.stdin
    out = stdout if stdout is not None else sys.stdout

    packs_dir = workspace_root / "packs"
    pack_dir = packs_dir / pack_id
    if not pack_dir.exists():
        raise PackInstallError(f"Pack '{pack_id}' not installed at {pack_dir}")

    # Phase 1: plan
    garage_dir = workspace_root / ".garage"
    manifest = read_manifest(garage_dir)
    pack_entries: list[ManifestFileEntry] = []
    if manifest is not None:
        pack_entries = [e for e in manifest.files if e.pack_id == pack_id]

    files_to_remove: list[Path] = [pack_dir]
    sidecar_dirs_to_remove: list[Path] = []
    skill_dirs_to_remove: set[Path] = set()
    hosts_affected: set[str] = set()

    for entry in pack_entries:
        dst_path = Path(entry.dst)
        files_to_remove.append(dst_path)
        hosts_affected.add(entry.host)
        # If SKILL.md, also remove skill dir + sidecars (references/ assets/ evals/ scripts/)
        # F010 PR #30 _sync_skill_sidecars copies these; uninstall reverses
        if dst_path.name == "SKILL.md":
            skill_dir = dst_path.parent
            for sidecar_name in ("references", "assets", "evals", "scripts"):
                sidecar_dir = skill_dir / sidecar_name
                if sidecar_dir.is_dir():
                    sidecar_dirs_to_remove.append(sidecar_dir)
            skill_dirs_to_remove.add(skill_dir)

    plan_paths = (
        [str(p) for p in files_to_remove]
        + [str(d) for d in sidecar_dirs_to_remove]
        + [str(d) for d in sorted(skill_dirs_to_remove)]
    )
    n_files = len(files_to_remove)
    n_hosts = len(hosts_affected)

    # Phase 2: confirm
    if dry_run:
        print(f"DRY RUN: would remove {n_files} files from {n_hosts} hosts:", file=out)
        for path in plan_paths:
            print(f"  would remove {path}", file=out)
        return UninstallSummary(
            pack_id=pack_id,
            n_files_removed=0,
            n_hosts_affected=n_hosts,
            removed_paths=plan_paths,
            skipped=True,
        )

    if not yes:
        # Interactive prompt (B5 user-pact)
        is_tty = getattr(src_in, "isatty", lambda: False)()
        if not is_tty:
            print(
                "non-interactive shell detected; pass --yes to confirm uninstall",
                file=err,
            )
            return UninstallSummary(
                pack_id=pack_id,
                n_files_removed=0,
                n_hosts_affected=n_hosts,
                removed_paths=[],
                skipped=True,
            )
        print(
            f"Will remove pack '{pack_id}': {n_files} files from {n_hosts} hosts. "
            "Continue? [y/N]: ",
            end="",
            file=out,
            flush=True,
        )
        try:
            answer = input("").strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = ""
        if answer not in ("y", "yes"):
            print("Cancelled.", file=out)
            return UninstallSummary(
                pack_id=pack_id,
                n_files_removed=0,
                n_hosts_affected=n_hosts,
                removed_paths=[],
                skipped=True,
            )

    # Phase 3: execute (atomic — back up packs/<id>/ to temp, restore on failure)
    backup_root: Path | None = None
    if pack_dir.exists():
        backup_root = Path(tempfile.mkdtemp(prefix=f"garage-uninstall-backup-{pack_id}-"))
        backup_pack = backup_root / pack_id
        shutil.copytree(pack_dir, backup_pack)

    removed: list[str] = []
    try:
        # 1. Delete sidecar dirs
        for sidecar in sidecar_dirs_to_remove:
            if sidecar.exists():
                shutil.rmtree(sidecar)
                removed.append(str(sidecar))
        # 2. Delete dst files
        for dst in files_to_remove:
            if dst == pack_dir:
                continue  # delete pack_dir last
            if dst.is_file() or dst.is_symlink():
                dst.unlink()
                removed.append(str(dst))
        # 3. Remove empty skill dirs
        for skill_dir in sorted(skill_dirs_to_remove, reverse=True):
            if skill_dir.exists() and not any(skill_dir.iterdir()):
                skill_dir.rmdir()
                removed.append(str(skill_dir))
        # 4. Remove packs/<pack-id>/
        if pack_dir.exists():
            shutil.rmtree(pack_dir)
            removed.append(str(pack_dir))
        # 5. Update host-installer.json (drop entries for this pack)
        if manifest is not None and pack_entries:
            new_files = [e for e in manifest.files if e.pack_id != pack_id]
            new_packs = [p for p in manifest.installed_packs if p != pack_id]
            new_manifest = Manifest(
                schema_version=manifest.schema_version,
                installed_hosts=manifest.installed_hosts,
                installed_packs=new_packs,
                installed_at=manifest.installed_at,
                files=new_files,
            )
            write_manifest(garage_dir, new_manifest)
    except Exception as exc:
        # Restore backup if available
        if backup_root is not None:
            backup_pack = backup_root / pack_id
            if backup_pack.exists():
                if pack_dir.exists():
                    shutil.rmtree(pack_dir)
                shutil.copytree(backup_pack, pack_dir)
        raise PackInstallError(f"Uninstall failed for {pack_id}, rolled back: {exc}") from exc
    finally:
        if backup_root is not None and backup_root.exists():
            shutil.rmtree(backup_root)

    return UninstallSummary(
        pack_id=pack_id,
        n_files_removed=len(removed),
        n_hosts_affected=n_hosts,
        removed_paths=removed,
        skipped=False,
    )
