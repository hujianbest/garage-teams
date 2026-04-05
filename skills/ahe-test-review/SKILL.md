---
name: ahe-test-review
description: 对已实现任务的测试进行评审，检查新增或变更测试是否体现有效 fail-first、覆盖关键行为、真正有用并足以支撑后续 `ahe-code-review`。适用于 full / standard profile 中 `ahe-bug-patterns` 之后的正式测试质量判断；lightweight 默认跳过，若手动调用则视为补充性评审。
---

# AHE 测试评审

评审当前任务的测试。

在完整 AHE workflow 中，它通常用于 full / standard 正式评审链中的测试质量判断。

## 角色定位

这个 skill 用于判断测试是否真的在验证行为，而不只是给任务表面上加了一层浅覆盖。

它负责：

- 判断 fail-first 是否有效
- 判断测试是否足以支撑对当前实现结果的信任
- 给出能否安全进入 `ahe-code-review` 的测试质量结论

它不替代：

- `ahe-code-review` 的实现质量判断
- `ahe-regression-gate` 的更广义验证执行

## 与 AHE 主链的关系

- 在 full / standard profile 中，通常位于 `ahe-bug-patterns` 之后、`ahe-code-review` 之前
- 在 lightweight profile 中，`ahe-workflow-starter` 默认跳过本节点；若手动调用，应视为补充性评审，而不是改写 workflow canonical state 的正式节点
- 在 full / standard 正式链路中，若测试质量不足，应把下一步写回 `ahe-test-driven-dev`

## Reviewer Subagent 运行约定

本 skill 默认运行在独立 reviewer subagent 中。

当以该模式运行时：

- reviewer 负责读取测试资产、实现交接块和最小必要辅助上下文
- reviewer 负责把评审记录写入约定路径
- reviewer 负责回传结构化摘要
- reviewer 不负责代替父会话推进整个 workflow
- reviewer 不负责代替父会话继续执行 `ahe-code-review`
- reviewer 可以建议下一步，但 canonical workflow state 与 `task-progress.md` 更新归父会话维护

## 适用时机

优先用于以下场景：

- 需要判断当前测试是否足以支撑对实现结果的信任
- 当前任务已经完成一轮最小实现并补充了测试
- 准备从缺陷模式排查进入正式评审链
- 需要判断现有测试是否足以支撑后续代码评审和完成判定

## 高质量评审基线

高质量的 `ahe-test-review` 结果，至少应满足：

- 先消费上游实现交接块和 bug-patterns 记录，而不是脱离上下文做孤立判断
- 不只问“有没有测试”，还要判断 RED / GREEN 是否有效
- 能说明测试到底覆盖了哪些行为、还没覆盖什么、以及为什么这些缺口重要
- 输出能直接被 `ahe-code-review` 或 `ahe-test-driven-dev` 消费

## 输入

阅读以下最少必要信息：

- `AGENTS.md` 中与当前项目相关的 testing 规范（如果存在）
- 当前任务新增或变更的测试
- 当前实现与测试目标
- `ahe-test-driven-dev` 的实现交接块或等价证据
- `ahe-bug-patterns` 记录（如当前链路要求）
- 与这些测试相关的需求、设计或任务背景，以及 fail-first 证据

如果当前上下文无法提供完整规格或设计，至少应提供测试目标、当前实现范围和可核对的失败证据；若无法提供 fail-first 证据，则按证据不足处理。

## Pre-flight

开始评审前，至少固定：

- 当前任务 ID
- 当前 profile
- `AGENTS.md` 中声明的测试命令、测试分层、mock 边界、覆盖要求与 fail-first 例外（如有）
- 上游实现交接块中的 RED / GREEN 证据摘要
- bug-patterns 已识别出的高风险点（如有）
- 当前测试变更涉及的主要行为

## 记录要求

评审完成后，必须将本次结论写入：

- `docs/reviews/test-review-<task>.md`

如 `AGENTS.md` 为当前项目声明了等价路径，按其中映射路径保存。

若项目尚未形成固定 review 记录格式，默认使用：

- `templates/review-record-template.md`

如果当前任务正在使用 `task-progress.md` 驱动 workflow，且当前 profile 是 full / standard，则父会话在消费本 skill 的评审记录与结构化摘要后，应同步更新：

- `task-progress.md` 中的测试评审状态
- 当前任务是否需要回到 `ahe-test-driven-dev`，还是可以进入 `ahe-code-review`
- 当前阻塞原因或待补测试缺口（如有）

若项目尚未形成固定进度记录格式，默认使用：

- `templates/task-progress-template.md`

## 检查维度

### 1. Valid RED / GREEN

评审 fail-first 时，不只看“曾经出现过失败”，而要判断它是否有效：

- RED 是否在当前会话或可信等价证据中真实执行过
- 失败是否准确代表缺失行为，而不是环境噪音、无关编译错误或旧失败
- GREEN 是否来自当前代码状态的新鲜通过结果，而不是旧日志
- 若声称“这个测试会防止回归”，是否能说清没有 fix 时它应继续失败

### 2. 行为价值

- 测试验证的是行为，而不是实现细节吗？
- 断言是否真的能抓到错误，而不是只证明代码跑过了？
- 测试是否映射到了当前任务要交付的关键行为 / 验收点？

### 3. Adequacy 与覆盖形态

- 在适用场景下，是否至少覆盖了关键边界、异常路径或反向场景？
- 当前 `ahe-bug-patterns` 中命中的高风险点，是否真的被测试编码进来了？
- 是否存在明显遗漏，导致测试存在但仍不足以让人信任？

### 4. 测试质量风险

- 过度使用 mock
- 断言过弱
- 命名模糊
- 测试与实现细节耦合过紧
- flake / 不稳定性风险

### 5. AI-assisted blind spots

- 是否存在主路径有测试、旁支路径没有测试的双路径不一致？
- 是否存在跨层传播不完整，导致一层行为更新了、另一层验证仍停留在旧预期？
- 是否存在看起来覆盖了风险，但实际上只验证了最顺路径的情况？

## 检查清单

- 不要跳过上面的结构化维度
- 不要把“有测试”误判成“测试足够好”

## 输出格式

请严格使用以下结构：

```markdown
## 结论

通过 | 需修改 | 阻塞

## 上游已消费证据

- Task ID
- 实现交接块 / 等价证据
- bug-patterns 记录（如适用）

## 发现项

- [严重级别] 问题

## 测试 ↔ 行为映射

- 行为 / 验收点
- 对应测试

## 测试质量缺口

- 条目

## 证伪 / 补强建议

- 建议

## 给 `ahe-code-review` 的提示

- 需继续核对的实现风险
- 哪些测试结论已经足够可信
- 哪些测试缺口可能影响实现级判断

## 下一步

- full / standard：`ahe-code-review` | `ahe-test-driven-dev`
- lightweight 手动调用：记录为 `N/A（补充性评审，不改写 canonical state）`

## 记录位置

- `docs/reviews/test-review-<task>.md` 或映射路径
```

## 判定规则

只有当这些测试对当前任务真正有验证价值时，才返回 `通过`。

如果测试质量太弱、缺少有效 fail-first、或不足以支撑对任务结果的信任，则返回 `需修改`。

如果缺少关键测试上下文、无法判断 fail-first 证据、当前测试资产本身不可读取，或连最基本的行为目标都无法核对，则返回 `阻塞`。

在 full / standard 正式链路中，若缺少当前任务对应的 `ahe-bug-patterns` 记录，或无法把其中命中的高风险点映射到 adequacy 判断，也返回 `阻塞`。

full / standard 中，本 skill 返回 `通过` 后进入 `ahe-code-review`，返回 `需修改` / `阻塞` 时回到 `ahe-test-driven-dev`。

lightweight 手动调用时，应把本次结果视为补充性评审：可以记录发现，但不要改写 workflow canonical `Next Action Or Recommended Skill`。

## 反模式

- 因为“有测试”就直接通过
- 忽略没有失败优先信号的问题
- 把浅层断言当成足够证据
- 不读取上游实现交接块或 bug-patterns 记录，就直接下结论
- 把 test-review 做成第二个 regression gate 或第二个 code review

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

只有在评审记录已经落盘，且给出明确结论、测试质量缺口、给 `ahe-code-review` 的提示和唯一下一步之后，这个 skill 才算完成。

若本 skill 由 reviewer subagent 执行，还应完成对父会话的结构化结果回传。
