---
name: ahe-design-review
description: 评审 AHE 实现设计，判断它是否已经足够清晰、可追溯、可测试并可进入真人确认与后续任务规划，而不是让任务拆解建立在猜测上。适用于设计草稿已完成、需要正式 review verdict 的场景；若当前阶段不清或证据冲突，先回到 `ahe-workflow-router`。
---

# AHE 设计评审

评审设计文档，并判断它是否已经可以提交给真人确认，作为进入 `ahe-tasks` 的候选已批准输入。

## Overview

这个 skill 用来防止过早拆解任务。

高质量设计评审不只是判断“文档看起来完整”，而是判断：

- 设计是否真正锚定已批准规格
- 关键设计决策是否站得住
- 接口、边界和风险是否已经清楚到足以进入任务规划

## When to Use

在这些场景使用：

- `ahe-design` 已完成设计草稿，需要正式 review verdict
- 用户明确要求“review 这份 design”
- reviewer subagent 被父会话派发来执行设计评审

不要在这些场景使用：

- 当前需要的是继续写或修设计，改用 `ahe-design`
- 当前需要的是任务拆解或编码，改用相应下游节点
- 当前请求只是阶段不清、route 不明或证据冲突，先回到 `ahe-workflow-router`

## Standalone Contract

当用户直接点名 `ahe-design-review` 时，至少确认以下条件：

- 存在当前设计草稿
- 存在已批准规格
- 能读取 `AGENTS.md` 中与设计评审、路径映射和状态命名有关的约定
- 当前请求确实是评审，而不是继续产出设计正文

如果前提不满足：

- 缺设计草稿或只是要继续完善设计：回到 `ahe-design`
- 缺已批准规格、route / stage 判断不清或批准证据冲突：回到 `ahe-workflow-router`

## Chain Contract

当本 skill 作为链路节点被带入时，默认由 reviewer subagent 执行，并读取：

- 已批准的需求规格
- 被评审的设计文档
- `AGENTS.md` 中与设计评审、路径映射和状态命名有关的约定
- `task-progress.md` 中的 `Current Stage` 与 `Workflow Profile`（如果存在）
- 做判断所需的最少技术上下文

本节点完成后应写回：

- review 记录正文
- 结构化 reviewer 返回摘要
- canonical `next_action_or_recommended_skill`

评审记录落盘与结构化摘要由 reviewer 负责；真正向真人展示结论、发起批准确认和推进主链的动作，仍由父会话负责。

## Hard Gates

- 在设计通过评审并经过真人确认之前，不得进入 `ahe-tasks`。
- 如果当前输入工件还不足以判定 stage / route，不直接开始设计评审。
- reviewer 不负责代替父会话发起真人确认，也不顺手开始拆任务或写代码。

## Quality Bar

交付给真人确认前，高质量评审结果至少应做到：

- 明确指出设计是否可追溯到已批准规格
- 明确指出关键风险、隐藏假设和任务规划阻塞点
- 区分“可修补的不完整”与“不能继续规划的阻塞问题”
- 不把评审退化成设计重写、任务拆解或编码建议
- 给出唯一下一步，并保持与 `ahe-workflow-router` 的暂停点契约一致

## Inputs / Required Artifacts

评审完成后，必须将本次结论写入：

- `docs/reviews/design-review-<topic>.md`

如 `AGENTS.md` 为当前项目声明了等价路径，按其中映射路径保存。

若项目尚未形成固定 review 记录格式，默认使用：

- `templates/review-record-template.md`

如果使用通用模板中的英文结论字段，请按以下方式映射：

- `通过` -> `pass`
- `需修改` -> `revise`
- `阻塞` -> `blocked`

如果当前任务正在使用 `task-progress.md` 驱动 workflow，且真人确认通过，还应同步更新：

- 设计文档中的状态字段
- `task-progress.md` 中的 `Current Stage`
- `task-progress.md` 中的 `Next Action Or Recommended Skill`

这些状态字段更新由父会话在真人确认通过后执行；reviewer subagent 不代替父会话写入批准结论。

若项目尚未形成固定进度记录格式，默认使用：

- `templates/task-progress-template.md`

## Workflow

### 1. 先建立证据基线

在给出结论前，先读取并固定以下证据来源：

- 已批准规格
- 当前设计文档
- `AGENTS.md` 中的路径、状态词和模板约定
- `task-progress.md` 中的 `Current Stage` 与 `Workflow Profile`（如果存在）
- 必要的技术上下文

不要只根据会话记忆、用户口头确认或零散聊天内容判断“已批准”或“设计已经讲清楚”。

### 2. 做多维评分与挑战式审查

在形成最终结论前，至少对以下维度做内部评分，评分范围 `0-10`：

- 需求覆盖与追溯
- 架构一致性
- 决策质量
- 接口与任务规划准备度
- 测试准备度与风险可控性

评分不是最终结论本身，但它能帮助区分：

- 哪些只是轻微缺口
- 哪些已经足以拉低到 `需修改`
- 哪些会让任务规划建立在错误前提上，从而升级到 `阻塞`

判定辅助规则：

- 任一关键维度低于 `6/10` 时，不得返回 `通过`
- 任一维度低于 `8/10` 时，通常至少应对应一条具体发现项或薄弱点

### 3. 按 checklist 做正式审查

#### 3.1 需求覆盖与追溯

- 设计是否覆盖了规格中的关键需求？
- 主要行为是否映射到了组件、模块、流程或接口？
- 关键需求能否回指到稳定需求条目、需求编号或等价规格锚点？
- 是否存在新增行为、接口、数据持久化或运营流程，却无法追溯到已批准规格？

#### 3.2 架构一致性

- 职责和边界是否清晰？
- 模块之间的交互是否容易理解？
- 设计是否是连贯架构，而不是组件清单？
- 关键视图、关键交互或关键流程是否已经清楚到足以支撑评审？

#### 3.3 决策质量

- 是否真的比较了至少两个可行方案？
- 是否说明为什么选定当前方案？
- 是否记录了主要收益、代价、风险与缓解思路？

#### 3.4 约束与非功能需求适配

- 设计是否体现了已声明约束？
- 是否考虑了非功能需求和集成点？
- 这些要求是否真正影响了设计，而不是只在概述里被提到？

#### 3.5 接口与任务规划准备度

- 关键契约是否足够明确，可以支撑任务规划？
- 主要数据流和控制流是否清晰？
- 模块边界是否已经稳定到可以继续拆任务？
- 是否还存在会直接破坏任务拆解顺序的设计空洞？

#### 3.6 测试准备度与隐藏假设

- 设计是否包含设计层面的测试策略？
- 该设计是否可测试，而不依赖隐藏假设？
- 是否指出了需要在后续任务规划或实现阶段优先验证的高风险点？

### 4. 形成 verdict、severity 与下一步

severity 统一使用：

- `critical`: 阻塞任务规划，或会直接导致错误任务输入
- `important`: 应在批准前修复
- `minor`: 不阻塞，但建议改进

判定规则：

- 只有在可以追溯到已批准规格、关键决策和接口足够清晰、主要约束和非功能需求被吸收、且不存在足以阻塞任务规划的设计空洞时，才返回 `通过`
- 核心设计可用但仍有局部缺口、决策说明不足、接口描述偏弱、测试准备度不足但可通过一轮定向修订补齐时，返回 `需修改`
- 设计无法清晰支撑需求规格、存在无法追溯到已批准规格的关键新增内容、关键架构决策缺失，或 route / stage / 证据链冲突时，返回 `阻塞`

### 5. 写 review 记录并回传父会话

- 若结论为 `通过`，下一步为 `设计真人确认`，`needs_human_confirmation=true`
- 若结论为 `需修改`，下一步为 `ahe-design`
- 若结论为 `阻塞` 且问题属于设计内容本身，下一步为 `ahe-design`
- 若结论为 `阻塞` 且问题属于需求漂移、规格本身需要变更才能消除追溯断裂、route / stage / 证据冲突，下一步为 `ahe-workflow-router`，并设置 `reroute_via_starter=true`

## Output Contract

review 记录正文请严格使用以下结构：

```markdown
## 结论

通过 | 需修改 | 阻塞

## 发现项

- [critical|important|minor] 问题

## 薄弱或缺失的设计点

- 条目

## 下一步

- `通过`：`设计真人确认`
- `需修改`：`ahe-design`
- `阻塞`：`ahe-design` 或 `ahe-workflow-router`

## 记录位置

- `docs/reviews/design-review-<topic>.md` 或映射路径

## 交接说明

- `设计真人确认`：仅当结论为 `通过`
- `ahe-design`：用于所有需要回修设计内容的场景
- `ahe-workflow-router`：仅在需求漂移、route / stage / 证据链冲突时使用
```

若本 skill 运行在 reviewer subagent 中，`next_action_or_recommended_skill` 必须只写一个 canonical 值，不得把多个候选值拼在同一个字符串里。

最小返回示例：

```json
{
  "conclusion": "通过",
  "next_action_or_recommended_skill": "设计真人确认",
  "record_path": "实际写入的 review 记录路径",
  "key_findings": ["关键发现 1", "关键发现 2"],
  "needs_human_confirmation": true,
  "reroute_via_starter": false
}
```

返回规则：

- `通过`：`next_action_or_recommended_skill=设计真人确认`，`needs_human_confirmation=true`
- `需修改`：`next_action_or_recommended_skill=ahe-design`，`needs_human_confirmation=false`
- `阻塞` 且属于设计内容回修：`next_action_or_recommended_skill=ahe-design`，`needs_human_confirmation=false`
- `阻塞` 且属于需求漂移、规格改动、route / stage / 证据链冲突：`next_action_or_recommended_skill=ahe-workflow-router`，`needs_human_confirmation=false`，`reroute_via_starter=true`

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| “设计已经写了很多，应该可以过了” | 文档长度不等于任务规划准备度。 |
| “任务拆解的时候再补接口和边界也来得及” | 接口和边界不稳会直接污染 `ahe-tasks`。 |
| “这个新增行为实现时自然会补齐” | 无法追溯到已批准规格的关键新增内容必须在 design review 暴露。 |
| “只写结论，不写权衡也没关系” | 没有收益、代价和风险，就无法判断设计决策是否站得住。 |
| “先让真人看，再说是否要修” | review 的职责是先把结论聚焦到可确认状态，而不是把未审清的设计直接丢给真人。 |
| “我顺手把任务也列一下更完整” | reviewer 的职责是 gate 设计，不是提前拆任务。 |

## Red Flags

- 因为“实现时再说”就直接通过
- 把设计评审变成底层编码建议
- 接受只是复述需求、没有设计决策的文档
- 忽略缺失的接口或模块边界
- 忽略无法追溯到已批准规格的新增设计内容
- 设计评审刚返回“通过”就直接进入 `ahe-tasks`
- 不和真人确认，就把设计当成已批准输入

## Verification

只有在以下条件全部满足时，这个 skill 才算完成：

- [ ] 评审记录已经落盘
- [ ] 给出明确结论、发现项、薄弱点和唯一下一步
- [ ] 结构化 reviewer 返回摘要已使用 `next_action_or_recommended_skill`
- [ ] 若结论为 `通过`，已明确要求进入 `设计真人确认`
- [ ] 若本 skill 由 reviewer subagent 执行，已完成对父会话的结构化结果回传
