---
name: mdc-traceability-review
description: 检查需求、设计、任务、实现、测试与验证证据之间是否仍然一致，用于确认当前改动没有无记录偏离、设计漂移或验证断链。
---

# MDC 可追溯性评审

检查规格、设计、任务、实现与验证之间是否仍然对齐。

在完整 MDC workflow 中，它通常用于正式评审链中的追溯性判断。

## 目的

这个 skill 用于防止“代码能跑，但和原本批准的东西已经不是一回事”。

它关注的是一致性和追溯性，而不是代码风格或实现技巧。

## 适用时机

优先用于以下场景：

- 需要确认当前改动的规格、设计、任务、实现和验证是否还能互相回指
- 当前任务已完成代码评审，准备进入回归门禁
- 当前改动涉及用户可见行为、接口变化或复杂业务规则
- 当前任务在实现过程中发生过设计调整或需求收敛
- 热修复、增量变更后需要确认工件链路仍然一致

## 输入

阅读以下最少必要信息：

- 当前实现改动、测试变更与已有验证证据
- 与这些改动相关的规格、设计和任务片段
- 当前任务的完成声明或交付范围

如果当前上下文无法提供完整已批准工件，至少应提供当前改动范围、目标行为和可核对的一组需求 / 设计 / 任务 / 验证依据。

## 记录要求

如果当前项目需要留痕，默认 review 记录路径为：

- `docs/reviews/traceability-review-<task>.md`

如 `AGENTS.md` 为当前项目声明了等价路径，按其中映射路径保存。

若项目尚未形成固定 review 记录格式，默认使用：

- `skills/mdc-workflow/templates/review-record-template.md`

若需要追溯性专属字段，可在默认模板基础上补充 `references/traceability-review-record-template.md` 中的内容。

如果当前任务正在使用 `task-progress.md` 驱动 workflow，应同步更新：

- `task-progress.md` 中的追溯性评审状态
- 当前任务是否需要回到实现修订，还是可以进入后续验证
- 当前阻塞原因、断链点或待补同步项（如有）

若项目尚未形成固定进度记录格式，默认使用：

- `skills/mdc-workflow/templates/task-progress-template.md`

## 与入口 skill 的结构化衔接

本 skill 的结论会被 `mdc-workflow-starter` 用来决定是进入 `mdc-regression-gate`、回到实现修订，还是在补齐证据链后重试当前评审。

因此除人类可读的评审结论外，还应显式交接：

- `nextNode`：`mdc-regression-gate` | `mdc-implement` | `mdc-traceability-review`
- `blockingReasons`：缺少哪些已批准工件、评审记录、验证证据或同步回写
- `requiredReads`：本轮追溯性评审实际读取的规格、设计、任务、实现、测试与验证证据
- `expectedWrites`：traceability review 记录、`task-progress.md`、必要时待回写的同步项
- `writesScope`：默认是当前 `change workspace`

## 参考资料

如果团队还没有统一的追溯性评审记录格式，可先使用以下模板：

- `references/traceability-review-record-template.md`

## 检查清单

### 1. 规格与设计一致性

- 当前实现是否仍然满足已批准规格？
- 当前实现是否仍然符合已批准设计？

### 2. 任务与实现一致性

- 当前完成项是否能回指到任务计划中的明确任务？
- 是否出现任务之外的无记录行为扩张？

### 3. 测试与验证一致性

- 测试是否覆盖了被声称完成的关键行为？
- 当前验证证据是否能支撑实现结论？

### 4. 漂移与断链

- 是否出现 undocumented behavior？
- 是否出现 orphan code、无对应任务的实现、无对应验证的结论？
- 是否需要回写规格、设计或任务文档以恢复一致性？

## 输出格式

请严格使用以下结构：

```markdown
## 结论

通过 | 需修改 | 阻塞

## 追溯缺口

- 缺口

## 漂移风险

- 风险

## 下一步

`进入后续验证` | `回到实现修订` | `补齐阻塞条件后重试当前评审`

## 阻塞原因

- 无 | 阻塞原因

## 记录位置

- `docs/reviews/traceability-review-<task>.md` 或映射路径

## 结构化交接

- currentWorkspace: <当前 workspace>
- nextNode: `mdc-regression-gate` | `mdc-implement` | `mdc-traceability-review`
- blockingReasons: 无 | <阻塞原因>
- requiredReads: <本轮实际读取的最少证据>
- expectedWrites: <traceability review 路径>, `task-progress.md`, <必要的同步项>
- writesScope: `change workspace`
```

## 判定规则

只有当规格、设计、任务、实现、测试和验证之间的关键链路保持一致，且不存在明显断链或无记录偏离时，才返回 `通过`。

如果存在设计漂移、实现越界、测试无法支撑结论，或需要先补同步记录，则返回 `需修改`。

如果缺少已批准工件、关键评审记录或无法获得必要证据链，则返回 `阻塞`。

## 反模式

- 把追溯性评审做成重复的代码评审
- 只检查代码，不检查任务和规格
- 明显发生偏离，却不记录、不回写
- 因为功能看起来可用就忽略断链问题

## 完成条件

评审结论可以输出在当前对话、评审评论或临时评审记录中，但仍必须给出明确结论、追溯缺口、漂移风险和唯一下一步。

只有在给出明确结论、追溯缺口、漂移风险、记录位置（或等价输出位置）和唯一下一步之后，这个 skill 才算完成。
