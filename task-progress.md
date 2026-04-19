# Task Progress

## Goal

- Goal: F007 — Garage Packs 与宿主安装器（spec 已批准；待进入 hf-design）
- Owner: hujianbest
- Status: ▶ Active — 规格已批准，等待 design 阶段启动
- Last Updated: 2026-04-19

## Previous Milestones

- F001 Phase 1: ✅ 完成（T1-T22，416 测试通过）
- F002 Garage Live: ✅ 完成（CLI + 真实 Claude Code 集成，436 测试通过）
- F003 Garage Memory: ✅ 完成（T1-T9，384 测试通过）
- F004 Garage Memory v1.1: ✅ 完成（T1-T5，414 测试通过）
- F005 Garage Knowledge Authoring CLI: ✅ 完成（T1-T6，451 测试通过）
- F006 Garage Recall & Knowledge Graph: ✅ 完成（T1-T5，496 测试通过；workflow closeout 见 `docs/verification/F006-finalize-closeout-pack.md`）

## Current Workflow State

- Current Stage: `hf-design`（规格已批准，等待 design 阶段启动）
- Workflow Profile: `coding`
- Execution Mode: `auto-mode`
- Workspace Isolation: `in-place`
- Current Active Task: F007 design（待启动）
- Pending Reviews And Gates: F007 design review（design 草稿完成后派发）
- Next Action Or Recommended Skill: `hf-design`
- Relevant Files:
  - `docs/features/F007-garage-packs-and-host-installer.md`（已批准规格，r2 head）
  - `docs/approvals/F007-spec-approval.md`（auto-mode approval record）
  - `docs/reviews/spec-review-F007-garage-packs-and-host-installer.md`（r1 + r2 review record）
  - `docs/principles/skill-anatomy.md`（pack 内 skill anatomy 对齐基线）
  - `docs/soul/manifesto.md`、`design-principles.md`（宿主无关原则约束）
  - 调研参考: OpenSpec `docs/supported-tools.md`（host id + skills/commands path pattern 模型）
  - F006 closeout 链路：`docs/verification/F006-finalize-closeout-pack.md`、`RELEASE_NOTES.md` 首条目
- Constraints:
  - Stage 2 仍保持 workspace-first，不引入外部数据库、常驻服务、Web UI
  - 优先使用 markdown、JSON、文件系统存储
  - 所有数据存储在 Garage 仓库内部

## Next Step

1. 启动 `hf-design`，输入 = 已批准的 F007 spec + F001 `HostAdapterProtocol` 不变契约 + F002 `garage init` 向后兼容承诺（CON-702）+ F005 stdout marker 风格基线。
2. design 草稿完成后派发独立 reviewer subagent 执行 `hf-design-review`。
3. design 阶段需消化 § 11 非阻塞性开放问题：Cursor surface 选型（`.cursor/skills/` vs `.cursor/rules/`）、安装标记块形式（HTML 注释 vs front matter）、交互 prompt 形式（stdlib `input()` 实现选型）、pack-id 收敛（单一 `garage` vs `coding/product-insights` 多 pack）。

延后项（与 F007 解耦的后续候选）：

- F008 候选：把 `.agents/skills/` 下 30 个 HF skills 实际搬迁到 `packs/coding/skills/`（F007 § 5 deferred）
- F008 候选：`garage uninstall` / `garage update --hosts <list>`
- 单独候选：全局安装到 `~/.claude/skills/...`（OpenSpec issue #752 模式）
- F006 finalize 中显式延后的 minor：`_recommend_experience` 多次累加语义对齐；CON-501/502/NFR-602 契约测试
- F006 § 5 deferred backlog：`garage knowledge unlink` / 多跳 graph / experience link / 跨类型 link / 图导出 / `recommend --format json`
- pre-existing baseline 的 2 个 mypy errors + 47 个 ruff stylistic warnings 清理
