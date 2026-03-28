---
name: mdc-regression-gate
description: 在代码评审之后、最终完成宣告之前，对已实现的 MDC 任务执行回归门禁。适用于当前任务看起来已经完成并通过评审，但仍需确认相关行为、更大范围测试、构建或检查未被破坏的场景。
---

# MDC 回归门禁

在任务可被视为完成之前，执行最小必要的回归验证。

## 目的

这个 skill 用于防止“局部修好了，但周边悄悄坏掉”的情况。

仅仅当前新任务测试通过，并不足以说明没有引入回归。

## 适用时机

优先用于以下场景：

- 当前任务已完成主要实现与前置评审
- 当前改动影响了相邻模块、共享能力或集成点
- 准备从当前任务进入最终完成判定

## 输入

使用以下输入：

- 当前实现的任务
- 任务计划中的验证要求
- 项目常规验证命令

## 记录要求

回归门禁完成后，默认将本次验证写入：

- `docs/verification/regression-<task>.md`

如 `AGENTS.md` 为当前项目声明了等价路径，按其中映射路径保存。

若项目尚未形成固定 verification 记录格式，默认使用：

- `skills/mdc-workflow/templates/verification-record-template.md`

如果结论为 `通过`，应同步更新：

- `task-progress.md` 中相关回归状态
- `task-progress.md` 的 Next Skill 为 `mdc-completion-gate`

如果结论为 `需修改`，应同步更新：

- 当前任务仍需回到实现
- `task-progress.md` 的 Next Skill 为 `mdc-implement`

如果结论为 `阻塞`，应同步更新：

- `task-progress.md` 中相关回归状态与阻塞原因
- `task-progress.md` 的 Next Skill 暂时保持为 `mdc-regression-gate`

若项目尚未形成固定进度记录格式，默认使用：

- `skills/mdc-workflow/templates/task-progress-template.md`

## 工作流

### 1. 明确相关回归面

确定本次改动之后，哪些内容必须继续保持成立：

- 相关测试
- 受影响模块
- 构建或类型检查状态
- 本地集成点

### 2. 运行最新检查

立即运行相关验证命令。

不要依赖更早之前的结果，除非那些结果正是针对当前这份最新任务状态，在本轮流程中执行得到的。

### 3. 读取实际结果

检查：

- 退出状态
- 失败数量
- 本次验证范围是否覆盖了回归面

### 4. 决定门禁结果

如果回归面仍然健康，下一步进入 `mdc-completion-gate`。

如果不健康，下一步回到 `mdc-implement`。

## 输出格式

请严格使用以下结构：

```markdown
## 结论

通过 | 需修改 | 阻塞

## 证据

- 命令与结果摘要

## 回归风险

- 风险项

## 下一步

`mdc-completion-gate` | `mdc-implement` | `补齐阻塞条件后重试 mdc-regression-gate`

## 记录位置

- `docs/verification/regression-<task>.md` 或映射路径
```

## 判定规则

只有在相关回归检查为最新执行，且结果支持继续推进时，才返回 `通过`。

如果检查失败，或覆盖范围不足，则返回 `需修改`。

如果由于环境或验证配置损坏，暂时无法运行正确的回归命令，则返回 `阻塞`。

## 反模式

- 想当然地认为周边行为仍然正常
- 使用过期测试输出
- 只跑新测试就声称已经覆盖回归
- 因为单测通过就忽略构建或类型检查失败

## 完成条件

只有在基于最新证据给出明确门禁结论、记录位置和唯一下一步后，这个 skill 才算完成。
