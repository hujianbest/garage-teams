"""F012-D T4 tests: knowledge export --anonymize (FR-1211..1213 + ADR-D12-5 r2)."""

from __future__ import annotations

import io
import json
import tarfile
from datetime import datetime
from pathlib import Path

import pytest

from garage_os.knowledge.exporter import (
    ANONYMIZE_RULES,
    ExportSummary,
    _anonymize_body,
    _split_front_matter,
    export_anonymized,
    load_user_extra_rules,
)
from garage_os.knowledge.knowledge_store import KnowledgeStore
from garage_os.storage.file_storage import FileStorage
from garage_os.types import KnowledgeEntry, KnowledgeType


def _seed_knowledge(workspace: Path) -> None:
    """Seed several entries with sensitive content."""
    storage = FileStorage(workspace / ".garage")
    store = KnowledgeStore(storage)

    store.store(KnowledgeEntry(
        id="d-001", type=KnowledgeType.DECISION, topic="Test decision",
        date=datetime(2026, 4, 25), tags=["test"],
        content="Decision: discussed with alice@example.com",
    ))
    store.store(KnowledgeEntry(
        id="p-001", type=KnowledgeType.PATTERN, topic="Test pattern",
        date=datetime(2026, 4, 25), tags=[],
        content="Use api_key=sk-1234567890 for auth",
    ))
    store.store(KnowledgeEntry(
        id="s-001", type=KnowledgeType.SOLUTION, topic="Test solution",
        date=datetime(2026, 4, 25), tags=[],
        content="commit hash 1234567890abcdef1234567890abcdef12345678",
    ))


class TestAnonymizeRules:
    def test_7_rules_present(self) -> None:
        rule_names = [r[0] for r in ANONYMIZE_RULES]
        assert sorted(rule_names) == sorted([
            "email", "password", "api_key", "secret", "token", "sha1_hash", "private_key",
        ])

    def test_email_replacement(self) -> None:
        body = "Contact alice@example.com tomorrow"
        result = _anonymize_body(body, ANONYMIZE_RULES, {})
        assert "alice@example.com" not in result
        assert "<REDACTED:email>" in result

    def test_password_replacement_preserves_key(self) -> None:
        body = "password=secret123"
        result = _anonymize_body(body, ANONYMIZE_RULES, {})
        assert result == "password=<REDACTED>"

    def test_sha1_hash_replacement(self) -> None:
        body = "commit 1234567890abcdef1234567890abcdef12345678"
        result = _anonymize_body(body, ANONYMIZE_RULES, {})
        assert "1234567890abcdef1234567890abcdef12345678" not in result
        assert "<REDACTED:sha1>" in result

    def test_private_key_replacement(self) -> None:
        body = "-----BEGIN RSA PRIVATE KEY-----\nMIIEvQ...\n-----END RSA PRIVATE KEY-----"
        result = _anonymize_body(body, ANONYMIZE_RULES, {})
        assert "MIIEvQ" not in result
        assert "-----REDACTED-----" in result


class TestSplitFrontMatter:
    def test_with_front_matter(self) -> None:
        content = "---\nid: foo\ntopic: bar\n---\n# Body\n"
        front, body = _split_front_matter(content)
        assert front == "---\nid: foo\ntopic: bar\n---\n"
        assert body == "# Body\n"

    def test_no_front_matter(self) -> None:
        content = "# Just body, no front matter\n"
        front, body = _split_front_matter(content)
        assert front == ""
        assert body == content


class TestExportAnonymizedRealTarball:
    def test_tarball_created_with_redacted_content(self, tmp_path: Path) -> None:
        workspace = tmp_path / "ws"
        workspace.mkdir()
        _seed_knowledge(workspace)

        output_dir = tmp_path / "exports"
        summary = export_anonymized(workspace, output_dir=output_dir)

        assert summary.entry_count == 3
        assert summary.output_path is not None
        assert summary.output_path.is_file()
        # Email + api_key + sha1_hash hits
        assert summary.rule_hit_counts.get("email", 0) >= 1
        assert summary.rule_hit_counts.get("api_key", 0) >= 1
        assert summary.rule_hit_counts.get("sha1_hash", 0) >= 1

        # Inspect tarball content
        with tarfile.open(summary.output_path, "r:gz") as tar:
            members = tar.getnames()
            assert any("manifest.json" in m for m in members)
            # Extract decision and check redaction
            extract_dir = tmp_path / "extracted"
            tar.extractall(extract_dir, filter="data")
            d001 = extract_dir / "knowledge-export" / "decisions"
            md_files = list(d001.glob("*.md"))
            assert md_files
            # Original email replaced
            content = md_files[0].read_text()
            assert "alice@example.com" not in content
            assert "<REDACTED:email>" in content
            # Front matter preserved (id, topic, tags fields not anonymized)
            assert "topic: Test decision" in content


class TestFrontMatterPreserved:
    """ADR-D12-5 r2 + FR-1211 step 2: front matter not anonymized."""

    def test_topic_in_front_matter_preserved(self, tmp_path: Path) -> None:
        workspace = tmp_path / "ws"
        workspace.mkdir()
        storage = FileStorage(workspace / ".garage")
        store = KnowledgeStore(storage)
        # Topic contains email-shaped string in front matter
        store.store(KnowledgeEntry(
            id="fm-001", type=KnowledgeType.DECISION,
            topic="Email pattern alice@example.com discussion",  # in front matter
            date=datetime(2026, 4, 25), tags=["email"],
            content="Body talks about bob@example.com here",  # in body
        ))

        summary = export_anonymized(workspace, output_dir=tmp_path / "out")
        with tarfile.open(summary.output_path, "r:gz") as tar:
            tar.extractall(tmp_path / "ex", filter="data")
        md = list((tmp_path / "ex" / "knowledge-export" / "decisions").glob("*.md"))[0]
        text = md.read_text()
        # Front matter topic preserves email-shaped string (not anonymized)
        assert "Email pattern alice@example.com discussion" in text or "alice@example.com" in text.split("\n---\n")[0]
        # Body's email is anonymized
        body = text.split("\n---\n")[-1]
        assert "bob@example.com" not in body
        assert "<REDACTED:email>" in body


class TestExportDryRun:
    def test_dry_run_no_tarball(self, tmp_path: Path, capsys) -> None:
        workspace = tmp_path / "ws"
        workspace.mkdir()
        _seed_knowledge(workspace)
        output_dir = tmp_path / "exports"

        summary = export_anonymized(
            workspace, output_dir=output_dir, dry_run=True,
        )
        assert summary.output_path is None
        # rule hit counts populated
        assert sum(summary.rule_hit_counts.values()) > 0
        # No tarball written
        assert not output_dir.exists() or not list(output_dir.glob("*.tar.gz"))
        captured = capsys.readouterr()
        assert "DRY RUN" in captured.err


class TestExportOutputInWorkspaceWarn:
    """Mi-3 fix: workspace 内 output + .gitignore 不含 → stderr warn."""

    def test_warn_when_output_inside_workspace_no_gitignore(
        self, tmp_path: Path, capsys
    ) -> None:
        workspace = tmp_path / "ws"
        workspace.mkdir()
        _seed_knowledge(workspace)
        # No .gitignore in workspace
        output_dir = workspace / "exports"

        export_anonymized(workspace, output_dir=output_dir)
        captured = capsys.readouterr()
        assert "WARNING" in captured.err
        assert "exports" in captured.err

    def test_no_warn_when_gitignore_excludes(
        self, tmp_path: Path, capsys
    ) -> None:
        workspace = tmp_path / "ws"
        workspace.mkdir()
        _seed_knowledge(workspace)
        (workspace / ".gitignore").write_text("exports/\n*.tar.gz\n")
        output_dir = workspace / "exports"

        export_anonymized(workspace, output_dir=output_dir)
        captured = capsys.readouterr()
        # Warning suppressed
        assert "WARNING" not in captured.err

    def test_default_outside_workspace(self, tmp_path: Path, monkeypatch) -> None:
        """Default output is ~/.garage/exports/ (outside workspace, no warn)."""
        workspace = tmp_path / "ws"
        workspace.mkdir()
        _seed_knowledge(workspace)

        # Redirect HOME to tmp to avoid polluting real ~/
        fake_home = tmp_path / "fake-home"
        fake_home.mkdir()
        monkeypatch.setenv("HOME", str(fake_home))
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))

        summary = export_anonymized(workspace)
        assert summary.output_path is not None
        # Output is outside workspace
        assert fake_home in summary.output_path.parents


class TestUserExtraRules:
    """FR-1212: ~/.garage/anonymize-patterns.txt extra rules."""

    def test_user_rule_applied(self, tmp_path: Path, monkeypatch) -> None:
        workspace = tmp_path / "ws"
        workspace.mkdir()
        storage = FileStorage(workspace / ".garage")
        KnowledgeStore(storage).store(KnowledgeEntry(
            id="ur-001", type=KnowledgeType.DECISION, topic="t",
            date=datetime(2026, 4, 25), tags=[],
            content="MyCompany internal decision",
        ))

        # Plant user extra rules
        fake_home = tmp_path / "fake-home"
        fake_home.mkdir()
        (fake_home / ".garage").mkdir()
        (fake_home / ".garage" / "anonymize-patterns.txt").write_text(
            "# Custom rules\nMyCompany\n",
        )
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))

        # Verify rules loaded
        extra = load_user_extra_rules()
        assert len(extra) == 1
        assert extra[0][0].startswith("user_rule_")

        # Run export
        summary = export_anonymized(workspace, output_dir=tmp_path / "out")
        with tarfile.open(summary.output_path, "r:gz") as tar:
            tar.extractall(tmp_path / "ex", filter="data")
        md = list((tmp_path / "ex" / "knowledge-export" / "decisions").glob("*.md"))[0]
        body = md.read_text().split("\n---\n")[-1]
        assert "MyCompany" not in body
        assert "<REDACTED:user>" in body
