---
name: ahe-tasks-review
description: 评审 AHE 任务计划，判断它是否已经拆成可执行、可验证、顺序正确的任务单元，并可进入真人确认与 `ahe-test-driven-dev`；若阶段不清、上游证据冲突或任务计划只是实现愿望清单，先回到 `ahe-workflow-router`。
---

# AHE 任务计划评审

评审任务计划，并判断它是否已经可以提交给真人确认，作为进入 `ahe-test-driven-dev` 的候选已批准输入。

## Overview

这个 skill 用来防止任务计划失真。

高质量任务评审不只是判断“任务已经列出来”，而是判断：

- 任务是否真正建立在已批准规格和已确认设计之上
- 任务拆分是否足够小、顺序是否正确、依赖是否清楚
- 测试、验证与交接点是否已经明确到可以安全进入实现

## When to Use

在这些场景使用：

- `ahe-tasks` 已完成任务计划，需要正式 review verdict
- 用户明确要求“review 这份 tasks / plan”
- reviewer subagent 被父会话派发来执行任务计划评审

不要在这些场景使用：

- 当前需要的是继续写或修任务计划，改用 `ahe-tasks`
- 当前需要的是开始实现，改用 `ahe-test-driven-dev`
- 当前发现规格、设计、route 或阶段判断不稳定，先回到 `ahe-workflow-router`

## Standalone Contract

当用户直接点名 `ahe-tasks-review` 时，至少确认以下条件：

- 存在当前任务计划
- 存在已批准规格
- 存在已批准或已确认可作为任务输入的设计
- 能读取 `AGENTS.md` 中与任务状态、路径映射和实现入口有关的约定
- 当前请求确实是评审，而不是继续拆解任务或直接编码

如果前提不满足：

- 缺任务计划或只是需要继续拆任务：回到 `ahe-tasks`
- 缺设计、缺上游批准输入、阶段不清或证据冲突：回到 `ahe-workflow-router`

## Chain Contract

当本 skill 作为链路节点被带入时，默认由 reviewer subagent 执行，并读取：

- 已批准规格
- 已批准或已确认的设计
- 当前任务计划
- `AGENTS.md` 中与任务状态、路径映射和实现入口有关的约定
- `task-progress.md` 中的 `Current Stage`、`Current Active Task` 与 `Workflow Profile`（如果存在）
- 理解任务计划所需的最少项目上下文

本节点完成后应写回：

- review 记录正文
- 结构化 reviewer 返回摘要
- canonical `next_action_or_recommended_skill`

评审记录落盘与结构化摘要由 reviewer 负责；真正向真人展示结论、推进批准确认和恢复主链，仍由父会话负责。

## Hard Gates

- 在任务计划通过评审并完成真人确认之前，不得进入 `ahe-test-driven-dev`。
- 如果当前输入工件还不足以判定 stage / route，不直接开始任务评审。
- reviewer 不负责代替父会话发起真人确认，也不顺手锁定 `Current Active Task` 或开始实现。

## Quality Bar

交付给真人确认前，高质量评审结果至少应做到：

- 明确指出任务是否忠实覆盖已批准规格和设计
- 明确指出任务顺序、依赖关系和里程碑是否合理
- 明确指出每个关键任务是否具备验证方式或测试设计种子
- 识别出会污染 `ahe-test-driven-dev` 的模糊任务、过大任务或顺序错误
- 给出唯一下一步，并与实现入口契约保持一致

## Inputs / Required Artifacts

评审完成后，必须将本次结论写入：

- `docs/reviews/tasks-review-<topic>.md`

如 `AGENTS.md` 为当前项目声明了等价路径，按其中映射路径保存。

若项目尚未形成固定 review 记录格式，默认使用：

- `templates/review-record-template.md`

如果使用通用模板中的英文结论字段，请按以下方式映射：

- `通过` -> `pass`
- `需修改` -> `revise`
- `阻塞` -> `blocked`

如果当前任务正在使用 `task-progress.md` 驱动 workflow，且真人确认通过，还应同步更新：

- 任务计划中的状态字段
- `task-progress.md` 中的 `Current Stage`
- `task-progress.md` 中的 `Next Action Or Recommended Skill`

这些状态字段更新由父会话在真人确认通过后执行；reviewer subagent 不代替父会话写入批准结论或锁定权威版 `Current Active Task`。

若项目尚未形成固定进度记录格式，默认使用：

- `templates/task-progress-template.md`

## Workflow

### 1. 先建立证据基线

在给出结论前，先读取并固定以下证据来源：

- 已批准规格
- 已批准或已确认的设计
- 当前任务计划
- `AGENTS.md` 中的任务、路径和状态约定
- `task-progress.md` 中的 `Current Stage`、`Current Active Task` 与 `Workflow Profile`（如果存在）
- 理解任务执行上下文所需的最少项目信息

不要只根据“任务看起来合理”或“用户已经口头同意”判断可以进入实现。

### 2. 做多维评分与挑战式审查

在形成最终结论前，至少对以下维度做内部评分，评分范围 `0-10`：

- 上游覆盖与追溯
- 任务拆分粒度
- 顺序与依赖合理性
- 验证与测试准备度
- 实现入口准备度

判定辅助规则：

- 任一关键维度低于 `6/10` 时，不得返回 `通过`
- 任一维度低于 `8/10` 时，通常至少应对应一条具体发现项或薄弱点

### 3. 按 checklist 做正式审查

#### 3.1 上游覆盖与追溯

- 任务是否覆盖了规格与设计中的关键范围？
- 关键任务能否回指到具体需求、设计决策、接口或模块？
- 是否存在关键范围没有被任务承接？
- 是否存在脱离规格和设计的“想做项”或实现愿望清单？

#### 3.2 任务拆分粒度

- 任务单元是否足够小到可以执行、验证并回写结果？
- 是否避免把多个高风险变化塞进同一个任务？
- 是否避免把“完成整个模块”这类过大任务当作单一执行单元？

#### 3.3 顺序与依赖合理性

- 任务顺序是否符合真实依赖？
- 是否先处理 prerequisite，再处理依赖其结果的下游任务？
- 是否说明了关键并行边界和串行边界？
- 是否会因为顺序错误导致返工或无法验证？

#### 3.4 验证与测试准备度

- 每个关键任务是否说明了验证方式、测试思路或验收信号？
- 高风险任务是否附带更强验证要求？
- 是否存在无法判断完成与否的任务描述？

#### 3.5 实现入口准备度

- 任务计划是否已经清楚到足以锁定 `Current Active Task`？
- 首个活动任务是否具备明确输入、动作和预期输出？
- 是否已经说明进入 `ahe-test-driven-dev` 前后所需的交接信息？
- 是否还存在会让实现阶段被迫重新做设计判断的空洞？

### 4. 形成 verdict、severity 与下一步

severity 统一使用：

- `critical`: 阻塞实现入口，或会直接导致错误执行顺序
- `important`: 应在批准前修复
- `minor`: 不阻塞，但建议改进

判定规则：

- 只有在任务计划忠实覆盖已批准规格与设计、拆分粒度合理、顺序和依赖正确、关键验证方式存在、且至少可以清楚锁定首个活动任务时，才返回 `通过`
- 核心拆分可用但仍有粒度不均、验证描述偏弱、顺序说明不足或少量遗漏时，返回 `需修改`
- 缺失上游追溯、任务过大或顺序明显错误、无法锁定实现入口、或 route / stage / 证据链冲突时，返回 `阻塞`

### 5. 写 review 记录并回传父会话

- 若结论为 `通过`，下一步为 `任务真人确认`，`needs_human_confirmation=true`
- 若结论为 `需修改`，下一步为 `ahe-tasks`
- 若结论为 `阻塞` 且问题属于任务计划内容本身，下一步为 `ahe-tasks`
- 若结论为 `阻塞` 且问题属于上游规格 / 设计缺失、route / stage / 证据冲突，下一步为 `ahe-workflow-router`，并设置 `reroute_via_starter=true`

## Output Contract

review 记录正文请严格使用以下结构：

```markdown
## 结论

通过 | 需修改 | 阻塞

## 发现项

- [critical|important|minor] 问题

## 任务计划薄弱点

- 条目

## 下一步

- `通过`：`任务真人确认`
- `需修改`：`ahe-tasks`
- `阻塞`：`ahe-tasks` 或 `ahe-workflow-router`

## 记录位置

- `docs/reviews/tasks-review-<topic>.md` 或映射路径

## 交接说明

- `任务真人确认`：仅当结论为 `通过`
- `ahe-tasks`：用于回修任务计划
- `ahe-workflow-router`：仅在上游输入失稳或 route / stage / 证据链冲突时使用
```

若本 skill 运行在 reviewer subagent 中，`next_action_or_recommended_skill` 必须只写一个 canonical 值，不得把多个候选值拼在同一个字符串里。

最小返回示例：

```json
{
  "conclusion": "通过",
  "next_action_or_recommended_skill": "任务真人确认",
  "record_path": "实际写入的 review 记录路径",
  "key_findings": ["关键发现 1", "关键发现 2"],
  "needs_human_confirmation": true,
  "reroute_via_starter": false
}
```

返回规则：

- `通过`：`next_action_or_recommended_skill=任务真人确认`，`needs_human_confirmation=true`
- `需修改`：`next_action_or_recommended_skill=ahe-tasks`，`needs_human_confirmation=false`
- `阻塞` 且属于任务计划内容回修：`next_action_or_recommended_skill=ahe-tasks`，`needs_human_confirmation=false`
- `阻塞` 且属于上游规格 / 设计缺失、route / stage / 证据链冲突：`next_action_or_recommended_skill=ahe-workflow-router`，`needs_human_confirmation=false`，`reroute_via_starter=true`

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| “任务列出来就能开工了” | 列表不等于可执行计划。 |
| “大任务实现时再拆” | 过大的任务会让 `Current Active Task` 无法稳定锁定。 |
| “测试等实现时再补” | 没有验证方式的任务无法判断完成，也会污染 TDD 入口。 |
| “顺序差一点没关系，做的时候再调整” | 顺序错误会直接带来返工与假进展。 |
| “review 先过，真人再帮忙挑问题” | reviewer 的职责是先把任务计划收敛到可确认状态。 |
| “顺手指定第一条任务并开始做更高效” | reviewer 负责 gate，不负责代替实现节点开工。 |

## Red Flags

- 接受无法追溯到规格或设计的任务项
- 接受“实现整个功能”这类过大任务
- 忽略首个活动任务仍然模糊不清
- 忽略缺失的验证方式或测试种子
- 任务评审刚返回“通过”就直接进入 `ahe-test-driven-dev`
- 不经过真人确认，就把任务计划当成已批准输入

## Verification

只有在以下条件全部满足时，这个 skill 才算完成：

- [ ] 评审记录已经落盘
- [ ] 给出明确结论、发现项、薄弱点和唯一下一步
- [ ] 结构化 reviewer 返回摘要已使用 `next_action_or_recommended_skill`
- [ ] 若结论为 `通过`，已明确要求进入 `任务真人确认`
- [ ] 若本 skill 由 reviewer subagent 执行，已完成对父会话的结构化结果回传
