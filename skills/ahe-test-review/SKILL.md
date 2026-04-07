---
name: ahe-test-review
description: 评审当前任务的测试资产，判断 fail-first、行为覆盖和风险覆盖是否足以支撑进入 `ahe-code-review`，而不是让“有几条绿测试”伪装成可信验证。适用于 full / standard profile 中 `ahe-bug-patterns` 之后的正式测试质量判断；若阶段不清、证据冲突或当前其实需要补测试，先回到 `ahe-workflow-router` 或 `ahe-test-driven-dev`。
---

# AHE 测试评审

评审当前任务的测试，并判断它是否已经足够可信，可以进入 `ahe-code-review`。

## Overview

这个 skill 用来防止浅覆盖测试混进正式质量链。

高质量测试评审不只是判断“测试有没有写”，而是判断：

- fail-first 是否真的成立
- 测试是否覆盖了当前任务的关键行为与风险
- 当前测试质量是否足以支撑后续实现级评审

## When to Use

在这些场景使用：

- `ahe-bug-patterns` 已完成，准备判断测试质量是否足以进入 `ahe-code-review`
- 用户明确要求“review 当前测试是否够用”
- reviewer subagent 被父会话派发来执行测试评审
- 在 `lightweight` profile 中，`ahe-workflow-router` 通常跳过本节点；若手动调用，应视为补充性评审

不要在这些场景使用：

- 当前需要补测试、修测试或继续实现，改用 `ahe-test-driven-dev`
- 当前需要判断代码实现质量，改用 `ahe-code-review`
- 当前请求只是阶段不清、profile 不稳或证据链冲突，先回到 `ahe-workflow-router`

## Standalone Contract

当用户直接点名 `ahe-test-review` 时，至少确认以下条件：

- 存在当前任务对应的测试资产
- 存在当前实现范围或实现交接块
- 能读取 `AGENTS.md` 中与测试、fail-first、mock 边界和验证约定有关的规则
- 当前请求确实是评审，而不是继续补测试

如果前提不满足：

- 缺测试资产、缺实现交接块或本质上需要补测试：回到 `ahe-test-driven-dev`
- 缺 route / stage 判断、profile 不清或输入证据冲突：回到 `ahe-workflow-router`

## Chain Contract

当本 skill 作为链路节点被带入时，默认由 reviewer subagent 执行，并读取：

- 当前实现交接块或等价证据
- 当前任务新增 / 修改的测试
- `ahe-bug-patterns` 记录（full / standard 正式链路）
- `AGENTS.md` 中与测试、mock、覆盖要求和 fail-first 例外有关的约定
- 当前任务相关的规格 / 设计 / 任务锚点
- `task-progress.md` 中的 `Current Stage`、`Current Active Task` 与 `Workflow Profile`（如果存在）

本节点完成后应写回：

- review 记录正文
- 结构化 reviewer 返回摘要
- canonical `next_action_or_recommended_skill`

评审记录落盘与结构化摘要由 reviewer 负责；真正推进 `ahe-code-review`、回到实现修订或触发重编排，仍由父会话负责。

结构化返回字段定义以 `skills/ahe-workflow-starter/references/reviewer-return-contract.md` 为准。

## Hard Gates

- 在测试评审通过前，不得把当前任务视为已准备好进入 `ahe-code-review`。
- 如果当前输入工件还不足以判定 stage / route，不直接开始测试评审。
- reviewer 不负责补测试、改测试、继续实现或代替父会话执行下一个评审节点。

## Quality Bar

高质量测试评审结果至少应做到：

- 明确 fail-first 是否真实、可信、与当前行为直接相关
- 明确测试覆盖了哪些关键行为、风险点与边界
- 区分“测试还需要补强”与“当前根本无法判定测试质量”
- 给 `ahe-code-review` 留下清楚的可信边界与风险提示
- 给出唯一下一步，并与 shared reviewer return contract 保持一致

## Inputs / Required Artifacts

评审完成后，必须将本次结论写入：

- `docs/reviews/test-review-<task>.md`

如 `AGENTS.md` 为当前项目声明了等价路径，按其中映射路径保存。

若项目尚未形成固定 review 记录格式，默认使用：

- `templates/review-record-template.md`

如果使用通用模板中的英文结论字段，请按以下方式映射：

- `通过` -> `pass`
- `需修改` -> `revise`
- `阻塞` -> `blocked`

如果当前任务正在使用 `task-progress.md` 驱动 workflow，且当前 profile 是 full / standard，则父会话在消费本 skill 的评审记录与结构化摘要后，还应同步更新：

- `task-progress.md` 中的测试评审状态
- `task-progress.md` 中的 `Next Action Or Recommended Skill`
- 当前待补测试缺口、阻塞原因或重编排说明（如有）

这些状态字段更新由父会话在消费 reviewer 返回后执行；reviewer subagent 不代替父会话改写权威流程状态。

若项目尚未形成固定进度记录格式，默认使用：

- `templates/task-progress-template.md`

## Workflow

### 1. 先建立证据基线

在给出结论前，先读取并固定以下证据来源：

- 当前实现交接块或等价证据
- 当前测试资产
- `ahe-bug-patterns` 记录（full / standard 正式链路）
- `AGENTS.md` 中与测试、mock、fail-first 和验证有关的约定
- 当前任务的规格 / 设计 / 任务锚点
- `task-progress.md` 中的 `Current Stage`、`Current Active Task` 与 `Workflow Profile`（如果存在）

不要只根据“测试跑绿了”或聊天中的口头说明判断测试足够好。

### 2. 做多维评分与挑战式审查

在形成最终结论前，至少对以下维度做内部评分，评分范围 `0-10`：

- fail-first 有效性
- 行为覆盖与验收映射
- 风险覆盖与边界覆盖
- 测试设计质量
- 下游代码评审准备度

判定辅助规则：

- 任一关键维度低于 `6/10` 时，不得返回 `通过`
- 任一维度低于 `8/10` 时，通常至少应对应一条具体发现项或薄弱点

### 3. 按 checklist 做正式审查

#### 3.1 fail-first 与 RED / GREEN

- RED 是否真实发生过，且对应当前缺失行为？
- RED 是否避免了环境噪音、无关旧失败或伪失败？
- GREEN 是否来自当前代码状态的新鲜通过证据？
- 若项目允许 fail-first 例外，当前例外是否被 `AGENTS.md` 或上游约定明确授权？

#### 3.2 行为价值与验收映射

- 测试验证的是行为，而不是实现细节吗？
- 关键验收点是否能回指到至少一条可信测试？
- 是否存在“看起来覆盖了，但只验证最顺路径”的情况？

#### 3.3 风险覆盖与边界

- `ahe-bug-patterns` 命中的关键风险是否被测试承接？
- 边界、负路径、异常路径或兼容路径是否有足够验证？
- 是否存在高风险变更几乎没有对应测试？

#### 3.4 测试设计质量

- 断言是否足够强，不只是“代码执行到了这里”？
- mock / stub 使用是否合理，没有把真实风险隔离掉？
- 是否存在 flake、过度耦合、命名模糊或维护成本异常高的问题？

#### 3.5 下游代码评审准备度

- 当前测试是否足以让 `ahe-code-review` 聚焦实现风险，而不是先质疑测试真实性？
- 是否还存在会直接污染后续实现级判断的测试空洞？

### 4. 形成 verdict、severity 与下一步

severity 统一使用：

- `critical`: 阻塞下游代码评审，或测试证据明显失真
- `important`: 应在进入 `ahe-code-review` 前修复
- `minor`: 不阻塞，但建议改进

判定规则：

- 只有在 fail-first 可信、关键行为与风险被可信测试覆盖、且不存在会误导下游实现评审的测试空洞时，才返回 `通过`
- 测试总体可用，但仍需补关键边界、加强断言、减少脆弱 mock 或修正局部测试设计时，返回 `需修改`
- 缺少关键测试上下文、缺少可信 RED / GREEN 证据、缺少 full / standard 所需的上游风险记录，或 route / stage / profile 证据冲突时，返回 `阻塞`

### 5. 写 review 记录并回传父会话

- 若结论为 `通过`，下一步为 `ahe-code-review`，`needs_human_confirmation=false`
- 若结论为 `需修改`，下一步为 `ahe-test-driven-dev`
- 若结论为 `阻塞` 且问题属于测试内容、测试证据或实现修订类，下一步为 `ahe-test-driven-dev`
- 若结论为 `阻塞` 且问题属于 stage / route / profile / 上游证据冲突，下一步为 `ahe-workflow-router`，并设置 `reroute_via_starter=true`

## Output Contract

review 记录正文请严格使用以下结构：

```markdown
## 结论

通过 | 需修改 | 阻塞

## 上游已消费证据

- Task ID
- 实现交接块 / 等价证据
- `ahe-bug-patterns` 记录（如适用）

## 发现项

- [critical|important|minor] 问题

## 测试 ↔ 行为映射

- 行为 / 验收点
- 对应测试

## 测试质量缺口

- 条目

## 给 `ahe-code-review` 的提示

- 已可信的测试结论
- 仍需重点怀疑的实现风险

## 下一步

- `通过`：`ahe-code-review`
- `需修改`：`ahe-test-driven-dev`
- `阻塞`：`ahe-test-driven-dev` 或 `ahe-workflow-router`

## 记录位置

- `docs/reviews/test-review-<task>.md` 或映射路径
```

若本 skill 运行在 reviewer subagent 中，`next_action_or_recommended_skill` 必须只写一个 canonical 值，不得把多个候选值拼在同一个字符串里。

最小返回示例：

```json
{
  "conclusion": "通过",
  "next_action_or_recommended_skill": "ahe-code-review",
  "record_path": "实际写入的 review 记录路径",
  "key_findings": ["关键发现 1", "关键发现 2"],
  "needs_human_confirmation": false,
  "reroute_via_starter": false
}
```

返回规则：

- `通过`：`next_action_or_recommended_skill=ahe-code-review`，`needs_human_confirmation=false`
- `需修改`：`next_action_or_recommended_skill=ahe-test-driven-dev`，`needs_human_confirmation=false`
- `阻塞` 且属于测试 / 实现修订类：`next_action_or_recommended_skill=ahe-test-driven-dev`，`needs_human_confirmation=false`
- `阻塞` 且属于 route / stage / profile / 上游证据冲突：`next_action_or_recommended_skill=ahe-workflow-router`，`needs_human_confirmation=false`，`reroute_via_starter=true`

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| “测试都绿了，应该可以过” | 绿不等于 fail-first 可信，也不等于行为覆盖充分。 |
| “这些边界测试以后补也行” | 缺关键边界会直接污染 `ahe-code-review` 对实现可信度的判断。 |
| “bug-patterns 提到的风险先不测也问题不大” | 已识别的高风险点不被测试承接，就不该视为已收敛。 |
| “mock 多一点比较省事” | 过强隔离会让测试失去真实验证价值。 |
| “反正下游还会继续 review” | 下游 review 不是替代测试评审；它们消费的是你给出的可信边界。 |

## Red Flags

- 没读取实现交接块就直接评价测试
- 把“有测试文件”误判为“测试足够好”
- 忽略无效 RED / GREEN 证据
- 忽略 `ahe-bug-patterns` 已命中的高风险点
- 在测试评审里顺手开始改测试或补实现
- 返回多个候选下一步，而不是唯一 canonical handoff

## Verification

只有在以下条件全部满足时，这个 skill 才算完成：

- [ ] 评审记录已经落盘
- [ ] 给出明确结论、发现项、测试质量缺口和唯一下一步
- [ ] 结构化 reviewer 返回摘要已使用 `next_action_or_recommended_skill`
- [ ] 若本 skill 由 reviewer subagent 执行，已完成对父会话的结构化结果回传
- [ ] 当前结论已经足以让父会话判断是进入 `ahe-code-review`、回到 `ahe-test-driven-dev`，还是回到 `ahe-workflow-router`
