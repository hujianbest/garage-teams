# Approval Record - F006 Design

- Artifact: `docs/designs/2026-04-19-garage-recall-and-knowledge-graph-design.md`
- Approval Type: `designApproval`
- Approver: cursor cloud agent (auto-mode policy approver)
- Date: 2026-04-19
- Workflow Profile / Execution Mode: `standard` / `auto`
- Workspace Isolation: `in-place`

## Evidence

- Round 1 review: `docs/reviews/design-review-F006-recall-and-knowledge-graph.md` — `通过`
  - 0 critical / 0 important / 3 minor (all LLM-FIXABLE)
  - 全部 3 项 minor 在 approval-time inline-fixed:
    - D2: `ERR_LINK_FROM_NOT_FOUND_FMT` 与 `KNOWLEDGE_NOT_FOUND_FMT` alias 关系在 §9.5 注释里说明
    - D5: §10.1 mermaid 加 Note 说明 `skill_name_only` fallback 的统一打印口径
    - D6: §12 失败模式表新增"graph 入边扫描遇损坏 entry"行，引用 `knowledge_store.py:299-300` 现有兜底
  - 关键源码事实经 reviewer 磁盘验证：
    - `_DATACLASS_FRONT_MATTER_KEYS` 含 `related_decisions` / `related_tasks`（update 持久化保证）
    - `RecommendationService.recommend()` 仅 tags 也能产生 score>0 命中（FR-601 + FR-602 mixed recall 可行）
    - `ExperienceIndex.list_records()` 是 O(N) 全读（NFR-603 < 1.5s 可达）
- Auto-mode policy basis: `AGENTS.md` 未限制 standard cycle 内 design 子节点 auto resolve

## Decision

**Approved**. Design 状态由 `草稿` → `已批准（auto-mode approval r1）`。下一步 = `hf-tasks`，输入为本 design 的 §13 / §14 task readiness 段。

## Hash & 锚点

- Design 初稿: `57af7ba`
- 修订 + approval（同 commit）: 见 "design(F006): r1 follow-up — D2 alias note, D5 skill_name_only fallback note, D6 corrupt-entry failure mode; approve design"
