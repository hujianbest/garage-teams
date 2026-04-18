# Review Record - F003: Garage Memory 自动知识提取与经验推荐（Round 2）

## Metadata

- Review Type: HF Spec Review
- Scope: `docs/features/F003-garage-memory-auto-extraction.md`
- Reviewer: Independent Reviewer
- Date: 2026-04-18
- Record Path: `docs/reviews/spec-review-F003-garage-memory-auto-extraction-r2.md`
- Review Basis: 定向复核上一轮 review 的 4 个 finding 是否已关闭，并重新执行 precheck + rubric

## Inputs

- Primary Artifact: `docs/features/F003-garage-memory-auto-extraction.md`
- Previous Review Record: `docs/reviews/spec-review-F003-garage-memory-auto-extraction.md`
- Supporting Context:
  - `AGENTS.md`
  - `task-progress.md`
  - `.agents/skills/hf-spec-review/SKILL.md`
  - `.agents/skills/hf-spec-review/references/spec-review-rubric.md`
  - `.agents/skills/hf-spec-review/references/review-record-template.md`
  - `docs/soul/user-pact.md`
  - `docs/soul/growth-strategy.md`

## Precheck 结果

**Precheck 通过**，可以进入第二轮正式 rubric review：

- 存在稳定、可定位的规格草稿，且 `task-progress.md` 仍明确当前任务为 F003 规格评审前状态
- `Current Stage: hf-specify`、`Pending Reviews And Gates: hf-spec-review`、`Next Action Or Recommended Skill: hf-spec-review` 三者一致
- route / stage / profile / active task 没有冲突，不需要改走 `hf-workflow-router`
- 本轮请求明确是对既有 spec 执行第二轮独立 `hf-spec-review`

## 结构契约确认

当前规格继续遵循 HF 默认规格骨架，包含背景、目标、范围、术语、FR / NFR / IFR / CON / ASM / 开放问题等核心章节。

同时，Garage 的核心价值边界仍被明确守住：

- 自动提取只产生候选草稿，不越过用户直接发布
- 所有自动化都有开关，可关闭、可降级
- 数据仍保持 workspace-first、文件可追踪、宿主无关

这与 `docs/soul/user-pact.md` 和 `docs/soul/growth-strategy.md` 的 Stage 2 方向一致，可作为进入 approval step 的稳定规格输入。

## 上一轮 4 个 Finding 的定向回修复核

### 1. [Q4] “主动推荐”与“按需调用”行为冲突

**结论：已解决**

- `FR-305` 现在明确要求：当系统开始执行相似任务时，系统必须默认主动查询历史 knowledge 与 experience，并返回相关推荐结果
- `IFR-303` 现在把推荐查询定义为“第一版默认主动推荐的底层接口”，并补充了“未显式关闭推荐功能时，任务开始阶段默认触发一次推荐查询”
- 因此，“可调用接口”被收敛为实现表面，“默认主动推荐”被收敛为产品行为，不再冲突

### 2. [C6] 自动提取成功判定过于空泛，可 vacuous pass

**结论：已解决**

- `FR-301` 现在区分了三类场景：
  - 命中至少一条满足最小质量门槛的知识信号 → 必须生成至少 1 条结构化候选
  - 没有可提取证据 → 允许 0 条候选，并记录“无可提取证据”
  - 有证据但全部因重复、信息不足或未达到门槛被过滤 → 允许 0 条候选，并记录“已评估但未形成候选”的原因摘要
- 这样“合法零候选”和“提取成功”边界已被显式写入 contract，能够支撑验收判断

### 3. [C1] “四类候选”未进入正式 requirement contract

**结论：已解决**

- `FR-302a` 已把“第一版必须支持 decision / pattern / solution / experience summary 四类候选”升格为正式需求
- 该需求已具备 `ID`、`Priority`、`Source`、`Statement` 与可执行的 acceptance criteria
- 范围 4.1 中的“候选分类”现在已能回指到正式 contract

### 4. [C7] 用户审阅负担边界仅停留在 assumption 层

**结论：已解决**

- `FR-303a` 已将确认负担控制正式化，明确第一版：
  - 单次待确认候选上限为 5 条
  - 超过 5 条时只保留优先级最高的 5 条进入待确认队列
  - 支持批量拒绝
  - 支持延后处理且不发布知识
- 因此，上一轮要求关闭的产品边界已经从 assumption 进入正式 FR contract

## 正式 Findings

本轮未发现新的 `critical` 或 `important` finding。

本轮也未发现会阻止 approval step 的 `USER-INPUT` 未闭合问题。

## 缺失或薄弱项

- 无阻塞设计主干的缺失项
- 第 12 节保留的开放问题均属于设计阶段可继续收敛事项，不改变当前规格主干

## 结论

**通过**

本轮复核表明，上一轮 4 个 finding 都已经被定向回修完成，而且修复方式已经进入正式需求契约，而不是继续停留在 prose 或 assumption 中。

当前规格的范围边界、用户控制门禁、失败降级、推荐闭环与追溯要求已经足够清晰、可验收、可追溯，可作为 `hf-design` 的稳定输入。按照 HF workflow，下一步应进入 `规格真人确认`，而不是继续回到 `hf-specify`。

## 发现项汇总

- 上一轮 [Q4] 推荐触发行为冲突已通过 `FR-305` + `IFR-303` 收敛
- 上一轮 [C6] 自动提取成功判定已通过 `FR-301` 明确“非空候选”与“合法零候选”边界
- 上一轮 [C1] “四类候选”已通过 `FR-302a` 升格为正式 contract
- 上一轮 [C7] 用户确认负担已通过 `FR-303a` 形成明确产品边界

## 下一步

**推荐下一步**：`规格真人确认`

## 记录位置

- `docs/reviews/spec-review-F003-garage-memory-auto-extraction-r2.md`

## 交接说明

- 当前结论不是 workflow blocker，不需要改走 `hf-workflow-router`
- 当前结论已达到 approval-ready，下一步应执行 `规格真人确认`
- reviewer 不代替父会话完成 approval step，也不直接进入 `hf-design`
