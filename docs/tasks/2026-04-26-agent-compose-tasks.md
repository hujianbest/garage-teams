# F015 Tasks — Agent Compose 实施分块

- **状态**: r1 (auto-streamlined per F011/F012/F013-A/F014 mode)
- **关联 spec**: `docs/features/F015-agent-compose.md` r2 APPROVED
- **关联 design**: `docs/designs/2026-04-26-agent-compose-design.md` r1 APPROVED
- **日期**: 2026-04-26

## 任务总览

| 任务 | 提交主题 | 测试增量 | 依赖 | DoD |
|---|---|---|---|---|
| **T1** | `agent_compose/{__init__, types, template_generator}` + 多行 desc 切分 + 10 测试 | 10 | 无 | 10/10 PASS; ruff diff 0 |
| **T2** | `agent_compose/composer.py` + 双层 missing 语义 + 12 测试 | 12 | T1 | 12/12 PASS; ruff diff 0 |
| **T3** | CLI `garage agent compose` + `agent ls` + `_print_agent_compose_status` + `pipeline.py` + 10 测试 | 10 | T1+T2 | 10/10 PASS; ruff diff 0; CON-1505 sentinel PASS |
| **T4** | AGENTS / RELEASE_NOTES + manual smoke + 4 sentinel | 4 | T1-T3 | 4 sentinel PASS (INV-F15-5 / CON-1503 / CON-1502 / CON-1505); 全套 1043 → 1079 + 0 regression |

**总测试**: ~36, F014 后基线 1043 → F015 完成 1079.

## 通过条件

- ✅ T1-T4 与 design ADR-D15-6 任务表 1:1
- ✅ 每个 task 显式列 FR / INV / CON 覆盖
- ✅ Sentinel 命名: `tests/agent_compose/test_{f011_agents_unchanged,compose_no_pack_json_mutation,no_sibling_import}.py`
- ✅ Smoke walkthrough (T4) 4 tracks 设计完整 (Cr-1 r2: 用 `demo-overwrite-agent` 而非 F011 既有)

## 归档

✅ **F015 tasks r1 APPROVED**, 进入 hf-test-driven-dev T1.
