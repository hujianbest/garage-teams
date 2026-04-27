# Regression Gate — F013-A r1 (Skill Mining Push)

- **日期**: 2026-04-26
- **审阅人**: Cursor Agent (auto-streamlined per F011/F012 mode)

## Verdict: PASS

## 测试基线

| 阶段 | passed | 增量 |
|---|---|---|
| F012 finalize 后 | 930 | baseline |
| F013-A T1 (suggestion_store) | 939 | +9 |
| F013-A T2 (pattern_detector + perf) | 957 | +18 |
| F013-A T3 (template_generator) | 970 | +13 |
| F013-A T4 (pipeline + hook + suggest) | 983 | +13 |
| F013-A T5 (promote + sentinel) | **989** | +6 |

**总增量: +59 测试; 0 regression**

## Sentinel 测试

```
$ pytest tests/sync/test_baseline_no_regression.py -v
PASSED [100%]  (1 passed in 87.76s)
```

## ruff baseline

- F012 完成时: 478 errors
- F013-A T5 完成时: **0 increment** (T1-T5 引入 0 新 ruff 错误)

## 依赖变更

```
$ git diff main..HEAD -- pyproject.toml uv.lock
(empty)
```

**CON-1302 守门: 0 字节依赖变更.**

## Performance gate (CON-1303)

- 单测 100 entries: < 0.5s ✓
- Manual smoke 1000+1000 entries: **0.803s** (5s 预算余 84%) ✓

```
$ uv run python scripts/skill_mining_perf_smoke.py
Seeding 1000 records + 1000 entries (100 distinct buckets)...
  seed elapsed: 8.86s
Running detect_and_write...
  detect elapsed: 0.803s
  suggestions written: 100

✓ PASS: Pattern detection completed within CON-1303 5s budget
```

## 文件清单

### 新增 (5 src + 5 test + 2 docs + 1 script)
- `src/garage_os/skill_mining/{__init__,types,suggestion_store,pattern_detector,template_generator,pipeline}.py` (5 模块, 6 文件)
- `tests/skill_mining/{__init__,test_suggestion_store,test_pattern_detector,test_pattern_detector_perf_100_entries,test_template_generator,test_pipeline,test_promote_no_pack_json_mutation}.py` (7 文件)
- `scripts/skill_mining_perf_smoke.py`
- `docs/manual-smoke/F013-A-walkthrough.md`
- 6 个 review/approval/spec/design/tasks 文档

### 修改 (3 src + 1 test + 2 docs)
- `src/garage_os/cli.py` (+280 LOC; skill subparser + 2 handler + status section)
- `src/garage_os/runtime/session_manager.py` (+12 LOC; Cr-1 Path 1 hook)
- `src/garage_os/ingest/pipeline.py` (+13 LOC; Cr-1 Path 2 hook)
- `tests/test_cli.py` (+~250 LOC; 2 CLI test classes)
- `AGENTS.md` (+60 LOC; Skill Mining Push section)
- `RELEASE_NOTES.md` (+85 LOC; F013-A cycle entry)

## Manual Smoke Walkthrough

`docs/manual-smoke/F013-A-walkthrough.md` — 5 tracks 全绿:
- Track 1: empty status (No data)
- Track 2: seed evidence + `--rescan` → 1 proposal
- Track 3: list + `--id detail` + SKILL.md 6 章节 preview
- Track 4: `garage status` 显 metadata + 💡 行
- Track 5: promote → SKILL.md 创建; pack.json byte 不变 (CON-1304 ✓)

## 通过条件

✅ regression gate PASS, 进入 completion gate.
