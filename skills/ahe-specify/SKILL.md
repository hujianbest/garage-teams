---
name: ahe-specify
description: 澄清需求并起草可评审规格。适用于尚无已批准规格、现有规格仍是草稿或被 `ahe-spec-review` 退回、用户需要先把范围、验收标准、约束和非目标讲清楚再进入设计的场景；若当前阶段不清或仍需 authoritative workflow routing，先回到 `ahe-workflow-router`。
---

# AHE 需求澄清

创建一份定义“做什么、为什么做、做到什么程度算完成”的需求规格说明，并把它准备到可交给 `ahe-spec-review` 的状态。

## Overview

这个 skill 的职责不是给出设计方案，而是把需求收敛成后续设计和实现不需要靠猜测推进的规格草稿。

高质量规格不只要“写明白”，还要做到：

- 结构化：核心需求能逐条读取，而不是只散落在 prose 里
- 可追溯：每条核心需求都能回指到用户请求、上游工件或外部约束
- 粒度合适：不过大到把多个独立能力打包，也不过散到失去当前轮聚焦
- 可回修：review findings 能回到本节点被定向修订，而不是重新整轮发散

高质量规格的目标不是“写得很长”，而是让后续节点知道：

- 当前轮次要解决什么问题
- 哪些内容必须做
- 哪些内容明确不做
- 成功与失败如何判断
- 哪些约束、依赖和假设会影响后续设计

## When to Use

在这些场景使用：

- 尚无已批准需求规格
- 现有规格仍停留在想法、草稿或待收敛状态
- `ahe-spec-review` 返回 `需修改` 或 `阻塞`，需要按 findings 修订规格
- 用户明确需要先澄清范围、验收标准、边界、约束、非目标，再进入设计或实现

不要在这些场景使用：

- 已有已批准规格，当前问题已经进入 HOW 层设计，改用 `ahe-design`
- 规格已批准、设计也已批准，当前需要任务计划，改用 `ahe-tasks`
- 当前是热修复、增量变更或阶段不清，先回到 `ahe-workflow-router`
- 当前只是要求执行规格评审，且证据支持应进入评审节点，改用 `ahe-spec-review`
- 当前其实还在判断产品是否值得做、哪个 wedge 更强、该先验证什么假设，先去 `ahe-product-skills/using-ahe-product-workflow`

direct invoke 常见信号：

- “先把需求梳理清楚”
- “帮我写 / 补这份规格”
- “这个规格被 review 打回了，继续改”
- “先别做设计，先把范围和验收标准说明白”

## Standalone Contract

当用户直接点名 `ahe-specify` 时，至少确认以下条件：

- 当前请求确实是规格澄清或规格修订工作
- 最少可读取到用户请求、相关规格草稿 / 评审记录、必要项目约定
- 若已存在 `docs/insights/*-spec-bridge.md`，将其视为高价值上游输入
- 当前不是已经更适合进入设计、任务、实现或支线的阶段

如果出现以下任一情况，不要强行继续，应先回到 `ahe-workflow-router`：

- 当前阶段不清
- 请求同时混入增量 / 热修 / review-only 信号
- 上游证据彼此冲突
- 用户点名了 `ahe-specify`，但现有工件显示更应该进入其它节点

## Chain Contract

作为主链节点被串联调用时，默认读取：

- `ahe-workflow-router` 已识别的当前主题与 profile
- `AGENTS.md` 中与规格相关的路径映射、模板覆盖和约束
- `docs/insights/*-spec-bridge.md`（若存在）
- 现有规格草稿、评审记录与 `task-progress.md`
- 用户当前请求中与需求澄清直接相关的部分

本节点完成后应写回：

- 一份可评审规格草稿
- 如有必要，一份与规格相邻的 deferred backlog
- 必要的状态字段与记录路径
- canonical handoff：`ahe-spec-review`

是否进入 `ahe-spec-review`、何时完成 approval step、何时进入 `ahe-design`，都交回父会话 / `ahe-workflow-router` 统一编排。

## Hard Gates

- 在需求规格通过评审并获批之前，不得开始架构设计、任务拆解、脚手架或实现代码编写。
- 在 `ahe-spec-review` 给出“通过”结论之前，不发起 approval step。
- 当前请求若尚未经过 `using-ahe-workflow` 或 `ahe-workflow-router` 的入口判断，不直接开始规格工作。
- 不得为缺失的业务规则、优先级或来源锚点自行编造答案。
- 不得把真实的“后续会做”的需求只藏在 prose 里而不显式标成延后项。

## Quality Bar

交给 `ahe-spec-review` 之前，规格至少应具备这些特征：

- 范围清晰，范围外内容显式写出
- 核心功能需求是可观察、可验证的，并具备稳定 `ID`
- 每条核心 `FR` / 关键 `NFR` 都有需求陈述、验收口径、优先级和 `Source / Trace Anchor`
- 需求粒度适合当前轮次，不把多个独立能力硬塞进一条 `FR`
- 真实的延后需求已被识别，并在需要时写入 deferred backlog，而不是只留成一句“以后再做”
- 关键边界、失败路径或权限差异至少被识别
- 非功能需求和约束不是口号，而是可落地判断的条件
- 需求与设计决策分离，不提前做架构选型
- 阻塞性开放问题已解决，或不会被误带入评审

## Inputs / Required Artifacts

默认情况下，需求规格保存到：

- `docs/specs/YYYY-MM-DD-<topic>-srs.md`

若当前轮次存在真实 deferred requirements，默认与规格相邻保存：

- `docs/specs/YYYY-MM-DD-<topic>-deferred.md`

若当前主题来自 product discovery，优先补充读取：

- `docs/insights/*-spec-bridge.md`

按需再展开读取：

- `docs/insights/*-insight-pack.md`
- `docs/insights/*-concept-brief.md`
- `docs/insights/*-probe-plan.md`

其中 `spec-bridge` 只负责提供更稳定的上游 thesis、范围边界与 unknowns，不替代正式需求规格正文。

若 `AGENTS.md` 为当前项目声明了规格路径映射、优先级体系、章节骨架或模板覆盖，优先遵循这些约定。

起草时默认使用以下 reference：

- `references/requirement-authoring-contract.md`
- `references/granularity-and-deferral.md`

规格草稿交评审前，文档至少应体现：

- 状态字段，例如 `状态: 草稿`
- 主题或范围标识
- 清晰章节结构

若项目尚未形成固定进度记录格式，默认使用：

- `ahe-coding-skills/templates/task-progress-template.md`

交给 `ahe-spec-review` 后，还应同步：

- 规格文档状态
- `task-progress.md` 中的 `Current Stage`
- `task-progress.md` 中的 `Next Action Or Recommended Skill`

## Workflow

按以下顺序执行。

### 1. 了解最少但必要的上下文

只阅读完成规格澄清所需的最少材料：

- 用户当前请求
- `docs/insights/*-spec-bridge.md`（若存在且与当前主题直接相关）
- 与当前范围直接相关的现有项目文档
- 现有规格草稿或评审记录中与当前修订直接相关的部分
- `AGENTS.md` 中与规格路径、模板、团队约束相关的内容
- `task-progress.md` 中的当前阶段记录（如果存在）

先提炼：

- 已确认事实
- 初始目标与成功标准
- 约束、依赖与兼容性线索
- 明显未知项、矛盾点和潜在误解

### 2. 先判断是否需要缩小本轮范围

如果当前请求同时包含多个相对独立的系统、阶段或产品能力，不要直接为整个大而散的目标起草一份规格。

先帮助收敛当前轮次：

- 这一轮最值得优先解决的核心问题是什么
- 哪些能力必须进入当前版本
- 哪些能力应推迟到后续增量

规格要服务于当前这轮可被评审、可被设计的范围，而不是把未来所有想法一次性装进去。

这里先只做范围收敛，不急着决定最终如何拆分到每条 `FR`；真正的拆分和延后判断在后面的粒度步骤完成。

### 3. 分轮澄清需求

澄清时遵循 `Capture -> Challenge -> Clarify`：

- `Capture`：先复述当前理解的目标、对象和范围
- `Challenge`：指出模糊词、打包需求、隐藏假设或缺失边界
- `Clarify`：把想法收敛成可观察、可验证、可评审的表述

默认至少检查这些澄清轮次是否需要：

1. **问题、用户、目标与非目标**
2. **核心行为与关键流程**
3. **边界、异常与失败路径**
4. **约束、依赖、接口与兼容性**
5. **非功能需求与验收口径**
6. **术语与待确认项**

这些轮次是 coverage checklist，不是机械的 6 轮脚本。若当前信息已经覆盖多个主题，可以合并；若当前只剩 1 到 2 个阻塞事实，不要为了“走完流程”再补无关轮次。

提问规则：

- 优先先问会决定当前轮范围、主要角色、成功标准和阻塞业务规则的问题，再问边界、非功能需求和术语细节
- 尽量一次只推进一个主题；但若 2 到 4 个问题共享同一工作流、同一决策或同一阻塞点，应合并成一轮一起问
- 合并提问时，使用编号、短标签或选项，方便用户用简短回复逐项对应
- 如果用户表现出时间紧、回复短或明确要求“快一点”，优先使用“我当前理解是 A / B，对吗？”、“以下哪项更接近？”这类 assume-and-confirm 问法
- 对同一轮已被部分回答的问题，只补问 delta，不重复回顾整个主题
- 如果只剩 1 到 3 个阻塞事实，优先在一个回合中问完，不再机械展开额外澄清轮
- 优先用具体场景、反例和失败路径来问
- 把模糊表述替换成可衡量描述
- 如果用户未给出范围外内容，要主动询问
- 如果用户已经提供足够完整的信息，不机械地把所有轮次都问一遍
- 若用户明确授权使用默认假设或暂时无法提供细节，把该内容写成 `ASM` 并标明失效风险，再请用户确认，而不是 silently invent
- 每轮结束前，先用 1 到 3 句总结已锁定事实与仍待确认项，再决定是否进入下一轮

若当前是因为 `ahe-spec-review` 返回 `需修改` 或 `阻塞` 而重新进入本 skill：

- 先读取 review findings
- 优先修复阻塞性缺口
- 只针对仍阻塞修订的问题补充确认
- 不要重新发起整轮无关澄清

### 4. 先整理 requirement rows，再写文档

在写规格前，先把已确认内容整理成结构化 requirement rows 或等价结构。默认至少区分：

- `FR`：功能需求
- `NFR`：非功能需求
- `CON`：约束
- `IFR`：接口与依赖
- `ASM`：假设
- `EXC`：范围外内容

对于 non-trivial 的规格，核心功能需求默认使用稳定编号，例如 `FR-001`、`FR-002`。非功能需求可使用 `NFR-001`。

最小契约详见 `references/requirement-authoring-contract.md`。若项目模板已有等价字段，优先遵循模板；否则默认每条核心需求至少要有：

- `ID`
- `Statement`：可观察、可判断的需求陈述
- `Acceptance`：至少一个可验证验收标准
- `Priority`：若项目未声明其它体系，默认 `Must` / `Should` / `Could` / `Won't`
- `Source / Trace Anchor`：回指用户请求、上游工件、review finding 或外部约束

要求如下：

- 每条核心功能需求要能单独理解
- 不要把多个彼此独立的行为硬写成一条需求
- 每条核心功能需求都应配至少一个可验证验收标准
- 验收标准优先使用场景化表达，例如 Given / When / Then，但不为格式牺牲清晰度
- 对关键失败路径、边界条件和权限冲突，也至少写出对应验收口径
- 若来源锚点或优先级不清楚，回到用户或上游工件确认，不自行编造

### 5. 做粒度检查与延后判断

起草正文前，先根据 `references/granularity-and-deferral.md` 做一次粒度检查。

至少检查这些问题：

- 是否存在多角色打包、CRUD 打包、场景爆炸、多状态混写、时间耦合等 `G1-G6` 信号
- 是否有些需求虽然真实存在，但已经清楚属于后续增量，而不是当前轮交付
- 当前规格中的 `EXC` 是真正的非目标，还是其实应该被回收到 deferred backlog

处理规则：

- 1 到 3 个不改变本轮范围的明显拆分，可以在草稿中给出拆分建议和理由
- 若拆分会产生 4 个及以上子需求，或会改变当前轮范围边界，必须向用户显式确认
- 若某项需求只是当前轮不做，但后续预计会通过 `ahe-increment` 回收，则写入 deferred backlog
- 若某项只是明确非目标，不必强行进入 backlog，留在 `EXC` 即可
- 拆分后的子需求要保留来源锚点和优先级，不得只保留父需求编号
- 若拆分只是把当前轮内的复合需求机械拆开，且不改变范围、优先级或延后归属，可以作为直接修文处理
- 若拆分会改变当前轮范围、引入新的 deferred backlog 判断，或改变已确认优先级 / 角色边界，则不再属于纯 `LLM-FIXABLE`；必须先向用户确认拆分与范围决策

### 6. 起草规格

若 `AGENTS.md` 为当前项目声明了规格模板、章节骨架或命名要求，优先遵循这些约定。

若未提供模板覆盖，则使用以下默认结构：

```markdown
# <主题> 需求规格说明

- 状态: 草稿
- 主题: <主题>

## 1. 背景与问题陈述
## 2. 目标与成功标准
## 3. 用户角色与关键场景
## 4. 范围
## 5. 范围外内容
## 6. 术语与定义（按需）
## 7. 功能需求
## 8. 非功能需求
## 9. 外部接口与依赖（按需）
## 10. 约束
## 11. 假设（按需）
## 12. 开放问题
```

编写要求：

- 背景描述为什么要做，不写成方案介绍
- 功能需求描述可观察行为，而不是实现手段
- 非功能需求描述可判断条件，而不是空泛形容词
- 约束描述硬性限制
- 假设要写明失效风险或影响
- 开放问题只能保留那些不会阻塞评审的问题
- 若模板没有单独的 requirement row 结构，也要在章节内部保留 `ID / Priority / Source / Acceptance` 这些语义
- 若存在 deferred backlog，应在范围外内容或等价章节中明确指向该 backlog，而不是只写“后续再做”
- 不要为追求形式统一而破坏项目已声明的模板结构；优先保留模板，再把契约语义嵌入进去

### 7. 区分开放问题

写规格时，明确区分：

- 已确认事项：可直接写入正文
- 需用户确认事项：必须先问清再写
- 非阻塞开放问题：可以保留，但不能影响设计主干判断
- 阻塞性开放问题：交给 `ahe-spec-review` 前必须已经解决

以下情况通常视为阻塞性开放问题：

- 核心范围仍然摇摆
- 主要用户或主要成功标准未定
- 核心流程的关键结果无法判断
- 关键约束、依赖或兼容要求未知
- 关键非功能要求完全缺失，且会显著影响设计

### 8. 评审前自检

交给 `ahe-spec-review` 前，请确认：

- 问题陈述、目标和主要用户清楚
- 范围内与范围外内容都已显式说明
- 核心功能需求逐条可观察、可验证
- 核心 `FR` / 关键 `NFR` 都具备稳定 `ID`
- 功能需求与验收标准的粒度基本对应
- 核心需求都写明了 `Priority` 与 `Source / Trace Anchor`
- `G1-G6` 明显命中的 oversized requirements 已被拆开、确认或显式标注待确认
- 真实 deferred requirements 已写入 backlog，或已明确说明当前没有这类项
- 关键异常、边界、失败路径或权限差异至少已识别
- 模糊词已量化、替换或删除
- 需求陈述中没有混入设计选择
- 非功能需求不是“快 / 稳 / 好用”式口号
- 没有把阻塞性开放问题留到评审之后

### 9. 派发 reviewer subagent 与定向回修

草稿准备好后，不要在父会话里内联执行 `ahe-spec-review`。正确做法是：

1. 将规格草稿保存到约定路径
2. 若存在 deferred backlog，一并保存到约定路径
3. 组装最小 spec review request
4. 启动独立 reviewer subagent，并在该 subagent 中调用 `ahe-spec-review`
5. 由 reviewer subagent 写 review 记录并回传结构化摘要
6. 父会话读取 reviewer 返回结果后继续：
   - 若结论为 `通过`，由父会话完成 approval step（`interactive` 下等待真人，`auto` 下写 approval record）
   - 若结论为 `需修改`，携带关键 findings 回到本 skill 修订
   - 若结论为 `阻塞` 且 `reroute_via_router=true`（或历史字段 `reroute_via_starter=true`）或 `next_action_or_recommended_skill=ahe-workflow-router`，回到 `ahe-workflow-router` 重编排
   - 其他 `阻塞`，携带关键 findings 回到本 skill 补条件或修订

当本 skill 因 review findings 重新进入时：

- 对 `LLM-FIXABLE` findings，只修 findings 直接指向的条目，不重新发散整份规格
- 但若某条被标为 `LLM-FIXABLE` 的拆分 / 去耦合问题，实际修到一半发现会改变当前轮范围、优先级或 deferred backlog 归属，必须立刻转为对用户的定向确认，不能静默继续修
- 对 `USER-INPUT` findings，只向用户提出定向问题，不把整轮澄清重新问一遍
- 若 findings 同时包含可直接修文的项和需用户确认的项，先收集用户输入，再一起回修，减少 reviewer 循环次数
- 若当前只剩 1 到 3 个 `USER-INPUT` finding，优先在一个回合里编号问完，不重新做整段 `Capture -> Challenge -> Clarify` 开场
- 对用户的简短回复，先复述当前理解并请求确认 / 纠正，再决定是否继续追问
- 在 interactive 模式下，对用户只展示当前必须回答的问题；`LLM-FIXABLE` 项由本节点直接处理，不把可直接修文的问题转嫁给用户
- 对同一份草稿，若已经历 2 轮 reviewer 循环且仍无新用户输入，不再静默反复修文；应把剩余阻塞点显式展示给用户
- 若 findings 指向 route / stage / profile / 上游证据冲突，不在本节点硬修，交回 `ahe-workflow-router`

不要在 `ahe-specify` 阶段请求 approval step；对应 approval step 只发生在 `ahe-spec-review` 返回“通过”之后。

## Output Contract

本节点完成时，至少应产出：

- 一份可评审规格草稿
- 如适用，一份 deferred backlog
- 可供 reviewer 定位的最小上下文
- canonical handoff：`ahe-spec-review`

交接前请同步：

- 将草稿保存到约定路径
- 若存在 deferred backlog，将其保存到映射路径或默认相邻路径
- 将 `task-progress.md` 中的 `Current Stage` 更新为能唯一映射到“规格草稿已完成、等待评审”的规范阶段名
- 将 `task-progress.md` 中的 `Next Action Or Recommended Skill` 更新为 `ahe-spec-review`

推荐输出：

```markdown
需求规格草稿已起草完成，下一步应派发独立 reviewer subagent 执行 `ahe-spec-review`。

推荐下一步 skill: `ahe-spec-review`
```

如果草稿仍未达到评审门槛，不要伪造 handoff；明确写出仍缺什么，再继续本节点修订。

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| “需求已经差不多清楚了，直接做设计吧” | 规格未通过评审前，不进入设计。 |
| “这些细节实现时自然会知道” | 范围、约束、验收标准必须先在规格里写清楚。 |
| “先写个大概，范围外内容不用专门说明” | 范围外内容必须显式写出。 |
| “用户没提验收标准，就先按常识理解” | 成功标准必须明确，不能靠默认理解。 |
| “我先顺手提个架构方案更高效” | 规格阶段不提前做设计决策。 |
| “这些开放问题以后再说，不影响继续写” | 会阻塞评审的问题必须先澄清。 |
| “这个需求很大，先全部塞进一份规格” | 先拆清当前轮次范围，再写规格。 |
| “优先级和来源只是 review 时再补一下就行” | 每条核心需求在起草时就应具备 `Priority` 和 `Source / Trace Anchor`。 |
| “后续再做的项写进范围外内容一句话就够了” | 对真实 deferred requirements，必要时要写成可回收的 deferred backlog。 |
| “一个 FR 先把多个角色和流程写在一起，后面实现时自然会拆” | 命中 `G1-G6` 的 oversized requirement 应在规格阶段先拆或先确认。 |

## Red Flags

- 从用户想法直接跳到架构设计
- 把头脑风暴笔记当成已批准规格
- 在规格里直接写任务、里程碑或提交计划
- 把多个独立能力打包成一句“大需求”
- 核心需求没有 `Priority` 或没有 `Source / Trace Anchor`
- 只写 happy path，不写边界和失败路径
- 除非是硬性外部约束，否则提前使用 class、endpoint、table、framework 这类设计语言
- 已经决定“后续再做”的能力只留在 prose 里，没有 backlog 或明确回收方式
- 把成功标准留成隐含信息
- handoff 已缺失却声称“规格可以继续往下走”

## Verification

只有在存在一份可评审需求规格草稿，并且它已经准备好交给 `ahe-spec-review` 时，这个 skill 才算完成。

交接前确认：

- [ ] 规格草稿已保存到约定路径
- [ ] 范围、范围外内容、核心功能需求、关键约束和主要非功能需求已写清
- [ ] 核心 `FR` / 关键 `NFR` 已具备 `ID`、`Priority`、`Source / Trace Anchor`
- [ ] 明显 oversized 的需求已按 `G1-G6` 做过拆分、确认或显式保留理由
- [ ] 真实 deferred requirements 已写入 backlog，或已明确不存在
- [ ] 阻塞性开放问题已解决，或明确为空 / `无`
- [ ] 规格草稿已达到可交 reviewer 的质量门槛
- [ ] `task-progress.md` 或等价状态工件已写回 canonical stage 与 `Next Action Or Recommended Skill`
- [ ] 下一步明确为 `ahe-spec-review`
