---
name: ahe-regression-gate
description: 执行正式回归门禁。适用于已有当前任务的实现交接块、需要用 fresh regression evidence 确认相邻模块、共享能力、构建或集成入口未被破坏，并判断是否可以安全进入 `ahe-completion-gate` 的场景；若阶段不清、上游证据缺失或 profile 要求冲突，先回到 `ahe-workflow-starter`。
---

# AHE 回归门禁

在任务可被视为完成之前，执行最小必要但足够可信的回归验证。

## Overview

这个 skill 的职责是防止“局部修好了，但周边悄悄坏掉”的情况。

它负责：

- 定义当前最小必要的回归面
- 基于当前最新代码状态收集 fresh regression evidence
- 给出能否安全进入 `ahe-completion-gate` 的正式门禁结论

它不替代：

- `ahe-traceability-review` 的 evidence-chain 检查
- `ahe-completion-gate` 的最终完成宣告判断

## When to Use

在这些场景使用：

- full / standard profile 中，通常位于 `ahe-traceability-review` 之后、`ahe-completion-gate` 之前
- lightweight profile 中，通常位于 `ahe-test-driven-dev` 之后、`ahe-completion-gate` 之前
- 当前任务已完成主要实现与前置评审，需要确认没有破坏相邻模块、共享能力或集成点
- 用户明确要求“跑正式回归门禁”或“确认现在能不能进 completion gate”

不要在这些场景使用：

- 当前还没有 `ahe-test-driven-dev` 的实现交接块或等价证据
- 当前需要的是追溯性审计，改用 `ahe-traceability-review`
- 当前需要的是最终完成宣告，改用 `ahe-completion-gate`
- 当前阶段不清、profile 冲突或上游证据缺失，先回到 `ahe-workflow-starter`

## Standalone Contract

当用户直接点名 `ahe-regression-gate` 时，至少确认以下条件：

- 当前任务 / scope 明确
- 存在 `ahe-test-driven-dev` 的实现交接块或等价证据
- 能读取到可执行的回归验证入口
- 若当前 profile 是 `full` / `standard`，还应能读取 `ahe-traceability-review` 记录

若这些前提不满足，不要硬跑门禁：

- 缺实现交接块或当前任务上下文：返回 `阻塞`
- 缺 profile / route 判断：先回到 `ahe-workflow-starter`
- 缺必要验证入口或环境坏损：返回 `阻塞`

## Chain Contract

作为主链节点被串联调用时，默认读取：

- `AGENTS.md` 中声明的验证命令、验证分层与环境要求
- 当前改动范围与目标行为
- `ahe-test-driven-dev` 的实现交接块或等价证据
- `ahe-traceability-review` 记录（full / standard）
- `task-progress.md` 当前状态与 `Pending Reviews And Gates`

本节点完成后应写回：

- 一份 regression gate verification record
- canonical `Next Action Or Recommended Skill`
- 当前阻塞原因、失败项或覆盖缺口（如有）

当前 regression gate 仍由父工作流在当前会话执行，不按 review dispatch protocol 派发 reviewer subagent；它消费 review 记录，但自身不是 review 节点。

## Hard Gates

- 没有 `ahe-test-driven-dev` 的实现交接块或等价证据，不得声称当前 regression gate 输入充分。
- 没有 fresh evidence，不得返回 `通过`。
- full / standard 缺少 `ahe-traceability-review` 记录时，不得直接跳过，应按 `阻塞` 处理。
- 不得把 regression gate 写成第二个 completion gate。

## Quality Bar

高质量的 `ahe-regression-gate` 结果，至少应满足：

- 先消费上游 handoff / review 记录，再定义当前回归面
- 不只说“跑过了”，还要说清跑了什么、覆盖了什么、还有什么没覆盖
- fresh evidence 能证明这些结果属于当前最新代码状态，而不是旧日志
- 输出能直接被 `ahe-completion-gate` 和 `ahe-finalize` 消费

## Inputs / Required Artifacts

开始门禁前，至少固定：

- 当前任务 ID
- 当前 workflow profile
- `AGENTS.md` 中声明的验证入口、顺序、环境前置条件与特殊例外（如有）
- 上游实现交接块中的关键风险与 proving command 摘要
- full / standard 下的 `ahe-traceability-review` 结论与主要缺口
- 当前要覆盖的回归面：相邻模块、共享能力、构建 / 类型 / 集成入口
- 当前状态工件中的 `Pending Reviews And Gates` / `Next Action`

默认回归记录保存到：

- `docs/verification/regression-<task>.md`

若 `AGENTS.md` 为当前项目声明了映射路径，优先使用映射路径。

若项目尚未形成固定 verification 记录格式，默认使用：

- `templates/verification-record-template.md`

若项目尚未形成固定进度记录格式，默认使用：

- `templates/task-progress-template.md`

Profile-aware 回归面：

| Profile | 默认至少覆盖的回归面 |
|---|---|
| `full` | `ahe-traceability-review` 指出的相邻模块 / 共享能力 / 构建 / 类型 / 集成入口，以及项目约定要求的关键验证 |
| `standard` | 与当前改动直接相关的相邻模块 / 共享能力 / 构建 / 类型 / 集成入口 |
| `lightweight` | 最小必要的 build / test / 验证入口，但不能缩成“只跑新测试” |

如果 `AGENTS.md` 为当前项目定义了更严格的回归门槛，优先遵守项目规则。

## Workflow

### 1. 对齐上游结论与 profile

先确认：

- 当前 profile 是什么
- 当前要验证的回归面是否与上游 handoff / traceability 记录一致
- full / standard 下是否存在 `ahe-traceability-review` 记录
- 当前状态工件与上游结论是否互相冲突

若 route、profile、证据链或验证入口定义本身无法确定，先按 `阻塞` 处理并要求经 `ahe-workflow-starter` 重编排。

### 2. 明确当前回归面

确定本次改动之后，哪些内容必须继续保持成立：

- 相关测试
- 受影响模块
- 构建或类型检查状态
- 本地集成点
- 上游 review 明确指出的高风险区域

### 3. 运行最新检查

立即运行相关验证命令。

不要依赖更早之前的结果，除非那些结果正是针对当前这份最新任务状态，在本轮流程中执行得到的。

### 4. 读取实际结果

检查：

- 退出状态
- 失败数量
- 本次验证范围是否覆盖了回归面
- 这些结果是否明确属于当前最新代码状态

### 5. 形成 fresh evidence bundle

至少记录：

- 命令
- 退出码
- 结果摘要
- 覆盖的回归面
- 新鲜度锚点：为什么这次运行属于当前最新代码状态
- 当前未覆盖的剩余区域（如果有）

### 6. 决定门禁结果并写回状态

- 如果回归面健康，下一步进入 `ahe-completion-gate`
- 如果回归失败或覆盖范围不足，下一步回到 `ahe-test-driven-dev`
- 如果环境 / 工具链损坏，下一步重试 `ahe-regression-gate`
- 如果阻塞暴露的是上游编排 / profile / 证据 / 验证入口定义问题，下一步经 `ahe-workflow-starter` 重编排

同步更新验证记录与 `task-progress.md` 中的相关回归状态、阻塞原因和 canonical 下一步。

## Output Contract

请严格使用以下结构：

```markdown
## 结论

通过 | 需修改 | 阻塞

## 已消费的上游结论

- Task ID
- 实现交接块 / 等价证据
- `ahe-traceability-review` 记录（如适用）

## 回归面

- 条目

## 证据

- 命令 | 退出码 | 结果摘要 | 覆盖范围 | 新鲜度锚点

## 覆盖缺口 / 剩余风险

- 条目

## 明确不在本轮范围内

- 条目 | `N/A`

## 回归风险

- 风险项

## 下一步

- `通过`：`ahe-completion-gate`
- `需修改`：`ahe-test-driven-dev`
- `阻塞`：
  - 环境 / 工具链类：`ahe-regression-gate`
  - 上游编排 / profile / 证据 / 验证入口定义类：`ahe-workflow-starter`

## 记录位置

- `docs/verification/regression-<task>.md` 或映射路径
```

判定规则：

- 只有在相关回归检查为最新执行，且结果支持继续推进时，才返回 `通过`
- 如果检查失败，或覆盖范围不足，则返回 `需修改`
- 如果由于环境或验证配置损坏，暂时无法运行正确的回归命令，则返回 `阻塞`
- full / standard 缺少必要的 traceability 记录、验证入口或状态冲突时，也返回 `阻塞`

应在 `task-progress.md` 或等价状态工件中显式写入 canonical `Next Action Or Recommended Skill`：`ahe-completion-gate`、`ahe-test-driven-dev`、`ahe-regression-gate` 或 `ahe-workflow-starter`。

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| “新测试都绿了，就说明没有回归” | 当前任务级证明不等于更广义回归健康。 |
| “先跑一条最方便的命令看看就够了” | 回归面必须覆盖受影响模块、共享能力、构建或集成入口。 |
| “traceability 记录这次没有也没关系” | full / standard 缺少该记录时应按阻塞处理。 |
| “旧日志也能说明这次没问题” | regression gate 只接受 fresh evidence。 |
| “环境坏了先记成需修改，反正后面再试” | 环境 / 工具链问题应明确分类为 `阻塞`。 |
| “completion gate 还会再看一次，这里可以粗略一点” | regression gate 是正式 gate artifact，completion / finalize 会直接消费它。 |

## Red Flags

- 想当然地认为周边行为仍然正常
- 使用过期测试输出
- 只跑新测试就声称已经覆盖回归
- 因为单测通过就忽略构建或类型检查失败
- 不读取上游 traceability / handoff 记录，就直接跑命令
- 把 regression gate 做成第二个 completion gate

## Verification

门禁结论必须写入仓库中的验证记录路径。可以在对话中摘要结论，但对话不能替代验证工件。

只有在以下条件全部满足时，这个 skill 才算完成：

- [ ] regression verification record 已落盘
- [ ] 记录中写清已消费的上游结论、回归面、fresh evidence、覆盖缺口和回归风险
- [ ] 基于最新证据给出唯一门禁结论
- [ ] `task-progress.md` 或等价状态工件已写回 canonical `Next Action Or Recommended Skill`
- [ ] 下一步明确为 `ahe-completion-gate`、`ahe-test-driven-dev`、`ahe-regression-gate` 或 `ahe-workflow-starter`
