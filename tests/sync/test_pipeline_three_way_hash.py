"""F010 T3: ADR-D10-3 r2 三方 hash 决策表三种状态测试."""

from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path

import pytest

from garage_os.knowledge.knowledge_store import KnowledgeStore
from garage_os.storage.file_storage import FileStorage
from garage_os.sync.pipeline import SyncWriteAction, sync_hosts
from garage_os.types import KnowledgeEntry, KnowledgeType


def _seed(workspace_root: Path, n: int = 1) -> None:
    storage = FileStorage(workspace_root / ".garage")
    store = KnowledgeStore(storage)
    for i in range(n):
        store.store(
            KnowledgeEntry(
                id=f"d-{i:03d}",
                type=KnowledgeType.DECISION,
                topic=f"topic {i}",
                date=datetime(2026, 4, 24, 10, i),
                tags=[],
                content=f"content {i}",
            )
        )


class TestThreeWayHashDecision:
    def test_first_sync_write_new(self, tmp_path: Path) -> None:
        _seed(tmp_path)
        summary = sync_hosts(tmp_path, ["claude"])
        assert summary.targets[0].action == SyncWriteAction.WRITE_NEW.value

    def test_unchanged_when_no_modification(self, tmp_path: Path) -> None:
        _seed(tmp_path)
        sync_hosts(tmp_path, ["claude"])
        summary = sync_hosts(tmp_path, ["claude"])
        assert summary.targets[0].action == SyncWriteAction.UNCHANGED.value

    def test_update_from_source_when_garage_changes(self, tmp_path: Path) -> None:
        _seed(tmp_path)
        sync_hosts(tmp_path, ["claude"])
        # Add another entry
        _seed(tmp_path, n=2)  # adds d-001 (already there) + d-001? actually just same hash; use new
        storage = FileStorage(tmp_path / ".garage")
        store = KnowledgeStore(storage)
        store.store(
            KnowledgeEntry(
                id="d-new",
                type=KnowledgeType.DECISION,
                topic="new",
                date=datetime(2026, 4, 25),
                tags=[],
                content="new content",
            )
        )
        summary = sync_hosts(tmp_path, ["claude"])
        assert summary.targets[0].action == SyncWriteAction.UPDATE_FROM_SOURCE.value

    def test_skip_locally_modified(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _seed(tmp_path)
        sync_hosts(tmp_path, ["claude"])

        # User edits marker block content
        claude_md = tmp_path / "CLAUDE.md"
        edited = claude_md.read_text().replace("topic 0", "USER_EDITED")
        claude_md.write_text(edited)

        stderr = io.StringIO()
        summary = sync_hosts(tmp_path, ["claude"], stderr=stderr)
        # Skip
        assert summary.n_hosts_skipped == 1
        assert "SKIP_LOCALLY_MODIFIED" in stderr.getvalue()
        # File preserved
        assert "USER_EDITED" in claude_md.read_text()

    def test_overwrite_forced_with_force_flag(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _seed(tmp_path)
        sync_hosts(tmp_path, ["claude"])

        claude_md = tmp_path / "CLAUDE.md"
        edited = claude_md.read_text().replace("topic 0", "USER_EDITED")
        claude_md.write_text(edited)

        stderr = io.StringIO()
        summary = sync_hosts(tmp_path, ["claude"], force=True, stderr=stderr)
        assert summary.n_hosts_written == 1
        assert summary.targets[0].action == SyncWriteAction.OVERWRITE_FORCED.value
        assert "OVERWRITE_FORCED" in stderr.getvalue()
        # User edit overwritten
        assert "USER_EDITED" not in claude_md.read_text()


class TestSyncManifestIsolation:
    """INV-F10-6: sync-manifest.json 与 host-installer.json 完全独立."""

    def test_only_sync_manifest_written(self, tmp_path: Path) -> None:
        _seed(tmp_path)
        sync_hosts(tmp_path, ["claude"])

        sync_path = tmp_path / ".garage" / "config" / "sync-manifest.json"
        host_installer_path = tmp_path / ".garage" / "config" / "host-installer.json"

        assert sync_path.is_file()
        assert not host_installer_path.exists()  # 完全独立, 不创建 install manifest


class TestThreeHostsTargets:
    """FR-1004 + FR-1002: 三家 host 路径 + per-host scope override."""

    def test_three_hosts_project_scope(self, tmp_path: Path) -> None:
        _seed(tmp_path)
        summary = sync_hosts(tmp_path, ["claude", "cursor", "opencode"])
        assert summary.n_hosts_written == 3
        assert (tmp_path / "CLAUDE.md").exists()
        assert (tmp_path / ".cursor/rules/garage-context.mdc").exists()
        assert (tmp_path / ".opencode/AGENTS.md").exists()

    def test_cursor_mdc_has_front_matter(self, tmp_path: Path) -> None:
        _seed(tmp_path)
        sync_hosts(tmp_path, ["cursor"])
        mdc = (tmp_path / ".cursor/rules/garage-context.mdc").read_text()
        assert mdc.startswith("---\n")
        assert "alwaysApply: true" in mdc

    def test_per_host_scope_override(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake_home = tmp_path / "fake-home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))
        _seed(tmp_path)

        summary = sync_hosts(
            tmp_path,
            ["claude", "cursor"],
            scopes_per_host={"claude": "user", "cursor": "project"},
        )
        assert summary.n_hosts_written == 2
        assert (fake_home / ".claude/CLAUDE.md").exists()
        assert (tmp_path / ".cursor/rules/garage-context.mdc").exists()
        assert not (tmp_path / "CLAUDE.md").exists()  # claude went to user scope only
