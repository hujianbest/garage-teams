# Task Progress

## Goal

- Goal: F009 — `garage init` 双 Scope 安装（project / user）+ 交互式 Scope 选择
- Owner: hujianbest
- Status: 🟡 In Progress — F009 spec 草稿已落，等待 `hf-spec-review`
- Last Updated: 2026-04-23

## Previous Milestones

- F001 Phase 1: ✅ 完成（T1-T22，416 测试通过）
- F002 Garage Live: ✅ 完成（CLI + 真实 Claude Code 集成，436 测试通过）
- F003 Garage Memory: ✅ 完成（T1-T9，384 测试通过）
- F004 Garage Memory v1.1: ✅ 完成（T1-T5，414 测试通过）
- F005 Garage Knowledge Authoring CLI: ✅ 完成（T1-T6，451 测试通过）
- F006 Garage Recall & Knowledge Graph: ✅ 完成（T1-T5，496 测试通过；workflow closeout 见 `docs/verification/F006-finalize-closeout-pack.md`）
- F007 Garage Packs 与宿主安装器: ✅ 完成（T1-T5，586 测试通过；workflow closeout 见 `docs/verification/F007-finalize-closeout-pack.md`）
- F008 Garage Coding Pack 与 Writing Pack: ✅ 完成（T1a/T1b/T1c + T2 + T3 + T4a/T4b/T4c + T5，633 测试通过；workflow closeout 见 `docs/verification/F008-finalize-closeout-pack.md`）

## Current Workflow State

- Current Stage: `hf-specify`
- Workflow Profile: `full`
- Execution Mode: `auto`
- Workspace Isolation: `in-place`（工作分支 `cursor/f009-init-scope-selection-bf33`）
- Current Active Task: 无（spec drafting 阶段）
- Pending Reviews And Gates: `hf-spec-review`（待派发）
- Next Action Or Recommended Skill: `hf-spec-review`
- Relevant Files:
  - `docs/features/F009-garage-init-scope-selection.md`（草稿 r1，10 FR + 4 NFR + 4 CON + 4 ASM）
  - `docs/soul/manifesto.md`、`user-pact.md`、`design-principles.md`、`growth-strategy.md`（价值锚点；本 cycle 与 workspace-first 信念有 trade-off，需显式评估）
  - F008 spec § 5 deferred backlog 第 3 行（"全局安装到 `~/.claude/skills/...`：solo creator 跨多客户仓库的需求"——本 cycle 即落地）
  - F007 安装管道 `src/garage_os/adapter/installer/{pack_discovery,pipeline,manifest,host_registry}.py` + 三家 adapter `hosts/{claude,opencode,cursor}.py`（F009 扩展点）
  - 调研锚点 3 家宿主官方 user scope path 文档（spec § 1）
- Constraints:
  - F002/F007/F008 既有 `garage init` 行为字节级不变（CON-901 + 沿用 CON-702）
  - D7 安装管道核心算法不动（CON-902，仅 phase 2 增 scope 分流）
  - 复用 F007 pack.json schema + F008 ADR-D8-9 EXEMPTION_LIST（CON-903）
  - manifest schema 1 → 2 migration 单向（CON-904）
  - 不改 packs/ 内容物
  - 不引入 enterprise / plugin scope（solo creator 用不到）

## Next Step

派发独立 reviewer subagent 执行 `hf-spec-review`，对 `docs/features/F009-garage-init-scope-selection.md` 出 verdict。

下一节点候选（由 spec-review 结果决定）：
- 通过 → `hf-design`（需含 user/project scope trade-off ADR + manifest schema 2 ADR + adapter Protocol 扩展 ADR + 交互式 UX ADR）
- 需修改 → 回 `hf-specify` 按 review findings 修订
- 阻塞 → 回 `hf-workflow-router` 重新判定 scope
