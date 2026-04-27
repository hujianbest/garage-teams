# Traceability Review — F015 r1 (Agent Compose)

- **日期**: 2026-04-26
- **审阅人**: Cursor Agent (auto-streamlined per F011/F012/F013-A/F014 mode)
- **范围**: 5 个 FR (FR-1501..1505) + 5 个 INV (INV-F15-1..5) + 5 个 CON (CON-1501..1505)

## Verdict: APPROVED

## FR ↔ 实现 ↔ 测试 矩阵

| FR | 实现位置 | 测试 |
|---|---|---|
| **FR-1501** AgentComposer | `composer.py::compose` + `template_generator.py::render` | `test_composer.py` 18 + `test_template_generator.py` 22 |
| **FR-1502** STYLE entries 集成 | `composer.py::_collect_style_entries` (Mi-2 r2 完整签名) | `TestStyleExclusion` + `TestStyleEmpty` + `TestComposeHappyPath` |
| **FR-1503** `garage agent compose` CLI | `cli.py::_agent_compose` + Im-1 r2 strict | `TestAgentComposeCommand` 7 用例 |
| **FR-1504** `garage agent ls` CLI | `cli.py::_agent_ls` | `TestAgentLsCommand` 3 用例 |
| **FR-1505** `garage status` 集成 | `pipeline.py::compute_status_summary` + `cli.py::_print_agent_compose_status` | `test_pipeline.py` 6 用例 |

**5 / 5 FR 全部追溯**

## INV ↔ 测试

| INV | 测试 |
|---|---|
| INV-F15-1 (read-only on SKILL.md + KS) | `TestComposeHappyPath` (SKILL.md unchanged) + KS read via list_entries |
| INV-F15-2 (写仅 .garage/agent_compose/ + packs/<target>/agents/) | T2 composer 不写盘 + T3 CLI 唯一写盘点 + sentinel: 不写 outside 目录 |
| INV-F15-3 (compose 不动 pack.json) | `test_compose_does_not_modify_pack_json` byte hash sentinel |
| INV-F15-4 (F003-F014 schema 字节级) | sentinel: src/garage_os/types 不动 |
| INV-F15-5 (F011 3 agent byte 不变) | `test_f011_agents_unchanged.py` byte hash sentinel + BDD 8.4 用 demo-overwrite-agent (不破 F011 既有 3 个名) |

**5 / 5 INV 全部覆盖**

## CON ↔ 验证

| CON | 验证 |
|---|---|
| CON-1501 | git diff main..HEAD -- src/garage_os 既有 F003-F014 模块 = 0 |
| CON-1502 | git diff main..HEAD -- pyproject.toml uv.lock = 0 |
| CON-1503 | byte sentinel PASS (pack.json bytes 前后相等) |
| CON-1504 | TestRenderFullSchema 9 用例验 7-section |
| CON-1505 | `test_no_sibling_import.py` AST sentinel |

## 上下游 trace

- **Spec ↔ Design ↔ Tasks ↔ Impl**: spec r2 → design r1 → tasks r1 → 实施 commits (e671070 T1, 3e5c470 T2, 5be6f2d T3, T4 finalize)
- **F011 复用 (CON-1501)**: F011 既有 3 个 agent.md 是 F015 模板参考 (Cr-2 r2 收窄 2 个); KnowledgeType.STYLE 既有 (F011 cycle); F015 不动 F011 任何 method 签名
- **F013-A pattern 复刻**: template_generator + composer + CLI promote (与 F013-A skill mining 同 pattern)
- **vision 闭环**: growth-strategy.md § Stage 3 第 67 行 ⚠️ 半交付 → ✅; Stage 3 三项核心新增全交付

## 残余项

- **None blocking**.

## 通过条件

✅ traceability review APPROVED, 进入 regression gate.
