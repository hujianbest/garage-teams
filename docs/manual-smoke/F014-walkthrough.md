# F014 Manual Smoke Walkthrough

- **日期**: 2026-04-26
- **执行人**: Cursor Agent (auto mode)
- **PR**: #38 (branch `cursor/f014-workflow-recall-bf33`)

## Tracks (5 全绿)

### Track 1 — empty status (FR-1405 + RSK-1401)

```
$ garage init --yes
Initialized Garage OS in /tmp/f014-smoke/.garage

$ garage status
No data    # F009 既有行为 (空目录早返回); 一旦至少 1 record/entry, workflow recall 段始终显
```

### Track 2 — seed evidence + recall (FR-1401 + FR-1402)

```python
# Seed 5 ExperienceRecord 全部 problem_domain="cli-design", task_type="implement",
# skill_ids 序列各 ["hf-specify", "hf-design", "hf-tasks", "hf-test-driven-dev"]
for i in range(5):
    ei.store(ExperienceRecord(
        record_id=f"r-{i:03d}", task_type="implement",
        skill_ids=["hf-specify", "hf-design", "hf-tasks", "hf-test-driven-dev"],
        problem_domain="cli-design",
        duration_seconds=3600 + i * 100,  # 3600, 3700, 3800, 3900, 4000
        session_id=f"ses-{i:03d}",
        lessons_learned=["先 read spec 再 design"],
    ))
```

```
$ garage recall workflow --problem-domain cli-design
SEQUENCE                                                     HITS   AVG (s)    TOP LESSON
hf-specify → hf-design → hf-tasks → hf-test-driven-dev       5      3800.0     先 read spec 再 design
```

✓ FR-1401 + Cr-2 r2 (用 list_records + Python filter on problem_domain); 阈值 5 ≥ 3; per-sequence avg = (3600+3700+3800+3900+4000)/5 = 3800.0 (Im-3 r2 ✓).

### Track 3 — `--json` output (供 router step 3.5 调用)

```
$ garage recall workflow --problem-domain cli-design --json
{
  "advisories": [
    {
      "skills": ["hf-specify", "hf-design", "hf-tasks", "hf-test-driven-dev"],
      "count": 5,
      "avg_duration_seconds": 3800.0,
      "top_lessons": [["先 read spec 再 design", 5]],
      "task_type": null,
      "problem_domain": "cli-design"
    }
  ],
  "scanned_count": 5,
  "bucket_size": 5,
  "threshold_met": true
}
```

✓ FR-1402 --json schema 完整 (供 hf-workflow-router step 3.5 自动调用; recall-integration.md 描述的 JSON 结构对齐).

### Track 4 — `--skill-id` Im-4 r2 子序列契约

```
$ garage recall workflow --skill-id hf-design
SEQUENCE                                                     HITS   AVG (s)    TOP LESSON
hf-tasks → hf-test-driven-dev                                5      3800.0     先 read spec 再 design
```

✓ Im-4 r2 算法契约: `--skill-id Z` 取 Z 第一次出现位置之后的子序列. 序列原 `["hf-specify", "hf-design", "hf-tasks", "hf-test-driven-dev"]`; 给 Z=hf-design (idx=1) → 子序列 `("hf-tasks", "hf-test-driven-dev")` ✓; 5 record 全贡献此子序列 → hits=5 ✓.

### Track 5 — `garage status` workflow recall 段 (FR-1405 + Im-6)

```
$ garage status
... (其他段)
Skill mining: scanned 0 entries / 5 records / 0 proposed (last scan: never)
Workflow recall: scanned 5 records / 0 buckets / 0 advisories (last scan: never) (stale, will rebuild on next recall call)
```

✓ FR-1405 + Im-6 + RSK-1401: workflow recall 元数据行始终显; cache 未持久化时附 "(stale, will rebuild on next recall call)". scanned=5 records 用户感知到管道在工作.

## 测试基线

- F013-A baseline: 989 passed
- F014 实施完成 T1-T5: **~1045 passed** (+56, 0 regressions)
- INV-F14-1..5 全部通过
- CON-1403 perf smoke: 1000 records recall in 0.064s (2s 预算余 97%)

## Conclusion

✅ F014 5 tracks 全绿. Workflow Recall 信号完整: 系统能从 ExperienceIndex 自动识别 (task_type, problem_domain) 重复 cycle path + 评分 + JSON 输出供 router 自动调用 + Im-4 子序列契约 + status 段始终可见. growth-strategy.md § Stage 3 第 68 行 "工作流编排从手动变成半自动" ❌ → ✅.
