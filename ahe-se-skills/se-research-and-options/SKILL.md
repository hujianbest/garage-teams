---
name: se-research-and-options
description: 结合仓库调研、网络检索和候选方案比较，为 SE 分析建立证据基础。适用于问题定义已经成形，但当前还不知道现有系统能力、外部最佳实践、关键 trade-off 或推荐方案应如何收敛的场景。
---

# SE Research And Options

## Overview

这个 skill 的职责不是直接写最终设计，而是把“应该查什么、怎么比较方案、凭什么推荐”做扎实。

它的核心目标是：

- 弄清当前仓库里已经有什么
- 查清外部资料里有哪些可信模式或约束
- 至少形成 2 到 3 个可比较的候选方案
- 通过只读并行研究，把方案选择建立在证据而不是经验口号上

## When to Use

在这些场景使用：

- discovery 已经完成，当前需要进入结构化调研
- 你不确定当前系统里是否已有可复用能力
- 你需要理解“为什么要封装某个库 / 为什么要某种并发模型 / 为什么要这么设计接口”
- 你需要把多个候选方案放到同一张 trade-off 视图里比较
- 你需要用并行 agent 同时研究仓库、网络资料和方案风险

不要在这些场景使用：

- 问题定义还没收敛，先回到 `se-discovery`
- 研究和选项已经足够充分，当前只是写最终输出，改用 `se-design-pack`
- 当前只是做单一事实检索，不需要形成方案矩阵

## Standalone Contract

当用户直接点名 `se-research-and-options` 时，至少确认：

- 当前已有明确的分析主题
- 已经能列出一组待研究问题
- 允许并行启动只读 agent 或只读研究步骤

如果你连“本轮到底要回答哪些研究问题”都说不清，先回到 `se-discovery`。

## Chain Contract

作为 `se-analysis-workflow` 的本地节点时，默认读取：

- 当前 analysis pack
- 与问题直接相关的仓库上下文
- 外部依赖、协议、框架或技术关键词

本节点完成后应写回：

- analysis pack 中的 research findings
- 候选方案比较矩阵
- 推荐方向及其证据来源
- 本地下一步建议：通常为 `se-design-pack`

## Inputs / Required Artifacts

优先读取：

- `docs/analysis/YYYY-MM-DD-<topic>-analysis-pack.md`
- 与当前问题直接相关的代码、README、架构或设计文档
- 当前涉及的外部技术名词、协议、框架或组件名

默认写回：

- 现有 analysis pack 的 research / options 部分

## Workflow

按以下顺序执行。

### 1. 把未知点改写成研究问题

先把 discovery 阶段的开放问题转换成一组可研究问题，并标记来源：

- `repo`：需要在仓库里确认
- `web`：需要查官方文档、公开资料或外部模式
- `decision`：需要通过方案比较回答

典型研究问题示例：

- 当前系统里是否已有类似服务或协议处理组件
- OpenSSL 封装在这个系统里可能承担什么职责
- 并发请求应该走线程池、事件循环还是串行 worker
- AI 推理接口在现有框架里如何接入
- 方案在资源受限的 SOC 上会受哪些约束

### 2. 先做仓库调研

当问题涉及现有系统能力、接口 ownership、部署约束或可复用代码时，优先做仓库调研。

推荐使用：

- `agents/se-repo-researcher.md`

调研目标至少包括：

- 当前模块边界、服务关系和启动方式
- 现有通信协议、接口层和安全层
- 可复用的公共组件、工具库和线程 / 任务模型
- 与本主题最相关的文件和路径
- 尚未在仓库里回答的问题

### 3. 再做外部研究

当问题涉及模式选择、库职责、行业实践或协议细节时，做外部研究。

推荐使用：

- `agents/se-web-researcher.md`

研究要求：

- 优先官方文档、框架文档、标准或高可信来源
- 记录来源与适用前提
- 不把外部最佳实践直接套进当前仓库；先判断适配条件

### 4. 形成候选方案

对于非 trivial 决策，至少形成两个候选方案；如果确实只有一个合理方向，也要写出“为什么其他路不成立”。

每个候选方案至少说明：

- 核心思路
- 适用前提
- 主要优点
- 主要代价
- 与当前仓库或当前平台约束的匹配情况
- 关键风险

### 5. 对候选方案做挑战和反驳

推荐对每个候选方案做一次独立挑战，检查：

- 是否隐含了未被确认的前提
- 是否忽略了部署、性能、安全、可观测或维护代价
- 是否低估了协议 ownership 或上下游协作成本
- 是否在代码量、改动面和验证成本上过于乐观

推荐使用：

- `agents/se-option-challenger.md`

如果多个 challenger 给出冲突观点，不要投票式决策；回到证据，找哪一条前提仍未被验证。

### 6. 收敛成方案矩阵

将研究结果整理成一张结构化矩阵，至少比较这些维度：

- 需求匹配度
- 与现有框架的兼容度
- 实现复杂度
- 运维 / 部署复杂度
- DFX 风险
- 参考代码量和验证成本
- 关键未知项

如果推荐了某个方案，必须写清：

- 为什么它比其他方案更适合当前问题
- 哪些结论是证据支撑的
- 哪些结论仍然是工作假设

### 7. 写回 analysis pack，并准备进入设计收敛

analysis pack 至少补齐以下内容：

- 仓库调研摘要
- 外部研究摘要
- 候选方案列表
- 方案矩阵
- 推荐方向
- 推荐理由
- 剩余开放问题

当这些内容已经足够支撑正式输出时，再进入 `se-design-pack`。

## Output Contract

本节点完成时，至少应产出：

- 已落盘的仓库调研结论
- 已落盘的外部研究结论
- 一张可读的候选方案矩阵
- 一个有理由、有边界的推荐方向
- 本地下一步建议：通常为 `se-design-pack`

推荐输出：

```markdown
research 与 options 已完成，analysis pack 已补齐证据、方案矩阵和推荐方向。

推荐下一步 skill: `se-design-pack`
```

## Common Rationalizations

| Rationalization | Reality |
| --- | --- |
| “这个方案行业里很常见，不用专门查仓库了。” | 行业通用做法不等于当前系统已经具备实施条件。 |
| “既然外部资料说这样做最好，就直接采用。” | 外部资料必须先经过当前仓库和约束过滤。 |
| “只要列一个我最喜欢的方案就够了。” | 没有备选方案，就很难看出当前推荐的真实 trade-off。 |
| “让多个 agent 各写一版结论，最后投票。” | 方案选择要回到证据，而不是多数表决。 |

## Red Flags

- 没有研究问题列表就开始翻代码
- 仓库调研和外部研究混在一起，来源不清
- 只有推荐方案，没有备选方案或拒绝理由
- 方案优缺点全是抽象形容词，没有证据或前提
- analysis pack 没有记录剩余开放问题，却声称可以直接落地

## Supporting References

按需读取：

- `agents/se-repo-researcher.md`
- `agents/se-web-researcher.md`
- `agents/se-option-challenger.md`
- `ahe-se-skills/se-analysis-workflow/references/analysis-output-template.md`
- `ahe-se-skills/se-analysis-workflow/references/dfx-default-lenses.md`
- `ahe-se-skills/se-analysis-workflow/references/code-estimation-rubric.md`

## Verification

只有在以下条件都满足时，这个 skill 才算完成：

- 你已经把开放问题转换成结构化研究问题
- 你已经分别完成仓库调研和外部研究，且来源清楚
- 你已经形成至少两个可比较方案，或说明为什么只有一个成立
- 你已经把 trade-off 收敛成方案矩阵
- 你已经把结果落盘到 analysis pack
- 当前输入已经足够支持进入 `se-design-pack`
