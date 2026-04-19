# Approval Record - F005 Spec

- Artifact: `docs/features/F005-garage-knowledge-authoring-cli.md`
- Approval Type: `specApproval`
- Approver: cursor cloud agent (auto-mode policy approver)
- Date: 2026-04-19
- Workflow Profile / Execution Mode: `standard` / `auto`
- Workspace Isolation: `in-place`

## Evidence

- Round 1 review: `docs/reviews/spec-review-F005-knowledge-authoring-cli.md` — `需修改`
  - 0 critical / 2 important / 3 minor (all LLM-FIXABLE)
  - 全部 5 项均不涉及业务事实变化（USER-INPUT=0），可在同一回合内消化
- Round 1 follow-up commit: `fix(F005): spec r1 follow-up — FR-501/508 ID alignment, FR-507 split, FR-507b index path, NFR-502 dependency-surface, ASM-504 confirmation`
- Round 2 review: `docs/reviews/spec-review-F005-knowledge-authoring-cli-r2.md` — `通过`
  - 0 critical / 0 important / 0 minor
  - delta-only 二轮扫描，未发现新冲突
  - `needs_human_confirmation=true` 但 reviewer 已说明 `auto` mode 下父会话可写 approval record；不存在 USER-INPUT 类阻塞
  - `reroute_via_router=false`
- Auto-mode policy basis: `AGENTS.md` 未限制 standard cycle 内 spec 子节点 auto resolve；本 cycle 由父会话路由为 `auto`，approval step 在 record 落盘后即可解锁下游

## Decision

**Approved**. Spec 状态由 `草稿` → `已批准（auto-mode approval）`。下一步 = `hf-design`，输入为本 spec + F004 v1.1 publisher / KnowledgeStore.update() 不变量 + F003 candidate→publisher 互不污染契约。

## Hash & 锚点

- Spec 初稿提交: `5d1febb` "feat(F005): draft Knowledge Authoring CLI spec (knowledge/experience CRUD)"
- 修订提交: `2137f67` "fix(F005): spec r1 follow-up — FR-501/508 ID alignment, FR-507 split, FR-507b index path, NFR-502 dependency-surface, ASM-504 confirmation"
