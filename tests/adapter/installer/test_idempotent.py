"""NFR-702: re-running install with no source changes must not refresh mtime.

This is a focused, separate test from test_pipeline.py to make NFR-702
verifiable in isolation (so future regressions narrow quickly).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from garage_os.adapter.installer.pipeline import install_packs


def _build_pack(packs_root: Path) -> None:
    pack_dir = packs_root / "garage"
    skill_dir = pack_dir / "skills" / "g"
    skill_dir.mkdir(parents=True)
    (pack_dir / "pack.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "pack_id": "garage",
                "version": "0.1.0",
                "description": "x",
                "skills": ["g"],
                "agents": [],
            }
        ),
        encoding="utf-8",
    )
    (skill_dir / "SKILL.md").write_text(
        "---\nname: g\ndescription: x\n---\n\n# g\n", encoding="utf-8"
    )


class TestNoWriteWhenSourceUnchanged:
    def test_target_mtime_preserved(self, tmp_path: Path) -> None:
        _build_pack(tmp_path / "packs")
        install_packs(tmp_path, tmp_path / "packs", ["claude"], force=False)

        target = tmp_path / ".claude/skills/g/SKILL.md"
        mtime_before = target.stat().st_mtime_ns

        # Wait a meaningful interval so any write would change mtime_ns.
        time.sleep(0.02)

        install_packs(tmp_path, tmp_path / "packs", ["claude"], force=False)

        mtime_after = target.stat().st_mtime_ns
        assert mtime_after == mtime_before, (
            f"mtime changed despite source unchanged: "
            f"before={mtime_before} after={mtime_after}"
        )

    def test_force_with_unmodified_still_no_op(self, tmp_path: Path) -> None:
        # Even with --force, if no source change AND no local change,
        # the bytes are identical → no actual write → mtime preserved.
        _build_pack(tmp_path / "packs")
        install_packs(tmp_path, tmp_path / "packs", ["claude"], force=False)

        target = tmp_path / ".claude/skills/g/SKILL.md"
        mtime_before = target.stat().st_mtime_ns
        time.sleep(0.02)

        install_packs(tmp_path, tmp_path / "packs", ["claude"], force=True)

        assert target.stat().st_mtime_ns == mtime_before
