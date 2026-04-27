# F016 Tasks — Memory Activation 实施分块

- **状态**: r1 (auto-streamlined per F011-F015 mode)
- **关联**: spec r2 + design r1 APPROVED
- **日期**: 2026-04-27

## 任务总览

| T | 提交主题 | 测试 | 依赖 | DoD |
|---|---|---|---|---|
| **T1** | `memory_activation/{__init__, types, templates}` + 3 STYLE 模板 + 8 测试 | 8 | 无 | 8/8 PASS; ruff diff 0 |
| **T2** | `memory_activation/ingest.py` (3 paths + dedup + dry-run + strict) + 12 测试 | 12 | T1 | 12/12 PASS |
| **T3** | CLI `garage memory {enable, disable, status, ingest}` + `_init` prompt + `_status` 集成 + 10 测试 | 10 | T1+T2 | 10/10 PASS |
| **T4** | sentinel + AGENTS + RELEASE_NOTES + manual smoke + 5 sentinel | 5 | T1-T3 | 5 sentinel PASS; 全套 1103 → ~1138 + 0 regression |

**总测试**: ~35 (基线 F015 1103 → ~1138).

## 通过条件

- ✅ T1-T4 与 design ADR-D16-6 1:1
- ✅ Sentinel 命名: `tests/memory_activation/test_{init_yes_does_not_enable_memory,no_pipeline_changes,style_template_parse}.py`
- ✅ Smoke walkthrough (T4) 4 tracks (init prompt / ingest reviews / ingest style / status 显示)

✅ **F016 tasks r1 APPROVED**, 进入 hf-test-driven-dev T1.
