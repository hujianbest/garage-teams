"""F012-C T3 tests: publish_pack + flag matrix + e2e file:// remote."""

from __future__ import annotations

import io
import json
import subprocess
from pathlib import Path

import pytest

from garage_os.adapter.installer.pack_install import (
    PackInstallError,
    publish_pack,
)


def _build_pack_in_workspace(workspace: Path, pack_id: str = "pub-test", version: str = "0.1.0",
                              with_sensitive: bool = False) -> None:
    """Create packs/<pack-id>/ directly in workspace (skip install path)."""
    pack_dir = workspace / "packs" / pack_id
    pack_dir.mkdir(parents=True)
    (pack_dir / "skills" / "h").mkdir(parents=True)
    (pack_dir / "skills" / "h" / "SKILL.md").write_text(
        f"---\nname: h\ndescription: v{version}\n---\n# v{version}\n", encoding="utf-8",
    )
    if with_sensitive:
        (pack_dir / "config.env").write_text("password=secret-shouldnotpublish\n", encoding="utf-8")
    (pack_dir / "pack.json").write_text(json.dumps({
        "schema_version": 1, "pack_id": pack_id, "version": version,
        "description": f"v{version}", "skills": ["h"], "agents": [],
    }), encoding="utf-8")


def _bare_remote(tmp_path: Path) -> str:
    """Create an empty bare git repo + return file:// URL."""
    bare = tmp_path / "remote-bare.git"
    subprocess.run(["git", "init", "--bare", "-q", str(bare)], check=True)
    return f"file://{bare}"


class TestPublishE2EFileRemote:
    """SM-1203 + HYP-1203: file:// bare git remote round-trip."""

    def test_publish_then_clone_back(self, tmp_path: Path) -> None:
        workspace = tmp_path / "ws"
        workspace.mkdir()
        _build_pack_in_workspace(workspace, "e2e-test")
        remote_url = _bare_remote(tmp_path)

        summary = publish_pack(workspace, "e2e-test", remote_url, yes=True)
        assert summary.pushed is True
        assert summary.skipped is False

        # Clone back into a fresh dir
        clone_dst = tmp_path / "clone-back"
        subprocess.run(
            ["git", "clone", "-q", "--branch", "main", remote_url, str(clone_dst)],
            check=True,
        )
        # Verify pack.json + skill content
        cloned_pack = json.loads((clone_dst / "pack.json").read_text())
        assert cloned_pack["pack_id"] == "e2e-test"
        assert (clone_dst / "skills" / "h" / "SKILL.md").is_file()

        # source_url written back to local pack.json
        local_pj = json.loads((workspace / "packs" / "e2e-test" / "pack.json").read_text())
        assert local_pj["source_url"] == remote_url


class TestPublishSensitiveAbort:
    """FR-1207 r2 flag matrix: default + --yes both abort on sensitive."""

    def test_default_sensitive_aborts(self, tmp_path: Path, capsys) -> None:
        workspace = tmp_path / "ws"
        workspace.mkdir()
        _build_pack_in_workspace(workspace, "sens-test", with_sensitive=True)
        remote_url = _bare_remote(tmp_path)

        # Default: no --yes, no --force; sensitive present → skipped + warning
        summary = publish_pack(workspace, "sens-test", remote_url, yes=True)
        assert summary.pushed is False
        assert summary.skipped is True
        assert summary.sensitive_matches is not None
        assert len(summary.sensitive_matches) > 0
        captured = capsys.readouterr()
        assert "Sensitive content detected" in captured.err

    def test_yes_does_not_bypass_sensitive(self, tmp_path: Path) -> None:
        """flag matrix: --yes does NOT bypass sensitive scan."""
        workspace = tmp_path / "ws"
        workspace.mkdir()
        _build_pack_in_workspace(workspace, "ynb-test", with_sensitive=True)
        remote_url = _bare_remote(tmp_path)

        summary = publish_pack(workspace, "ynb-test", remote_url, yes=True)
        # Should still skip due to sensitive (yes does not bypass)
        assert summary.pushed is False


class TestPublishForceBypassSensitive:
    """FR-1207 r2 flag matrix: --force bypasses sensitive scan."""

    def test_yes_force_pushes_with_sensitive(self, tmp_path: Path) -> None:
        workspace = tmp_path / "ws"
        workspace.mkdir()
        _build_pack_in_workspace(workspace, "yf-test", with_sensitive=True)
        remote_url = _bare_remote(tmp_path)

        summary = publish_pack(workspace, "yf-test", remote_url, yes=True, force=True)
        # --yes --force: completely unattended push even with sensitive
        assert summary.pushed is True


class TestPublishDryRun:
    """FR-1209: dry-run implies yes; sensitive scan still runs."""

    def test_dry_run_no_push_no_source_url_change(self, tmp_path: Path, capsys) -> None:
        workspace = tmp_path / "ws"
        workspace.mkdir()
        _build_pack_in_workspace(workspace, "dr-test")
        remote_url = _bare_remote(tmp_path)

        summary = publish_pack(workspace, "dr-test", remote_url, dry_run=True)
        assert summary.pushed is False
        assert summary.skipped is False
        captured = capsys.readouterr()
        assert "DRY RUN" in captured.out
        # source_url not written
        local_pj = json.loads((workspace / "packs" / "dr-test" / "pack.json").read_text())
        assert "source_url" not in local_pj


class TestPublishCustomCommitAuthor:
    """Mi-4 fix: --commit-author flag override."""

    def test_commit_author_override(self, tmp_path: Path) -> None:
        workspace = tmp_path / "ws"
        workspace.mkdir()
        _build_pack_in_workspace(workspace, "ca-test")
        remote_url = _bare_remote(tmp_path)

        summary = publish_pack(
            workspace, "ca-test", remote_url, yes=True,
            commit_author="Alice Doe <alice@example.com>",
        )
        assert summary.pushed is True

        # Inspect remote commit log
        log_dst = tmp_path / "log-clone"
        subprocess.run(
            ["git", "clone", "-q", "--branch", "main", remote_url, str(log_dst)],
            check=True,
        )
        log_out = subprocess.run(
            ["git", "log", "--pretty=%an <%ae>", "-1"],
            cwd=log_dst, capture_output=True, text=True, check=True,
        ).stdout.strip()
        assert "Alice Doe" in log_out
        assert "alice@example.com" in log_out


class TestPublishCustomCommitMessage:
    """Mi-4 fix: --commit-message flag override."""

    def test_commit_message_override(self, tmp_path: Path) -> None:
        workspace = tmp_path / "ws"
        workspace.mkdir()
        _build_pack_in_workspace(workspace, "cm-test")
        remote_url = _bare_remote(tmp_path)

        publish_pack(
            workspace, "cm-test", remote_url, yes=True,
            commit_message="Custom v0.1.0 message",
        )
        log_dst = tmp_path / "log-clone-cm"
        subprocess.run(
            ["git", "clone", "-q", "--branch", "main", remote_url, str(log_dst)],
            check=True,
        )
        log_out = subprocess.run(
            ["git", "log", "--pretty=%s", "-1"],
            cwd=log_dst, capture_output=True, text=True, check=True,
        ).stdout.strip()
        assert "Custom v0.1.0 message" in log_out


class TestPublishNoUpdateSourceUrl:
    """I-1 fix: --no-update-source-url preserves local pack.json."""

    def test_no_update_keeps_source_url_unchanged(self, tmp_path: Path) -> None:
        workspace = tmp_path / "ws"
        workspace.mkdir()
        _build_pack_in_workspace(workspace, "nus-test")
        # Pre-set source_url to some other value
        pj_path = workspace / "packs" / "nus-test" / "pack.json"
        pj = json.loads(pj_path.read_text())
        pj["source_url"] = "file:///tmp/old-source"
        pj_path.write_text(json.dumps(pj))

        remote_url = _bare_remote(tmp_path)
        summary = publish_pack(
            workspace, "nus-test", remote_url, yes=True,
            no_update_source_url=True,
        )
        assert summary.pushed is True

        new_pj = json.loads(pj_path.read_text())
        # source_url unchanged (not bumped to remote_url)
        assert new_pj["source_url"] == "file:///tmp/old-source"


class TestPublishNonexistent:
    def test_nonexistent_raises(self, tmp_path: Path) -> None:
        with pytest.raises(PackInstallError):
            publish_pack(tmp_path, "nonexistent", "file:///tmp/x.git", yes=True)


class TestPublishNonTTYWithoutYes:
    """Flag matrix: non-TTY without --yes / --dry-run → skipped."""

    def test_non_tty_returns_skipped(self, tmp_path: Path, capsys) -> None:
        workspace = tmp_path / "ws"
        workspace.mkdir()
        _build_pack_in_workspace(workspace, "nty-test")
        remote_url = _bare_remote(tmp_path)

        fake_stdin = io.StringIO("")
        fake_stdin.isatty = lambda: False  # type: ignore[method-assign]
        summary = publish_pack(
            workspace, "nty-test", remote_url, stdin=fake_stdin,
        )
        assert summary.pushed is False
        assert summary.skipped is True
        captured = capsys.readouterr()
        assert "non-interactive" in captured.err
