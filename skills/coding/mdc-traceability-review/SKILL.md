---
name: mdc-traceability-review
description: 在代码评审之后、回归门禁之前，检查需求、设计、任务、实现、测试与验证证据之间是否仍然一致。适用于功能实现已经成形，需要确认没有无记录偏离、设计漂移或验证断链的场景。
---

# MDC 可追溯性评审

检查规格、设计、任务、实现与验证之间是否仍然对齐。

## 目的

这个 skill 用于防止“代码能跑，但和原本批准的东西已经不是一回事”。

它关注的是一致性和追溯性，而不是代码风格或实现技巧。

## 适用时机

优先用于以下场景：

- 当前任务已完成代码评审，准备进入回归门禁
- 当前改动涉及用户可见行为、接口变化或复杂业务规则
- 当前任务在实现过程中发生过设计调整或需求收敛
- 热修复、增量变更后需要确认工件链路仍然一致

## 输入

阅读以下最少必要信息：

- 已批准规格中的相关片段
- 已批准设计中的相关片段
- 当前任务计划与完成项
- 当前实现改动、测试变更与已有评审结果

## 记录要求

默认 review 记录路径为：

- `docs/reviews/traceability-review-<task>.md`

如项目已有等价路径，可按 `mdc-contract` 映射路径保存。

若项目尚未形成固定 review 记录格式，默认使用：

- `skills/coding/templates/review-record-template.md`

若需要追溯性专属字段，可在默认模板基础上补充 `references/traceability-review-record-template.md` 中的内容。

如果结论为 `通过`，应同步更新：

- `task-progress.md` 中的追溯性评审状态
- `task-progress.md` 的 Next Skill 为 `mdc-regression-gate`

如果结论为 `需修改`，应同步更新：

- 当前任务需要回到实现修订
- `task-progress.md` 的 Next Skill 为 `mdc-implement`

如果结论为 `阻塞`，应同步更新：

- `task-progress.md` 中的追溯性评审阻塞状态与原因
- `task-progress.md` 的 Next Skill 暂时保持为 `mdc-traceability-review`

若项目尚未形成固定进度记录格式，默认使用：

- `skills/coding/templates/task-progress-template.md`

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

`mdc-regression-gate` | `mdc-implement` | `补齐阻塞条件后重试 mdc-traceability-review`

## 记录位置

- `docs/reviews/traceability-review-<task>.md` 或映射路径
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

只有在给出明确结论、追溯缺口、漂移风险、记录位置和唯一下一步之后，这个 skill 才算完成。
