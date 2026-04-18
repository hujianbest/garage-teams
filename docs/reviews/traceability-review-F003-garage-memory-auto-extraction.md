# Traceability Review — F003 Garage Memory 自动知识提取与经验推荐

- 评审范围: F003 spec → design → tasks → implementation → tests → verification → review/status 全链路证据追溯
- Review skill: `hf-traceability-review`
- 评审者: cursor cloud agent (auto mode, reviewer subagent)
- 日期: 2026-04-18
- Worktree branch: `cursor/f003-quality-chain-3d5f`
- Workspace isolation: `in-place`
- 上游已通过:
  - `docs/reviews/code-review-F003-garage-memory-auto-extraction-r2.md`（code review r2 = 通过）
  - `docs/reviews/test-review-F003-garage-memory-auto-extraction-r3.md`（test review r3 = 通过）
- 关联工件:
  - 规格 `docs/features/F003-garage-memory-auto-extraction.md`（已批准）
  - 设计 `docs/designs/2026-04-18-garage-memory-auto-extraction-design.md`（已批准）
  - 任务计划 `docs/tasks/2026-04-18-garage-memory-auto-extraction-tasks.md`（已批准；T1-T9 全部 done）
  - Approvals: `F003-spec-approval.md` / `F003-design-approval.md` / `F003-tasks-approval.md` / `F003-T1-test-design-approval.md`
  - 实现交接块: `F003-T1-implementation-handoff.md` / `F003-test-review-r1-handoff.md` / `F003-code-review-r1-handoff.md`
  - 历史 review: spec r1+r2 / design r1+r2 / tasks r1+r2+r3 / test-review r1+r2+r3 / code-review r1+r2
  - 进度: `task-progress.md`
  - 平台默认配置: `.garage/config/platform.json`
- 当次回归证据（reviewer 独立复跑）: `pytest tests/ -q` → `384 passed in 24.62s`，与 code-review r2 / test-review r3 报告完全一致

## 评审范围

- topic / 任务: F003 — Garage Memory（自动知识提取与经验推荐）的端到端证据链可追溯性
- 相关需求: FR-301 / FR-302a / FR-302b / FR-303 / FR-303a / FR-304 / FR-305 / FR-306 / FR-307；NFR-301 / NFR-302 / NFR-303 / NFR-304；CON-301..304；ASM-301..303
- 相关设计: §2 设计驱动因素，§3 需求覆盖矩阵，§7 ADR-001..003，§8 架构视图，§9 模块职责（含 §9.1A 输入证据契约 / §9.4 ConflictDetector / §9.7 RecommendationService / §9.8 CLI canonical surface），§10 数据流，§11 接口与契约（§11.3 CandidateDraft / §11.4 KnowledgeEntry+ExperienceRecord 扩展 / §11.5 ConfirmationRecord / §11.6 不变量），§14 失败模式
- 相关任务: T1-T9（全部 done，关键路径 T1 → T2 → T5 → T8 → T9）
- 相关实现:
  - `src/garage_os/memory/{__init__.py,types.py,candidate_store.py,signal_builder?,extraction_orchestrator.py,conflict_detector.py,publisher.py,recommendation_service.py}`
  - `src/garage_os/runtime/session_manager.py`（archive 触发 + extraction 短路）
  - `src/garage_os/runtime/skill_executor.py`（推荐 context 构造 + 默认主动推荐）
  - `src/garage_os/cli.py`（`garage memory review` + `garage run` 推荐摘要）
  - `src/garage_os/types/__init__.py`（traceability 字段扩展）
  - `src/garage_os/knowledge/{knowledge_store.py,experience_index.py}`（发布态字段持久化）
- 相关测试 / 验证:
  - `tests/memory/{test_candidate_store.py,test_extraction_orchestrator.py,test_publisher.py,test_recommendation_service.py}`
  - `tests/runtime/{test_session_manager.py,test_skill_executor.py}`
  - `tests/integration/test_e2e_workflow.py::test_memory_pipeline_e2e_flow`
  - `tests/test_cli.py::TestRunCommand::*` + `TestMemoryReviewCommand::*`
  - 三份实现交接块（T1 + test-review r1 + code-review r1）
  - 5 份审批记录（spec / design / tasks / T1 test-design / 含 r1-r3 review evidence）

## 结论

通过

F003 从规格 → 设计 → 任务 → 实现 → 测试 → 验证 → review 的端到端证据链已完整闭合。9 条 FR / 4 条 NFR / 4 条 CON / 3 条 ASM 都能在设计、任务、源码、测试与 verification handoff 中找到稳定锚点；code-review r2 与 test-review r3 的两条主链均已为 384 passed 的回归基线背书；reviewer 独立复跑 `pytest tests/ -q` 复现 `384 passed in 24.62s`，与所有交接块声明的 GREEN 摘要一致。6 个 traceability 维度（TZ1-TZ6）评分全部 ≥7/10，关键维度 TZ3/TZ4/TZ6 ≥8/10。可放行进入 `hf-regression-gate`。

遗留项均为低优非阻塞条目（详见"发现项"），其中：
- code-review r1 finding 5（`KnowledgePublisher` 用 `candidate_id` 当 `KnowledgeEntry.id`）已被 `docs/verification/F003-code-review-r1-handoff.md` 与 `docs/reviews/code-review-F003-garage-memory-auto-extraction-r2.md` 显式延后，本 review 接受该延后并标记为 USER-INPUT 级 minor，不要求在进入 regression gate 前修复
- 仅 T1 有 `testDesignApproval`，T2-T9 的测试设计依靠 `docs/approvals/F003-tasks-approval.md`（任务计划第 5 节"测试设计种子" + 第 7 节"完成定义与验证策略"）+ auto-mode merge 承接，本 review 接受该收束策略

## 多维评分（0-10）

| 维度 | 评分 | 说明 |
|------|------|------|
| `TZ1` 规格 → 设计追溯 | 9 | 设计 §3 显式给出 FR/NFR ↔ 设计模块对应矩阵；FR-301..307 + NFR-301/302/304 全部能在 §9 模块职责 / §10 数据流 / §11 契约 / §14 失败模式中找到承接段 |
| `TZ2` 设计 → 任务追溯 | 9 | 任务计划 §4 给出"规格/设计锚点 → 覆盖任务"映射；§3.1/3.2/3.3 文件影响图与设计模块边界一致；§5 任务卡片均显式给出 Files / Acceptance / Verify |
| `TZ3` 任务 → 实现追溯 | 9 | T1-T9 触碰工件清单与实际 `src/garage_os/memory/` + `src/garage_os/runtime/` + `src/garage_os/cli.py` 修改完全一致；任务 done 状态有 `task-progress.md` 与三份交接块证据 |
| `TZ4` 实现 → 验证追溯 | 8 | 每条 FR 的 acceptance 至少有一个聚焦测试覆盖；T1 实现交接块 + r1 / r1-follow-up 交接块均给出 RED → GREEN 当次会话内可冷读证据；reviewer 复跑 `pytest tests/ -q` 复现 `384 passed`，与所有交接块声明的 GREEN 摘要一致；E2E `test_memory_pipeline_e2e_flow` 把"archive → extract → review → publish → recommend"主链锁住 |
| `TZ5` 漂移与回写义务 | 7 | 主要 spec/design 锚点未发生未记录漂移；CLI / publisher / orchestrator / session_manager 的关键扩展（`--strategy=`、`--action=abandon`、`conflict_strategy` 必传、`extraction_failed` batch、`source_evidence_anchors` anchor 写盘）都已分别在 r1 / r1-follow-up 交接块与 review r2 中显式声明；`KnowledgeEntry.id ← candidate_id` 弱耦合按 r1-follow-up 显式延后；`testDesignApproval` 仅 T1 一份这一治理级偏离已在 test-review r1 / r2 / r3 + tasks-approval 中显式承认，且第一版 testDesignApproval 与 tasks-approval 的范围合并属于 auto-mode 设计内行为 |
| `TZ6` 整体链路闭合 | 9 | 384 passed + 三份 handoff + 三轮 test review + 两轮 code review 形成一致基线；公开锚点（`KnowledgeEntry.source_evidence_anchor`、`ExperienceRecord.source_evidence_anchors`、`confirmation_ref`、`published_from_candidate`）在源码、front matter、JSON 文件层均可机器读取；可安全进入 regression gate |

## 链接矩阵

### Spec → Design

| Spec | Design 锚点 |
|------|-------------|
| FR-301 自动触发知识提取 | §3 表（FR-301 行）；§9.1A 输入证据最小契约（no_evidence / evaluated_no_candidate / evaluated_with_candidates）；§10.1 自动提取流程；§13.1 最薄验证路径 |
| FR-302a 四类候选 | §3 表（FR-302a 行）；§9.2 CandidateGenerator；§11.3 CandidateDraft 最小契约 |
| FR-302b 自描述与追溯 | §3 表（FR-302b 行）；§9.1A；§11.3；§11.4 KnowledgeEntry/ExperienceRecord 扩展；§11.6 不变量第 6 条 |
| FR-303 用户确认门禁 | §3 表；§9.5 CandidateReviewService；§9.6 KnowledgePublisher；§10.2 用户确认流程；§11.5 ConfirmationRecord 契约；§11.6 不变量第 1 / 4 条 |
| FR-303a 5 条上限 / 批量拒绝 / 延后 | §3 表；§9.2 / §9.3；§11.2 CandidateBatch（`truncated_count`）；§11.6 不变量第 3 条 |
| FR-304 相似知识冲突三选一 | §3 表；§9.4 ConflictDetector；§9.6 KnowledgePublisher；§9.8 CLI canonical surface |
| FR-305 主动推荐闭环 | §3 表；§9.7 RecommendationService；§10.3 主动推荐流程；§10.4 推荐触发输入构造与降级 |
| FR-306 推荐原因 match_reasons | §3 表；§9.7（`match_reasons` 输出） |
| FR-307 失败降级 | §3 表；§9.6 / §10.1 step 4-7 / §14.2 失败模式表 |
| NFR-301 全链路可追溯 | §11.4 / §11.6 不变量 |
| NFR-302 用户控制优先 | §9.5 / §9.6 / §11.6 不变量第 1 / 4 条 |
| NFR-303 Stage 2 性能 | §12（NFR 表）"性能" 行 |
| NFR-304 与 Phase 1/2 兼容 | §12 "兼容性" 行；§9.7 推荐可关闭；ADR-001/-002 |
| CON-301 Workspace-first | §11.1 新增目录契约；ADR-002 |
| CON-302 不得静默自动发布 | §9.5 / §9.6 / §11.6 不变量 |
| CON-303 契约可兼容演进 | §11.2/§11.3/§11.4/§11.5（带 `schema_version`）|
| CON-304 第一版不引入外部依赖 | §4 架构模式选择 / §11.1 |

### Design → Tasks

| Design 段 | 覆盖任务 |
|-----------|----------|
| §9.1 / §9.1A / §9.2 / §11.3 候选生成与契约 | T1 / T2 |
| §9.3 CandidateBatchStore + §11.2 truncated_count | T1 / T2 |
| §9.5 / §9.6 / §11.5 / §11.6 review/publish gate | T5 |
| §9.4 ConflictDetector + §11.6 不变量 | T6 |
| §9.7 / §10.3 / §10.4 RecommendationService + 上下文 | T4 / T8 |
| §9.8 CLI-first canonical surface | T7 / T8 |
| §10.1 archive → orchestrator + §14.2 失败模式 | T3 |
| §11.4 KnowledgeEntry / ExperienceRecord 扩展 | T5 |
| feature flag / on-off 行为 | T4 |
| 最薄端到端 §13.1 | T9 |

任务计划 §4 已显式以表格形式给出"规格 / 设计锚点 → 覆盖任务"映射，与上述结果一致；任务计划 §3.1/3.2/3.3 文件影响图也与设计模块边界一致。

### Tasks → Impl

| 任务 | 实现工件（实际触碰） |
|------|---------------------|
| T1 候选/确认存储契约 | `src/garage_os/memory/__init__.py` `types.py` `candidate_store.py` |
| T2 输入证据 + 四类候选生成 | `src/garage_os/memory/extraction_orchestrator.py`（`_build_signals` + `_generate_candidates` + `_build_anchor`）|
| T3 archive 触发 + 失败降级 | `src/garage_os/runtime/session_manager.py`（`_trigger_memory_extraction`、`archive_session` 调用点）+ `extraction_orchestrator.py` 异常归一化为 `extraction_failed` batch |
| T4 memory feature flag / 配置开关 | `extraction_orchestrator.load_memory_config` + `RecommendationService.is_enabled` + `session_manager._trigger_memory_extraction` 短路 + `cli._run` recommendation 短路 |
| T5 candidate review + publish 主链 | `src/garage_os/memory/publisher.py`（accept/edit_accept/reject/batch_reject/defer/abandon、`_to_knowledge_entry`、`_to_experience_record`、`conflict_strategy` 必传）+ `src/garage_os/types/__init__.py`（`KnowledgeEntry.source_evidence_anchor / confirmation_ref / published_from_candidate` 与 `ExperienceRecord.source_evidence_anchors / confirmation_ref / published_from_candidate`）+ `src/garage_os/knowledge/{knowledge_store.py,experience_index.py}`（front_matter / record 字段持久化）|
| T6 ConflictDetector | `src/garage_os/memory/conflict_detector.py` + publisher.py `VALID_CONFLICT_STRATEGIES` + supersede/coexist/abandon 三向行为 |
| T7 CLI canonical surface | `src/garage_os/cli.py::_memory_review` + `build_parser`（`memory review` 子命令、`--action`、`--strategy`、`--candidate-id`）|
| T8 主动推荐 + `garage run` 展示 | `src/garage_os/memory/recommendation_service.py`（`RecommendationService` + `RecommendationContextBuilder`）+ `src/garage_os/runtime/skill_executor.py`（`_build_recommendation_service` / `_recommendation_service_enabled` / `_merge_recommendation_metadata`）+ `src/garage_os/cli.py::_run`（推荐摘要打印）|
| T9 最薄 E2E + 关闭分支兼容性 | `tests/integration/test_e2e_workflow.py::test_memory_pipeline_e2e_flow` + 关闭分支测试已合并到 T3/T4 用例 |

### Impl → Test / Verification

| FR / 设计锚点 | 关键测试 | 验证 / 交接块证据 |
|---------------|----------|-------------------|
| FR-301 自动触发 | `tests/memory/test_extraction_orchestrator.py::test_extract_generates_candidate_batch` `test_extract_records_no_evidence` `test_extract_records_evaluated_no_candidate`；`tests/runtime/test_session_manager.py::test_archive_session_creates_memory_batch_when_enabled` | T1 handoff（首次 ModuleNotFoundError → 3 passed）；test-review r1 handoff |
| FR-302a 四类候选 | `tests/memory/test_candidate_store.py::test_reject_invalid_candidate_type`；`tests/memory/test_extraction_orchestrator.py::test_extract_emits_complete_experience_summary_candidate`；`tests/memory/test_publisher.py::test_publish_orchestrator_output_end_to_end` | code-review r1 handoff（experience_summary 完整字段补齐 + contract test）|
| FR-302b 自描述追溯 | `tests/memory/test_candidate_store.py::test_reject_candidate_missing_required_metadata`；`tests/memory/test_extraction_orchestrator.py::test_extract_attaches_source_evidence_anchors`；`tests/memory/test_publisher.py::test_publish_decision_candidate_with_traceability` `test_publish_orchestrator_output_end_to_end`；`tests/knowledge/test_knowledge_store.py`、`tests/knowledge/test_experience_index.py` 持久化字段 | test-review r1 handoff（FR-302b 必填校验）+ code-review r1 handoff（anchor 写盘）|
| FR-303 用户确认 | `tests/memory/test_publisher.py::test_publish_decision_candidate_with_traceability` `test_publish_experience_summary_candidate_to_experience_record` `test_edit_accept_uses_edited_content` `test_reject_or_defer_does_not_publish`；`tests/test_cli.py::TestMemoryReviewCommand::test_memory_review_shows_batch_summary` | code-review r2 |
| FR-303a 5-cap / 批量拒绝 / 延后 | `tests/memory/test_candidate_store.py::test_reject_batch_over_pending_limit` `test_store_and_retrieve_confirmation_record`；`tests/memory/test_extraction_orchestrator.py::test_extract_truncates_to_max_pending_and_records_truncated_count`；`tests/test_cli.py::TestMemoryReviewCommand::test_memory_review_batch_reject_updates_candidates` `test_memory_review_defer_marks_batch_pending_later` | test-review r1 handoff（truncated_count 修复）|
| FR-304 conflict 三选一 | `tests/memory/test_publisher.py::test_detect_conflicts_returns_supersede_for_similar_knowledge` `test_publish_supersede_records_relation_to_existing_entries` `test_publish_requires_explicit_strategy_when_conflict_detected` `test_publish_coexist_does_not_record_supersede_relation` `test_publish_abandon_skips_publication` `test_publish_abandon_skips_experience_summary`；`tests/test_cli.py::TestMemoryReviewCommand::test_memory_review_accept_requires_strategy_when_conflict_exists` `test_memory_review_abandon_skips_publication` | test-review r1 handoff（supersede + abandon）+ code-review r1 handoff（CLI `--strategy` / `--action=abandon`）|
| FR-305 主动推荐闭环 | `tests/memory/test_recommendation_service.py::test_recommendations_include_match_reasons` `test_skill_name_only_degrades_reason`；`tests/runtime/test_skill_executor.py::test_execute_skill_uses_recommendation_service_when_available`；`tests/test_cli.py::TestRunCommand::test_run_shows_recommendation_summary_when_enabled`；`tests/integration/test_e2e_workflow.py::test_memory_pipeline_e2e_flow` | code-review r2 |
| FR-306 match_reasons | `tests/memory/test_recommendation_service.py::test_recommendations_include_match_reasons` `test_skill_name_only_degrades_reason`；`tests/memory/test_recommendation_service.py::test_context_builder_uses_session_and_repo_metadata` | code-review r2 |
| FR-307 失败降级 | `tests/memory/test_extraction_orchestrator.py::test_extraction_failure_writes_error_batch`；`tests/runtime/test_session_manager.py::test_archive_session_ignores_memory_errors` | code-review r1 handoff（`extraction_failed` batch 持久化）|
| NFR-301 / NFR-302 用户主导 + 全链可追溯 | `tests/memory/test_publisher.py::test_publish_decision_candidate_with_traceability` `test_publish_orchestrator_output_end_to_end` `test_publish_requires_explicit_strategy_when_conflict_detected`；`tests/knowledge/test_knowledge_store.py` / `tests/knowledge/test_experience_index.py` 持久化字段；`tests/runtime/test_session_manager.py::test_archive_session_skips_memory_when_extraction_disabled`；`tests/test_cli.py::TestRunCommand::test_run_skips_recommendation_when_disabled` | code-review r2 / test-review r3 |
| NFR-304 与 Phase 1/2 兼容 | `pytest tests/ -q` → `384 passed`；`tests/runtime/test_session_manager.py::test_archive_session_skips_memory_when_extraction_disabled`；`tests/test_cli.py::TestRunCommand::test_run_skips_recommendation_when_disabled`；`.garage/config/platform.json` 默认 memory off（实际配置缺少 `memory` 块 → `load_memory_config` 默认 False）|

### Verification handoff 覆盖矩阵

| 工件 | T1 handoff | test-review r1 handoff | code-review r1 handoff |
|------|------------|------------------------|------------------------|
| `src/garage_os/memory/types.py` | ✅ | — | — |
| `src/garage_os/memory/candidate_store.py` | ✅ | ✅（FR-302b 校验）| — |
| `src/garage_os/memory/extraction_orchestrator.py` | — | ✅（truncated_count）| ✅（anchors / experience_summary 字段 / `extraction_failed` batch）|
| `src/garage_os/memory/publisher.py` | — | ✅（supersede 写回 / abandon 早返回）| ✅（`conflict_strategy` 必传 / `.get()` 默认值 / 端到端 contract test）|
| `src/garage_os/memory/conflict_detector.py` | — | （由 publisher 间接覆盖）| （由 publisher 间接覆盖）|
| `src/garage_os/memory/recommendation_service.py` | — | — | （由 r2 review 复检）|
| `src/garage_os/runtime/session_manager.py` | — | ✅（off-switch 测试）| ✅（删除 dead code）|
| `src/garage_os/runtime/skill_executor.py` | — | — | （由 r2 review 复检）|
| `src/garage_os/cli.py` | — | ✅（recommendation off 测试）| ✅（`--strategy` + `--action=abandon`）|
| `src/garage_os/types/__init__.py` | — | — | （由 r2 review 复检；扩展字段在 T5 已落）|
| `src/garage_os/knowledge/knowledge_store.py` | — | — | （由 r2 review 复检）|
| `src/garage_os/knowledge/experience_index.py` | — | — | （由 r2 review 复检）|
| `tests/memory/test_candidate_store.py` | ✅ | ✅ | — |
| `tests/memory/test_extraction_orchestrator.py` | — | ✅ | ✅ |
| `tests/memory/test_publisher.py` | — | ✅ | ✅ |
| `tests/memory/test_recommendation_service.py` | — | — | （r2/r3 review 基线复检）|
| `tests/runtime/test_session_manager.py` | — | ✅ | — |
| `tests/runtime/test_skill_executor.py` | — | — | （r3 review 基线复检）|
| `tests/integration/test_e2e_workflow.py` | — | — | （r3 review 基线复检）|
| `tests/test_cli.py` | — | ✅ | ✅ |

→ 所有 F003 实际触碰的源码与测试都已被至少一份 verification handoff 或 code-review/test-review 记录直接锚定，无 orphan 实现。

## 发现项

> r2 / r3 通过的两条主链未引入新 important findings。本 review 聚焦"追溯链是否闭合"与"是否存在未回写的漂移"。所有 finding 均为 minor / 非阻塞 / 已在上游 review 记录中显式声明，列出仅供 regression gate / completion gate 一并裁决。

- `[minor][USER-INPUT][TZ5]` `KnowledgePublisher` 仍以 `payload["candidate_id"]` 直接当 `KnowledgeEntry.id` / `ExperienceRecord.record_id`；同一 `candidate_id` 重复 `accept` 会原地覆盖且不走 `KnowledgeStore.update().version+=1` 链路（`src/garage_os/memory/publisher.py:113-145`）。spec / design 第 11.4 节并未明示"`KnowledgeEntry.id` 必须与 `candidate_id` 解耦"，因此从严格契约看本身不构成 design drift；但与 NFR-301"已发布条目状态变化可回读"的精神弱耦合。`docs/verification/F003-code-review-r1-handoff.md`"剩余风险 / 未覆盖项"与 `docs/reviews/code-review-F003-garage-memory-auto-extraction-r2.md`"finding 5 延后接受度"已显式延后，理由是修复需要 `KnowledgeStore` 引入独立 ID 体系，属设计层修补。**Traceability 结论**: 接受 USER-INPUT 级延后；不要求在进入 `hf-regression-gate` 前修复；建议在 `hf-completion-gate` 之前由真人裁决"接受现状作为 F003 v1 行为"或"开独立 hotfix 单独修复"。
- `[minor][LLM-FIXABLE][TZ5]` 仅 `T1` 有 `testDesignApproval`（`docs/approvals/F003-T1-test-design-approval.md`），T2-T9 的测试设计依靠 `docs/approvals/F003-tasks-approval.md` + 任务计划 §5 各任务卡片"测试设计种子"承接；test-review r1 handoff 与 r2/r3 review 显式说明 auto-mode 下未引入新行为契约时不需要单独走 `testDesignApproval`。**Traceability 结论**: 治理路径已显式记录、可冷读，不构成 trace anchor 缺口；建议在 `hf-finalize` 阶段顺手在 `task-progress.md` 或新增一份 `F003-test-design-merge-note.md` 中显式声明"T2-T9 testDesignApproval 在 auto-mode 下随 tasks-approval 合并批准，依据各任务卡片测试设计种子"，避免后续 review / 真人审计误读为治理缺口。**不阻塞 regression gate**。
- `[minor][LLM-FIXABLE][TZ5]` `src/garage_os/memory/extraction_orchestrator.py:68` 的 `# pragma: no cover - defensive: persisted instead of raising` 注释已被 `tests/memory/test_extraction_orchestrator.py::test_extraction_failure_writes_error_batch` 稳定覆盖，注释成 stale；code-review r2 已点名为"顺手清理"。**不阻塞 regression gate**，可在 `hf-completion-gate` 或 `hf-finalize` 阶段顺手摘掉。
- `[minor][LLM-FIXABLE][TZ5]` `KnowledgePublisher.publish_candidate` 仅在 `similar_entries` 非空分支才校验 `VALID_CONFLICT_STRATEGIES`；若调用方在无冲突时误传 `conflict_strategy="garbage"` 不会报错。code-review r2 已显式列入"顺手清理"。**不阻塞**。
- `[minor][LLM-FIXABLE][TZ5]` CLI `--action=abandon` 与 `--action=accept --strategy=abandon` 在最终效果上重叠，code-review r2 与 r1 follow-up handoff 均显式声明"语义上重叠为可接受"。如果产品侧未来要求严格区分"主动放弃整条候选" vs "因相似条目放弃发布"，再独立任务推进。**不阻塞**。
- `[minor][LLM-FIXABLE][TZ5]` `SessionManager._trigger_memory_extraction` 异常路径仍只走 `logger.warning(..., exc_info=True)`（`session_manager.py:228-236`），未额外往 `sessions/archived/<id>/memory-extraction-error.json` 双写；FR-307 第 2 / 3 条"保存错误摘要、时间和关联 session"的文件级证据由 orchestrator 层 `extraction_failed` batch 持有。这是合理的单点持久化（避免双写），但若 traceability 期间真人要求 session-side 也持久化，可顺手补一条 minimal 写盘。**不阻塞**，`tests/runtime/test_session_manager.py::test_archive_session_ignores_memory_errors` 已断言 archive 仍成功。
- `[minor][LLM-FIXABLE][TZ5]` `.garage/config/platform.json` 当前只有 `schema_version=1` 等基础字段，**未显式包含 `memory` 块**；运行时由 `extraction_orchestrator.load_memory_config` 兜底成 `{extraction_enabled: False, recommendation_enabled: False}`。这与设计 §11 / 任务 T4 一致（feature flag 默认 OFF，第一版需用户主动开启），且测试通过临时配置覆盖验证开关行为；但 `.garage/config/platform.json` 可在 finalize 阶段补一条注释或样例 `memory` 块（带 `schema_version`），让真人可以零文档查找直接看到 feature flag 落点。**不阻塞**，可在 `hf-finalize` 阶段处理。

## 追溯缺口

经全链路核对，未发现以下任一类硬缺口：

- `ZA1` spec drift：FR-301..FR-307 / NFR-301..304 的最新版本与 design / tasks / impl 一致；spec 第 9 / 10 节 IFR / CON 也都有承接
- `ZA2` orphan task：T1-T9 全部能反向追到 design / spec 锚点（任务计划 §4）
- `ZA3` undocumented behavior：本轮代码扩展（`--strategy`、`--action=abandon`、`conflict_strategy` 必传、`extraction_failed` batch、`source_evidence_anchors` 写盘）均已在 r1 / r1-follow-up handoff 与 review r2 中显式声明
- `ZA4` unsupported completion claim：384 passed + 三份 handoff + E2E 闭环 + reviewer 独立复跑结果一致

唯一 borderline 项是 finding 5（`candidate_id` 复用为 `KnowledgeEntry.id`），但 spec / design 第 11.4 节未做"必须解耦"的硬约束，技术上不构成 ZA3；且已被 r1 follow-up handoff 显式延后并在 code-review r2 中接受。

## 需要回写或同步的工件

以下条目均为 LLM-FIXABLE / minor 性质，建议在 `hf-completion-gate` → `hf-finalize` 阶段一并清理；本 review 不阻塞 regression gate：

- 工件: `task-progress.md`
  - 原因: 本 review 通过后，`Pending Reviews And Gates` 应进入 `hf-regression-gate` → `hf-completion-gate`；`Next Action Or Recommended Skill` 应同步为 `hf-regression-gate`
  - 建议动作: 在 regression gate 通过后由父会话同步更新；本 review 不直接编辑 `task-progress.md`
- 工件: `docs/approvals/F003-test-design-merge-note.md`（建议新增）或在 `task-progress.md` 中加一段说明
  - 原因: 仅 T1 有 `testDesignApproval`；T2-T9 的测试设计在 auto-mode 下随 `tasks-approval` 合并批准，建议留一份显式可冷读的治理记录
  - 建议动作: 在 `hf-finalize` 阶段顺手补充；不阻塞 regression gate
- 工件: `src/garage_os/memory/extraction_orchestrator.py:68` 的 `# pragma: no cover` 注释
  - 原因: 已被 `test_extraction_failure_writes_error_batch` 稳定覆盖，stale
  - 建议动作: 顺手清理；不阻塞
- 工件: `.garage/config/platform.json`
  - 原因: 缺 `memory` 块，feature flag 落点不直观
  - 建议动作: 在 `hf-finalize` 阶段补一段样例/注释；不阻塞
- 工件: `KnowledgePublisher.publish_candidate` 的 `VALID_CONFLICT_STRATEGIES` 入口校验
  - 原因: 仅在 `similar_entries` 非空时校验，调用方误传不会报错
  - 建议动作: 把校验前移到入口；可在 `hf-completion-gate` / `hf-finalize` 顺手清理
- 工件: `KnowledgePublisher` `candidate_id` ↔ `KnowledgeEntry.id` 体系（finding 5）
  - 原因: 同一 candidate 重复 accept 会静默覆盖
  - 建议动作: 由真人在 `hf-completion-gate` 阶段裁决"接受现状 / 立独立 hotfix"

## 关于路由判断

- 实现交接块（T1 + test-review r1 + code-review r1）齐全，可冷读，触碰工件可逐行定位
- 测试套件 `pytest tests/ -q` reviewer 独立复跑得到 `384 passed in 24.62s`，与所有交接块声明的 GREEN 摘要一致，无回归
- 上游 stage / route / profile 一致；`hf-test-review r3` + `hf-code-review r2` 都已通过且推荐 `hf-traceability-review`
- 本 review 未发现 important / critical findings；遗留 minor 全部为已知低优 / USER-INPUT 延后项，不构成 stage / route / profile / 上游证据冲突
- finding 5（`candidate_id` 复用）按 `code-review r2` 与 r1 follow-up handoff 的 USER-INPUT 延后处理，traceability review 接受现状不要求 reroute；建议在 `hf-completion-gate` 阶段以 USER-INPUT 形式正式裁决

不需要 reroute via router。

## 下一步

- `hf-regression-gate`：消费本 review 的链接矩阵 + 三份 verification handoff 的 GREEN 摘要 + reviewer 独立复跑的 `384 passed`，做 F003 完整回归判定。重点关注：
  1. 全套 `pytest tests/ -q` 是否仍稳定 `384 passed`
  2. memory feature on / off 双向行为是否仍稳定（已有 `test_archive_session_skips_memory_when_extraction_disabled` + `test_run_skips_recommendation_when_disabled` 锁定）
  3. E2E `test_memory_pipeline_e2e_flow` 是否仍稳定
  4. 关键持久化文件 schema（`memory/candidates/batches/*.json`、`memory/candidates/items/*.md`、`memory/confirmations/*.json`、`knowledge/decisions/*.md`、`experience/records/*.json`）字段是否未发生未记录漂移

## 结构化返回（供父会话路由）

```json
{
  "conclusion": "通过",
  "next_action_or_recommended_skill": "hf-regression-gate",
  "record_path": "docs/reviews/traceability-review-F003-garage-memory-auto-extraction.md",
  "key_findings": [
    "[非阻塞 minor 提示] FR-301..307 / NFR-301/302/304 / CON-301..304 全链路追溯闭合，384 passed 与三份 verification handoff 一致；6 个 traceability 维度全部 ≥7/10",
    "[minor][USER-INPUT][TZ5] code-review r1 finding 5（KnowledgePublisher 用 candidate_id 当 KnowledgeEntry.id）按 r1 follow-up handoff + code-review r2 显式延后；spec/design §11.4 未硬要求解耦，traceability 不强制修，但建议 hf-completion-gate 阶段由真人正式裁决",
    "[minor][LLM-FIXABLE][TZ5] 仅 T1 有 testDesignApproval；T2-T9 在 auto-mode 下随 tasks-approval 合并批准，治理路径已记录但建议在 hf-finalize 时显式回写",
    "[minor][LLM-FIXABLE][TZ5] extraction_orchestrator.py:68 # pragma: no cover 已 stale；publisher VALID_CONFLICT_STRATEGIES 仅在冲突分支校验；CLI --action=abandon 与 accept --strategy=abandon 语义重叠；session 侧 _trigger_memory_extraction 仍 logger.warning 兜底；.garage/config/platform.json 缺 memory 块。均为顺手清理项，不阻塞 regression gate"
  ],
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "finding_breakdown": [
    {
      "severity": "minor",
      "classification": "USER-INPUT",
      "rule_id": "TZ5",
      "summary": "publisher 用 candidate_id 当 KnowledgeEntry.id 仍未修复，按 code-review r2 / r1 follow-up handoff 显式延后；建议 hf-completion-gate 阶段真人裁决"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TZ5",
      "summary": "T2-T9 testDesignApproval 在 auto-mode 下随 tasks-approval 合并批准，治理路径已显式记录；建议 hf-finalize 阶段顺手回写一份 merge-note"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TZ5",
      "summary": "extraction_orchestrator.py:68 # pragma: no cover 注释已 stale，建议 hf-finalize 阶段顺手清理"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TZ5",
      "summary": "KnowledgePublisher.publish_candidate 仅在 similar_entries 非空时校验 VALID_CONFLICT_STRATEGIES，建议入口处提前校验"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TZ5",
      "summary": "CLI --action=abandon 与 --action=accept --strategy=abandon 语义重叠，待产品侧确认是否需要差异化"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TZ5",
      "summary": "SessionManager._trigger_memory_extraction 仍走 logger.warning，FR-307 文件级证据由 orchestrator batch 文件承担，建议产品侧确认是否需要 session-side 双写"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TZ5",
      "summary": ".garage/config/platform.json 缺 memory 块，运行时由默认值兜底；建议 hf-finalize 阶段补一段样例/注释，提升 feature flag 落点可发现性"
    }
  ]
}
```
