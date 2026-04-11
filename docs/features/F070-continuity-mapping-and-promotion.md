# F070: Garage Phase 1 Continuity Mapping And Promotion

- Feature ID: `F070`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 在 `A130-garage-continuity-memory-skill-architecture.md` 已定义 continuity 高层分层的基础上，进一步冻结 phase 1 中 `memory`、`skill`、`evidence` 在 `Product Insights Pack` 与 `Coding Pack` 上的候选来源、映射关系、晋升规则、治理检查点与禁止自动晋升边界。
- 当前阶段: phase 1
- 关联文档:
  - `docs/GARAGE.md`
  - `docs/architecture/A120-garage-core-subsystems-architecture.md`
  - `docs/features/F010-shared-contracts.md`
  - `docs/architecture/A130-garage-continuity-memory-skill-architecture.md`
  - `docs/features/F110-reference-packs.md`
  - `docs/design/D110-garage-product-insights-pack-design.md`
  - `docs/design/D120-garage-coding-pack-design.md`
  - `docs/features/F050-governance-model.md`
  - `docs/features/F040-session-lifecycle-and-handoffs.md`
  - `docs/features/F060-artifact-and-evidence-surface.md`

## 1. 文档目标与范围

这篇文档只回答一个问题：

**在 phase 1 中，`Garage` 应如何把 continuity 轴映射到 `Product Insights Pack` 与 `Coding Pack`，并以保守方式冻结 `promotion` 行为。**

本文覆盖：

- 两个 `reference packs` 中 `memory`、`skill`、`evidence` 的候选来源
- continuity 对象与 pack 语义之间的映射关系
- `promotion` 的允许路径、显式确认路径和禁止自动路径
- phase 1 的治理检查点与最小证据要求

本文不覆盖：

- 具体 schema 字段
- 自动学习流水线
- 向量检索实现
- skill 文件格式细节

## 2. 为什么需要这份文档

高层 continuity 文档已经回答了“四层要分开”，但还没有回答下面这些 phase 1 必须冻结的问题：

- 两个 `reference packs` 分别会产生什么样的 continuity 候选
- 哪些候选只应该停留在 `evidence`
- 哪些候选可以保守晋升到 `memory` 或 `skill`
- promotion 发生前，需要经过哪些治理检查点
- 哪些行为在 phase 1 必须明确禁止自动化

如果没有这一层，系统很容易出现：

- `Product Insights Pack` 的判断痕迹被误晋升成长期事实
- `Coding Pack` 的一次性 workaround 被误晋升成长期 skill
- pack 之间对“可晋升”理解不一致

## 3. continuity 映射的核心判断

phase 1 建议先冻结 4 个判断：

- `session` 负责当前推进，不直接成为长期沉淀的默认来源
- `evidence` 是 promotion 的默认观察面
- `memory` 只接纳跨 session、跨阶段仍然稳定成立的信息
- `skill` 只接纳边界清楚、可重复复用、已被验证的方法

一句话压缩就是：

**先记录，再判断，再晋升；宁可少晋升，也不要错晋升。**

## 4. continuity 对象总览

| continuity 对象 | 回答的问题 | 在 phase 1 的默认来源 | 默认进入方式 |
| --- | --- | --- | --- |
| `memory` | 哪些长期事实以后仍成立 | 经确认的长期偏好、稳定约束、跨 pack 可复用背景 | 保守晋升 |
| `skill` | 哪些方法以后值得反复调用 | 经验证的工作流、模板、协作套路、复查方式 | 保守晋升 |
| `evidence` | 为什么这样判断、做过什么验证 | decision、review、approval、verification、bridge、closeout | 默认记录 |
| `session` | 当前工作正在发生什么 | 当前 pack / node / handoff / 活跃上下文 | 默认运行时承接 |

这里要明确：

- `session` 可以产生候选，但不应默认直接变成 `memory` 或 `skill`
- `evidence` 是主晋升面，不是所有内容的最终归宿
- 两个 pack 都可以贡献 continuity 候选，但判断门槛必须统一

## 5. `Product Insights Pack` 的 continuity 候选来源

### 5.1 可形成 `evidence` 的来源

- framing 判断
- research 信号与来源引用
- 假设、对比、取舍理由
- `probe` 结果
- `bridge artifact` 的形成依据
- pack 内 review / approval / exception 痕迹

### 5.2 可形成 `memory` 候选的来源

- 创作者长期关注的问题域
- 稳定的目标偏好或方向约束
- 反复被确认的判断标准
- 对某类机会的长期偏向

### 5.3 可形成 `skill` 候选的来源

- 稳定有效的研究工作流
- 可复用的分析模板
- 多次证明有效的 framing / probing 方法
- 跨 session 可复用的洞察整理套路

### 5.4 默认不应晋升的来源

- 一次性市场观察
- 尚未验证的机会猜测
- 当前 session 才成立的临时 framing
- 缺少来源支撑的直觉判断

## 6. `Coding Pack` 的 continuity 候选来源

### 6.1 可形成 `evidence` 的来源

- 设计取舍记录
- review verdict
- verification 结果
- closeout 结论
- 风险、限制与未决项
- 关键 handoff 与返工原因

### 6.2 可形成 `memory` 候选的来源

- 长期工程约束
- 仓库级稳定偏好
- 持续成立的质量偏向
- 被反复确认的环境事实

### 6.3 可形成 `skill` 候选的来源

- 可重复复用的实现流程
- 稳定有效的 review 方法
- closeout / verification 模板
- 与特定仓库无强耦合的协作套路

### 6.4 默认不应晋升的来源

- 单次修复中的临时绕路
- 只适用于当前 repo 状态的特例步骤
- 未完成验证的实现路径
- 依赖宿主偶然性的 workaround

## 7. 两个 packs 的 continuity 对照

| 维度 | `Product Insights Pack` | `Coding Pack` |
| --- | --- | --- |
| `evidence` 重点 | 信号、判断、假设验证、bridge 依据 | 设计取舍、review、verification、closeout |
| `memory` 候选 | 长期问题域偏好、目标约束、稳定判断偏向 | 工程约束、仓库偏好、质量偏向、稳定环境事实 |
| `skill` 候选 | 研究套路、分析模板、洞察工作流 | 实现流程、验证方法、复查套路、收尾模板 |
| 高风险误晋升 | 临时判断被当长期事实 | workaround 被当长期方法 |
| 关键治理关注点 | 来源可靠性、bridge 完整性 | 验证充分性、质量结论可靠性 |

这张表的目的，是冻结：

- 两个 pack 都可以贡献 continuity 候选
- 但候选类型不同，风险点不同
- promotion 判断方式应尽量统一

## 8. phase 1 的 promotion 路径

### 8.1 默认允许路径

- `Session -> Evidence`
- `Product Insights candidate -> Evidence`
- `Coding candidate -> Evidence`

### 8.2 允许但必须显式确认的路径

- `Evidence -> Memory`
- `Evidence -> Skill`
- 极少数 `Session -> Memory`
- 极少数 `Session -> Skill`

### 8.3 phase 1 默认禁止自动路径

- `Session -> Memory` 自动晋升
- `Session -> Skill` 自动晋升
- `Evidence -> Memory` 无门槛自动晋升
- `Evidence -> Skill` 无门槛自动晋升
- `Memory <-> Skill` 自动互转
- pack 内私有 heuristics 自动进入全局 continuity 资产

## 9. promotion 判定规则

### 9.1 `Evidence -> Memory`

至少应满足：

- 信息具有跨 session 稳定性
- 不依赖单次上下文才成立
- 已有明确确认动作
- 不属于争议中结论
- 未来多个 pack 或 session 仍可能引用

### 9.2 `Evidence -> Skill`

至少应满足：

- 是方法，不是结果
- 边界清楚，可描述为可重复动作
- 不依赖一次性特例
- 已有验证、review 或重复使用依据
- 对未来工作具有明显复用价值

保守判断原则：

**不能证明值得晋升时，默认停留在 `evidence`。**

## 10. 明确禁止自动晋升的内容

下面这些内容在 phase 1 中不应因为“被看见”就自动进入 `memory` 或 `skill`：

- 全量聊天记录
- 原始思维过程
- 未经确认的假设
- 临时计划
- 一次性 workaround
- 宿主特定操作细节
- 失败样本与争议痕迹本身
- 缺少 review / verification / approval 的结论

phase 1 必须坚持：

**连续性资产宁可少而准，也不要多而混。**

## 11. governance checkpoints 与 promotion 的关系

promotion 不能脱离治理。

phase 1 至少应有这组检查点：

- 候选识别 checkpoint
- review checkpoint
- approval checkpoint
- exception checkpoint
- archive checkpoint

其中：

- `Product Insights Pack` 更关注来源、判断与 bridge 完整性
- `Coding Pack` 更关注验证、质量与方法是否可泛化

## 12. 对后续开发的意义

这篇文档冻结的不是一个自动学习系统，而是：

- 什么能留下来
- 留到哪一层
- 在什么条件下允许晋升
- 哪些东西绝不能自动被固化

只有这一层先说清楚，后面的任务拆分才不会一边实现一边重新发明 continuity 规则。

## 13. 遵循的设计原则

- continuity 分层优先：`memory`、`session`、`skill`、`evidence` 必须分层，而不是混成一个桶。
- promotion 保守化：默认先进入 `evidence`，只有少量内容可显式晋升到 `memory` 或 `skill`。
- `Evidence-first promotion`：大多数晋升优先经过 `evidence`，而不是从原始 session 直接生长。
- Pack 贡献候选，core 冻结规则：不同 pack 可以贡献 continuity 候选，但 promotion 语义应由统一架构冻结。
- Pack-specific, core-consistent：pack 的候选来源可以不同，但允许路径、禁止路径和治理语汇应保持一致。
- 禁止自动固化噪音：全量聊天、临时计划、一次性 workaround、未确认假设不得自动晋升。
- 治理先于晋升：review、approval、exception 等治理动作先于关键 promotion。
- 来源可追溯：任何 `memory` 或 `skill` 都应能回指其 `artifact` 与 `evidence` 来源。
- `Markdown-first` / `file-backed`：phase 1 的 continuity 资产优先保持人类可读、文件可见。
- phase 1 克制：先冻结 continuity mapping 与 promotion 规则，再讨论自动学习和更重实现。

