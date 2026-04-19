# Task Progress

## Goal

- Goal: F007 — Garage Packs 与宿主安装器（spec 草稿待评审）
- Owner: hujianbest
- Status: ▶ Active — 规格起草中
- Last Updated: 2026-04-19

## Previous Milestones

- F001 Phase 1: ✅ 完成（T1-T22，416 测试通过）
- F002 Garage Live: ✅ 完成（CLI + 真实 Claude Code 集成，436 测试通过）
- F003 Garage Memory: ✅ 完成（T1-T9，384 测试通过）
- F004 Garage Memory v1.1: ✅ 完成（T1-T5，414 测试通过）
- F005 Garage Knowledge Authoring CLI: ✅ 完成（T1-T6，451 测试通过）
- F006 Garage Recall & Knowledge Graph: ✅ 完成（T1-T5，496 测试通过；workflow closeout 见 `docs/verification/F006-finalize-closeout-pack.md`）

## Current Workflow State

- Current Stage: `hf-specify`
- Workflow Profile: `coding`
- Execution Mode: `auto-mode`（用户在新 cycle 触发：先调研后起草）
- Workspace Isolation: `in-place`
- Current Active Task: F007 spec 起草
- Pending Reviews And Gates: F007 spec review（待派发 reviewer subagent）
- Next Action Or Recommended Skill: `hf-spec-review`
- Relevant Files:
  - `docs/features/F007-garage-packs-and-host-installer.md`（本 cycle 规格草稿）
  - `docs/principles/skill-anatomy.md`（pack 内 skill anatomy 对齐基线）
  - `docs/soul/manifesto.md`、`design-principles.md`（宿主无关原则约束）
  - 调研参考: OpenSpec `docs/supported-tools.md`（host id + skills/commands path pattern 模型）
  - F006 closeout 链路：`docs/verification/F006-finalize-closeout-pack.md`、`RELEASE_NOTES.md` 首条目
- Constraints:
  - Stage 2 仍保持 workspace-first，不引入外部数据库、常驻服务、Web UI
  - 优先使用 markdown、JSON、文件系统存储
  - 所有数据存储在 Garage 仓库内部

## Next Step

1. 派发独立 reviewer subagent 执行 `hf-spec-review`，评审 `docs/features/F007-garage-packs-and-host-installer.md`。
2. 按 reviewer 结论：通过 → 进入 approval & `hf-design`；需修改 → 回到 `hf-specify` 修订。
3. 本 cycle 实施前先解决 § 11 非阻塞开放问题（Cursor surface 选型、安装标记块形式、交互 prompt 实现、pack-id 收敛）。

延后项（与 F007 解耦的后续候选）：

- F008 候选：把 `.agents/skills/` 下 30 个 HF skills 实际搬迁到 `packs/coding/skills/`（F007 § 5 deferred）
- F008 候选：`garage uninstall` / `garage update --hosts <list>`
- 单独候选：全局安装到 `~/.claude/skills/...`（OpenSpec issue #752 模式）
- F006 finalize 中显式延后的 minor：`_recommend_experience` 多次累加语义对齐；CON-501/502/NFR-602 契约测试
- F006 § 5 deferred backlog：`garage knowledge unlink` / 多跳 graph / experience link / 跨类型 link / 图导出 / `recommend --format json`
- pre-existing baseline 的 2 个 mypy errors + 47 个 ruff stylistic warnings 清理
