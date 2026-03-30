---
name: mdc-tasks-review
description: 评审 MDC 任务计划，检查粒度、顺序、依赖正确性、可验证性以及是否足以指导实现。
---

# MDC 任务评审

评审任务计划，并判断是否可以开始实现。

在完整 MDC workflow 中，它通常用于实现前的任务质量判断。

## 硬性门禁

在任务计划通过评审，或用户明确接受已知缺口之前，不得进入 `mdc-implement`。

## 目的

这个 skill 是执行准备度门禁。

如果任务计划过于粗糙，实现阶段就容易漂移。

## 记录要求

如果当前项目需要留痕，评审完成后，默认将本次结论写入：

- `docs/reviews/tasks-review-<topic>.md`

如 `AGENTS.md` 为当前项目声明了等价路径，按其中映射路径保存。

若项目尚未形成固定 review 记录格式，默认使用：

- `skills/mdc-workflow/templates/review-record-template.md`

如果当前任务正在使用 `task-progress.md` 驱动 workflow，且结论为 `通过`，还应同步更新：

- 任务计划中的状态字段或批准记录
- `task-progress.md` 的 Current Stage
- `task-progress.md` 的 Current Active Task
- `task-progress.md` 中记录的推荐下一步动作或 skill

若项目尚未形成固定进度记录格式，默认使用：

- `skills/mdc-workflow/templates/task-progress-template.md`

## 与入口 skill 的结构化衔接

本 skill 的结论会被 `mdc-workflow-starter` 用来决定是进入 `mdc-implement`，还是退回 `mdc-tasks`。

因此除人类可读的评审结论外，还应显式交接：

- `nextNode`：`mdc-implement` 或 `mdc-tasks`
- `blockingReasons`：为什么当前不能安全进入实现
- `requiredReads`：本轮评审依赖的任务、规格、设计与状态证据
- `expectedWrites`：tasks review 记录、任务状态、`task-progress.md`
- `writesScope`：默认是当前 `change workspace`

## 检查清单

### 1. 粒度

- 任务是否足够小，可以直接执行和验证？
- 是否仍存在一个任务里混入多个行为的情况？

### 2. 顺序

- 任务顺序是否合理？
- 前置条件是否被正确遵守？

### 3. 验证准备度

- 每个关键任务是否都有清晰验证方法？
- 完成条件是否明确？

### 4. 可追溯性

- 主要任务能否追溯回设计和规格？
- 风险区域是否体现在计划中？

## 输出格式

请严格使用以下结构：

```markdown
## 结论

通过 | 需修改 | 阻塞

## 发现项

- [严重级别] 问题

## 计划薄弱点

- 条目

## 下一步

`进入实现` | `回到任务修订`

## 阻塞原因

- 无 | 阻塞原因

## 记录位置

- `docs/reviews/tasks-review-<topic>.md` 或映射路径

## 结构化交接

- currentWorkspace: <当前 workspace>
- nextNode: `mdc-implement` | `mdc-tasks`
- blockingReasons: 无 | <阻塞原因>
- requiredReads: <本轮实际读取的最少证据>
- expectedWrites: <tasks review 路径>, <任务状态更新>, `task-progress.md`
- writesScope: `change workspace`
```

## 判定规则

只有当计划满足以下条件时，才返回 `通过`：

- 顺序连贯
- 粒度可执行
- 完成条件明确
- 可以支撑实现而无需大量猜测

以下情况返回 `需修改`：

- 计划整体可用，但部分任务过大或描述不足

以下情况返回 `阻塞`：

- 基于当前任务计划，无法安全推进实现

## 反模式

- 因为“实现的人会自己补齐”就直接通过
- 忽略缺失的验证步骤
- 用里程碑标题代替真正的任务项
- 评审通过后却不更新当前活跃任务和推荐下一步状态

## 完成条件

评审结论可以输出在当前对话、评审评论或临时评审记录中，但仍必须给出明确结论、计划薄弱点和唯一下一步。

只有在给出明确结论、记录位置（或等价输出位置）和唯一下一步之后，这个 skill 才算完成。
