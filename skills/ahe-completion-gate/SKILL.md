---
name: ahe-completion-gate
description: 执行正式完成门禁。适用于已有 `ahe-regression-gate` 记录、需要用 fresh completion evidence 判断当前任务是否允许宣告完成、更新状态并安全进入 `ahe-finalize` 的场景；若阶段不清、上游证据链缺失或 profile 条件冲突，先回到 `ahe-workflow-starter`。
---

# AHE 完成门禁

在宣告完成之前，必须先确认有足够、最新且与当前任务同范围的证据。

## Overview

这个 skill 的职责是在更新状态、切换任务或输出完成说明之前，确认“当前任务已完成”这件事有最新证据支撑。

它负责：

- 锁定当前准备宣告的完成范围
- 基于上游 review / gate 记录与 fresh evidence 判断当前任务是否允许宣告完成
- 给出能否进入 `ahe-finalize` 的最终门禁结论

与 `ahe-regression-gate` 的区别是：regression gate 判断更广义的回归面是否健康；completion gate 重新锚定当前“完成宣告范围”本身是否被最新证据直接支持。两者可复用部分命令，但不要把它们当成同一个 gate。

它不替代：

- `ahe-regression-gate` 的更广义回归判断
- `ahe-finalize` 的文档 / 状态 / 发布收尾

## When to Use

在这些场景使用：

- 当前节点位于 `ahe-regression-gate` 之后、`ahe-finalize` 之前
- 需要确认当前任务是否真的可以宣告完成
- 当前任务已通过必要的 review / gate，准备更新 `task-progress.md`、`RELEASE_NOTES.md` 或其它完成状态记录
- 用户明确要求“现在能不能算完成”或“是否可以进入 finalize”

不要在这些场景使用：

- 当前没有 `ahe-regression-gate` 记录或 `ahe-test-driven-dev` 的实现交接块
- 当前需要的是更广义回归验证，改用 `ahe-regression-gate`
- 当前需要的是状态与文档收尾，改用 `ahe-finalize`
- 当前阶段不清、profile 条件冲突或上游证据链缺失，先回到 `ahe-workflow-starter`

## Standalone Contract

当用户直接点名 `ahe-completion-gate` 时，至少确认以下条件：

- 当前任务 / 完成范围明确
- 存在 `ahe-regression-gate` 记录
- 存在 `ahe-test-driven-dev` 的实现交接块或等价证据
- 能读取到支持当前完成声明的最新验证命令
- 若当前 profile 是 `full` / `standard`，还能读取必需的 review / gate 记录

若这些前提不满足，不要强行宣告完成：

- 缺最新完成证据：返回 `需修改`
- 缺 regression 记录、实现交接块或必需上游记录：返回 `阻塞`
- 缺 route / profile 判断：先回到 `ahe-workflow-starter`

## Chain Contract

作为主链节点被串联调用时，默认读取：

- `AGENTS.md` 中声明的验证入口、完成判断约定和状态字段
- 当前任务标识与其完成声明
- `ahe-test-driven-dev` 的实现交接块或等价证据
- `ahe-regression-gate` 记录
- 当前 profile 下适用的 review / gate 记录
- `task-progress.md` 当前状态

本节点完成后应写回：

- 一份 completion gate verification record
- 当前任务的完成状态
- canonical `Next Action Or Recommended Skill`

当前 completion gate 仍由父工作流在当前会话执行，不按 review dispatch protocol 派发 reviewer subagent；它消费 review / gate 记录，但自身不是 review 节点。

## Hard Gates

- 没有针对当前最新代码状态的验证证据，就不能宣称任务完成。
- 如果本轮流程里没有亲自运行验证命令，就不能诚实地宣称完成。
- 缺少当前任务对应的 `ahe-test-driven-dev` 实现交接块或 `ahe-regression-gate` 记录，不得返回 `通过`。
- 不得把 completion gate 写成第二个 regression gate 或第二个 finalize。

## Quality Bar

高质量的 `ahe-completion-gate` 结果，至少应满足：

- 先消费 regression 记录、实现交接块和当前 profile 下应存在的 review / gate 记录
- 不只说“现在差不多完成了”，而要清楚定义本轮正在宣告什么完成范围
- fresh evidence 能证明这些结果属于当前最新代码状态
- 输出能直接被 `ahe-finalize` 消费

## Inputs / Required Artifacts

开始门禁前，至少固定：

- 当前任务 ID
- 当前 workflow profile
- `AGENTS.md` 中声明的完成判断规则、验证顺序和状态字段
- 当前到底准备宣告什么：任务完成 | 缺陷已修复 | 某项行为已可交付
- `ahe-test-driven-dev` 实现交接块中的 Task ID、`Pending Reviews And Gates` 与 handoff
- `ahe-regression-gate` 的结论与记录路径
- `task-progress.md` 中的 `Current Stage` / `Current Active Task` / `Pending Reviews And Gates` / `Next Action Or Recommended Skill`

默认 completion 记录保存到：

- `docs/verification/completion-<task>.md`

若 `AGENTS.md` 为当前项目声明了映射路径，优先使用映射路径。

若项目尚未形成固定 verification 记录格式，默认使用：

- `templates/verification-record-template.md`

若项目尚未形成固定进度记录格式，默认使用：

- `templates/task-progress-template.md`

Profile-aware 上游证据矩阵：

| Profile | completion gate 前默认应确认的上游记录 |
|---|---|
| `full` | `ahe-bug-patterns`、`ahe-test-review`、`ahe-code-review`、`ahe-traceability-review`、`ahe-regression-gate`、实现交接块 |
| `standard` | `ahe-bug-patterns`、`ahe-test-review`、`ahe-code-review`、`ahe-traceability-review`、`ahe-regression-gate`、实现交接块 |
| `lightweight` | `ahe-regression-gate`、实现交接块；其余项写 `N/A（按 profile 跳过）` |

若当前 profile 是 `full` / `standard`，上述记录缺失、过旧或结论不支持继续进入 completion gate，应停止并按 `阻塞` 处理。

## Workflow

### 1. 明确你要宣告的完成范围

明确写出你准备宣告什么，例如：

- 测试通过
- 功能行为正常
- 缺陷已修复
- 任务已完成

### 2. 对齐上游结论与 profile 条件

先确认：

- 当前 profile 下必需存在的 review / gate 记录是否都齐全
- `ahe-regression-gate` 是否真的给出了允许继续的最新结论
- 实现交接块、`task-progress.md` 和当前完成声明是否在同一任务 / 同一范围上

### 3. 确定证明该结论的命令

选择真正能证明该结论的命令。

不要用更弱的证据替代。

### 4. 执行最新验证

立即运行完整验证命令。

### 5. 阅读完整结果

检查：

- 退出码
- 失败数量
- 输出是否真的支持该结论
- 这些结果是否明确属于当前最新代码状态

### 6. 形成 completion evidence bundle

至少记录：

- 正在宣告的完成范围
- 命令
- 退出码
- 结果摘要
- 新鲜度锚点：为什么这次运行属于当前最新代码状态
- 这些证据明确没有覆盖什么

### 7. 对结论做门禁判断并写回状态

- 如果证据支持结论，则允许进入 `ahe-finalize`
- 如果证据不足以支持该结论，或仍需继续实现，则回到 `ahe-test-driven-dev`
- 如果环境 / 工具链损坏，下一步重试 `ahe-completion-gate`
- 如果阻塞暴露的是上游编排 / profile / 证据链问题，下一步经 `ahe-workflow-starter` 重编排

同步更新 verification record、当前任务完成状态、阻塞原因和 canonical 下一步。

## Output Contract

请严格使用以下结构：

```markdown
## 结论

通过 | 需修改 | 阻塞

## 已消费的上游结论

- Task ID

## 上游证据矩阵

- `ahe-bug-patterns`: 路径 | `N/A（按 profile 跳过）`
- `ahe-test-review`: 路径 | `N/A（按 profile 跳过）`
- `ahe-code-review`: 路径 | `N/A（按 profile 跳过）`
- `ahe-traceability-review`: 路径 | `N/A（按 profile 跳过）`
- `ahe-regression-gate`: 路径
- 实现交接块: 路径 | 等价证据说明

## 完成宣告范围

- 条目

## 已验证结论

- 结论项

## 证据

- 命令 | 退出码 | 结果摘要 | 新鲜度锚点

## 覆盖 / 声明边界

- 条目

## 明确不在本轮范围内

- 条目 | `N/A`

## 下一步

- `通过`：`ahe-finalize`
- `需修改`：`ahe-test-driven-dev`
- `阻塞`：
  - 环境 / 工具链类：`ahe-completion-gate`
  - 上游编排 / profile / 证据链类：`ahe-workflow-starter`

## 记录位置

- `docs/verification/completion-<task>.md` 或映射路径
```

判定规则：

- 只有当准备宣告的“完成”结论被最新证据直接支持时，才返回 `通过`
- 如果证据不足以支持该结论，或者仍需继续实现，则返回 `需修改`
- 如果由于环境或工具链问题无法运行正确的验证命令，则返回 `阻塞`
- full / standard 缺少必需的 review / gate 记录、这些记录与 `task-progress.md` 状态冲突，或当前 completion 声明超出了这些记录支持的范围，也返回 `阻塞`

应在 `task-progress.md` 或等价状态工件中显式写入 canonical `Next Action Or Recommended Skill`：`ahe-finalize`、`ahe-test-driven-dev`、`ahe-completion-gate` 或 `ahe-workflow-starter`。

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| “现在应该算完成了” | completion gate 只接受能直接支撑完成宣告的最新证据。 |
| “评审都过了，就不用再跑完成验证了” | review 通过不等于当前完成声明已被最新运行结果支持。 |
| “先把状态改成完成，证据后面补” | 没有 evidence bundle 就不能诚实宣告完成。 |
| “环境坏了也先记成需修改吧” | 环境 / 工具链问题应明确分类为 `阻塞`。 |
| “lightweight 就不用写哪些证据跳过了” | profile 可跳过不等于可以留空，必须写 `N/A（按 profile 跳过）`。 |
| “finalize 里再收一次就行，这里先口头说完成” | completion gate 自身就是正式 gate artifact，不是 narrative summary。 |

## Red Flags

- 说“现在应该算完成了”
- 依赖旧输出
- 把主观感觉当成证据
- 认为评审通过就等于运行成功
- 因为做烦了就直接进入下一步
- 不读取 regression 记录就直接宣告完成
- 把 completion gate 做成第二个 finalize

## Verification

门禁结论必须写入仓库中的验证记录路径。可以在对话中摘要结论，但对话不能替代验证工件。

只有在以下条件全部满足时，这个 skill 才算完成：

- [ ] completion verification record 已落盘
- [ ] 记录中写清已消费的上游证据矩阵、完成宣告范围、evidence bundle 和声明边界
- [ ] 基于最新证据给出唯一门禁结论
- [ ] `task-progress.md` 或等价状态工件已写回当前任务完成状态与 canonical `Next Action Or Recommended Skill`
- [ ] 下一步明确为 `ahe-finalize`、`ahe-test-driven-dev`、`ahe-completion-gate` 或 `ahe-workflow-starter`
