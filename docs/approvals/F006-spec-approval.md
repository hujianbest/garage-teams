# Approval Record - F006 Spec

- Artifact: `docs/features/F006-garage-recall-and-knowledge-graph.md`
- Approval Type: `specApproval`
- Approver: cursor cloud agent (auto-mode policy approver)
- Date: 2026-04-19
- Workflow Profile / Execution Mode: `standard` / `auto`
- Workspace Isolation: `in-place`

## Evidence

- Round 1 review: `docs/reviews/spec-review-F006-recall-and-knowledge-graph.md` — `需修改`
  - 0 critical / 1 important / 4 minor
  - F-1 important USER-INPUT 提供了 3 条裁决路径（A 缩小 scope / B CLI-internal scorer / C 放宽 CON-605）；选择 **Path B** —— 在 `cli.py` 新增纯本地 `_recommend_experience()` helper 扫描 `ExperienceIndex.list_records()`；理由：保留 F003 `garage run` 路径行为不变、保留 CON-605、与 F005 同地（cli.py handler 层）扩展、零模块边界变化
- Round 1 follow-up commit: `bbb6489` "fix(F006): spec r1 follow-up — split recommend into FR-601 knowledge / FR-602 experience halves; FR-603 zero-results unified; FR-608 keep F005 subcommands; minor wording fixes"
- Round 2 review: `docs/reviews/spec-review-F006-recall-and-knowledge-graph-r2.md` — `通过`
  - 0 critical / 0 important / 0 minor
  - 全部 5 项 round-1 finding 闭合验证
- Auto-mode policy basis: `AGENTS.md` 未限制 standard cycle 内 spec 子节点 auto resolve

## Decision

**Approved**. Spec 状态由 `草稿` → `已批准（auto-mode approval）`。下一步 = `hf-design`，输入为本 spec + F003 `RecommendationService` / `RecommendationContextBuilder` 现有实现 + F005 CLI handler 模式。

## Hash & 锚点

- Spec 初稿: `79bd324`
- 修订: `bbb6489`
