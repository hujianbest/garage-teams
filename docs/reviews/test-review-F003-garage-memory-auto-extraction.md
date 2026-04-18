# Test Review — F003 Garage Memory 自动知识提取与经验推荐

- 评审范围: F003 全量实现批次（T1-T9）的测试质量
- Review skill: `hf-test-review`
- 评审者: cursor cloud agent (auto mode)
- 日期: 2026-04-18
- 关联工件:
  - 实现交接块: `docs/verification/F003-T1-implementation-handoff.md`
  - 任务计划: `docs/tasks/2026-04-18-garage-memory-auto-extraction-tasks.md`
  - 设计: `docs/designs/2026-04-18-garage-memory-auto-extraction-design.md`
  - 规格: `docs/features/F003-garage-memory-auto-extraction.md`
  - 测试设计批准（仅 T1）: `docs/approvals/F003-T1-test-design-approval.md`
- 评审测试资产:
  - `tests/memory/test_candidate_store.py`
  - `tests/memory/test_extraction_orchestrator.py`
  - `tests/memory/test_publisher.py`
  - `tests/memory/test_recommendation_service.py`
  - `tests/runtime/test_session_manager.py`
  - `tests/runtime/test_skill_executor.py`
  - `tests/integration/test_e2e_workflow.py`
  - `tests/test_cli.py`
  - `tests/knowledge/test_knowledge_store.py`
  - `tests/knowledge/test_experience_index.py`
  - `tests/knowledge/test_integration.py`
- 当次 GREEN 证据: `pytest tests/memory/ tests/runtime/test_session_manager.py tests/runtime/test_skill_executor.py tests/integration/test_e2e_workflow.py tests/test_cli.py tests/knowledge/ -q` → `130 passed in 16.07s`

## 结论

需修改

测试覆盖了 F003 主链的 happy path、几条核心降级分支与 E2E 闭环，整体已经接近 code-review 就绪，但仍存在 4 项 important 与 1 项 critical 缺口，集中在：(1) T2-T9 缺少冷读可核实的 fail-first / fresh evidence；(2) T4 开关契约关闭分支零覆盖；(3) T6 冲突策略只测了探测，没有覆盖 supersede 关系回写与 abandon 发布跳过；(4) 候选生成 truncation 数字未被任何测试断言；(5) FR-302b 候选元信息完整性校验缺失。建议回到 `hf-test-driven-dev` 做一轮定向回修后再走 code review。

## 多维评分（0-10）

| 维度 | 评分 | 说明 |
|------|------|------|
| `TT1` fail-first 有效性 | 5 | 仅 T1 有 RED/GREEN handoff；T2-T9 没有提交任何"先失败再通过"的可核实证据 |
| `TT2` 行为/验收映射 | 7 | 测试种子大体可以回指到 FR-301/FR-302a/FR-303/FR-303a/FR-305/FR-307 与设计 9.1A、11.4，但 docstring/命名层面没有显式 trace anchor |
| `TT3` 风险覆盖 | 5 | 缺 T4 关闭分支、T6 supersede/abandon 完整路径、truncation/截断断言、FR-302b 必填校验 |
| `TT4` 测试设计质量 | 8 | 多数用真 `FileStorage` + `tmp_path`，mock 限定在 host adapter / recommendation_service 等真实边界，独立可重复 |
| `TT5` 新鲜证据完整性 | 5 | 仅 T1 handoff 有当次 RED/GREEN 证据；T2-T9 缺乏可冷读的 fresh evidence，本次 GREEN 仅证明"现在绿"，无法证明"曾经红" |
| `TT6` 下游就绪度 | 7 | E2E 闭环 + 单元覆盖足以让 code review 启动，但 T4/T6 的核心契约缺测会拖累 code-review 信号清晰度 |

> 关键维度 `TT1`、`TT3`、`TT5` 低于 6/10，按 `references/review-checklist.md` 的评分辅助规则不可返回 `通过`。

## 发现项

### `[critical][LLM-FIXABLE][TT5]` T2-T9 缺少 fresh RED/GREEN evidence，handoff 仅覆盖 T1
- `docs/verification/F003-T1-implementation-handoff.md` 只记录 T1 的首次失败摘要 (`ModuleNotFoundError: No module named 'garage_os.memory'`) 与 GREEN 摘要 (`3 passed in 0.07s`)。T2-T9 实现已落盘、`task-progress.md` 已标 done，但仓库内没有任何 fresh evidence 工件证明 `tests/memory/test_extraction_orchestrator.py`、`tests/memory/test_publisher.py`、`tests/memory/test_recommendation_service.py`、`tests/runtime/test_session_manager.py::test_archive_session_creates_memory_batch_when_enabled`、`tests/runtime/test_session_manager.py::test_archive_session_ignores_memory_errors`、`tests/runtime/test_skill_executor.py::test_execute_skill_uses_recommendation_service_when_available`、`tests/integration/test_e2e_workflow.py::test_memory_pipeline_e2e_flow`、`tests/test_cli.py::TestMemoryReviewCommand::*` 这些用例曾经红、现在绿。
- 当前 `pytest ... -q` 只能证明"目前绿"。在测试代码与生产代码同 PR 的情况下，"目前绿"等价于"测试与实现一起合上去就绿了"，无法满足 TT1/TT5。
- 整改建议：补一份 T2-T9 的实现交接块或验证记录，至少为每个非 T1 任务给出 (a) 当次会话内的失败摘要、(b) 通过摘要、(c) 与任务种子的 trace 对应。

### `[important][LLM-FIXABLE][TT3][TA2]` T4 配置开关的关闭分支零覆盖
- 任务 T4 验收明确要求："extraction 关闭时，archive 后不触发候选提取且 session 主链不受影响" / "recommendation 关闭时，任务开始前不触发推荐查询" / "两个开关关闭时现有 session / CLI 主链仍工作"。
- 仓库 grep 结果（`extraction_enabled.*False|recommendation_enabled.*False`）为零。`tests/runtime/test_session_manager.py` 只测了 `extraction_enabled=True` 的两条路径；`tests/test_cli.py::test_run_shows_recommendation_summary_when_enabled` 只测了 `recommendation_enabled=True` 的路径。
- 后果：`session_manager.archive_session` 的 `if not orchestrator.is_extraction_enabled(): return` 短路与 `cli` 中 `if memory_config["recommendation_enabled"]` 的关闭分支属于"未被任何测试触达"的 critical 主链路径，code review 无法依靠现有测试判断该 acceptance 是否真的成立。
- 整改建议：补两个最小测试，分别断言 (a) `extraction_enabled=False` 时 archive 之后 `memory/candidates/batches/` 为空，(b) `recommendation_enabled=False` 时 `garage run` 不打印 `Recommendations:` 段。

### `[important][LLM-FIXABLE][TT3][TA2]` T6 冲突探测只覆盖了 strategy 判定，没覆盖 supersede 关系回写与 abandon 发布跳过
- 任务 T6 验收要求："选择 supersede 时能写回新旧条目关系" / "选择 abandon 时不发布正式知识"。
- 实际只有 `tests/memory/test_publisher.py::test_detect_conflicts_returns_supersede_for_similar_knowledge` 验证 `detect_conflicts` 返回 `strategy == "supersede"` + `similar_entries` 列表非空，但没有断言 publisher 真的把新旧关系写到正式知识条目上。
- `KnowledgePublisher.publish_candidate` 中 `action == "abandon"` 的早返回分支没有任何测试触达。
- 整改建议：补两个测试 — (a) 当存在相似 active knowledge 且 action=`accept` 时，新发布条目带回 supersede 关系字段（可 piggyback `front_matter` / `related_decisions`）；(b) `action="abandon"` 在存在相似条目时返回 `published_id is None` 且不写入 `KnowledgeStore`。

### `[important][LLM-FIXABLE][TT3]` 候选 truncation 行为没有任何断言
- 设计 11.2 与 FR-303a 要求批次 schema 含 `truncated_count`，且当超过 5 条候选时只保留 top-5 并把被截断数量回写。`MemoryExtractionOrchestrator._generate_candidates` 用 `[: CandidateStore.MAX_PENDING_CANDIDATES]` 硬截断，但 `_build_summary` 永远写 `truncated_count=0`。
- `tests/memory/test_candidate_store.py::test_reject_batch_over_pending_limit` 只测了"显式构造 6 条 id 时存储层拒绝"，未覆盖"orchestrator 在 6+ 个 signals 下应裁剪到 5 + 写 truncated_count=N"这一真实业务路径。
- 整改建议：构造一个 6+ signals 的 archived session，断言生成的 batch `len(candidate_ids) == 5` 且 `truncated_count >= 1`；同时在 orchestrator 实现里把 `truncated_count = max(0, len(generated_before_cap) - MAX_PENDING_CANDIDATES)` 写回（实现修复属于 hf-test-driven-dev，但测试缺口属于本评审）。

### `[important][LLM-FIXABLE][TT3][TA4]` FR-302b 候选必填元信息没有 negative 测试
- FR-302b 的 acceptance："候选缺少必需元信息时，系统校验该候选不能进入待确认队列"。
- `CandidateStore.store_candidate` 仅校验 `candidate_type ∈ ALLOWED_CANDIDATE_TYPES`，对 `session_id` / `source_artifacts` / `match_reasons` / `title` 等 schema-mandatory 字段不做拒绝；测试也没有任何 negative case 守住这一约束。
- 整改建议：补一个 `test_reject_candidate_missing_required_metadata`，断言缺 `session_id` 或 `source_artifacts` 时 `store_candidate` 抛错；并在实现层补一个轻量校验（属 hf-test-driven-dev 范畴）。

### `[minor][LLM-FIXABLE][TT2][TA4]` 测试 docstring 缺少显式 FR / 设计章节回指
- `tests/memory/test_*` / `tests/runtime/test_session_manager.py::test_archive_session_*memory*` 等关键 F003 用例 docstring 描述行为但未引用 FR-301..FR-307 / 设计 9.1A / 11.4 / 9.8 中任何 trace anchor。
- 这不阻塞 code review，但日后追溯成本会上升。建议在 docstring 顶部加一行类似 `Covers FR-303a 5-cap; design §9.2.` 的 trace 行。

### `[minor][LLM-FIXABLE][TT4]` `test_execute_skill_uses_recommendation_service_when_available` 链式 Mock attribute 易脆
- `session_manager.restore_session.return_value = Mock(topic=..., context=Mock(metadata={...}))` 是嵌套属性 Mock，未来 `SessionMetadata.context.metadata` 字段名一旦重构容易失真而不报错。
- 建议直接构造一个真 `SessionMetadata` / `SessionContext`（项目内已有 dataclass）来替代嵌套 Mock，提升对结构变化的敏感度。

## 缺失或薄弱项

- T2-T9 实现交接块缺位（建议在 `docs/verification/` 下补一份合并后的 `F003-batch-implementation-handoff.md`，列出每个非 T1 任务的 RED/GREEN 摘要）。
- 仅 T1 有 `test-design-approval`。从 hf-test-review 角度这本身是上游审批不完整的信号，但**不属于 router blocker**：测试文件本身齐全、可冷读、可执行，本评审在测试质量层面已能形成 verdict。建议在 `hf-test-driven-dev` 回修轮里顺便由父会话补 T2-T9 的 testDesignApproval（或在 handoff 里显式标注 auto-mode 下测试设计已随实现合并批准）。
- 缺失的 important findings（T4 关闭分支、T6 supersede/abandon、truncation、FR-302b 校验）应在同一轮 hf-test-driven-dev 内集中回修，避免出现"再次绕回 test review"的多轮反复。

## 关于路由判断

虽然存在 T2-T9 缺 test-design-approval 的上游薄弱，但：

1. 实现交接块（T1）存在；
2. 任务计划已批准（`docs/approvals/F003-tasks-approval.md`）；
3. 测试资产已落盘且可执行；
4. profile=full / stage=hf-test-review 与 task-progress 一致；

不构成 stage / route / profile 冲突，**不需要 reroute via router**。下一步保持在 `hf-test-driven-dev` 回修上述 important findings + 补 T2-T9 fresh evidence 即可。

## 下一步

- `hf-test-driven-dev`：在同一轮内：
  1. 为 T2-T9 补 fresh RED/GREEN 证据（先 revert + 重跑得到失败摘要，或在 implementation-handoff 中给出可冷读的会话内证据）；
  2. 补 T4 关闭分支双向测试；
  3. 补 T6 supersede 关系回写测试 + abandon 发布跳过测试；
  4. 补 orchestrator 截断 + `truncated_count` 测试与最小实现修复；
  5. 补 FR-302b 必填字段 negative 测试。
- 完成后回 `hf-test-review` 走 r2 评审。

## 结构化返回（供父会话路由）

```json
{
  "conclusion": "需修改",
  "next_action_or_recommended_skill": "hf-test-driven-dev",
  "record_path": "docs/reviews/test-review-F003-garage-memory-auto-extraction.md",
  "key_findings": [
    "[critical][LLM-FIXABLE][TT5] T2-T9 缺 fresh RED/GREEN evidence，仅 T1 有 implementation-handoff",
    "[important][LLM-FIXABLE][TT3] T4 extraction_enabled / recommendation_enabled 关闭分支零测试覆盖",
    "[important][LLM-FIXABLE][TT3] T6 冲突仅测 strategy 判定，缺 supersede 关系回写与 abandon 发布跳过测试",
    "[important][LLM-FIXABLE][TT3] orchestrator 候选 truncation 与 batch.truncated_count 字段无任何断言",
    "[important][LLM-FIXABLE][TT3] FR-302b 候选必填元信息缺 negative 校验测试"
  ],
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "finding_breakdown": [
    {
      "severity": "critical",
      "classification": "LLM-FIXABLE",
      "rule_id": "TT5",
      "summary": "T2-T9 缺 fresh RED/GREEN evidence，仅 T1 有 implementation-handoff"
    },
    {
      "severity": "important",
      "classification": "LLM-FIXABLE",
      "rule_id": "TT3",
      "summary": "T4 extraction_enabled / recommendation_enabled 关闭分支零覆盖"
    },
    {
      "severity": "important",
      "classification": "LLM-FIXABLE",
      "rule_id": "TT3",
      "summary": "T6 冲突仅测 strategy 判定，缺 supersede 回写与 abandon 跳过测试"
    },
    {
      "severity": "important",
      "classification": "LLM-FIXABLE",
      "rule_id": "TT3",
      "summary": "orchestrator 候选截断与 batch.truncated_count 无断言"
    },
    {
      "severity": "important",
      "classification": "LLM-FIXABLE",
      "rule_id": "TT3",
      "summary": "FR-302b 候选必填元信息缺 negative 校验测试"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TT2",
      "summary": "F003 关键测试 docstring 缺 FR/设计章节 trace anchor"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TT4",
      "summary": "test_execute_skill_uses_recommendation_service_when_available 嵌套属性 Mock 易脆"
    }
  ]
}
```
