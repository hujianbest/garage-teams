# Regression Gate — F014 r1 (Workflow Recall)

- **日期**: 2026-04-26
- **审阅人**: Cursor Agent (auto-streamlined per F011/F012/F013-A mode)

## Verdict: PASS

## 测试基线

| 阶段 | passed | 增量 |
|---|---|---|
| F013-A finalize 后 | 989 | baseline |
| F014 T1 (cache foundation) | 1003 | +14 |
| F014 T2 (path_recaller + perf) | 1024 | +21 |
| F014 T3 (pipeline + 4 caller hook + status) | 1032 | +8 |
| F014 T4 (CLI recall workflow) | 1040 | +8 |
| F014 T5 (router SKILL.md + dogfood SHA + sentinel) | **1043** | +3 |

**总增量: +54 测试; 0 regression**

## Sentinel 测试

```
$ pytest tests/sync/test_baseline_no_regression.py -v
PASSED [100%]  (1 passed in 79.94s)
```

## ruff baseline

- F013-A 完成时: 0 increment from F012's 478 baseline
- F014 T5 完成时: **0 increment** (T1-T5 引入 0 新 ruff 错误)

## 依赖变更

```
$ git diff main..HEAD -- pyproject.toml uv.lock
(empty)
```

**CON-1402 守门: 0 字节依赖变更.**

## Performance gate (CON-1403)

- 单测 100 records: < 0.2s ✓
- Manual smoke 1000 records: **0.064s** (2s 预算余 97%) ✓

```
$ uv run python scripts/workflow_recall_perf_smoke.py
Seeding 1000 records (100 distinct (task_type, problem_domain) buckets)...
Running recall(problem_domain='domain-5')...
  recall elapsed: 0.064s
  bucket_size: 100
  advisories: 1

✓ PASS: PathRecaller completed within CON-1403 2s budget
```

## Dogfood SHA gate (CON-1404 + INV-F14-5)

```
$ pytest tests/adapter/installer/test_dogfood_invariance_F009.py -v
PASSED  test_baseline_json_exists_and_loadable
PASSED  test_dogfood_skill_md_sha256_match  ← baseline 已更 2 keys (router .cursor/ + .claude/)

$ pytest tests/adapter/installer/test_neutrality_exemption_list.py -v
PASSED (3 tests)
```

## 文件清单

### 新增 (4 src + 5 test + 1 script + 5 docs)
- `src/garage_os/workflow_recall/{__init__,types,cache,path_recaller,pipeline}.py` (5 文件)
- `tests/workflow_recall/{__init__,test_cache,test_path_recaller,test_path_recaller_perf_100_records,test_pipeline,test_recall_no_recommend_import}.py` (6 文件)
- `scripts/workflow_recall_perf_smoke.py`
- `packs/coding/skills/hf-workflow-router/references/recall-integration.md`
- `docs/manual-smoke/F014-walkthrough.md`
- 6 个 review/approval/spec/design/tasks 文档

### 修改 (5 src + 1 test + 2 docs + 1 baseline)
- `src/garage_os/cli.py` (+160 LOC; recall subparser + handler + status 段)
- `src/garage_os/runtime/session_manager.py` (+9 LOC; Cr-1 Path 1 hook)
- `src/garage_os/memory/publisher.py` (+7 LOC; Im-1 r2 hook)
- `src/garage_os/knowledge/integration.py` (+7 LOC; Path 4 hook)
- `tests/test_cli.py` (+~250 LOC; 1 CLI test class)
- `tests/test_documentation.py` (+18 LOC; 1 sentinel)
- `tests/adapter/installer/test_dogfood_layout.py` (+8 LOC; 1 sentinel)
- `packs/coding/skills/hf-workflow-router/SKILL.md` (+37 LOC; additive step 3.5)
- `tests/adapter/installer/dogfood_baseline/skill_md_sha256.json` (2 hash 更新)
- `AGENTS.md` (+50 LOC; Workflow Recall (F014) section)
- `RELEASE_NOTES.md` (+85 LOC; F014 cycle entry)

## Manual Smoke Walkthrough

`docs/manual-smoke/F014-walkthrough.md` — 5 tracks 全绿:
- Track 1: empty status (No data)
- Track 2: seed evidence + recall → 1 advisory (5 hits, avg 3800s)
- Track 3: --json output schema 完整
- Track 4: --skill-id Im-4 r2 子序列契约 (hf-design 后取 hf-tasks → hf-test-driven-dev)
- Track 5: garage status 显 workflow recall 段 (RSK-1401: scanned 5 records 始终显)

## 通过条件

✅ regression gate PASS, 进入 completion gate.
