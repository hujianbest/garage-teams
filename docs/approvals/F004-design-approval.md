# Approval Record - F004 Design

- Artifact: `docs/designs/2026-04-19-garage-memory-v1-1-design.md`
- Approval Type: `designApproval`
- Approver: cursor cloud agent (auto-mode policy approver)
- Date: 2026-04-19
- Workflow Profile / Execution Mode: `full` / `auto`
- Workspace Isolation: `in-place`
- Design Stage Composition: 仅 `hf-design`（F004 spec 不含 UI surface，`hf-ui-design` 未激活）

## Evidence

- Round 1 review: `docs/reviews/design-review-F004-memory-v1-1.md` (conclusion: `需修改`)
  - 0 critical / 1 important (LLM-FIXABLE) / 3 minor (LLM-FIXABLE)
  - rubric scores: D1=9, D2=9, D3=8, D4=9, D5=6.5（important 卡线）, D6=7.5
  - `needs_human_confirmation=false`、`reroute_via_router=false`
  - reviewer 明确接受 author self-check 闭合 finding 后直接进入 `设计真人确认`，无需复审

## Round 1 → R1 finding 闭合矩阵（author self-check）

| Finding | 闭合位置 | 验证方式 |
|---------|---------|---------|
| `[important][LLM-FIXABLE][D5]` supersede 链 carry-over 仅留 §18 backlog 未升格 | §10.1 数据流加 `_merge_unique` + carry-over 伪代码；§11.2.1 新增 `PRESERVED_FRONT_MATTER_KEYS` contract（含 `supersedes` / `related_decisions`）；§13.2 加 2 条测试名（`test_repeated_publish_preserves_supersedes_chain_from_v1` + `test_repeated_publish_preserves_related_decisions_from_v1`）；§3 追溯矩阵 FR-401 行更新；§15 T2 描述纳入 carry-over 责任；§18#1 升格说明 | grep "PRESERVED_FRONT_MATTER_KEYS" 应在 §10.1 + §11.2.1 + §15 + §18 命中；T2 描述显式提到 "supersede 链 carry-over" |
| `[minor][LLM-FIXABLE][D6]` self-conflict false-positive 假设隐藏 | §10.1.1 新增 publisher 短路段；§11.2 self-conflict 短路约束；§13.2 加 1 条测试名（`test_repeated_accept_short_circuits_self_conflict`）；§14 失败模式表加 1 行；§18#4 升格说明 | grep "self-conflict" / "短路" 应在 §10.1.1 + §11.2 + §14 + §18 命中 |
| `[minor][LLM-FIXABLE][D5]` 命名漂移 `derive_id` / `pub_id_generator.derive` | §3 追溯矩阵 NFR-401 行 + §6 A1 行 + §7.2 ADR-401 + §8.2 sequence diagram + §10.1 伪代码 全部统一为 `derive_knowledge_id(candidate_id, knowledge_type)` / `derive_experience_id(candidate_id)`；与 §11.1 contract 一致 | grep "derive_id" / "pub_id_generator" / "exp_id_generator" 不应在 §6/§7/§8/§10 出现（仅在 §11.1 contract 与 §16 ADR 中出现 `derive_*` 抽象写法） |
| `[minor][LLM-FIXABLE][D3]` §6 A1 行 trade-off SOC 论据缺失 | §6 A1 行"主要代价"列末尾追加："vs A2：保护 F001 KnowledgeStore 公开契约稳定性 + publisher 层职责单一（'管发布身份' vs KnowledgeStore '管知识存储'），SOC 清晰" | grep "SOC" 在 §6 表内命中 |

4/4 finding 全部 1:1 闭合，无悬空。

## Auto-mode policy basis

- `AGENTS.md` 默认 mode 未禁止 design 子节点 auto resolve；本 cycle 由 `hf-workflow-router` 路由为 `auto`
- reviewer 在 review record §8 明确支持 author self-check 直接进入 approval（不强制复派 reviewer），符合 `auto` mode policy
- design 修订仅按 finding 列表定向回修，未引入新决策、未改变范围、未触动已批准 spec；无需回流 `hf-spec-review`

## Decision

**Approved**. Design status updated to `已批准（auto-mode approval r1）`。下一步 = `hf-tasks`，输入为本 design + F004 spec + design-review r1 record + spec-review record。

## Hash & 锚点

- Design 草稿落盘 commit: 见 `cursor/f004-memory-polish-1bde` 分支 PR #15 中 "design(F004): draft Garage Memory v1.1 design ..." 提交
- Design r1 修订 + approval commit: 同分支后续提交 "design(F004): r1 — close design-review findings ..."
