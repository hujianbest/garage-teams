"""F013-A T5 sentinel: CON-1304 — promote MUST NOT modify packs/<id>/pack.json."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from garage_os.cli import main


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_promote_does_not_modify_pack_json(tmp_path: Path, capsys) -> None:
    """CON-1304 sentinel: after `garage skill promote`, packs/garage/pack.json
    bytes are identical (skills[] not touched). User must run hf-test-driven-dev
    to register the skill in pack.json themselves.
    """
    workspace = tmp_path / "ws"
    workspace.mkdir()

    # Create packs/garage/ with a real pack.json
    pack_dir = workspace / "packs" / "garage"
    pack_dir.mkdir(parents=True)
    pack_json = pack_dir / "pack.json"
    pack_json.write_text(json.dumps({
        "schema_version": 1,
        "pack_id": "garage",
        "version": "0.3.0",
        "description": "test",
        "skills": ["existing-skill"],
        "agents": [],
    }, indent=2), encoding="utf-8")

    # Snapshot pack.json hash
    before_hash = _hash_file(pack_json)

    # Init + seed + rescan + promote
    main(["init", "--path", str(workspace), "--yes"])
    capsys.readouterr()

    # Seed evidence directly
    from garage_os.knowledge.experience_index import ExperienceIndex
    from garage_os.skill_mining.suggestion_store import SuggestionStore
    from garage_os.skill_mining.types import SkillSuggestionStatus
    from garage_os.storage.file_storage import FileStorage
    from garage_os.types import ExperienceRecord
    storage = FileStorage(workspace / ".garage")
    ei = ExperienceIndex(storage)
    for i in range(5):
        ei.store(ExperienceRecord(
            record_id=f"r-{i:03d}",
            task_type="review",
            skill_ids=[],
            tech_stack=[],
            domain="dev",
            problem_domain="review-verdict",
            outcome="success",
            duration_seconds=60,
            complexity="low",
            session_id=f"ses-{i:03d}",
            key_patterns=["verdict-format", "5-section"],
        ))
    main(["skill", "suggest", "--path", str(workspace), "--rescan"])
    capsys.readouterr()

    ss = SuggestionStore(workspace / ".garage")
    sg_id = ss.list_by_status(SkillSuggestionStatus.PROPOSED)[0].id

    rc = main(["skill", "promote", "--path", str(workspace), sg_id, "--yes"])
    assert rc == 0
    capsys.readouterr()

    # Sentinel: pack.json bytes unchanged
    after_hash = _hash_file(pack_json)
    assert before_hash == after_hash, (
        "CON-1304 violated: garage skill promote modified packs/garage/pack.json. "
        "Per spec FR-1304, promote MUST NOT touch pack.json skills[] list — "
        "users must run hf-test-driven-dev to register the new skill themselves."
    )
