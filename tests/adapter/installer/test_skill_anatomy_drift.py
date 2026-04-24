"""Sentinel test: root-level vs packs/coding/principles/ skill-anatomy.md byte equality.

Implements F008 spec § 4.2 红线 3 (drift collapse) + design ADR-D8-3 (reverse-sync
strategy) + INV-3 (drift collapse hard gate).

Background:
    Before F008 the repo had two divergent copies of skill-anatomy.md:
    - root: ``docs/principles/skill-anatomy.md`` (early "AHE" terminology)
    - HF family: ``.agents/skills/harness-flow/docs/principles/skill-anatomy.md``
      (current "HF" terminology, 70 byte diff)

    F008 ADR-D8-3 chose **reverse-sync**:
    - HF family copy (HF terminology, 2026-04-18) is the authoritative source
    - copied to ``packs/coding/principles/skill-anatomy.md`` (T1b)
    - root file is overwritten with the same byte content (T1c)

    This sentinel test guards against future drift: any commit that modifies
    ONE of the two files without the other will turn this test RED.

Note (per F008 task plan T1c Files spec):
    This test does NOT use ``tmp_path`` or any ``.garage/`` fixture. It directly
    reads two fixed paths in the repo. That is the defining characteristic of a
    sentinel test - it asserts repo-state invariants, not behaviour.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
ROOT_PRINCIPLE_PATH = REPO_ROOT / "docs" / "principles" / "skill-anatomy.md"
PACKS_PRINCIPLE_PATH = (
    REPO_ROOT / "packs" / "coding" / "principles" / "skill-anatomy.md"
)


class TestSkillAnatomyDriftCollapse:
    def test_root_and_packs_principles_byte_equal(self) -> None:
        """Both copies of skill-anatomy.md MUST be byte-level equal (INV-3)."""
        assert ROOT_PRINCIPLE_PATH.is_file(), (
            f"Expected root principle at {ROOT_PRINCIPLE_PATH} (F008 ADR-D8-3 keeps "
            "this file as the AGENTS.md cold-read entrypoint)."
        )
        assert PACKS_PRINCIPLE_PATH.is_file(), (
            f"Expected packs principle at {PACKS_PRINCIPLE_PATH} (F008 T1b "
            "should have copied the HF authoritative source here)."
        )

        root_hash = hashlib.sha256(ROOT_PRINCIPLE_PATH.read_bytes()).hexdigest()
        packs_hash = hashlib.sha256(PACKS_PRINCIPLE_PATH.read_bytes()).hexdigest()

        assert root_hash == packs_hash, (
            "skill-anatomy.md drift detected!\n"
            f"  {ROOT_PRINCIPLE_PATH.relative_to(REPO_ROOT)} sha256={root_hash}\n"
            f"  {PACKS_PRINCIPLE_PATH.relative_to(REPO_ROOT)} sha256={packs_hash}\n"
            "F008 ADR-D8-3 requires both copies to be byte-equal. If you "
            "intentionally modified one, run "
            "`cp packs/coding/principles/skill-anatomy.md docs/principles/skill-anatomy.md` "
            "(or vice-versa) to restore parity."
        )
