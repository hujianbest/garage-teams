# Approval Record - F005 Design

- Artifact: `docs/designs/2026-04-19-garage-knowledge-authoring-cli-design.md`
- Approval Type: `designApproval`
- Approver: cursor cloud agent (auto-mode policy approver)
- Date: 2026-04-19
- Workflow Profile / Execution Mode: `standard` / `auto`
- Workspace Isolation: `in-place`

## Evidence

- Round 1 review: `docs/reviews/design-review-F005-knowledge-authoring-cli.md` — `通过`
  - 0 critical / 0 important / 4 minor (all LLM-FIXABLE)
  - All 4 minor findings (CON-501 wording / ADR-503 publisher artifacts wording / §10.2 mermaid signature / `edit` date field) closed in approval-time follow-up commit before approval is recorded
- Approval-time follow-up commit收敛内容（不影响 task plan 拆解，故内联收敛而非另开 r2）:
  - CON-501 trace 行明确 `experience` 是新引入的二级 subparser，不破坏顶级命令复用
  - ADR-503 重写：源标记区分性靠 `"cli:"` 前缀命名空间，不依赖 `artifacts` 是否为空；与 publisher 写入 path-style artifact 共存
  - §10.2 mermaid: `KnowledgeStore.update()` 实际签名 `-> str`；version 在 `entry.version += 1` in-place，handler 应回读 `entry.version`
  - 新增 §10.2.1 `knowledge edit` 字段覆写规则表（含 `date` 字段保持原值的显式说明）
- Auto-mode policy basis: `AGENTS.md` 未限制 standard cycle 内 design 子节点 auto resolve；本 cycle 由父会话路由为 `auto`，approval step 在 record 落盘后即可解锁下游

## Decision

**Approved**. Design status updated to `已批准（auto-mode approval）`. 下一步 = `hf-tasks`，输入为本 design 的 §13.2 / §14 task readiness 段。

## Hash & 锚点

- Design 初稿提交: `208c612` "design(F005): draft Knowledge Authoring CLI design (D005)"
- 修订提交（与 approval 同 commit）: 见本 approval 一并提交的 "design(F005): r1 follow-up — CON-501 wording, ADR-503 cli: prefix, §10.2 update() signature, §10.2.1 edit field overlay table"
