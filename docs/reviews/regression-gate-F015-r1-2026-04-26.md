# Regression Gate — F015 r1 (Agent Compose)

- **日期**: 2026-04-26
- **审阅人**: Cursor Agent (auto-streamlined per F011/F012/F013-A/F014 mode)

## Verdict: PASS

## 测试基线

| 阶段 | passed | 增量 |
|---|---|---|
| F014 finalize 后 (基于 cursor/f014-workflow-recall-bf33) | 1043 | baseline |
| F015 T1 (template_generator) | 1065 | +22 |
| F015 T2 (composer) | 1083 | +18 |
| F015 T3 (CLI compose / ls + status) | 1099 | +16 |
| F015 T4 (sentinel + AGENTS / RELEASE_NOTES + smoke) | **1103** | +4 |

**总增量: +60 测试; 0 regression**

## Sentinel 测试

```
$ pytest tests/sync/test_baseline_no_regression.py -v
PASSED [100%]  (1 passed in 78.69s)
```

## ruff baseline diff = 0

T1-T4 引入 0 新 ruff 错误 (与 F013-A / F014 同预算).

## 依赖变更

```
$ git diff main..HEAD -- pyproject.toml uv.lock
(empty)
```

**CON-1502 守门: 0 字节依赖变更.**

## INV / CON sentinels

```
$ pytest tests/agent_compose/test_f011_agents_unchanged.py -v   # INV-F15-5
PASSED

$ pytest tests/agent_compose/test_no_sibling_import.py -v        # CON-1505
PASSED

$ pytest tests/test_cli.py::TestAgentComposeCommand::test_compose_does_not_modify_pack_json -v   # CON-1503
PASSED
```

## 文件清单

### 新增 (4 src + 6 test + 1 doc)
- `src/garage_os/agent_compose/{__init__,types,template_generator,composer,pipeline}.py` (5 文件)
- `tests/agent_compose/{__init__,test_template_generator,test_composer,test_pipeline,test_f011_agents_unchanged,test_no_sibling_import}.py` (6 文件)
- `docs/manual-smoke/F015-walkthrough.md`
- 6 个 review/approval/spec/design/tasks 文档

### 修改 (1 src + 2 test + 2 docs)
- `src/garage_os/cli.py` (+220 LOC; agent subparser + 2 handler + status 段)
- `tests/test_cli.py` (+~280 LOC; 2 CLI test classes)
- `tests/test_documentation.py` (+18 LOC; 1 sentinel)
- `tests/adapter/installer/test_dogfood_layout.py` (+8 LOC; 1 sentinel)
- `AGENTS.md` (+60 LOC; Agent Compose (F015) section)
- `RELEASE_NOTES.md` (+85 LOC; F015 cycle entry)

## Manual Smoke Walkthrough

`docs/manual-smoke/F015-walkthrough.md` — 5 tracks 全绿:
- Track 1: empty agents + status (No agents in pack 'garage')
- Track 2: compose --dry-run → 7-section preview
- Track 3: compose --yes → packs/garage/agents/<name>.md 创建; pack.json 不变
- Track 4: agent ls + status with agent
- Track 5: missing skill → exit 1; pack.json 不变 (CON-1503 ✓)

## 通过条件

✅ regression gate PASS, 进入 completion gate.
