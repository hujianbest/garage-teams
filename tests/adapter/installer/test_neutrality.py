"""NFR-701: ``packs/`` content (skill + agent files) must be host-neutral.

This is the primary contract test for the spec NFR-701 + design NFR-701
mandate: packs/ source files MUST NOT contain any host-specific terms
(``.claude/`` / ``.cursor/`` / ``.opencode/`` / ``claude-code``). Only the
adapter implementations may know host names; packs themselves stay neutral
so adding a new host doesn't require touching any pack.

Scope: this test scans ``packs/<pack-id>/skills/<id>/SKILL.md`` and
``packs/<pack-id>/agents/<id>.md`` only — pack-level READMEs and pack.json
are meta-files (they document the contract itself) and are out of scope.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
PACKS_ROOT = REPO_ROOT / "packs"

HOST_BLACKLIST_PATTERN = re.compile(
    r"\.claude/|\.cursor/|\.opencode/|claude-code", re.IGNORECASE
)


def _iter_pack_content_files() -> list[Path]:
    """Return every SKILL.md and agent .md under packs/."""
    if not PACKS_ROOT.exists():
        return []
    out: list[Path] = []
    for skill in PACKS_ROOT.glob("*/skills/*/SKILL.md"):
        out.append(skill)
    for agent in PACKS_ROOT.glob("*/agents/*.md"):
        out.append(agent)
    return out


class TestPacksHostNeutrality:
    def test_packs_root_exists(self) -> None:
        # Sanity: T1 must have created packs/ before this test runs.
        assert PACKS_ROOT.is_dir(), f"Expected packs/ at {PACKS_ROOT}"

    @pytest.mark.parametrize("file_path", _iter_pack_content_files())
    def test_no_host_specific_terms(self, file_path: Path) -> None:
        text = file_path.read_text(encoding="utf-8")
        match = HOST_BLACKLIST_PATTERN.search(text)
        assert match is None, (
            f"Host-specific term {match.group(0)!r} found in {file_path}; "
            "pack content must stay host-neutral (NFR-701)."
        )
