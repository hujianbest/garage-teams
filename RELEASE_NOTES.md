# Release Notes

本文件按 feature cycle 倒序记录 Garage OS 的用户可见变化。每个条目对应一次 `hf-finalize` 关闭的 workflow cycle。

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
