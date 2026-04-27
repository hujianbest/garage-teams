#!/usr/bin/env python3
"""F014 T2 + T5 finalize gate: 1000-record path_recaller perf prof.

Run via: ``uv run python scripts/workflow_recall_perf_smoke.py``

CON-1403 budget: < 2s on local SSD. If exceeded, ADR-D14-3 fallback is
``platform.json workflow_recall.enabled: false`` config gate so users can
opt out of the multi-caller invalidate hooks and rely on manual
``garage recall workflow --rebuild-cache``.
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
from garage_os.storage.file_storage import FileStorage  # noqa: E402
from garage_os.types import ExperienceRecord  # noqa: E402
from garage_os.workflow_recall.path_recaller import recall  # noqa: E402


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        garage_dir = tmp_path / ".garage"
        ei = ExperienceIndex(FileStorage(garage_dir))

        print("Seeding 1000 records (100 distinct (task_type, problem_domain) buckets)...")
        seed_start = time.perf_counter()
        for i in range(1000):
            ei.store(ExperienceRecord(
                record_id=f"r-{i:04d}",
                task_type=f"task-{i % 10}",
                skill_ids=["hf-specify", "hf-design", "hf-tasks", "hf-test-driven-dev"],
                tech_stack=[],
                domain="d",
                problem_domain=f"domain-{i % 10}",
                outcome="success",
                duration_seconds=3600,
                complexity="low",
                session_id=f"ses-{i:04d}",
                key_patterns=[],
                created_at=datetime(2026, 4, 26),
            ))
        seed_elapsed = time.perf_counter() - seed_start
        print(f"  seed elapsed: {seed_elapsed:.2f}s")

        print("Running recall(problem_domain='domain-5')...")
        start = time.perf_counter()
        result = recall(ei, problem_domain="domain-5")
        elapsed = time.perf_counter() - start

        print(f"  recall elapsed: {elapsed:.3f}s")
        print(f"  bucket_size: {result.bucket_size}")
        print(f"  advisories: {len(result.advisories)}")

        if elapsed < 2.0:
            print("\n✓ PASS: PathRecaller completed within CON-1403 2s budget")
            return 0
        else:
            print(f"\n✗ FAIL: PathRecaller took {elapsed:.3f}s (budget 2s)")
            print("  → ADR-D14-3 fallback: implement platform.json")
            print("    `workflow_recall.enabled: false` config gate so users")
            print("    can disable invalidate hooks + rely on manual --rebuild-cache")
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
