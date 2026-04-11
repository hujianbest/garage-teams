# Product Insight Foundations

## Purpose

本文记录 `ahe-product-skills/` 背后的外部实践来源，以及它们被如何吸收进当前目录设计。

## Key Inspirations

### `humanlayer/12-factor-agents`

来源：

- [humanlayer/12-factor-agents](https://github.com/humanlayer/12-factor-agents)

吸收点：

- 小而专注的 agent，而不是一个巨型“全能 PM agent”
- 自己掌控 prompts、context 和 control flow
- 用结构化输出和清晰 handoff，而不是隐式魔法

在本目录中的体现：

- skill 和 agent 拆成多个窄职责节点
- `spec-bridge` 明确承担向 `ahe-coding-skills` 的结构化交接

### `assafelovic/gpt-researcher`

来源：

- [assafelovic/gpt-researcher](https://github.com/assafelovic/gpt-researcher)

吸收点：

- planner -> researcher -> synthesizer 的多阶段结构
- 并行证据采集，再集中综合
- 对来源、总结和最终报告之间做清晰分层

在本目录中的体现：

- `using-ahe-product-workflow` 先判断节点
- `ahe-insight-mining` 聚焦证据采集
- `ahe-concept-shaping` 和 `ahe-spec-bridge` 承担综合与收敛
- 在关键收敛点引入多 agent debate / PK，而不是单次 synthesis 直接拍板

### `langchain-ai/open_deep_research`

来源：

- [langchain-ai/open_deep_research](https://github.com/langchain-ai/open_deep_research)

吸收点：

- supervisor / researcher 结构
- 先做 scoped research brief，再做并行研究
- 强调可配置阶段和 evaluation mindset

在本目录中的体现：

- 每个 skill 先把问题改写成研究 / 发散任务
- `probe-plan` 强调在进入实现前先做便宜验证

### `deanpeters/Product-Manager-Skills`

来源：

- [deanpeters/Product-Manager-Skills](https://github.com/deanpeters/Product-Manager-Skills)

吸收点：

- 把 discovery 拆成 workflow、component、interactive skills
- 用 JTBD、OST、PoL probe 等框架做具体节点
- 强调 trigger clarity、pedagogic value 和 reusable command layer

在本目录中的体现：

- 使用 entry skill + leaf skill 的分层
- 把 JTBD / opportunity / probe 方法嵌入不同节点
- 明确每个 skill 的 `When to Use`、`When NOT to Use`

### `microsoft/ai-discovery-agent`

来源：

- [microsoft/ai-discovery-agent](https://github.com/microsoft/ai-discovery-agent)

吸收点：

- 把 discovery 当成协作式 workshop / facilitation 问题
- 支持 use case framing、优先级讨论和 workshop 过程管理

在本目录中的体现：

- `ahe-outcome-framing` 和 `ahe-opportunity-mapping` 都强调 guided framing，而不是直接填模板

### Teresa Torres / Product Talk

来源：

- [Opportunity Solution Trees - Product Talk](https://www.producttalk.org/opportunity-solution-trees/)

吸收点：

- 先有 outcome，再有 opportunity，再有 solution，再有 assumption test
- OST 需要真实输入，不能凭空捏机会
- discovery 的目标是更快学习，而不是更快堆功能

在本目录中的体现：

- 所有 skill 都显式区分 `Observed`、`Inferred`、`Invented`、`Untested`
- `ahe-opportunity-mapping` 不允许把 solution 冒充 opportunity
- `ahe-assumption-probes` 在进入 spec 前先暴露危险未知项

## Why A Separate Family Exists

`ahe-coding-skills/` 的长处是：

- 准确
- 可追溯
- 可 gate
- 可验证

但它天然不会替你发明：

- 更锋利的问题定义
- 更有传播性的 product wedge
- 更反常识但更有潜力的机会 framing

所以需要一条单独的上游 family，专门负责：

- 重新定义问题
- 提取洞察
- 生成多个方向
- 设计低成本验证
- 最后再交给实现链路

## Design Translation

从这些实践中，当前目录提炼出 5 条本地设计原则：

1. `问题先于方案`
   没有明确 desired outcome 和用户 progress，不进入 feature 讨论。
2. `证据先于洞察，洞察先于规格`
   先采信号，再写 insight，再进 spec。
3. `发散先于收敛`
   至少提出多个 framing / concept，再选方向。
4. `假设先暴露，再投入工程`
   用 probe 和 kill criteria 对危险前提做便宜验证。
5. `bridge 明确，而不是隐式跳转`
   使用 `spec-bridge` 把产品创意压缩为 coding family 可以消费的输入。

## Debate Translation

除了 research -> synthesis，本目录还额外强调：

- 关键 insight 不直接采纳第一份总结，而要先经过正反 PK
- 关键 opportunity 不靠单点偏好，而要留下 why-not-others 的显式记录
- 关键 concept 不靠“哪个听起来酷”，而要经过 wedge 级对撞后再收敛

因此本地默认不是单 agent PM，而是：

- `Scout` 并行收证据
- `Advocate` 建 strongest case
- `Contrarian` 做反 commodity challenge
- `Referee` 输出 verdict
