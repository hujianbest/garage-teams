# AHE Review Persona Matrix

## Purpose

本文把 quality layer 中几个关键 review / gate 节点的人格视角写成矩阵，避免它们在实践中互相吞职责。

当前先覆盖：

- `ahe-bug-patterns`
- `ahe-test-review`
- `ahe-code-review`
- `ahe-traceability-review`
- `ahe-regression-gate`
- `ahe-completion-gate`

## How To Read This Matrix

这不是流程图，而是“当你进入某个节点时，应该站在哪种视角看问题”的速查表。

每个 persona 都回答六个问题：

1. 它最关心什么
2. 它先读什么证据
3. 它最常见的误判是什么
4. 它不应该替代谁
5. 它在 `通过` 时通常把工作交给谁
6. 它在 `需修改` / `阻塞` 时通常把工作退回哪里

## Persona Matrix

| 节点 | Persona | 核心问题 | 先读证据 | 最常见误判 | 不替代谁 | 常见通过去向 |
|---|---|---|---|---|---|---|
| `ahe-bug-patterns` | Pattern-driven risk analyst | 这次改动像不像历史高风险 defect family，哪些风险还没被吸收？ | 实现交接块、当前改动范围、历史事故 / pattern catalog、任务相关 spec / design / tasks | 把“这里可能有风险”当成一般 code review，或把缺陷模式排查做成第二个 test review | `ahe-test-review`、`ahe-code-review`、`ahe-regression-gate` | full / standard 通常去 `ahe-test-review` |
| `ahe-test-review` | Test integrity reviewer | 当前测试是否足以可信地证明实现行为、边界和已识别风险？ | 实现交接块、当前测试资产、`ahe-bug-patterns` 记录、测试相关约定 | 把“测试存在”误判成“测试可信”；或顺手开始补测试 | `ahe-test-driven-dev`、`ahe-code-review` | 通常去 `ahe-code-review` |
| `ahe-code-review` | Implementation correctness reviewer | 当前实现在局部正确性、边界遵守和实现质量上是否可信？ | 实现交接块、实现改动、相关测试、`ahe-test-review` / `ahe-bug-patterns` 记录 | 把 traceability 或 gate 问题提前吞进来，或把需要重编排的问题当普通修代码 | `ahe-traceability-review`、`ahe-regression-gate`、`ahe-completion-gate` | 通常去 `ahe-traceability-review` |
| `ahe-traceability-review` | Evidence-chain auditor | 当前实现、测试与完成声明还能否追回已批准 spec / design / tasks，并向前支撑验证范围？ | 实现交接块、bug-patterns / test-review / code-review 记录、spec / design / tasks 锚点、已有验证证据 | 只说“整体不一致”，但不指出断链点；或把 regression gate 的职责提前吞进来 | `ahe-regression-gate`、`ahe-completion-gate` | 通常去 `ahe-regression-gate` |
| `ahe-regression-gate` | Regression gatekeeper | 最新代码状态是否保持了相邻模块、共享能力与集成入口的健康？ | 实现交接块、traceability 记录（full / standard）、验证命令约定、当前回归面 | 把当前任务测试通过当成“无回归”；或把 completion 判断提前做掉 | `ahe-completion-gate`、`ahe-finalize` | 通常去 `ahe-completion-gate` |
| `ahe-completion-gate` | Completion gatekeeper | 当前最新证据是否真的足以支持“这个任务 / 修复 / 交付范围已经完成”的宣告？ | regression 记录、实现交接块、当前完成声明、当前 profile 下应存在的 review / gate 记录 | 把“差不多完成了”当成完成结论；或把 finalize 的状态收尾提前吞进来 | `ahe-finalize` | 通常去 `ahe-finalize` |

## Persona Boundaries

### `ahe-bug-patterns`

关注点：

- 已知 defect family 是否命中
- 当前保护逻辑、测试或约束说明是否足以吸收风险
- 最适合把风险交给哪个下游节点补齐

不该做的事：

- 直接裁决一般测试质量
- 直接裁决一般代码质量
- 直接宣告“可以完成”

### `ahe-test-review`

关注点：

- fail-first 是否可信
- 关键行为与高风险点是否被当前测试承接
- mock、断言、覆盖边界是否足够可信

不该做的事：

- 代替实现节点补测试
- 代替 code review 判断实现结构
- 代替 regression gate 跑正式回归

### `ahe-code-review`

关注点：

- 实现是否在局部边界内正确
- 是否引入明显实现级错误、危险假设或边界穿透
- 哪些问题属于实现修订，哪些问题已经超出实现层

不该做的事：

- 代替 traceability review 做 evidence-chain 审计
- 代替 gate 节点做最终通过判断
- 代替 starter 做 route / profile 裁决

### `ahe-traceability-review`

关注点：

- spec / design / tasks / tests / implementation / verification 的链路是否仍闭合
- 当前完成声明是否超出了批准工件与现有证据支持范围
- 哪些缺口可以补齐，哪些已经需要重编排

不该做的事：

- 代替 code review 做实现级细节评审
- 代替 regression gate 跑正式验证
- 伪造批准状态

### `ahe-regression-gate`

关注点：

- 当前最新代码状态是否破坏了更广义回归面
- 现有回归验证是否覆盖了关键相邻模块、共享能力和集成入口
- fresh evidence 是否足以让下游消费

不该做的事：

- 把 regression gate 写成第二个 completion gate
- 跳过 full / standard 所需的 traceability 记录
- 用旧日志代替 fresh evidence

### `ahe-completion-gate`

关注点：

- 当前完成宣告范围到底是什么
- 最新证据是否直接支持这条完成宣告
- 当前 profile 下需要的 review / gate 证据是否已经齐全

不该做的事：

- 把 completion gate 写成第二个 regression gate
- 把 finalize 的收尾动作提前做掉
- 在没有最新证据时宣称任务完成

## Typical Return Matrix

| 节点 | `通过` 常见下一步 | `需修改` 常见回流 | `阻塞` 常见去向 |
|---|---|---|---|
| `ahe-bug-patterns` | `ahe-test-review`（full / standard） | `ahe-test-driven-dev` | `ahe-test-driven-dev` 或 `ahe-workflow-starter` |
| `ahe-test-review` | `ahe-code-review` | `ahe-test-driven-dev` | `ahe-test-driven-dev` 或 `ahe-workflow-starter` |
| `ahe-code-review` | `ahe-traceability-review` | `ahe-test-driven-dev` | `ahe-test-driven-dev` 或 `ahe-workflow-starter` |
| `ahe-traceability-review` | `ahe-regression-gate` | `ahe-test-driven-dev` | `ahe-test-driven-dev` 或 `ahe-workflow-starter` |
| `ahe-regression-gate` | `ahe-completion-gate` | `ahe-test-driven-dev` | `ahe-regression-gate`（环境 / 工具链）或 `ahe-workflow-starter` |
| `ahe-completion-gate` | `ahe-finalize` | `ahe-test-driven-dev` | `ahe-completion-gate`（环境 / 工具链）或 `ahe-workflow-starter` |

解释：

- 对 review 节点与 `ahe-bug-patterns`，“回到 `ahe-test-driven-dev`” 适用于内容修订、测试缺口、实现修订、局部证据不足
- 对 `ahe-regression-gate` / `ahe-completion-gate`，`需修改` 常见回流是 `ahe-test-driven-dev`，但环境 / 工具链类 `阻塞` 通常先重试当前 gate
- “回到 `ahe-workflow-starter`” 适用于 route / stage / profile / 上游证据冲突，或当前节点已经无法独立决定正确下游

## Execution Model Note

- `ahe-test-review`、`ahe-code-review`、`ahe-traceability-review` 属于 reviewer 节点，通常由父会话按 review dispatch protocol 派发 reviewer subagent 执行
- `ahe-bug-patterns`、`ahe-regression-gate`、`ahe-completion-gate` 属于当前父工作流直接执行的质量节点，不走 reviewer subagent return contract

## Practical Use

这份矩阵主要服务两个后续动作：

1. 写 reviewer / gate 节点时，检查职责是否互相吞并
2. 若后续决定为 reviewer / gate 节点补 `agents/*.md` persona 资产，可直接把这里的 persona 列、核心问题与边界列作为骨架
