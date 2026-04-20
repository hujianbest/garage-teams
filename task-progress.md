# Task Progress

## Goal

- Goal: F007 — Garage Packs 与宿主安装器（已 closeout）
- Owner: hujianbest
- Status: ✅ Closed — F007 cycle 完整 closeout（T1-T5 + 全部 review/gate + finalize）
- Last Updated: 2026-04-19

## Previous Milestones

- F001 Phase 1: ✅ 完成（T1-T22，416 测试通过）
- F002 Garage Live: ✅ 完成（CLI + 真实 Claude Code 集成，436 测试通过）
- F003 Garage Memory: ✅ 完成（T1-T9，384 测试通过）
- F004 Garage Memory v1.1: ✅ 完成（T1-T5，414 测试通过）
- F005 Garage Knowledge Authoring CLI: ✅ 完成（T1-T6，451 测试通过）
- F006 Garage Recall & Knowledge Graph: ✅ 完成（T1-T5，496 测试通过；workflow closeout 见 `docs/verification/F006-finalize-closeout-pack.md`）
- F007 Garage Packs 与宿主安装器: ✅ 完成（T1-T5，586 测试通过；workflow closeout 见 `docs/verification/F007-finalize-closeout-pack.md`）

## Current Workflow State

- Current Stage: `closed`
- Workflow Profile: `N/A`（无活跃 cycle）
- Execution Mode: `N/A`
- Workspace Isolation: `in-place`
- Current Active Task: 无
- Pending Reviews And Gates: 无
- Next Action Or Recommended Skill: `null`
- Relevant Files:
  - `docs/verification/F007-finalize-closeout-pack.md`（F007 workflow closeout pack）
  - `docs/verification/F007-completion-gate.md`、`docs/verification/F007-regression-gate.md`
  - `docs/features/F007-garage-packs-and-host-installer.md`（已批准规格）
  - `docs/designs/2026-04-19-garage-packs-and-host-installer-design.md`（已批准设计 r2）
  - `docs/tasks/2026-04-19-garage-packs-and-host-installer-tasks.md`（已批准任务计划）
  - `docs/approvals/F007-{spec,design,tasks}-approval.md`
  - `docs/reviews/{spec,design,tasks,test,code,traceability}-review-F007-*.md`（完整 review 链路）
  - `RELEASE_NOTES.md`（按 cycle 倒序记录用户可见变化；首条目 = F007）
  - `AGENTS.md`（新增 ## Packs & Host Installer 段 + adapter 模块表已更新）
  - `docs/soul/manifesto.md`、`user-pact.md`、`design-principles.md`、`growth-strategy.md`（项目灵魂，跨 cycle 仍生效）
- Constraints:
  - Stage 2 仍保持 workspace-first，不引入外部数据库、常驻服务、Web UI
  - 优先使用 markdown、JSON、文件系统存储
  - 所有数据存储在 Garage 仓库内部

## Next Step

无活跃下一步。下一个 cycle 启动时由 `hf-workflow-router` 重新建立 stage / profile / mode / active task。

可选的后续候选（由 `hf-workflow-router` 在新 cycle 中独立判断与拆分）：

- **F008 候选 — 把 `.agents/skills/` 30 个 HF skills 搬迁到 `packs/coding/skills/`**：F007 cycle 已在 packs/garage 验证管道与 conflict 检测都到位，搬迁本身是机械动作 + 路径替换；spec FR-701 验收 #1 / NFR-701 grep 测试已为 `packs/coding/` 自动覆盖
- **F008 候选 — `garage uninstall --hosts <list>` + `garage update --hosts <list>`**：F007 cycle 显式 deferred 的安装逆向操作 + 拉新流程；安装清单 manifest 已为这两条留好 entry point
- **单独候选 — 全局安装到 `~/.claude/skills/...`**（OpenSpec issue #752 模式）：solo creator 跨多客户仓库的需求；与 Garage workspace-first 信念有 trade-off，应单独 spec 化
- **F008+ 候选 — 新增宿主**（Codex / Gemini CLI / Windsurf / Copilot 等）：F007 已确立 first-class adapter 注册模式；新增宿主成本 = 1 个 adapter 子模块 + 注册表 1 行
- 处理 F006 finalize 中显式延后的 minor：`_recommend_experience` 多次累加语义对齐；CON-501/502/NFR-602 契约测试
- 处理 F006 § 5 deferred backlog：`garage knowledge unlink` / 多跳 graph / experience link / 跨类型 link / 图导出 / `recommend --format json`
- 处理 pre-existing baseline 的 1 个 mypy error（`_memory_review` line 562 on main）+ 47 个 ruff stylistic warnings（F002/F003/F004 历史；F007 已确认未新增）
- 评估是否启动 Stage 3（"工匠"）：进入信号 "知识库条目 >100" 与 "识别到 5+ 可复用模式" 仍依赖用户使用频率
- 详见 `RELEASE_NOTES.md` "F007 — 已知限制 / 后续工作" 段
