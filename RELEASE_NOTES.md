# Release Notes

本文件按 feature cycle 倒序记录 Garage OS 的用户可见变化。每个条目对应一次 `hf-finalize` 关闭的 workflow cycle。

---

## F004 — Garage Memory v1.1（发布身份解耦与确认语义收敛）

- 状态: ✅ 已完成（2026-04-19）
- Workflow Profile: `full`
- Execution Mode: `auto`
- Branch / PR: `cursor/f004-memory-polish-1bde` / [#15](https://github.com/hujianbest/garage-agent/pull/15)
- 关联文档:
  - 规格 `docs/features/F004-garage-memory-v1-1-publication-identity-and-confirmation-semantics.md`
  - 设计 `docs/designs/2026-04-19-garage-memory-v1-1-design.md`（r1）
  - 任务计划 `docs/tasks/2026-04-19-garage-memory-v1-1-tasks.md`
  - completion gate `docs/verification/F004-completion-gate.md`
  - regression gate `docs/verification/F004-regression-gate.md`
  - 完整 review 链路：`docs/reviews/{spec,design,tasks,test,code,traceability}-review-F004-memory-v1-1.md`

### 用户可见变化

- **重复发布走 update 链（FR-401）**：同一 candidate 被多次 `accept` / `edit_accept` 时，系统现在会沿用 `KnowledgeStore.update()` 的 `version+=1` 路径，git 历史可读出完整版本链。F003 v1 行为下重复发布会原地覆盖文件且不递增 version，现已修复。
- **Publisher 入口校验前置（FR-402）**：`KnowledgePublisher.publish_candidate(...)` 在入口立即校验 `conflict_strategy`，不再依赖冲突分支命中；调用方误传无效值会立即收到 `ValueError("Allowed: ['abandon', 'coexist', 'supersede']")`。
- **CLI abandon 双路径语义化（FR-403）**：`garage memory review --action=abandon`（主动放弃）与 `--action=accept --strategy=abandon`（因冲突放弃）现在在 confirmation 持久产物 + stdout 文案 + 用户文档 3 个面均可独立识别：
  - `--action=abandon` → confirmation `resolution=abandon` + `conflict_strategy=null` + stdout `"Candidate '...' abandoned without publication attempt"`
  - `--action=accept --strategy=abandon` 命中冲突 → confirmation `resolution=accept` + `conflict_strategy=abandon` + stdout `"Candidate '...' abandoned due to conflict with published knowledge"`
  - `--action=accept --strategy=abandon` 不命中冲突 → 退化为正常 accept publish（与 v1 一致）
  - 详细差异说明见 `docs/guides/garage-os-user-guide.md` 新增的 "Memory review — abandon paths" 段
- **Session memory-extraction-error.json 文件级证据（FR-404）**：`SessionManager._trigger_memory_extraction` 在 archive-time 触发链路任意 phase（`orchestrator_init` / `enablement_check` / `extraction`）失败时，都会在 `.garage/sessions/archived/<session_id>/memory-extraction-error.json` 写入可机器读取的 schema-v1 错误摘要（含 `phase` / `error_type` / `error_message` / `triggered_at`）。session 归档结果保持 `archive_session()=True`；orchestrator 内部 batch-level 错误（`evaluation_summary=extraction_failed`）按 F003 行为继续写入，session 错误文件不重复 batch 信息。
- **F003 KnowledgeStore extra-key 持久化修复**：`KnowledgeStore._entry_to_front_matter()` 之前只持久化 14 个 dataclass 字段，`entry.front_matter` 中的 extra keys（如 publisher 写入的 `supersedes`）从未 make it to disk。本 cycle 按 design § 9 escape hatch 修复：reserved keys 从 dataclass 重建，extras 在末尾合并，兼容 F003 v1 已发布数据。

### 数据与契约影响

- **新增 publisher helper class** `PublicationIdentityGenerator`（`src/garage_os/memory/publisher.py`）：含 `derive_knowledge_id(candidate_id, knowledge_type)` / `derive_experience_id(candidate_id)` 两个纯函数。v1.1 默认实现 = candidate_id 透传，**不破坏 F003 v1 已发布数据**。
- **新增 publisher carry-over contract** `PRESERVED_FRONT_MATTER_KEYS = ("supersedes", "related_decisions")`：在重复发布的 update 路径上自动 carry-over，避免 v1 supersede 链丢失。
- **新增运行时文件**：`.garage/sessions/archived/<session_id>/memory-extraction-error.json`（仅在失败时存在；schema_version=1；旧 session 目录无该文件可正常读取）。
- **CLI surface 新增模块常量**：`MEMORY_REVIEW_ABANDONED_NO_PUB` / `MEMORY_REVIEW_ABANDONED_CONFLICT`（`src/garage_os/cli.py`）。
- **`KnowledgeEntry` / `ExperienceRecord` / `MemoryCandidate` dataclass 字段不变**；`platform.json` schema 不变。

### 验证证据

- `pytest tests/ -q` → **414 passed in ~25s**（F003 baseline 384 → +30 个 F004 新增测试，零回归）
- F004 focused 子集 → `147 passed in ~1s`
- F004 触动文件 mypy 持平 baseline（无新引入错误）
- 完整质量链：spec-review（通过）→ design-review（需修改 → r1 1:1 闭合）→ tasks-review（通过）→ test-review（通过 +2 supplementary tests）→ code-review（通过 +2 docstring 补强）→ traceability-review（通过）→ regression-gate（通过）→ completion-gate（通过）

### 已知限制 / 后续工作

- **Trace 矩阵措辞补强（traceability review TZ5 minor）**：design § 3 / § 9 trace 矩阵未显式登记 KnowledgeStore extra-key 修复（已在 design § 9 escape hatch + 实现交接块 + code-review §5.2 + test-review §4.5A 共 4 处文档化，仅 trace 矩阵措辞机会）。
- **T5 implementation handoff RED 段仅 narrative**（test review TT5 minor）：lint-only 测试，已接受现状。
- **`scripts/benchmark.py` 不补 publisher 专项基准**（ASM-403 已裁决）：当前 `pytest tests/memory/ -q` wall-clock 已能反映回归；如未来用户大量重复发布出现 git diff 噪声升级，可独立立项。
- **CLI `--action=abandon` 仍写 confirmation**：与 design § 10.3 + ADR-403 一致；如要 revisit "abandon 不写 confirmation" 应走 `hf-increment`。
- **Pre-existing baseline mypy 错误**：23 个 F002/F003 历史 mypy 错误超出 F004 范围，由后续 cycle 单独治理。

---

## F003 — Garage Memory（自动知识提取与经验推荐）

- 状态: ✅ 已完成（2026-04-18）
- Workflow Profile: `full`
- Branch / PR: `cursor/f003-quality-chain-3d5f` / [#13](https://github.com/hujianbest/garage-agent/pull/13)
- 关联文档:
  - 规格 `docs/features/F003-garage-memory-auto-extraction.md`
  - 设计 `docs/designs/2026-04-18-garage-memory-auto-extraction-design.md`
  - 任务计划 `docs/tasks/2026-04-18-garage-memory-auto-extraction-tasks.md`
  - completion gate `docs/verification/F003-completion-gate.md`
  - 完整 review 链路：`docs/reviews/{spec,design,tasks,test,code,traceability}-review-F003-*.md`

### 用户可见变化

- **新增 memory 子模块** (`src/garage_os/memory/`)：候选层与正式发布层解耦，提供四类候选（decision / pattern / solution / experience_summary）的存储、提取、确认、发布与冲突探测能力。
- **session 归档自动触发候选提取**：`SessionManager.archive_session()` 在归档完成后自动调用 `MemoryExtractionOrchestrator`。提取失败不阻塞 session 归档，错误以 `evaluation_summary=extraction_failed` batch 写入 `.garage/memory/candidates/batches/`，可冷读。
- **CLI canonical surface — `garage memory review`**：
  - `garage memory review <batch-id>` 查看候选批次摘要
  - `--action accept|edit_accept|reject|batch_reject|defer|abandon|show-conflicts`
  - `--strategy coexist|supersede|abandon` 处理与已发布知识的冲突；`accept` / `edit_accept` 命中相似条目时**强制要求** `--strategy`，不再静默写 supersede（FR-304）
- **`garage run` 主动推荐**：当 `recommendation_enabled=true` 时，每次 `garage run <skill>` 在执行前展示一次推荐摘要（含 `match_reasons`），仅消费正式发布态。
- **正式知识与经验记录扩展**：`KnowledgeEntry` / `ExperienceRecord` 新增 `source_evidence_anchor(s)`、`confirmation_ref`、`published_from_candidate` 等可追溯字段（设计 §11.4）。
- **Feature flag 双开关**：`platform.json` 新增 `memory.extraction_enabled` 与 `memory.recommendation_enabled`，默认两者均为 `false`，关闭时现有 `garage` 主链不回归。

### 数据与契约影响

- 新增运行时目录：
  - `.garage/memory/candidates/batches/`（batch JSON）
  - `.garage/memory/candidates/items/`（candidate markdown + YAML front matter）
  - `.garage/memory/confirmations/`（confirmation JSON）
- 新增 `.garage/config/platform.json` 字段：`memory.extraction_enabled`、`memory.recommendation_enabled`（默认全 `false`，向后兼容）。
- `KnowledgeStore` / `ExperienceIndex` 接受额外可选字段；旧 entry 在缺字段时仍可读，未做强制迁移。

### 验证证据

- `pytest tests/ -q` → `384 passed in ~24s`（基线 369 → 376 → 384，每轮回流 fresh evidence，零回归）
- F003 任务范围聚焦验证 → `145 passed in ~16s`
- 完整质量链：test-review r1（需修改）→ test-review r2（通过）→ test-review r3 增量（通过）→ code-review r1（需修改）→ code-review r2（通过）→ traceability-review（通过，6 维度 ≥7/10）→ regression-gate（通过）→ completion-gate（通过）

### 已知限制 / 后续工作

- **延后接受（USER-INPUT）**：`KnowledgePublisher` 当前用 `candidate_id` 直接作为 `KnowledgeEntry.id`。同一候选重复 `accept` / `edit_accept` 会原地覆盖前一次发布，不触发 `KnowledgeStore.update()` 的版本递增链路。spec / design §11.4 未硬要求"必须解耦"，此项在 `code-review r1 finding 5` → `code-review r2` → `traceability-review TZ5` → `completion-gate` 中均**显式延后**，建议下一个 cycle 作为独立 task 推进（带版本后缀或独立 ID）。
- **延后处理（LLM-FIXABLE，行为变更类）**：
  - `KnowledgePublisher.publish_candidate` 仅在 `similar_entries` 非空时校验 `VALID_CONFLICT_STRATEGIES`，建议在入口处提前校验
  - CLI `--action=abandon` 与 `--action=accept --strategy=abandon` 语义重叠，待产品侧确认是否需要差异化
  - `SessionManager._trigger_memory_extraction` 仍用 `logger.warning` 兜底（FR-307 文件级证据由 orchestrator batch 文件承担），如需 session 侧双写可独立任务推进
- 本轮 finalize 已顺手清理：移除 `extraction_orchestrator.py:68` 已 stale 的 `# pragma: no cover` 注释；为 `.garage/config/platform.json` 补 `memory` 块；为 T2-T9 testDesignApproval 治理路径写 merge note (`docs/approvals/F003-T2-T9-test-design-merge-note.md`)。

---

## Previous Cycles

- **F002 — Garage Live**：✅ 已完成（CLI + 真实 Claude Code 集成，436 测试通过）
- **F001 — Garage Agent OS Phase 1**：✅ 已完成（T1-T22，416 测试通过）
