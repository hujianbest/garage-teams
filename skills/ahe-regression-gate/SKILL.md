---
name: ahe-regression-gate
description: 对当前改动执行回归门禁，用于确认相关行为、更大范围测试、构建或检查未被破坏，并判断其是否足以安全进入 `ahe-completion-gate`。适用于 full / standard profile 中 `ahe-traceability-review` 之后、以及 lightweight profile 中 `ahe-test-driven-dev` 之后的正式回归判断。
---

# AHE 回归门禁

在任务可被视为完成之前，执行最小必要的回归验证。

在完整 AHE workflow 中，它通常用于正式完成判断之前。

## 角色定位

这个 skill 用于防止“局部修好了，但周边悄悄坏掉”的情况。

仅仅当前新任务测试通过，并不足以说明没有引入回归。

它负责：

- 定义当前最小必要的回归面
- 基于当前最新代码状态收集 fresh regression evidence
- 给出能否安全进入 `ahe-completion-gate` 的回归结论

它不替代：

- `ahe-traceability-review` 的 evidence-chain 检查
- `ahe-completion-gate` 的最终“可以宣告完成吗”判断

## 与 AHE 主链的关系

- 在 full / standard profile 中，通常位于 `ahe-traceability-review` 之后、`ahe-completion-gate` 之前
- 在 lightweight profile 中，通常位于 `ahe-test-driven-dev` 之后、`ahe-completion-gate` 之前
- 若本节点结论为 `需修改`，按主链返回 `ahe-test-driven-dev`
- 若本节点结论为 `阻塞`，先区分阻塞类型：环境 / 工具链类优先补条件后重试本节点；上游编排、profile、证据或验证入口定义类则先经 `ahe-workflow-starter` 重编排
- 若 root cause 是上游编排、profile、证据缺失或“当前应跑什么验证入口”本身无法确定，应在记录中明确要求先经 `ahe-workflow-starter` 重编排

## 高质量门禁基线

高质量的 `ahe-regression-gate` 结果，至少应满足：

- 先消费上游 handoff / review 记录，再定义当前回归面
- 不只说“跑过了”，还要说清跑了什么、覆盖了什么、还有什么没覆盖
- fresh evidence 能证明这些结果属于当前最新代码状态，而不是旧日志
- 输出能直接被 `ahe-completion-gate` 和 `ahe-finalize` 消费

## 适用时机

优先用于以下场景：

- 需要确认当前改动没有破坏相邻模块、共享能力或集成点
- 当前任务已完成主要实现与前置评审
- 当前改动影响了相邻模块、共享能力或集成点
- 准备从当前任务进入最终完成判定

## 输入

使用以下输入：

- `AGENTS.md` 中声明的验证命令、验证分层与环境要求（如果存在）
- 当前改动范围与目标行为
- `ahe-test-driven-dev` 的实现交接块或等价证据
- `ahe-traceability-review` 记录（full / standard）
- 与本次改动相关的验证要求、回归面或风险面
- 项目常规验证命令与当前可执行的检查入口
- `task-progress.md` 当前状态与 Pending Reviews And Gates

如果当前上下文无法提供完整任务计划，至少应提供当前改动范围、需要保持不变的行为，以及可执行的回归验证命令。

如果连 `ahe-test-driven-dev` 的实现交接块或等价证据都缺失，不得继续声称当前 regression gate 已具备足够输入。

## Pre-flight

开始门禁前，至少固定：

- 当前任务 ID
- 当前 workflow profile
- `AGENTS.md` 中声明的验证入口、顺序、环境前置条件与特殊例外（如有）
- 上游实现交接块中的关键风险与 proving command 摘要
- full / standard 下的 `ahe-traceability-review` 结论与主要缺口
- 当前要覆盖的回归面：相邻模块、共享能力、构建 / 类型 / 集成入口
- 当前状态工件中的 Pending Reviews And Gates / Next Action

## Profile-aware 回归面

默认不要把不同 profile 的回归要求混成一套：

| Profile | 默认至少覆盖的回归面 |
|---|---|
| `full` | `ahe-traceability-review` 指出的相邻模块 / 共享能力 / 构建 / 类型 / 集成入口，以及项目约定要求的关键验证 |
| `standard` | 与当前改动直接相关的相邻模块 / 共享能力 / 构建 / 类型 / 集成入口 |
| `lightweight` | 最小必要的 build / test / 验证入口，但不能缩成“只跑新测试” |

如果 `AGENTS.md` 为当前项目定义了更严格的回归门槛，优先遵守项目规则。

## 记录要求

回归门禁完成后，必须将本次验证写入：

- `docs/verification/regression-<task>.md`

如 `AGENTS.md` 为当前项目声明了等价路径，按其中映射路径保存。

若项目尚未形成固定 verification 记录格式，默认使用：

- `templates/verification-record-template.md`

如果当前任务正在使用 `task-progress.md` 驱动 workflow，应同步更新：

- `task-progress.md` 中相关回归状态
- 当前任务是需要回到 `ahe-test-driven-dev`、进入 `ahe-completion-gate`，还是在环境 / 工具链阻塞解除后重试 `ahe-regression-gate`
- `task-progress.md` 中的 `Next Action Or Recommended Skill`
- 当前阻塞原因、失败项或覆盖缺口（如有）

若项目尚未形成固定进度记录格式，默认使用：

- `templates/task-progress-template.md`

## 工作流

### 1. 明确相关回归面

确定本次改动之后，哪些内容必须继续保持成立：

- 相关测试
- 受影响模块
- 构建或类型检查状态
- 本地集成点
- 上游 review 明确指出的高风险区域

### 2. 对齐上游结论

先确认：

- 当前 profile 是什么
- 当前要验证的回归面是否与上游 handoff / traceability 记录一致
- 若 full / standard 缺少 traceability 记录，先按阻塞处理，而不是直接跑命令

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

### 6. 决定门禁结果

如果回归面仍然健康，下一步进入 `ahe-completion-gate`。

如果不健康，下一步回到实现修订。

## 输出格式

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
  - 上游编排 / profile / 证据 / 验证入口定义类：`ahe-test-driven-dev`

## 记录位置

- `docs/verification/regression-<task>.md` 或映射路径
```

## 判定规则

只有在相关回归检查为最新执行，且结果支持继续推进时，才返回 `通过`。

如果检查失败，或覆盖范围不足，则返回 `需修改`。

如果由于环境或验证配置损坏，暂时无法运行正确的回归命令，则返回 `阻塞`。

若缺少当前任务对应的 `ahe-test-driven-dev` 实现交接块或等价证据，也返回 `阻塞`。

在 full / standard 正式链路中，若缺少当前任务对应的 `ahe-traceability-review` 记录、必要的验证入口、或 `task-progress.md` 与上游结论互相冲突，也返回 `阻塞`。

full / standard / lightweight 中，本 skill 返回 `通过` 后进入 `ahe-completion-gate`，返回 `需修改` 时回到 `ahe-test-driven-dev`。

应在 `task-progress.md` 或等价状态工件中显式写入 canonical `Next Action Or Recommended Skill`：`ahe-completion-gate`、`ahe-test-driven-dev` 或 `ahe-regression-gate`（仅用于环境 / 工具链类阻塞重试）。

若结论为 `阻塞`，记录里必须写清阻塞是“环境 / 工具链类”还是“上游编排 / profile / 证据 / 验证入口定义类”：

- 若是环境 / 工具链类，先补齐运行条件，并把 `Next Action Or Recommended Skill` 写为 `ahe-regression-gate` 后重试本节点
- 若是上游编排 / profile / 证据 / 验证入口定义类，`ahe-test-driven-dev` 不得伪造缺失证据，应先经 `ahe-workflow-starter` 重编排，再决定是否继续实现或回到更上游节点

## 反模式

- 想当然地认为周边行为仍然正常
- 使用过期测试输出
- 只跑新测试就声称已经覆盖回归
- 因为单测通过就忽略构建或类型检查失败
- 不读取上游 traceability / handoff 记录，就直接跑命令
- 把 regression gate 做成第二个 completion gate

## 完成条件

门禁结论必须写入仓库中的验证记录路径。可以在对话中摘要结论，但对话不能替代验证工件。

只有在验证记录已经落盘，且基于最新证据给出明确门禁结论、回归风险和唯一下一步后，这个 skill 才算完成。
