# F070: Garage Continuity Mapping And Promotion

- Feature ID: `F070`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 在 `A130` 已冻结 continuity 分层、`F080` 已冻结主动成长 loop 之后，进一步定义 `Product Insights Pack` 与 `Coding Pack` 在 `memory / skill / runtime update` 上的候选来源、映射关系、晋升规则、治理关注点与禁止路径。
- 当前阶段: 完整架构主线，实施将按切片推进
- 关联文档:
  - `docs/GARAGE.md`
  - `docs/architecture/A130-garage-continuity-memory-skill-architecture.md`
  - `docs/features/F050-governance-model.md`
  - `docs/features/F060-artifact-and-evidence-surface.md`
  - `docs/features/F080-garage-self-evolving-learning-loop.md`
  - `docs/features/F110-reference-packs.md`
  - `docs/design/D110-garage-product-insights-pack-design.md`
  - `docs/design/D120-garage-coding-pack-design.md`

## 1. 文档目标与范围

这篇文档只回答一个问题：

**当 `Garage` 进入主动成长模式后，`Product Insights Pack` 与 `Coding Pack` 分别会贡献什么样的 continuity 候选，又应该通过什么规则晋升为 `memory`、`skill` 或 `runtime update`。**

本文覆盖：

- 两个 reference packs 的候选来源
- continuity 对象与 pack 语义之间的映射关系
- `Evidence -> GrowthProposal -> Update` 在两个 packs 上的差异化关注点
- 默认禁止路径与高风险误晋升类型

本文不覆盖：

- learning loop 的总体结构
- proposal lifecycle 的通用定义
- skill 文件格式
- pack 之外的全局 memory / skill 架构

## 2. 为什么这篇文档要与 `F080` 分开

`F080` 负责解释：

- learning loop 如何发生
- proposal 如何进入治理
- 哪些自动化默认允许

而这篇文档只负责解释：

- 不同 packs 到底会产出什么候选
- 这些候选更适合晋升到哪一类长期更新
- 每个 pack 的高风险误晋升点是什么

一句话说：

- `F080` 讲 loop
- `F070` 讲 mapping

## 3. mapping 的核心判断

完整架构下建议先冻结 5 个判断：

1. `session` 仍负责当前推进，不直接成为长期沉淀的默认来源。
2. `evidence` 仍是成长观察面，pack 先贡献 evidence，再通过 proposal 走向长期更新。
3. `memory` 只接纳跨 session 仍成立的事实、偏好与约束。
4. `skill` 只接纳可描述、可重复、可复用的方法。
5. `runtime update` 只接纳那些会影响团队协作纪律、review 方式、prompt 模块或运行策略的改进建议。

一句话压缩就是：

**不同 packs 可以贡献不同类型的成长候选，但长期更新语义必须统一。**

## 4. 两个 packs 的 continuity 对照

| 维度 | `Product Insights Pack` | `Coding Pack` |
| --- | --- | --- |
| `evidence` 重点 | 信号、判断、来源、假设验证、bridge 依据 | 设计取舍、review、verification、closeout、限制与风险 |
| `memory` 候选 | 长期问题域偏好、目标约束、稳定判断偏向 | 工程约束、仓库偏好、长期环境事实、质量倾向 |
| `skill` 候选 | 研究套路、分析模板、洞察整理方法 | 实现流程、验证方法、复查套路、收尾模板 |
| `runtime update` 候选 | framing checklist、probe discipline、bridge review 规则 | verification checklist、handoff discipline、closeout policy |
| 高风险误晋升 | 临时判断被当长期事实 | workaround 被当长期方法 |
| 核心治理关注点 | 来源可靠性、判断依据、bridge 完整性 | 验证充分性、方法泛化性、质量结论可靠性 |

## 5. `Product Insights Pack` 的候选映射

### 5.1 可形成 `evidence` 的来源

- framing 判断
- research 信号与来源引用
- 假设、对比、取舍理由
- `probe` 结果
- `bridge artifact` 的形成依据
- pack 内 review / approval / exception 痕迹

### 5.2 更适合进入 `memory` 的候选

- 创作者长期关注的问题域
- 稳定的目标偏好或方向约束
- 反复被确认的判断标准
- 对某类机会的长期偏向

### 5.3 更适合进入 `skill` 的候选

- 稳定有效的研究工作流
- 可复用的分析模板
- 多次证明有效的 framing / probing 方法
- 跨 session 可复用的洞察整理套路

### 5.4 更适合进入 `runtime update` 的候选

- 新的 probe checklist
- 更好的来源记录规范
- 更稳的 bridge 审核步骤
- 对 pack-level review policy 的调整建议

### 5.5 默认不应晋升的内容

- 一次性市场观察
- 尚未验证的机会猜测
- 当前 session 才成立的临时 framing
- 缺少来源支撑的直觉判断
- 情绪化偏好表达

## 6. `Coding Pack` 的候选映射

### 6.1 可形成 `evidence` 的来源

- 设计取舍记录
- review verdict
- verification 结果
- closeout 结论
- 风险、限制与未决项
- 关键 handoff 与返工原因

### 6.2 更适合进入 `memory` 的候选

- 长期工程约束
- 仓库级稳定偏好
- 持续成立的质量偏向
- 被反复确认的环境事实

### 6.3 更适合进入 `skill` 的候选

- 可重复复用的实现流程
- 稳定有效的 review 方法
- closeout / verification 模板
- 与特定仓库无强耦合的协作套路

### 6.4 更适合进入 `runtime update` 的候选

- review checklist 调整
- verification discipline 调整
- handoff 模板更新
- prompt / rule / policy patch 建议

### 6.5 默认不应晋升的内容

- 单次修复中的临时绕路
- 只适用于当前 repo 状态的特例步骤
- 未完成验证的实现路径
- 依赖宿主偶然性的 workaround
- 临时 debug 痕迹

## 7. canonical promotion route

在两个 packs 上，建议统一采用下面这条 canonical route：

1. pack 内节点先形成 `evidence`
2. `evidence` 被观察并转写成 `GrowthProposal`
3. proposal 根据类型进入 `memory`、`skill` 或 `runtime update` 的治理路径
4. 被接受的更新回流到未来 session

这里最重要的不是“能不能自动发现候选”，而是：

- 是否先形成 evidence
- 是否显式写成 proposal
- 是否有足够治理来决定最后落点

## 8. 允许路径与禁止路径

### 8.1 默认允许路径

- `PackEvidence -> GrowthProposal`
- `GrowthProposal -> Memory`
- `GrowthProposal -> Skill`
- `GrowthProposal -> RuntimeUpdate`

这里的前提是：

- proposal 已显式形成
- governance 已参与

### 8.2 默认禁止路径

- `PackSession -> Memory` 自动晋升
- `PackSession -> Skill` 自动晋升
- `PackEvidence -> Memory` 无门槛自动晋升
- `PackEvidence -> Skill` 无门槛自动晋升
- `PackEvidence -> RuntimeUpdate` 绕过 proposal
- pack 私有 heuristics 自动进入共享长期资产

## 9. 判断一个 proposal 更像哪类更新

### 9.1 更像 `memory`

当候选主要回答：

- 以后应该记住什么事实
- 哪些偏好或约束长期成立

### 9.2 更像 `skill`

当候选主要回答：

- 以后应该怎样更稳定地做一类工作
- 哪种方法可以被重复调用

### 9.3 更像 `runtime update`

当候选主要回答：

- 团队自身以后该怎样运行得更稳
- 哪些治理、review、prompt 或 routing 规则需要调整

## 10. 两个 packs 的治理重点

### 10.1 `Product Insights Pack`

治理重点更偏向：

- 来源可靠性
- 判断依据是否充分
- bridge artifact 是否完整
- 提议的长期偏向是否真的跨 session 成立

### 10.2 `Coding Pack`

治理重点更偏向：

- 验证是否充分
- 方法是否可泛化
- proposed skill 是否脱离一次性 repo 状态
- runtime update 是否只是当前宿主特例

## 11. pack-specific mapping 的意义

如果没有这层 mapping，learning loop 虽然存在，但很容易出现：

- 不同 packs 对“什么值得成长”理解不一致
- `Product Insights Pack` 的临时判断被误当成长期事实
- `Coding Pack` 的临时 workaround 被误当成可复用 skill

因此，这篇文档冻结的不是整个成长系统，而是：

- 两个 reference packs 分别贡献什么
- 它们该往哪里走
- 各自最容易犯什么错

## 12. 一句话总结

`F070` 的作用，是把 `Product Insights Pack` 与 `Coding Pack` 放回同一条主动成长主链里，并明确它们各自更容易贡献哪类长期更新、应走什么晋升路径，以及哪些内容绝不能被误固化为 `memory`、`skill` 或 runtime update。
