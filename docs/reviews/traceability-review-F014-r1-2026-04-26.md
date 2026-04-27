# Traceability Review — F014 r1 (Workflow Recall)

- **日期**: 2026-04-26
- **审阅人**: Cursor Agent (auto-streamlined per F011/F012/F013-A mode)
- **范围**: 5 个 FR (FR-1401..1405) + 5 个 INV (INV-F14-1..5) + 5 个 CON (CON-1401..1405)

## Verdict: APPROVED

## FR ↔ 实现 ↔ 测试 矩阵

| FR | 实现位置 | 测试 |
|---|---|---|
| **FR-1401** Path Recaller | `path_recaller.py::recall` | `test_path_recaller.py` 20 用例 + `test_path_recaller_perf_100_records.py` |
| **FR-1402** `garage recall workflow` CLI | `cli.py::_recall_workflow` (含 --task-type / --problem-domain / --skill-id / --top-k / --json / --rebuild-cache) | `TestRecallWorkflowCommand` 8 用例 |
| **FR-1403** hf-workflow-router 集成 | `packs/coding/skills/hf-workflow-router/SKILL.md` step 3.5 + `references/recall-integration.md` | `test_dogfood_invariance_F009.py` baseline + `test_documentation.py::test_agents_md_mentions_workflow_recall_cli` |
| **FR-1404** Cache + invalidate hook | `cache.py::WorkflowRecallCache` + `pipeline.py::WorkflowRecallHook.invalidate` + 4 caller 接入 | `test_cache.py` 14 用例 + `test_pipeline.py::TestInvalidateDeletes` + `TestCallerHookIntegration` |
| **FR-1405** `garage status` 集成 | `pipeline.py::compute_status_summary` + `cli.py::_print_workflow_recall_status` | `TestComputeStatusZeroRecords` + `TestComputeStatusWithAdvisories` |

**5 / 5 FR 全部追溯**

## INV ↔ 测试

| INV | 测试 |
|---|---|
| INV-F14-1 (read-only on EI) | `test_path_recaller.py::TestReadOnlyOnExperienceIndex::test_recall_does_not_mutate_records` (sentinel: list_records 前后字节相等) |
| INV-F14-2 (写仅 .garage/workflow-recall/) | `test_cache.py::TestLazyMkdir` + write only to `_root` |
| INV-F14-3 (advisory only, 不改 router authoritative routing) | 文档级守门: SKILL.md step 3.5 + recall-integration.md "advisory only — 用户可改"; 无运行时强制路径 |
| INV-F14-4 (F004 schema + API 字节级不变) | sentinel: `git diff main..HEAD -- src/garage_os/knowledge/experience_index.py src/garage_os/types/__init__.py` 应为 0 (除 F015+ 显式扩) |
| INV-F14-5 (router step 1-10 + dogfood SHA) | `test_dogfood_invariance_F009.py` baseline 已更 2 keys + `test_neutrality_exemption_list.py` PASS |

**5 / 5 INV 全部覆盖**

## CON ↔ 验证

| CON | 验证 |
|---|---|
| CON-1401 (F003-F013 既有 API 字节级不变) | 4 caller try/except 包不改 method 签名; F004 ExperienceIndex 不修改; 全套 989 → 1043 + 0 regression |
| CON-1402 (零依赖) | `git diff main..HEAD -- pyproject.toml uv.lock` = 0 |
| CON-1403 (perf < 2s for 1000 records) | `test_path_recaller_perf_100_records.py` 100 records < 0.2s + `scripts/workflow_recall_perf_smoke.py` 1000 records = 0.064s |
| CON-1404 (router 改不破 3 项守门) | (a) `test_dogfood_invariance_F009.py` PASS (baseline 已更 2 keys); (b) `test_neutrality_exemption_list.py` PASS; (c) 全套 1043 passed 0 regression |
| CON-1405 (recall 与 recommend 独立) | `test_recall_no_recommend_import.py` AST 静态分析 sentinel; CLI handler 不 import recommend 模块 |

## 上下游 trace

- **Spec ↔ Design ↔ Tasks ↔ Impl**: spec r2 (FR-1401..1405 + 5 INV + 5 CON) → design r2 (7 ADR + 5 INV + 5 CON) → tasks T1-T5 → 实施 commits (cae3f3d / 0287880 / 3cd3abe / 98936e7 / TBD-T5)
- **F003-F013 既有 API 复用 (CON-1401)**: F004 ExperienceIndex.list_records / ExperienceRecord schema 不动; F006 recommend 完全独立 (CON-1405); F009 dogfood SHA baseline 同 sentinel 守门; F010 sync inline status 同 pattern; F011 publisher.py 多 caller 接入同 pattern; F013-A SkillMiningHook 多 caller pattern 复用
- **vision 闭环**: growth-strategy.md § Stage 3 第 68 行 ❌ → ✅ (workflow 半自动编排)
- **router 文档化**: hf-workflow-router/SKILL.md step 3.5 + recall-integration.md → 2 keys dogfood baseline 同步

## 残余项

- **None blocking**.

## 通过条件

✅ traceability review APPROVED, 进入 regression gate.
