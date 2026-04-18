# Review Record - F003: Garage Memory 自动知识提取与经验推荐

## Metadata

- Review Type: HF Spec Review
- Scope: `docs/features/F003-garage-memory-auto-extraction.md`
- Reviewer: Independent Reviewer
- Date: 2026-04-18
- Record Path: `docs/reviews/spec-review-F003-garage-memory-auto-extraction.md`

## Inputs

- Primary Artifact: `docs/features/F003-garage-memory-auto-extraction.md`
- Supporting Context:
  - `AGENTS.md`
  - `task-progress.md`
  - `.agents/skills/hf-spec-review/SKILL.md`
  - `docs/soul/user-pact.md`
  - `docs/soul/growth-strategy.md`

## Precheck 结果

**Precheck 通过**，可以进入正式 rubric review：

- 存在稳定、可定位的规格草稿，且文档状态明确为“草稿”
- `task-progress.md` 明确当前 `Current Stage: hf-specify`、`Pending Reviews And Gates: hf-spec-review`、`Next Action Or Recommended Skill: hf-spec-review`
- route / stage / profile 证据一致，没有需要改走 `hf-workflow-router` 的冲突
- 当前请求是独立 reviewer 对规格草稿执行正式评审，符合 `hf-spec-review` 适用条件

## 结构契约确认

当前规格遵循 HF 默认规格骨架，包含背景、目标、范围、FR / NFR / IFR / CON / ASM / 开放问题等完整章节。

同时，规格已明确守住 Garage 的核心边界：

- 自动提取停留在“候选草稿/建议”层
- 发布前必须经过用户确认
- 不允许静默自动发布

以上约束在 `FR-303`、`NFR-302`、`CON-302` 中有明确表达，符合 Garage “系统可以建议，但不能替用户发布”的愿景约束。

## 正式 Findings

### Group Q / C / G

- [important][USER-INPUT][Q4] **“主动推荐”与“按需调用”存在行为冲突，推荐闭环尚未闭合**：成功标准 2.2、关键场景 3.2 和 `FR-305` 都要求系统在“下一次相似任务”中主动推荐历史知识；但 `IFR-303` 又把推荐定义为“可调用的查询能力”，并允许“调用方不需要推荐时不触发查询”。当前规格没有明确第一版到底是“默认主动弹出推荐”，还是“宿主/CLI 选择性调用推荐”。这会直接影响设计主干与验收方式，需由作者补齐唯一产品判定。

- [important][USER-INPUT][C6] **自动提取的成功判定过于空泛，无法证明“不是只留下原始记录”**：`FR-301` 的首条验收标准写成“生成至少 0 条以上结构化候选草稿”，在存在可读取证据时仍允许零候选通过。这样会使“自动提取可用”的 success criteria 失去可判定性。规格需要明确：在什么条件下 evidence-bearing session 可以合法地产生 0 条候选，以及什么情形才算一次成功的自动提取。

- [important][LLM-FIXABLE][C1] **范围内能力“候选分类”尚未进入正式需求契约**：4.1 范围声明“至少支持 decision / pattern / solution / experience summary 四类候选”，但正文没有对应的 FR / NFR / IFR 验收条款；`FR-302` 只要求候选带有“类型”，并未要求系统必须支持这四类。当前这项范围内能力不可测、不可追溯，需升格为正式 contract。

- [important][USER-INPUT][C7] **用户审阅负担的边界仍停留在假设层，approval 前未闭合**：`ASM-302` 假设用户愿意审阅“小批量候选”，并在缓解措施中提出“控制单次候选数量，并支持批量拒绝或延后处理”；但对应的产品边界没有进入 FR/NFR，也没有定义“小批量”阈值。与此同时，`FR-303` 要求用户对每条候选都做接受/编辑后接受/拒绝动作。当前规格无法判断第一版允许多大的确认摩擦，这属于 approval 前应关闭的 USER-INPUT 问题。

## 缺失或薄弱项

- 自动提取“非空候选”与“合法零候选”的边界缺少明确判定
- 推荐闭环的默认触发策略未定：主动推荐还是宿主按需调用
- “四类候选”尚未写成可验收的正式 requirement contract
- 用户确认负担只写在 assumption，没有形成当前轮的明确产品边界

## 结论

**需修改**

这份规格的方向是对的，且已经明确守住了 Garage 的核心价值边界：自动提取只能到候选层，不能绕过用户直接发布；workspace-first、文件可追踪、失败安全降级也都写得较清楚。

但 approval 前仍有 3 个重要的 USER-INPUT 问题和 1 个重要的 contract 缺口没有闭合。它们集中在“推荐是否主动触发”“什么算一次成功的自动提取”“第一版允许多大确认摩擦”这几个会影响设计输入稳定性的点上。问题是定向可修的，因此结论为“需修改”，而不是“阻塞”。

## 发现项汇总

- [important][USER-INPUT][Q4] “主动推荐”与“按需调用”存在行为冲突
- [important][USER-INPUT][C6] 自动提取成功判定允许 vacuous pass
- [important][LLM-FIXABLE][C1] “四类候选”缺少正式 requirement contract
- [important][USER-INPUT][C7] 用户审阅负担边界未闭合

## 下一步

**推荐下一步**：`hf-specify`

作者应先补齐上述 USER-INPUT 决策，并把“四类候选”补成正式需求契约；完成定向回修后，再重新进入 `hf-spec-review`。

## USER-INPUT 问题清单

1. 第一版推荐链路到底是默认“主动推荐”，还是只提供“宿主/CLI 可调用的推荐能力”？
2. 在 session 已有可读取证据的情况下，哪些条件允许系统合法地产生 0 条候选？什么情形才算一次成功的自动提取？
3. 第一版允许的候选确认负担边界是什么？是否需要把“单次候选上限”“批量拒绝”“延后处理”中的一部分纳入当前范围？

## 记录位置

- `docs/reviews/spec-review-F003-garage-memory-auto-extraction.md`

## 交接说明

- 当前结论不是 workflow blocker，不需要改走 `hf-workflow-router`
- 当前结论也不是 approval-ready，因此下一步不是“规格真人确认”
- 回修应由 `hf-specify` 处理，完成后再发起新一轮 `hf-spec-review`
