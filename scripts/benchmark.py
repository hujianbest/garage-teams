#!/usr/bin/env python3
"""T18 Performance Benchmark Script for Garage Agent OS.

Measures:
1. Session create/restore latency (100 iterations, mean/p50/p90)
2. Knowledge query performance (100 queries after 100/500/1000 entries, p90)
3. Degradation check (100→1000 entries p90 growth ≤ 50%)

Results saved to .garage/benchmark/baseline-YYYYMMDD.json

Usage:
    uv run python scripts/benchmark.py
"""

import json
import os
import shutil
import statistics
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

# Ensure project root is on sys.path so garage_os is importable
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from garage_os.storage import FileStorage
from garage_os.runtime.session_manager import SessionManager
from garage_os.knowledge.knowledge_store import KnowledgeStore
from garage_os.types import KnowledgeType, KnowledgeEntry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _percentile(sorted_data: list[float], pct: float) -> float:
    """Return the *pct*-th percentile (0-100) from already-sorted data."""
    if not sorted_data:
        return 0.0
    idx = (pct / 100.0) * (len(sorted_data) - 1)
    lo = int(idx)
    hi = min(lo + 1, len(sorted_data) - 1)
    frac = idx - lo
    return sorted_data[lo] + frac * (sorted_data[hi] - sorted_data[lo])


def _stats(times: list[float]) -> dict:
    """Return mean / p50 / p90 / max for a list of durations in seconds."""
    s = sorted(times)
    return {
        "mean": round(statistics.mean(s), 6),
        "p50": round(_percentile(s, 50), 6),
        "p90": round(_percentile(s, 90), 6),
        "max": round(max(s), 6),
        "iterations": len(s),
    }


def _make_knowledge_entry(idx: int, ktype: KnowledgeType = KnowledgeType.SOLUTION) -> KnowledgeEntry:
    """Create a synthetic knowledge entry for benchmarking."""
    return KnowledgeEntry(
        id=f"bench-{idx:05d}",
        type=ktype,
        topic=f"Benchmark topic {idx} – performance testing entry",
        date=datetime.now(),
        tags=[f"bench", f"tag-{idx % 20}", f"category-{idx % 5}"],
        content=(
            f"Benchmark content for entry {idx}. "
            "This is synthetic data used to measure knowledge store query performance. "
            f"Entry number {idx} of the benchmark dataset. "
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
            "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
        ),
        status="active",
        version=1,
    )


# ---------------------------------------------------------------------------
# Benchmark 1: Session create / restore
# ---------------------------------------------------------------------------

def bench_session_create_restore(tmp_dir: Path, iterations: int = 100) -> dict:
    """Benchmark SessionManager.create_session and restore_session."""
    storage = FileStorage(tmp_dir)
    mgr = SessionManager(storage)

    created_ids: list[str] = []
    create_times: list[float] = []

    # --- create ---
    for i in range(iterations):
        t0 = time.perf_counter()
        meta = mgr.create_session(
            pack_id="bench-pack",
            topic=f"benchmark session {i}",
            user_goals=[f"goal-{i}"],
            constraints=[f"constraint-{i}"],
        )
        t1 = time.perf_counter()
        create_times.append(t1 - t0)
        created_ids.append(meta.session_id)

    # --- restore ---
    restore_times: list[float] = []
    for sid in created_ids:
        t0 = time.perf_counter()
        result = mgr.restore_session(sid)
        t1 = time.perf_counter()
        if result is None:
            print(f"  WARNING: could not restore session {sid}", file=sys.stderr)
        restore_times.append(t1 - t0)

    return {
        "create": _stats(create_times),
        "restore": _stats(restore_times),
    }


# ---------------------------------------------------------------------------
# Benchmark 2: Knowledge query at different scales
# ---------------------------------------------------------------------------

def bench_knowledge_queries(tmp_dir: Path, scales: tuple[int, ...] = (100, 500, 1000),
                            queries_per_scale: int = 100) -> dict:
    """Benchmark KnowledgeStore.search at different data volumes."""
    storage = FileStorage(tmp_dir)
    ks = KnowledgeStore(storage)

    results: dict[str, dict] = {}
    all_inserted_ids: list[str] = []

    for scale in scales:
        # Determine how many new entries to insert to reach `scale`
        already = len(all_inserted_ids)
        to_insert = scale - already
        for idx in range(already, scale):
            entry = _make_knowledge_entry(idx)
            ks.store(entry)
            all_inserted_ids.append(entry.id)

        # Build a pool of queries — some hit, some miss
        query_terms = [
            f"topic {all_inserted_ids[i % len(all_inserted_ids)].split('-')[1]}"  # partial hit
            for i in range(queries_per_scale)
        ]
        # mix in some generic searches
        for i in range(queries_per_scale // 2):
            query_terms.append(f"category-{i % 5}")
        # trim to exact count
        query_terms = query_terms[:queries_per_scale]

        query_times: list[float] = []
        for q in query_terms:
            t0 = time.perf_counter()
            ks.search(query=q)
            t1 = time.perf_counter()
            query_times.append(t1 - t0)

        stat = _stats(query_times)
        results[f"entries_{scale}"] = stat

    return results


# ---------------------------------------------------------------------------
# Benchmark 3: Degradation check
# ---------------------------------------------------------------------------

def check_degradation(knowledge_results: dict) -> dict:
    """Verify that p90 query time grows ≤ 50 % from 100 → 1000 entries."""
    p90_100 = knowledge_results.get("entries_100", {}).get("p90", 0)
    p90_1000 = knowledge_results.get("entries_1000", {}).get("p90", 0)

    growth_pct = ((p90_1000 - p90_100) / p90_100 * 100) if p90_100 > 0 else 0.0
    passed = growth_pct <= 50.0

    return {
        "p90_at_100": p90_100,
        "p90_at_1000": p90_1000,
        "growth_percent": round(growth_pct, 2),
        "threshold_percent": 50.0,
        "passed": passed,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    today_str = datetime.now().strftime("%Y%m%d")
    print(f"=== Garage Agent OS – T18 Performance Benchmark ({today_str}) ===\n")

    # Use a temp directory so benchmarks don't pollute the real .garage
    tmp_dir = tempfile.mkdtemp(prefix="garage_bench_")
    tmp_path = Path(tmp_dir)
    try:
        # 1. Session create / restore
        print("1. Session create / restore (100 iterations) ...")
        session_results = bench_session_create_restore(tmp_path / "session_bench")
        print(f"   create  → mean={session_results['create']['mean']*1000:.2f}ms  "
              f"p50={session_results['create']['p50']*1000:.2f}ms  "
              f"p90={session_results['create']['p90']*1000:.2f}ms")
        print(f"   restore → mean={session_results['restore']['mean']*1000:.2f}ms  "
              f"p50={session_results['restore']['p50']*1000:.2f}ms  "
              f"p90={session_results['restore']['p90']*1000:.2f}ms")
        print()

        # 2. Knowledge queries at scale (use separate dir for clean state)
        print("2. Knowledge query performance ...")
        knowledge_results = bench_knowledge_queries(tmp_path / "knowledge_bench")
        for key, stat in knowledge_results.items():
            print(f"   {key:15s} → p90={stat['p90']*1000:.2f}ms  mean={stat['mean']*1000:.2f}ms")
        print()

        # 3. Degradation check
        print("3. Degradation check (100 → 1000 entries, p90 growth ≤ 50%) ...")
        degradation = check_degradation(knowledge_results)
        status = "PASS ✓" if degradation["passed"] else "FAIL ✗"
        print(f"   p90@100={degradation['p90_at_100']*1000:.2f}ms  "
              f"p90@1000={degradation['p90_at_1000']*1000:.2f}ms  "
              f"growth={degradation['growth_percent']:.1f}%  → {status}")
        print()

    finally:
        # Clean up temp files
        shutil.rmtree(tmp_path, ignore_errors=True)

    # 4. Save results
    output = {
        "timestamp": datetime.now().isoformat(),
        "benchmark": "T18-performance-baseline",
        "session_create_restore": session_results,
        "knowledge_queries": knowledge_results,
        "degradation_check": degradation,
    }

    bench_dir = _PROJECT_ROOT / ".garage" / "benchmark"
    bench_dir.mkdir(parents=True, exist_ok=True)
    out_path = bench_dir / f"baseline-{today_str}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"4. Results saved → {out_path}")
    print(f"\n{'='*60}")
    print(f"Session create p90 : {session_results['create']['p90']*1000:.2f} ms")
    print(f"Session restore p90: {session_results['restore']['p90']*1000:.2f} ms")
    print(f"Knowledge query p90 @1000 entries: {knowledge_results.get('entries_1000',{}).get('p90',0)*1000:.2f} ms")
    print(f"Degradation check : {status}")
    print(f"{'='*60}")

    # Exit with non-zero if degradation check failed
    if not degradation["passed"]:
        print("\n⚠ Degradation threshold exceeded!", file=sys.stderr)
        sys.exit(1)

    print("\n✓ All benchmarks passed.")


if __name__ == "__main__":
    main()
