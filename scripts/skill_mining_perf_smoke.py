#!/usr/bin/env python3
"""F013-A T2 + T4 finalize gate: 1000+1000 entry pattern_detector perf prof.

Run via: ``uv run python scripts/skill_mining_perf_smoke.py``

CON-1303 budget: < 5s on local SSD. If exceeded, the F013-A design (ADR-D13-3
Im-4 fallback) instructs the implementer to add ``platform.json
skill_mining.hook_enabled: false`` config gate so users can opt-out of the
sync hook and rely on manual ``garage skill suggest --rescan``.
"""

from __future__ import annotations

import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from garage_os.knowledge.experience_index import ExperienceIndex  # noqa: E402
from garage_os.knowledge.knowledge_store import KnowledgeStore  # noqa: E402
from garage_os.skill_mining.pattern_detector import detect_and_write  # noqa: E402
from garage_os.skill_mining.suggestion_store import SuggestionStore  # noqa: E402
from garage_os.storage.file_storage import FileStorage  # noqa: E402
from garage_os.types import (  # noqa: E402
    ExperienceRecord,
    KnowledgeEntry,
    KnowledgeType,
)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        garage_dir = tmp_path / ".garage"
        storage = FileStorage(garage_dir)
        ks = KnowledgeStore(storage)
        ei = ExperienceIndex(storage)
        ss = SuggestionStore(garage_dir)
        packs_root = tmp_path / "packs"

        print("Seeding 1000 records + 1000 entries (100 distinct buckets)...")
        seed_start = time.perf_counter()
        for i in range(1000):
            ei.store(ExperienceRecord(
                record_id=f"r-{i:04d}",
                task_type="task",
                skill_ids=[],
                tech_stack=[],
                domain="d",
                problem_domain=f"domain-{i % 100}",
                outcome="success",
                duration_seconds=60,
                complexity="low",
                session_id=f"ses-r-{i:04d}",
                key_patterns=[f"tag-{i % 100}-a", f"tag-{i % 100}-b"],
                created_at=datetime(2026, 4, 26),
            ))
        for i in range(1000):
            ks.store(KnowledgeEntry(
                id=f"e-{i:04d}",
                type=KnowledgeType.DECISION,
                topic=f"domain-{i % 100} entry {i}",
                date=datetime(2026, 4, 26),
                tags=[f"tag-{i % 100}-a", f"tag-{i % 100}-b"],
                content="...",
                source_session=f"ses-e-{i:04d}",
                front_matter={"problem_domain": f"domain-{i % 100}"},
            ))
        seed_elapsed = time.perf_counter() - seed_start
        print(f"  seed elapsed: {seed_elapsed:.2f}s")

        print("Running detect_and_write...")
        start = time.perf_counter()
        new = detect_and_write(ks, ei, ss, packs_root, threshold=5)
        elapsed = time.perf_counter() - start

        print(f"  detect elapsed: {elapsed:.3f}s")
        print(f"  suggestions written: {len(new)}")

        if elapsed < 5.0:
            print("\n✓ PASS: Pattern detection completed within CON-1303 5s budget")
            return 0
        else:
            print(f"\n✗ FAIL: Pattern detection took {elapsed:.3f}s (budget 5s)")
            print("  → ADR-D13-3 Im-4 fallback: implement platform.json")
            print("    `skill_mining.hook_enabled: false` config gate so users")
            print("    can disable sync hook + rely on manual `garage skill suggest --rescan`")
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
