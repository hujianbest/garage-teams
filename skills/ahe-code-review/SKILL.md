---
name: ahe-code-review
description: 评审当前任务的实现代码，判断正确性、局部设计一致性、状态安全性和可维护性是否足以进入 `ahe-traceability-review`，而不是把“测试跑绿”误当成实现已经可靠。适用于 full / standard profile 中 `ahe-test-review` 之后的正式实现质量判断；若阶段不清、证据冲突或当前其实需要继续修实现，先回到 `ahe-workflow-router` 或 `ahe-test-driven-dev`。
---

# AHE 代码评审

评审当前任务的实现，并判断它是否已经足够可靠，可以进入 `ahe-traceability-review`。

## Overview

这个 skill 用来防止“测试通过”掩盖实现层问题。

高质量代码评审不只是判断“代码能跑”，而是判断：

- 实现是否真的满足当前任务目标
- 局部设计、状态处理、错误处理是否依然合理
- 当前实现质量是否足以进入追溯性评审

## When to Use

在这些场景使用：

- `ahe-test-review` 已完成，准备判断实现质量是否足以进入 `ahe-traceability-review`
- 用户明确要求“review 当前实现代码”
- reviewer subagent 被父会话派发来执行代码评审
- 在 `lightweight` profile 中，`ahe-workflow-router` 通常跳过本节点；若手动调用，应视为补充性评审

不要在这些场景使用：

- 当前需要继续修实现、补测试或补交接块，改用 `ahe-test-driven-dev`
- 当前需要检查规格 / 设计 / 任务 / 实现 / 验证链路的一致性，改用 `ahe-traceability-review`
- 当前请求只是阶段不清、profile 不稳或证据链冲突，先回到 `ahe-workflow-router`

## Standalone Contract

当用户直接点名 `ahe-code-review` 时，至少确认以下条件：

- 存在当前任务对应的实现改动
- 存在当前实现交接块或等价证据
- 能读取 `AGENTS.md` 中与代码约定、分层边界、安全 / 性能约束和 review 规则有关的内容
- 当前请求确实是评审，而不是继续改实现

如果前提不满足：

- 缺实现改动、缺实现交接块或本质上需要继续修实现：回到 `ahe-test-driven-dev`
- 缺 route / stage 判断、profile 不清或输入证据冲突：回到 `ahe-workflow-router`

## Chain Contract

当本 skill 作为链路节点被带入时，默认由 reviewer subagent 执行，并读取：

- 当前实现交接块或等价证据
- 当前任务实现改动与相关测试
- `ahe-test-review` 记录
- `ahe-bug-patterns` 记录（full / standard 正式链路）
- `AGENTS.md` 中与代码约定、分层边界、安全 / 性能 / 可观测性规则有关的约定
- 当前任务相关的规格 / 设计 / 任务锚点
- `task-progress.md` 中的 `Current Stage`、`Current Active Task` 与 `Workflow Profile`（如果存在）

本节点完成后应写回：

- review 记录正文
- 结构化 reviewer 返回摘要
- canonical `next_action_or_recommended_skill`

评审记录落盘与结构化摘要由 reviewer 负责；真正推进 `ahe-traceability-review`、回到实现修订或触发重编排，仍由父会话负责。

结构化返回字段定义以 `skills/ahe-workflow-starter/references/reviewer-return-contract.md` 为准。

## Hard Gates

- 在代码评审通过前，不得把当前任务视为已准备好进入 `ahe-traceability-review`。
- 如果当前输入工件还不足以判定 stage / route，不直接开始代码评审。
- reviewer 不负责修代码、补交接块、继续执行 `ahe-traceability-review`，也不代替父会话推进主链。

## Quality Bar

高质量代码评审结果至少应做到：

- 明确实现级正确性和局部设计一致性是否可信
- 明确哪些问题属于实现修订，哪些问题已经超出实现层而需要重编排
- 不把 traceability、regression 或 completion 的职责提前吞进来
- 给 `ahe-traceability-review` 留下可消费的风险与边界信息
- 给出唯一下一步，并与 shared reviewer return contract 保持一致

## Inputs / Required Artifacts

评审完成后，必须将本次结论写入：

- `docs/reviews/code-review-<task>.md`

如 `AGENTS.md` 为当前项目声明了等价路径，按其中映射路径保存。

若项目尚未形成固定 review 记录格式，默认使用：

- `templates/review-record-template.md`

如果使用通用模板中的英文结论字段，请按以下方式映射：

- `通过` -> `pass`
- `需修改` -> `revise`
- `阻塞` -> `blocked`

如果当前任务正在使用 `task-progress.md` 驱动 workflow，且当前 profile 是 full / standard，则父会话在消费本 skill 的评审记录与结构化摘要后，还应同步更新：

- `task-progress.md` 中的代码评审状态
- `task-progress.md` 中的 `Next Action Or Recommended Skill`
- 当前待修实现风险、阻塞原因或重编排说明（如有）

这些状态字段更新由父会话在消费 reviewer 返回后执行；reviewer subagent 不代替父会话改写权威流程状态。

若项目尚未形成固定进度记录格式，默认使用：

- `templates/task-progress-template.md`

## Workflow

### 1. 先建立证据基线

在给出结论前，先读取并固定以下证据来源：

- 当前实现交接块或等价证据
- 当前实现改动与相关测试
- `ahe-test-review` 记录
- `ahe-bug-patterns` 记录（full / standard 正式链路）
- `AGENTS.md` 中与分层边界、安全、性能、可观测性和 coding 规范有关的约定
- 当前任务的规格 / 设计 / 任务锚点
- `task-progress.md` 中的 `Current Stage`、`Current Active Task` 与 `Workflow Profile`（如果存在）

不要只根据 diff 直觉或“测试已经绿了”判断实现可靠。

### 2. 做多维评分与挑战式审查

在形成最终结论前，至少对以下维度做内部评分，评分范围 `0-10`：

- 实现级正确性
- 局部设计一致性
- 状态 / 错误 / 安全处理
- 可读性与可维护性
- 下游追溯性评审准备度

判定辅助规则：

- 任一关键维度低于 `6/10` 时，不得返回 `通过`
- 任一维度低于 `8/10` 时，通常至少应对应一条具体发现项或薄弱点

### 3. 按 checklist 做正式审查

#### 3.1 实现级正确性

- 代码是否真的满足当前任务目标，而不是只碰巧通过当前测试？
- 关键分支、边界条件、失败路径和早退逻辑是否处理合理？
- 是否存在主路径可用、旁支路径 silent failure 的情况？

#### 3.2 局部设计一致性

- 当前实现是否仍符合已批准设计中的模块边界、接口约束和状态假设？
- 是否出现 sneaky scope expansion、临时修补写成长期结构或明显设计漂移？
- 哪些问题应在本节点处理，哪些应留给 `ahe-traceability-review` 继续核对？

#### 3.3 状态、安全与错误路径

- 状态切换、重入、一致性假设或资源释放是否安全？
- 错误处理、默认值、降级逻辑与恢复路径是否合理？
- 若触及 trust boundary、权限或敏感数据，是否至少满足项目最低安全约定？

#### 3.4 可读性与可维护性

- 命名是否清楚？
- 逻辑是否存在不必要复杂度、深嵌套或隐性耦合？
- 是否把过多职责堆在单处代码，导致后续修改脆弱？

#### 3.5 下游追溯性评审准备度

- 当前实现是否足以让 `ahe-traceability-review` 聚焦链路一致性，而不是先怀疑实现本身是否可信？
- 是否还存在会直接污染后续工件一致性判断的实现空洞？

### 4. 形成 verdict、severity 与下一步

severity 统一使用：

- `critical`: 阻塞下游追溯性评审，或实现级风险足以推翻当前交付可信度
- `important`: 应在进入 `ahe-traceability-review` 前修复
- `minor`: 不阻塞，但建议改进

判定规则：

- 只有在实现级正确性可信、局部设计仍然一致、状态 / 错误处理安全、且不存在会误导下游追溯性评审的关键问题时，才返回 `通过`
- 实现总体可用，但仍需修正局部逻辑、边界处理、错误路径、可维护性问题或局部设计漂移时，返回 `需修改`
- 缺少关键输入、无法定位实现范围、缺少 full / standard 所需上游记录，或 route / stage / profile / 上游证据冲突时，返回 `阻塞`

### 5. 写 review 记录并回传父会话

- 若结论为 `通过`，下一步为 `ahe-traceability-review`，`needs_human_confirmation=false`
- 若结论为 `需修改`，下一步为 `ahe-test-driven-dev`
- 若结论为 `阻塞` 且问题属于实现修订类，下一步为 `ahe-test-driven-dev`
- 若结论为 `阻塞` 且问题属于 stage / route / profile / 上游证据冲突，下一步为 `ahe-workflow-router`，并设置 `reroute_via_starter=true`

## Output Contract

review 记录正文请严格使用以下结构：

```markdown
## 结论

通过 | 需修改 | 阻塞

## 上游已消费证据

- Task ID
- 实现交接块 / 等价证据
- `ahe-test-review` 记录
- `ahe-bug-patterns` 记录（如适用）

## 发现项

- [critical|important|minor] 问题

## 代码风险

- 条目

## 给 `ahe-traceability-review` 的提示

- 建议继续核对的链路风险
- 已可信的实现边界

## 下一步

- `通过`：`ahe-traceability-review`
- `需修改`：`ahe-test-driven-dev`
- `阻塞`：`ahe-test-driven-dev` 或 `ahe-workflow-router`

## 记录位置

- `docs/reviews/code-review-<task>.md` 或映射路径
```

若本 skill 运行在 reviewer subagent 中，`next_action_or_recommended_skill` 必须只写一个 canonical 值，不得把多个候选值拼在同一个字符串里。

最小返回示例：

```json
{
  "conclusion": "通过",
  "next_action_or_recommended_skill": "ahe-traceability-review",
  "record_path": "实际写入的 review 记录路径",
  "key_findings": ["关键发现 1", "关键发现 2"],
  "needs_human_confirmation": false,
  "reroute_via_starter": false
}
```

返回规则：

- `通过`：`next_action_or_recommended_skill=ahe-traceability-review`，`needs_human_confirmation=false`
- `需修改`：`next_action_or_recommended_skill=ahe-test-driven-dev`，`needs_human_confirmation=false`
- `阻塞` 且属于实现修订类：`next_action_or_recommended_skill=ahe-test-driven-dev`，`needs_human_confirmation=false`
- `阻塞` 且属于 route / stage / profile / 上游证据冲突：`next_action_or_recommended_skill=ahe-workflow-router`，`needs_human_confirmation=false`，`reroute_via_starter=true`

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| “测试都过了，代码应该也没问题” | 测试通过不能替代实现级正确性判断。 |
| “这个分支很少走到，可以先不管” | 被忽略的旁支路径往往正是实现级缺陷来源。 |
| “traceability review 再看设计漂移也行” | 明显实现漂移应先在 code review 暴露，不该甩给下游兜底。 |
| “先过再说，反正后面还有 gate” | gate 不是替代实现修订的垃圾桶。 |
| “我顺手把代码改了再回结论更快” | reviewer 的职责是判断与落盘，不是直接修实现。 |

## Red Flags

- 不读实现交接块就直接评价代码
- 因为测试是绿的就直接通过实现
- 忽略明显的状态、安全或错误路径问题
- 在 code review 里顺手开始 traceability 或 regression 执行
- 返回多个候选下一步，而不是唯一 canonical handoff

## Verification

只有在以下条件全部满足时，这个 skill 才算完成：

- [ ] 评审记录已经落盘
- [ ] 给出明确结论、发现项、代码风险和唯一下一步
- [ ] 结构化 reviewer 返回摘要已使用 `next_action_or_recommended_skill`
- [ ] 若本 skill 由 reviewer subagent 执行，已完成对父会话的结构化结果回传
- [ ] 当前结论已经足以让父会话判断是进入 `ahe-traceability-review`、回到 `ahe-test-driven-dev`，还是回到 `ahe-workflow-router`
