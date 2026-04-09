---
name: se-design-pack
description: 将 discovery 和 research 的结论收敛成可评审的分析包与方案包。适用于需求、约束和候选方案已经基本稳定，当前需要正式输出需求描述、方案、接口设计、时序图、DFX 设计、AR 分解和参考代码量估算的场景。
---

# SE Design Pack

## Overview

这个 skill 的职责是把前面的采访、调研和方案比较，收成一套能交给他人阅读、评审和继续拆解的正式产物。

它不是新的研究阶段，也不是实现阶段。它要回答的是：

- 这次分析的需求和边界到底是什么
- 为什么推荐当前方案
- 接口、时序和关键设计决策如何表达
- DFX 风险如何显式化
- 需求应该如何切成 AR
- 参考代码量大概落在什么区间，置信度如何

## When to Use

在这些场景使用：

- discovery 和 research 基本完成，当前需要输出正式分析结果
- 你需要把候选方案收敛成一个推荐方案
- 你需要同时产出分析包和方案包，而不是只给口头结论
- 你需要在方案文档里加入接口设计、时序图、DFX 和 AR 分解

不要在这些场景使用：

- 关键范围、术语或参与者还不清楚，先回到 `se-discovery`
- 关键技术问题、仓库证据或候选方案还没查完，先回到 `se-research-and-options`
- 当前要做的是 AHE 主链设计评审或任务拆解，改用 `ahe-design` 或 `ahe-tasks`

## Standalone Contract

当用户直接点名 `se-design-pack` 时，至少确认：

- 已经存在可回读的 discovery / research 结论
- 当前推荐方向已经能说明“为什么是它”
- 剩余开放问题不会阻塞主要输出结构

如果当前仍缺核心证据，不要用写文档来掩盖缺口；明确返回上游节点补证据。

## Chain Contract

作为 `se-analysis-workflow` 的本地节点时，默认读取：

- 当前 analysis pack
- discovery 的问题定义与开放问题
- research 的仓库结论、外部资料和方案矩阵

本节点完成后应写回：

- 更新后的 analysis pack
- `docs/designs/YYYY-MM-DD-<topic>-solution-pack.md`
- 推荐方案、接口设计、时序图、DFX、AR 分解和代码量估算

## Inputs / Required Artifacts

优先读取：

- `docs/analysis/YYYY-MM-DD-<topic>-analysis-pack.md`
- 相关研究记录和引用来源
- 必要的仓库文件和外部资料链接

默认输出到：

- `docs/analysis/YYYY-MM-DD-<topic>-analysis-pack.md`
- `docs/designs/YYYY-MM-DD-<topic>-solution-pack.md`

## Workflow

按以下顺序执行。

### 1. 先检查证据是否足够

在开始正式写包之前，先确认这些输入已经存在：

- 问题定义和范围
- 关键约束与依赖
- 研究结论和来源
- 候选方案及其 trade-off
- 推荐方向

如果上述任一项仍为空白或全靠假设，先回到上游节点补齐。

### 2. 固定两类输出

默认产出分成两类：

- `analysis pack`：记录问题定义、研究证据、方案矩阵、推荐理由和开放问题
- `solution pack`：记录正式方案、接口设计、时序图、DFX、AR 分解和工作量估算

不要把所有内容都混成一份“万能文档”。

### 3. 先写需求和推荐方案，再写结构化设计内容

solution pack 的主干顺序建议是：

1. 需求描述与目标
2. 推荐方案与理由
3. 架构 / 模块划分
4. 接口设计
5. 关键时序
6. DFX 设计
7. AR 分解
8. 参考代码量估算
9. 剩余风险与开放问题

如果一开始就写接口字段或时序图，而需求和推荐理由还没站稳，通常说明顺序错了。

### 4. 接口设计要写职责和边界，不只写字段

接口设计至少应回答：

- 谁调用谁
- 触发时机是什么
- 请求 / 响应或消息语义是什么
- 异常、失败、超时、重试和回退如何处理
- 接口 ownership 在哪一层
- 当前接口设计还依赖哪些待确认前提

如果下层组件会定义一部分协议，你仍需要说明上层封装层负责什么、为什么需要这一层，以及它与下层接口的边界。

### 5. 时序图优先表达关键交互

对非 trivial 场景，至少给一张 Mermaid 时序图，表达：

- 关键参与者
- 请求流向
- 状态订阅或事件流
- 关键同步 / 异步边界
- 异常或失败处理节点

写 Mermaid 时注意：

- 节点 ID 不要有空格
- 含括号或冒号的标签用双引号
- 不要为了美观添加主题样式

### 6. DFX 设计必须显式落盘

默认从以下通用维度检查：

- 安全
- 性能
- 可靠性
- 可测试性
- 可维护性
- 可观测性
- 可部署性
- 安全性 / 运行风险

每个维度至少回答：

- 当前方案面临什么风险
- 方案如何应对
- 还存在哪些残余风险
- 后续应如何验证

细化口径参考：

- `ahe-se-skills/se-analysis-workflow/references/dfx-default-lenses.md`

### 7. AR 分解按“可交付需求切片”来写

这里的 `AR` 默认按类似 User Story 的需求切片理解。

每个 AR 至少说明：

- `AR ID`
- 用户 / 角色
- 场景 / 目标
- 业务价值
- 依赖或前提
- 验收要点
- 主要风险或备注
- 工作量级别
- 参考代码量范围
- 主要工作项
- 关键不确定性

不要把 AR 写成纯技术任务；AR 是需求切片，不是实现任务。

这里的“每个 AR 的工作量分析”也不是让你把 AR 直接改写成实现任务清单，而是帮助读者判断：

- 哪些 AR 最重
- 重量主要来自哪里
- 哪些前提会显著放大工作量
- 哪些 AR 适合优先拆解或先做预研

细化口径参考：

- `ahe-se-skills/se-analysis-workflow/references/ar-breakdown-rubric.md`

### 8. 代码量估算要同时覆盖整体和 AR 分项

solution pack 中建议同时给出两层估算：

- 整体方案级参考代码量
- 每个 AR 的工作量分析

每个 AR 的工作量分析至少给出：

- `工作量级别`，例如小 / 中 / 大，或中到大
- `参考代码量范围`
- `主要工作项`
- `关键不确定性`

参考代码量估算至少给出：

- 估算范围，例如 `600-900 LoC`
- 范围包含什么
- 范围不包含什么
- 主要不确定性
- 当前置信度

不要把估算写成单点精确数字，也不要把代码量直接等同于工期承诺。

细化口径参考：

- `ahe-se-skills/se-analysis-workflow/references/code-estimation-rubric.md`

### 9. 写回 analysis pack 和 solution pack

analysis pack 至少保留：

- 问题定义
- 研究来源
- 候选方案矩阵
- 推荐理由
- 假设与开放问题

solution pack 至少保留：

- 需求描述
- 推荐方案
- 接口设计
- Mermaid 时序图
- DFX 设计
- AR 分解
- 每个 AR 的工作量分析
- 参考代码量估算

默认结构参考：

- `ahe-se-skills/se-analysis-workflow/references/analysis-output-template.md`

## Output Contract

本节点完成时，至少应产出：

- 一份已更新的 analysis pack
- 一份已落盘的 solution pack
- 明确标注的事实、假设和开放问题

推荐输出：

```markdown
analysis pack 与 solution pack 已完成，当前已具备进入评审、继续细化或进一步拆解的基础。
```

## Common Rationalizations

| Rationalization | Reality |
| --- | --- |
| “研究差不多了，先把推荐方案写出来就行。” | 没有分析包支撑的方案包，容易失去来源和推理链。 |
| “接口字段后面实现时再补。” | 接口设计至少要先说明职责、边界和交互语义。 |
| “DFX 太泛了，先略过。” | DFX 正是帮助新人发现隐藏风险的关键部分。 |
| “代码量估算没法准，干脆别写。” | 估算可以写成范围和置信度，不必伪精确。 |

## Red Flags

- 方案包里没有推荐理由，只剩结论
- 时序图缺失，关键交互只能靠文字猜
- DFX 只写几个形容词，没有风险和缓解
- AR 分解被写成技术任务清单
- 代码量估算没有范围、边界和不确定性说明

## Supporting References

按需读取：

- `ahe-se-skills/se-analysis-workflow/references/analysis-output-template.md`
- `ahe-se-skills/se-analysis-workflow/references/dfx-default-lenses.md`
- `ahe-se-skills/se-analysis-workflow/references/ar-breakdown-rubric.md`
- `ahe-se-skills/se-analysis-workflow/references/code-estimation-rubric.md`
- `ahe-se-skills/se-analysis-workflow/references/embedded-ai-inference-example.md`

## Verification

只有在以下条件都满足时，这个 skill 才算完成：

- 你已经检查输入证据足够，不是靠文档掩盖缺口
- analysis pack 和 solution pack 都已经落盘
- solution pack 已包含需求描述、推荐方案、接口设计、时序图、DFX、AR 和代码量估算
- 事实、假设和开放问题有清晰边界
- 文档已经足够支撑后续评审或进一步细化
