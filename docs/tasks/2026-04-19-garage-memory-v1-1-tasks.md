# T004: Garage Memory v1.1 任务计划

- 状态: 已批准（auto-mode approval；见 `docs/approvals/F004-tasks-approval.md`）
- 主题: F004 — Garage Memory v1.1（发布身份解耦与确认语义收敛）
- 关联规格: `docs/features/F004-garage-memory-v1-1-publication-identity-and-confirmation-semantics.md`
- 关联设计: `docs/designs/2026-04-19-garage-memory-v1-1-design.md`
- 关联审批:
  - `docs/approvals/F004-spec-approval.md`
  - `docs/approvals/F004-design-approval.md`
- 关联评审:
  - `docs/reviews/spec-review-F004-memory-v1-1.md`（通过）
  - `docs/reviews/design-review-F004-memory-v1-1.md`（需修改 → r1 by author self-check 1:1 闭合）

---

## 1. 概述

本计划把 D004 设计拆成 5 个可独立验证的工程任务，目标是收敛 F003 显式延后的 4 项 finding（USER-INPUT minor 1 项 + LLM-FIXABLE minor 3 项），同时**保持 F003 现有 145 个 memory focused 测试 + 384 个 full suite 零回归**。

任务边界：

- 不修改 `KnowledgeStore` / `ExperienceIndex` / `CandidateStore` / `MemoryExtractionOrchestrator` 公开 API
- 不修改 `KnowledgeEntry` / `ExperienceRecord` / `MemoryCandidate` dataclass 字段
- 不修改 `platform.json` schema
- 不引入新 PyPI 依赖、不引入数据库、不引入常驻服务

---

## 2. 里程碑

| 里程碑 | 目标 | 任务数 | 退出标准 |
|--------|------|--------|----------|
| **M1: Publisher 重构** | publisher 入口校验前置 + 发布身份生成器 + store-or-update 决策 + supersede 链 carry-over + self-conflict 短路 | 2 (T1, T2) | publisher 单元测试可独立验证 FR-401 / FR-402 / FR-405 supersede 不变量 |
| **M2: CLI + Session 表面收敛** | CLI abandon 双路径文案与 confirmation 字段差异化 + session 触发链路文件级留痕 | 2 (T3, T4) | CLI / SessionManager 测试可独立验证 FR-403 / FR-404 |
| **M3: 文档 + 全链路回归** | 用户指南 + 开发者指南 + 全 suite 回归 | 1 (T5) | `pytest tests/ -q` ≥ 384 passed; 用户/开发者指南可被 grep 检索到关键段 |

---

## 3. 文件 / 工件影响图

### 3.1 修改的源码模块

| 文件 | 影响类型 | 说明 |
|------|---------|------|
| `src/garage_os/memory/publisher.py` | 修改 | 新增 `PublicationIdentityGenerator` helper class；`publish_candidate` 前置 `_validate_conflict_strategy`；`store-or-update` 决策；supersede 链 carry-over；self-conflict 短路 |
| `src/garage_os/runtime/session_manager.py` | 修改 | 重构 `_trigger_memory_extraction` 为分 phase try/except；新增 `_persist_extraction_error` |
| `src/garage_os/cli.py` | 修改 | 新增 `MEMORY_REVIEW_ABANDONED_NO_PUB` / `MEMORY_REVIEW_ABANDONED_CONFLICT` 模块常量；abandon 双路径 confirmation 字段语义化 + stdout 文案 |

### 3.2 修改的文档

| 文件 | 影响类型 | 说明 |
|------|---------|------|
| `docs/guides/garage-os-user-guide.md` | 修改 | 新增 "Memory review abandon paths" 段，显式区分 `--action=abandon` vs `--action=accept --strategy=abandon` |
| `docs/guides/garage-os-developer-guide.md` | 修改 | 新增 "Publisher 重复发布与 ID 生成规则" 段；新增 "Session memory-extraction-error.json schema" 段 |

### 3.3 新增 / 修改的测试

| 文件 | 影响类型 | 说明 |
|------|---------|------|
| `tests/memory/test_publisher.py` | 修改 + 新增 | 新增重复发布、入口校验、supersede 链 carry-over、self-conflict 短路、决定性 ID 等测试；可能微调若干现有断言 |
| `tests/runtime/test_session_manager.py` | 修改 + 新增 | 新增 3 个 phase 失败 + 1 个成功路径的 `memory-extraction-error.json` 测试 |
| `tests/test_cli.py`（或新建 `tests/cli/test_memory_review.py`） | 修改 + 新增 | 新增 abandon 双路径 confirmation + stdout 测试 |
| `tests/test_documentation.py`（若不存在则新建） | 新增 | 用户指南 abandon 段落存在性检查 |

---

## 4. 需求与设计追溯

| 规格 / 设计锚点 | 覆盖任务 |
|----------------|----------|
| `FR-401` 重复发布版本链 + 设计 §10.1 store-or-update + §11.2 publish_candidate 契约 | T1, T2 |
| `FR-401` + `FR-405` supersede 链 carry-over + 设计 §10.1 + §11.2.1 PRESERVED_FRONT_MATTER_KEYS | T2 |
| `FR-401` self-conflict 短路 + 设计 §10.1.1 | T2 |
| `FR-402` 入口立即校验 + 设计 §10.2 + §11.2 入口校验段 + ADR-402 | T1 |
| `FR-403a` confirmation 持久差异化 + 设计 §10.3 + ADR-403 | T3 |
| `FR-403b` CLI 输出文案 + 设计 §11.5 输出常量 | T3 |
| `FR-403c` 用户文档段 + 设计 §9 模块表 | T5 |
| `FR-404` session 触发证据 + 设计 §10.4 + §11.3 + §11.4 + ADR-404 | T4 |
| `FR-405` 兼容性（145 + 384 全 suite 0 回归） | T2 + T3 + T4 + T5（每任务 verify 中显式跑 affected suite） |
| `NFR-401` 决定性发布身份 + 设计 §11.1 generator contract | T1 |
| `NFR-402` 不退化 + 设计 §12 + ASM-403 | T2（wall-clock 对比） |
| `IFR-401` / `IFR-402` 复用 update | T2 |
| `CON-401~404` | T4 + T5 |
| 设计 §11.4 `memory-extraction-error.json` schema | T4 |
| `CON-403` schema 兼容（confirmation 字段不删除 + `memory-extraction-error.json` 旧版本无该文件可正常读取） | T3, T4 |

---

## 5. 任务拆解

### T1. PublicationIdentityGenerator + publisher 入口校验前置

- **目标**: 在 `src/garage_os/memory/publisher.py` 中新增 `PublicationIdentityGenerator` 私有 helper class（含 `derive_knowledge_id` / `derive_experience_id`），并把 `_validate_conflict_strategy` 提到 `publish_candidate` 入口（任何业务分支前）。
- **Acceptance**:
  - `PublicationIdentityGenerator` 是纯函数：`derive_knowledge_id(c, t)` 任意 N 次调用返回同值；`derive_experience_id(c)` 同理（NFR-401）
  - `derive_knowledge_id(c, KnowledgeType.DECISION)` 默认实现返回 `c`（保 F003 v1 已发布数据零迁移；ADR-401）
  - `publish_candidate(...)` 在第一行（candidate retrieve、action 早返回、conflict 探测之前）调 `_validate_conflict_strategy(conflict_strategy)`
  - 调用方传 `conflict_strategy="garbageX"` 抛 `ValueError`，错误消息含 `Allowed: ['abandon', 'coexist', 'supersede']`，无论是否命中相似条目（FR-402 验收 1 + 4）
  - 调用方传 `conflict_strategy=None` → 不校验（FR-402 验收 3）
  - 调用方传 `conflict_strategy="coexist"` 且不命中相似条目 → 不报错（FR-402 验收 2）
- **依赖**: -
- **Ready When**: F004 spec/design approval 已完成
- **初始队列状态**: ready
- **Selection Priority**: P1
- **Files / 触碰工件**:
  - `src/garage_os/memory/publisher.py`
  - `tests/memory/test_publisher.py`
- **测试设计种子（hf-test-driven-dev 起点；fail-first）**:
  1. **fail-first**: `test_publication_identity_generator_is_deterministic` — 同一 `(candidate_id, type)` 调 100 次返回同值
  2. `test_publication_identity_default_returns_candidate_id` — 默认实现 `derive_knowledge_id("c-001", DECISION)` 返回 `"c-001"`（保 v1 兼容）
  3. `test_publish_candidate_rejects_garbage_strategy_at_entry` — 传 `conflict_strategy="garbageX"` 立即 `ValueError`，无论是否有冲突
  4. `test_publish_candidate_accepts_valid_strategy_without_conflict` — 传 `conflict_strategy="coexist"` 且无冲突 → 正常发布
  5. **关键边界**: `test_publish_candidate_none_strategy_passes_when_no_conflict` — 兼容 v1 行为
- **Verify**:
  - `uv run pytest tests/memory/test_publisher.py -q`
  - `uv run mypy src/garage_os/memory/publisher.py`
- **预期证据**: 5 个新测试通过；F003 现有 publisher 测试不变绿
- **完成条件**: publisher 入口校验前置 + ID 生成器接口稳定，T2 可基于该 generator 直接做 store-or-update 决策

### T2. publisher store-or-update 决策 + supersede 链 carry-over + self-conflict 短路

- **目标**: 在 T1 基础上，让 `publish_candidate` 的 knowledge / experience 路径都先 `retrieve(identity)` → 存在则 `update`、不存在则 `store`；并在 update 路径上 carry-over `PRESERVED_FRONT_MATTER_KEYS`；在 conflict 判定前对 `similar_entries` 做 self-conflict 短路。
- **Acceptance**:
  - 同一 candidate `c-001` (decision) 第 1 次 `accept` → `KnowledgeEntry id=c-001, version=1`，markdown 文件名 `decision-c-001.md`
  - 同一 candidate 第 2 次 `edit_accept` → `KnowledgeStore.list_entries(DECISION)` 仍只有 1 条 `id=c-001`，`version=2`，文件名不变（FR-401 验收 1+2）
  - 同一 candidate (experience_summary) 重复发布 → `ExperienceIndex` 中仍只有 1 条 `record_id` 与之对应（FR-401 验收 3）
  - v1 已带 `front_matter["supersedes"] = ["k-X", "k-Y"]` 的 entry，重复发布后新 entry `front_matter["supersedes"]` 至少含 `["k-X", "k-Y"]`（FR-405 supersede 不变量；§11.2.1）
  - v1 已带 `related_decisions = ["k-Z"]` 的 entry，重复发布后新 entry `related_decisions` 至少含 `["k-Z"]`（§11.2.1）
  - 重复 `accept` 同一 candidate（v1 已发布、`title` 与 `tags` 命中自身），publisher 在 require strategy 前剔除 `similar_entries` 中等于 `derive_knowledge_id(candidate_id, type)` 的元素；剔除后空 → 不要求 strategy（§10.1.1）
  - F003 现有的 `test_publish_orchestrator_output_end_to_end` 通过（可能需要轻微调整断言，预期不破坏）
  - `pytest tests/memory/ -q` 总时长不超过 F003 baseline 的 110%（NFR-402）
- **依赖**: T1
- **Ready When**: T1=done
- **初始队列状态**: pending
- **Selection Priority**: P1
- **Files / 触碰工件**:
  - `src/garage_os/memory/publisher.py`
  - `tests/memory/test_publisher.py`
- **测试设计种子（hf-test-driven-dev；fail-first）**:
  1. **fail-first**: `test_repeated_accept_uses_update_increments_version` — 第 1 次 accept → version=1；第 2 次 edit_accept → version=2，文件名不变
  2. `test_retrieve_after_repeated_accept_returns_latest_version` — 重复发布后 `KnowledgeStore.retrieve(DECISION, "c-001").version == 2`
  3. `test_repeated_publish_experience_summary_updates_index` — experience 路径仅 1 条 record_id
  4. **FR-405 关键不变量**: `test_repeated_publish_preserves_supersedes_chain_from_v1` — fixture 模拟 v1 已发布 entry `front_matter["supersedes"] = ["k-X"]`，第 2 次发布后该字段保留 `["k-X"]`（可能合并新 supersede）
  5. `test_repeated_publish_preserves_related_decisions_from_v1` — 同上但针对 `related_decisions` 字段
  6. **§10.1.1 关键边界**: `test_repeated_accept_short_circuits_self_conflict` — v1 已发布同名 entry，重复 `accept` 不要求 `--strategy`
  7. **NFR-402 性能**: baseline T0 通过"实施前 `git stash` 当前修改 → `git checkout` F003 cycle 完结 commit (`44f85ab` Merge PR #14 或更早 F003 closeout commit `772e4dd`) → `uv run pytest tests/memory/ -q` 跑 3 次取均值"获取；T1 通过"切回 v1.1 实现分支 → 同样 3 次取均值"获取；断言 T1 ≤ 1.1 * T0
- **Verify**:
  - `uv run pytest tests/memory/ -q`（重点 publisher.py 测试）
  - `uv run pytest tests/ -q`（FR-405 全 suite 回归）
  - `uv run mypy src/garage_os/memory/publisher.py`
- **预期证据**: 7 个新增 publisher 测试通过；145 个 memory focused + 384 个 full suite 全绿；wall-clock 不退化超过 10%
- **完成条件**: publisher 重复发布幂等 + supersede 不变量保留 + self-conflict 不触发误判，主链可端到端验证

### T3. CLI abandon 双路径 confirmation + stdout 文案差异化

- **目标**: 在 `src/garage_os/cli.py` 的 `garage memory review` handler 中，让 `--action=abandon` 与 `--action=accept --strategy=abandon` 在 confirmation 持久产物 + stdout 文案上独立可识别。
- **Acceptance**:
  - cli.py 模块级常量 `MEMORY_REVIEW_ABANDONED_NO_PUB = "Candidate '{cid}' abandoned without publication attempt"` 与 `MEMORY_REVIEW_ABANDONED_CONFLICT = "Candidate '{cid}' abandoned due to conflict with published knowledge"` 已定义且互不重叠
  - `--action=abandon` 路径：候选 `status=abandoned`；confirmation 文件 `resolution=abandon` + `conflict_strategy=null`；stdout 含 `MEMORY_REVIEW_ABANDONED_NO_PUB.format(cid=...)`（FR-403a 验收 1 + FR-403b 验收 1）
  - `--action=accept --strategy=abandon` 且命中相似条目（v1 已发布同名 entry 已被 §10.1.1 短路剔除，所以这里指**真正的不同 entry 命中**）：候选 `status=abandoned`；confirmation 文件 `resolution=accept` + `conflict_strategy=abandon`；stdout 含 `MEMORY_REVIEW_ABANDONED_CONFLICT.format(cid=...)`（FR-403a 验收 2 + FR-403b 验收 2）
  - `--action=accept --strategy=abandon` 且不命中相似条目：行为退化为正常 accept 发布，候选 `status=published`，confirmation `resolution=accept` + `conflict_strategy=null`（FR-403a 验收 3）
  - 两条 abandon 路径 stdout 字符串可被 grep 区分（FR-403b 验收 3）
  - F003 现有的 `test_memory_review_abandon_skips_publication` 与 `test_memory_review_accept_requires_strategy_when_conflict_exists` 测试通过（可能需要轻微更新断言）
- **依赖**: T2（依赖 §10.1.1 self-conflict 短路实现，避免 v1 已发布同名 entry 触发本任务的 conflict 路径）
- **Ready When**: T2=done
- **初始队列状态**: pending
- **Selection Priority**: P1
- **Files / 触碰工件**:
  - `src/garage_os/cli.py`
  - `tests/test_cli.py`（或新建 `tests/cli/test_memory_review.py`）
- **测试设计种子（fail-first）**:
  1. **fail-first**: `test_memory_review_abandon_writes_resolution_abandon_with_null_strategy` — `--action=abandon`，断言 confirmation `resolution=abandon` + `conflict_strategy=null`
  2. `test_memory_review_accept_with_strategy_abandon_writes_resolution_accept` — `--action=accept --strategy=abandon` + 真实冲突，断言 confirmation `resolution=accept` + `conflict_strategy=abandon`
  3. `test_memory_review_abandon_outputs_no_pub_marker` — stdout 含 `MEMORY_REVIEW_ABANDONED_NO_PUB`
  4. `test_memory_review_conflict_abandon_outputs_conflict_marker` — stdout 含 `MEMORY_REVIEW_ABANDONED_CONFLICT`
  5. **关键边界**: `test_memory_review_two_abandon_markers_do_not_overlap` — 两个常量 grep 后唯一命中各自路径
  6. `test_memory_review_accept_with_abandon_strategy_no_conflict_falls_through_to_publish` — 不命中冲突时退化为 accept publish
- **Verify**:
  - `uv run pytest tests/test_cli.py -q`（或对应的新文件）
  - `uv run pytest tests/ -q`（全 suite 回归）
- **预期证据**: 6 个新增/修改的 CLI 测试通过；F003 现有 CLI 测试不变绿
- **完成条件**: CLI canonical surface 单一职责，两条 abandon 路径在持久层 + stdout 双层可识别

### T4. SessionManager._trigger_memory_extraction_safely 三 phase 持久化

- **目标**: 在 `src/garage_os/runtime/session_manager.py` 中重构 `_trigger_memory_extraction` 为分 phase try/except；新增 `_persist_extraction_error(session_id, phase, exc)`。
- **Acceptance**:
  - phase 1（`orchestrator_init`）失败：`archive_session()` 仍 `True`；`.garage/sessions/archived/<id>/memory-extraction-error.json` 含 `phase="orchestrator_init"` + `error_type` + `error_message` + `triggered_at` + `session_id` + `schema_version="1"`（FR-404 验收 1 + §11.4 schema）
  - phase 2（`enablement_check`）失败：同上但 `phase="enablement_check"`（FR-404 验收 2）
  - phase 3（`extraction`）失败：同上但 `phase="extraction"`；orchestrator 内部 batch 文件（`evaluation_summary=extraction_failed`）仍按 F003 行为写入；session 错误文件不重复写 batch 信息（FR-404 验收 3）
  - 触发链路成功完成：`memory-extraction-error.json` 不存在；行为与 F003 一致（FR-404 验收 4）
  - `extraction_enabled=false`：不写错误文件、不抛异常、行为与 F003 一致
  - `logger.warning(...)` 调用保留（与文件层双层防护）
- **依赖**: -（与 T1/T2/T3 解耦，可与 T1 并行；但实施顺序按 Selection Priority 让 router 优先选 T1 → T2 → T3 → T4）
- **Ready When**: F004 spec/design approval 已完成
- **初始队列状态**: ready（与 T1 真并行；router 按 Selection Priority P2 < P1 自然让 T4 排在 T3 后被选中）
- **Selection Priority**: P2
- **Files / 触碰工件**:
  - `src/garage_os/runtime/session_manager.py`
  - `tests/runtime/test_session_manager.py`
- **测试设计种子（fail-first）**:
  1. **fail-first**: `test_archive_session_persists_extraction_error_orchestrator_init` — monkeypatch `MemoryExtractionOrchestrator.__init__` 抛错；断言 `archive_session()` 返回 True + 文件存在 + `phase="orchestrator_init"`
  2. `test_archive_session_persists_extraction_error_enablement_check` — 同上但 monkeypatch `is_extraction_enabled` 抛错
  3. `test_archive_session_persists_extraction_error_extraction` — 同上但 monkeypatch `extract_for_archived_session` 抛错；断言不重写 orchestrator batch
  4. **关键边界**: `test_archive_session_no_error_file_when_extraction_succeeds` — 成功路径下 `memory-extraction-error.json` 不存在
  5. `test_archive_session_no_error_file_when_extraction_disabled` — `extraction_enabled=false` 路径下不写文件
  6. **schema 不变量**: `test_memory_extraction_error_json_has_full_schema` — 文件存在时含全部 6 个字段（schema_version, session_id, phase, error_type, error_message, triggered_at）
- **Verify**:
  - `uv run pytest tests/runtime/test_session_manager.py -q`
  - `uv run pytest tests/ -q`（全 suite 回归）
- **预期证据**: 6 个新增 session_manager 测试通过；F003 现有 session_manager 测试不变绿
- **完成条件**: archive-time 触发链路任意失败点都在文件层留痕，FR-307 session 层证据零盲点

### T5. 用户指南 + 开发者指南 + 全链路最终回归

- **目标**: 把 `docs/guides/garage-os-user-guide.md` 与 `docs/guides/garage-os-developer-guide.md` 同步到 v1.1 行为；执行最终 384 + 145 全 suite 回归。
- **Acceptance**:
  - `garage-os-user-guide.md` 中 memory review 相关段含 1 段独立"Abandon paths"说明，明确两条路径的语义、何时使用、对 confirmation 持久产物的影响（FR-403c 验收 1+2+3）
  - `garage-os-developer-guide.md` 含 1 段"Publisher 重复发布与 ID 生成规则"，描述 `PublicationIdentityGenerator` 默认实现 + 重复发布走 `KnowledgeStore.update()` 的 version 递增链路 + supersede 链 carry-over 不变量（NFR-401 验收 2）
  - `garage-os-developer-guide.md` 含 1 段"Session memory-extraction-error.json schema"，描述文件路径、字段集合、phase 封闭枚举（CON-404）
  - `pytest tests/ -q` ≥ 384 passed（FR-405 验收 2）
  - `pytest tests/memory/ -q` 全绿（FR-405 验收 1）
  - `pytest tests/memory/ -q` 总时长不超过 baseline 的 110%（NFR-402）
- **依赖**: T1, T2, T3, T4
- **Ready When**: T1=done AND T2=done AND T3=done AND T4=done
- **初始队列状态**: pending
- **Selection Priority**: P3
- **Files / 触碰工件**:
  - `docs/guides/garage-os-user-guide.md`
  - `docs/guides/garage-os-developer-guide.md`
  - `tests/test_documentation.py`（如果不存在则新建一个最小 docs lint）
- **测试设计种子**:
  1. **docs lint**: `test_user_guide_memory_review_documents_both_abandon_paths` — `garage-os-user-guide.md` 含 "abandon" + "publication attempt" + "conflict" 关键 token
  2. `test_developer_guide_documents_publication_identity_generator` — `garage-os-developer-guide.md` 含 "PublicationIdentityGenerator" + "version" + "update" 关键 token
  3. `test_developer_guide_documents_memory_extraction_error_json_schema` — `garage-os-developer-guide.md` 含 "memory-extraction-error.json" + "phase" + 三个 phase 枚举值
- **Verify**:
  - `uv run pytest tests/ -q`（全 suite 回归 ≥ 384 passed）
  - `uv run pytest tests/memory/ -q`（145 个 memory focused 0 回归）
  - `uv run mypy src/`（类型检查）
  - `uv run ruff check src/ tests/`（lint）
  - 手工 grep `docs/guides/garage-os-user-guide.md` 与 `garage-os-developer-guide.md` 验证关键段存在
- **预期证据**: 文档段已落盘可冷读；全 suite 全绿；类型与 lint 检查通过
- **完成条件**: 用户文档 + 开发者文档同步；F004 全链路验收完整可被审计

---

## 6. 任务队列投影

| Task ID | Status | Depends On | Ready When | Selection Priority |
|---------|--------|-----------|-----------|-------------------|
| T1 | ready | - | F004 spec/design approval 已完成 | P1 |
| T2 | pending | T1 | T1=done | P1 |
| T3 | pending | T2 | T2=done | P1 |
| T4 | ready | - | F004 spec/design approval 已完成 | P2 |
| T5 | pending | T1, T2, T3, T4 | T1=done AND T2=done AND T3=done AND T4=done | P3 |

注：T1 与 T4 在 spec/design approval 通过时同时 ready；按 §6.1 选择规则，P1 优先于 P2，所以 router 第一轮选 T1。T4 的 `Status=ready` 反映"无前置任务依赖"，与 T1 是真并行候选；router 通过 Selection Priority 排序锁定唯一 active task。

### 6.1 唯一 Current Active Task 选择规则

启动时：T1 与 T4 都 ready；T1 是 P1，T4 是 P2 → router 锁定 T1。

T1 完成后（router 重选）：T2 因 `Depends On=T1` 与 `Ready When=T1=done` 满足而成为新 ready；T4 仍 ready (P2)。T2 Priority 更高（P1 > P2）→ 选 T2。

T2 完成后（router 重选）：T3 ready (P1)；T4 仍 ready (P2)。T3 优先 → 选 T3。

T3 完成后（router 重选）：T4 ready (P2) 是唯一 next-ready → 选 T4。

T4 完成后（router 重选）：T5 ready (P3) 是唯一 next-ready → 选 T5。

T5 完成后：无剩余任务 → `hf-finalize`。

**不变量**：每轮 router 重选时 ready 候选可能不止一个（T4 在 T1/T2/T3 完成期间始终 ready），但 Selection Priority 保证唯一最高优 ready，避免 hard stop。

### 6.2 router 重选触发点

每个 task 通过 `hf-completion-gate` 后，父会话回到 `hf-workflow-router`：
- 若存在唯一 next-ready task（按上表 Selection Priority + Depends On + Ready When 判定），锁定为新的 `Current Active Task`，进入 `hf-test-driven-dev`
- 若不存在剩余任务（T5 完成后），进入 `hf-finalize`
- 若多个 ready task 优先级相同（不会出现，本计划已显式保证 P1 > P2 > P3 唯一），hard stop

---

## 7. 测试设计 approval 治理路径

沿用 F003 已确立的 testDesignApproval 治理（见 `docs/approvals/F003-T2-T9-test-design-merge-note.md`）：每个 task 进入 RGR (Red-Green-Refactor) 前，由 task 实现者在 task implementation handoff 中显式列出 test design list（fail-first 测试 + 覆盖测试 + 关键边界），auto mode 下由 author 写 self-approval merge note。

本计划的测试设计种子（见 §5 各 task 的"测试设计种子"段）作为 RGR 的初始输入；hf-test-driven-dev 在实施时可补充覆盖测试，但**fail-first 测试与关键边界测试不能省略**。

---

## 8. 风险与缓解

| 风险 | 触发条件 | 缓解 |
|------|---------|------|
| `_to_knowledge_entry` 重新构造 front_matter 丢失 v1 supersede 链 | T2 实现忘记 carry-over `PRESERVED_FRONT_MATTER_KEYS` | T2 fail-first 测试 `test_repeated_publish_preserves_supersedes_chain_from_v1` 锁住；设计 §11.2.1 contract 显式列出 |
| ConflictDetector self-conflict false-positive 让 CLI 强制 `--strategy` | T2 实现忘记 §10.1.1 短路逻辑 | T2 测试 `test_repeated_accept_short_circuits_self_conflict` 锁住 |
| FR-405 兼容性回归（145 / 384 测试不变绿） | 任意 task 触动现有断言 | 每个 task verify 段都跑全 suite；T5 最终回归是兜底 |
| NFR-402 性能退化 | T2 引入额外 retrieve 调用，但 KnowledgeStore in-memory index 是 O(1)，影响应可忽略 | T2 测试 7 显式 wall-clock 对比；ASM-403 已裁决不补 publisher 专项 benchmark |
| 命名漂移（`derive_id` vs `derive_knowledge_id`） | T1 实现引入与 design §11.1 contract 不一致的方法名 | T1 测试 `test_publication_identity_generator_is_deterministic` 显式调 `derive_knowledge_id`；design r1 已统一全文档命名 |
| docs lint 与代码同步漂移 | T5 文档段落与 T1~T4 实际行为不一致 | T5 测试种子 1~3 用 token 检查；CI grep 回归会捕获 |

---

## 9. 不在本任务计划范围

- `KnowledgeEntry.id` schema 升级（含 namespace / scope / 版本后缀）
- LLM-based candidate 去重 / 相似度算法升级
- 异步 / 队列 / 后台服务承接 `_trigger_memory_extraction`
- 新 CLI 顶级命令 / 新子命令
- `platform.json` schema 变更
- 改 4 类候选 contract（decision / pattern / solution / experience_summary）
- 自动 skill 生成（属于 Stage 3）
- 在 `scripts/benchmark.py` 中追加 publisher 专项基准（按 ASM-403 已裁决）

---

## 10. Open Questions

无阻塞性开放问题。

非阻塞、可在 hf-test-driven-dev 阶段或 hf-tasks-review 阶段顺手收敛：

1. T5 文档 lint 测试（`test_documentation.py`）若项目历史无该文件，是否新建？建议**新建**，作为 docs/code 同步保护。
2. T2 性能测试 #7（`pytest tests/memory/ -q` wall-clock 对比）是否需要在 CI 中长期跑？建议**不固化**，仅作为 T2 实现期一次性验证；若 CI 偶尔抖动 >10% 可手动复跑判断。

---

**文档状态**: 已批准（auto-mode approval；见 §0 状态字段）。

**下一步**: 进入 `hf-test-driven-dev`，先实现 T1（Current Active Task）。
