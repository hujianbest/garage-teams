---
name: se-analysis-workflow
description: 面向方案分析与需求拆解的 SE 工作流入口。适用于用户对现有系统不熟、需求描述仍粗糙、需要先通过访谈澄清，再结合仓库调研、网络资料和多方案对比收敛出可评审分析结果的场景；若当前只是局部问题且节点已明确，可直接进入 `se-discovery`、`se-research-and-options` 或 `se-design-pack`。
---

# SE Analysis Workflow

## Overview

这个 skill 是一套独立的 `se-*` 分析 workflow 入口，目标是把“资深 SE 带着新人一起做方案分析”的工作方式沉淀成可复用流程。

它不属于 `ahe-*` 主链，也不替代 `ahe-specify`、`ahe-design`、`ahe-tasks`。它更适合用在这些场景：

- 需求还停留在口头描述或粗糙想法
- 你对当前系统架构、代码和现有能力不熟
- 你需要先搞清楚应该问什么、查什么、比较什么，再谈方案
- 你最终想产出一套面向评审的分析包和方案包，而不是直接写代码

## When to Use

在这些场景使用：

- 用户希望“像经验老到的 SE 一样”陪他做分析、访谈、调研和方案收敛
- 用户只给出一个业务或技术场景，但还没有稳定的需求描述、接口边界和约束
- 你需要在仓库调研、网络研究和多方案比较之间来回切换
- 你需要输出需求描述、方案、接口设计、时序图、DFX 设计、AR 分解和参考代码量估算
- 你需要并行启动多个只读 agent，分别研究仓库、外部资料和方案风险

不要在这些场景使用：

- 当前只是实现已有明确方案，应该进入编码或 AHE 主链
- 当前只是回答一个局部技术问题，不需要完整分析包
- 当前只是要求做 `ahe-*` 节点级工作，例如规格评审、设计评审或任务拆解
- 当前已经有足够稳定的输入，并且你只需要一个具体节点，例如 `se-design-pack`

## Standalone Contract

当用户直接点名这个 skill 时，至少确认：

- 当前目标是“先分析，再收敛方案”，而不是“直接实现”
- 至少存在一个可以命名的话题、场景或问题陈述
- 允许通过访谈进一步缩小范围

如果以下任一情况成立，不要停留在本 skill：

- 用户真正要的是局部调研，直接进入 `se-research-and-options`
- 用户真正要的是结构化产出，且证据已经齐全，直接进入 `se-design-pack`
- 用户真正要的是 AHE 主链工作，回到 `using-ahe-workflow`

## Local Workflow

按以下顺序工作。

### 1. 先判断当前从哪里起步

将当前请求归入以下三类之一：

- `blank-start`：只有粗糙场景，没有稳定需求和边界
- `partial-context`：已经有一些背景、文档或代码线索，但还缺系统调研和方案比较
- `synthesis-ready`：访谈和研究已基本完成，主要需要收敛输出

对应默认起点：

- `blank-start` -> `se-discovery`
- `partial-context` -> `se-research-and-options`
- `synthesis-ready` -> `se-design-pack`

### 2. 维持三层分离

不管从哪个节点起步，都保持以下三层分离：

- `事实`：用户已确认、仓库已观察、外部资料已引用的内容
- `推断`：基于事实形成的解释或判断
- `假设 / 开放问题`：当前仍未证实、但会影响方案选择的内容

如果这三层被混在一起，后续方案就会看起来完整、实则靠猜。

### 3. 使用只读并行，而不是多写并发

调研阶段允许并行，但只允许并行做这些事：

- 仓库结构与现有能力盘点
- 外部资料检索与模式调研
- 方案选项优缺点挑战

最终写回分析结论和方案包时，保持单 writer。不要让多个 agent 同时改主文档。

### 4. 把 workflow 结果沉淀成两类工件

默认输出分成两类：

- `docs/analysis/YYYY-MM-DD-<topic>-analysis-pack.md`
- `docs/designs/YYYY-MM-DD-<topic>-solution-pack.md`

前者记录问题框定、访谈结果、研究证据、候选方案和开放问题；后者记录推荐方案、接口设计、时序图、DFX、AR 分解和工作量估算。

### 5. 用本地 handoff，不冒充 AHE canonical 节点

这套 `se-*` workflow 是独立工作流，不是 `ahe-*` router 已知节点。

因此：

- 不要把 `se-*` 名称写进 AHE canonical `Next Action Or Recommended Skill`
- 不要假装 `ahe-workflow-router` 会理解 `se-*` 本地 handoff
- 只在本 workflow 自己的文档和对话里使用 `se-*` 下一步表达

## Node Selection

### 进入 `se-discovery`

满足任一条件即可：

- 需求目标、范围、参与者或成功标准仍模糊
- 术语含义不稳定，例如团队内部简称、接口名、流程名
- 你还说不清楚“到底要分析什么”

### 进入 `se-research-and-options`

满足任一条件即可：

- 问题已经能描述，但不知道当前框架和代码里有没有现成能力
- 需要查外部资料和设计模式
- 需要比较 2 到 3 个候选方案，并明确 trade-off

### 进入 `se-design-pack`

只有在以下条件都满足时才进入：

- 需求和约束已经足够稳定
- 已有可引用的仓库证据和外部资料
- 已经形成候选方案与推荐方向
- 剩余开放问题不会阻塞输出主干结构

## Output Contract

本 skill 自己不负责完成全部分析，而是负责：

- 判断当前最合适的起点
- 解释为什么从该节点起步
- 把上下文交给下游 `se-*` 节点

推荐输出应至少说明：

- 当前入口分类：`blank-start` / `partial-context` / `synthesis-ready`
- 推荐进入的本地节点：`se-discovery` / `se-research-and-options` / `se-design-pack`
- 1 到 3 条关键原因

## Supporting References

按需读取：

- `ahe-se-skills/se-analysis-workflow/references/interview-checklists.md`
- `ahe-se-skills/se-analysis-workflow/references/analysis-output-template.md`
- `ahe-se-skills/se-analysis-workflow/references/dfx-default-lenses.md`
- `ahe-se-skills/se-analysis-workflow/references/ar-breakdown-rubric.md`
- `ahe-se-skills/se-analysis-workflow/references/code-estimation-rubric.md`
- `ahe-se-skills/se-analysis-workflow/references/embedded-ai-inference-example.md`
- `agents/se-repo-researcher.md`
- `agents/se-web-researcher.md`
- `agents/se-option-challenger.md`

## Common Rationalizations

| Rationalization | Reality |
| --- | --- |
| “先按我理解写个方案，后面再补访谈。” | 没有先澄清范围和术语，后面的方案通常是在替用户做决定。 |
| “已经查过一点代码了，可以直接收敛。” | 仓库里看见几个文件，不等于完成了结构化调研和选项比较。 |
| “调研阶段让几个 agent 一起写文档更快。” | 并行适合做只读研究，不适合并发改主文档。 |
| “这套 workflow 也能直接当 AHE 下一节点。” | `se-*` 是独立 workflow，不是 AHE router 的 canonical 节点。 |

## Red Flags

- 还没澄清核心问题就开始推荐唯一方案
- 把猜测写成“系统当前就是这样”
- 没有记录开放问题，却声称分析已闭环
- 多个 agent 同时改分析主文档
- 把 `se-*` 名字写进 AHE canonical handoff 字段

## Verification

只有在以下条件满足时，这个 skill 才算正确完成：

- 你已经判断当前应该从哪个本地节点起步
- 你已经明确区分事实、推断和假设
- 你已经说明并行部分只用于只读研究
- 你没有让 `se-*` workflow 冒充 AHE 主链节点
- 你给出的下一步足够明确，能直接进入某个 `se-*` 节点
