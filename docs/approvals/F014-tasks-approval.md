# F014 Tasks Approval

- **Cycle**: F014 — Workflow Recall
- **Tasks**: `docs/tasks/2026-04-26-workflow-recall-tasks.md` r1
- **Date Approved**: 2026-04-26
- **Approver**: Cursor Agent (auto-streamlined per F011/F012/F013-A mode)

## Verdict: APPROVED

## 任务结构

| 任务 | LOC 估 | 测试增量 | 依赖 | 关键风险 |
|---|---|---|---|---|
| T1 foundation | ~150 | 8 | 无 | 无 (CRUD + dataclass + atomic write) |
| T2 path_recaller | ~200 | 13 (12+1 perf) | T1 | CON-1403 性能门 |
| T3 pipeline + 4 caller hook + status | ~250 | 6 | T1+T2 | Cr-1+Cr-2+Im-1 r2 修订: 4 caller 接入 (cli.py / publisher.py 顶层 / integration.py / session_manager.py) |
| T4 CLI recall workflow | ~200 | 8 | T1-T3 | CON-1405 (与 F006 recommend 独立) |
| T5 router SKILL.md + dogfood SHA + docs + smoke | ~200 | 5 | T1-T4 | INV-F14-5 (additive step 3.5) + Im-2 r2 (2 处 hash 而非 3) |

**总测试**: ~40, 基线 main `f5950b4` 989 → 预计 1029.

## 通过条件

- ✅ T1-T5 与 design ADR-D14-7 任务表 1:1
- ✅ 每个 task 显式列 FR / INV / CON 覆盖
- ✅ 性能 fallback (CON-1403) 明确写在 T2 + T5 DoD
- ✅ 4 caller 接入点 (Cr-1+Cr-2+Im-1 r2) 显式列出真实文件 + 行号 (cli.py:1741 / publisher.py:143 / integration.py:222 / session_manager.py:268-277)
- ✅ Sentinel 命名: `tests/workflow_recall/test_recall_no_recommend_import.py` (CON-1405)
- ✅ Smoke walkthrough (T5) 4 tracks 设计完整

## 与 F011/F012/F013-A 对照

- F011: 4 task / ~2 工作日
- F012: 5 task / ~2 工作日
- F013-A: 5 task / +59 测试 / ~2 工作日
- F014: 5 task / +40 测试 (路由学习 + cache; 比 F013-A 略小)

## 归档

✅ **F014 tasks r1 APPROVED**, 进入 hf-test-driven-dev T1.
