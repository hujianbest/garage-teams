"""F014 T2 / CON-1403: pattern_detector performance unit gate.

100 records spread across 10 buckets must complete recall in < 0.2s on
local CI. Extrapolates to 1000 records < 2s (CON-1403); the canonical
1000-record verification is ``scripts/workflow_recall_perf_smoke.py``.
"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

from garage_os.knowledge.experience_index import ExperienceIndex
from garage_os.storage.file_storage import FileStorage
from garage_os.types import ExperienceRecord
from garage_os.workflow_recall.path_recaller import recall


def test_path_recaller_perf_100_records(tmp_path: Path) -> None:
    ei = ExperienceIndex(FileStorage(tmp_path / ".garage"))

    for i in range(100):
        ei.store(ExperienceRecord(
            record_id=f"r-{i:03d}",
            task_type="task",
            skill_ids=["a", "b", "c"],
            tech_stack=[],
            domain="d",
            problem_domain=f"domain-{i % 10}",
            outcome="success",
            duration_seconds=60,
            complexity="low",
            session_id=f"ses-{i:03d}",
            key_patterns=[],
            created_at=datetime(2026, 4, 26),
        ))

    # Time a single recall over the full 100-record store
    start = time.perf_counter()
    result = recall(ei, problem_domain="domain-3")
    elapsed = time.perf_counter() - start

    assert result.bucket_size == 10
    assert result.threshold_met is True
    assert elapsed < 0.2, f"PathRecaller took {elapsed:.3f}s on 100 records (budget 0.2s)"
