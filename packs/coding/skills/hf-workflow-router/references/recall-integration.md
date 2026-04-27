# F014 Workflow Recall Integration (router step 3.5 reference)

This reference describes how `hf-workflow-router` step 3.5 consumes the F014 `garage recall workflow --json` output and emits an optional `Historical advisory` block in the handoff.

## When to call

Step 3.5 calls `garage recall workflow` only if **all** of the following hold:

1. `.garage/experience/records/` exists and is non-empty (skip on empty repo / first-time use)
2. User did not say "ignore history" / "fresh start" / equivalent
3. `platform.json workflow_recall.enabled` is not explicitly `false`

Otherwise the step is a no-op (continues straight to step 4 Profile decision).

## Call format

The router invokes (or instructs the agent to invoke) the CLI with `--json`:

```
garage recall workflow [--task-type <X>] [--problem-domain <Y>] [--top-k 3] --json
```

At least one filter MUST be provided. When the cycle's task type is uncertain, prefer `--problem-domain` (typically more stable across cycle types).

## JSON schema

`--json` produces:

```json
{
  "advisories": [
    {
      "skills": ["hf-specify", "hf-design", "hf-tasks", "hf-test-driven-dev"],
      "count": 5,
      "avg_duration_seconds": 3580.0,
      "top_lessons": [["先 read spec 再 design", 5], ["perf 单测优先", 3]],
      "task_type": "implement",
      "problem_domain": "cli-design"
    }
  ],
  "scanned_count": 15,
  "bucket_size": 5,
  "threshold_met": true
}
```

Field semantics:

- `advisories[]`: top-K sequences sorted by `count` desc; empty when `threshold_met=false` or all sequences filtered out (e.g. `--skill-id` is the last item)
- `scanned_count`: total ExperienceRecord scanned across all buckets
- `bucket_size`: records in the matched (task_type, problem_domain) bucket before threshold
- `threshold_met`: bucket_size >= threshold (default 3)
- `avg_duration_seconds`: per-sequence mean (NOT bucket-wide; only records matching that advisory's `skills` sequence)
- `top_lessons`: list of `(lesson, freq)` tuples, top 3, also per-sequence

## Advisory block format (handoff)

When `threshold_met=true` AND `len(advisories) > 0`, the router emits this block in the handoff:

```
Historical advisory: based on <count> similar cycles, the typical path is
<seq[0]> → <seq[1]> → ... → <seq[N-1]> (avg <avg_duration_seconds>s).
Top lessons: <lesson-1> (<freq>x); <lesson-2> (<freq>x).
advisory only — 用户可改
```

The trailing `advisory only — 用户可改` line is mandatory (INV-F14-3): it signals the receiving leaf skill that this is non-authoritative input.

## When to omit

The advisory block is omitted entirely (no placeholder / no "no history" line) when:

- `threshold_met=false` (bucket too small)
- `advisories[]` is empty after sequence filtering (e.g. `--skill-id Z` where Z is always the last item)
- `garage recall workflow` exits non-zero (CLI / cache error)
- platform.json `workflow_recall.enabled=false`

This is consistent with F009 and F010 patterns (silent skip when subsystem has no signal to emit).

## Relationship with step 4 (Profile decision)

The advisory does NOT change Profile selection logic. step 4 still follows:

1. `AGENTS.md` mandatory rules
2. Sustain existing profile
3. Pick by evidence
4. Conflicts → escalate (only upgrade, never downgrade)

The advisory may **inform** the human's mental model ("oh, last time this took 1 hour, this time we should expect similar"), but the `Workflow Profile` cell in the handoff is determined by step 4 logic alone, not by the advisory.

## Failure modes

- `garage recall workflow` not on PATH → step 3.5 logs a one-line warning and continues (best-effort)
- ExperienceIndex empty / first-time use → step 3.5 noops without warning (expected)
- Cache stale → CLI auto-rebuilds on demand (transparent to router)
- User-set `workflow_recall.enabled=false` → step 3.5 noops (CLI returns empty advisories)

## See also

- F014 spec: `docs/features/F014-workflow-recall.md`
- F014 design: `docs/designs/2026-04-26-workflow-recall-design.md`
- ExperienceRecord schema: `src/garage_os/types/__init__.py:124-147`
- PathRecaller algorithm: `src/garage_os/workflow_recall/path_recaller.py`
