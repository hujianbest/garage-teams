---
name: se-discovery
description: 通过采访、澄清和术语归一化，把粗糙需求收敛成可调研的问题定义。适用于用户只给了一个场景、自己对系统不熟、团队术语含义不稳定，或当前还说不清目标、边界、约束和成功标准的场景。
---

# SE Discovery

## Overview

这个 skill 的职责不是给方案，而是把“到底要分析什么”先说清楚。

它要解决的典型问题是：

- 用户脑子里有场景，但表述还不稳定
- 团队内部名词很多，新人听不懂
- 需求、约束、接口边界和成功标准掺在一起
- 如果不先问清楚，后面的研究和方案会全部建立在猜测上

## When to Use

在这些场景使用：

- 用户给出的是粗糙问题场景，而不是稳定需求
- 你需要持续追问，才能弄清楚范围、上下游、触发条件和边界
- 团队内存在缩写、简称或本地术语，需要先归一化
- 你需要产出一份可供后续研究使用的问题定义和研究问题列表

不要在这些场景使用：

- 问题已经收敛，当前更需要仓库调研和方案比较，改用 `se-research-and-options`
- 输入已经很完整，当前只需要收敛成正式方案包，改用 `se-design-pack`
- 当前要做的是 AHE 主链的规格澄清和审批链，改用 `ahe-specify`

## Standalone Contract

当用户直接点名 `se-discovery` 时，至少确认：

- 已经有一个当前轮次要分析的主题
- 允许通过多轮问答来收敛问题定义
- 当前不要求直接得出最终设计结论

如果连主题都无法命名，先帮助用户把问题压缩成一个可描述的一句话主题，再继续。

## Chain Contract

作为 `se-analysis-workflow` 的本地节点时，默认读取：

- 用户当前请求
- 与当前问题直接相关的最少仓库文档
- 已存在的分析笔记、会议纪要或草稿（如果有）

本节点完成后应写回：

- `docs/analysis/YYYY-MM-DD-<topic>-analysis-pack.md` 的 discovery 部分
- 已确认事实、假设、开放问题和研究问题
- 本地下一步建议：通常为 `se-research-and-options`

## Inputs / Required Artifacts

优先读取最少但必要的材料：

- 用户当前场景描述
- 当前系统的高层说明、README、相关设计文档
- 与术语或接口有关的现有说明

默认输出到：

- `docs/analysis/YYYY-MM-DD-<topic>-analysis-pack.md`

如果现有分析包已经存在，应更新而不是另起一份互相冲突的新文档。

## Workflow

按以下顺序工作。

### 1. 先提炼已知、未知和危险假设

在开始追问前，先把当前输入拆成三类：

- `已知`：用户已明确说出的事实
- `未知`：当前必须补齐的问题
- `危险假设`：如果默认采用，会直接影响后续方案方向的内容

优先识别这些危险假设：

- 服务边界和职责
- 上下游系统
- 协议与接口所有权
- 安全、实时性、资源和部署约束
- 成功标准和验收口径

### 2. 先统一术语

如果用户使用了团队内部术语、缩写或模糊词，先做术语归一化，再继续问答。

例如：

- `AR`：按本 workflow 默认理解为类似 User Story 的需求切片
- `DFX`：默认从通用工程质量维度理解，而不是假设某个团队私有定义
- “封装 OpenSSL”：“需要确认是在做 TLS、安全边界、证书管理、接口适配，还是别的职责”

术语处理规则：

- 先给出你当前理解
- 明确标出“这是当前工作假设，不是既定事实”
- 如果术语含义会影响方案方向，必须先向用户确认

### 3. 分主题采访

优先按以下主题分轮采访；一次只推进一个主题，除非几个问题天然绑定。

1. 问题背景、目标和为什么现在要做
2. 使用方、调用方、依赖方和关键角色
3. 核心场景、触发条件、正常流程和失败路径
4. 外部接口、协议、数据边界和上下游 ownership
5. 资源、性能、安全、可靠性、部署和兼容约束
6. 当前已知限制、开放问题和非目标

需要更多问题种子时，读取：

- `ahe-se-skills/se-analysis-workflow/references/interview-checklists.md`

### 4. 形成“问题定义”而不是“先验方案”

采访阶段的目标是写出下面这些内容，而不是过早选择技术方案：

- 需求描述
- 范围和范围外内容
- 参与者与调用链
- 关键场景
- 约束与依赖
- 已确认事实
- 假设和开放问题
- 需要进入研究阶段验证的问题

如果你在 discovery 阶段已经开始写线程模型、模块划分、接口字段或库选型，通常说明你越界了。

### 5. 判断是否达到“可研究”状态

当以下条件满足时，可进入 `se-research-and-options`：

- 当前轮次分析主题已稳定
- 关键参与者和系统边界已大致明确
- 至少知道要研究哪些仓库问题和外部问题
- 剩余开放问题不会阻止你定义研究方向

如果这些条件仍不满足，继续采访，不要伪造 handoff。

### 6. 写回 analysis pack

将 discovery 结果写进分析包时，至少包含这些小节：

- 问题陈述
- 当前范围 / 非目标
- 参与者与上下游
- 关键场景
- 约束与依赖
- 已确认事实
- 假设
- 开放问题
- 研究问题列表

默认结构参考：

- `ahe-se-skills/se-analysis-workflow/references/analysis-output-template.md`

## Output Contract

本节点完成时，至少应产出：

- 一份已落盘的 analysis pack discovery 部分
- 一组清晰的研究问题
- 本地下一步建议：通常为 `se-research-and-options`

推荐输出：

```markdown
discovery 已完成，当前主题已可进入仓库调研、外部研究和候选方案比较。

推荐下一步 skill: `se-research-and-options`
```

## Common Rationalizations

| Rationalization | Reality |
| --- | --- |
| “先按常见微服务模式理解，后面再纠正。” | Discovery 阶段最怕的就是把经验当事实。 |
| “这些术语我大概懂，不用专门确认。” | 团队术语误解会直接把后续研究带偏。 |
| “先开始查代码，边查边补问题定义。” | 没有问题定义的调研通常会变成无目标翻仓库。 |
| “用户提到 OpenSSL / 线程池，说明方案已经定了。” | 用户提到的是待理解现象，不一定是已确认设计决策。 |

## Red Flags

- 还没明确范围就开始比较方案
- 把用户的模糊词直接写成确定结论
- 不区分事实、假设和开放问题
- 没有研究问题列表，却说可以进入调研
- 把 discovery 文档写成设计方案草稿

## Supporting References

按需读取：

- `ahe-se-skills/se-analysis-workflow/references/interview-checklists.md`
- `ahe-se-skills/se-analysis-workflow/references/analysis-output-template.md`
- `ahe-se-skills/se-analysis-workflow/references/embedded-ai-inference-example.md`

## Verification

只有在以下条件都满足时，这个 skill 才算完成：

- 你已经把当前主题压缩成可描述的问题定义
- 你已经统一关键术语，或把仍未确认的术语标成开放问题
- 你已经写出范围、关键场景、约束和研究问题
- 你已经把结果落盘到 analysis pack
- 当前输入已经足够支持进入 `se-research-and-options`
