"""F010 code-review-r1 IMP-1 + IMP-2 fix tests."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from garage_os.cli import main
from garage_os.sync.manifest import (
    SyncManifestMigrationError,
    SyncSources,
    SyncManifest,
    write_sync_manifest,
)
from garage_os.sync.pipeline import sync_hosts
from garage_os.sync.render.markdown import wrap_with_markers


class TestImpOneSyncCatchesManifestMigrationError:
    """IMP-1 fix: _sync catches SyncManifestMigrationError + exits 1 + stderr message."""

    def test_corrupted_sync_manifest_returns_1_with_stderr(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Init garage skeleton
        main(["init", "--path", str(tmp_path), "--yes"])

        # Write corrupted sync-manifest.json
        config_dir = tmp_path / ".garage" / "config"
        (config_dir / "sync-manifest.json").write_text("{BROKEN", encoding="utf-8")
        capsys.readouterr()

        rc = main(["sync", "--path", str(tmp_path), "--hosts", "claude"])
        assert rc == 1
        captured = capsys.readouterr()
        assert "Sync manifest migration failed" in captured.err


class TestImpTwoMdcFrontMatterFallback:
    """IMP-2 fix: cursor .mdc 已存在 + 无 marker + 有用户内容路径必须注入 front matter."""

    def test_existing_mdc_no_marker_no_front_matter_gets_front_matter_injected(
        self, tmp_path: Path
    ) -> None:
        from datetime import datetime
        from garage_os.knowledge.knowledge_store import KnowledgeStore
        from garage_os.storage.file_storage import FileStorage
        from garage_os.types import KnowledgeEntry, KnowledgeType

        # Pre-create .mdc with user content but NO front matter and NO marker
        mdc_path = tmp_path / ".cursor" / "rules" / "garage-context.mdc"
        mdc_path.parent.mkdir(parents=True, exist_ok=True)
        original_user = "# My existing cursor rules\n\nUser-written prose without front matter.\n"
        mdc_path.write_text(original_user, encoding="utf-8")

        # Seed 1 knowledge entry
        storage = FileStorage(tmp_path / ".garage")
        KnowledgeStore(storage).store(
            KnowledgeEntry(
                id="d-imp2",
                type=KnowledgeType.DECISION,
                topic="imp2 test",
                date=datetime(2026, 4, 24),
                tags=[],
                content="content",
            )
        )

        sync_hosts(tmp_path, ["cursor"])

        new_content = mdc_path.read_text(encoding="utf-8")
        # IMP-2 fix: front matter MUST be at top now (FR-1004 + HYP-1002)
        assert new_content.startswith("---\n"), (
            f"FR-1004 violated: cursor .mdc must start with YAML front matter; "
            f"got: {new_content[:100]!r}"
        )
        assert "alwaysApply: true" in new_content
        # User content preserved (NFR-1003)
        assert "# My existing cursor rules" in new_content
        assert "User-written prose without front matter" in new_content
        # Marker block appended
        assert "<!-- garage:context-begin -->" in new_content

    def test_existing_mdc_with_front_matter_preserves(self, tmp_path: Path) -> None:
        """If user already has front matter (no marker), don't double-inject."""
        from datetime import datetime
        from garage_os.knowledge.knowledge_store import KnowledgeStore
        from garage_os.storage.file_storage import FileStorage
        from garage_os.types import KnowledgeEntry, KnowledgeType

        mdc_path = tmp_path / ".cursor" / "rules" / "garage-context.mdc"
        mdc_path.parent.mkdir(parents=True, exist_ok=True)
        existing_with_fm = (
            "---\n"
            "alwaysApply: true\n"
            "description: My own rules\n"
            "---\n"
            "\n"
            "# Custom user rules\n"
        )
        mdc_path.write_text(existing_with_fm, encoding="utf-8")

        storage = FileStorage(tmp_path / ".garage")
        KnowledgeStore(storage).store(
            KnowledgeEntry(
                id="d-imp2b",
                type=KnowledgeType.DECISION,
                topic="t",
                date=datetime(2026, 4, 24),
                tags=[],
                content="c",
            )
        )

        sync_hosts(tmp_path, ["cursor"])

        new_content = mdc_path.read_text(encoding="utf-8")
        # User's own front matter preserved (single occurrence of "My own rules")
        assert new_content.count("My own rules") == 1
        # User content preserved
        assert "# Custom user rules" in new_content
        # Marker block appended
        assert "<!-- garage:context-begin -->" in new_content
        # No double front matter
        assert new_content.count("alwaysApply: true") == 1
