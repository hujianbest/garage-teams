---
name: ahe-spec-review
description: 评审 AHE 需求规格，判断它是否已经具备范围清晰度、需求可测性、验收标准、开放问题闭合度和进入 approval step 的准备度，而不是把模糊规格提前送进设计阶段。适用于规格草稿已完成、需要正式 review verdict 的场景；若当前阶段不清或证据冲突，先回到 `ahe-workflow-router`。
---

# AHE 需求评审

评审需求规格，并判断它是否已经可以提交给 approval step，作为进入 `ahe-design` 的候选已批准输入。

## Overview

这个 skill 是需求规格冻结门禁。

高质量规格评审不只是判断“文档写得像规格”，而是判断：

- 范围、问题和成功标准是否已经站稳
- 关键需求是否真的可观察、可判断、可验收
- 关键需求是否具备 `ID`、`Priority`、`Source / Trace Anchor`
- 需求粒度是否足够支撑后续设计，而不是把多个独立能力打包在一起
- review findings 是否足够结构化，能让 `ahe-specify` 做 1 到 2 轮定向回修

## When to Use

在这些场景使用：

- `ahe-specify` 已完成规格草稿，需要正式 review verdict
- 用户明确要求“review 这份 spec / SRS”
- reviewer subagent 被父会话派发来执行规格评审

不要在这些场景使用：

- 当前需要的是继续写或修规格，改用 `ahe-specify`
- 当前请求只是阶段不清、route 不明或证据冲突，先回到 `ahe-workflow-router`
- 当前没有可评审的规格草稿

## Standalone Contract

当用户直接点名 `ahe-spec-review` 时，至少确认以下条件：

- 存在当前规格草稿
- 能读取 `AGENTS.md` 中与规格、路径、状态词相关的约定
- 能读取 `task-progress.md` 或等价状态工件（若项目使用）
- 当前请求确实是评审，而不是继续产出规格正文

如果前提不满足：

- 缺规格草稿或只是要继续澄清：回到 `ahe-specify`
- 缺 route / stage 判断或批准证据冲突：回到 `ahe-workflow-router`

优先级规则：

- 若同时存在“没有稳定规格草稿”和“route / stage / profile / 证据冲突”，优先按 workflow blocker 处理，回到 `ahe-workflow-router`
- 只有在 route 明确、stage 明确、上游证据不冲突，但单纯缺稳定规格草稿时，才回到 `ahe-specify`

## Chain Contract

当本 skill 作为链路节点被带入时，默认由 reviewer subagent 执行，并读取：

- 当前需求规格
- 如存在，与规格相邻的 deferred backlog
- `AGENTS.md` 中的路径、模板、术语和状态约定
- `task-progress.md`（如果存在）
- 做判断所需的最少辅助上下文

本节点完成后应写回：

- review 记录正文
- 结构化 reviewer 返回摘要
- canonical `next_action_or_recommended_skill`

评审记录落盘与结构化摘要由 reviewer 负责；真正向用户展示结论、完成 approval step 和推进主链的动作，仍由父会话负责。

## Hard Gates

- 在规格通过评审并完成 approval step 之前，不得进入 `ahe-design`。
- 如果当前输入工件还不足以判定 stage / route，不直接开始规格评审。
- reviewer 不负责代替父会话完成 approval step，也不顺手开始设计。
- reviewer 不得为了让规格“看起来能过”而发明业务事实、优先级、性能阈值或来源锚点。

## Quality Bar

交付给 approval step 前，高质量规格评审结果至少应做到：

- 对齐 `ahe-specify` 的交付契约，而不是只看文档表面完整性
- 用统一 rubric 判断质量、反模式、完整性、粒度和延后处理是否达标
- 明确指出规格中的歧义、冲突、模糊词、缺失来源、缺失优先级和未闭合开放问题
- 对每条 finding 标明 `USER-INPUT` 或 `LLM-FIXABLE`
- 给出足够结构化的 findings，支持 `ahe-specify` 做 1 到 2 轮定向回修
- 不把评审退化成重新澄清一切，或顺手开始做设计

## Inputs / Required Artifacts

评审完成后，必须将本次结论写入：

- `docs/reviews/spec-review-<topic>.md`

如 `AGENTS.md` 为当前项目声明了等价路径，按其中映射路径保存。

若项目尚未形成固定 review 记录格式，默认使用：

- `ahe-coding-skills/templates/review-record-template.md`

如果使用通用模板中的英文结论字段，请按以下方式映射：

- `通过` -> `pass`
- `需修改` -> `revise`
- `阻塞` -> `blocked`

评审时默认使用以下 reference：

- `references/spec-review-rubric.md`

如果当前任务正在使用 `task-progress.md` 驱动 workflow，且 approval step 已完成，还应同步更新：

- 需求规格文档中的状态字段
- `task-progress.md` 中的 `Current Stage`
- `task-progress.md` 中的 `Next Action Or Recommended Skill`

这些状态字段更新由父会话在 approval step 完成后执行；reviewer subagent 不代替父会话写入批准结论。

若项目尚未形成固定进度记录格式，默认使用：

- `ahe-coding-skills/templates/task-progress-template.md`

## Workflow

### 1. 先建立证据基线

在给出结论前，先读取并固定：

- 当前需求规格
- 如存在，当前 deferred backlog
- `AGENTS.md` 中的路径、模板、优先级体系、术语和状态约定
- `task-progress.md`（如果存在）
- 必要时回查少量上下文，用于确认规格状态、批准证据和关键锚点

不要只根据聊天记忆判断“这个规格已经差不多可以过了”。

### 1.5 先判断能否合法进入 review

在正式进入结构检查和 rubric 之前，先做 precheck：

- 是否存在稳定、可定位的当前规格草稿
- 当前 route / stage / profile 是否已明确
- 上游 approval / review / progress evidence 是否彼此一致

处理规则：

- 若 route / stage / profile / 上游证据存在冲突，不进入正式 rubric；直接写最小 blocked precheck record，`next_action_or_recommended_skill=ahe-workflow-router`，并设置 `reroute_via_router=true`
- 若 route 明确、证据不冲突，但缺稳定规格草稿，则写最小 blocked precheck record，`next_action_or_recommended_skill=ahe-specify`
- 只有 precheck 通过后，才继续做结构检查和 rubric 审查

在 interactive 模式下：

- precheck blocked 只向用户说明 workflow / artifact blocker 和下一步
- 不继续追问规格正文细节
- 不把 workflow blocker 伪装成 `USER-INPUT` 的规格问题

### 2. 先确定当前规格的结构契约

review 不是拿一个固定 12 章节模板去硬套所有项目。先判断：

- 项目是否通过 `AGENTS.md` 声明了规格骨架、字段名或优先级体系
- 当前规格是否遵循了项目模板；若无模板，是否至少满足 AHE 默认骨架
- requirement rows 是否以表格、子标题或项目自定义字段承载了同一组语义

只要语义可回读，不强迫文档长得和默认模板一模一样。

### 3. 用 rubric 做正式审查

详细规则见 `references/spec-review-rubric.md`。

#### 3.1 Group Q: Quality Attributes

至少检查：

- 每条核心需求是否可回指到真实来源
- 模糊词是否已量化或替换
- 验收标准是否足以形成通过 / 不通过判断
- 需求之间是否有冲突或重复
- 是否存在缺失 `Priority` 或 `Source / Trace Anchor`

#### 3.2 Group A: Anti-Patterns

至少检查：

- 模糊词
- 复合需求
- 设计泄漏
- 无主体的被动表达
- 关键需求中的 `待确认` / 占位值
- 缺少负路径、边界或权限差异

#### 3.3 Group C: Completeness And Contract

至少检查：

- 核心 `FR` / 关键 `NFR` 是否具备 `ID`、`Statement`、`Acceptance`、`Priority`、`Source / Trace Anchor`
- 范围内 / 范围外内容是否闭合
- 阻塞性开放问题是否已经为空或明确写为 `无`
- 结构是否遵循当前项目模板或默认骨架
- 真实 deferred requirements 是否得到了显式处理

#### 3.4 Group G: Granularity And Scope-Fit

至少检查：

- 是否存在命中 `GS1-GS6` 的 oversized requirements
- 当前轮能力和后续增量能力是否仍混写在一条核心需求里
- findings 是否已经足够具体，能支持 `ahe-specify` 做定向回修，而不是只能“整份重写”

#### 3.5 给每条 finding 分类

以下分类规则适用于已经进入正式 rubric review 的规格内容 findings。

若在 `### 1.5` precheck 阶段就因为 route / stage / profile / 证据冲突提前 `阻塞`，不强行套用 `USER-INPUT` / `LLM-FIXABLE`；应直接返回最小 blocked precheck record 和唯一下一步。

每条 finding 都必须带上：

- `severity`: `critical` / `important` / `minor`
- `classification`: `USER-INPUT` / `LLM-FIXABLE`
- `rule_id`: 对应 rubric 检查项或粒度子信号，例如 `Q2`、`A3`、`C1`、`G1`、`G2`、`G3`、`GS1`

分类规则：

- 缺的是业务事实、外部决策、性能阈值、优先级冲突、来源无法唯一确认时，标 `USER-INPUT`
- 缺的是 wording、拆分、章节放置、重复条目整理、设计泄漏改写时，标 `LLM-FIXABLE`
- 若无法在不新增事实的前提下修复，就不能标成 `LLM-FIXABLE`

### 4. 形成 verdict、severity 与下一步

severity 统一使用：

- `critical`: 阻塞设计，或会直接导致错误设计输入
- `important`: 应在批准前修复
- `minor`: 不阻塞，但建议改进

判定规则：

- 只有在范围清晰、目标明确、核心需求可验收、关键需求具备 `ID / Priority / Source`、无阻塞性开放问题、无阻塞设计的 `USER-INPUT` finding 且规格足以成为 `ahe-design` 稳定输入时，才返回 `通过`
- 规格有用但还不完整，且 findings 能收敛成 1 到 2 轮定向修订补齐时，返回 `需修改`
- 规格过于模糊、核心范围或关键业务规则未定、关键外部约束仍未解决，或 findings 无法被定向回修时，返回 `阻塞`

下一步规则：

- `通过` -> `规格真人确认`
- `需修改` -> `ahe-specify`
- `阻塞` 且属于规格内容或缺失业务输入 -> `ahe-specify`
- `阻塞` 且属于 route / stage / profile / 上游证据冲突 -> `ahe-workflow-router`

### 5. 写 review 记录并回传父会话

- 若结论为 `通过`，下一步为 `规格真人确认`，`needs_human_confirmation=true`
- 若结论为 `需修改`，下一步为 `ahe-specify`
- 若结论为 `阻塞` 且问题属于规格内容本身，下一步为 `ahe-specify`
- 若结论为 `阻塞` 且问题属于 route / stage / 证据冲突，下一步为 `ahe-workflow-router`，并设置 `reroute_via_router=true`

review findings 应足够具体，使 `ahe-specify` 可以按条修订，而不是只能得到一句“规格还不够好”。

在 interactive 模式下，review 记录与用户可见摘要不是一回事：

- 完整 rubric、finding breakdown、rule_id 和全部 findings 留在 review 记录中
- 父会话对用户先展示 1 到 2 句 plain-language 结论，再只提出必须由用户回答的 `USER-INPUT` 问题
- 若同时存在 `USER-INPUT` 和 `LLM-FIXABLE` findings，对用户说明“其余结构 / wording / 拆分问题将由 `ahe-specify` 直接回修”，不要把可直接修文的项转嫁给用户
- 若 `USER-INPUT` finding 为 0，不应为了 review 结果再向用户抛出额外问卷；直接将修订重点带回 `ahe-specify`
- 若 `USER-INPUT` finding 为 1 到 3 个且彼此独立，优先一次编号问完；若后一个问题依赖前一个答案，再顺序追问
- 不要在用户消息里整段粘贴 rubric、JSON 或完整 finding 列表；用户侧只保留完成当前决策所需的最小信息
- 若 `reroute_via_router=true`，父会话只说明 workflow / evidence blocker 与下一步 router，不继续展示规格细节问题

## Output Contract

review 记录正文请严格使用以下结构：

```markdown
## 结论

通过 | 需修改 | 阻塞

## 发现项

- [critical|important|minor][USER-INPUT|LLM-FIXABLE][Q1|A2|C3|G1|G2|G3|GS1] 问题

## 缺失或薄弱项

- 条目

## 下一步

- `通过`：`规格真人确认`
- `需修改`：`ahe-specify`
- `阻塞`：`ahe-specify` 或 `ahe-workflow-router`

## 记录位置

- `docs/reviews/spec-review-<topic>.md` 或映射路径

## 交接说明

- `规格真人确认`：仅当结论为 `通过`；`interactive` 下等待真人，`auto` 下由父会话写 approval record
- `ahe-specify`：用于所有需要回修规格内容的场景；若存在 `USER-INPUT` finding，必须先向用户提出定向问题；若不存在，则不把 `LLM-FIXABLE` 问题转嫁给用户
- `ahe-workflow-router`：仅在 route / stage / 证据链冲突时使用
```

若本 skill 运行在 reviewer subagent 中，`next_action_or_recommended_skill` 必须只写一个 canonical 值，不得把多个候选值拼在同一个字符串里。

交互约束：

- `key_findings` 在 interactive 场景下，若存在 `USER-INPUT` finding，则只写 plain-language 的用户必答问题；其他关键信息留在 review 记录中
- 若存在 `USER-INPUT` finding，父会话应只向用户展示这些问题，不直接转发完整 rubric
- 若不存在 `USER-INPUT` finding，父会话可以概述修订重点，但不应要求用户亲自修 wording、拆分或章节整理问题
- 若是 precheck blocked 且 `reroute_via_router=true`，`key_findings` 只写 workflow blocker 的 plain-language 摘要，不写规格正文问题

最小返回示例：

```json
{
  "conclusion": "需修改",
  "next_action_or_recommended_skill": "ahe-specify",
  "record_path": "实际写入的 review 记录路径",
  "key_findings": ["[important][USER-INPUT][Q2] 响应时间缺少可验证阈值"],
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "finding_breakdown": [
    {
      "severity": "important",
      "classification": "USER-INPUT",
      "rule_id": "Q2",
      "summary": "响应时间缺少可验证阈值"
    }
  ]
}
```

precheck blocked 示例：

```json
{
  "conclusion": "阻塞",
  "next_action_or_recommended_skill": "ahe-workflow-router",
  "record_path": "实际写入的 review 记录路径",
  "key_findings": ["当前没有稳定 spec draft，且 stage / approval evidence 冲突，需先回到 ahe-workflow-router 重判"],
  "needs_human_confirmation": false,
  "reroute_via_router": true
}
```

返回规则：

- `通过`：`next_action_or_recommended_skill=规格真人确认`，`needs_human_confirmation=true`
- `需修改`：`next_action_or_recommended_skill=ahe-specify`，`needs_human_confirmation=false`
- `阻塞` 且属于规格内容回修：`next_action_or_recommended_skill=ahe-specify`，`needs_human_confirmation=false`
- `阻塞` 且属于 route / stage / 证据链冲突：`next_action_or_recommended_skill=ahe-workflow-router`，`needs_human_confirmation=false`，`reroute_via_router=true`
- precheck blocked 时也沿用上面的 `阻塞` 返回规则；区别只是跳过正式 rubric，不强行生成 spec-content finding taxonomy

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| “规格大体上差不多了，先过吧” | 通过意味着它已具备进入 approval step 和设计的稳定输入质量。 |
| “设计阶段再补这些开放问题也来得及” | 会阻塞设计的问题必须在 spec review 阶段暴露并收口。 |
| “验收标准写得有点弱，但实现时自然会补齐” | 验收标准弱会直接让设计和实现继承歧义。 |
| “先口头说一下范围外内容，不必落盘” | 未落盘的范围外内容无法稳定约束后续设计。 |
| “这轮就别太严格了，反正还要 approval step” | approval step 不是替代 review；review 应先把问题聚焦到可确认状态。 |
| “我顺手给出设计建议会更高效” | reviewer 的职责是 gate 规格，不是偷偷开始设计。 |
| “priority 或 source 缺一点没关系，作者回去自己补就行” | 缺失是否能补，取决于它是不是 `USER-INPUT`；不能假设 author 一定知道答案。 |
| “一个 FR 虽然很大，但整体意思能看懂就可以过” | 命中 `GS1-GS6` 的 oversized requirement 会直接污染设计输入。 |
| “项目没用默认 12 章节，所以结构不合格” | 结构是否合格取决于当前模板或 `AGENTS.md`，不是 reviewer 个人偏好。 |
| “把完整 rubric 和所有 findings 原样贴给用户最省事” | review record 要完整，但 interactive 场景下用户只应看到必须回答的问题和最小结论摘要。 |
| “顺手让用户一起决定 wording、拆分和章节问题更高效” | `LLM-FIXABLE` 问题应由 `ahe-specify` 直接回修，不要转嫁给用户。 |
| “既然没有稳定 spec draft，就先按 spec 内容继续问下去” | 如果同时存在 route / stage / 证据冲突，优先回 router，而不是继续假装已经进入合法 review。 |

## Red Flags

- 把评审变成重新设计
- 因为“后面再想”就直接批准
- 把隐含范围当成可以接受
- 忽略缺失的验收标准
- 忽略缺失的 `Priority` 或 `Source / Trace Anchor`
- 忽略仍未闭合的阻塞性开放问题
- 评审 findings 没有 `USER-INPUT` / `LLM-FIXABLE` 分类
- interactive 模式下把完整 rubric / JSON / 全量 findings 原样贴给用户
- 把 `LLM-FIXABLE` 问题作为“请用户回答”的作业抛回去
- 命中 `reroute_via_router=true` 后仍继续追问规格正文细节
- 因为项目模板不同，就机械判定结构不合格
- 评审刚返回“通过”就直接进入 `ahe-design`
- 不完成 approval step，就把规格当成已批准输入

## Verification

只有在以下条件全部满足时，这个 skill 才算完成：

- [ ] 评审记录已经落盘
- [ ] 给出明确结论、发现项、薄弱项和唯一下一步
- [ ] 若进入正式 rubric review，发现项已标明 `severity`、`classification` 和 `rule_id`
- [ ] 若在 precheck 阶段提前 `阻塞`，已写明 workflow blocker、唯一下一步和是否 `reroute_via_router`
- [ ] 结构化 reviewer 返回摘要已使用 `next_action_or_recommended_skill`
- [ ] 若存在 `USER-INPUT` finding，已能支持父会话向用户发起最小定向问题，而不是倾倒完整 rubric
- [ ] 若结论为 `通过`，已明确要求进入 `规格真人确认` 这一 approval step
- [ ] 若本 skill 由 reviewer subagent 执行，已完成对父会话的结构化结果回传
