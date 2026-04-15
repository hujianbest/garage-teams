---
name: ahe-opportunity-mapping
description: 适用于已有 insight 信号但需要收敛为 JTBD/机会分支/优先排序的场景。不适用于证据不够（→ ahe-insight-mining）或已选好机会缺概念方向（→ ahe-concept-shaping）的场景。
---

# AHE Opportunity Mapping

负责把上游 research 收敛成"先追哪个机会"——提炼 JTBD、生成机会分支、通过多 agent 对撞做出优先排序。不替代概念发散或验证探针设计。

本 skill 借鉴 JTBD（Jobs to Be Done）和 OST（Opportunity Solution Tree）思路，但目标不是画树，而是避免把 solution 假装成 opportunity。这些方法论的应用为项目化实践。

## When to Use

**正向触发：**
- 已经有 insight-pack 或相近 research 结论
- 需要从多个痛点中选一个优先机会
- 需要把 feature wishlist 退回到 problem / job 视角

**不适用：**
- 证据还不够 → `ahe-insight-mining`
- 已选定机会，当前更缺概念方向 → `ahe-concept-shaping`

**Direct invoke：** 用户说"机会太多不知道先做哪个""帮我把功能列表退回问题视角""哪个痛点最值得追"

**相邻边界：** 若在排序过程中发现证据不足支撑判断，退回 `ahe-insight-mining` 补充。

## Workflow

### 1. 先读取已有 insight-pack 和上游工件

读取项目中的 insight-pack、framing 文档等已有证据。若无 insight 工件，reroute 到 `ahe-insight-mining`。

### 2. 锁定 desired outcome

先写清：

- 希望改变什么产品 / 业务结果
- 为什么这是当前轮次的顶层 outcome

**决策点：** 若连 top outcome 都模糊，停下来补齐，而不是继续画机会图。

### 3. 提炼 JTBD

至少分别提炼：

- functional jobs
- social jobs
- emotional jobs

不要只写"用户想要一个更好的工具"。

### 4. 生成机会分支

机会应写成：

- 未满足的 progress
- 被阻碍的动作
- 重复出现的痛点
- 用户明确的 desire

不要写成："做推荐算法""上 AI 助手""支持 dark mode"。

如果一个"机会"只有一种实现方式，它大概率是 solution 伪装。

### 5. 为每个机会补齐 4 个判断维度

- 频率 / 强度
- outcome leverage
- 差异化空间
- 风险或依赖

### 6. 至少保留 3 个候选机会再收敛

除非证据极强，否则不要只剩一个机会。

**决策点：** 若候选不足 3 个，说明上游 insight 不够丰富或已被 solution 限定，退回 step 4 或 `ahe-insight-mining`。

### 7. 让 Advocate 为前 2-3 个候选机会建立 strongest case

使用 `../../agents/product-thesis-advocate.md`，至少说明：

- 为什么用户会优先为这个机会买单或改变行为
- 为什么它比其他机会更接近强 wedge
- 它成立需要哪些条件

### 8. 让 Contrarian 对候选机会做 PK challenge

使用 `../../agents/product-contrarian.md`，至少挑战：

- 哪个机会只是 problem wording 更好看，但不更重要
- 哪个机会看起来有价值，但其实会落回 commodity 功能
- 哪个机会依赖太多前提，不适合当前轮次下注

### 9. 让 Referee 给出机会 PK verdict

使用 `../../agents/product-debate-referee.md`，至少输出：

- 候选机会排序
- survive / park / drop
- 为什么不选其他机会

### 10. 选择当前最值得下注的机会

优先选择：

- 用户痛感强
- outcome leverage 高
- 不是所有人都已经解决得很好
- 有形成 wedge 的空间

### 11. 落盘成 opportunity-map

使用 pack 内模板 `../templates/opportunity-map-template.md`，至少补齐：

- JTBD Summary
- Opportunity Branches
- Opportunity Ranking
- Selected Opportunity
- Debate Verdict

## Output Contract

- **写什么：** opportunity-map 文档
- **写到哪里：** 项目约定位置（参考 AGENTS.md），默认示例 `docs/insights/YYYY-MM-DD-<topic>-opportunity-map.md`
- **状态同步：** opportunity-map 包含 JTBD、机会分支、排序和 PK 结论
- **下一步：** `ahe-concept-shaping`

## Red Flags

- 机会写法本质上还是功能清单
- 没有 social / emotional job
- 只按"好不好做"排机会
- 没有说明为什么不选其他机会
- 多个候选机会没有经过正反对撞就直接拍板

## Common Mistakes

| 错误 | 后果 | 修复 |
|------|------|------|
| 把 solution 写成 opportunity | 选出的"机会"只有一种实现方式 | 用 progress/痛点语言重写 |
| 只排功能层 JTBD | 忽略 social/emotional 需求 | 至少提炼 3 类 job |
| 只留 1 个候选 | 无对比基准，选择理由空洞 | 至少保留 3 个再收敛 |

## 和其他 Skill 的区别

| 对比项 | ahe-opportunity-mapping | ahe-insight-mining | ahe-concept-shaping | ahe-outcome-framing |
|--------|------------------------|--------------------|---------------------|---------------------|
| 核心任务 | 选择优先机会 | 提取外部信号 | 发散收敛概念方向 | 重写模糊 idea 为锋利问题 |
| 输入 | insight-pack | framing 文档 | opportunity-map | 用户模糊 idea |
| 输出 | opportunity-map | insight-pack | concept-brief | problem/outcome frame |
| 关键动作 | JTBD + 机会排序 + PK | 多源信号 → thesis PK | 多方向 PK → wedge | 问题重构 |

## Reference Guide

| 材料 | 路径 | 用途 |
|------|------|------|
| Opportunity Map 模板 | `../templates/opportunity-map-template.md` | 落盘格式 |
| 产品洞察共享约定 | `../docs/product-insight-shared-conventions.md` | 家族级术语和约定 |
| 产品辩论协议 | `../docs/product-debate-protocol.md` | 多 agent 讨论规范 |
| 产品洞察基础 | `../docs/product-insight-foundations.md` | 方法论背景 |
| Agent: thesis-advocate | `../../agents/product-thesis-advocate.md` | 为机会辩护 |
| Agent: contrarian | `../../agents/product-contrarian.md` | 反向挑战 |
| Agent: debate-referee | `../../agents/product-debate-referee.md` | PK 裁判 |

## Verification

- [ ] opportunity-map 已落盘
- [ ] 机会不是 solution 伪装（每个机会有 >= 2 种可能的实现方式）
- [ ] JTBD 包含 functional / social / emotional 三层
- [ ] 至少比较了 3 个机会
- [ ] 选中的机会有明确理由（含不选其他机会的理由）
- [ ] 有多 agent PK 结论记录（Debate Verdict）
- [ ] 下一步 skill 已明确（→ ahe-concept-shaping）
