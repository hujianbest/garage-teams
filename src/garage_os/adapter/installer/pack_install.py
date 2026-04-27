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

import contextlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import IO

from garage_os.adapter.installer.pack_discovery import (
    InvalidPackError,
    discover_packs,
)


@contextlib.contextmanager
def _clone_pack_to_tempdir(git_url: str) -> Iterator[Path]:
    """F012-B helper (ADR-D12-3 r2): shallow-clone a pack URL to temp dir, yield clone path,
    auto-cleanup on exit (avoids dangling-Path bug from r1 design F-2)."""
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
        yield clone_dst


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

    # Step 1: shallow clone to temp (T2 refactor: use _clone_pack_to_tempdir helper)
    with _clone_pack_to_tempdir(git_url) as clone_dst:
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


# ============================================================
# F012-B — update_pack (T2)
# ============================================================


@dataclass
class UpdateSummary:
    """F012-B FR-1204: returned by update_pack."""

    pack_id: str
    old_version: str
    new_version: str
    skipped: bool = False  # True when already-up-to-date or interactive cancel
    rolled_back: bool = False  # True on failure (rollback to old)


def update_pack(
    workspace_root: Path,
    pack_id: str,
    *,
    yes: bool = False,
    preserve_local_edits: bool = False,
    stderr: IO[str] | None = None,
    stdin: IO[str] | None = None,
    stdout: IO[str] | None = None,
) -> UpdateSummary:
    """F012-B FR-1204..1206: re-clone from source_url + replace + sync host dirs.

    Steps (ADR-D12-3 r2):
    1. Read packs/<pack-id>/pack.json source_url
    2. Shallow clone to temp via _clone_pack_to_tempdir
    3. Compare versions; same → no-op; different → prompt or yes
    4. Atomic replace packs/<pack-id>/ (tempdir backup + swap)
    5. Re-run install_packs(force=True) to sync host dirs (ADR-D12-3 r2 F-5)
    6. On failure: roll back from backup
    """
    from garage_os.adapter.installer.manifest import read_manifest
    from garage_os.adapter.installer.pipeline import install_packs

    err = stderr if stderr is not None else sys.stderr
    src_in = stdin if stdin is not None else sys.stdin
    out = stdout if stdout is not None else sys.stdout

    pack_dir = workspace_root / "packs" / pack_id
    if not pack_dir.exists():
        raise PackInstallError(f"Pack '{pack_id}' not installed at {pack_dir}")

    # Step 1: read local pack.json
    local_pack_json_path = pack_dir / "pack.json"
    try:
        local_raw = json.loads(local_pack_json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PackInstallError(f"Failed to read local pack.json: {exc}") from exc

    source_url = local_raw.get("source_url")
    old_version = str(local_raw.get("version", "0.0.0"))
    if not source_url:
        raise PackInstallError(
            f"Pack '{pack_id}' has no source_url; was it installed via 'pack install'? "
            "Local-only packs cannot be updated (use git pull / manual cp)."
        )

    # Step 2 + 3: clone + version compare
    with _clone_pack_to_tempdir(source_url) as clone_dst:
        new_pack_json_path = clone_dst / "pack.json"
        if not new_pack_json_path.is_file():
            raise PackInstallError(
                f"Remote {source_url} no longer has pack.json"
            )
        try:
            new_raw = json.loads(new_pack_json_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PackInstallError(
                f"Failed to parse remote pack.json: {exc}"
            ) from exc

        new_version = str(new_raw.get("version", "0.0.0"))
        if new_version == old_version:
            print(f"Pack '{pack_id}' already up to date (v{old_version})", file=out)
            return UpdateSummary(
                pack_id=pack_id,
                old_version=old_version,
                new_version=new_version,
                skipped=True,
            )

        # Step 3.5: --preserve-local-edits warn (FR-1206)
        if preserve_local_edits:
            print(
                "WARNING: --preserve-local-edits set; true 3-way merge deferred to "
                "F013 D-1211. Proceeding with overwrite (your local edits will be lost).",
                file=err,
            )

        # Step 3 prompt (FR-1204 BDD interactive cancel)
        if not yes:
            is_tty = getattr(src_in, "isatty", lambda: False)()
            if not is_tty:
                print(
                    f"non-interactive shell detected; pass --yes to confirm update "
                    f"v{old_version} → v{new_version}",
                    file=err,
                )
                return UpdateSummary(
                    pack_id=pack_id,
                    old_version=old_version,
                    new_version=new_version,
                    skipped=True,
                )
            print(
                f"Update '{pack_id}': v{old_version} → v{new_version}. "
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
                return UpdateSummary(
                    pack_id=pack_id,
                    old_version=old_version,
                    new_version=new_version,
                    skipped=True,
                )

        # Step 4: atomic replace (backup + swap)
        backup_root = Path(tempfile.mkdtemp(prefix=f"garage-update-backup-{pack_id}-"))
        backup_pack = backup_root / pack_id
        shutil.copytree(pack_dir, backup_pack)

        try:
            # Remove old pack dir
            shutil.rmtree(pack_dir)
            # Copy new contents (clone_dst has fresh content; preserve source_url)
            def _ignore_git(_src: str, names: list[str]) -> list[str]:
                return [n for n in names if n == ".git"]
            shutil.copytree(clone_dst, pack_dir, ignore=_ignore_git)
            # Re-write source_url (preserved from local, in case remote pack.json doesn't have it)
            new_installed_raw = json.loads((pack_dir / "pack.json").read_text(encoding="utf-8"))
            new_installed_raw["source_url"] = source_url
            (pack_dir / "pack.json").write_text(
                json.dumps(new_installed_raw, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            # Step 5: re-run install_packs(force=True) to sync host dirs
            prior = read_manifest(workspace_root / ".garage")
            if prior is not None and prior.installed_hosts:
                install_packs(
                    workspace_root,
                    packs_root=workspace_root / "packs",
                    hosts=list(prior.installed_hosts),
                    force=True,
                )
        except Exception as exc:
            # Roll back from backup
            if pack_dir.exists():
                shutil.rmtree(pack_dir)
            shutil.copytree(backup_pack, pack_dir)
            raise PackInstallError(
                f"Update failed for {pack_id}, rolled back to v{old_version}: {exc}"
            ) from exc
        finally:
            if backup_root.exists():
                shutil.rmtree(backup_root)

    return UpdateSummary(
        pack_id=pack_id,
        old_version=old_version,
        new_version=new_version,
        skipped=False,
    )


# ============================================================
# F012-C — publish_pack + sensitive_scan (T3)
# ============================================================

# F012 ADR-D12-4 r2 SENSITIVE_RULES: 5 categories scanned at publish time.
# Patterns allow optional surrounding quotes (handles JSON / YAML / .env styles).
SENSITIVE_RULES = [
    ("password", re.compile(r'["\']?password["\']?\s*[:=]\s*\S+', re.IGNORECASE)),
    ("api_key", re.compile(r'["\']?api[_-]?key["\']?\s*[:=]\s*\S+', re.IGNORECASE)),
    ("secret", re.compile(r'["\']?secret["\']?\s*[:=]\s*\S+', re.IGNORECASE)),
    ("token", re.compile(r'["\']?token["\']?\s*[:=]\s*\S+', re.IGNORECASE)),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----")),
]

# F012 ADR-D12-4 r2 + spec FR-1208 I-3 fix: extension allowlist for text-only scan.
TEXT_EXTENSIONS = frozenset({
    ".md", ".py", ".txt", ".json", ".yaml", ".yml", ".toml",
    ".sh", ".js", ".ts", ".ini", ".cfg", ".conf", ".env",
    ".lock", ".gitignore",
})


@dataclass
class SensitiveMatch:
    """F012-C FR-1208: one sensitive pattern hit during pack publish scan."""
    file: str  # relative to pack_dir
    line: int  # 1-indexed
    rule: str
    excerpt: str  # the matched text


@dataclass
class PublishSummary:
    """F012-C FR-1207: returned by publish_pack."""
    pack_id: str
    version: str
    to_url: str
    pushed: bool = False  # False on dry-run / cancel / sensitive-abort
    skipped: bool = False  # True on cancel
    sensitive_matches: list[SensitiveMatch] | None = None
    binary_skipped_count: int = 0


def sensitive_scan(pack_dir: Path) -> tuple[list[SensitiveMatch], int]:
    """F012-C FR-1208: scan text files in pack_dir for sensitive content.

    Returns (matches, n_binary_skipped). Only files with extensions in
    TEXT_EXTENSIONS are scanned; others count toward n_binary_skipped (per ADR-D12-4 I-3 fix).
    """
    matches: list[SensitiveMatch] = []
    binary_skipped = 0
    for path in sorted(pack_dir.rglob("*")):
        if not path.is_file():
            continue
        if ".git" in path.parts:
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            binary_skipped += 1
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeDecodeError):
            binary_skipped += 1
            continue
        rel = str(path.relative_to(pack_dir))
        for line_num, line in enumerate(text.splitlines(), start=1):
            for rule_name, pattern in SENSITIVE_RULES:
                m = pattern.search(line)
                if m:
                    matches.append(SensitiveMatch(
                        file=rel, line=line_num, rule=rule_name,
                        excerpt=line.strip()[:80],
                    ))
    return matches, binary_skipped


def _resolve_commit_author(commit_author: str | None) -> tuple[str, str]:
    """F012-C ADR-D12-4 step 3 + Mi-4: resolve git commit author.

    Priority: --commit-author "Name <email>" > git config user.name/email > fallback.
    Returns (name, email). Fallback "Garage <garage-publish@local>" matches spec FR-1207 step 5.
    """
    if commit_author:
        # Parse "Name <email>" format
        m = re.match(r"^(.+?)\s*<(.+?)>$", commit_author.strip())
        if m:
            return (m.group(1).strip(), m.group(2).strip())
        # Fallback: treat as name only
        return (commit_author.strip(), "garage-publish@local")
    # Try git config
    try:
        name = subprocess.run(
            ["git", "config", "user.name"], capture_output=True, text=True, check=True,
        ).stdout.strip()
        email = subprocess.run(
            ["git", "config", "user.email"], capture_output=True, text=True, check=True,
        ).stdout.strip()
        if name and email:
            return (name, email)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    # F-8 fix: rendered as "Garage <garage-publish@local>" matches spec FR-1207 step 5
    return ("Garage", "garage-publish@local")


def publish_pack(
    workspace_root: Path,
    pack_id: str,
    to_url: str,
    *,
    yes: bool = False,
    force: bool = False,
    dry_run: bool = False,
    no_update_source_url: bool = False,
    commit_author: str | None = None,
    commit_message: str | None = None,
    stderr: IO[str] | None = None,
    stdin: IO[str] | None = None,
    stdout: IO[str] | None = None,
) -> PublishSummary:
    """F012-C FR-1207..1210: publish a pack to a git URL.

    Phase A: sensitive_scan (matches + force gate)
    Phase B: git ls-remote check (force-push risk awareness)
    Phase C: prompt (skipped under --yes / --dry-run)
    Phase D: actual publish (or dry-run no-push)
    Phase E: writeback source_url (skipped under --no-update-source-url / --dry-run)

    Flag matrix per FR-1207 r2 + ADR-D12-4 r2.
    """
    err = stderr if stderr is not None else sys.stderr
    src_in = stdin if stdin is not None else sys.stdin
    out = stdout if stdout is not None else sys.stdout

    pack_dir = workspace_root / "packs" / pack_id
    if not pack_dir.exists():
        raise PackInstallError(f"Pack '{pack_id}' not installed at {pack_dir}")

    # Read pack version
    try:
        local_raw = json.loads((pack_dir / "pack.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PackInstallError(f"Failed to read local pack.json: {exc}") from exc
    version = str(local_raw.get("version", "0.0.0"))

    # Phase A: sensitive scan
    matches, binary_skipped = sensitive_scan(pack_dir)
    if matches and not force:
        # Default / --yes: --yes does NOT bypass sensitive (per FR-1207 r2 状态表)
        print(
            f"Sensitive content detected in pack '{pack_id}':", file=err,
        )
        for m in matches:
            print(f"  {m.file}:{m.line} ({m.rule}): {m.excerpt}", file=err)
        print(
            f"({binary_skipped} binary/non-text files skipped). "
            "Use --force to override at your own risk (B5 user-pact).",
            file=err,
        )
        return PublishSummary(
            pack_id=pack_id, version=version, to_url=to_url,
            pushed=False, skipped=True,
            sensitive_matches=matches, binary_skipped_count=binary_skipped,
        )

    # Phase B: remote check (FR-1207 step 3 + I-2 fix)
    remote_has_refs = False
    try:
        result = subprocess.run(
            ["git", "ls-remote", to_url],
            capture_output=True, text=True, timeout=30,
        )
        remote_has_refs = bool(result.stdout.strip())
    except (subprocess.SubprocessError, FileNotFoundError):
        # Best-effort; if ls-remote fails, fall through to prompt
        pass

    # Phase C: prompt (skipped on --yes or --dry-run; FR-1209 dry-run implies yes)
    effective_yes = yes or dry_run
    if not effective_yes:
        is_tty = getattr(src_in, "isatty", lambda: False)()
        if not is_tty:
            print(
                "non-interactive shell detected; pass --yes to confirm publish",
                file=err,
            )
            return PublishSummary(
                pack_id=pack_id, version=version, to_url=to_url,
                pushed=False, skipped=True,
                sensitive_matches=matches, binary_skipped_count=binary_skipped,
            )
        # Prompt content per FR-1207 step 4
        print(
            f"Will publish '{pack_id}' v{version} to {to_url}:\n"
            f"  - Force push to remote (will OVERWRITE existing content if any)\n"
            f"  - {'Update' if not no_update_source_url else 'Keep'} packs/{pack_id}/pack.json source_url\n"
            f"  - Sensitive scan: {'PASSED' if not matches else 'SKIPPED via --force'}\n"
            + (f"WARNING: remote has existing refs:\n{result.stdout}\n" if remote_has_refs else "")
            + "Continue? [y/N]: ",
            end="", file=out, flush=True,
        )
        try:
            answer = input("").strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = ""
        if answer not in ("y", "yes"):
            print("Cancelled.", file=out)
            return PublishSummary(
                pack_id=pack_id, version=version, to_url=to_url,
                pushed=False, skipped=True,
                sensitive_matches=matches, binary_skipped_count=binary_skipped,
            )

    # Phase D: actual publish
    author_name, author_email = _resolve_commit_author(commit_author)
    msg = commit_message or f"Publish {pack_id} v{version} from Garage"

    with tempfile.TemporaryDirectory(prefix=f"garage-publish-{pack_id}-") as tmpdir:
        tmp_repo = Path(tmpdir) / "repo"
        # Copy pack to tmp_repo (skip .git/)
        def _ignore_git(_src: str, names: list[str]) -> list[str]:
            return [n for n in names if n == ".git"]
        shutil.copytree(pack_dir, tmp_repo, ignore=_ignore_git)

        # git init -b main (F-6 fix); fallback for older git
        try:
            subprocess.run(
                ["git", "init", "-b", "main", "-q"],
                cwd=tmp_repo, check=True, capture_output=True, text=True,
            )
        except subprocess.CalledProcessError:
            # Older git (< 2.28): init then symbolic-ref
            subprocess.run(["git", "init", "-q"], cwd=tmp_repo, check=True)
            subprocess.run(
                ["git", "symbolic-ref", "HEAD", "refs/heads/main"],
                cwd=tmp_repo, check=True,
            )

        subprocess.run(["git", "add", "."], cwd=tmp_repo, check=True)
        subprocess.run(
            ["git", "-c", f"user.name={author_name}", "-c", f"user.email={author_email}",
             "commit", "-q", "-m", msg],
            cwd=tmp_repo, check=True,
        )

        if dry_run:
            print(
                f"DRY RUN: would push '{pack_id}' v{version} to {to_url} "
                f"(commit by {author_name} <{author_email}>; "
                f"{len(matches)} sensitive {'matches' if matches else 'free'}, "
                f"{binary_skipped} binary skipped)",
                file=out,
            )
            return PublishSummary(
                pack_id=pack_id, version=version, to_url=to_url,
                pushed=False, skipped=False,
                sensitive_matches=matches, binary_skipped_count=binary_skipped,
            )

        # Real push
        subprocess.run(
            ["git", "remote", "add", "origin", to_url],
            cwd=tmp_repo, check=True,
        )
        try:
            subprocess.run(
                ["git", "push", "--force", "origin", "main"],
                cwd=tmp_repo, check=True, capture_output=True, text=True,
            )
            # Update remote HEAD to main (for bare remotes initialized with master default,
            # so subsequent `git clone` checks out main automatically)
            subprocess.run(
                ["git", "push", "--force", "origin", "HEAD:main"],
                cwd=tmp_repo, capture_output=True, text=True,
            )
            # Try to set remote HEAD symbolic ref via direct git (works on local file:// bare)
            if to_url.startswith("file://"):
                bare_path = to_url[len("file://"):]
                try:
                    subprocess.run(
                        ["git", "symbolic-ref", "HEAD", "refs/heads/main"],
                        cwd=bare_path, check=True, capture_output=True, text=True,
                    )
                except (subprocess.CalledProcessError, FileNotFoundError):
                    pass  # best-effort; clone with --branch main still works
        except subprocess.CalledProcessError as exc:
            raise PackInstallError(
                f"git push failed for {to_url}: {exc.stderr.strip()}"
            ) from exc

    # Phase E: writeback source_url
    if not no_update_source_url:
        local_raw["source_url"] = to_url
        (pack_dir / "pack.json").write_text(
            json.dumps(local_raw, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    return PublishSummary(
        pack_id=pack_id, version=version, to_url=to_url,
        pushed=True, skipped=False,
        sensitive_matches=matches, binary_skipped_count=binary_skipped,
    )
