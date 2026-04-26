# F014 Tasks — Workflow Recall 实施分块

- **状态**: 草稿 r1 (auto-streamlined per F011/F012/F013-A mode)
- **关联 spec**: `docs/features/F014-workflow-recall.md` r2 APPROVED
- **关联 design**: `docs/designs/2026-04-26-workflow-recall-design.md` r2 APPROVED (ADR-D14-7 任务表为本计划唯一来源)
- **日期**: 2026-04-26

## 0. 总览

| 任务 | 提交主题 | 测试增量 | 依赖 | FR / INV / CON 覆盖 |
|---|---|---|---|---|
| **T1** | `workflow_recall/{__init__, types, cache}` + 8 测试 | 8 | 无 | INV-F14-2 + CON-1402 |
| **T2** | `workflow_recall/path_recaller.py` + 12 测试 + 1 perf 单测 + scripts/workflow_recall_perf_smoke.py | 13 | T1 | FR-1401 + INV-F14-1 + CON-1403 |
| **T3** | `workflow_recall/pipeline.py` + 4 caller 接入 (Cr-1+Cr-2+Im-1 r2 修订: cli.py / publisher.py 顶层 / integration.py / session_manager.py) + `garage status` 段 + 6 测试 | 6 | T1+T2 | FR-1404 + FR-1405 + CON-1401 |
| **T4** | CLI `garage recall workflow` (含 --task-type / --problem-domain / --skill-id Im-4 子序列 / --top-k / --json / --rebuild-cache) + 8 测试 | 8 | T1-T3 | FR-1402 + CON-1405 |
| **T5** | hf-workflow-router/SKILL.md step 3.5 + references/recall-integration.md + dogfood SHA baseline (2 keys) 同步 + AGENTS / RELEASE_NOTES + manual smoke + 5 测试 | 5 | T1-T4 | FR-1403 + INV-F14-3/5 + CON-1404 |

**总测试增量**: ~40 (基线 main `f5950b4` 989 → 预计 1029)

## 1. T1 — `workflow_recall` foundation

### 交付

- `src/garage_os/workflow_recall/__init__.py`
- `src/garage_os/workflow_recall/types.py` — `RecallResult` + `WorkflowAdvisory` dataclass
- `src/garage_os/workflow_recall/cache.py` — `cache.json` + `last-indexed.json` CRUD + atomic write
- `tests/workflow_recall/__init__.py` + `tests/workflow_recall/test_cache.py` (8 用例)

### 测试 (8)

1. `test_cache_load_returns_none_when_missing`
2. `test_cache_write_atomic` (mock os.replace 失败 → 部分文件不可见)
3. `test_cache_round_trip`
4. `test_invalidate_deletes_last_indexed`
5. `test_load_returns_stale_when_last_indexed_missing`
6. `test_cache_key_format` (`{tt}|{pd}` with `*` for None)
7. `test_lazy_mkdir_on_first_write`
8. `test_load_corrupted_json_returns_empty_with_warning`

### Definition of Done

- 8/8 测试过
- ruff diff = 0
- `uv run pytest tests/workflow_recall/test_cache.py -q` PASS

## 2. T2 — Path Recaller

### 交付

- `src/garage_os/workflow_recall/path_recaller.py` — Counter 算法 + 阈值 3 + window 10 + Im-4 `--skill-id` 子序列
- `tests/workflow_recall/test_path_recaller.py` (12 用例)
- `tests/workflow_recall/test_path_recaller_perf_100_records.py` (1 用例)
- `scripts/workflow_recall_perf_smoke.py` (手工 1000 record < 2s)

### 测试 (12 + 1 perf)

1. `test_recall_below_threshold_returns_empty`
2. `test_recall_at_threshold_returns_advisory`
3. `test_recall_groups_by_task_type_and_problem_domain`
4. `test_recall_top_k_default_3`
5. `test_recall_window_default_10` (按 created_at desc 取 10)
6. `test_recall_skill_id_subsequence_after_first_occurrence` (Im-4)
7. `test_recall_skill_id_at_last_position_skipped`
8. `test_recall_skill_id_not_in_record_skipped`
9. `test_recall_avg_duration_per_sequence` (Im-3 r2: 不是桶级)
10. `test_recall_top_lessons_per_sequence`
11. `test_recall_read_only_on_experience_index` (sentinel: list_records 前后字节相等)
12. `test_recall_empty_filter_raises`
13. (perf) `test_path_recaller_perf_100_records` < 0.2s

### Definition of Done

- 13/13 测试过
- `uv run python scripts/workflow_recall_perf_smoke.py` 输出 1000 record < 2s
- ruff diff = 0

## 3. T3 — Pipeline + WorkflowRecallHook + `garage status` 集成

### 交付

- `src/garage_os/workflow_recall/pipeline.py` — `WorkflowRecallHook.invalidate(garage_dir)` + `compute_status_summary(garage_dir)`
- 修改 `src/garage_os/runtime/session_manager.py` `_trigger_memory_extraction` 末尾 (在 F013-A SkillMiningHook 之后) try/except invoke
- 修改 `src/garage_os/cli.py` `_experience_add` (~ L1741 后) try/except invoke
- 修改 `src/garage_os/memory/publisher.py` if-else 末尾 (~ L143 后) try/except invoke (Im-1 r2 修订: 覆盖 store + update 两路径)
- 修改 `src/garage_os/knowledge/integration.py` (~ L222 后) try/except invoke
- 修改 `src/garage_os/cli.py` `_status` 末尾在 `_print_skill_mining_status` 后加 `_print_workflow_recall_status`
- 加 `platform.json` schema: `workflow_recall.enabled: bool` (默认 true)
- `tests/workflow_recall/test_pipeline.py` (6 用例)

### 测试 (6)

1. `test_invalidate_deletes_last_indexed`
2. `test_invalidate_idempotent` (再调用一次不报错)
3. `test_invalidate_failure_does_not_block_caller` (mock IOError → log + return None)
4. `test_compute_status_summary_with_zero_records`
5. `test_compute_status_summary_with_advisories`
6. `test_config_gate_workflow_recall_enabled_false` (platform.json `workflow_recall.enabled=false` → status 段显 "(disabled)")

### Definition of Done

- 6/6 测试过
- 4 caller 接入处全 try/except (CON-1401)
- ruff diff = 0

## 4. T4 — CLI `garage recall workflow`

### 交付

- 修改 `src/garage_os/cli.py` 加 `recall` subparser + `workflow` 子子命令 + handler `_recall_workflow`
- 含 flags: `--task-type` / `--problem-domain` / `--skill-id` / `--top-k` / `--json` / `--rebuild-cache`
- 与 F006 `recommend` subparser **完全独立** (CON-1405): `recall` 是新 top-level subcommand, 不嵌入 `recommend`
- `tests/test_cli.py::TestRecallWorkflowCommand` (8 用例)

### 测试 (8)

1. `test_recall_workflow_no_filter_errors`
2. `test_recall_workflow_problem_domain_filter`
3. `test_recall_workflow_task_type_filter`
4. `test_recall_workflow_skill_id_filter` (Im-4 子序列)
5. `test_recall_workflow_top_k_override`
6. `test_recall_workflow_json_output_schema`
7. `test_recall_workflow_below_threshold_friendly_msg`
8. `test_recall_workflow_rebuild_cache_flag`

### Definition of Done

- 8/8 测试过
- `recall` handler 不 import recommend 模块 (CON-1405 sentinel)
- ruff diff = 0

## 5. T5 — hf-workflow-router 集成 + dogfood SHA + docs + smoke

### 交付

- 修改 `packs/coding/skills/hf-workflow-router/SKILL.md`: 在 step 3 (支线信号) 与 step 4 (Profile) 之间加 step 3.5 (additive)
- 新增 `packs/coding/skills/hf-workflow-router/references/recall-integration.md` (描述 advisory 块格式 + JSON schema)
- 跑 `garage init --hosts cursor,claude --yes` 重生 `.cursor/` + `.claude/` mirror
- 计算 2 个 hf-workflow-router mirror 的 SHA-256, 更新 `tests/adapter/installer/dogfood_baseline/skill_md_sha256.json` 中 2 个 keys (Im-2 r2 修订)
- 修改 `AGENTS.md` 加 "Workflow Recall (F014)" 段
- 修改 `RELEASE_NOTES.md` 加 F014 cycle entry
- 写 `docs/manual-smoke/F014-walkthrough.md` (4 tracks)
- `tests/workflow_recall/test_recall_no_recommend_import.py` (CON-1405 sentinel)
- `tests/test_dogfood_layout.py` 加 1 sentinel (workflow_recall 模块结构)
- `tests/test_documentation.py` 加 1 sentinel (README/AGENTS 含 `recall workflow`)
- 1 个 smoke walkthrough 验证测试 (manual_smoke walkthrough 文件存在)

### 测试 (5)

1. `test_recall_no_recommend_import` (CON-1405)
2. `test_dogfood_workflow_recall_module_exists`
3. `test_readmes_mention_recall_workflow`
4. `test_dogfood_invariance_F009 still passes after baseline update` (sentinel; 隐含, 由全套测试守)
5. `test_neutrality_exemption_list still passes` (sentinel; 隐含)

### Manual smoke (T5)

`docs/manual-smoke/F014-walkthrough.md` 4 tracks:
- Track 1: 0 record → "No workflow advisory yet (3 records minimum; current N for bucket: 0)"
- Track 2: seed 5 record → `recall workflow --problem-domain X` 1 advisory + status 段显
- Track 3: cache invalidation (write 第 6 条 record via `garage experience add` → cache stale → recall 重算)
- Track 4: --skill-id Im-4 子序列 (Z 在序列中 → 取后续; Z 是序列最后 → 跳过)

### Definition of Done

- 5/5 测试过 + 4 tracks smoke 全绿
- ruff diff = 0
- 全套 `uv run pytest tests/ -q --ignore=tests/sync/test_baseline_no_regression.py` 应 ~1029 passed
- `uv run pytest tests/sync/test_baseline_no_regression.py` PASS
- `uv run pytest tests/adapter/installer/test_dogfood_invariance_F009.py -v` PASS (baseline 更新后)
- AGENTS.md / RELEASE_NOTES.md F014 段完整

## 6. 任务依赖图

```
T1 ── T2 ── T3 ── T4 ── T5
```

T2 / T3 顺序依赖 (T3 用 T2 的 PathRecaller); T4 用 T3 的 status 段; T5 是 router 文档化 + smoke + finalize, 必须最后.

## 7. Commit 边界

每个 T 一个 commit, 主消息格式: `f014(<part>): T<N> <description>`. T2 含 perf script, T3 含 platform.json schema 扩展, T5 含 docs + smoke + dogfood baseline 更新.

## 8. 与 vision 对齐 (任务级 deliverable)

- T1-T4 完成后 = pattern recall + CLI + cache 闭环 (技术能力到位)
- T5 完成后 = router 集成 + 文档 + smoke (用户感知 + Stage 3 ~95%)

---

> **本任务计划是 r1 (auto-streamlined per F011/F012/F013-A mode); 直接进入 hf-test-driven-dev T1**.
