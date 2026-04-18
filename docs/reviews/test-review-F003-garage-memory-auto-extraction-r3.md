# Test Review (r3) — F003 Garage Memory 自动知识提取与经验推荐

- 评审范围: F003 code-review r1（结论 = 需修改）回流后新增/调整的测试质量；并复检 r2 通过基线（off-switch / supersede / abandon / truncation / FR-302b）在 r1 follow-up 之上是否仍成立
- Review skill: `hf-test-review`
- Review 轮次: r3（增量轮，r2 = 通过；本轮针对 +8 fresh-evidence 测试）
- 评审者: cursor cloud agent (auto mode, reviewer subagent)
- 日期: 2026-04-18
- Worktree branch: `cursor/f003-quality-chain-3d5f`
- Workspace isolation: `in-place`
- 关联工件:
  - 上游回修来源: `docs/reviews/code-review-F003-garage-memory-auto-extraction.md`
  - 本轮回流交接块: `docs/verification/F003-code-review-r1-handoff.md`
  - 上一轮 review: `docs/reviews/test-review-F003-garage-memory-auto-extraction-r2.md`
  - r1 回修交接块: `docs/verification/F003-test-review-r1-handoff.md`
  - T1 实现交接块: `docs/verification/F003-T1-implementation-handoff.md`
  - 任务计划: `docs/tasks/2026-04-18-garage-memory-auto-extraction-tasks.md`
  - 设计: `docs/designs/2026-04-18-garage-memory-auto-extraction-design.md`
  - 规格: `docs/features/F003-garage-memory-auto-extraction.md`
  - 进度: `task-progress.md`
- 评审测试资产（本轮新增/更新部分为重点）:
  - `tests/memory/test_extraction_orchestrator.py`（+3 fresh）
  - `tests/memory/test_publisher.py`（+3 fresh，1 update）
  - `tests/memory/test_candidate_store.py`（r2 基线，复检）
  - `tests/memory/test_recommendation_service.py`（r2 基线，复检）
  - `tests/runtime/test_session_manager.py`（r2 基线，复检：off-switch）
  - `tests/runtime/test_skill_executor.py`（r2 基线，复检）
  - `tests/integration/test_e2e_workflow.py`（r2 基线，复检）
  - `tests/test_cli.py`（+2 fresh）
- 评审实现资产:
  - `src/garage_os/memory/extraction_orchestrator.py`
  - `src/garage_os/memory/publisher.py`
  - `src/garage_os/cli.py`
  - `src/garage_os/runtime/session_manager.py`
- 当次 GREEN 证据（reviewer 复跑）: `pytest tests/ -q` → `384 passed in 24.71s`（r2 基线 376 → r3 基线 384，+8 新测试，全套零回归；与父会话承诺一致）

## 结论

通过

code-review r1 列出的 3 项 important（CR1: `experience_summary` 抛 `KeyError`；CR2: 自动提取候选缺 `source_evidence_anchors`；CR2/CR3: CLI 静默 supersede / 缺 abandon 入面）+ 1 项 minor（CR3: FR-307 错误未持久化）在本轮以 8 条 fresh-evidence 测试 + 1 条 supersede 测试显式化策略参数的方式全部闭合，并辅以一条 orchestrator → publisher 的 contract test 把"自动产出形状 → 发布字段完整性"的契约面正式锁住。r2 已通过的关键覆盖（off-switch、supersede 关系、abandon 三类候选、truncation/`truncated_count`、FR-302b 必填校验）在本轮 `pytest tests/ -q` 全套 384 passed 中可重现，无回归。3 项关键维度（TT1/TT3/TT5）均 ≥7/10，6 维度全部 ≥7/10，可放行进入 `hf-code-review` r2。

## 多维评分（0-10，括号内为 r2 → r3 变化）

| 维度 | r3 评分 | 说明 |
|------|---------|------|
| `TT1` fail-first 有效性 | 8 (7 → 8) | r1 follow-up 交接块 `docs/verification/F003-code-review-r1-handoff.md` 给出 8 条新测试的首次失败摘要：`AssertionError: ... is missing source_evidence_anchors` / `AssertionError: experience_summary candidate missing field 'task_type'` / `RuntimeError: synthetic extraction failure`（被吸收前）/ `KeyError: 'task_type'` / `Failed: DID NOT RAISE <class 'ValueError'>` / `TypeError: ... unexpected keyword argument 'conflict_strategy'` / `assert 0 == 1` / `SystemExit: 2`。每条 RED 都直接对应 r1 reviewer 标注的代码层缺陷，确属当次会话产生的"先红后绿"，不是天生绿色。GREEN 摘要为 `23 passed in 0.35s`（模块子集）+ 全套 `384 passed`。 |
| `TT2` 行为/验收映射 | 8 (7 → 8) | 新测试 docstring 全部回指到对应 FR / 设计章节：`FR-302b / design §11.6`、`FR-304`、`FR-307`、`T6 acceptance`、`CR1/CR2`。`test_publish_orchestrator_output_end_to_end` 的 docstring 直接标注 `(CR1/CR2)`，便于 traceability review 冷读。 |
| `TT3` 风险覆盖 | 9 (8 → 9) | r1 reviewer 标注的三个核心风险面（`experience_summary` 字段契约漂移 / 自动提取缺锚点 / FR-304 静默 supersede + 缺 abandon 入面）均以 happy + negative 双向覆盖；FR-307 错误持久化新增 negative 路径覆盖；publisher 端 conflict_strategy 三选一（supersede / coexist / abandon）的关系回写差异都被显式断言。 |
| `TT4` 测试设计质量 | 8 (8 → 8) | 全部新测试沿用真 `FileStorage` + `tmp_path`，断言落在持久化的行为结果（`KnowledgeEntry.source_evidence_anchor`、`ExperienceRecord.source_evidence_anchors`、`KnowledgeEntry.related_decisions` 是否含 supersede ID、`stored_batch["evaluation_summary"] == "extraction_failed"`、CLI exit code + stdout 文本、磁盘 `decisions/*.md` 文件清单），而不是 mock 调用细节。`test_extraction_failure_writes_error_batch` 用 `monkeypatch` 注入 `_generate_candidates` 失败属白盒手法，但这是 FR-307 异常吸收路径在测试层唯一可控的入口，符合 mock 仅用于真实边界的原则。`test_publish_orchestrator_output_end_to_end` 是设计明确推荐的 contract test 形态（用 orchestrator 真实输出喂 publisher），正面回应了 r1 reviewer "publisher 与 orchestrator 间没有契约级合约测试" 的判断。 |
| `TT5` 新鲜证据完整性 | 8 (7 → 8) | `docs/verification/F003-code-review-r1-handoff.md` 同时给出 RED（首次失败摘要）+ GREEN（`23 passed` 子集 + `384 passed` 全套）+ 与上一轮种子的差异说明（"在原种子之上新增 contract 级测试"）+ 剩余风险列表（finding 5 / abandon 与 accept --strategy=abandon 语义重叠 / session 侧 logger 兜底）。reviewer 当次会话独立复跑 `pytest tests/ -q` → `384 passed in 24.71s`，与交接块声明完全一致，证据可冷读、可重现。 |
| `TT6` 下游就绪度 | 9 (8 → 9) | 新增的 contract test 把 publisher / orchestrator 之间的字段契约面锁住，配合 CLI accept 强制 `--strategy` + abandon 入面，`hf-code-review` r2 已经具备直接判断"四类候选闭环 + FR-304 用户主导 + FR-307 文件级证据"的测试基线，不再有会污染 code review 的明显测试缺口。 |

> 关键维度 TT1/TT3/TT5 均 ≥6/10，按 `references/review-checklist.md` 评分辅助规则可返回 `通过`。

## code-review r1 → 本轮新测试闭合矩阵

| code-review r1 finding | severity / rule_id | 闭合证据 | 关键测试 / 断言 |
|------------------------|--------------------|----------|------------------|
| F1: `experience_summary` 自动候选喂给 publisher 时抛 `KeyError: 'task_type'` | important / CR1, CR3 | **关闭** | `tests/memory/test_extraction_orchestrator.py::test_extract_emits_complete_experience_summary_candidate`（断言 `task_type / domain / problem_domain / outcome / duration_seconds` 五个字段在自动产出 candidate 中全部存在）+ `tests/memory/test_publisher.py::test_publish_orchestrator_output_end_to_end`（断言 orchestrator 真实产物全部 `published_id is not None`，`experience_records[*].source_evidence_anchors` 非空）；publisher 侧 `_to_experience_record` / `_to_knowledge_entry` 已改为 `.get()` + default，无裸 `KeyError` 路径 |
| F2: 自动提取候选未携带 `source_evidence_anchors`，`KnowledgeEntry.source_evidence_anchor=None`，违反设计 §11.6 / FR-302b | important / CR2 | **关闭** | `tests/memory/test_extraction_orchestrator.py::test_extract_attaches_source_evidence_anchors`（遍历 `memory/candidates/items/*.md`，断言每个候选 markdown 都含 `source_evidence_anchors`）+ contract test 中 `entry.source_evidence_anchor is not None` 与 `entry.confirmation_ref is not None` 双重断言；orchestrator `_build_anchor` 对 `artifact / metadata_tags / problem_domain` 三类 signal 都构造了自描述 anchor |
| F3: CLI accept 路径绕过 FR-304 三选一，且没有 `abandon` 入面 | important / CR2, CR3 | **关闭** | `tests/test_cli.py::TestMemoryReviewCommand::test_memory_review_accept_requires_strategy_when_conflict_exists`（已有同名 decision 时 `garage memory review --action accept` 必须以 `exit 1` + 提示文本 `--strategy` 中止）+ `tests/test_cli.py::TestMemoryReviewCommand::test_memory_review_abandon_skips_publication`（`--action abandon` 直接把候选置 `abandoned` 且 `decisions/*.md` 为空清单）+ `tests/memory/test_publisher.py::test_publish_requires_explicit_strategy_when_conflict_detected`（publisher 层 `pytest.raises(ValueError, match="conflict_strategy")`）+ `tests/memory/test_publisher.py::test_publish_coexist_does_not_record_supersede_relation`（coexist 不写 `related_decisions`）+ 调整后的 `test_publish_supersede_records_relation_to_existing_entries`（显式传 `conflict_strategy="supersede"`，与新参数面对齐） |
| F6: `_trigger_memory_extraction` 失败仅 `logger.warning`，FR-307 错误未在文件层留痕 | minor / CR3 | **关闭（在 orchestrator 层落盘）** | `tests/memory/test_extraction_orchestrator.py::test_extraction_failure_writes_error_batch`（用 `monkeypatch` 注入 `_generate_candidates` 抛 `RuntimeError("synthetic extraction failure")`，断言 `summary["evaluation_summary"] == "extraction_failed"`、`metadata.error` 含异常字符串、磁盘上的 batch 也持有同一 `evaluation_summary`）。session 侧仍走 `logger.warning`，但 batch 文件已有持久化错误证据，符合 FR-307 "保存错误摘要、时间和关联 session" 的最小可机器读取约束 |

## r2 已通过覆盖在本轮的存活性复检

| r2 已通过覆盖 | 当前位置 | 复检结果 |
|---------------|----------|----------|
| 关闭分支：archive 不触发 extraction | `tests/runtime/test_session_manager.py::test_archive_session_skips_memory_when_extraction_disabled` | 全套 `pytest -q` 通过；行为契约未受 r1 follow-up 影响 |
| 关闭分支：CLI run 不调用 RecommendationService | `tests/test_cli.py::TestRunCommand::test_run_skips_recommendation_when_disabled` | 通过 |
| supersede 关系回写 | `tests/memory/test_publisher.py::test_publish_supersede_records_relation_to_existing_entries` | 通过；本轮已显式传 `conflict_strategy="supersede"`，对齐新接口面，未削弱断言 |
| abandon 跳过 decision 与 experience_summary | `tests/memory/test_publisher.py::test_publish_abandon_skips_publication` / `test_publish_abandon_skips_experience_summary` | 通过；publisher 入口 `if action in {"reject", "defer", "batch_reject", "abandon"}` 早返回，与 r2 行为一致 |
| Truncation + `truncated_count` | `tests/memory/test_extraction_orchestrator.py::test_extract_truncates_to_max_pending_and_records_truncated_count` | 通过；`_generate_candidates` 现返回 `(candidates, truncated_count)`，magic 数仍为 `MAX_PENDING_CANDIDATES=5` |
| FR-302b 必填校验 | `tests/memory/test_candidate_store.py::test_reject_candidate_missing_required_metadata` | 通过；`store_candidate` 校验链未被 r1 follow-up 弱化 |

## 发现项

- `[minor][LLM-FIXABLE][TT4]` `tests/memory/test_extraction_orchestrator.py::test_extraction_failure_writes_error_batch` 用 `monkeypatch.setattr(MemoryExtractionOrchestrator, "_generate_candidates", _boom)` 替换私有方法触发 FR-307 异常路径，属于白盒手法。FR-307 的 happy path 是真实异常（OOM / disk full / 第三方组件抛错），test 选择 monkeypatch 是为了测试可控性。建议未来在 `extraction_orchestrator` 内部抽象出更小的失败注入入口（例如把候选生成异常通过策略对象触发），让此用例可以走真实公共入口。**不阻塞 r3**。
- `[minor][LLM-FIXABLE][TT4]` `src/garage_os/memory/extraction_orchestrator.py:68` 的 `except Exception as exc:` 仍带 `# pragma: no cover` 注释，但 `test_extraction_failure_writes_error_batch` 已稳定覆盖该分支，注释已成 stale。属于实现层小幅清理，与测试质量无关；建议在 code-review r2 顺手摘掉 pragma。**不阻塞 r3**，记录为 code-review r2 视野内的 minor。
- `[minor][LLM-FIXABLE][TT3]` `test_publish_orchestrator_output_end_to_end` 对 `experience_records[*].source_evidence_anchors` 仅断言"非空"，未进一步断言 `kind=session_metadata` 或 `ref` 能反向解析回 `sessions/archived/<session_id>/session.json`。当前断言已足够暴露 r1 finding 1/2 复发，但若后续 traceability review 要求"已发布数据可被回读到原 session/anchor"做更严格机器校验，此用例可再加一条断言。**不阻塞 r3**。
- `[minor][LLM-FIXABLE][TA4]` r2 沿用的"F003 关键测试 docstring 缺 FR / 设计章节 trace anchor"在本轮新增测试中已基本补齐（`FR-302b / design §11.6 / FR-304 / FR-307 / CR1/CR2 / T6 acceptance` 都出现在 docstring 中），存量旧测试仍未补全。沿用 r1/r2 判断：不阻塞，作为 hotfix 候选。
- `[minor][LLM-FIXABLE][TT4]` r2 沿用的 `test_execute_skill_uses_recommendation_service_when_available` 嵌套属性 Mock 仍未替换为真 `SessionMetadata` / `SessionContext`。本轮未触碰相关代码路径，沿用 r1/r2 判断：不阻塞。
- `[minor][USER-INPUT][TT3]` code-review r1 finding 5（publisher 用 `candidate_id` 直接当 `KnowledgeEntry.id`，重复 accept 静默覆盖）属于 ID 体系层的设计层修补，r1 follow-up 交接块明确"超出 1-2 轮可消化范围"显式延后。本轮没有为该缺口补"重复 accept" negative 测试。建议在 code-review r2 / traceability review 期间正式裁决"接受现状 / 立独立 hotfix"。**不阻塞 r3**，作为后续路由提示。

## 缺失或薄弱项

- CLI `--action abandon` 与 `--action accept --strategy=abandon` 在语义上重叠（前者无视冲突探测、后者仅在冲突时生效），当前 CLI 测试只覆盖前者，未单独验证后者路径下候选状态被置为 `abandoned`（`cli.py` line 520-521 已实现）。如果后续 traceability 要求双入口都有 fresh evidence，可补一条 minimal 用例。
- `test_extraction_failure_writes_error_batch` 没有断言 batch 在磁盘上的 `metadata.error` 也包含异常类型前缀（仅断言 summary dict 中包含），其实 source 已经写入 `f"{type(exc).__name__}: {exc}"`，更严格的断言能锁住 FR-307 错误摘要的"类型 + 消息"格式。
- F003 端到端 `tests/integration/test_e2e_workflow.py::test_memory_pipeline_e2e_flow` 的 archived session 仍不带 `problem_domain`，因此 E2E 集成路径不会落到 `experience_summary` 分支。本轮通过 `test_publish_orchestrator_output_end_to_end` 在 publisher 单测层补齐了"orchestrator 自动产出 → publisher 落库"的契约证据；如后续 traceability review 要求 E2E 必须覆盖第四类候选，可单独扩展 integration 用例。

## 关于路由判断

- 实现交接块（T1 + r1 回流合并 + r1 follow-up）齐全，可冷读，触碰工件可逐行定位
- 任务计划已批准（`docs/approvals/F003-tasks-approval.md`）；本轮 r1 follow-up 仅闭合 LLM-FIXABLE finding，未引入新行为契约（仅显式化 FR-302b / FR-304 / §11.6 / FR-307 的硬约束面），不需要新增 `test-design-approval` 或重走 `hf-tasks-review`
- 测试资产齐全、可执行，全套 `pytest tests/ -q` → `384 passed in 24.71s`
- `profile=full` / `stage=hf-test-review (r3)` 与 `task-progress.md` 状态一致

不构成 stage / route / profile / 上游证据冲突，**不需要 reroute via router**。下一步直接进入 `hf-code-review` r2。

## 下一步

- `hf-code-review`（r2）：评审 r1 follow-up 后的实现质量。重点关注：
  1. `MemoryExtractionOrchestrator._generate_candidates` 异常处理分支的 `# pragma: no cover` 已 stale，是否顺手清理；
  2. `KnowledgePublisher.publish_candidate` 在 `similar_entries` 为空时仍会忽略错误传入的 `conflict_strategy`（不会校验 `VALID_CONFLICT_STRATEGIES`），是否需要在无冲突路径上也做 strict 校验；
  3. `cli.py` `accept` / `edit_accept` 与 `abandon` 的状态转换矩阵（`new_status` 表）是否完整覆盖 `--strategy=abandon` 的特殊收束；
  4. code-review r1 finding 5（`candidate_id` 复用）是否需要在本轮立 hotfix，还是延后到 ID 体系演进。
- 通过后进入 `hf-traceability-review`。

## 结构化返回（供父会话路由）

```json
{
  "conclusion": "通过",
  "next_action_or_recommended_skill": "hf-code-review",
  "record_path": "docs/reviews/test-review-F003-garage-memory-auto-extraction-r3.md",
  "key_findings": [
    "[important→关闭][TT1/TT3] CR1 experience_summary KeyError：test_extract_emits_complete_experience_summary_candidate + contract test test_publish_orchestrator_output_end_to_end 双重锁定字段契约",
    "[important→关闭][TT3] CR2 source_evidence_anchors 缺失：test_extract_attaches_source_evidence_anchors 直接断言磁盘候选含 anchor，contract test 断言已发布 entry.source_evidence_anchor 非空",
    "[important→关闭][TT3] CR2/CR3 FR-304 三选一 + abandon 入面：publisher test_publish_requires_explicit_strategy_when_conflict_detected / coexist / supersede 三向覆盖；CLI test_memory_review_accept_requires_strategy_when_conflict_exists 与 test_memory_review_abandon_skips_publication 显式覆盖 surface 行为",
    "[minor→关闭][TT3] FR-307 错误持久化：test_extraction_failure_writes_error_batch 断言 evaluation_summary=extraction_failed 且 metadata.error 留痕",
    "[r2 持守] off-switch / supersede 关系 / abandon decision+experience_summary / truncated_count / FR-302b 必填校验：全套 384 passed 中可重现，零回归",
    "[minor 维持] FR-307 异常注入用 monkeypatch 私有方法 + extraction_failed 分支 # pragma: no cover 已 stale + experience_records anchor 仅断非空 + finding 5 ID 体系延后：均不阻塞 r3，记入 code-review r2 视野"
  ],
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "finding_breakdown": [
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TT4",
      "summary": "test_extraction_failure_writes_error_batch 通过 monkeypatch 私有方法注入异常，建议未来抽象更小的失败注入入口"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TT4",
      "summary": "extraction_orchestrator.py 异常分支 # pragma: no cover 已 stale，建议 code-review r2 顺手清理"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TT3",
      "summary": "test_publish_orchestrator_output_end_to_end 对 experience_records[*].source_evidence_anchors 仅断言非空，未断言 anchor.kind/ref 可解析"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TA4",
      "summary": "存量旧测试 docstring 仍缺 FR/设计章节 trace anchor（r1/r2 minor 维持）"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TT4",
      "summary": "test_execute_skill_uses_recommendation_service_when_available 嵌套属性 Mock 仍易脆（r1/r2 minor 维持）"
    },
    {
      "severity": "minor",
      "classification": "USER-INPUT",
      "rule_id": "TT3",
      "summary": "code-review r1 finding 5（publisher candidate_id 当 KnowledgeEntry.id，重复 accept 静默覆盖）本轮无 negative 测试覆盖，按 r1 follow-up 显式延后，建议 code-review r2 / traceability 期间裁决"
    }
  ]
}
```
