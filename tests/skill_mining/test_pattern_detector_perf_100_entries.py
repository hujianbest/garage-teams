"""F013-A T2.13 / CON-1303: pattern_detector performance unit gate.

100 entries (50 records + 50 entries) must cluster + score in < 0.5 seconds
on local CI. Extrapolates to 1000+1000 < 5s (CON-1303 budget); the canonical
1000+1000 verification is ``scripts/skill_mining_perf_smoke.py`` (manual prof).
"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

import pytest

from garage_os.knowledge.experience_index import ExperienceIndex
from garage_os.knowledge.knowledge_store import KnowledgeStore
from garage_os.skill_mining.pattern_detector import detect_and_write
from garage_os.skill_mining.suggestion_store import SuggestionStore
from garage_os.storage.file_storage import FileStorage
from garage_os.types import ExperienceRecord, KnowledgeEntry, KnowledgeType


def test_pattern_detector_perf_100_entries(tmp_path: Path) -> None:
    garage_dir = tmp_path / ".garage"
    storage = FileStorage(garage_dir)
    ks = KnowledgeStore(storage)
    ei = ExperienceIndex(storage)
    ss = SuggestionStore(garage_dir)
    packs_root = tmp_path / "packs"

    # 50 records + 50 entries spread across 10 (domain, tag-bucket) buckets
    for i in range(50):
        ei.store(ExperienceRecord(
            record_id=f"r-{i:03d}",
            task_type="task",
            skill_ids=[],
            tech_stack=[],
            domain="d",
            problem_domain=f"domain-{i % 10}",
            outcome="success",
            duration_seconds=60,
            complexity="low",
            session_id=f"ses-{i:03d}",
            key_patterns=[f"tag-{i % 10}-a", f"tag-{i % 10}-b"],
            created_at=datetime(2026, 4, 26),
        ))
    for i in range(50):
        ks.store(KnowledgeEntry(
            id=f"e-{i:03d}",
            type=KnowledgeType.DECISION,
            topic=f"domain-{i % 10} entry {i}",
            date=datetime(2026, 4, 26),
            tags=[f"tag-{i % 10}-a", f"tag-{i % 10}-b"],
            content="...",
            source_session=f"ses-e-{i:03d}",
            front_matter={"problem_domain": f"domain-{i % 10}"},
        ))

    start = time.perf_counter()
    new = detect_and_write(ks, ei, ss, packs_root, threshold=5)
    elapsed = time.perf_counter() - start

    # Each of 10 buckets has 10 sessions (5 records + 5 entries) → all qualify
    assert len(new) == 10
    assert elapsed < 0.5, f"Pattern detection took {elapsed:.3f}s (budget 0.5s for 100 items)"
