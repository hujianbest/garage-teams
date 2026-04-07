---
name: ahe-spec-review
description: 评审 AHE 需求规格，判断它是否已经具备范围清晰度、需求可测性、验收标准、开放问题闭合度和进入真人确认的准备度，而不是把模糊规格提前送进设计阶段。适用于规格草稿已完成、需要正式 review verdict 的场景；若当前阶段不清或证据冲突，先回到 `ahe-workflow-router`。
---

# AHE 需求评审

评审需求规格，并判断它是否已经可以提交给真人确认，作为进入 `ahe-design` 的候选已批准输入。

## Overview

这个 skill 是需求规格冻结门禁。

高质量规格评审不只是判断“文档写得像规格”，而是判断：

- 范围、问题和成功标准是否已经站稳
- 关键需求是否真的可观察、可判断、可验收
- 规格是否已经足以成为 `ahe-design` 的稳定输入

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

## Chain Contract

当本 skill 作为链路节点被带入时，默认由 reviewer subagent 执行，并读取：

- 当前需求规格
- `AGENTS.md` 中的路径、模板、术语和状态约定
- `task-progress.md`（如果存在）
- 做判断所需的最少辅助上下文

本节点完成后应写回：

- review 记录正文
- 结构化 reviewer 返回摘要
- canonical `next_action_or_recommended_skill`

评审记录落盘与结构化摘要由 reviewer 负责；真正向真人展示结论、发起批准确认和推进主链的动作，仍由父会话负责。

## Hard Gates

- 在规格通过评审并经过真人确认之前，不得进入 `ahe-design`。
- 如果当前输入工件还不足以判定 stage / route，不直接开始规格评审。
- reviewer 不负责代替父会话发起真人确认，也不顺手开始设计。

## Quality Bar

交付给真人确认前，高质量规格评审结果至少应做到：

- 对齐 `ahe-specify` 的交付契约，而不是只看文档表面完整性
- 明确指出规格中的歧义、冲突、模糊词和未闭合开放问题
- 明确指出哪些问题会直接阻塞设计
- 不把评审退化成重新澄清一切，或顺手开始做设计

## Inputs / Required Artifacts

评审完成后，必须将本次结论写入：

- `docs/reviews/spec-review-<topic>.md`

如 `AGENTS.md` 为当前项目声明了等价路径，按其中映射路径保存。

若项目尚未形成固定 review 记录格式，默认使用：

- `templates/review-record-template.md`

如果使用通用模板中的英文结论字段，请按以下方式映射：

- `通过` -> `pass`
- `需修改` -> `revise`
- `阻塞` -> `blocked`

如果当前任务正在使用 `task-progress.md` 驱动 workflow，且真人确认通过，还应同步更新：

- 需求规格文档中的状态字段
- `task-progress.md` 中的 `Current Stage`
- `task-progress.md` 中的 `Next Action Or Recommended Skill`

这些状态字段更新由父会话在真人确认通过后执行；reviewer subagent 不代替父会话写入批准结论。

若项目尚未形成固定进度记录格式，默认使用：

- `templates/task-progress-template.md`

## Workflow

### 1. 先建立证据基线

在给出结论前，先读取并固定：

- 当前需求规格
- `AGENTS.md` 中的路径、模板、术语和状态约定
- `task-progress.md`（如果存在）
- 必要时回查少量上下文，用于确认规格状态、批准证据和关键锚点

不要只根据聊天记忆判断“这个规格已经差不多可以过了”。

### 2. 用冷读者视角检查规格

把自己当成一个马上要进入设计阶段、但没有聊天上下文的读者，重点问：

- 这个规格到底服务谁、解决什么问题、怎么判断成功？
- 哪些需求真的可验收，哪些只是听起来像要求？
- 如果把规格交给设计人员，哪里还会逼着对方补脑？

### 3. 按 checklist 做正式审查

#### 3.1 问题、范围与成功标准

- 问题陈述是否清晰？
- 规格是否清楚说明服务对象、目标与成功标准？
- 当前规格是否代表一个可被评审、可被设计的本轮增量？
- 范围内内容是否明确？
- 范围外内容是否显式写出？

#### 3.2 需求质量与结构完整性

- 核心需求是否可观察、可测试？
- 关键功能需求是否带有对应验收标准？
- 是否存在重复、冲突、孤立或无法判断的需求条目？
- 需求描述中是否避免了隐藏设计决策？

#### 3.3 非功能需求与模糊词审计

- 模糊表达是否被移除或量化？
- 相关非功能需求与关键约束是否写成可判断、可验收的条件？
- 是否存在“快速 / 稳定 / 安全 / 友好”这类没有判断标准的表述？

#### 3.4 边界、依赖、接口与例外

- 主要用户角色是否已识别？
- 边界情况或负路径是否至少被识别出来？
- 约束、依赖、外部接口和假设是否写明？
- 范围例外、边界条件和失败路径是否足以支撑后续设计？

#### 3.5 开放问题与设计准备度

- 阻塞性开放问题是否被清楚标出？
- 若规格准备进入真人确认，阻塞性开放问题是否已经为空或明确写为“无”？
- 剩余非阻塞开放问题是否真的不会改变设计主干判断？
- 设计人员能否在不猜测基础信息的情况下继续？

### 4. 形成 verdict、severity 与下一步

severity 统一使用：

- `critical`: 阻塞设计，或会直接导致错误设计输入
- `important`: 应在批准前修复
- `minor`: 不阻塞，但建议改进

判定规则：

- 只有在范围清晰、目标明确、核心需求可验收、无阻塞性开放问题且规格足以成为 `ahe-design` 稳定输入时，才返回 `通过`
- 规格有用但还不完整、验收标准偏弱、边界和非功能要求仍可通过一轮定向修订补齐时，返回 `需修改`
- 规格过于模糊、核心范围或问题不清、关键矛盾未解决、阻塞性开放问题仍未闭合，或设计将被迫补脑时，返回 `阻塞`

### 5. 写 review 记录并回传父会话

- 若结论为 `通过`，下一步为 `规格真人确认`，`needs_human_confirmation=true`
- 若结论为 `需修改`，下一步为 `ahe-specify`
- 若结论为 `阻塞` 且问题属于规格内容本身，下一步为 `ahe-specify`
- 若结论为 `阻塞` 且问题属于 route / stage / 证据冲突，下一步为 `ahe-workflow-router`，并设置 `reroute_via_starter=true`

## Output Contract

review 记录正文请严格使用以下结构：

```markdown
## 结论

通过 | 需修改 | 阻塞

## 发现项

- [critical|important|minor] 问题

## 缺失或薄弱项

- 条目

## 下一步

- `通过`：`规格真人确认`
- `需修改`：`ahe-specify`
- `阻塞`：`ahe-specify` 或 `ahe-workflow-router`

## 记录位置

- `docs/reviews/spec-review-<topic>.md` 或映射路径

## 交接说明

- `规格真人确认`：仅当结论为 `通过`
- `ahe-specify`：用于所有需要回修规格内容的场景
- `ahe-workflow-router`：仅在 route / stage / 证据链冲突时使用
```

若本 skill 运行在 reviewer subagent 中，`next_action_or_recommended_skill` 必须只写一个 canonical 值，不得把多个候选值拼在同一个字符串里。

最小返回示例：

```json
{
  "conclusion": "通过",
  "next_action_or_recommended_skill": "规格真人确认",
  "record_path": "实际写入的 review 记录路径",
  "key_findings": ["关键发现 1", "关键发现 2"],
  "needs_human_confirmation": true,
  "reroute_via_starter": false
}
```

返回规则：

- `通过`：`next_action_or_recommended_skill=规格真人确认`，`needs_human_confirmation=true`
- `需修改`：`next_action_or_recommended_skill=ahe-specify`，`needs_human_confirmation=false`
- `阻塞` 且属于规格内容回修：`next_action_or_recommended_skill=ahe-specify`，`needs_human_confirmation=false`
- `阻塞` 且属于 route / stage / 证据链冲突：`next_action_or_recommended_skill=ahe-workflow-router`，`needs_human_confirmation=false`，`reroute_via_starter=true`

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| “规格大体上差不多了，先过吧” | 通过意味着它已具备进入真人确认和设计的稳定输入质量。 |
| “设计阶段再补这些开放问题也来得及” | 会阻塞设计的问题必须在 spec review 阶段暴露并收口。 |
| “验收标准写得有点弱，但实现时自然会补齐” | 验收标准弱会直接让设计和实现继承歧义。 |
| “先口头说一下范围外内容，不必落盘” | 未落盘的范围外内容无法稳定约束后续设计。 |
| “这轮就别太严格了，反正还要真人确认” | 真人确认不是替代 review；review 应先把问题聚焦到可确认状态。 |
| “我顺手给出设计建议会更高效” | reviewer 的职责是 gate 规格，不是偷偷开始设计。 |

## Red Flags

- 把评审变成重新设计
- 因为“后面再想”就直接批准
- 把隐含范围当成可以接受
- 忽略缺失的验收标准
- 忽略仍未闭合的阻塞性开放问题
- 评审刚返回“通过”就直接进入 `ahe-design`
- 不和真人确认，就把规格当成已批准输入

## Verification

只有在以下条件全部满足时，这个 skill 才算完成：

- [ ] 评审记录已经落盘
- [ ] 给出明确结论、发现项、薄弱项和唯一下一步
- [ ] 结构化 reviewer 返回摘要已使用 `next_action_or_recommended_skill`
- [ ] 若结论为 `通过`，已明确要求进入 `规格真人确认`
- [ ] 若本 skill 由 reviewer subagent 执行，已完成对父会话的结构化结果回传
