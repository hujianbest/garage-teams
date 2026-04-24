# Task Progress

## Goal

- Goal: Vision-gap analysis + F010+ next-cycle planning (planning artifact, 不是 spec; 真正 spec 由 hf-specify 起草)
- Owner: hujianbest
- Status: 🟡 Planning artifact 已落, 待用户确认 P0/P1/P2 排序后启 F010 spec
- Last Updated: 2026-04-24

## Previous Milestones

- F001 Phase 1: ✅ 完成（T1-T22，416 测试通过）
- F002 Garage Live: ✅ 完成（CLI + 真实 Claude Code 集成，436 测试通过）
- F003 Garage Memory: ✅ 完成（T1-T9，384 测试通过）
- F004 Garage Memory v1.1: ✅ 完成（T1-T5，414 测试通过）
- F005 Garage Knowledge Authoring CLI: ✅ 完成（T1-T6，451 测试通过）
- F006 Garage Recall & Knowledge Graph: ✅ 完成（T1-T5，496 测试通过；workflow closeout 见 `docs/verification/F006-finalize-closeout-pack.md`）
- F007 Garage Packs 与宿主安装器: ✅ 完成（T1-T5，586 测试通过；workflow closeout 见 `docs/verification/F007-finalize-closeout-pack.md`）
- F008 Garage Coding Pack 与 Writing Pack: ✅ 完成（T1a/T1b/T1c + T2 + T3 + T4a/T4b/T4c + T5，633 测试通过；workflow closeout 见 `docs/verification/F008-finalize-closeout-pack.md`）
- F009 garage init 双 Scope 安装: ✅ 完成（T1-T6 + manual smoke + post-code-review，713 测试通过；finalize approval 见 `docs/approvals/F009-finalize-approval.md`）
- packs/search hotfix (PR#28 candidate): ✅ 落地（补 pack metadata + INV-1 30→31 + dogfood baseline 59→63，715 测试通过）

## Current Workflow State

- Current Stage: `planning` (vision-gap analysis written; awaiting user P0/P1/P2 confirmation)
- Workflow Profile: `N/A` (planning artifact, not a workflow cycle)
- Execution Mode: `auto`
- Workspace Isolation: `in-place`（工作分支 `cursor/vision-gap-analysis-bf33`）
- Current Active Task: 无 (planning 文档已落)
- Pending Reviews And Gates: 用户确认 F010 范围 (单独 F010-A 还是 F010-A+B 一起) → 启 `hf-specify`
- Next Action Or Recommended Skill: 用户确认后, 派发 `hf-specify` 起草 F010 spec (基于 `docs/planning/2026-04-24-vision-gap-and-next-cycle-plan.md` § 2.1)
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

完成 vision-gap 分析, 推荐**单一最优下一步**:

### F010-A — 自动 context handoff pipeline (`garage sync` + 三家 host context surface)

**为什么 P0 中的 P0**:
- 同时复活 manifesto promise ① + ③, 让 B4 飞轮真正能转
- F003-F006 已 build 的整个 memory 子系统在用户日常 Cursor / Claude Code 对话里 invisible — 必须有 `garage sync` 把 top-N knowledge + recent experience 编译到宿主原生 context surface (CLAUDE.md / .cursor/rules/ / OpenCode 等价路径) 才能让用户感知到
- 复用既有 F007 host adapter pattern, 没有架构性重构成本

**推荐组合 (如果做 2-3 cycle)**:
1. **F010-A** — context inject (用户感知)
2. **F010-B** — `garage session import --from <host-history>` (闭合飞轮 input 端)
3. **F011-B** — `packs/garage/agents/code-review-agent.md` + `blog-writing-agent.md` (Stage 3 启动证据)

详细 vision-gap 分析 + 候选清单 + 排序理由见 `docs/planning/2026-04-24-vision-gap-and-next-cycle-plan.md`.

### F009 carry-forward (与 F010 候选并行)

- I-1 (CON-902 phase 1+3 body 守门, F010-A 不必修, 等 garage uninstall 同 cycle)
- I-2 (VersionManager host-installer migration 链注册, 同上)

## 完成证据 (F009 final + search hotfix, 2026-04-24)

- 测试基线: 633 (F008 baseline) → 713 (F009 closed) → **715 passed** (search hotfix landed, 0 regressions)
- F009 cycle: 8 commits (T1-T6 + manual smoke + post-code-review), 12 个新增测试文件
- search hotfix: 1 commit (补 pack metadata + INV-1 30→31 + dogfood baseline 59→63)
- 完整 review/gate 链路: F009 spec/design/tasks 三方 approved + test/code/traceability review + regression/completion gate + finalize approval
- Vision-gap planning artifact: `docs/planning/2026-04-24-vision-gap-and-next-cycle-plan.md`
