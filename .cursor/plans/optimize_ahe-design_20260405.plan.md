# 优化 `ahe-design` 方案

## 目标

把 `skills/ahe-design/SKILL.md` 从“能产出可评审设计草稿”的 skill，提升为“能稳定产出高质量实现设计文档”的 skill。

这次优化只增强 `ahe-design` 的设计深度、文档结构和评审对齐能力，不改 AHE 主链契约：

- 仍然必须先经过 `skills/ahe-workflow-starter/SKILL.md` 路由
- 仍然只在已批准规格基础上产出 HOW 层设计
- 仍然通过 `skills/ahe-design-review/SKILL.md` 进入评审
- 仍然禁止在 `ahe-design` 阶段发起真人批准
- 仍然保持 `ahe-design -> ahe-design-review -> 真人确认 -> ahe-tasks` 的顺序

## 当前问题

当前 `skills/ahe-design/SKILL.md` 已经具备正确的门禁和基本流程，但仍偏“可用设计草稿生成器”，主要短板是：

- 虽要求设计覆盖需求，但没有把“需求 -> 模块/接口/流程”的追溯关系制度化
- 候选方案比较存在，但重大设计决策缺少稳定记录形态，容易只给出结论，不给出后果与风险
- 默认文档骨架对架构视图、接口契约、NFR 落点、风险与可测试性约束不够操作化
- 缺少对图示、关键视图和设计连贯性的最小产出标准，容易生成文字型设计而不是可执行设计
- 交付给 `ahe-design-review` 之前只有轻量自检，缺少按 review 视角的预检
- 对“支撑 `ahe-tasks`，但不能直接变成任务计划”的边界说明仍不够强

## 优化方向

### 1. 强化“设计输入提取”

在读取规格阶段，不只提取范围、约束和验收标准，还要显式提取：

- 关键需求编号或稳定需求条目
- 关键 NFR 阈值
- 外部接口与兼容性要求
- 影响架构选择的风险与开放问题

为什么这么改：

- 高质量设计不是从“规格大意”出发，而是从明确的设计驱动因素出发
- 如果输入提取太粗，后续方案比较和设计覆盖都容易漂

主要参考：

- `references/longtaskforagent-main/skills/long-task-design/SKILL.md`
- `skills/ahe-design-review/SKILL.md`

### 2. 把候选方案比较升级为“决策记录”

保留当前 2 到 3 个候选方案的要求，但增加结构化决策要求：

- 背景 / 决策上下文
- 候选方案
- 选定方案
- 主要收益
- 主要代价
- 关键风险与缓解思路

为什么这么改：

- 当前版本要求比较方案，但没有强制记录“为什么选、代价是什么”
- 这样会让设计文档更像意见，而不是可审计的设计决策

主要参考：

- `references/everything-claude-code-main/skills/architecture-decision-records/SKILL.md`
- `references/longtaskforagent-main/skills/long-task-design/SKILL.md`

### 3. 升级默认设计文档骨架

保留 AHE 轻量原则，但把默认结构增强为更高质量的设计框架，例如强化：

- 设计驱动因素
- 需求覆盖与追溯
- 候选方案与决策记录
- 架构视图
- 模块职责与边界
- 数据流 / 控制流 / 关键时序
- 接口与契约
- NFR 落地方式
- 测试策略
- 风险、待定项与任务规划准备度

为什么这么改：

- `ahe-design-review` 的检查维度已经隐含要求这些内容
- 如果默认骨架不承接这些维度，产物质量就很依赖临场发挥

主要参考：

- `skills/ahe-design-review/SKILL.md`
- `references/longtaskforagent-main/skills/long-task-design/SKILL.md`

### 4. 引入“最少必要设计视图”要求

对非 trivial 设计，要求至少产出能支撑理解的关键视图，例如：

- 逻辑架构视图
- 模块 / 组件关系视图
- 关键流程或关键交互视图

视图形式保持轻量，可用 Mermaid，不要求为每个小点都画图。

为什么这么改：

- 高质量设计要能让评审与后续任务拆解快速建立共同模型
- 只靠文字很容易产生“看起来完整，其实不连贯”的问题

主要参考：

- `references/longtaskforagent-main/skills/long-task-design/SKILL.md`
- `docs/skills_refer.md` 中对高质量设计类 skill 的归纳

### 5. 强化接口与契约章节

把“接口与契约”从泛泛要求提升为明确检查项，至少覆盖：

- 关键输入 / 输出
- 错误或异常语义
- 兼容性与边界
- 外部依赖约束
- 为什么这些接口已经足够支撑后续任务规划

为什么这么改：

- `ahe-design-review` 明确会检查接口准备度
- 如果这一层不清楚，`ahe-tasks` 就只能在任务拆解阶段补设计

主要参考：

- `skills/ahe-design-review/SKILL.md`
- `references/longtaskforagent-main/skills/long-task-design/SKILL.md`

### 6. 增加“需求追溯与任务规划准备度”说明

在设计中明确：

- 哪些关键需求被哪些模块、接口或流程承接
- 哪些部分已经足以支撑任务拆解
- 哪些仍然只是设计层面的开放点

为什么这么改：

- `ahe-design` 需要为 `ahe-tasks` 服务，但又不能直接下沉成任务计划
- 这要求 skill 明确说明“设计输出怎样成为任务规划输入”

主要参考：

- `skills/ahe-tasks/SKILL.md`
- `skills/ahe-design-review/SKILL.md`

### 7. 把评审前自检升级为“按 review 维度干跑”

在正式交给 `ahe-design-review` 之前，用接近 review 的维度做自检：

- 是否覆盖关键需求
- 是否体现约束与 NFR
- 是否解释清楚边界与交互
- 是否足以支撑任务规划
- 是否存在关键设计风险未处理

为什么这么改：

- 这不是替代 `ahe-design-review`
- 目标是减少低质量设计草稿进入 review，降低往返成本

主要参考：

- `skills/ahe-design-review/SKILL.md`
- `references/skills-main/skills/doc-coauthoring/SKILL.md`

## 明确不做的事

- 不把 `ahe-design` 变成 `ahe-design-review`
- 不把设计文档写成任务计划或实现说明
- 不引入重型、多层级的复杂流程，保持 AHE 单人可维护性
- 不照搬 `long-task-design` 的整套重流程，只轻量借鉴其中高价值结构

## 计划中的实际改动

会对 `skills/ahe-design/SKILL.md` 做一轮聚焦重构，预计包括：

- 收紧 `description`
- 增强“读取规格输入”的提取维度
- 升级候选方案比较为结构化决策记录
- 升级默认设计文档骨架
- 增加最少必要视图要求
- 强化接口与契约、NFR 落地、需求追溯和任务规划准备度说明
- 升级评审前自检
- 调整 handoff 文案与 `task-progress.md` 阶段写法，使其更贴近 `ahe-workflow-starter` 的连续执行模型

## 预期效果

优化后的 `ahe-design` 应该具备这些特征：

- 不只是“写出设计文档”，而是能稳定产出可追溯、可评审、可拆解的设计稿
- 更清楚地区分 WHAT / HOW / TASKS 三层边界
- 更容易一次通过 `ahe-design-review`，或者至少让 review 反馈更聚焦
- 给 `ahe-tasks` 的输入更稳定，减少任务拆解阶段反补设计
