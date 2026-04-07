---
name: ahe-increment
description: 在不绕过规格与设计纪律的前提下处理需求变更。适用于用户明确要求增删改需求、`ahe-workflow-router` 已判定当前属于 increment 分支、或已批准范围 / 验收 / 约束发生变化、必须在继续实现前先完成高质量变更分析、失效判断、工件同步与 canonical re-entry handoff 的场景。本 skill 不直接推进实现，而是负责把增量变化安全带回 AHE 主链。
---

# AHE 增量变更

处理需求变更，但不能把变化偷偷渗透到主链下游。

## Overview

这个 skill 用来把“范围、验收或约束变化”重新锚定回正确阶段。

高质量 increment 不只是记录“需求变了”，而是判断：

- 当前变化是不是 increment，而不是 hotfix 或单纯澄清
- 哪些批准、任务、验证证据和活动任务已经失效
- 应该把主链安全地回流到哪个唯一 canonical 节点

## When to Use

在这些场景使用：

- 用户明确要求增删改需求、范围、验收标准或约束
- `ahe-workflow-router` 已判定当前属于 increment 分支
- 已批准规格 / 设计 / 任务 / 验证依据发生了实质性变化
- 当前需要先完成影响分析与工件同步，再决定回到哪个主链节点

不要在这些场景使用：

- 当前问题本质上是“原本应成立的行为没有被正确实现”，改用 `ahe-hotfix`
- 当前已经明确进入实现阶段，需要继续实现，改用 `ahe-test-driven-dev`
- 当前请求只是阶段不清、profile 不稳或证据链冲突，先回到 `ahe-workflow-router`

## Standalone Contract

当用户直接点名 `ahe-increment` 时，至少确认以下条件：

- 存在明确的变更请求或实质性变化信号
- 当前变化本质上是范围 / 规则 / 验收 / 约束变化，而不是实现缺陷
- 能读取 `AGENTS.md` 中与工件路径、批准规则、状态字段和 re-entry 约定有关的内容
- 当前请求确实是做变更分析与回流，而不是直接改实现

如果前提不满足：

- 当前问题更像实现缺陷修复：回到 `ahe-hotfix`
- 变更仍然含糊、route / stage 判断不清或输入证据冲突：回到 `ahe-workflow-router`
- 已经完成变更分析并需要继续具体产出 / 实现：进入正确的 canonical re-entry 节点

## Chain Contract

当本 skill 作为分支节点被带入时，默认在父会话 / 当前执行上下文中运行，而不是按 reviewer subagent return contract 消费。

默认读取：

- 当前变更请求本身
- `task-progress.md` 中的 `Workflow Profile`、`Current Stage`、`Current Active Task` 与 `Pending Reviews And Gates`
- 当前已批准规格、设计、任务工件
- 当前已存在的 review / gate / 验证证据（如受影响）
- `AGENTS.md` 中与工件路径、批准规则、状态字段和 re-entry 约定有关的内容

本节点完成后应写回：

- 结构化变更包
- 受影响工件与失效项矩阵
- 同步更新项
- canonical `Next Action Or Recommended Skill`

这个 skill 的职责是把变化重新锚定回正确阶段，而不是自己替代 `ahe-specify`、`ahe-design`、`ahe-tasks` 或 `ahe-test-driven-dev`。

## Hard Gates

- 在完成影响分析与失效判断前，不得把当前 increment 直接交给下游实现节点。
- 如果当前输入工件还不足以判定 stage / route，不直接开始 increment 分析。
- `ahe-increment` 不直接替代规格、设计、任务、实现、review 或 gate 节点；它只负责同步变化并选唯一 re-entry 节点。

## Quality Bar

高质量 increment 结果至少应做到：

- 开始前已经固定当前 profile、当前阶段、当前活跃任务和已批准工件基线
- 变化不是口头描述，而是整理成 `New / Modified / Deprecated` 的结构化变更包
- 失效的批准、任务、验证证据和 review 结论被显式列出
- 只更新最小必要工件，不把 increment 写成第二次从零规格化
- 回到主链时写的是唯一 canonical `ahe-*` handoff，而不是自然语言阶段名

## Inputs / Required Artifacts

变更影响分析完成后，默认应将本次分析记录到项目变更记录中；若没有专门路径，可至少同步到：

- `docs/reviews/increment-<topic>.md`
- `task-progress.md`
- 相关规格 / 设计 / 任务工件

如 `AGENTS.md` 为当前项目声明了等价路径，按其中映射路径保存。

如果团队还没有统一的变更影响同步记录格式，可先使用以下模板：

- `skills/ahe-increment/references/change-impact-sync-record-template.md`

开始前，先固定以下状态基线：

- `Workflow Profile`
- `Current Stage`
- `Current Active Task`
- 当前已批准规格 / 设计 / 任务工件
- 当前已存在的验证 / review 证据（如受影响）

如果变更影响了已批准工件，应明确记录：

- 哪些批准状态失效
- 哪些任务计划不再可执行
- 哪些测试设计、验证证据或 review 结论已经失效
- 哪些失效的 review 结论需要由父会话重新派发对应 reviewer subagent
- 当前活跃任务是否仍然有效；若失效，是否必须清空为待重选
- 当前阶段是否需要回退
- `Next Action Or Recommended Skill` 应该改成什么
- 是否出现需要升级 profile 的新信号

## Workflow

### 1. 固定当前基线并判断 branch 类型

在给出结论前，先读取并固定以下证据来源：

- 当前变更请求本身
- `task-progress.md` 中的 `Workflow Profile`、`Current Stage`、`Current Active Task` 与 `Pending Reviews And Gates`
- 当前已批准规格、设计、任务工件
- 当前已存在的 review / gate / 验证证据（如受影响）
- `AGENTS.md` 中与工件路径、批准规则、状态字段和 re-entry 约定有关的内容

先回答：

- 具体变了什么
- 哪些内容仍然有效
- 当前变化更像 increment 还是 hotfix
- 当前是否已经出现 profile 升级信号

### 2. 形成结构化变更包与影响矩阵

把本次变化整理成至少以下结构：

- `New`
- `Modified`
- `Deprecated`

然后评估对以下内容的影响：

- 范围与需求
- 约束或验收标准
- 架构或接口
- 任务顺序与依赖
- 测试与验证策略
- 已完成实现

同时显式写出：

- 受影响工件
- 失效的批准状态
- 失效的任务 / `Current Active Task`
- 失效的测试设计 / 验证证据 / review 结论
- 是否出现 profile 升级信号

如果当前变化仍然太含糊，无法稳定写成 `New / Modified / Deprecated`，不要补脑继续：

- 若 blocker 是“本质上这是实现缺陷修复，而不是需求变更”，下一步交回 `ahe-hotfix`
- 若 blocker 是 route / stage / profile 不清，下一步交回 `ahe-workflow-router`
- 若 profile 与当前阶段仍然清楚，但变化本身需要重新收敛需求表达，下一步交回 `ahe-specify`

### 3. 更新最小必要工件

规则如下：

- 需求变化先落到需求规格
- 只有当需求变化影响“如何实现”时，才继续更新设计
- 只有当设计或范围变化影响执行时，才更新任务计划
- 当行为结论或风险边界变化时，要同步更新验证策略与完成依据
- 如果用户可见结果或项目状态受影响，也要同步更新发布说明和进度记录

若某个 review 结论因本次变更失效，不要只写“需要重审”；应写出对应 canonical review 节点，例如：

- `ahe-spec-review`
- `ahe-design-review`
- `ahe-tasks-review`
- `ahe-test-review`
- `ahe-code-review`
- `ahe-traceability-review`

### 4. 决定唯一 re-entry 节点

下一步规则：

- 变化仍然含糊，需要重新收敛需求：`ahe-specify`
- 当前判断其实是实现缺陷修复：`ahe-hotfix`
- 规格发生实质变化，需要重新产出规格：`ahe-specify`
- 规格已同步完成，且下一步是重新规格评审：`ahe-spec-review`
- 设计变化过大，不适合在 increment 中就地同步：`ahe-design`
- 设计已同步完成，且下一步是重新设计评审：`ahe-design-review`
- 任务计划、活动任务、测试设计种子或验证依据需要重新收敛：`ahe-tasks`
- 工件已保持一致、批准仍然有效、当前活动任务仍可执行，且可以继续实现：`ahe-test-driven-dev`
- 若 route / stage / profile 仍不清，或需要重新决定分支：`ahe-workflow-router`

如果同时有多个失效 review 需要重派发，则：

- 将最早应恢复的 canonical 节点写入 `Next Action Or Recommended Skill`
- 其余节点继续写入 `Pending Reviews And Gates`

### 5. 写回状态与回流说明

至少同步：

1. `Current Stage`
2. `Workflow Profile`（如出现升级信号）
3. `Current Active Task`：仅在原任务仍然有效时保留；若已失效则清空或写 `pending reselection`
4. `Pending Reviews And Gates`
5. 唯一 canonical `Next Action Or Recommended Skill`

若 `Next Action Or Recommended Skill` 指向 review 节点，其含义是父会话或 `ahe-workflow-router` 会按 review dispatch protocol 派发 reviewer subagent，而不是当前 increment 会话直接内联继续评审。

## Output Contract

变更记录正文请严格使用以下结构：

```markdown
## 变更摘要

- 变更摘要
- 当前 workflow profile / 当前阶段
- 当前判断：真实 increment | 更像 hotfix | 仍需进一步规格化

## 变更包

- New
- Modified
- Deprecated

## 影响矩阵

- 受影响工件
- 失效的批准状态
- 失效的任务 / Active Task
- 失效的测试设计 / 验证证据 / review 结论
- 需重新派发的 reviewer / review 节点（如有）
- Profile 升级信号（如有）

## 同步更新项

- 更新项
- 明确不做的内容

## 状态回流

- `Current Stage`
- `Workflow Profile`
- `Current Active Task`（保留原值或写 `pending reselection`）
- `Pending Reviews And Gates`
- `Next Action Or Recommended Skill`: `ahe-specify` | `ahe-hotfix` | `ahe-spec-review` | `ahe-design` | `ahe-design-review` | `ahe-tasks` | `ahe-test-driven-dev` | `ahe-workflow-router`
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| “这只是个小改动，直接改实现就好” | 只要需求、范围或验收变了，就先做影响分析。 |
| “先把代码改了，文档后面再补” | increment 的职责就是先同步变化，再决定回到哪个阶段。 |
| “旧批准应该还能沿用，不用重审” | 实质内容变化后，必须重新判断批准与 review 结论是否仍有效。 |
| “先推进，回头再决定回哪个阶段” | increment 完成时必须选定唯一 canonical re-entry 节点。 |
| “这更像实现修复，但先按 increment 走也没关系” | hotfix / increment 选错分支会直接污染后续工件与路由。 |

## Red Flags

- 把需求变更误当成单纯任务调整
- 把实现缺陷误判成 increment，导致错分支
- 范围实质变化后仍假定旧批准有效
- 不显式标记失效的批准、任务或验证证据
- 没有完成影响分析，就提前回到实现阶段
- `Next Action Or Recommended Skill` 写成自由文本或自然语言阶段名

## Verification

只有在以下两种情况之一成立时，这个 skill 才算完成：

- [ ] 已形成稳定的变更包，受影响工件与失效项已被同步或显式标记，并写回唯一 canonical `Next Action Or Recommended Skill`
- [ ] 已明确记录“当前变化仍不足以稳定结构化或已判断为错分支”的阻塞 / 重分类状态、最小必要影响记录与唯一下一步（`ahe-specify`、`ahe-hotfix` 或 `ahe-workflow-router`），且没有伪造更下游的 re-entry handoff

无论属于哪种完成路径，还应满足：

- [ ] `Current Stage`、`Workflow Profile`、`Current Active Task` 与 `Pending Reviews And Gates` 已按需要同步
- [ ] 当前结论已经足以让父会话恢复到正确主链节点，而不是继续补脑推进
