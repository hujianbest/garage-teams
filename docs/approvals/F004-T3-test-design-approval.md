# Test Design Approval - F004 T3

- Task: T3 — CLI abandon 双路径 confirmation + stdout 文案差异化
- Approval Type: `testDesignApproval`
- Approver: cursor cloud agent (auto-mode self-approval)
- Date: 2026-04-19
- Workflow Profile / Execution Mode: `full` / `auto`
- Workspace Isolation: `in-place`
- 关联任务计划: `docs/tasks/2026-04-19-garage-memory-v1-1-tasks.md` § T3
- 关联设计: `docs/designs/2026-04-19-garage-memory-v1-1-design.md` § 10.3 + § 11.5 + ADR-403
- 上游依赖: T2 已完成（self-conflict 短路在 publisher 层已实现，本任务测试条件可干净复现"真实命中不同 entry 的冲突"）

## 测试设计

### Fail-first 测试（RED 阶段必须先失败）

1. **`test_memory_review_abandon_outputs_no_pub_marker`** — `--action=abandon`，stdout 包含 `MEMORY_REVIEW_ABANDONED_NO_PUB.format(cid="candidate-001")`。**预期失败原因**：当前 cli.py 输出通用 "Candidate 'X' action 'abandon' applied" 文案；常量 `MEMORY_REVIEW_ABANDONED_NO_PUB` 尚不存在。
2. **`test_memory_review_conflict_abandon_outputs_conflict_marker`** — `--action=accept --strategy=abandon` + 真实冲突命中（不同 entry，不是 self-conflict），stdout 包含 `MEMORY_REVIEW_ABANDONED_CONFLICT.format(cid=...)`。**预期失败原因**：常量不存在；当前 stdout 同样通用。
3. **`test_memory_review_two_abandon_markers_do_not_overlap`** — 两个常量 substring 互不重叠，可独立 grep 区分（FR-403b 验收 3）。**预期失败原因**：常量不存在。

### 关键边界覆盖

4. **`test_memory_review_abandon_writes_resolution_abandon_with_null_strategy`** — `--action=abandon` 路径 confirmation 文件 `resolution=abandon` + `conflict_strategy=null`（FR-403a 验收 1）。**预期失败原因**：当前 cli.py abandon 路径与 accept/edit_accept/reject 走共享 confirmation 写入逻辑，`resolution=abandon` 已正确，`conflict_strategy=null` 也正确；但常量化的 stdout 检查需要新增。fail-first 状态依赖测试 1。**注**：此测试当前可能已经过（abandon 不带 --strategy 默认 None），但作为 acceptance 锁住。
5. **`test_memory_review_accept_with_strategy_abandon_writes_resolution_accept`** — `--action=accept --strategy=abandon` + 真实冲突，confirmation 文件 `resolution=accept` + `conflict_strategy=abandon`（FR-403a 验收 2）。
6. **`test_memory_review_accept_with_abandon_strategy_no_conflict_falls_through_to_publish`** — `--action=accept --strategy=abandon` + 不命中冲突，行为退化为正常 accept publish，candidate `status=published`，confirmation `resolution=accept` + `conflict_strategy=null`（FR-403a 验收 3）。

### Mock 边界

- 不 mock 任何 publisher / store — 用 `tmp_path` fixture
- 通过 `runner.invoke(main, [...])` 或 `main(["memory", "review", ...])` 直接调用 CLI；用 `capsys.readouterr()` 捕获 stdout
- 真实冲突场景（不是 self-conflict）：先种一个**不同 candidate id** 的 v1 entry（与待发布 candidate 同 title/tags），让 ConflictDetector 命中且 self-conflict 短路不剔除

### 与任务计划测试种子的差异

完全一致；6 个种子 1:1 实现。

## RED→GREEN→REFACTOR 计划

1. **RED**：写 6 个测试 → 至少 3 个 fail-first 测试失败（常量缺失 / stdout 文案不匹配）
2. **GREEN**：
   - 在 cli.py 模块级新增 `MEMORY_REVIEW_ABANDONED_NO_PUB` 与 `MEMORY_REVIEW_ABANDONED_CONFLICT` format string 常量
   - 改 abandon 路径（`--action=abandon`）：仍走现有 confirmation 写入；stdout 改为 `MEMORY_REVIEW_ABANDONED_NO_PUB.format(cid=candidate_id)`
   - 改 accept-with-abandon 路径（publisher 返回 `conflict_strategy="abandon"` 早返回）：stdout 在 publish_result 检测到 `conflict_strategy="abandon"` 时打印 `MEMORY_REVIEW_ABANDONED_CONFLICT.format(cid=candidate_id)`
   - 不命中冲突的 accept-with-abandon 路径：行为不变（与 v1 一致，正常 publish stdout）
   - 全部测试转绿
3. **REFACTOR**：
   - 模块顶部统一管理两个常量
   - abandon 路径与正常 accept 路径的 stdout 分支清晰

## Auto-mode self-approval rationale

- 测试设计完全在 design § 10.3 + § 11.5 + ADR-403 范围内
- 6 个测试名 1:1 映射 task plan T3 测试种子
- 不存在 USER-INPUT 类决策点
- T2 已 GREEN 提供了 self-conflict 短路，"真实冲突命中"测试场景可干净复现

## Decision

**Approved**. T3 RGR 可立即开始。
