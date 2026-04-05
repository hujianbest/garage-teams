---
name: ahe-traceability-review
description: 检查规格、设计、任务、实现、测试与验证证据之间是否仍然一致，用于确认当前改动没有无记录偏离、设计漂移或验证断链，并判断其是否足以进入 `ahe-regression-gate`。适用于 full / standard profile 中 `ahe-code-review` 之后的正式 evidence-chain 判断；若阶段不清、批准缺失或证据链冲突，先回到 `ahe-workflow-starter` 或 `ahe-test-driven-dev`。
---

# AHE 可追溯性评审

评审规格、设计、任务、实现、测试与验证证据之间的链路，并判断它是否已经足够闭合，可以进入 `ahe-regression-gate`。

## Overview

这个 skill 用来防止“代码能跑，但和已批准工件已经不是同一件事”。

高质量追溯性评审不只是判断“文档大体还在”，而是判断：

- 规格、设计、任务、实现与验证是否还能互相回指
- 当前完成声明是否被最新证据直接支撑
- 当前链路是否已经足够健康，可以进入回归门禁

## When to Use

在这些场景使用：

- `ahe-code-review` 已完成，准备判断 evidence-chain 是否足以进入 `ahe-regression-gate`
- 用户明确要求“review 当前改动是否仍可追溯”
- reviewer subagent 被父会话派发来执行追溯性评审
- 在 `lightweight` profile 中，`ahe-workflow-starter` 通常跳过本节点；若手动调用，应视为补充性评审

不要在这些场景使用：

- 当前需要继续修实现、补记录或补测试，改用 `ahe-test-driven-dev`
- 当前需要执行新鲜验证，改用 `ahe-regression-gate`
- 当前请求只是阶段不清、批准状态不明或证据链冲突，先回到 `ahe-workflow-starter`

## Standalone Contract

当用户直接点名 `ahe-traceability-review` 时，至少确认以下条件：

- 存在当前实现范围与当前完成声明
- 存在至少一组可核对的规格 / 设计 / 任务 / 测试 / 验证依据
- 能读取 `AGENTS.md` 中与批准规则、工件路径、状态字段和 review 约定有关的内容
- 当前请求确实是评审链路一致性，而不是继续修实现

如果前提不满足：

- 缺工件链、缺实现范围或本质上需要继续补证据 / 修实现：回到 `ahe-test-driven-dev`
- 缺 route / stage 判断、批准状态不清或输入证据冲突：回到 `ahe-workflow-starter`

## Chain Contract

当本 skill 作为链路节点被带入时，默认由 reviewer subagent 执行，并读取：

- 当前实现交接块或等价证据
- `ahe-bug-patterns` 记录（full / standard 正式链路）
- `ahe-test-review` 与 `ahe-code-review` 记录
- 当前任务相关的规格、设计和任务锚点
- 当前测试变更与已有验证证据
- `AGENTS.md` 中与批准规则、工件位置、状态字段和 review 规范有关的约定
- `task-progress.md` 中的 `Current Stage`、`Current Active Task`、`Workflow Profile` 与 `Next Action Or Recommended Skill`（如果存在）

本节点完成后应写回：

- review 记录正文
- 结构化 reviewer 返回摘要
- canonical `next_action_or_recommended_skill`

评审记录落盘与结构化摘要由 reviewer 负责；真正推进 `ahe-regression-gate`、回到实现修订或触发重编排，仍由父会话负责。

结构化返回字段定义以 `skills/ahe-workflow-starter/references/reviewer-return-contract.md` 为准。

## Hard Gates

- 在追溯性评审通过前，不得把当前任务视为已准备好进入 `ahe-regression-gate`。
- 如果当前输入工件还不足以判定 stage / route，不直接开始追溯性评审。
- reviewer 不负责补工件、伪造批准证据、继续执行 `ahe-regression-gate`，也不代替父会话推进主链。

## Quality Bar

高质量追溯性评审结果至少应做到：

- 明确指出断链发生在哪一段，而不是只说“整体不一致”
- 区分“实现 / 记录可以补齐的缺口”与“必须回 starter 重编排的上游问题”
- 不把 code review 或 regression gate 的职责提前吞进来
- 给 `ahe-regression-gate` 留下可消费的完成范围与证据边界
- 给出唯一下一步，并与 shared reviewer return contract 保持一致

## Inputs / Required Artifacts

评审完成后，必须将本次结论写入：

- `docs/reviews/traceability-review-<task>.md`

如 `AGENTS.md` 为当前项目声明了等价路径，按其中映射路径保存。

若项目尚未形成固定 review 记录格式，默认使用：

- `templates/review-record-template.md`

如果使用通用模板中的英文结论字段，请按以下方式映射：

- `通过` -> `pass`
- `需修改` -> `revise`
- `阻塞` -> `blocked`

如果当前任务正在使用 `task-progress.md` 驱动 workflow，且当前 profile 是 full / standard，则父会话在消费本 skill 的评审记录与结构化摘要后，还应同步更新：

- `task-progress.md` 中的追溯性评审状态
- `task-progress.md` 中的 `Next Action Or Recommended Skill`
- 当前断链点、待补同步项、阻塞原因或重编排说明（如有）

这些状态字段更新由父会话在消费 reviewer 返回后执行；reviewer subagent 不代替父会话改写权威流程状态。

若项目尚未形成固定进度记录格式，默认使用：

- `templates/task-progress-template.md`

## Workflow

### 1. 先建立证据基线

在给出结论前，先读取并固定以下证据来源：

- 当前实现交接块或等价证据
- `ahe-bug-patterns` 记录（full / standard 正式链路）
- `ahe-test-review` 与 `ahe-code-review` 记录
- 当前任务相关的规格、设计和任务锚点
- 当前测试变更与已有验证证据
- `AGENTS.md` 中与批准、工件路径和状态字段有关的约定
- `task-progress.md` 中的 `Current Stage`、`Current Active Task`、`Workflow Profile` 与 `Next Action Or Recommended Skill`（如果存在）

不要只根据“功能现在能用”或聊天里的口头确认判断链路闭合。

### 2. 做多维评分与挑战式审查

在形成最终结论前，至少对以下维度做内部评分，评分范围 `0-10`：

- 规格 -> 设计承接度
- 设计 -> 任务承接度
- 任务 -> 实现承接度
- 实现 -> 测试 / 验证承接度
- 状态工件与完成声明一致性

判定辅助规则：

- 任一关键维度低于 `6/10` 时，不得返回 `通过`
- 任一维度低于 `8/10` 时，通常至少应对应一条具体发现项或断链点

### 3. 按 checklist 做正式审查

#### 3.1 规格 -> 设计

- 当前实现所对应的设计，是否仍承接了已批准规格中的关键行为、约束和边界？
- 是否出现规格或设计一端变化而另一端没同步的 silent drift？

#### 3.2 设计 -> 任务

- 当前任务计划是否覆盖了设计要求中的关键实现点与完成条件？
- 是否出现“设计有要求，但任务没拆到”或“任务做了设计没承认的额外内容”？

#### 3.3 任务 -> 实现

- 当前完成项是否能回指到任务计划中的明确任务？
- 是否出现无记录行为扩张、隐式范围增加或 undocumented behavior？

#### 3.4 实现 -> 测试 / 验证

- 测试与已有验证证据，是否真的支撑了当前实现被声称完成的行为？
- 是否出现 orphan code、无对应验证的结论，或“代码改了但验证记录还停留在旧状态”的情况？

#### 3.5 状态工件与完成声明

- `task-progress.md`、相关状态字段或用户可见交付说明是否与当前完成声明一致？
- 若这些同步问题超出本节点范围，是否已被明确记录为待补项，而不是被假装忽略？

### 4. 形成 verdict、severity 与下一步

severity 统一使用：

- `critical`: 阻塞回归门禁，或当前完成声明缺少基本证据支撑
- `important`: 应在进入 `ahe-regression-gate` 前修复
- `minor`: 不阻塞，但建议改进

判定规则：

- 只有在规格、设计、任务、实现、测试和验证之间的关键链路保持一致，且不存在会误导回归门禁的明显断链时，才返回 `通过`
- 存在可由实现 / 记录同步补齐的追溯缺口、设计漂移或验证断层，但总体链路仍可被一轮定向修复收敛时，返回 `需修改`
- 缺少已批准工件、缺少关键评审记录、无法获得必要证据链，或 route / stage / profile / 批准状态冲突时，返回 `阻塞`

### 5. 写 review 记录并回传父会话

- 若结论为 `通过`，下一步为 `ahe-regression-gate`，`needs_human_confirmation=false`
- 若结论为 `需修改`，下一步为 `ahe-test-driven-dev`
- 若结论为 `阻塞` 且问题属于实现 / 记录同步修订类，下一步为 `ahe-test-driven-dev`
- 若结论为 `阻塞` 且问题属于 stage / route / profile / 批准状态 / 上游证据冲突，下一步为 `ahe-workflow-starter`，并设置 `reroute_via_starter=true`

## Output Contract

review 记录正文请严格使用以下结构：

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
- 状态工件 / 完成声明：通过 | 需修改 | 阻塞 | `N/A`

## 追溯缺口

- 缺口

## 漂移风险

- 风险

## 下一步

- `通过`：`ahe-regression-gate`
- `需修改`：`ahe-test-driven-dev`
- `阻塞`：`ahe-test-driven-dev` 或 `ahe-workflow-starter`

## 记录位置

- `docs/reviews/traceability-review-<task>.md` 或映射路径
```

若本 skill 运行在 reviewer subagent 中，`next_action_or_recommended_skill` 必须只写一个 canonical 值，不得把多个候选值拼在同一个字符串里。

最小返回示例：

```json
{
  "conclusion": "通过",
  "next_action_or_recommended_skill": "ahe-regression-gate",
  "record_path": "实际写入的 review 记录路径",
  "key_findings": ["关键发现 1", "关键发现 2"],
  "needs_human_confirmation": false,
  "reroute_via_starter": false
}
```

返回规则：

- `通过`：`next_action_or_recommended_skill=ahe-regression-gate`，`needs_human_confirmation=false`
- `需修改`：`next_action_or_recommended_skill=ahe-test-driven-dev`，`needs_human_confirmation=false`
- `阻塞` 且属于实现 / 记录同步修订类：`next_action_or_recommended_skill=ahe-test-driven-dev`，`needs_human_confirmation=false`
- `阻塞` 且属于 route / stage / profile / 批准状态 / 上游证据冲突：`next_action_or_recommended_skill=ahe-workflow-starter`，`needs_human_confirmation=false`，`reroute_via_starter=true`

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| “功能现在能用了，链路应该也没问题” | 可用不等于可追溯，完成声明必须能回指到已批准工件与最新证据。 |
| “这些文档同步问题 finalize 再补就行” | 若同步缺口会影响当前完成声明，就不该拖到 finalize。 |
| “code review 已经看过设计漂移了，这里不用再查” | code review 不替代 evidence-chain 闭环。 |
| “只要 task-progress 写得像完成就够了” | 状态字段必须与规格、设计、任务和验证证据同时一致。 |
| “先过 regression 再说” | regression gate 不是替代追溯性评审的地方。 |

## Red Flags

- 不读上游评审记录就直接下 traceability 结论
- 把聊天记录当成批准证据
- 只检查代码，不检查规格 / 设计 / 任务锚点
- 明显发生偏离，却不记录断链点
- 返回多个候选下一步，而不是唯一 canonical handoff

## Verification

只有在以下条件全部满足时，这个 skill 才算完成：

- [ ] 评审记录已经落盘
- [ ] 给出明确结论、链路矩阵、追溯缺口和唯一下一步
- [ ] 结构化 reviewer 返回摘要已使用 `next_action_or_recommended_skill`
- [ ] 若本 skill 由 reviewer subagent 执行，已完成对父会话的结构化结果回传
- [ ] 当前结论已经足以让父会话判断是进入 `ahe-regression-gate`、回到 `ahe-test-driven-dev`，还是回到 `ahe-workflow-starter`
