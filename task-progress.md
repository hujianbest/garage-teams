# Task Progress

## Goal

- Goal: F009 — `garage init` 双 Scope 安装（project / user）+ 交互式 Scope 选择
- Owner: hujianbest
- Status: ✅ 完成 (closed by hf-finalize 2026-04-23)
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

- Current Stage: `closed`
- Workflow Profile: `N/A` (无活跃 cycle, F009 已完成)
- Execution Mode: `N/A`
- Workspace Isolation: `in-place`（工作分支 `cursor/f009-init-scope-selection-bf33`；PR #24）
- Current Active Task: 无 (cycle 完成)
- Pending Reviews And Gates: 无
- Next Action Or Recommended Skill: `null` (cycle 已 closed)
- Relevant Files:
  - `docs/features/F009-garage-init-scope-selection.md`（已批准 r2，10 FR + 4 NFR + 4 CON + 4 ASM）
  - `docs/designs/2026-04-23-garage-init-scope-selection-design.md`（已批准 r2，11 ADR + 6 task + 9 INV + 11 测试文件）
  - `docs/approvals/F009-{spec,design}-approval.md`（auto-mode approval records）
  - `docs/reviews/{spec,design}-review-F009-garage-init-scope-selection.md`（r1 需修改 + r2 通过）
  - `docs/tasks/2026-04-23-garage-init-scope-selection-tasks.md`（已批准 r3，6 个 task：T1 adapter / T2 pipeline / T3 manifest / T4 cli / T5 tests / T6 docs）
  - `docs/approvals/F009-tasks-approval.md`（auto-mode approval record）
  - `docs/reviews/tasks-review-F009-garage-init-scope-selection.md`（r1 → r2 → r3 通过）
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

无. F009 cycle 已 closed.

下一 cycle 候选 (F010+):
- `garage uninstall --scope <scope>` (与 F009 正交)
- `garage update --scope <scope>` (与 F009 正交)
- D7 安装管道扩展为递归 `references/` / `evals/` / `scripts/` 子目录 (F008 deferred)
- F009 carry-forward I-1/I-2 (CON-902 body 守门 + VersionManager 注册链, 与 garage uninstall/update --scope 同 cycle 修复)

## 完成证据 (F009 final, 2026-04-23 closed)

- 测试基线: 633 (F008 baseline) → **713 passed** (+80 增量, 0 退绿)
- 8 cycle commits: T1 adapter / T2 pipeline / T3 manifest / T4 cli / T5 tests / T6 docs + manual smoke + post-code-review
- 12 个新增测试文件（含 baseline JSON fixture + post-code-review 修复测试）+ 4 处 carry-forward wording 修复
- INV-F9-1..9 全部通过（design § 11.1）
- 完整 review/gate 链路: spec/design/tasks 三方 approved + test/code/traceability review + regression/completion gate + finalize approval
- Manual smoke walkthrough 4 tracks 全绿 (dogfood + project + user + mixed)
- 详见 `docs/approvals/F009-finalize-approval.md`
