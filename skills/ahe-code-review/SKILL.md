---
name: ahe-code-review
description: 对已实现任务的代码进行评审，检查实现级正确性、局部设计一致性、错误处理、状态安全性与可维护性，并判断其是否足以安全进入 `ahe-traceability-review`。适用于 full / standard profile 中 `ahe-test-review` 之后的正式实现质量判断；lightweight 默认跳过，若手动调用则视为补充性评审。
---

# AHE 代码评审

评审当前任务的实现代码。

在完整 AHE workflow 中，它通常用于 full / standard 正式评审链中的实现质量判断。

## 角色定位

这个 skill 用于判断实现本身是否可靠，而不只是“测试绿了所以大概率没问题”。

它负责：

- 判断实现级正确性是否可信
- 判断局部设计、状态处理、错误处理与代码结构是否合理
- 给出能否安全进入 `ahe-traceability-review` 的实现质量结论

它不替代：

- `ahe-test-review` 的测试质量裁决
- `ahe-traceability-review` 的工件链路一致性检查
- `ahe-regression-gate` 的回归执行

## 与 AHE 主链的关系

- 在 full / standard profile 中，通常位于 `ahe-test-review` 之后、`ahe-traceability-review` 之前
- 在 lightweight profile 中，`ahe-workflow-starter` 默认跳过本节点；若手动调用，应视为补充性评审，而不是改写 workflow canonical state 的正式节点
- 在 full / standard 正式链路中，若本节点结论不是 `通过`，按主链返回 `ahe-test-driven-dev`；若 root cause 是上游证据缺失或链路错位，应在评审记录中明确要求它先经 `ahe-workflow-starter` 重编排，而不是直接继续编码

## Reviewer Subagent 运行约定

本 skill 默认运行在独立 reviewer subagent 中。

当以该模式运行时：

- reviewer 负责读取实现改动、测试证据、实现交接块和最小必要辅助上下文
- reviewer 负责把评审记录写入约定路径
- reviewer 负责回传结构化摘要
- reviewer 不负责代替父会话推进整个 workflow
- reviewer 不负责代替父会话继续执行 `ahe-traceability-review`
- reviewer 可以建议下一步，但 canonical workflow state 与 `task-progress.md` 更新归父会话维护

## 适用时机

优先用于以下场景：

- 需要判断当前实现是否已经达到可接受质量
- 当前任务已经通过测试评审，准备进入实现质量判断
- 当前改动涉及核心逻辑、错误处理或设计约束
- 需要决定当前实现是否可以进入追溯性评审

## 高质量评审基线

高质量的 `ahe-code-review` 结果，至少应满足：

- 先消费上游实现交接块、test-review 记录与必要的 bug-patterns 上下文，而不是只凭 diff 印象下结论
- 不只问“代码能不能工作”，还要判断状态处理、错误路径、局部设计与维护成本是否合理
- 明确哪些结论属于实现级判断，哪些应留给 `ahe-traceability-review` / `ahe-regression-gate`
- 输出能直接被 `ahe-traceability-review` 或 `ahe-test-driven-dev` 消费

## 输入

阅读以下最少必要信息：

- `AGENTS.md` 中与当前项目相关的 coding / review 规范（如果存在）
- 当前任务实现改动与相关测试
- `ahe-test-driven-dev` 的实现交接块或等价证据
- `ahe-test-review` 记录
- `ahe-bug-patterns` 记录（如当前链路要求）
- 与这些改动相关的规格、设计或任务背景
- 已有验证证据或其它足以支撑评审的上下文

如果当前上下文无法提供完整规格、设计或测试评审结论，至少应提供当前改动范围、目标行为和可参考的测试或验证证据。

lightweight 手动补充评审时，可放宽为最少提供当前改动范围、目标行为和可核对的实现 / 测试证据；full / standard 正式链路不适用这条放宽。

## Pre-flight

开始评审前，至少固定：

- 当前任务 ID
- 当前 profile
- `AGENTS.md` 中声明的代码约定、分层边界、性能 / 安全 / 观测性规则（如有）
- 上游实现交接块中的 RED / GREEN 证据摘要
- `ahe-test-review` 结论与主要缺口
- 当前任务对应的规格 / 设计 / 任务锚点
- `ahe-bug-patterns` 命中的高风险摘要（如当前链路要求）
- 当前 diff / 触碰工件 / 关键实现范围

## 记录要求

评审完成后，必须将本次结论写入：

- `docs/reviews/code-review-<task>.md`

如 `AGENTS.md` 为当前项目声明了等价路径，按其中映射路径保存。

若项目尚未形成固定 review 记录格式，默认使用：

- `templates/review-record-template.md`

如果当前任务正在使用 `task-progress.md` 驱动 workflow，且当前 profile 是 full / standard，则父会话在消费本 skill 的评审记录与结构化摘要后，应同步更新：

- `task-progress.md` 中的代码评审状态
- 当前任务是否需要回到 `ahe-test-driven-dev`，还是可以进入 `ahe-traceability-review`
- 若结论为 `阻塞`，阻塞原因是否要求 `ahe-test-driven-dev` 先经 `ahe-workflow-starter` 重编排
- 当前阻塞原因或待处理代码风险（如有）

若项目尚未形成固定进度记录格式，默认使用：

- `templates/task-progress-template.md`

## 检查维度

### 1. 实现级正确性

- 代码是否真的满足当前任务目标，而不只是碰巧通过当前测试？
- 关键分支、边界条件、早退路径和失败路径是否处理合理？
- 是否存在“主路径能工作，但旁支路径会 silently 出错”的情况？

### 2. 局部设计一致性

- 当前实现是否仍然符合已批准设计中的模块边界、接口约束和状态假设？
- 是否出现 sneaky scope expansion、局部架构漂移或把临时修补写成长期结构？
- 若发现跨规格 / 设计 / 任务的全链路断链，记录为风险并交由 `ahe-traceability-review` 继续核对，而不是在本节点假装完成追溯判断

### 3. 状态、安全与错误路径

- 状态切换、并发 / 重入、一致性假设是否安全？
- 错误处理、降级逻辑、默认值与恢复路径是否合理？
- 若改动触及 trust boundary、权限、敏感数据或外部输入，是否至少满足项目的最低安全约定？

### 4. 可读性与可维护性

- 命名是否清晰易懂？
- 逻辑是否存在不必要的复杂度、深层嵌套或隐性耦合？
- 是否把过多职责堆进单处代码，导致后续修改脆弱？

### 5. 可观测性与调试性

- 当关键路径失败时，是否留下了足够的错误信号、日志、状态或诊断入口？
- 若项目约定要求 metrics / tracing / debug hooks，当前改动是否保持一致？

## 检查清单

- 不要跳过上面的结构化维度
- 不要因为测试是绿的就直接把实现判成“可靠”

## 输出格式

请严格使用以下结构：

```markdown
## 结论

通过 | 需修改 | 阻塞

## 上游已消费证据

- Task ID
- 实现交接块 / 等价证据
- test-review 记录
- bug-patterns 记录（如适用）

## 本轮评审焦点

- 触碰工件 / diff 面
- 重点核对的实现风险

## 发现项

- [严重级别] 问题

## 代码风险

- 条目

## 明确不在本轮范围内

- 条目 | `N/A`

## 给 `ahe-traceability-review` 的提示

- 建议继续核对的规格 / 设计 / 任务 / 验证链路
- 可能存在的断链风险或证据空洞
- 当前实现对上游假设或下游验证的关键依赖

## 下一步

- full / standard：`ahe-traceability-review` | `ahe-test-driven-dev`
- lightweight 手动调用：记录为 `N/A（补充性评审，不改写 canonical state）`

## 记录位置

- `docs/reviews/code-review-<task>.md` 或映射路径
```

## 判定规则

只有当当前任务实现足够合理、可以进入下一步验证时，才返回 `通过`。

如果在实现级正确性、状态安全性、错误处理、局部设计一致性或可维护性方面仍有问题需要先修正，再返回 `需修改`。

如果缺少关键输入、无法定位实现范围，或代码上下文本身不可读，则返回 `阻塞`。

在 full / standard 正式链路中，若缺少当前任务对应的 `ahe-test-review` 记录、必要的规格 / 设计 / 任务锚点、必要的 bug-patterns 风险摘要，或无法把实现交接块、test-review 结论与当前 diff 对齐，也返回 `阻塞`。

full / standard 中，本 skill 返回 `通过` 后进入 `ahe-traceability-review`，返回 `需修改` / `阻塞` 时回到 `ahe-test-driven-dev`。

full / standard 中，若结论为 `阻塞`，评审记录里必须写清阻塞是“实现修订类”还是“上游证据 / 链路类”：

- 若是实现修订类，`ahe-test-driven-dev` 处理后再恢复后续编排
- 若是上游证据 / 链路类，`ahe-test-driven-dev` 不得伪造缺失证据，应先经 `ahe-workflow-starter` 重编排，再决定是否继续实现或回到更上游节点

lightweight 手动调用时，应把本次结果视为补充性评审：可以记录发现，但不要改写 workflow canonical `Next Action Or Recommended Skill`。

## 反模式

- 在这里重复需求评审意见
- 只因为测试是绿的就直接通过代码
- 因为任务小就忽略设计漂移
- 不读取上游实现交接块和 test-review 记录，就直接下结论
- 把 code-review 做成第二个 traceability review 或第二个 regression gate

## 回传给父会话

若本 skill 运行在 reviewer subagent 中，至少回传：

- `conclusion`
- `next_action`
- `record_path`
- `key_findings`
- `needs_human_confirmation`：对本 skill 通常为 `false`
- 若发现当前需要先回到 `ahe-workflow-starter` 重编排，而不是直接回到实现修订，补充 `reroute_via_starter=true`

## 完成条件

评审结论必须写入仓库中的评审记录路径。可以在对话中摘要结论，但对话不能替代记录工件。

只有在评审记录已经落盘，且给出明确结论、发现项、代码风险、给 `ahe-traceability-review` 的提示和唯一下一步之后，这个 skill 才算完成。

若本 skill 由 reviewer subagent 执行，还应完成对父会话的结构化结果回传。
