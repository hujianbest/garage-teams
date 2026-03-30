---
name: mdc-implement
description: 以受控方式执行已批准的 MDC 任务计划并完成实现。适用于任务计划已通过评审，且实现阶段应按任务逐项推进，并通过 `mdc-test-driven-dev` 执行 TDD，再把结果交给后续质量能力与门禁处理的场景。
---

# MDC 实现

按已批准任务计划，一次实现一个任务。

## 硬性门禁

任务计划未通过评审前，不得开始实现。

当前任务在实现、评审、验证完成之前，不得切换到下一个任务。

在进入 `mdc-test-driven-dev` 之前，必须先让真人确认当前任务的测试用例设计满足预期。

## 核心规则

一次只允许有一个活跃任务。

实现阶段的活跃任务不应依赖聊天记忆推断。优先从 `task-progress.md` 读取：

- `Current Stage`
- `Current Active Task`
- `Pending Reviews And Gates`
- `Next Action Or Recommended Skill`

如果 `task-progress.md` 与任务计划冲突，按更保守的上游工件处理，不直接继续实现。

## Artifact Model 与 starter 交接

本 skill 默认在一个明确的 `change workspace` 内推进实现。

进入本 skill 时，先区分：

- `baseline artifacts`：当前仍有效的已批准规格、已批准设计和稳定团队规则
- `change workspace`：当前任务计划、代码改动、测试、review、verification、`task-progress.md` 与发布记录
- `archive`：已完成 change 的历史实现与验证，只用于恢复历史背景

旧的 archive 记录不能代替当前任务的新鲜验证证据，也不能代替当前 workspace 的批准依据。

如果当前调用来自 `mdc-workflow-starter`，应把 starter 的内部 payload 视为最小执行契约：

- `currentWorkspace`：当前实现所属 workspace
- `requiredReads`：本轮必须读取的任务、规格、设计、评审或验证证据
- `expectedWrites`：代码、测试、`task-progress.md`、后续 review / verification 记录的目标写入
- `blockingReasons`：若存在冲突或前置缺失，先解决阻塞，再继续实现
- `currentProfile`：决定后续必须衔接的质量链密度

## TDD 规则

TDD 执行统一委托给现有的 `mdc-test-driven-dev` skill。

除非当前任务明确属于非代码配置类工作且该例外已被记录，否则不得绕过 `mdc-test-driven-dev`，也不得在没有失败测试的前提下编写生产代码。

调用方式应优先使用系列级 `mdc-test-driven-dev` 入口，再由该入口按语言或项目类型路由到具体 TDD 实现。

在调用 `mdc-test-driven-dev` 之前，必须先给出测试用例设计，并与真人对话确认；如果真人提出意见，应继续修改测试设计，直到真人明确确认。

## `AGENTS.md` 测试约定

进入实现阶段后，先检查 `AGENTS.md` 是否为当前项目声明了 testing 规范。

优先读取：

- 测试命令与执行顺序
- 单测 / 集成测 / 端到端测试的分层要求
- mock、fixture、外部依赖替身的边界
- 覆盖率门槛或必须覆盖的风险类型
- 哪些非代码或纯配置变更可例外豁免 TDD

若 `AGENTS.md` 没有声明这些约定，再回落到 `mdc-test-driven-dev` 和项目现有默认测试方式。

## 红旗信号

出现以下想法时，先停下。这通常说明你正在为跳步找理由：

| 想法 | 实际要求 |
|---|---|
| “这个任务很小，直接改掉更快” | 任务再小，也必须先通过 `mdc-test-driven-dev`。 |
| “测试用例大概可以，先跑起来再说” | 先让真人确认测试用例设计，再进入 TDD。 |
| “测试后面再补也行” | 先有失败测试，再写生产代码。 |
| “我先顺手把相邻任务一起做了” | 一次只允许一个活跃任务。 |
| “现在已经差不多了，可以先说完成” | 完成要等评审、回归和完成门禁都走完。 |
| “这些 review 太重了，先跳过一个” | 在 workflow 中，后续质量能力与门禁有默认顺序，不能擅自省略。 |
| “旧的绿测结果也能证明这次改动没问题” | 必须有当前任务对应的新鲜证据。 |

## 工作流

### 1. 对齐上下文

阅读：

- `AGENTS.md` 中与当前任务相关的 testing / coding 约定（如果存在）
- 已批准任务计划
- 当前 `change workspace` 中的进度或状态记录
- 当前任务对应的规格和设计片段
- 当前仍有效的 `baseline artifacts`
- 仅在需要恢复历史实现背景时读取 `archive`

只选定一个活跃任务。

默认顺序：

1. 先读 `task-progress.md` 中的 `Current Active Task`
2. 再用任务计划校验该任务是否真实存在且仍然有效
3. 若两者冲突，暂停实现并先修正状态记录或回到上游阶段

如果当前是因为后续质量能力（`mdc-bug-patterns`、`mdc-test-review`、`mdc-code-review`、`mdc-traceability-review`）或门禁（`mdc-regression-gate`、`mdc-completion-gate`）返回"需修改"或"阻塞"而重新进入本 skill：

- 先读取评审或门禁结论中的发现项、风险和修订建议
- 定位需要修正的具体代码或测试区域
- 优先修复 `critical` 与 `important` 级别的问题
- 修复完成后，应从触发回流的那个质量能力或门禁重新开始后续检查，而不是从质量链起点重走
- 不要因为回流修订就重新执行整个 TDD 流程，除非修订涉及行为变更需要新增或修改测试

### 2. 设计测试用例并与真人确认

在进入 TDD 之前，先输出当前任务的测试设计，至少说明：

- 要验证哪些行为
- 关键正向/反向场景
- 边界条件
- 预期输入与输出
- 哪些测试应先失败

测试设计应优先反映 `AGENTS.md` 中声明的测试分层、命令入口和覆盖要求。

然后：

1. 把测试用例设计展示给真人
2. 邀请真人确认“这些测试是否满足当前预期”
3. 如果真人提出意见，继续对话并修改测试设计
4. 只有在真人明确确认后，才能进入下一步

### 3. 使用 `mdc-test-driven-dev` 执行 TDD

对于当前任务：

1. 调用系列级 `mdc-test-driven-dev`
2. 结合 `AGENTS.md` 中的测试约定，按 Red-Green-Refactor 完成当前任务的最小闭环
3. 确认失败测试、最小实现、通过验证和必要重构都有对应证据

### 4. 准备评审输入

在声称任务完成之前：

- 明确本次改了什么
- 明确哪些测试在证明它
- 明确还存在哪些风险区域
- 同步更新 `task-progress.md` 中当前任务的进展与待处理的质量检查 / gate

### 5. 交给后续质量能力与门禁

当前任务实现完成后，在 workflow 中默认按以下顺序交给后续质量能力与门禁：

1. 使用 `mdc-bug-patterns`
2. 然后使用 `mdc-test-review`
3. 然后使用 `mdc-code-review`
4. 然后使用 `mdc-traceability-review`
5. 然后使用 `mdc-regression-gate`
6. 然后使用 `mdc-completion-gate`

这是 workflow 的默认推荐顺序，用于把实现结果交给后续检查和完成判断。

具体应进入哪些后续节点，以当前 `Workflow Profile` 和 starter 迁移表为准：

- `full` / `standard`：按完整质量链推进
- `lightweight`：默认进入 `mdc-regression-gate` -> `mdc-completion-gate`

不要把 full profile 的完整链，机械套到当前 profile 不包含的节点上。

## workflow 默认顺序

```text
实现 -> 测试用例设计 -> 真人确认测试设计 -> `mdc-test-driven-dev` -> 缺陷模式排查 -> 测试评审 -> 代码评审 -> 可追溯性评审 -> 回归门禁 -> 完成门禁
```

在输出或交接中，请补充结构化信息，至少包含：

- `currentWorkspace`
- `nextNode`
- `requiredReads`
- `expectedWrites`
- `blockingReasons`
- `writesScope: change workspace`

不要因为任务看起来简单就跳过后续质量检查或门禁。

## 反模式

- 并行处理多个任务
- 未经真人确认测试用例设计，就直接进入 `mdc-test-driven-dev`
- 不通过 `mdc-test-driven-dev` 就直接开始实现
- 先写实现，再补失败测试
- 把旧的绿测结果当成当前证据
- 在完成门禁前就说“做完了”
- 因为当前任务变麻烦就切换任务
- 因为赶进度而跳过缺陷模式排查、评审或门禁
- 不读取 `task-progress.md` 就靠会话印象决定当前活跃任务

## 完成条件

只有在测试设计已经过真人确认，且当前任务已经完成实现并被清晰移交给后续质量能力 / 门禁，或明确报告了阻塞问题后，这个 skill 才算完成。
