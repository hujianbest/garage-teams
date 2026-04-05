---
name: ahe-completion-gate
description: 使用最新验证证据对当前任务执行最终完成门禁，判断当前任务是否已经具备宣告完成、更新状态或切换任务的条件，并决定其是否可以安全进入 `ahe-finalize`。适用于 `ahe-regression-gate` 之后的正式完成判断。
---

# AHE 完成门禁

在宣告完成之前，必须先确认有足够证据。

在完整 AHE workflow 中，它通常作为末端完成判断。

## 角色定位

这个 skill 用于在更新状态、切换任务或输出完成说明之前，确认“当前任务已完成”这件事有最新证据支撑。

它负责：

- 锁定当前准备宣告的完成范围
- 基于上游 review / gate 记录与 fresh evidence 判断当前任务是否允许宣告完成
- 给出能否进入 `ahe-finalize` 的最终完成结论

它不替代：

- `ahe-regression-gate` 的更广义回归判断
- `ahe-finalize` 的文档 / 状态 / 发布收尾

## 与 AHE 主链的关系

- 当前节点位于 `ahe-regression-gate` 之后、`ahe-finalize` 之前
- `ahe-completion-gate` 关注的是“是否允许宣告当前任务完成”，不是重新定义回归面
- 若本节点结论为 `需修改`，按主链返回 `ahe-test-driven-dev`
- 若本节点结论为 `阻塞`，先区分阻塞类型：环境 / 工具链类优先补条件后重试本节点；上游编排、profile 或证据链问题则先经 `ahe-workflow-starter` 重编排，再决定是否回到 `ahe-test-driven-dev` 或更上游节点

## 与 review subagent 协议的兼容性

本 skill 当前不是 reviewer subagent，也不要求按 review dispatch protocol 派发独立 verifier 执行。

当前约定：

- 上游 `ahe-test-review`、`ahe-code-review`、`ahe-traceability-review` 等记录可以来自独立 reviewer subagent，本 skill 只消费这些已落盘记录、`ahe-regression-gate` 记录与当前 fresh evidence
- 当前 completion gate 仍由父工作流在当前会话执行，因为它需要基于当前环境运行最终验证命令并判断是否允许宣告完成
- 当前 canonical handoff、验证记录落盘和状态更新，仍由执行本 gate 的当前会话直接维护
- 若后续 AHE 统一引入 verifier subagent，本 skill 可以平移到 verifier 执行；在那之前不要把它误写成 review 型 subagent 节点

## 高质量门禁基线

高质量的 `ahe-completion-gate` 结果，至少应满足：

- 先消费 regression 记录、实现交接块和当前 profile 下应存在的 review / gate 记录
- 不只说“现在差不多完成了”，而要清楚定义本轮正在宣告什么完成范围
- fresh evidence 能证明这些结果属于当前最新代码状态
- 输出能直接被 `ahe-finalize` 消费

## 适用时机

优先用于以下场景：

- 需要确认当前任务是否真的可以宣告完成
- 当前任务已通过测试评审、代码评审、追溯性评审和回归检查
- 准备更新 `task-progress.md`、`RELEASE_NOTES.md` 或其他完成状态记录
- 准备宣告“当前任务完成”并进入 `ahe-finalize`

## 输入

阅读以下最少必要信息：

- `AGENTS.md` 中声明的验证入口、完成判断约定和状态字段（如果存在）
- 当前任务标识与其完成声明
- `ahe-test-driven-dev` 的实现交接块或等价证据
- `ahe-regression-gate` 记录
- 当前 profile 下适用的 review / gate 记录
- 最新测试、构建、类型检查或集成验证命令
- `task-progress.md` 当前状态

若当前 profile 是 `full` 或 `standard`，缺少必需的上游 review / gate 记录时不得继续完成判断，应立即按 `阻塞` 处理。

若当前 profile 是 `lightweight`，最少也必须提供当前任务的完成声明、`ahe-test-driven-dev` 实现交接块、`ahe-regression-gate` 记录、支持该声明的最新验证命令，以及可用的结果证据。

## Pre-flight

开始门禁前，至少固定：

- 当前任务 ID
- 当前 workflow profile
- `AGENTS.md` 中声明的完成判断规则、验证顺序和状态字段
- 当前到底准备宣告什么：任务完成 | 缺陷已修复 | 某项行为已可交付
- `ahe-test-driven-dev` 实现交接块中的 Task ID、Pending Reviews And Gates 与 handoff
- `ahe-regression-gate` 的结论与记录路径
- `task-progress.md` 中的 Current Stage / Current Active Task / Pending Reviews And Gates / Next Action

## Profile-aware 完成条

完成门禁不要假设所有 profile 都有同一条上游证据链：

| Profile | completion gate 前默认应确认的上游记录 |
|---|---|
| `full` | `ahe-bug-patterns`、`ahe-test-review`、`ahe-code-review`、`ahe-traceability-review`、`ahe-regression-gate`、实现交接块 |
| `standard` | `ahe-bug-patterns`、`ahe-test-review`、`ahe-code-review`、`ahe-traceability-review`、`ahe-regression-gate`、实现交接块 |
| `lightweight` | `ahe-regression-gate`、实现交接块；其余项写 `N/A（按 profile 跳过）` |

若当前 profile 是 `full` 或 `standard`，上述记录缺失、过旧或结论不支持继续进入 completion gate，应停止并按阻塞处理。

## 铁律

没有针对当前最新代码状态的验证证据，就不能宣称任务完成。

如果本轮流程里没有亲自运行验证命令，就不能诚实地宣称完成。

## 在以下动作前必须使用本 Skill

- 说任务已经完成
- 更新进度或状态为已完成
- 切换到下一个任务
- 编写带有“已完成”含义的提交或交付说明

## 记录要求

完成门禁结束后，必须将本次验证写入：

- `docs/verification/completion-<task>.md`

如 `AGENTS.md` 为当前项目声明了等价路径，按其中映射路径保存。

若项目尚未形成固定 verification 记录格式，默认使用：

- `templates/verification-record-template.md`

如果当前任务正在使用 `task-progress.md` 驱动 workflow，应同步更新：

- `task-progress.md` 中当前任务的完成状态
- 当前任务是可以进入 `ahe-finalize`、仍需回到 `ahe-test-driven-dev`、先经 `ahe-workflow-starter` 重编排，还是在阻塞条件解除后重试 `ahe-completion-gate`
- `task-progress.md` 中的 `Next Action Or Recommended Skill`
- 当前阻塞原因或证据缺口（如有）

若项目尚未形成固定进度记录格式，默认使用：

- `templates/task-progress-template.md`

## 工作流

### 1. 明确你要宣告的结论

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

### 7. 对结论做门禁判断

- 如果证据支持结论，则允许完成
- 如果不支持，则说明真实状态并回到实现修订

## 输出格式

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

## 判定规则

只有当准备宣告的“完成”结论被最新证据直接支持时，才返回 `通过`。

如果证据不足以支持该结论，或者仍需继续实现，则返回 `需修改`。

如果由于环境或工具链问题无法运行正确的验证命令，则返回 `阻塞`。

若缺少当前任务对应的 `ahe-test-driven-dev` 实现交接块或 `ahe-regression-gate` 记录，也返回 `阻塞`。

若当前 profile 是 `full` 或 `standard`，但缺少必需的 review / gate 记录、这些记录与 `task-progress.md` 状态冲突，或当前 completion 声明超出了这些记录支持的范围，也返回 `阻塞`。

本 skill 返回 `通过` 后进入 `ahe-finalize`，返回 `需修改` 时回到 `ahe-test-driven-dev`。

应在 `task-progress.md` 或等价状态工件中显式写入 canonical `Next Action Or Recommended Skill`：`ahe-finalize`、`ahe-test-driven-dev` 或 `ahe-completion-gate`（仅用于环境 / 工具链类阻塞重试）。
对于上游编排 / profile / 证据链类阻塞，应将 canonical `Next Action Or Recommended Skill` 写为 `ahe-workflow-starter`。

若结论为 `阻塞`，记录里必须写清阻塞是“环境 / 工具链类”还是“上游编排 / profile / 证据链类”：

- 若是环境 / 工具链类，先补齐运行条件，并把 `Next Action Or Recommended Skill` 写为 `ahe-completion-gate` 后重试本节点
- 若是上游编排 / profile / 证据链类，`ahe-test-driven-dev` 不得伪造缺失证据，应先经 `ahe-workflow-starter` 重编排，再决定是否继续实现、回到更上游节点，或在阻塞解除后重新进入 `ahe-completion-gate`

## 反模式

- 说“现在应该算完成了”
- 依赖旧输出
- 把主观感觉当成证据
- 认为评审通过就等于运行成功
- 因为做烦了就直接进入下一步
- 不读取 regression 记录就直接宣告完成
- 把 completion gate 做成第二个 finalize

## 完成条件

门禁结论必须写入仓库中的验证记录路径。可以在对话中摘要结论，但对话不能替代验证工件。

只有在验证记录已经落盘，且用最新证据批准或拒绝完成结论，并给出唯一下一步后，这个 skill 才算完成。
