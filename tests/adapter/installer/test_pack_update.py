"""F012-B T2 tests: update_pack + version compare + atomic + rollback."""

from __future__ import annotations

import io
import json
import subprocess
from pathlib import Path

import pytest

from garage_os.adapter.installer.pack_install import (
    PackInstallError,
    install_pack_from_url,
    update_pack,
)
from garage_os.adapter.installer.pipeline import install_packs


def _build_pack(repo_dir: Path, pack_id: str, version: str = "0.1.0", extra_skill_dir: bool = False) -> str:
    if (repo_dir / ".git").exists():
        # Reset for incremental commit
        pass
    (repo_dir / "skills" / "hello").mkdir(parents=True, exist_ok=True)
    (repo_dir / "skills" / "hello" / "SKILL.md").write_text(
        f"---\nname: hello\ndescription: minimal v{version}\n---\n# Hello v{version}\n",
        encoding="utf-8",
    )
    skills_list = ["hello"]
    if extra_skill_dir:
        (repo_dir / "skills" / "world").mkdir(parents=True, exist_ok=True)
        (repo_dir / "skills" / "world" / "SKILL.md").write_text(
            "---\nname: world\ndescription: minimal\n---\n# World\n",
            encoding="utf-8",
        )
        skills_list.append("world")
    (repo_dir / "pack.json").write_text(
        json.dumps({
            "schema_version": 1, "pack_id": pack_id, "version": version,
            "description": f"v{version}", "skills": skills_list, "agents": [],
        }, indent=2),
        encoding="utf-8",
    )
    if not (repo_dir / ".git").exists():
        subprocess.run(["git", "init", "-q"], cwd=repo_dir, check=True)
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=T", "commit", "-q",
         "--allow-empty", "-m", f"v{version}"],
        cwd=repo_dir, check=True,
    )
    return f"file://{repo_dir}"


class TestUpdateAlreadyUpToDate:
    def test_same_version_no_op(self, tmp_path: Path, capsys) -> None:
        workspace = tmp_path / "ws"
        workspace.mkdir()
        repo = tmp_path / "src"
        repo.mkdir()
        url = _build_pack(repo, "ut-test", "0.1.0")
        install_pack_from_url(workspace, url)

        summary = update_pack(workspace, "ut-test", yes=True)
        assert summary.skipped is True
        assert summary.old_version == "0.1.0"
        assert summary.new_version == "0.1.0"
        captured = capsys.readouterr()
        assert "already up to date" in captured.out.lower()


class TestUpdateVersionBump:
    def test_update_yes_replaces_pack_and_syncs_host(self, tmp_path: Path) -> None:
        workspace = tmp_path / "ws"
        workspace.mkdir()
        repo = tmp_path / "src"
        repo.mkdir()
        url = _build_pack(repo, "vb-test", "0.1.0")
        install_pack_from_url(workspace, url)
        # init host dirs (claude only for fast)
        install_packs(workspace, packs_root=workspace / "packs", hosts=["claude"])
        # Verify v0.1.0 SKILL.md content
        host_skill = workspace / ".claude" / "skills" / "hello" / "SKILL.md"
        assert "v0.1.0" in host_skill.read_text()

        # Bump remote to v0.2.0 (with extra skill)
        _build_pack(repo, "vb-test", "0.2.0", extra_skill_dir=True)

        summary = update_pack(workspace, "vb-test", yes=True)
        assert summary.skipped is False
        assert summary.old_version == "0.1.0"
        assert summary.new_version == "0.2.0"

        # Local pack.json updated
        new_local = json.loads((workspace / "packs" / "vb-test" / "pack.json").read_text())
        assert new_local["version"] == "0.2.0"
        assert "world" in new_local["skills"]
        # source_url preserved
        assert new_local["source_url"] == url
        # Host SKILL.md re-installed (force=True path)
        new_host = host_skill.read_text()
        assert "v0.2.0" in new_host
        # New skill 'world' also installed (host dirs synced)
        assert (workspace / ".claude" / "skills" / "world" / "SKILL.md").exists()


class TestUpdateNoSourceUrl:
    def test_pack_without_source_url_raises(self, tmp_path: Path) -> None:
        workspace = tmp_path / "ws"
        workspace.mkdir()
        # Manually create a pack without source_url (simulate local-only pack)
        pack_dir = workspace / "packs" / "local-only"
        pack_dir.mkdir(parents=True)
        (pack_dir / "skills" / "x").mkdir(parents=True)
        (pack_dir / "skills" / "x" / "SKILL.md").write_text(
            "---\nname: x\ndescription: x\n---\n# X\n", encoding="utf-8",
        )
        (pack_dir / "pack.json").write_text(json.dumps({
            "schema_version": 1, "pack_id": "local-only", "version": "0.1.0",
            "description": "x", "skills": ["x"], "agents": [],
        }), encoding="utf-8")

        with pytest.raises(PackInstallError) as exc_info:
            update_pack(workspace, "local-only", yes=True)
        assert "no source_url" in str(exc_info.value)


class TestUpdateNonexistent:
    def test_nonexistent_raises(self, tmp_path: Path) -> None:
        with pytest.raises(PackInstallError) as exc_info:
            update_pack(tmp_path, "nonexistent", yes=True)
        assert "not installed" in str(exc_info.value).lower()


class TestUpdateInteractiveCancel:
    """FR-1204 BDD interactive cancel scenario (Mi-1 fix in spec r2)."""

    def test_non_tty_without_yes_returns_skipped(self, tmp_path: Path, capsys) -> None:
        workspace = tmp_path / "ws"
        workspace.mkdir()
        repo = tmp_path / "src"
        repo.mkdir()
        url = _build_pack(repo, "cancel-test", "0.1.0")
        install_pack_from_url(workspace, url)
        # Bump remote
        _build_pack(repo, "cancel-test", "0.2.0")

        # Pre-update bytes
        before_bytes = (workspace / "packs" / "cancel-test" / "pack.json").read_bytes()

        # Non-TTY without --yes
        fake_stdin = io.StringIO("")
        fake_stdin.isatty = lambda: False  # type: ignore[method-assign]
        summary = update_pack(workspace, "cancel-test", stdin=fake_stdin)
        assert summary.skipped is True

        # Pack bytes unchanged
        after_bytes = (workspace / "packs" / "cancel-test" / "pack.json").read_bytes()
        assert before_bytes == after_bytes


class TestUpdatePreserveLocalEditsWarn:
    """FR-1206 — --preserve-local-edits issues warning, still overwrites."""

    def test_warn_still_overwrites(self, tmp_path: Path, capsys) -> None:
        workspace = tmp_path / "ws"
        workspace.mkdir()
        repo = tmp_path / "src"
        repo.mkdir()
        url = _build_pack(repo, "ple-test", "0.1.0")
        install_pack_from_url(workspace, url)
        # Bump remote
        _build_pack(repo, "ple-test", "0.2.0")

        stderr = io.StringIO()
        summary = update_pack(
            workspace, "ple-test",
            yes=True, preserve_local_edits=True, stderr=stderr,
        )
        assert summary.skipped is False
        assert summary.new_version == "0.2.0"
        assert "preserve-local-edits" in stderr.getvalue()
        assert "F013 D-1211" in stderr.getvalue()
