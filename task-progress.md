# Task Progress

## Goal

- Goal: F008 — Garage Coding Pack 与 Writing Pack（已 closeout）
- Owner: hujianbest
- Status: ✅ Closed — F008 cycle 完整 closeout（T1a/T1b/T1c + T2 + T3 + T4a/T4b/T4c + T5 + 全部 review/gate + finalize）
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
- Workflow Profile: `N/A`（无活跃 cycle）
- Execution Mode: `N/A`
- Workspace Isolation: `in-place`
- Current Active Task: 无
- Pending Reviews And Gates: 无
- Next Action Or Recommended Skill: `null`
- Relevant Files:
  - `docs/verification/F008-finalize-closeout-pack.md`（F008 workflow closeout pack）
  - `docs/verification/F008-completion-gate.md`、`docs/verification/F008-regression-gate.md`
  - `docs/features/F008-garage-coding-pack-and-writing-pack.md`（已批准规格 r2 + design/tasks 阶段反向同步 wording）
  - `docs/designs/2026-04-22-garage-coding-pack-and-writing-pack-design.md`（已批准设计 r2，9 ADR + 9 sub-commit + 9 INV + 5 测试文件）
  - `docs/tasks/2026-04-22-garage-coding-pack-and-writing-pack-tasks.md`（已批准任务计划 r4，9 task）
  - `docs/approvals/F008-{spec,design,tasks}-approval.md`
  - `docs/reviews/{spec(r1+r2),design(r1+r2),tasks(r1+r2+r3+r4),test,code,traceability}-review-F008-*.md`（完整 review 链路）
  - `RELEASE_NOTES.md`（按 cycle 倒序记录用户可见变化；首条目 = F008，含 9 sub-commit 完整列表 + manual smoke 实测数据）
  - `AGENTS.md`（更新 ## Packs & Host Installer (F007/F008) 段 + 当前 packs 表 + IDE 加载入口段）
  - `packs/{garage,coding,writing}/`（3 pack 落地内容物，含 22 + 3 + 4 = 29 skill）
  - `tests/adapter/installer/test_{skill_anatomy_drift,full_packs_install,packs_garage_extended,dogfood_layout,neutrality_exemption_list}.py`（5 个新增测试文件）
  - `docs/principles/skill-anatomy.md`（drift 反向同步收敛后状态，与 packs/coding/principles/ 字节相等）
  - `docs/soul/manifesto.md`、`user-pact.md`、`design-principles.md`、`growth-strategy.md`（项目灵魂，跨 cycle 仍生效）
- Constraints:
  - Stage 2 仍保持 workspace-first，不引入外部数据库、常驻服务、Web UI
  - 优先使用 markdown、JSON、文件系统存储
  - 所有数据存储在 Garage 仓库内部
  - F008 落地后 manifesto 承诺的"挂上 Garage 目录几秒变成你的 Agent"在交付路径上已闭合（packs 内容物从 1 → 29 skill）

## Next Step

无活跃下一步。下一个 cycle 启动时由 `hf-workflow-router` 重新建立 stage / profile / mode / active task。

可选的后续候选（由 `hf-workflow-router` 在新 cycle 中独立判断与拆分）：

- **F009 候选 — D7 安装管道扩展为递归 `references/` 子目录**：闭合 design ADR-D8-4 接受的"文档级提示"工程边界，让下游宿主装后 family-level 引用直接可达
- **F009 候选 — `garage uninstall --hosts <list>` + `garage update --hosts <list>`**：F007 显式 deferred 的安装逆向操作 + 拉新流程
- **单独候选 — `~/.claude/skills/` 全局安装**（OpenSpec issue #752 模式）：solo creator 跨多客户仓库的需求；与 Garage workspace-first 信念有 trade-off，应单独 spec 化
- **F008+ 候选 — 新增宿主**（Codex / Gemini CLI / Windsurf / Copilot 等）：F007/F008 已确立 first-class adapter 注册模式；新增宿主成本 = 1 个 adapter 子模块 + 注册表 1 行
- **`packs/product-insights/`**：F001 CON-002 提及但仓库当前无任何 product discovery skill 内容物；待真实内容物到位后再开 cycle
- **F008 minor 残留清理 cycle**（5-6 条 LLM-FIXABLE，全部归档至 F008 closeout pack "Limits / Open Notes" 段）：可选 minor cleanup cycle 一次性清理
- 处理 F006 finalize 中显式延后的 minor：`_recommend_experience` 多次累加语义对齐；CON-501/502/NFR-602 契约测试
- 处理 F006 § 5 deferred backlog：`garage knowledge unlink` / 多跳 graph / experience link / 跨类型 link / 图导出 / `recommend --format json`
- 处理 pre-existing baseline 的 1 个 mypy error（`_memory_review` line 562 on main）+ 47 个 ruff stylistic warnings（F002/F003/F004 历史；F008 已确认未新增）
- 评估是否启动 Stage 3（"工匠"）：进入信号 "知识库条目 >100" 仍依赖用户使用频率；F008 把 packs 内容物从 1 推到 29 后，growth-strategy.md 的 "Skills 数量 > 30" 触发信号已基本就位（差 1）
- 详见 `RELEASE_NOTES.md` "F008 — 已知限制 / 后续工作" 段
