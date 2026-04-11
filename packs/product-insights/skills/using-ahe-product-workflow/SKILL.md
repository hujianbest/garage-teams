---
name: using-ahe-product-workflow
description: Provides the public entrypoint to the AHE product insight family. Use when the user has an idea, product direction, or finished project that feels generic, unclear, or weak in value proposition, and you need to decide whether to reframe the outcome, mine insights, map opportunities, shape a wedge, design probes, or bridge into `ahe-coding-skills`.
---

# Using AHE Product Workflow

## Overview

这个 skill 是 `ahe-product-skills/` 的公开入口层。

它的目标不是直接写规格，也不是替 `ahe-coding-skills/` 做实现前置治理；它负责先判断：

- 当前更缺 `问题定义`
- 还是更缺 `外部 / GitHub / 用户信号`
- 还是更缺 `机会优先级`
- 还是更缺 `差异化概念`
- 还是更缺 `低成本验证`
- 还是已经可以整理成 `spec bridge`

## When to Use

在这些场景使用：

- 用户只有一个模糊产品想法，不知道真正的机会在哪里
- 项目已经做完，但“很一般”“没吸引力”，需要重写问题定义
- 用户说“先别写代码，先帮我想清楚产品洞察”
- 你需要判断现在该进入哪一个 product insight 节点
- 你想把更有创造性的上游工作，和后面的 `ahe-coding-skills` 精确实现链路分开

不要在这些场景使用：

- 已经有稳定需求规格，当前只是要继续写设计、任务或实现
- 当前只是要求 `ahe-coding-skills` 节点级工作
- 当前只是回答一个局部技术问题

## Node Selection

按下面规则选节点。

### 进入 `ahe-outcome-framing`

满足任一条件即可：

- 用户的问题描述仍停留在“我要做一个 X”
- 还说不清 desired outcome、目标用户、当前替代方案或非目标
- 项目“为什么不吸引人”还停留在感觉层

### 进入 `ahe-insight-mining`

满足任一条件即可：

- 已经有想法，但缺真实外部信号来判断是否 commodity
- 需要从 web、GitHub、社区、替代品和现有材料中提取证据
- 需要形成 insight pack，而不是直接想 feature

### 进入 `ahe-opportunity-mapping`

满足任一条件即可：

- 已有一定 evidence，需要收敛 JTBD / opportunity / wedge 视图
- 需要判断“先打哪个机会，而不是先做哪个功能”

### 进入 `ahe-concept-shaping`

满足任一条件即可：

- 已选机会，但解决方向仍然平庸
- 需要产生多个概念方向，并选出更有吸引力的 wedge

### 进入 `ahe-assumption-probes`

满足任一条件即可：

- 方向看起来不错，但关键成败假设还没暴露
- 需要在写 spec 前先设计便宜验证

### 进入 `ahe-spec-bridge`

只有在以下条件都满足时才进入：

- desired outcome、目标用户和优先机会已经清楚
- 已形成一个候选概念或 wedge
- 关键假设至少被列出来
- 当前需要把这些内容压缩成 `ahe-coding-skills/ahe-specify` 可消费输入

## Output Contract

本 skill 的正确输出只有两类：

1. 明确进入一个 product insight 节点
2. 明确说明已经可以进入 `ahe-spec-bridge`

推荐使用这 3 行快路径：

1. `Entry Classification`：直接写当前更缺的东西，例如 `framing-first`、`research-first`、`bridge-ready`
2. `Target Skill`：直接写 canonical skill 名
3. `Why`：只保留 1-2 条关键原因

## Shared References

按需读取：

- `ahe-product-skills/docs/product-insight-shared-conventions.md`
- `ahe-product-skills/docs/product-debate-protocol.md`
- `ahe-product-skills/docs/product-insight-foundations.md`
- `ahe-product-skills/README.md`

## Default Debate Expectation

当路由到下面节点时，默认按多 agent 讨论 / PK 方式执行，而不是单 agent 直接拍板：

- `ahe-insight-mining`
- `ahe-opportunity-mapping`
- `ahe-concept-shaping`

## Red Flags

- 一开始就把“做什么功能”当成唯一讨论对象
- 明明没有任何外部信号，却直接下结论说机会很大
- 还没形成差异化，就急着让 `ahe-coding-skills` 开始写规格
- 把 product insight family 用成“创意文案生成器”
