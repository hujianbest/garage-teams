# Task Progress

## Goal

- Goal: F008 — Garage Coding Pack 与 Writing Pack（把 `.agents/skills/` 物化为可分发 packs）
- Owner: hujianbest
- Status: 🟡 In Progress — F008 task plan **已批准**（r4 通过 + auto-mode approval），进入 `hf-test-driven-dev` 实施 T1a 起步
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

- Current Stage: `hf-test-driven-dev`
- Workflow Profile: `full`
- Execution Mode: `auto`
- Workspace Isolation: `in-place`（工作分支 `cursor/f008-coding-pack-and-writing-pack-bf33`；PR #22）
- Current Active Task: **T1a — packs/coding/ 22 skill cp -r 字节级搬迁**（task plan § 5 T1a，Selection Priority=1）
- Pending Reviews And Gates: 无（实施阶段；review/gate 在所有 9 task 完成后）
- Next Action Or Recommended Skill: `hf-test-driven-dev`（实施 T1a）
- Relevant Files:
  - `docs/features/F008-garage-coding-pack-and-writing-pack.md`（已批准 r2 + design/tasks 阶段反向同步收紧 wording）
  - `docs/approvals/F008-{spec,design,tasks}-approval.md`（三份 auto-mode approval records）
  - `docs/reviews/spec-review-F008-coding-pack-and-writing-pack.md`（r1 需修改 + r2 通过）
  - `docs/reviews/design-review-F008-coding-pack-and-writing-pack.md`（r1 需修改 + r2 通过）
  - `docs/reviews/tasks-review-F008-coding-pack-and-writing-pack.md`（r1 需修改 + r2 需修改 + r3 需修改 + r4 通过）
  - `docs/designs/2026-04-22-garage-coding-pack-and-writing-pack-design.md`（已批准，含 9 项 ADR + 9 sub-commit + 9 INV + 5 测试文件）
  - `docs/tasks/2026-04-22-garage-coding-pack-and-writing-pack-tasks.md`（已批准，9 个 task：T1a/T1b/T1c + T2 + T3 + T4a/T4b/T4c + T5）
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

进入 `hf-test-driven-dev` 实施 **T1a — packs/coding/ 22 skill cp -r 字节级搬迁**。

T1a 详情（task plan § 5）：
- 把 `.agents/skills/harness-flow/skills/{hf-*,using-hf-workflow}/` 共 22 skill 子目录 cp -r 到 `packs/coding/skills/<id>/`
- Acceptance: `ls packs/coding/skills/ | wc -l == 22` + 抽样 SHA-256 字节级相等 + INV-9 grep = 0
- Files: `packs/coding/skills/<id>/` × 22（新增）
- Verify: `ls packs/coding/skills/ | wc -l == 22` + `find packs/coding/skills/hf-specify -type f -exec sha256sum {} \;` 抽样比对 + `grep -rE '\.claude/|\.cursor/|\.opencode/|claude-code' packs/coding/skills/ | wc -l == 0`
- 完成条件: 22 skill 物理存在 + INV-9 通过 + commit 落地

T1a 完成后 router 重选 → T1b → T1c → T2 → T3 → T4a → T4b → T4c → T5（按 § 8 P 升序串行）。9 个 task 全部完成后做 manual smoke walkthrough → `hf-test-review` → `hf-code-review` → `hf-traceability-review` → `hf-regression-gate` → `hf-completion-gate` → `hf-finalize`。
