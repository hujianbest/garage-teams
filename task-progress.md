# Task Progress

## Goal

- Goal: F009 — `garage init` 双 Scope 安装（project / user）+ 交互式 Scope 选择
- Owner: hujianbest
- Status: 🟡 In Progress — F009 spec **已批准**（r2 通过 + auto-mode approval），进入 `hf-design`
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

- Current Stage: `hf-design`
- Workflow Profile: `full`
- Execution Mode: `auto`
- Workspace Isolation: `in-place`（工作分支 `cursor/f009-init-scope-selection-bf33`；PR #24）
- Current Active Task: 无（design 草稿已完成，等待 review）
- Pending Reviews And Gates: `hf-design-review`（待派发）
- Next Action Or Recommended Skill: `hf-design-review`
- Relevant Files:
  - `docs/features/F009-garage-init-scope-selection.md`（已批准 r2，10 FR + 4 NFR + 4 CON + 4 ASM）
  - `docs/approvals/F009-spec-approval.md`（auto-mode approval record）
  - `docs/reviews/spec-review-F009-garage-init-scope-selection.md`（r1 需修改 + r2 通过）
  - `docs/designs/2026-04-23-garage-init-scope-selection-design.md`（草稿 r1，9 ADR + 6 task + 9 INV + 10 测试文件）
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

进入 `hf-design`，产出 F009 设计文档，覆盖 9 项 ADR：

1. manifest schema 2 字段命名（`"project"`/`"user"` vs `"workspace"`/`"global"`）
2. `Path.home()` 抛 RuntimeError 的退出码
3. stdout 多 scope 段格式
4. manifest absolute path 是否带 `~/` 前缀
5. 交互式 UX 三选一（A 两轮 / B 一轮带后缀 / C 两轮+all P/all u/per-host）
6. HostInstallAdapter Protocol 新增 method 命名（`target_skill_path_user` vs `target_skill_path(scope=...)`）
7. `garage status` 输出格式
8. ManifestMigrationError 类型与退出码常量（spec r1 important #2 升级出）
9. host_id 命名约束（不允许字面 `:` 字符；spec r1 minor #2 升级出）

每项 ADR 必须能通过 spec § 11 + NFR-901 字节级 + CON-902 phase 5 enum + CON-904 跨用户立场等多重约束的检查。design 完成后派发独立 reviewer subagent 执行 `hf-design-review`。
