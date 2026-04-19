# Test Design Approval - F004 T2

- Task: T2 — publisher store-or-update 决策 + supersede 链 carry-over + self-conflict 短路
- Approval Type: `testDesignApproval`
- Approver: cursor cloud agent (auto-mode self-approval)
- Date: 2026-04-19
- Workflow Profile / Execution Mode: `full` / `auto`
- Workspace Isolation: `in-place`
- 关联任务计划: `docs/tasks/2026-04-19-garage-memory-v1-1-tasks.md` § T2
- 关联设计: `docs/designs/2026-04-19-garage-memory-v1-1-design.md` § 10.1 + § 10.1.1 + § 11.2 + § 11.2.1 + ADR-401
- 上游依赖: T1 已完成（见 `docs/verification/F004-T1-implementation-handoff.md`）

## 测试设计

### Fail-first 测试（RED 阶段必须先失败）

1. **`test_repeated_accept_uses_update_increments_version`** — 第 1 次 accept candidate `c-001` (decision) → entry version=1；第 2 次 edit_accept → 同一 entry id, version=2，文件名稳定 (`decision-c-001.md`)。**预期失败原因**：当前 publisher 总是调 `KnowledgeStore.store()`，会重复写入同一文件但 version 不递增（store 内部不递增 version）。
2. **`test_repeated_publish_preserves_supersedes_chain_from_v1`** — fixture 模拟 v1 已发布 entry `front_matter["supersedes"] = ["k-X"]`，当前 candidate 重复发布后新 entry `front_matter["supersedes"]` 至少包含 `["k-X"]`。**预期失败原因**：当前 `_to_knowledge_entry` 重新构造 front_matter 仅含 3 个键，update 路径会丢失 supersedes（FR-405 兼容性 break）。
3. **`test_repeated_accept_short_circuits_self_conflict`** — v1 已发布同名 entry（id == candidate_id），重复 `accept` 不要求 `--strategy`（ConflictDetector 命中自身但 publisher 短路剔除）。**预期失败原因**：当前 publisher 不剔除自身 id，会触发 `ValueError("conflict_strategy")`。

### 关键边界覆盖（fail-first 后补）

4. **`test_retrieve_after_repeated_accept_returns_latest_version`** — 重复发布后 `KnowledgeStore.retrieve(DECISION, "c-001").version == 2` 且 content 是后一次 edit。
5. **`test_repeated_publish_experience_summary_updates_index`** — experience 路径 `experience_summary` 候选重复发布，`ExperienceIndex` 中只有 1 条 record_id。
6. **`test_repeated_publish_preserves_related_decisions_from_v1`** — v1 entry `related_decisions = ["k-Z"]`，重复发布后保留 `["k-Z"]`（与 supersede 链 carry-over 联动验证）。

### 不在本任务覆盖

- 性能 wall-clock 对比（task plan 种子 #7）：在 T1~T5 完成后通过 task verify 段一次性跑全 suite 耗时对比；不强制独立测试，避免 CI 抖动
- CLI / SessionManager / docs（T3 / T4 / T5 范围）

### Mock 边界

- 不 mock storage / ConflictDetector — 用 `tmp_path` 真实 fixture
- v1 已发布 entry 通过 `knowledge_store.store(...)` 直接写入（fixture 复用 publisher.py 测试现有 `_to_knowledge_entry` 模式 + 手工设置 `front_matter["supersedes"]`）

### 与任务计划测试种子的差异

种子 7 (NFR-402 性能 wall-clock) 不作为独立 unit test 实现；改为在 task plan T5 verify 中跑全 suite 一次性核对（避免 CI 抖动）；本设计聚焦 6 个 functional invariant。

## RED→GREEN→REFACTOR 计划

1. **RED**：写 6 个测试 → 6 个全部失败
2. **GREEN**：
   - 在 `publish_candidate` knowledge 路径中：在 `if similar_entries` 之前，剔除 `similar_entries` 中等于 `derive_knowledge_id(candidate_id, knowledge_type)` 的元素（self-conflict 短路）
   - 在 `publish_candidate` knowledge 路径中：调 `_to_knowledge_entry()` 后，覆盖 `entry.id = derive_knowledge_id(candidate_id, knowledge_type)`
   - 在 `publish_candidate` knowledge 路径中：在 `knowledge_store.store(entry)` 前，先 `existing = knowledge_store.retrieve(knowledge_type, entry.id)`；若存在 → carry-over `entry.related_decisions = _merge_unique(existing.related_decisions, entry.related_decisions)`、carry-over `front_matter["supersedes"]` 与 `front_matter["related_decisions"]`、`entry.version = existing.version`、调 `knowledge_store.update(entry)`；否则调 `knowledge_store.store(entry)`
   - 在 `publish_candidate` experience 路径中：调 `_to_experience_record()` 后覆盖 `record.record_id = derive_experience_id(candidate_id)`；先 `existing = experience_index.retrieve(record.record_id)`；存在则 update，否则 store
   - 全部测试转绿
3. **REFACTOR**：
   - 抽出 `_merge_unique(a, b)` 私有 helper（保留 a 顺序 + 不丢失 b 中独有元素）
   - 抽出 `_apply_publish_or_update_for_knowledge(entry, knowledge_type)` 私有方法封装 retrieve → store-or-update + carry-over
   - 模块顶部声明 `PRESERVED_FRONT_MATTER_KEYS` 元组常量
   - 不引入新依赖

## Auto-mode self-approval rationale

- 测试设计完全在 design § 10.1 + § 10.1.1 + § 11.2 + § 11.2.1 范围内
- 6 个测试名 1:1 映射 design 的关键不变量（FR-401 / FR-405 supersede / self-conflict）
- 不存在 USER-INPUT 类决策点
- T1 已 GREEN 提供了 `PublicationIdentityGenerator` 接口，本任务直接复用

## Decision

**Approved**. T2 RGR 可立即开始。
