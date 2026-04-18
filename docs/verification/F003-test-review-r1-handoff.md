# 实现交接块 — F003 test-review r1 回流修订

- 关联任务: F003（T1-T9 全量批次的测试质量回流修订）
- 回流来源: `docs/reviews/test-review-F003-garage-memory-auto-extraction.md`（test review r1，结论 = 需修改）
- Workspace Isolation / Worktree Path / Worktree Branch: `in-place` / `N/A` / `cursor/f003-quality-chain-3d5f`
- 测试设计确认证据: auto-mode 下沿用 `docs/approvals/F003-tasks-approval.md`；本次回流修订只补 LLM-FIXABLE findings 的目标缺口（关闭分支、supersede/abandon、truncation、FR-302b 校验），未引入新行为契约，无需重走 `hf-tasks-review`/新增 `test-design-approval`。

## 触碰工件

源码：

- `src/garage_os/memory/candidate_store.py`（FR-302b：必填元信息校验）
- `src/garage_os/memory/extraction_orchestrator.py`（候选 truncation 数字真实回写到 `truncated_count`）
- `src/garage_os/memory/publisher.py`（accept 时 supersede 关系回写；abandon 早返回对所有候选类型生效）

测试：

- `tests/memory/test_candidate_store.py`（+ FR-302b negative 测试）
- `tests/memory/test_extraction_orchestrator.py`（+ truncation 与 `truncated_count` 测试）
- `tests/memory/test_publisher.py`（+ supersede 关系回写、+ abandon 跳过 decision、+ abandon 跳过 experience_summary）
- `tests/runtime/test_session_manager.py`（+ extraction_enabled=False 关闭分支测试）
- `tests/test_cli.py`（+ recommendation_enabled=False 关闭分支测试）

## RED 证据

命令：`pytest tests/runtime/test_session_manager.py::test_archive_session_skips_memory_when_extraction_disabled tests/test_cli.py::TestRunCommand::test_run_skips_recommendation_when_disabled tests/memory/test_publisher.py::TestKnowledgePublisher::test_publish_supersede_records_relation_to_existing_entries tests/memory/test_publisher.py::TestKnowledgePublisher::test_publish_abandon_skips_publication tests/memory/test_publisher.py::TestKnowledgePublisher::test_publish_abandon_skips_experience_summary tests/memory/test_extraction_orchestrator.py::TestExtractionOrchestrator::test_extract_truncates_to_max_pending_and_records_truncated_count tests/memory/test_candidate_store.py::TestCandidateStore::test_reject_candidate_missing_required_metadata -v`

首次失败摘要：

- `test_publish_supersede_records_relation_to_existing_entries` → `AssertionError: assert 'existing-001' in []`（`KnowledgeEntry.related_decisions` 为空）
- `test_publish_abandon_skips_experience_summary` → `AssertionError: assert 'candidate-002' is None`（`abandon` 仍把 experience_summary 入库）
- `test_extract_truncates_to_max_pending_and_records_truncated_count` → `assert 0 >= 1`（batch.truncated_count 一直写 0）
- `test_reject_candidate_missing_required_metadata` → `Failed: DID NOT RAISE <class 'ValueError'>`（store 未校验 FR-302b 字段）

为什么预期失败：

- supersede 关系：发布前已能探测，但发布时未把 `similar_entries` 写回 `related_decisions`，导致 T6 第二条验收（"supersede 时新旧关系正确写回"）无证据。
- abandon：原实现只在非 experience_summary 分支提前返回，experience_summary 永远会被发布，违反 T6 第三条验收。
- truncation：orchestrator 用 `[: MAX_PENDING_CANDIDATES]` 硬切，但 `_build_summary` 始终写 `truncated_count=0`，违反设计 11.2 / FR-303a 的 batch schema。
- FR-302b：候选缺 `session_id` / `source_artifacts` 时仍可入库，违反"候选缺必需元信息时不能进入待确认队列"。

另：`test_archive_session_skips_memory_when_extraction_disabled` 与 `test_run_skips_recommendation_when_disabled` 在实现侧已经支持，但此前**零测试覆盖**（reviewer important finding）。本轮直接补测试转绿，等价于把"开关关闭分支"这一 acceptance 用 fresh evidence 锁定。

## GREEN 证据

命令：`pytest tests/runtime/test_session_manager.py::test_archive_session_skips_memory_when_extraction_disabled tests/test_cli.py::TestRunCommand::test_run_skips_recommendation_when_disabled tests/memory/test_publisher.py tests/memory/test_extraction_orchestrator.py tests/memory/test_candidate_store.py -v`

通过摘要：`19 passed in 0.24s`

关键结果：

- `extraction_enabled=False` 下 archive 不在 `memory/candidates/batches/` 写入任何 batch；session 仍归档成功。
- `recommendation_enabled=False` 下 `garage run` 不打印 `Recommendations:`，且 `RecommendationService` 未被构造。
- 接受 candidate 时，若 `ConflictDetector` 给出 `supersede`，发布的 `KnowledgeEntry.related_decisions` 与 `front_matter["supersedes"]` 都包含旧条目 ID。
- `abandon` 对 decision/pattern/solution 与 experience_summary 都跳过发布，正式 store 列表保持空。
- 8 个 signals 输入下，batch 候选裁剪到 5 条，且 `truncated_count == 3`（`len(generated) - MAX_PENDING_CANDIDATES`），与磁盘 batch JSON 一致。
- Candidate 缺 `session_id` 或 `source_artifacts` 时 `store_candidate` 抛 `ValueError`。

回归证据：`pytest tests/ -q` → `376 passed in 24.55s`（基线 369，本轮 +7 新测试，全套零回归）。

## 与任务计划测试种子的差异

- T1（`tests/memory/test_candidate_store.py`）：在原有 3 条测试种子之外，新增 1 条 FR-302b negative 测试，与 task-plan 第 8 节里"未确认候选不得进入正式 knowledge / experience"的边界一致，未引入新行为。
- T3（`tests/runtime/test_session_manager.py`）：在原有 archive×extract happy path 与异常降级之外，新增 1 条 `extraction_enabled=False` 关闭分支测试，是 T4 acceptance 在 session_manager 侧的 missing 覆盖。
- T4（`tests/test_cli.py`）：新增 1 条 `recommendation_enabled=False` 关闭分支测试，覆盖 T4 第二、三条 acceptance。
- T6（`tests/memory/test_publisher.py`）：在原有 `detect_conflicts` 测试基础上，新增 supersede 关系回写测试（accept 路径） + 两条 abandon 跳过发布测试（decision、experience_summary），覆盖 T6 第二、三条 acceptance。
- T2（`tests/memory/test_extraction_orchestrator.py`）：新增 truncation 测试，与 task-plan 第 5 节"裁剪到最多 5 条"+ 设计 11.2 `truncated_count` schema 一致。

## 剩余风险 / 未覆盖项

- 实现修复保持最小：`store_candidate` 必填校验只覆盖 `candidate_id` / `session_id` / `title` / `source_artifacts`，未对 `match_reasons` 做强制非空（FR-302b 文本未明确"必须非空"）。如后续 review 要求加强，再扩。
- supersede 关系仅写在新条目侧（新 → 旧 ID 列表），未在旧条目侧反向写"被 supersede"。这与设计 11.4 的"新旧条目关系可回读"在最薄路径上是闭合的；如后续要求双向写回，再独立任务推进。
- 未对 reviewer 的 minor finding（trace anchor docstring / 嵌套 Mock 易脆）做改写。这两条均为 minor 且不影响 code review verdict，留待 hotfix 或后续轮次。

## Pending Reviews And Gates

- `hf-test-review`（r2）
- `hf-code-review`
- `hf-traceability-review`
- `hf-regression-gate`
- `hf-completion-gate`

## Next Action Or Recommended Skill

- `hf-test-review`（r2 复审本轮回流修订）
