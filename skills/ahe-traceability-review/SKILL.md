---
name: ahe-traceability-review
description: 检查需求、设计、任务、实现、测试与验证证据之间是否仍然一致，用于确认当前改动没有无记录偏离、设计漂移或验证断链，并判断其是否足以安全进入 `ahe-regression-gate`。适用于 full / standard profile 中 `ahe-code-review` 之后的正式 evidence-chain 判断；lightweight 默认跳过，若手动调用则视为补充性评审。
---

# AHE 可追溯性评审

检查规格、设计、任务、实现与验证之间是否仍然对齐。

在完整 AHE workflow 中，它通常用于 full / standard 正式评审链中的追溯性判断。

## 角色定位

这个 skill 用于防止“代码能跑，但和原本批准的东西已经不是一回事”。

它关注的是一致性和追溯性，而不是代码风格、实现技巧或回归执行本身。

它负责：

- 判断需求、设计、任务、实现、测试、验证之间的关键链路是否闭合
- 判断“已完成”的声明是否真的能回指到已批准工件与已有证据
- 给出能否安全进入 `ahe-regression-gate` 的 evidence-chain 结论

它不替代：

- `ahe-code-review` 的实现质量判断
- `ahe-regression-gate` 的新鲜验证执行

## 与 AHE 主链的关系

- 在 full / standard profile 中，通常位于 `ahe-code-review` 之后、`ahe-regression-gate` 之前
- 在 lightweight profile 中，`ahe-workflow-starter` 默认跳过本节点；若手动调用，应视为补充性评审，而不是改写 workflow canonical state 的正式节点
- 在 full / standard 正式链路中，若本节点结论不是 `通过`，按主链返回 `ahe-test-driven-dev`；若 root cause 是上游批准缺失、工件断链或编排错位，应在评审记录中明确要求它先经 `ahe-workflow-starter` 重编排，而不是直接继续编码

## Reviewer Subagent 运行约定

本 skill 默认运行在独立 reviewer subagent 中。

当以该模式运行时：

- reviewer 负责读取实现交接块、上游 review 记录和最小必要工件链上下文
- reviewer 负责把评审记录写入约定路径
- reviewer 负责回传结构化摘要
- reviewer 不负责代替父会话推进整个 workflow
- reviewer 不负责代替父会话继续执行 `ahe-regression-gate`
- 若 reviewer 判断当前问题本质上需要 profile 升级或重新编排，应在回传中显式要求先经 `ahe-workflow-starter`
- reviewer 可以建议下一步，但 canonical workflow state 与 `task-progress.md` 更新归父会话维护

## 适用时机

优先用于以下场景：

- 需要确认当前改动的规格、设计、任务、实现和验证是否还能互相回指
- 当前任务已完成代码评审，准备进入回归门禁
- 当前改动涉及用户可见行为、接口变化或复杂业务规则
- 当前任务在实现过程中发生过设计调整或需求收敛
- 热修复、增量变更后需要确认工件链路仍然一致

## 高质量评审基线

高质量的 `ahe-traceability-review` 结果，至少应满足：

- 先消费上游实现交接块、bug-patterns、test-review、code-review 与必要的任务 / 设计锚点，而不是只看代码和一句“已经完成”
- 不只说“链路有问题”，还要指出具体断链发生在哪一段
- 明确哪些问题属于 evidence-chain，哪些应留给 `ahe-code-review` 或 `ahe-regression-gate`
- 输出能直接被 `ahe-regression-gate`、`ahe-finalize` 或 `ahe-test-driven-dev` 消费

## 输入

阅读以下最少必要信息：

- `AGENTS.md` 中与当前项目相关的工件、批准、状态字段或 review 规范（如果存在）
- 当前实现改动、测试变更与已有验证证据
- `ahe-test-driven-dev` 的实现交接块或等价证据
- `ahe-bug-patterns` 记录（如当前链路要求）
- `ahe-test-review` 记录
- `ahe-code-review` 记录
- 与这些改动相关的规格、设计和任务片段
- `task-progress.md` 当前状态
- 当前任务的完成声明或交付范围

如果当前上下文无法提供完整已批准工件，至少应提供当前改动范围、目标行为和可核对的一组需求 / 设计 / 任务 / 验证依据。

lightweight 手动补充评审时，可放宽为最少提供当前改动范围、目标行为和一组可核对的工件 / 验证依据；full / standard 正式链路不适用这条放宽。

## Pre-flight

开始评审前，至少固定：

- 当前任务 ID
- 当前 profile
- `AGENTS.md` 中声明的批准规则、工件位置与状态字段约定（如有）
- 上游实现交接块中的 Task ID、RED / GREEN 证据摘要与 handoff
- `ahe-bug-patterns` 的结论与命中风险摘要（如当前链路要求）
- `ahe-test-review` 与 `ahe-code-review` 的结论与主要发现
- 当前任务对应的规格 / 设计 / 任务锚点
- `task-progress.md` 中的 Current Stage / Current Active Task / Pending Reviews And Gates
- 当前需要被证明的完成声明或交付范围

## 记录要求

评审完成后，必须将本次结论写入：

- `docs/reviews/traceability-review-<task>.md`

如 `AGENTS.md` 为当前项目声明了等价路径，按其中映射路径保存。

若项目尚未形成固定 review 记录格式，默认使用：

- `templates/review-record-template.md`

若需要追溯性专属字段，可在默认模板基础上补充当前 skill 目录下的 `references/traceability-review-record-template.md` 中的内容。

如果当前任务正在使用 `task-progress.md` 驱动 workflow，且当前 profile 是 full / standard，则父会话在消费本 skill 的评审记录与结构化摘要后，应同步更新：

- `task-progress.md` 中的追溯性评审状态
- 当前任务是否需要回到 `ahe-test-driven-dev`，还是可以进入 `ahe-regression-gate`
- `task-progress.md` 中的 `Next Action Or Recommended Skill`
- 若结论为 `阻塞`，阻塞原因是否要求 `ahe-test-driven-dev` 先经 `ahe-workflow-starter` 重编排
- 当前阻塞原因、断链点或待补同步项（如有）

若项目尚未形成固定进度记录格式，默认使用：

- `templates/task-progress-template.md`

## 参考资料

如果团队还没有统一的追溯性评审记录格式，可先使用以下模板：

- 当前 skill 目录下的 `references/traceability-review-record-template.md`

## 检查维度

### 1. 规格 -> 设计

- 当前实现所对应的设计，是否仍然承接了已批准规格中的关键行为、约束和边界？
- 若规格或设计之一已经变化，另一端是否同步更新，还是出现了 silent drift？

### 2. 设计 -> 任务

- 当前任务计划是否真的覆盖了设计要求中的关键实现点与完成条件？
- 是否出现“设计有要求，但任务没拆到”或“任务做了设计没承认的额外内容”？

### 3. 任务 -> 实现

- 当前完成项是否能回指到任务计划中的明确任务？
- 是否出现任务之外的无记录行为扩张、隐式范围增加或 undocumented behavior？

### 4. 实现 -> 测试 / 验证

- 测试与已有验证证据，是否真的支撑了当前实现被声称完成的行为？
- 是否出现 orphan code、无对应验证的结论、或“代码改了但验证记录还停留在旧状态”的情况？

### 5. 用户可见变化 / 状态工件（如适用）

- 若本轮改动影响用户可见行为、入口文档、发布说明或 task-progress 状态，这些工件是否与当前交付声明一致？
- 若这些同步问题超出本节点范围，至少要把它记录为待回写项，而不是假装链路已闭合

## 检查清单

- 不要把 traceability review 做成第二次 code review
- 不要把“聊天里说通过了”当成正式批准或正式证据
- 不要跳过链段定位，只给一个模糊的“一致 / 不一致”结论

## 输出格式

请严格使用以下结构：

```markdown
## 结论

通过 | 需修改 | 阻塞

## 上游已消费证据

- Task ID
- 实现交接块 / 等价证据
- `ahe-bug-patterns` 记录（如适用）
- `ahe-test-review` 记录
- `ahe-code-review` 记录

## 链路矩阵

- 规格 -> 设计：通过 | 需修改 | 阻塞
- 设计 -> 任务：通过 | 需修改 | 阻塞
- 任务 -> 实现：通过 | 需修改 | 阻塞
- 实现 -> 测试 / 验证：通过 | 需修改 | 阻塞
- 用户可见变化 / 状态工件（如适用）：通过 | 需修改 | 阻塞 | `N/A`

## 追溯缺口

- 缺口

## 漂移风险

- 风险

## 明确不在本轮范围内

- 条目 | `N/A`

## 下一步

- full / standard：`ahe-regression-gate` | `ahe-test-driven-dev`
- lightweight 手动调用：
  - 正常补充性评审：记录为 `N/A（补充性评审，不改写 canonical state）`
  - 若发现当前 profile 已不成立：`ahe-workflow-starter`

## 记录位置

- `docs/reviews/traceability-review-<task>.md` 或映射路径
```

## 判定规则

只有当规格、设计、任务、实现、测试和验证之间的关键链路保持一致，且不存在明显断链或无记录偏离时，才返回 `通过`。

如果存在设计漂移、实现越界、测试无法支撑结论，或需要先补同步记录，则返回 `需修改`。

如果缺少已批准工件、关键评审记录或无法获得必要证据链，则返回 `阻塞`。

在 full / standard 正式链路中，若缺少当前任务对应的实现交接块、必要的 `ahe-bug-patterns` 记录、`ahe-test-review` 记录、`ahe-code-review` 记录、必要的规格 / 设计 / 任务锚点，或 `task-progress.md` 与这些工件互相冲突，也返回 `阻塞`。

full / standard 中，本 skill 返回 `通过` 后进入 `ahe-regression-gate`，返回 `需修改` / `阻塞` 时回到 `ahe-test-driven-dev`。

full / standard 中，应在 `task-progress.md` 或等价状态工件中显式写入 canonical `Next Action Or Recommended Skill`：`ahe-regression-gate` 或 `ahe-test-driven-dev`。

full / standard 中，若结论为 `阻塞`，评审记录里必须写清阻塞是“实现修订类”还是“上游批准 / 工件 / 编排类”：

- 若是实现修订类，`ahe-test-driven-dev` 处理后再恢复后续编排
- 若是上游批准 / 工件 / 编排类，`ahe-test-driven-dev` 不得伪造缺失证据，应先经 `ahe-workflow-starter` 重编排，再决定是否继续实现或回到更上游节点

lightweight 手动调用时，应把本次结果视为补充性评审：默认不改写 workflow canonical `Next Action Or Recommended Skill`；但若发现证据足以证明当前 lightweight profile 不成立，应明确把下一步改为 `ahe-workflow-starter` 以触发 profile 升级或重编排。

## 反模式

- 把追溯性评审做成重复的代码评审
- 只检查代码，不检查任务和规格
- 明显发生偏离，却不记录、不回写
- 因为功能看起来可用就忽略断链问题
- 不读取上游实现交接块和评审记录，就直接下结论
- 把 traceability review 做成第二个 regression gate

## 回传给父会话

若本 skill 运行在 reviewer subagent 中，至少回传：

- `conclusion`
- `next_action`
- `record_path`
- `key_findings`
- `needs_human_confirmation`：对本 skill 通常为 `false`
- 若发现当前应先做 profile 升级、重编排或回到 workflow 入口，补充 `reroute_via_starter=true`

## 完成条件

评审结论必须写入仓库中的评审记录路径。可以在对话中摘要结论，但对话不能替代记录工件。

只有在评审记录已经落盘，且给出明确结论、追溯缺口、漂移风险和唯一下一步之后，这个 skill 才算完成。

若本 skill 由 reviewer subagent 执行，还应完成对父会话的结构化结果回传。
