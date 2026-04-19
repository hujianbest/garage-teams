# Test Design Approval - F004 T1

- Task: T1 — `PublicationIdentityGenerator` + publisher 入口校验前置
- Approval Type: `testDesignApproval`
- Approver: cursor cloud agent (auto-mode self-approval)
- Date: 2026-04-19
- Workflow Profile / Execution Mode: `full` / `auto`
- Workspace Isolation: `in-place`
- 关联任务计划: `docs/tasks/2026-04-19-garage-memory-v1-1-tasks.md` § T1
- 关联设计: `docs/designs/2026-04-19-garage-memory-v1-1-design.md` § 11.1 + § 11.2 + ADR-401 + ADR-402

## 测试设计

### Fail-first 测试（RED 阶段必须先失败）

1. **`test_publication_identity_generator_is_deterministic`** — 同一 `(candidate_id, knowledge_type)` 调 `derive_knowledge_id` N=10 次返回同值；同一 `candidate_id` 调 `derive_experience_id` N=10 次返回同值。**预期失败原因**：`PublicationIdentityGenerator` 类尚未存在，import 即 `ImportError` / `AttributeError`。
2. **`test_publication_identity_default_returns_candidate_id`** — `derive_knowledge_id("candidate-001", KnowledgeType.DECISION)` 返回 `"candidate-001"`；`derive_experience_id("candidate-002")` 返回 `"candidate-002"`。**预期失败原因**：同 1。锁住 ADR-401 默认实现 = candidate_id 透传。
3. **`test_publish_candidate_rejects_garbage_strategy_at_entry`** — `publish_candidate(c, "accept", cf, conflict_strategy="garbageX")` 抛 `ValueError`，错误消息含 `"Allowed: ['abandon', 'coexist', 'supersede']"`。**关键边界**：candidate 不命中相似条目时也必须立即抛错（FR-402 验收 1）。**预期失败原因**：当前 publisher 仅在 conflict 分支校验，无冲突路径下 garbage strategy 不会被拒绝。

### 关键边界覆盖（fail-first 后补）

4. **`test_publish_candidate_accepts_valid_strategy_without_conflict`** — `publish_candidate(c, "accept", cf, conflict_strategy="coexist")` 在不命中相似条目时正常发布，不抛错（FR-402 验收 2）。
5. **`test_publish_candidate_none_strategy_passes_when_no_conflict`** — `publish_candidate(c, "accept", cf, conflict_strategy=None)` 在不命中相似条目时正常发布（FR-402 验收 3，向后兼容）。

### Mock 边界

- 不 mock `KnowledgeStore` / `ExperienceIndex` / `CandidateStore` — 用 `tmp_path` fixture 真实文件存储，已是项目标准模式
- `PublicationIdentityGenerator` 是纯函数 helper class，不需要 mock
- `publish_candidate` 入口校验路径不需要触达存储层即可触发，测试 3 不需要 store fixture（但可复用 conftest fixture）

### 与任务计划测试种子的差异

T1 任务计划列出的 5 个种子全部纳入；测试 3 增加"不命中相似条目时" 条件以显式覆盖 FR-402 关键边界差异（任务计划种子已暗含但本设计显式断言）。

### 不在本任务覆盖

- store-or-update 决策（T2 范围）
- supersede 链 carry-over（T2 范围）
- self-conflict 短路（T2 范围）
- CLI / SessionManager 改动（T3 / T4 范围）

## RED→GREEN→REFACTOR 计划

1. **RED**：先写 5 个测试 → `pytest tests/memory/test_publisher.py::TestPublicationIdentityGenerator -v` 应有 import error；`pytest tests/memory/test_publisher.py::TestEntryValidation -v` 应有 3 个失败（fail-first 测试 3 + 边界 4 + 边界 5；测试 1+2 因 import error 不能跑到断言层但 import 错误本身即 RED）
2. **GREEN**：
   - 在 `src/garage_os/memory/publisher.py` 顶部新增 `PublicationIdentityGenerator` 类
   - 在 `KnowledgePublisher.__init__` 新增 `self._id_generator = PublicationIdentityGenerator()`
   - 在 `publish_candidate` 第一行新增 `self._validate_conflict_strategy(conflict_strategy)`
   - 删除现有 conflict 分支中冗余的 `if conflict_strategy not in self.VALID_CONFLICT_STRATEGIES:` 校验（合并到入口）
   - 全部测试转绿
3. **REFACTOR**：
   - `_validate_conflict_strategy` 私有方法只校验 None vs in-set 两种情况
   - `PublicationIdentityGenerator` 默认实现两个方法各一行
   - 不引入新依赖、不改变其他公开 API

## Auto-mode self-approval rationale

- T1 测试设计完全在 design § 11.1 + § 11.2 接口契约范围内，无新行为决策
- 5 个测试名 1:1 映射 task plan T1 测试种子 + FR-402 验收
- fail-first 路径清晰可执行
- 不存在 USER-INPUT 类决策点

## Decision

**Approved**. T1 RGR 可立即开始。
