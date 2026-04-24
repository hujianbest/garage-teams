"""End-to-end + unit tests for garage_os.adapter.installer.pipeline.

Covers F007 T3 walking skeleton + FR-704 / FR-706a / FR-706b / FR-708 / NFR-702.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import pytest

from garage_os.adapter.installer.manifest import (
    read_manifest,
)
from garage_os.adapter.installer.pipeline import (
    ConflictingSkillError,
    InstallSummary,
    install_packs,
)


def _build_garage_pack(packs_root: Path) -> None:
    """Create a minimal one-skill / one-agent pack at packs_root/garage/."""
    pack_dir = packs_root / "garage"
    skills_dir = pack_dir / "skills" / "garage-hello"
    agents_dir = pack_dir / "agents"
    skills_dir.mkdir(parents=True)
    agents_dir.mkdir(parents=True)

    (pack_dir / "pack.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "pack_id": "garage",
                "version": "0.1.0",
                "description": "test pack",
                "skills": ["garage-hello"],
                "agents": ["sample"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (skills_dir / "SKILL.md").write_text(
        "---\nname: garage-hello\ndescription: hi\n---\n\n# Hello\nBody.\n",
        encoding="utf-8",
    )
    (agents_dir / "sample.md").write_text(
        "# Sample Agent\n\nMinimal agent.\n", encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Walking skeleton (T3 测试种子 主行为)
# ---------------------------------------------------------------------------


class TestWalkingSkeleton:
    def test_install_packs_writes_skill_and_manifest(self, tmp_path: Path) -> None:
        _build_garage_pack(tmp_path / "packs")

        summary = install_packs(
            workspace_root=tmp_path,
            packs_root=tmp_path / "packs",
            hosts=["claude"],
            force=False,
        )

        # Skill installed.
        skill_dst = tmp_path / ".claude/skills/garage-hello/SKILL.md"
        assert skill_dst.exists()
        text = skill_dst.read_text(encoding="utf-8")
        assert "name: garage-hello" in text
        assert "installed_by: garage" in text
        assert "installed_pack: garage" in text

        # Agent installed (claude has agent surface).
        agent_dst = tmp_path / ".claude/agents/sample.md"
        assert agent_dst.exists()
        atext = agent_dst.read_text(encoding="utf-8")
        assert "installed_by: garage" in atext  # injected even for no-FM source

        # Manifest written and self-consistent.
        manifest = read_manifest(tmp_path / ".garage")
        assert manifest is not None
        assert manifest.installed_hosts == ["claude"]
        assert manifest.installed_packs == ["garage"]
        assert len(manifest.files) == 2
        # content_hash matches what was actually written.
        for entry in manifest.files:
            installed_path = tmp_path / entry.dst
            actual_hash = hashlib.sha256(
                installed_path.read_bytes()
            ).hexdigest()
            assert entry.content_hash == actual_hash

        # Summary returned.
        assert isinstance(summary, InstallSummary)
        assert summary.n_skills == 1
        assert summary.n_agents == 1
        assert summary.hosts == ["claude"]


class TestSkillSidecarSync:
    """references/ + assets/ beside SKILL.md are copied to the host skill dir."""

    def test_install_copies_references_and_assets(self, tmp_path: Path) -> None:
        pack_dir = tmp_path / "packs" / "demo"
        skill_dir = pack_dir / "skills" / "sidecar-skill"
        skill_dir.mkdir(parents=True)
        (pack_dir / "pack.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "pack_id": "demo",
                    "version": "0.1.0",
                    "description": "fixture",
                    "skills": ["sidecar-skill"],
                    "agents": [],
                }
            ),
            encoding="utf-8",
        )
        (skill_dir / "SKILL.md").write_text(
            "---\nname: sidecar-skill\ndescription: test\n---\n\n# Sidecar\n",
            encoding="utf-8",
        )
        (skill_dir / "references").mkdir()
        (skill_dir / "references" / "note.md").write_text(
            "reference body\n", encoding="utf-8"
        )
        (skill_dir / "assets").mkdir()
        (skill_dir / "assets" / "t.txt").write_text("asset bytes\n", encoding="utf-8")

        install_packs(
            workspace_root=tmp_path,
            packs_root=tmp_path / "packs",
            hosts=["claude"],
            force=False,
        )

        dst_base = tmp_path / ".claude/skills/sidecar-skill"
        note = dst_base / "references" / "note.md"
        ttxt = dst_base / "assets" / "t.txt"
        assert note.is_file()
        assert ttxt.is_file()
        assert note.read_text(encoding="utf-8") == "reference body\n"
        assert ttxt.read_text(encoding="utf-8") == "asset bytes\n"


# ---------------------------------------------------------------------------
# 关键边界 1 & 2: locally modified protection + --force
# ---------------------------------------------------------------------------


class TestLocallyModifiedProtection:
    def test_install_locally_modified_skip_default(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _build_garage_pack(tmp_path / "packs")
        install_packs(tmp_path, tmp_path / "packs", ["claude"], force=False)

        # User modifies a file.
        skill_dst = tmp_path / ".claude/skills/garage-hello/SKILL.md"
        skill_dst.write_text("USER EDIT", encoding="utf-8")

        capsys.readouterr()  # clear

        install_packs(tmp_path, tmp_path / "packs", ["claude"], force=False)

        # File NOT overwritten.
        assert skill_dst.read_text(encoding="utf-8") == "USER EDIT"
        captured = capsys.readouterr()
        assert "Skipped" in captured.err
        assert "locally modified" in captured.err

    def test_install_force_overwrites_locally_modified(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _build_garage_pack(tmp_path / "packs")
        install_packs(tmp_path, tmp_path / "packs", ["claude"], force=False)

        skill_dst = tmp_path / ".claude/skills/garage-hello/SKILL.md"
        skill_dst.write_text("USER EDIT", encoding="utf-8")
        capsys.readouterr()

        install_packs(tmp_path, tmp_path / "packs", ["claude"], force=True)

        # File restored from source (with marker injected).
        text = skill_dst.read_text(encoding="utf-8")
        assert "USER EDIT" not in text
        assert "name: garage-hello" in text
        captured = capsys.readouterr()
        assert "Overwrote" in captured.err


# ---------------------------------------------------------------------------
# 关键边界 3: extend hosts (no-touch existing)
# ---------------------------------------------------------------------------


class TestExtendHosts:
    def test_extend_hosts_no_touch_existing(self, tmp_path: Path) -> None:
        _build_garage_pack(tmp_path / "packs")

        # First install: claude only.
        install_packs(tmp_path, tmp_path / "packs", ["claude"], force=False)

        claude_skill = tmp_path / ".claude/skills/garage-hello/SKILL.md"
        mtime_before = claude_skill.stat().st_mtime_ns

        # Sleep briefly to make any false-positive mtime change easy to detect.
        time.sleep(0.01)

        # Second install: cursor only.
        install_packs(tmp_path, tmp_path / "packs", ["cursor"], force=False)

        # Claude file mtime unchanged.
        assert claude_skill.stat().st_mtime_ns == mtime_before

        # Cursor file appeared.
        cursor_skill = tmp_path / ".cursor/skills/garage-hello/SKILL.md"
        assert cursor_skill.exists()

        # Manifest accumulates both hosts.
        manifest = read_manifest(tmp_path / ".garage")
        assert manifest is not None
        assert manifest.installed_hosts == ["claude", "cursor"]


# ---------------------------------------------------------------------------
# 关键边界 4: cross-pack same-skill conflict
# ---------------------------------------------------------------------------


class TestConflict:
    def test_conflict_same_skill_two_packs(self, tmp_path: Path) -> None:
        packs = tmp_path / "packs"
        for pack_id in ("packs_a", "packs_b"):
            pack_dir = packs / pack_id
            skill_dir = pack_dir / "skills" / "foo"
            skill_dir.mkdir(parents=True)
            (pack_dir / "pack.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "pack_id": pack_id,
                        "version": "0.1.0",
                        "description": "fixture",
                        "skills": ["foo"],
                        "agents": [],
                    }
                ),
                encoding="utf-8",
            )
            (skill_dir / "SKILL.md").write_text(
                "---\nname: foo\ndescription: x\n---\n\n# foo\n",
                encoding="utf-8",
            )

        with pytest.raises(ConflictingSkillError) as exc_info:
            install_packs(tmp_path, packs, ["claude"], force=False)
        msg = str(exc_info.value)
        assert "packs_a" in msg
        assert "packs_b" in msg


# ---------------------------------------------------------------------------
# Empty packs / missing packs root
# ---------------------------------------------------------------------------


class TestNoPacksFound:
    def test_no_packs_returns_empty_manifest(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Empty packs/ dir → install completes, manifest has no files.
        (tmp_path / "packs").mkdir()
        summary = install_packs(tmp_path, tmp_path / "packs", ["claude"], force=False)
        assert summary.n_skills == 0
        assert summary.n_agents == 0

        manifest = read_manifest(tmp_path / ".garage")
        assert manifest is not None
        assert manifest.installed_hosts == ["claude"]
        assert manifest.installed_packs == []
        assert manifest.files == []

        captured = capsys.readouterr()
        assert "No packs found" in captured.out

    def test_missing_packs_root_returns_empty(self, tmp_path: Path) -> None:
        # No packs/ dir at all (e.g. fresh repo) → equivalent to empty packs.
        summary = install_packs(tmp_path, tmp_path / "packs", ["claude"], force=False)
        assert summary.n_skills == 0


# ---------------------------------------------------------------------------
# Cursor agent skip (no native agent surface)
# ---------------------------------------------------------------------------


class TestCursorAgentSkip:
    def test_cursor_does_not_install_agent_files(self, tmp_path: Path) -> None:
        _build_garage_pack(tmp_path / "packs")
        install_packs(tmp_path, tmp_path / "packs", ["cursor"], force=False)

        # Skill installed under .cursor/skills/.
        assert (tmp_path / ".cursor/skills/garage-hello/SKILL.md").exists()
        # No .cursor/agent/ or .cursor/agents/ directories created.
        assert not (tmp_path / ".cursor/agents").exists()
        assert not (tmp_path / ".cursor/agent").exists()


# ---------------------------------------------------------------------------
# Idempotency (NFR-702): mtime not refreshed when source unchanged
# ---------------------------------------------------------------------------


class TestIdempotentNoWrite:
    def test_unmodified_no_mtime_refresh(self, tmp_path: Path) -> None:
        _build_garage_pack(tmp_path / "packs")
        install_packs(tmp_path, tmp_path / "packs", ["claude"], force=False)

        skill_dst = tmp_path / ".claude/skills/garage-hello/SKILL.md"
        mtime_before = skill_dst.stat().st_mtime_ns

        time.sleep(0.01)

        # Re-run with no source changes; target mtime must stay the same.
        install_packs(tmp_path, tmp_path / "packs", ["claude"], force=False)
        assert skill_dst.stat().st_mtime_ns == mtime_before


# ---------------------------------------------------------------------------
# F007 test-review carry-forward F-4: D7 §10.2 decision table edge rows
# ---------------------------------------------------------------------------


class TestDecisionTableEdgeRows:
    """Two decision-table rows not covered by the main scenarios above."""

    def test_existing_entry_but_dst_deleted_writes_new(self, tmp_path: Path) -> None:
        """Row: existing entry yes, dst missing → WRITE_NEW (restore)."""
        _build_garage_pack(tmp_path / "packs")
        install_packs(tmp_path, tmp_path / "packs", ["claude"], force=False)

        skill_dst = tmp_path / ".claude/skills/garage-hello/SKILL.md"
        assert skill_dst.exists()

        # User deletes the file but leaves the manifest entry.
        skill_dst.unlink()
        assert not skill_dst.exists()

        # Re-install: should restore (WRITE_NEW path on missing dst with entry).
        install_packs(tmp_path, tmp_path / "packs", ["claude"], force=False)
        assert skill_dst.exists()
        assert "name: garage-hello" in skill_dst.read_text(encoding="utf-8")

    def test_no_entry_and_dst_exists_with_force_overwrites(
        self, tmp_path: Path, capsys
    ) -> None:
        """Row: no entry, dst exists, force=True → OVERWRITE_FORCED."""
        _build_garage_pack(tmp_path / "packs")
        # Pre-create a stray file at the would-be dst (not from prior install).
        (tmp_path / ".claude" / "skills" / "garage-hello").mkdir(
            parents=True
        )
        (tmp_path / ".claude/skills/garage-hello/SKILL.md").write_text(
            "USER WROTE THIS BEFORE GARAGE", encoding="utf-8"
        )

        # No prior install → no manifest entry.
        capsys.readouterr()  # clear

        # force=True must overwrite the stray file.
        install_packs(tmp_path, tmp_path / "packs", ["claude"], force=True)

        text = (tmp_path / ".claude/skills/garage-hello/SKILL.md").read_text(
            encoding="utf-8"
        )
        assert "USER WROTE" not in text
        assert "name: garage-hello" in text
        captured = capsys.readouterr()
        assert "Overwrote" in captured.err


class TestConflictAgentDimension:
    """F007 hf-code-review F007-CR-5 carry-forward: agent-name conflicts too."""

    def test_conflict_same_agent_two_packs(self, tmp_path: Path) -> None:
        packs = tmp_path / "packs"
        for pack_id in ("packs_x", "packs_y"):
            pack_dir = packs / pack_id
            agents_dir = pack_dir / "agents"
            agents_dir.mkdir(parents=True)
            (pack_dir / "pack.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "pack_id": pack_id,
                        "version": "0.1.0",
                        "description": "fixture",
                        "skills": [],
                        "agents": ["dup"],
                    }
                ),
                encoding="utf-8",
            )
            (agents_dir / "dup.md").write_text(
                "# dup agent\n", encoding="utf-8"
            )
        with pytest.raises(ConflictingSkillError) as exc_info:
            install_packs(tmp_path, packs, ["claude"], force=False)
        msg = str(exc_info.value)
        assert "packs_x" in msg
        assert "packs_y" in msg
