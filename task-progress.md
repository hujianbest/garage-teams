# Task Progress

## Goal

- Goal: F008 — Garage Coding Pack 与 Writing Pack（把 `.agents/skills/` 物化为可分发 packs）
- Owner: hujianbest
- Status: 🟡 In Progress — F008 design 草稿已落，等待 `hf-design-review`
- Last Updated: 2026-04-22

## Previous Milestones

- F001 Phase 1: ✅ 完成（T1-T22，416 测试通过）
- F002 Garage Live: ✅ 完成（CLI + 真实 Claude Code 集成，436 测试通过）
- F003 Garage Memory: ✅ 完成（T1-T9，384 测试通过）
- F004 Garage Memory v1.1: ✅ 完成（T1-T5，414 测试通过）
- F005 Garage Knowledge Authoring CLI: ✅ 完成（T1-T6，451 测试通过）
- F006 Garage Recall & Knowledge Graph: ✅ 完成（T1-T5，496 测试通过；workflow closeout 见 `docs/verification/F006-finalize-closeout-pack.md`）
- F007 Garage Packs 与宿主安装器: ✅ 完成（T1-T5，586 测试通过；workflow closeout 见 `docs/verification/F007-finalize-closeout-pack.md`）

## Current Workflow State

- Current Stage: `hf-design`
- Workflow Profile: `full`
- Execution Mode: `auto`
- Workspace Isolation: `in-place`（工作分支 `cursor/f008-coding-pack-and-writing-pack-bf33`；PR #22）
- Current Active Task: 无（design 草稿已完成，等待 review）
- Pending Reviews And Gates: `hf-design-review`（待派发）
- Next Action Or Recommended Skill: `hf-design-review`
- Relevant Files:
  - `docs/features/F008-garage-coding-pack-and-writing-pack.md`（已批准）
  - `docs/approvals/F008-spec-approval.md`（auto-mode approval record）
  - `docs/reviews/spec-review-F008-coding-pack-and-writing-pack.md`（r1 需修改 + r2 通过）
  - `docs/designs/2026-04-22-garage-coding-pack-and-writing-pack-design.md`（草稿 r1，含 8 项 ADR）
  - `docs/soul/manifesto.md`、`growth-strategy.md`、`design-principles.md`（愿景锚点）
  - `packs/README.md`、`packs/garage/`（F007 落下的现状）
  - `.agents/skills/harness-flow/`、`.agents/skills/write-blog/`、`.agents/skills/find-skills/`、`.agents/skills/writing-skills/`（搬迁源）
  - `docs/principles/skill-anatomy.md` + `.agents/skills/harness-flow/docs/principles/skill-anatomy.md`（双副本 drift 待 design 收敛）
- Constraints:
  - 不修改 F007 安装管道（`src/garage_os/adapter/installer/`）/ `pack.json` schema / host adapter 注册表
  - 搬迁是字节级 1:1（仅相对引用路径允许最小修复）
  - `.agents/skills/` 处置必须本 cycle 收敛（A/B/C 候选由 design ADR 决定）
  - `docs/principles/skill-anatomy.md` 双副本 drift 必须本 cycle 收敛（三策略由 design ADR 决定）
  - design 草稿必须能通过 § 4.2 "Design Reviewer 可拒红线" 6 条检查
  - Stage 2 仍保持 workspace-first，不引入外部数据库 / 常驻服务 / Web UI

## Next Step

派发独立 reviewer subagent 执行 `hf-design-review`，对 `docs/designs/2026-04-22-garage-coding-pack-and-writing-pack-design.md` 出 verdict。

design 草稿已收敛 8 项 ADR（D8-1 ~ D8-8）+ 显式承认 §2.4 "F007 管道只复制 SKILL.md 单文件" 工程边界（ADR-D8-4 文档级提示策略）+ 给出 5 类提交分组（T1-T5）。每项 ADR 都可逐条对应 spec § 4.2 6 条 "Design Reviewer 可拒红线" 的判定。

下一节点候选（由 design-review 结果决定）：
- 通过 → 写 `docs/approvals/F008-design-approval.md` → `hf-tasks` 拆分 5 个 task
- 需修改 → 回 `hf-design` 按 review findings 修订
- 阻塞 → 回 `hf-workflow-router` 重新判定
