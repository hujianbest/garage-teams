---
name: ahe-spec-bridge
description: Bridge product insight artifacts into a pre-spec input for `ahe-coding-skills/ahe-specify`. Use when outcome, opportunity, concept, and key assumptions are clear enough that implementation discipline can begin, but you do not want `ahe-coding-skills` to invent the product thesis from scratch.
---

# AHE Spec Bridge

## Overview

这个 skill 是 product insight family 到 `ahe-coding-skills` 的桥。

它不替代 `ahe-specify`，而是先把上游创造性工作压缩成后者可消费的输入，避免 coding family 被迫从模糊想法里反向猜产品命题。

## When to Use

在这些场景使用：

- 已有 framing、insight、opportunity、concept 或 probe 结果
- 当前需要进入 `ahe-coding-skills/ahe-specify`
- 你想把 evidence、concept 和 unknowns 一起带过去

不要在这些场景使用：

- 上游方向还没收敛，先回到前面的 product 节点
- 当前已经在写正式 spec 了

## Inputs

优先读取：

- `docs/insights/*-insight-pack.md`
- `docs/insights/*-opportunity-map.md`
- `docs/insights/*-concept-brief.md`
- `docs/insights/*-probe-plan.md`

## Workflow

按以下顺序执行。

### 1. 把上游内容压缩成“机会 thesis”

必须能写成一句话：

- 为谁
- 在什么情境下
- 解决什么 progress blockage
- 预期改变什么 outcome

### 2. 明确哪些内容已经足够稳定

至少区分：

- 已被 evidence 支撑的内容
- 仍然只是工作假设的内容

### 3. 给 `ahe-specify` 准备 scope 边界

至少写清：

- v1 必须包含什么行为
- 这轮明确不做什么
- 哪些开放问题需要在 spec 阶段继续澄清

### 4. 不把 concept brief 直接冒充正式需求规格

这里的目标不是抢写 spec，而是提供：

- 更好的上游输入
- 更少的猜测空间
- 更明确的非目标和风险

### 5. 落盘成 `spec-bridge`

默认使用：

- `ahe-product-skills/templates/spec-bridge-template.md`

至少补齐：

- `Opportunity Thesis`
- `Target User And Context`
- `Desired Outcome`
- `Proposed v1 Shape`
- `Differentiation`
- `Evidence And Unknowns`
- `Open Questions For Spec`

## Output Contract

完成后，推荐下一步：

- `ahe-coding-skills/ahe-specify`

推荐输出可直接写成：

1. `Bridge Status`：`ready-for-ahe-specify`
2. `Input Artifact`：`docs/insights/YYYY-MM-DD-<topic>-spec-bridge.md`
3. `Next Skill`：`ahe-specify`

## Quality Bar

高质量 spec bridge 至少应满足：

- coding family 不需要重新发明产品 thesis
- v1 范围有基本边界
- 非目标显式存在
- differentiation 被清楚表达
- assumptions 没有被伪装成事实

## Red Flags

- 读完 bridge 仍然不知道“为什么值得做”
- 所有内容都像 marketing 文案
- 完全没有 open questions
- 把 feature list 当作全部 bridge 内容
