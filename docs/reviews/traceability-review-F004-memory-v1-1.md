# Traceability Review — F004 Garage Memory v1.1

- Review Skill: `hf-traceability-review`
- Reviewer: cursor cloud agent (subagent dispatched by `hf-test-driven-dev` parent session)
- Date: 2026-04-19
- Workflow Profile / Execution Mode: `full` / `auto`
- Workspace Isolation: `in-place`
- Branch: `cursor/f004-memory-polish-1bde`
- 关联规格: `docs/features/F004-garage-memory-v1-1-publication-identity-and-confirmation-semantics.md`
- 关联设计: `docs/designs/2026-04-19-garage-memory-v1-1-design.md`
- 关联任务计划: `docs/tasks/2026-04-19-garage-memory-v1-1-tasks.md`
- 关联 approvals: `docs/approvals/F004-{spec,design,tasks}-approval.md` + `docs/approvals/F004-T{1,2,3,4}-test-design-approval.md`
- 关联实现交接块:
  - `docs/verification/F004-T1-implementation-handoff.md`
  - `docs/verification/F004-T2-implementation-handoff.md`
  - `docs/verification/F004-T5-implementation-handoff.md`
- 关联上游 reviews:
  - `docs/reviews/spec-review-F004-memory-v1-1.md` (通过)
  - `docs/reviews/design-review-F004-memory-v1-1.md` (需修改 → r1 闭合)
  - `docs/reviews/tasks-review-F004-memory-v1-1.md` (通过)
  - `docs/reviews/test-review-F004-memory-v1-1.md` (通过；4 项 minor，2 项已补 supplementary tests)
  - `docs/reviews/code-review-F004-memory-v1-1.md` (通过；2 项 minor docstring 已补)

---

## 0. 评审范围

F004 cycle 收敛 F003 r2 显式延后的 4 项 finding（1 USER-INPUT minor + 3 LLM-FIXABLE minor）。本评审仅检查证据链追溯完整性，不重做代码 / 测试质量评审。

工件总览：
- 1 spec（F004），7 FR（含 a/b/c）+ 2 NFR + 2 IFR + 4 CON + 3 ASM
- 1 design（D004 r1），4 ADR + 1 trace 矩阵 + supersede carry-over contract（§11.2.1）
- 1 task plan，5 tasks（T1~T5）
- 4 处源码改动（publisher.py / session_manager.py / cli.py / knowledge_store.py）+ 2 处文档增量（user-guide / developer-guide）
- 26 个 F004 新增测试 + 2 个 supplementary tests（test review 后补） = 28 个新测试
- 全 suite `pytest tests/ -q` → **414 passed in 24.94s**（baseline 384 → +30 = 414）

---

## 1. 证据基线

| 检查 | 结果 |
|------|------|
| 全 suite 当前状态 | ✓ 414 passed, 0 failed, 0 skipped (本 reviewer 跑过验证) |
| F004 focused 子集 | ✓ `tests/memory/ tests/knowledge/ tests/runtime/test_session_manager.py tests/test_cli.py tests/test_documentation.py` → 147 passed |
| 实现交接块 | ✓ T1/T2/T5 显式 handoff；T3/T4 在 commit `feat(F004 T3 T4 T5)` + handoff T5 末段 RED/GREEN 覆盖 |
| 上游 reviews 全部通过 | ✓ spec / design (r1) / tasks / test / code 全部 verdict=通过 |
| route / stage / profile 一致 | ✓ full / auto / in-place 在所有 5 份 review record + 3 份 approval + task-progress 中一致 |
| approval chain | ✓ spec → design → tasks → 4 个 task test design 全部落盘 |

---

## 2. Precheck

| 检查项 | 状态 | 证据 |
|--------|------|------|
| 上游工件稳定可定位 | ✓ spec / design / tasks 都标 `已批准`，文件路径稳定 |
| 实现交接块与上游 review 一致 | ✓ T1/T2/T5 handoff 触碰工件、测试名、commit 与 task plan §5 + design §11 一致；code-review §0 git diff 主体与 handoff 触碰文件清单 1:1 对应 |
| route / stage / profile 稳定 | ✓ task-progress.md Current Stage = `hf-test-driven-dev (T1~T5 全部 done)` → `hf-test-review` ✓ → `hf-code-review` ✓ → 当前 `hf-traceability-review` |
| 证据无冲突 | ✓ test-review 4 项 minor 中 2 项 (4.1 / 4.2) 已被 code-review 时段 supplementary tests 闭合（`test_extra_front_matter_keys_round_trip` / `test_extra_front_matter_keys_do_not_overwrite_dataclass_keys` / `test_repeated_publish_experience_summary_preserves_created_at`）；其余 2 项 (4.3 supersede merge / 4.4 RED narrative) 是补强而非阻塞 |

Precheck 通过，进入正式 6 维评审。

---

## 3. 多维评分

| ID | 维度 | 评分 | 说明 |
|----|------|------|------|
| `TZ1` | 规格 → 设计追溯 | 9/10 | F004 spec 全部 7 FR + 2 NFR + 2 IFR + 4 CON + 3 ASM 在 design §3 trace 矩阵中 1:1 出现，且每条进一步落到具体设计章节（§10/§11/§12/ADR）；ASM-403 在 §12 末尾段显式裁决；FR-401 supersede 不变量在 design r1 升格为 §10.1 + §11.2.1 PRESERVED_FRONT_MATTER_KEYS 的强契约。仅 NFR-401 验收 2 在 spec 中描述为"开发者文档抽象描述"的措辞，design §3 / §9 表格按"developer-guide 段"承接（轻微措辞偏移，但 traceability 不破） |
| `TZ2` | 设计 → 任务追溯 | 9/10 | task plan §4 显式给出"规格/设计 锚点 → 覆盖任务"矩阵，覆盖 §3 全部条目 + §10.1.1 self-conflict + §11.2.1 PRESERVED 列表 + §11.4 schema + ADR-401~404；§5 各 task 的"测试设计种子"段直接引用 design 关键不变量；T1+T2+T3+T4+T5 分工清晰，不存在 design 决策无任务承接的情况 |
| `TZ3` | 任务 → 实现追溯 | 9/10 | T1 触碰文件 = publisher.py + tests/memory/test_publisher.py ✓；T2 触碰文件 = publisher.py + knowledge_store.py（design §9 escape hatch）+ tests/memory/test_publisher.py ✓；T3 cli.py + tests/test_cli.py ✓；T4 session_manager.py + tests/runtime/test_session_manager.py ✓；T5 docs/guides/* + tests/test_documentation.py ✓。每个改动都在 publisher.py / cli.py / session_manager.py 中带 `# F004 ...` inline 锚点，可冷读回 design § 编号。T2 中间发现 KnowledgeStore extra-key bug fix 在 handoff "中间发现" 段显式登记并在 design §9 escape hatch 范围内（详见 §5.1） |
| `TZ4` | 实现 → 验证追溯 | 9/10 | 26 个 F004 新增测试 + 4 个 supplementary 测试 docstring 全部带 FR / NFR / design § / ADR 锚点；T1/T2/T4 RED 终端输出齐全（cmd + tail 行）；T3 RED 在 handoff 中描述 + commit message 中可冷读；T5 RED 仅 narrative（test review §4.4 finding 接受现状）；GREEN 全 suite 414 passed 在 T5 handoff + code-review §1 双重确认 |
| `TZ5` | 漂移与回写义务 | 8/10 | 显式登记的偏离均已回写：(a) KnowledgeStore extra-key fix 走 design §9 escape hatch + handoff "中间发现" + code-review §5.2 + test-review 4.5A 三处文档化；(b) test-review 4.1/4.2 minor 已 supplementary tests 闭合；(c) code-review 2 项 minor docstring 已补；(d) F003 r2 4 项延后 finding 全部映射到 F004 FR-401~404（详见 §5.2）。剩余轻微漂移：design §3 trace 矩阵未显式列出"KnowledgeStore.\_entry\_to\_front\_matter extra-key 合并新契约"作为 v1.1 forward-必需的内部接口（属 internal bug fix，design §9 escape hatch 已隐含覆盖；不阻塞，详见 finding 4.1） |
| `TZ6` | 整体链路闭合 | 9/10 | spec → design (r1) → tasks → 4 处实现 + 2 处文档 → 28 个测试 → 全 suite 414 passed → handoff + 5 份 review record → approval chain，链路完整无悬空。F003 r2 的 4 项延后 finding (§5.2) 在 F004 cycle 内全部端到端关闭。可安全进入 `hf-regression-gate` |

任一关键维度均 ≥ 8。可形成"通过" verdict。

---

## 4. 链接矩阵

### 4.1 FR / NFR / IFR 端到端追溯

| Spec 锚点 | Design 承接 | Task 承接 | 实现 | 测试 | 文档 |
|-----------|-------------|-----------|------|------|------|
| **FR-401** 重复发布版本链 | §3 + §10.1 + §11.2 + ADR-401 + §13.2 | T1 (PublicationIdentityGenerator) + T2 (store-or-update) | `publisher.py:103-221` + KnowledgeStore extra-key fix | `test_repeated_accept_uses_update_increments_version` / `test_retrieve_after_repeated_accept_returns_latest_version` / `test_repeated_publish_experience_summary_updates_index` / `test_publication_identity_default_returns_candidate_id` | developer-guide §"Publisher 重复发布与 ID 生成规则" |
| **FR-401 + FR-405 supersede carry-over** | §10.1 carry-over 数据流 + §11.2.1 PRESERVED\_FRONT\_MATTER\_KEYS contract + §13.2 | T2 | `publisher.py:194-215` + `publisher.py PRESERVED_FRONT_MATTER_KEYS` 元组 + `knowledge_store.py:_DATACLASS_FRONT_MATTER_KEYS` (extra-key 持久化 escape hatch fix) | `test_repeated_publish_preserves_supersedes_chain_from_v1` / `test_repeated_publish_preserves_related_decisions_from_v1` / `test_repeated_publish_merges_v1_supersedes_with_new_supersede_target` (supplementary) | developer-guide §"PRESERVED\_FRONT\_MATTER\_KEYS" |
| **FR-401 self-conflict 短路** | §10.1.1 + §11.2 + §14 失败模式 | T2 | `publisher.py:162-166` | `test_repeated_accept_short_circuits_self_conflict` | developer-guide §"同名 candidate 不会触发 self-conflict" |
| **FR-402** 入口校验前置 | §10.2 + §11.2 入口校验段 + ADR-402 | T1 | `publisher.py:83-114 _validate_conflict_strategy` 提前到 publish_candidate 第一行 | `test_publish_candidate_rejects_garbage_strategy_at_entry` / `test_publish_candidate_accepts_valid_strategy_without_conflict` / `test_publish_candidate_none_strategy_passes_when_no_conflict` | (FR-402 spec 未要求文档段；developer-guide 中通过 PublicationIdentityGenerator 段间接说明) |
| **FR-403a** confirmation 持久差异化 | §10.3 表格 + §11.5 + ADR-403 | T3 | `cli.py:507-540` confirmation `resolution` × `conflict_strategy` 字段写入 + 候选 status 派生逻辑 | `test_memory_review_abandon_writes_resolution_abandon_with_null_strategy` / `test_memory_review_accept_with_strategy_abandon_writes_resolution_accept` / `test_memory_review_accept_with_abandon_strategy_no_conflict_falls_through_to_publish` | user-guide §"Memory review — abandon paths" 表格 |
| **FR-403b** CLI 输出文案 | §11.5 + §10.3 表格 stdout 列 | T3 | `cli.py:11-21` MEMORY\_REVIEW\_ABANDONED\_NO\_PUB / MEMORY\_REVIEW\_ABANDONED\_CONFLICT 模块常量 + `cli.py:541-555` print 调用 | `test_memory_review_abandon_outputs_no_pub_marker` / `test_memory_review_conflict_abandon_outputs_conflict_marker` / `test_memory_review_two_abandon_markers_do_not_overlap` | user-guide grep 示例段 |
| **FR-403c** 用户文档差异化 | §3 trace + §9 模块表 | T5 | `docs/guides/garage-os-user-guide.md:299-322` "Memory review — abandon paths" 段 | `test_user_guide_memory_review_documents_both_abandon_paths`（6 关键 token） | user-guide 自身 |
| **FR-404** session 触发证据 | §10.4 + §11.3 + §11.4 schema + ADR-404 + §8.3 sequence | T4 | `session_manager.py:200-298` 三 phase try/except + `_persist_extraction_error` + `MEMORY_EXTRACTION_ERROR_FILENAME` 常量 | `test_archive_session_persists_extraction_error_orchestrator_init` / `_enablement_check` / `_extraction` / `_no_error_file_when_extraction_succeeds` / `_no_error_file_when_extraction_disabled` / `test_memory_extraction_error_json_has_full_schema` | developer-guide §"Session memory-extraction-error.json schema" |
| **FR-405** 兼容性零回归 | §3 + §13.3 已知触动测试段 | T2~T5 verify 段 | 全模块；KnowledgeStore extra-key fix 是 v1.1 forward-必需（详见 §5.1） | `pytest tests/ -q` → 414 passed (本 reviewer 复跑确认)；145 个 memory focused + 70 个 knowledge focused 0 回归 | — |
| **NFR-401** 决定性发布身份 | §11.1 + §12 + ADR-401 | T1 | `publisher.py:15-39 PublicationIdentityGenerator` (纯函数 derive_*) | `test_publication_identity_generator_is_deterministic` / `test_publication_identity_default_returns_candidate_id` | developer-guide §"生成规则"表 |
| **NFR-402** 不退化性能 | §12 + ASM-403 决议（不补 publisher 专项 benchmark） | T2 (NFR-402 wall-clock) | publisher 重复发布路径多 1 次 in-memory index lookup（O(1)） | T5 handoff "NFR-402 wall-clock 验证" 段：`pytest tests/memory/` T1=0.36s / T0=0.37s（≤ 1.1*T0） | — |
| **IFR-401** 复用 KnowledgeStore.update | §10.1 + §11.2 + §9 边界 | T2 | `publisher.py:200-215` 调 `knowledge_store.update(entry)`（接口签名不变） | 通过 `test_repeated_accept_uses_update_increments_version` 行为锁住 + `tests/knowledge/test_knowledge_store.py` 70 测试零回归 | — |
| **IFR-402** 复用 ExperienceIndex.update | §10.1 + §11.2 路径 A | T2 | `publisher.py:140-143` 调 `experience_index.update(record)` + `created_at` carry-over | `test_repeated_publish_experience_summary_updates_index` + `test_repeated_publish_experience_summary_preserves_created_at` (supplementary) | — |
| **CON-401** workspace-first | §12 落地表 | T4 | `memory-extraction-error.json` 写到 `.garage/sessions/archived/<id>/` | TestF004T4ExtractionErrorPersistence 6 测试断言路径 | — |
| **CON-402** 不引入外部依赖 | §12 落地表 | 全任务 | `pyproject.toml` 不变；仅 stdlib + 现有依赖 | — | — |
| **CON-403** schema 兼容 | §12 落地表 | T3 + T4 | confirmation 字段不删除；memory-extraction-error.json 是新文件 | TestF004T4ExtractionErrorPersistence + 全 suite 兼容性测试 | — |
| **CON-404** 文件契约可冷读 | §11.4 schema 显式 + §12 落地表 | T4 + T5 | session_manager.py `_persist_extraction_error` 写 6 字段 schema | `test_memory_extraction_error_json_has_full_schema` + `test_developer_guide_documents_memory_extraction_error_json_schema` | developer-guide schema 段 |

### 4.2 ADR / 关键设计决策追溯

| ADR | 设计章节 | 实现 | 测试 |
|-----|---------|------|------|
| ADR-401 发布身份 = candidate_id 透传（无 hash 后缀） | §11.1 + §16 | publisher.py:35 `return candidate_id` | `test_publication_identity_default_returns_candidate_id` |
| ADR-402 入口校验位于 publish_candidate 第一行 | §10.2 + §16 | publisher.py:114 第一行调 `_validate_conflict_strategy` | `test_publish_candidate_rejects_garbage_strategy_at_entry` |
| ADR-403 confirmation 复用 resolution × conflict_strategy 字段 | §10.3 + §16 | cli.py:507-540 字段写入逻辑 | `TestMemoryReviewAbandonDualPaths` 6 测试 |
| ADR-404 latest-error 单文件覆盖（不维护历史 array） | §11.4 + §16 | session_manager.py `_persist_extraction_error` 写单文件 | `test_archive_session_persists_extraction_error_*` 隐含 |

### 4.3 Approval / Review chain

| 阶段 | Record | Verdict |
|------|--------|---------|
| spec | `docs/reviews/spec-review-F004-memory-v1-1.md` + `docs/approvals/F004-spec-approval.md` | 通过（minor 已 author 顺手收敛） |
| design (r1) | `docs/reviews/design-review-F004-memory-v1-1.md` + `docs/approvals/F004-design-approval.md` | 需修改 → r1 闭合 → 已批准 |
| tasks | `docs/reviews/tasks-review-F004-memory-v1-1.md` + `docs/approvals/F004-tasks-approval.md` | 通过 |
| T1~T4 test design | `docs/approvals/F004-T{1,2,3,4}-test-design-approval.md` | auto-mode self-approved（T5 trivial 不需独立 approval） |
| test review | `docs/reviews/test-review-F004-memory-v1-1.md` | 通过（4 minor，2 已 supplementary 闭合） |
| code review | `docs/reviews/code-review-F004-memory-v1-1.md` | 通过（2 minor docstring 已补） |
| traceability review | 本文档 | **通过** |

---

## 5. 独立判断点回应（用户 prompt 要求）

### 5.1 KnowledgeStore extra-key 修复的追溯链

**判断**：**修复方向正确、追溯链充分；不需要回流 spec 加 IFR-403；可作为"实施时发现的 internal bug fix"接受**。

冷读链：
1. **设计层依据是否充分**：design §9 模块边界段显式列出"不修改 KnowledgeStore（**除非测试时发现 retrieve 路径有 bug**）"escape hatch。T2 实施 `test_repeated_publish_preserves_supersedes_chain_from_v1` 时通过 `python -c` 探针实测发现：F003 v1 publisher 在 strategy=supersede 路径写入 `entry.front_matter["supersedes"]`，但 KnowledgeStore.\_entry\_to\_front\_matter() 只写 14 个 hardcoded 字段，extra keys **从未** make it to disk。这是 escape hatch 触发条件的明确命中：是测试中发现的存储路径 bug，而非任意范围扩张。
2. **是否需要回流 spec 加 IFR-403**：**不需要**。理由：
   - spec 层面 IFR-401 已声明"复用 KnowledgeStore.store/update 现有契约"。F003 v1 的 \_entry\_to\_front\_matter 在 extra-key 上的行为是 **未文档化的 bug**，而非"已批准契约"——修复使 extra-key 持久化对齐 store/update 的语义直觉，**不构成新的对外契约**。
   - 修复严格落在 publisher → KnowledgeStore 的内部协议，不影响任何 KnowledgeEntry / 公开方法签名 / 文件命名 / 索引契约。
   - design §11.2.1 PRESERVED_FRONT_MATTER_KEYS 已经是"v1.1 forward 必需的内部 carry-over 契约"的对外承诺；KnowledgeStore extra-key 持久化是该契约可执行的前提，已被 design §9 escape hatch 隐含覆盖。
3. **是否作为 internal bug fix 接受**：**接受**。证据：
   - T2 handoff "中间发现" 段显式登记并贴出探针证据 + 70 测试零回归
   - code-review §5.2 独立判断"修复方向正确，落在 design §9 escape hatch 范围内"
   - test-review §4.5A 独立判断"对 v1 数据迁移 vacuously 满足；对 v1.1 forward 是**强制必需**"
   - 已被 supplementary tests `test_extra_front_matter_keys_round_trip` + `test_extra_front_matter_keys_do_not_overwrite_dataclass_keys` 锁住 KnowledgeStore 自身契约
   - 回写齐备：handoff + code-review record + test-review record 三层文档化
4. **唯一轻微漂移**：design §3 trace 矩阵在"FR-401 + FR-405 supersede 链 carry-over"行的"主要落点"列只提到 publisher.py，未显式提及 KnowledgeStore extra-key 修复。这属于 trace 矩阵措辞补强机会（finding 4.1），不影响整体证据链。

### 5.2 F003 r2 延后 finding 收敛

`docs/reviews/code-review-F003-garage-memory-auto-extraction-r2.md` `finding_breakdown` 中**显式延后**到 F004 / hotfix 的 4 项 minor，逐项追溯：

| F003 r2 finding | severity / classification | F004 spec 锚点 | F004 task | F004 实现 | F004 测试 | 状态 |
|----------------|---------------------------|---------------|-----------|-----------|-----------|------|
| publisher 用 `candidate_id` 当 `KnowledgeEntry.id`，重复 accept 静默覆盖 | minor / USER-INPUT (CR2/CR4) | FR-401 + FR-405 + NFR-401 | T1 + T2 | publisher.py PublicationIdentityGenerator + retrieve→store-or-update + supersede carry-over + KnowledgeStore extra-key fix | `TestPublishCandidateRepublication` 6 + supplementary 1 | ✓ 闭合 |
| publish_candidate 入口未校验 `VALID_CONFLICT_STRATEGIES`（只在冲突分支校验） | minor / LLM-FIXABLE (CR3) | FR-402 | T1 | publisher.py `_validate_conflict_strategy` 提前到第一行 | `TestPublishCandidateEntryValidation` 3 | ✓ 闭合 |
| CLI `--action=abandon` 与 `--action=accept --strategy=abandon` 在效果上重叠 | minor / LLM-FIXABLE (CR5/CR4) | FR-403a + FR-403b + FR-403c | T3 + T5 | cli.py 双 abandon stdout 常量 + confirmation 字段差异化 + user-guide 段 | `TestMemoryReviewAbandonDualPaths` 6 + `test_user_guide_memory_review_documents_both_abandon_paths` | ✓ 闭合 |
| `SessionManager._trigger_memory_extraction` 失败仅 logger.warning，无 session-level 文件证据 | minor / LLM-FIXABLE (CR3) | FR-404 + CON-401 + CON-404 | T4 | session_manager.py 三 phase try/except + `_persist_extraction_error` + memory-extraction-error.json schema | `TestF004T4ExtractionErrorPersistence` 6 + `test_developer_guide_documents_memory_extraction_error_json_schema` | ✓ 闭合 |

**4/4 全部端到端闭合**。F003 r2 同时记录了第 5 项 LLM-FIXABLE minor "extraction\_orchestrator.py:68 stale `# pragma: no cover` 注释"，该项**不在 F004 spec §1 收敛范围**（spec 显式列出 4 个问题域）；本 reviewer 验证 `extraction_orchestrator.py` 当前已无 `# pragma: no cover` 注释（grep 0 命中），属在其他 commit 中顺手清理，不影响 F004 trace 闭合。

### 5.3 T5 docs lint 测试对 FR-403c 的覆盖充分性

**判断**：**充分**。

冷读链：
- FR-403c 验收 1 "搜索 'abandon' 至少命中 1 段独立说明"：lint 检查 `"abandon"` token ✓ 且 user-guide §299 起单段 `## Memory review — abandon paths` 标题命中
- FR-403c 验收 2 "读者能正确回答应该用哪条路径"：lint 检查 `"--action abandon"` + `"--strategy abandon"` 两条命令行 token ✓；user-guide 表格 + "一句话怎么选" 段直接给决策建议
- FR-403c 验收 3 "段落显式列出两条路径下 confirmation 文件的字段差异"：lint 检查 `"conflict_strategy=abandon"` token ✓；user-guide 表格"confirmation 字段"列同时给出 `resolution=abandon、conflict_strategy=null` 与 `resolution=accept、conflict_strategy=abandon`
- 此外 lint 还检查 `"without publication attempt"` 与 `"due to conflict"`，与 FR-403b 的 stdout 标识符 `MEMORY_REVIEW_ABANDONED_NO_PUB` / `MEMORY_REVIEW_ABANDONED_CONFLICT` 文案锁定，避免 docs/code 漂移

唯一轻微补强机会：lint 是 token 检查不验证段落语义，未来如果 user-guide 段落顺序漂移仍可能需要人工 review。这属 task plan §10 已显式接受的轻量保护策略，不阻塞。

---

## 6. Findings

### 6.1 [minor][LLM-FIXABLE][TZ5 / ZA3] design §3 trace 矩阵未显式登记 KnowledgeStore extra-key 修复

**Context**：design §3 表格"FR-401 + FR-405 supersede 链 carry-over"行的"主要落点"列只写"publisher.py（新增 helper class + 方法 + carry-over + 短路）"，未显式提及 KnowledgeStore.\_entry\_to\_front\_matter 的 extra-key 持久化修复（实施期发现的 v1.1 forward-必需 internal bug fix，详见 §5.1）。

**Risk**：低。修复已在 design §9 escape hatch 范围内、handoff "中间发现" 段、code-review §5.2、test-review §4.5A 共 4 处文档化；未来 cold-read trace 矩阵的读者可能不立即意识到 KnowledgeStore 也是 v1.1 触动的源码模块。

**建议**（非阻塞，可在下一 cycle / hotfix 顺手补）：在 design §3 矩阵 FR-401+FR-405 行的"主要落点"列追加 `+ knowledge_store.py extra-key 持久化（design §9 escape hatch）`；或在 design §9 模块表"`memory/publisher.py`"行下方补一行 `knowledge_store.py | + _DATACLASS_FRONT_MATTER_KEYS / extra-key 末尾合并（design §9 escape hatch fix）| 公共 API 签名`。

不阻塞 traceability verdict。

### 6.2 [minor][LLM-FIXABLE][TZ4] T5 RED evidence 仅 narrative

**Context**：`docs/verification/F004-T5-implementation-handoff.md` "RED 证据" 段为 narrative：`... (会 fail，因为 user-guide / developer-guide 不含 abandon / PublicationIdentityGenerator / memory-extraction-error.json 关键 token)`，无真实终端输出。

**Risk**：低。lint-only 测试，逻辑显然；test-review §4.4 已识别同一 finding 并接受现状。GREEN 段终端输出齐全。

**建议**（非阻塞）：未来如有同类 docs lint task，handoff 可选保留一段 `pytest tests/test_documentation.py -v` 的真实 RED 输出；本 cycle 接受现状。

---

## 7. 追溯缺口

无核心断链。仅以下两处轻微补强机会（均为 minor LLM-FIXABLE，不阻塞）：

1. design §3 / §9 trace 矩阵未显式登记 KnowledgeStore extra-key 修复 → finding 6.1
2. T5 RED 仅 narrative → finding 6.2

无以下 anti-pattern：
- ZA1 spec drift：✗ 未发现，spec / design / tasks / 实现版本一致
- ZA2 orphan task：✗ 未发现，T1~T5 全部追溯到 FR / NFR
- ZA3 undocumented behavior：⚠ 仅 KnowledgeStore extra-key fix 在 design trace 矩阵中标识偏弱（finding 6.1），但 design §9 escape hatch 已隐含覆盖，handoff/test-review/code-review 共 3 处文档化，不属典型 ZA3
- ZA4 unsupported completion claim：✗ 未发现，全 suite 414 passed 本 reviewer 已亲自跑过

---

## 8. 需要回写或同步的工件

无强制回写项。可选补强（不阻塞 regression gate）：

- **工件**：`docs/designs/2026-04-19-garage-memory-v1-1-design.md` §3 + §9
  - **原因**：finding 6.1，trace 矩阵未显式登记 KnowledgeStore extra-key 修复
  - **建议动作**：下一 cycle 顺手在 §3 表格 FR-401+FR-405 行追加锚点；或在 §9 模块表新增 `knowledge_store.py` 一行说明 escape hatch fix。**可在 hf-finalize 阶段顺手处理**。

---

## 9. 结论

**通过**

理由：
- 6 维度评分全部 ≥ 8，最低 8/10（TZ5 漂移登记），无低于 6 的关键维度
- 链接矩阵（§4.1 + §4.2 + §4.3）端到端闭合：F004 全部 7 FR + 2 NFR + 2 IFR + 4 CON + 4 ADR 在 design / tasks / 实现 / 测试 / 文档 5 层都有锚点
- F003 r2 显式延后的 4 项 minor finding（1 USER-INPUT + 3 LLM-FIXABLE）全部在 F004 cycle 内端到端关闭（§5.2）
- KnowledgeStore extra-key 修复严格落在 design §9 escape hatch 范围内，不需要回流 spec（§5.1）
- T5 docs lint 充分覆盖 FR-403c 三条验收（§5.3）
- 全 suite 414 passed 零回归（本 reviewer 复跑确认）；handoff + 5 份上游 review record 提供端到端可冷读证据
- 2 项 minor finding 是 trace 矩阵措辞补强 + 已知 narrative RED，均不阻塞下游 regression gate

可进入 `hf-regression-gate`。

---

## 10. 下一步

- **next_action_or_recommended_skill**: `hf-regression-gate`
- **needs_human_confirmation**: false
- **reroute_via_router**: false
- **rationale**: traceability review 通过，所有维度 ≥ 8/10，4 项 F003 r2 延后 finding 全部端到端闭合，KnowledgeStore extra-key 修复在 design §9 escape hatch 范围内合法，T5 docs lint 对 FR-403c 覆盖充分；2 项 minor 是 trace 矩阵补强机会，不阻塞 regression gate

---

## 11. 结构化返回 JSON

```json
{
  "conclusion": "通过",
  "next_action_or_recommended_skill": "hf-regression-gate",
  "record_path": "docs/reviews/traceability-review-F004-memory-v1-1.md",
  "key_findings": [
    "[minor][LLM-FIXABLE][TZ5] design §3/§9 trace 矩阵未显式登记 KnowledgeStore extra-key 修复（已在 design §9 escape hatch + handoff 中间发现 + code-review §5.2 + test-review §4.5A 共 4 处文档化，trace 矩阵措辞补强机会）",
    "[minor][LLM-FIXABLE][TZ4] T5 implementation handoff RED 段仅 narrative（lint-only，test-review §4.4 已接受现状）"
  ],
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "finding_breakdown": [
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TZ5",
      "summary": "design §3 trace 矩阵 FR-401+FR-405 行的'主要落点'列只提 publisher.py，未显式登记 KnowledgeStore._entry_to_front_matter extra-key 持久化修复；建议在 design §3 / §9 追加锚点，可在 hf-finalize 顺手处理"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TZ4",
      "summary": "F004-T5-implementation-handoff.md RED 段仅 narrative，无真实终端输出；lint-only 任务，影响极小，test-review §4.4 已接受现状"
    }
  ]
}
```

---

**文档状态**: 已落盘。父会话可基于本记录继续 `hf-regression-gate`。
