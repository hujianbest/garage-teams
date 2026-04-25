"""F012-A T1 tests: uninstall_pack + reverse install + sync-manifest touch boundary."""

from __future__ import annotations

import io
import json
import subprocess
from pathlib import Path

import pytest

from garage_os.adapter.installer.pack_install import (
    PackInstallError,
    install_pack_from_url,
    uninstall_pack,
)
from garage_os.adapter.installer.pipeline import install_packs


def _build_test_pack(repo_dir: Path, pack_id: str = "uninstall-test") -> str:
    """Build a minimal git pack repo + return file:// URL."""
    (repo_dir / "skills" / "hello").mkdir(parents=True)
    (repo_dir / "skills" / "hello" / "SKILL.md").write_text(
        "---\nname: hello\ndescription: minimal\n---\n# Hello\n",
        encoding="utf-8",
    )
    (repo_dir / "skills" / "hello" / "references").mkdir()
    (repo_dir / "skills" / "hello" / "references" / "guide.md").write_text(
        "# Reference guide\n", encoding="utf-8"
    )
    (repo_dir / "pack.json").write_text(
        json.dumps({
            "schema_version": 1,
            "pack_id": pack_id,
            "version": "0.1.0",
            "description": "F012 uninstall test",
            "skills": ["hello"],
            "agents": [],
        }, indent=2),
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q"], cwd=repo_dir, check=True)
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=T", "commit", "-q", "-m", "init"],
        cwd=repo_dir, check=True,
    )
    return f"file://{repo_dir}"


def _install_and_init(workspace: Path, repo_dir: Path, pack_id: str = "uninstall-test") -> None:
    """Helper: install pack from local repo + run install_packs to populate host dirs."""
    url = _build_test_pack(repo_dir, pack_id)
    install_pack_from_url(workspace, url)
    install_packs(
        workspace,
        packs_root=workspace / "packs",
        hosts=["claude"],
    )


class TestUninstallPackHappyPath:
    def test_uninstall_yes_clears_all(self, tmp_path: Path) -> None:
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        repo = tmp_path / "src"
        repo.mkdir()
        _install_and_init(workspace, repo, pack_id="happy-test")

        # Verify install state
        assert (workspace / "packs" / "happy-test").is_dir()
        assert (workspace / ".claude" / "skills" / "hello" / "SKILL.md").is_file()

        summary = uninstall_pack(workspace, "happy-test", yes=True)

        assert summary.skipped is False
        assert summary.n_hosts_affected == 1
        assert summary.n_files_removed > 0
        # Pack dir gone
        assert not (workspace / "packs" / "happy-test").exists()
        # Host SKILL.md gone
        assert not (workspace / ".claude" / "skills" / "hello" / "SKILL.md").exists()
        # Host skill dir gone (empty after sidecar + SKILL removed)
        assert not (workspace / ".claude" / "skills" / "hello").exists()
        # host-installer.json updated
        manifest_path = workspace / ".garage" / "config" / "host-installer.json"
        manifest = json.loads(manifest_path.read_text())
        assert "happy-test" not in manifest["installed_packs"]
        # Files no longer reference happy-test
        for f in manifest["files"]:
            assert f["pack_id"] != "happy-test"


class TestUninstallNonexistent:
    def test_nonexistent_raises(self, tmp_path: Path) -> None:
        with pytest.raises(PackInstallError) as exc_info:
            uninstall_pack(tmp_path, "nonexistent-pack", yes=True)
        assert "not installed" in str(exc_info.value).lower()


class TestUninstallDryRun:
    def test_dry_run_prints_plan_no_changes(self, tmp_path: Path, capsys) -> None:
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        repo = tmp_path / "src"
        repo.mkdir()
        _install_and_init(workspace, repo, pack_id="dry-run-test")

        before_files = sorted((workspace / "packs" / "dry-run-test").rglob("*"))

        summary = uninstall_pack(workspace, "dry-run-test", dry_run=True)

        assert summary.skipped is True
        assert summary.n_files_removed == 0
        captured = capsys.readouterr()
        assert "DRY RUN" in captured.out
        assert "would remove" in captured.out
        # Files unchanged
        after_files = sorted((workspace / "packs" / "dry-run-test").rglob("*"))
        assert before_files == after_files


class TestUninstallNonTTYWithoutYes:
    def test_non_tty_without_yes_returns_skipped(
        self, tmp_path: Path, capsys
    ) -> None:
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        repo = tmp_path / "src"
        repo.mkdir()
        _install_and_init(workspace, repo, pack_id="non-tty-test")

        # Non-TTY: stdin.isatty() returns False
        fake_stdin = io.StringIO("")
        fake_stdin.isatty = lambda: False  # type: ignore[method-assign]
        summary = uninstall_pack(
            workspace, "non-tty-test", stdin=fake_stdin
        )

        assert summary.skipped is True
        captured = capsys.readouterr()
        assert "non-interactive" in captured.err
        # Pack dir untouched
        assert (workspace / "packs" / "non-tty-test").exists()


class TestUninstallSidecarReversed:
    """F010 PR #30 _sync_skill_sidecars reverse: uninstall removes references/ etc."""

    def test_uninstall_removes_sidecar_references(self, tmp_path: Path) -> None:
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        repo = tmp_path / "src"
        repo.mkdir()
        _install_and_init(workspace, repo, pack_id="sidecar-test")

        # Verify references/ was synced by F010 sidecar copy
        sidecar = workspace / ".claude" / "skills" / "hello" / "references"
        assert sidecar.is_dir()
        assert (sidecar / "guide.md").is_file()

        uninstall_pack(workspace, "sidecar-test", yes=True)

        # Sidecar removed
        assert not sidecar.exists()


class TestUninstallTouchBoundary:
    """INV-F12-9 + CON-1205 + HYP-1206: uninstall does NOT touch sync-manifest.json."""

    def test_sync_manifest_unchanged(self, tmp_path: Path) -> None:
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        repo = tmp_path / "src"
        repo.mkdir()
        _install_and_init(workspace, repo, pack_id="boundary-test")

        # Plant a sentinel sync-manifest.json (F010 fixture-ish)
        sync_manifest_path = workspace / ".garage" / "config" / "sync-manifest.json"
        sync_manifest_path.parent.mkdir(parents=True, exist_ok=True)
        sentinel_content = json.dumps({
            "schema_version": 1,
            "synced_at": "2026-04-25T00:00:00Z",
            "sources": {
                "knowledge_count": 0,
                "experience_count": 0,
                "knowledge_kinds": [],
                "size_bytes": 0,
                "size_budget_bytes": 16384,
            },
            "targets": [],
        }, indent=2) + "\n"
        sync_manifest_path.write_text(sentinel_content, encoding="utf-8")
        before_content = sync_manifest_path.read_bytes()

        uninstall_pack(workspace, "boundary-test", yes=True)

        # Sync manifest byte-level unchanged (CON-1205)
        after_content = sync_manifest_path.read_bytes()
        assert before_content == after_content


class TestUninstallManifestInstalledPacksSync:
    """FR-1201: installed_packs[] also drops the uninstalled pack."""

    def test_installed_packs_dropped(self, tmp_path: Path) -> None:
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        repo = tmp_path / "src"
        repo.mkdir()
        _install_and_init(workspace, repo, pack_id="multi-pack-test")

        manifest_before = json.loads(
            (workspace / ".garage" / "config" / "host-installer.json").read_text()
        )
        assert "multi-pack-test" in manifest_before["installed_packs"]

        uninstall_pack(workspace, "multi-pack-test", yes=True)

        manifest_after = json.loads(
            (workspace / ".garage" / "config" / "host-installer.json").read_text()
        )
        assert "multi-pack-test" not in manifest_after["installed_packs"]
