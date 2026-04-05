---
name: ahe-finalize
description: 执行正式收尾。适用于 `ahe-completion-gate` 已允许进入 finalize、当前需要把 gate 证据、进度状态、发布说明、文档同步和后续交接收成一套可持续状态的场景；本 skill 只做状态与文档收口，不再混入新的实现工作，若阶段不清或 gate 证据不成立则先回到 `ahe-workflow-starter`。
---

# AHE 收尾

把当前 AHE 工作周期干净地收尾，并沉淀为下一次会话无需猜测即可继续的项目状态。

## Overview

`ahe-finalize` 的目标，是把“已经完成的工作”沉淀为“可持续的项目状态”。

它负责：

- 串起 completion / regression 与当前 profile 下实际存在的证据链
- 更新进度状态、发布说明和最小文档一致性
- 形成可交接的 delivery / handoff pack

它不替代：

- `ahe-regression-gate` / `ahe-completion-gate`
- 新的实现工作
- `ahe-workflow-starter` 的恢复编排权

## When to Use

在这些场景使用：

- `ahe-completion-gate` 已给出允许进入 finalize 的结论
- 当前工作项已经完成，需要同步状态、发布说明、文档和证据索引
- 需要形成 closeout pack，供下一次会话、下一位执行者或用户消费

不要在这些场景使用：

- `ahe-completion-gate` 尚未通过
- 当前还需要补实现或补验证，先回到 `ahe-workflow-starter`
- 当前只是要重新跑 gate，改用对应 gate skill

## Standalone Contract

当用户直接点名 `ahe-finalize` 时，至少确认以下条件：

- 当前任务已经通过完成门禁
- 能读取到 `ahe-completion-gate` 与 `ahe-regression-gate` 的落盘记录
- 能读取当前 profile 下实际适用的 review / verification 结果
- 当前需要的是状态和文档收口，而不是新增实现

若这些前提不满足，不要强行收尾：

- gate 记录缺失、过旧或结论不支持 finalize：先回到 `ahe-workflow-starter`
- 收尾中发现仍需改实现：立即停止 finalize，并回到主链相应节点

## Chain Contract

作为主链节点被串联调用时，默认读取：

- `docs/verification/completion-<task>.md` 或映射路径
- `docs/verification/regression-<task>.md` 或映射路径
- 当前 profile 下实际适用的 review / verification 记录
- `task-progress.md`
- `RELEASE_NOTES.md`
- 与本轮变化直接相关的入口文档

本节点完成后应写回：

- 一份 delivery / handoff pack
- `task-progress.md` 的 closeout 状态
- 必要的发布说明与证据索引
- canonical `Next Action Or Recommended Skill`，或在 workflow 已结束时显式留空 / 使用项目约定 null 值

## Hard Gates

- 没有 completion / regression 的落盘记录，不得声称已经完成收尾。
- 收尾阶段不再混入新的实现工作。
- 如果发现仍需修改实现或补验证，应停止 finalize 并回到 `ahe-workflow-starter` 重新编排。
- 工作流完成是状态，不是 canonical skill；不得伪造新的 downstream skill。

## Quality Bar

高质量的 `ahe-finalize` 结果，至少应满足：

- 完成结论锚定在已经落盘的 completion / regression 记录，而不是会话记忆
- 能区分当前 profile 下哪些证据“应该存在”，哪些是 `N/A`
- `task-progress.md`、`RELEASE_NOTES.md`、相关入口文档和 verification 记录之间没有明显事实冲突
- 输出的不只是总结，而是一份可交接的 delivery / handoff pack
- `Next Action Or Recommended Skill` 使用 starter 认可的 canonical vocabulary；对 finalize 常见场景通常是 canonical `ahe-*` skill ID，若当前工作周期已经结束则留空或按项目约定表示无下一步

## Inputs / Required Artifacts

默认应结合以下状态工件一起完成收尾：

- `task-progress.md`
- `RELEASE_NOTES.md`
- `docs/reviews/`
- `docs/verification/`

Profile-aware 证据矩阵：

| Profile | 收尾时默认应确认的证据 |
|---|---|
| `full` | `ahe-bug-patterns`、`ahe-test-review`、`ahe-code-review`、`ahe-traceability-review`、`ahe-regression-gate`、`ahe-completion-gate` |
| `standard` | `ahe-bug-patterns`、`ahe-test-review`、`ahe-code-review`、`ahe-traceability-review`、`ahe-regression-gate`、`ahe-completion-gate` |
| `lightweight` | `ahe-regression-gate`、`ahe-completion-gate`；其余项应写 `N/A（按 profile 跳过）` |

规则：

- 若当前 profile 是 `full` / `standard`，上述必需 review / gate 记录缺失、过旧或结论不是可进入 finalize 的状态，应停止 finalize 并回到 `ahe-workflow-starter`
- 只有 `lightweight` 才允许把 `ahe-bug-patterns`、`ahe-test-review`、`ahe-code-review`、`ahe-traceability-review` 写成 `N/A（按 profile 跳过）`

## Workflow

### 1. 先读 gate 记录与当前状态

先固定：

- 当前 task / scope
- 当前 workflow profile
- completion gate 结论与记录路径
- regression gate 结论与记录路径
- 当前 profile 下实际存在的 review / verification 记录
- `task-progress.md` 的当前字段

不要只根据聊天内容回忆“应该通过了”。

### 2. 更新进度状态与状态字段

在项目进度记录中补充：

- 已完成任务或范围项
- 日期或会话标记
- 当前状态
- 当前阶段
- 已批准工件摘要
- 本轮 closeout 依赖的 completion / regression 记录
- `Session Log`

关于 `Next Action Or Recommended Skill`：

- 若已经存在明确的下一个合法 AHE 节点，按 `ahe-workflow-starter` 的显式交接值规范写入 canonical 节点名
- 若当前工作周期确实已经结束，不要伪造新的 skill；应在 `Current Stage` 或 closeout 结论中明确“工作流完成”，并让 `Next Action Or Recommended Skill` 留空或按项目约定表示无下一步

### 3. 更新发布说明与最小文档一致性

如果完成的工作影响了用户可见行为，请在发布说明中简要记录：

- 变了什么
- 为什么重要

同时至少检查以下入口文档是否与本轮交付事实一致：

- `RELEASE_NOTES.md`
- `task-progress.md`
- `README.md`（如受影响）
- `AGENTS.md`（如工作方式或入口约定受影响）
- 其它本轮直接引用的使用说明或交接文档

如果发现文档与事实不一致，只修正文档 / 状态，不在 finalize 中补做实现工作。

### 4. 记录证据矩阵与证据位置

记录支持完成结论的证据在哪里：

- 缺陷模式排查结果（如当前 profile / 链路要求）
- 测试评审结果（如适用）
- 代码评审结果（如适用）
- 追溯性评审结果（如适用）
- 回归结果
- 完成门禁结果

如果某项因为 profile 被跳过，写 `N/A（按 profile 跳过）`，不要留成看不出是遗漏还是不适用的空白。

### 5. 产出 delivery / handoff pack

明确说明：

- 哪些内容已经完成
- 用户可见变化是什么
- 已知限制、剩余风险和延后项是什么
- 哪些受影响工件已经同步刷新
- 当前 branch / PR / 集成状态（如项目使用）
- 如果下一次会话继续，推荐的下一步动作或 skill 是什么

如果本轮变更改变了用户如何使用或验证功能，可选补一段简短“使用 / 验证提示”。

### 6. 维护状态收口

确保以下内容已同步：

- `task-progress.md` 中的 `Current Stage`
- `task-progress.md` 中的 `Current Active Task`
- `task-progress.md` 中的 `Next Action Or Recommended Skill`
- `task-progress.md` 中的 `Session Log`
- 与本轮相关的证据索引

若当前主链任务全部完成，应在状态记录中明确标记工作流完成，而不是只在对话中说“结束了”。

## Output Contract

请严格使用以下结构：

```markdown
## 已完成工作

- 已完成项
- 用户可见变化

## 已更新记录

- 已更新记录项
- 已同步文档 / 入口文件

## 证据矩阵

- `ahe-bug-patterns`: 路径 | N/A（理由）
- `ahe-test-review`: 路径 | N/A（理由）
- `ahe-code-review`: 路径 | N/A（理由）
- `ahe-traceability-review`: 路径 | N/A（理由）
- `ahe-regression-gate`: 路径
- `ahe-completion-gate`: 路径

## 证据位置

- 路径

## 交付与交接

- 已知限制 / 剩余风险 / 延后项
- branch / PR / 集成状态（如适用）
- `Current Stage`
- `Current Active Task`
- `Next Action Or Recommended Skill`（仅在存在合法下游 skill 时填写；若 workflow 已结束则留空或按项目约定 null 值）

## 可选使用 / 验证提示

- 如不适用可写 `N/A`
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| “已经做完了，不用再写记录” | 收尾的目标就是把完成状态沉淀为可继续的项目状态。 |
| “这些证据我自己知道在哪，不用写出来” | 证据位置必须显式记录，便于后续追溯。 |
| “下一步别人自己看代码就知道了” | 交接信息必须明确说明下一步和剩余工作。 |
| “发布说明以后再补也没关系” | 只要影响用户可见行为，就应在收尾时同步记录。 |
| “顺手再改一点实现再一起收尾” | 收尾阶段不再混入新的实现工作。 |
| “状态先不更新，后面想起来再说” | 进度状态、同步状态和交接信息必须在当前收尾中完成。 |
| “这些 review 这次没有，是不是漏了” | 先看当前 profile；该有的必须引用，不该有的明确写 `N/A`。 |
| “`Next Action Or Recommended Skill` 先写成 `工作流完成` 就行” | 工作流完成是状态，不是 canonical skill；不要伪造 handoff。 |

## Red Flags

- 宣告完成，却没有更新项目状态
- 把下一任务留成隐含信息
- 对用户可见变化忘记写发布说明
- 明明发生过变更或热修复，却不确认受影响工件是否已同步
- 在收尾过程中混入新的实现工作
- 没有记录证据位置，就直接结束当前会话
- 用会话记忆替代 completion / regression 的落盘记录
- 把 profile 不适用的证据误写成遗漏
- 用自然语言短语替代 canonical `Next Action Or Recommended Skill`
- 没有更新 `task-progress.md` 中的阶段和下一步，却声称已经完成收尾

## Verification

只有在以下条件全部满足时，这个 skill 才算完成：

- [ ] gate 证据已被正确引用
- [ ] `task-progress.md`、`RELEASE_NOTES.md` 与相关入口文档已同步
- [ ] 交接 pack 已形成
- [ ] `Next Action Or Recommended Skill` 已按 canonical contract 填写，或在 workflow 已结束时显式留空 / 使用项目约定 null 值
- [ ] 下一次会话无需猜测就能继续，或能明确知道“本轮已完成”
