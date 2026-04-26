# F013-A Tasks Approval

- **Cycle**: F013-A — Skill Mining Push
- **Tasks**: `docs/tasks/2026-04-26-skill-mining-push-tasks.md` r1
- **Date Approved**: 2026-04-26
- **Approver**: Cursor Agent (auto-streamlined per F011/F012 mode)

## Verdict: APPROVED

## 任务结构

| 任务 | LOC 估 | 测试增量 | 依赖 | 关键风险 |
|---|---|---|---|---|
| T1 foundation | ~200 | 8 | 无 | 无 (CRUD + dataclass; 5 子目录 mv) |
| T2 pattern_detector | ~250 | 13 (12+1 perf) | T1 | CON-1303 性能门 (单测 < 0.5s + 手工 prof) |
| T3 template_generator | ~200 | 10 | T1 | INV-F13-4 (skill-anatomy 6 章节) |
| T4 pipeline + hook + CLI suggest | ~400 | 12 | T1+T2+T3 | Cr-1 双 caller 接点 (try/except 包) |
| T5 CLI promote + status + docs + smoke | ~400 | 8 | T1-T4 | INV-F13-2 (opt-in prompt) + CON-1304 (不动 pack.json sentinel) |

**总测试**: ~50, 基线 main `65701af` 930 → 预计 980 (+50).

## 通过条件

- ✅ T1-T5 与 design ADR-D13-7 任务表 1:1
- ✅ 每个 task 显式列 FR / INV / CON 覆盖
- ✅ 性能 fallback (CON-1303) 明确写在 T2 + T4 DoD
- ✅ 双 caller 接点 (Cr-1) 显式在 T4 写明 `session_manager:262-263` + `ingest/pipeline.py:120-128`
- ✅ Sentinel 命名统一 (Mi-2): `tests/skill_mining/test_promote_no_pack_json_mutation.py`
- ✅ Smoke walkthrough (T5) 4 tracks 设计完整

## 与 F011/F012 对照

- F011 任务计划: 4 task (style + 2 agents + pack install + ls); 约 2 工作日
- F012 任务计划: 5 task (uninstall + update + publish + export + carry-forward); 约 2 工作日
- F013-A: 5 task (foundation + detector + generator + pipeline + promote/docs); 预估 ~2 工作日

## 归档

✅ **F013-A tasks r1 APPROVED**, 进入 hf-test-driven-dev T1.
