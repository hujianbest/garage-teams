"""Sentinel test: docs/principles/skill-anatomy.md exists and is well-formed.

History:
    F008 ADR-D8-3 (reverse-sync from harness-flow upstream) initially created
    two byte-equal copies of skill-anatomy.md (one at docs/principles/, one at
    packs/coding/principles/), and this sentinel guarded their byte equality.

    The post-PR#41 reverse-sync from harness-flow v0.1.0 dropped the bundled
    HF principles tree entirely (per upstream ADR-001 D11: 'docs/principles/
    is design reference only, not a runtime dependency, not a release gate').
    packs/coding/principles/ no longer exists as a result.

    docs/principles/skill-anatomy.md remains as garage's own authoring spec
    referenced from AGENTS.md ('新增或重写任何 skill 时，必须遵循此文档'),
    so we still need a sentinel that catches accidental deletion of the root
    file. The cross-copy drift check is gone because there is no second copy
    to drift against.

Note:
    This test does NOT use ``tmp_path`` or any ``.garage/`` fixture. It
    directly reads a fixed path in the repo. That is the defining
    characteristic of a sentinel test — it asserts repo-state invariants,
    not behaviour.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
ROOT_PRINCIPLE_PATH = REPO_ROOT / "docs" / "principles" / "skill-anatomy.md"


class TestSkillAnatomyExists:
    """Garage-side authoring spec must exist (referenced from AGENTS.md)."""

    def test_root_principle_present(self) -> None:
        assert ROOT_PRINCIPLE_PATH.is_file(), (
            f"Expected garage authoring spec at {ROOT_PRINCIPLE_PATH}. "
            "AGENTS.md (## Skill 写作原则 section) declares this file as the "
            "mandatory authoring spec for any new garage skill. If you "
            "intentionally moved or removed it, update AGENTS.md and this "
            "sentinel together."
        )

    def test_root_principle_non_empty(self) -> None:
        size = ROOT_PRINCIPLE_PATH.stat().st_size
        assert size > 0, (
            f"{ROOT_PRINCIPLE_PATH} is empty. The authoring spec must contain "
            "at least the 7 core principles + directory anatomy + section "
            "skeleton sections that AGENTS.md cites."
        )
