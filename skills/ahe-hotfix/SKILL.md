---
name: ahe-hotfix
description: 在不放弃验证纪律的前提下处理紧急缺陷修复。适用于用户明确提出紧急修复、`ahe-workflow-router` 已判定当前属于 hotfix 分支、或某个实现缺陷必须尽快修复但仍需遵守先复现、root cause 收敛、最小安全修复边界和 canonical re-entry handoff 的场景。本 skill 只负责热修分析、状态同步与回流，不直接替代 `ahe-test-driven-dev` 的实现职责。
---

# AHE 热修复

处理紧急缺陷，但不能绕过工程纪律。

## Overview

这个 skill 用来在“必须尽快修复”与“不能跳过验证”之间维持边界。

高质量热修复不只是把问题快速改掉，而是判断：

- 当前问题是否真的是 hotfix，而不是 increment 或路线误判
- 是否已经建立最小且可信的复现证据
- 是否已经收敛 root cause 与最小安全修复边界，从而可以安全交接给 `ahe-test-driven-dev`

## When to Use

在这些场景使用：

- 用户明确提出紧急缺陷修复或线上问题修复
- `ahe-workflow-router` 已判定当前属于 hotfix 分支
- 当前问题本质上是“原本应成立的行为没有被正确实现”
- 当前需要先收敛复现证据、root cause 和 blast radius，再进入实现

不要在这些场景使用：

- 当前问题本质上是需求、范围、验收标准或约束变化，改用 `ahe-increment`
- 当前已经明确进入实现阶段，需要执行修复实现，改用 `ahe-test-driven-dev`
- 当前请求只是阶段不清、profile 不稳或证据链冲突，先回到 `ahe-workflow-router`

## Standalone Contract

当用户直接点名 `ahe-hotfix` 时，至少确认以下条件：

- 存在明确缺陷信号、故障报告、失败现象或线上异常
- 当前目标是恢复原本应成立的行为，而不是改规则或扩范围
- 能读取 `AGENTS.md` 中与紧急修复、验证纪律、风险区域和状态同步有关的约定
- 当前请求确实是分析 / 收敛热修，而不是直接让你改代码

如果前提不满足：

- 当前问题更像需求 / 范围 / 验收变化：回到 `ahe-increment`
- 缺复现线索、缺 route / stage 判断或输入证据冲突：回到 `ahe-workflow-router`
- 已经完成热修分析并需要实际修复实现：回到 `ahe-test-driven-dev`

## Chain Contract

当本 skill 作为分支节点被带入时，默认在父会话 / 当前执行上下文中运行，而不是按 reviewer subagent return contract 消费。

默认读取：

- 当前缺陷描述、失败证据、环境 / 版本 / 提交信息（若存在）
- 当前任务相关的规格、设计、任务上下文与最近实现证据（如有）
- `AGENTS.md` 中与 hotfix、验证纪律、回滚 / feature flag、监控关注点和状态同步有关的约定
- `task-progress.md` 中的 `Workflow Profile`、`Current Stage`、`Current Active Task` 与 `Pending Reviews And Gates`（如果存在）

本节点完成后应写回：

- 热修复记录
- 当前复现状态、root cause 状态与最小安全修复边界
- canonical `Next Action Or Recommended Skill`
- 需要恢复的 review / gate 线索与状态同步项

这个 skill 的职责是把问题安全交回唯一实现节点或正确上游分支，而不是自己继续实现或内联执行后续 review / gate。

一旦后续恢复到 review / gate 节点，其执行归父会话或 `ahe-workflow-router` 负责：review 节点按 review dispatch protocol 派发 reviewer subagent，gate 节点由父工作流按当前 workflow 约定执行。

## Hard Gates

- 在建立最小可信复现路径前，不得把当前 hotfix 交接给 `ahe-test-driven-dev`。
- 在确认 root cause 和最小安全修复边界前，不得把当前 hotfix 视为已准备好进入实现。
- 如果当前输入工件还不足以判定 stage / route，不直接开始 hotfix 分析。
- `ahe-hotfix` 不直接写生产代码，也不替代后续 `ahe-bug-patterns`、`ahe-test-review`、`ahe-code-review`、`ahe-traceability-review`、`ahe-regression-gate` 或 `ahe-completion-gate`。

## Quality Bar

高质量热修复结果至少应做到：

- 不是凭直觉认定“这是 hotfix”，而是有明确缺陷信号与紧急性依据
- 在进入实现前，已经留下最小且可靠的复现方式与失败签名
- root cause 不是模糊症状，而是一句可被挑战的结论
- blast radius、最小安全修复边界、回滚 / feature flag / 监控关注点已经被显式收敛
- 写回的 re-entry handoff 能被 `ahe-test-driven-dev` 或 `ahe-workflow-router` 直接消费

## Inputs / Required Artifacts

热修分析完成后，至少应将本次结论写入以下工件之一：

- `docs/reviews/hotfix-<topic>.md`
- 项目既有的缺陷修复记录路径
- `task-progress.md` 中的等价状态字段

如 `AGENTS.md` 为当前项目声明了等价路径，按其中映射路径保存。

如果团队还没有统一的热修复记录格式，可先使用以下模板：

- `skills/ahe-hotfix/references/hotfix-repro-and-sync-record-template.md`

无论当前是否已经进入实现，至少应同步：

- `Workflow Profile`
- `Current Stage`
- `Current Active Task` 或显式 hotfix-task 映射
- `Pending Reviews And Gates`
- 当前复现状态
- 当前 root cause 是否已确认
- 当前最小修复边界与 out-of-scope
- `Next Action Or Recommended Skill`

## Workflow

### 1. 先固定分支判断与证据基线

在给出结论前，先读取并固定以下证据来源：

- 缺陷描述、失败证据、环境 / 版本 / 提交信息
- 当前任务相关的规格、设计、任务上下文与最近实现证据（如有）
- `AGENTS.md` 中与 hotfix、验证纪律、回滚 / feature flag、监控关注点和状态同步有关的约定
- `task-progress.md` 中的 `Workflow Profile`、`Current Stage`、`Current Active Task` 与 `Pending Reviews And Gates`（如果存在）

先回答：

- 期望行为是什么
- 实际行为是什么
- 为什么当前判断更像 hotfix，而不是 increment
- 当前影响面与紧急性依据是什么

### 2. 建立最小且可信的复现方式

优先建立最小且可靠的失败复现方式：

- 优先复用现有测试、现有验证入口或无需改文件的失败验证步骤
- 否则至少提供可复用的手工复现步骤，并把它写成后续测试设计种子

在说“问题已确认存在”之前，至少留下：

- 命令或操作入口
- 运行环境
- 失败签名或关键异常
- 一段足以复用的证据摘要

如果无法稳定复现，不要硬进入实现。记录证据缺口，并把唯一下一步指向 `ahe-workflow-router` 以决定是否等待更多证据、改走其它分支或暂停。

### 3. 收敛 root cause 与最小安全修复边界

在进入实现前，至少完成：

1. 提出一个当前最强假设
2. 设计一个最小验证去挑战它
3. 根据验证结果收敛或否定假设
4. 给出一句已确认 root cause
5. 锁定本次最小安全修复边界

同时显式写明：

- 本次明确不做什么
- 可能影响哪些模块 / 文件 / 路径
- 是否有回滚手段、feature flag 或临时缓解策略
- 修复后应重点观察哪些监控或验证点

### 4. 决定唯一 re-entry 节点

下一步规则：

- 已完成复现、确认 root cause、锁定最小安全修复边界：`ahe-test-driven-dev`
- 发现问题本质上是需求 / 范围 / 验收变化：`ahe-increment`
- 证据不足、route / stage / profile 不清、或当前不应继续 hotfix：`ahe-workflow-router`

如果需要提前表达后续质量关注点，应把它们写成：

- `Pending Reviews And Gates`
- 风险提示
- 监控 / 验证关注点

不要把当前会话描述成会顺手继续执行下游 review / gate。

### 5. 写回 fresh evidence 与状态同步

至少写明：

1. 当前复现状态
2. 已确认 root cause 或当前证据缺口
3. 本次最小修复的范围边界
4. 最新分析 / 验证证据
5. 唯一 canonical `Next Action Or Recommended Skill`

如果热修暴露出规格、设计、任务、发布说明或状态记录已过时，也应把“哪些工件后续需要同步”一并写回，而不是留在聊天里。

## Output Contract

热修记录正文请严格使用以下结构：

```markdown
## 热修复摘要

- Hotfix ID / Task ID
- 严重级别与影响面
- 当前判断：真实 hotfix | 更像 increment | 证据不足暂停

## 复现方式

- 环境 / 提交 / 版本
- 复现步骤或命令
- 失败签名
- 最新证据摘要

## Root Cause

- 当前假设
- 已确认 root cause
- 若尚未确认，当前证据缺口

## 修复范围

- 最小安全修复边界
- 明确不做的内容
- Blast Radius
- 回滚 / Feature Flag / 缓解手段
- 建议优先验证的测试设计种子

## 状态同步

- `Workflow Profile`
- `Current Stage`
- `Current Active Task` 或 hotfix-task 映射
- `Pending Reviews And Gates`
- 当前复现状态
- 当前监控 / 验证关注点

## 交接字段

- `Next Action Or Recommended Skill`: `ahe-test-driven-dev` | `ahe-increment` | `ahe-workflow-router`
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| “这是线上问题，先改了再说” | 热修也必须先复现，再进入实现。 |
| “现在来不及确认 root cause” | 没有 root cause 与修复边界，热修只会扩大 blast radius。 |
| “先把问题压住，回头再补验证” | 修复后仍要恢复正式质量链，不能把补验证当成可选项。 |
| “这可能是预期变了，但先按 hotfix 处理” | 若本质是规则 / 范围变化，应退出到 `ahe-increment`。 |
| “下一步写自然语言就行，starter 会猜” | `Next Action Or Recommended Skill` 应优先写 canonical `ahe-*` skill ID。 |

## Red Flags

- 在没有失败复现证据时直接准备改实现
- 在没有确认 root cause 时直接推进到代码修复
- 明明无法稳定复现，却假装已经准备好进入实现
- 在热修中夹带无关清理工作
- 把本应进入 `ahe-increment` 的范围变更偷偷包进 hotfix
- `Next Action Or Recommended Skill` 写成自由文本

## Verification

只有在以下三种情况之一成立时，这个 skill 才算完成：

- [ ] 已成功复现缺陷，确认 root cause，锁定最小修复边界，并写回唯一合法的 `Next Action Or Recommended Skill`
- [ ] 已明确判断当前问题本质上是范围 / 验收 / 规则变化，而不是实现缺陷，并把状态同步字段与唯一下一步显式写回 `ahe-increment`
- [ ] 已明确记录“当前无法稳定复现或证据不足”的阻塞状态、证据缺口与状态同步字段，并把下一步显式交回 `ahe-workflow-router`
