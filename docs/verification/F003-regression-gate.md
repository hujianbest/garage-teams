# Verification Record — F003 Regression Gate

## Metadata

- Verification Type: regression-gate
- Scope: F003 全量实现批次（T1-T9 + test-review r1 / code-review r1 两轮回流修订）
- Date: 2026-04-18
- Record Path: `docs/verification/F003-regression-gate.md`
- Worktree Path / Worktree Branch: `in-place` / `cursor/f003-quality-chain-3d5f`
- Workflow Profile: `full`
- Execution Mode: `auto`

## Upstream Evidence Consumed

- Implementation Handoffs:
  - `docs/verification/F003-T1-implementation-handoff.md`
  - `docs/verification/F003-test-review-r1-handoff.md`
  - `docs/verification/F003-code-review-r1-handoff.md`
- Review / Gate Records:
  - `docs/reviews/test-review-F003-garage-memory-auto-extraction.md` (r1 = 需修改)
  - `docs/reviews/test-review-F003-garage-memory-auto-extraction-r2.md` (r2 = 通过)
  - `docs/reviews/test-review-F003-garage-memory-auto-extraction-r3.md` (r3 增量 = 通过)
  - `docs/reviews/code-review-F003-garage-memory-auto-extraction.md` (r1 = 需修改)
  - `docs/reviews/code-review-F003-garage-memory-auto-extraction-r2.md` (r2 = 通过)
  - `docs/reviews/traceability-review-F003-garage-memory-auto-extraction.md` (= 通过)
- Task / Progress Anchors:
  - `task-progress.md`
  - `docs/tasks/2026-04-18-garage-memory-auto-extraction-tasks.md`

## Claim Being Verified

- Claim: F003 全量实现批次 + 两轮回流修订引入的代码改动未破坏既有功能；新增能力（memory candidate 提取/确认/发布、recommendation、CLI surface、FR-307 错误归一化）端到端可运行；off-switch / FR-302b / FR-303a / FR-304 / FR-307 等硬约束在文件层与运行时均有 fresh evidence 支撑。

## Verification Scope

- Included Coverage:
  - 全套 pytest（`tests/` 384 个用例），覆盖 storage / runtime / knowledge / memory / platform / tools / cli / integration / types / 安全 / 兼容性
  - 重点回归点（来自 traceability link matrix）：
    - `tests/memory/test_candidate_store.py`（FR-302a/302b/303a 5-cap）
    - `tests/memory/test_extraction_orchestrator.py`（FR-301/302a/302b/303a/307 + 锚点）
    - `tests/memory/test_publisher.py`（FR-303/304 + 设计 §11.4 + contract test）
    - `tests/memory/test_recommendation_service.py`（FR-305/306）
    - `tests/runtime/test_session_manager.py`（FR-301 archive 触发 + FR-307 失败不阻塞 + T4 off-switch）
    - `tests/runtime/test_skill_executor.py`（FR-305/306 推荐注入）
    - `tests/test_cli.py`（设计 §9.8 canonical surface + T4 off-switch + FR-304 三选一 + abandon）
    - `tests/integration/test_e2e_workflow.py`（最薄 archive→candidate→publish→recommend 闭环）
    - `tests/knowledge/test_knowledge_store.py` / `test_experience_index.py` / `test_integration.py`（设计 §11.4 traceability 字段不破坏既有 store/index 行为）
- Uncovered Areas:
  - lint baseline 36 条已存在（main 同样 36 条），本轮零新增；按项目惯例不作为回归门禁信号
  - mypy 未在本轮执行：`AGENTS.md` 把 `uv run mypy src/` 列为辅助命令而非门禁；上轮亦未将其作为门禁信号
  - manual GUI 测试不适用：F003 全部为 CLI / 库级行为
  - `KnowledgePublisher` 用 `candidate_id` 当 `KnowledgeEntry.id` 的 minor finding（traceability TZ5 / code-review r1 finding 5）按 r1 follow-up handoff + r2 + traceability 显式延后接受，不在本回归覆盖范围

## Commands And Results

```text
source .venv/bin/activate && pytest tests/ -q --tb=line
```

- Exit Code: `0`
- Summary: `384 passed in 24.54s`
- Notable Output:
  - `tests/memory/test_candidate_store.py .....`（5/5）
  - `tests/memory/test_extraction_orchestrator.py .......`（7/7，含新增 anchors / experience_summary 完整性 / extraction_failed batch / truncation）
  - `tests/memory/test_publisher.py ...........`（11/11，含 contract test + supersede / coexist / abandon 三向 + abandon 跳过 experience_summary）
  - `tests/memory/test_recommendation_service.py ...`（3/3）
  - `tests/runtime/test_session_manager.py ...................`（19/19，含 off-switch + 失败不阻塞 + memory 触发）
  - `tests/runtime/test_skill_executor.py ....................`（20/20）
  - `tests/integration/test_e2e_workflow.py`（在 `tests/integration/` 12/12，含最薄 memory 闭环）
  - `tests/test_cli.py ........................`（24/24，含 abandon + accept 强制 strategy + recommendation off-switch）

辅助检查（非门禁，留作 finalize 视野）：

```text
ruff check src/garage_os/memory/ src/garage_os/runtime/session_manager.py src/garage_os/cli.py
```

- Exit Code: `1`
- Summary: `Found 36 errors`
- 与 `origin/main` 同等基线一致，本轮零新增；项目当前未把 `ruff` 列为质量链门禁

## Freshness Anchor

- 命令在当前会话内（worktree branch `cursor/f003-quality-chain-3d5f`、HEAD `2890403 docs(reviews): add F003 code-review r2 record (通过)`）实际执行
- 测试输出与 `F003-T1-implementation-handoff.md` / `F003-test-review-r1-handoff.md` / `F003-code-review-r1-handoff.md` 中声明的 GREEN 摘要一致（基线从 369 → 376 → 384 持续递增，每轮回流均有可冷读的 fresh evidence）
- `pytest` 在归档/恢复 fixture 上使用 `tmp_path`，不污染仓库 `.garage/` 状态；无 worktree 锚点冲突

## Conclusion

- Conclusion: `通过`
- Next Action Or Recommended Skill: `hf-completion-gate`

## Scope / Remaining Work Notes

- Remaining Task Decision: F003 任务计划 §9 任务队列已全 done，T1-T9 均已闭合；进入 completion gate 由其判断是否可宣告任务完成
- Notes:
  - `traceability-review` 列出的 7 项 minor（含 USER-INPUT 1 项）中：
    - 1 项 USER-INPUT（candidate_id 复用）建议 `hf-completion-gate` 阶段真人正式裁决
    - 6 项 LLM-FIXABLE（test-design-approval merge note、stale `# pragma`、conflict_strategy 入口校验、CLI abandon 语义重叠、session 侧 logger.warning 双写、`.garage/config/platform.json` 缺 memory 块）建议 `hf-finalize` 阶段顺手清理或在 release notes 中显式记录
  - 没有 critical/important 阻塞型 finding 流入回归门禁

## Related Artifacts

- 源码主线：`src/garage_os/memory/`、`src/garage_os/runtime/session_manager.py`、`src/garage_os/runtime/skill_executor.py`、`src/garage_os/cli.py`
- 测试主线：`tests/memory/`、`tests/runtime/test_session_manager.py`、`tests/runtime/test_skill_executor.py`、`tests/integration/test_e2e_workflow.py`、`tests/test_cli.py`
- 平台配置：`.garage/config/platform.json`（默认 memory 关闭，由 `cli._init` 写入 `DEFAULT_PLATFORM_CONFIG`）
