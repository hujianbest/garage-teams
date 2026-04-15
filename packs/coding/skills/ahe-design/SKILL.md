---
name: ahe-design
description: 产出可评审实现设计。适用于需求规格已批准、设计尚未批准，且当前需要在任务规划或编码前明确架构、模块边界、关键接口、数据流、技术决策和测试策略的场景；若规格仍未稳定、当前阶段不清或仍需 authoritative workflow routing，先回到 `ahe-workflow-router`。
---

# AHE 设计

把已批准规格转化为可评审的设计文档，说明"如何"实现，让后续任务规划与实现不再靠猜测推进。

## When to Use

使用：

- 需求规格已批准，但设计尚未批准
- `ahe-design-review` 返回 `需修改` 或 `阻塞`，需要按 findings 修订
- 当前问题已进入 HOW 层，需要明确架构、模块边界、接口、数据流、技术决策和测试策略

不使用：

- 规格仍是草稿/待评审/待批准 → `ahe-specify` / `ahe-spec-review`
- 设计已批准，需要任务计划 → `ahe-tasks`
- 只要求执行设计评审 → `ahe-design-review`
- 阶段不清或证据冲突 → `ahe-workflow-router`

直接调用信号："开始做设计"、"把实现方案写出来"、"设计被打回了"、"先别拆任务，把架构想清楚"。

## Chain Contract

读取：已批准规格、`task-progress.md`、`AGENTS.md` 路径映射，以及其中声明的项目级设计原则锚点（若存在），外加最少必要技术上下文。

产出：可评审设计草稿 + 设计层追溯与关键决策。

Handoff：`ahe-design-review`。

## Hard Gates

- 设计未评审获批前，不得拆解任务或编写实现代码
- `ahe-design-review` 给出"通过"前，不发起 approval step
- 未经 `using-ahe-workflow` 或 `ahe-workflow-router` 入口判断，不直接开始设计

## Design Constraints

### MUST DO

- 用 ADR 记录所有影响后续任务规划的关键决策
- 逐项处理非功能需求，明确它们如何影响方案选择和落到哪些模块
- 至少比较两个可行方案，权衡 trade-offs
- 分析关键路径的失败模式并给出缓解策略
- 识别架构模式并说明选择理由和天然限制
- 提供最少必要的架构视图（优先 Mermaid）

### MUST NOT DO

- 为假设的未来需求过度设计（YAGNI）
- 不评估备选方案就选定技术或模式
- 忽略运维复杂度和部署成本
- 在没理解需求前就开始画架构图
- 跳过安全性和隐私考量

## Core Workflow

### 1. 阅读已批准规格并提取设计驱动因素

读取 `AGENTS.md` 路径映射、`task-progress.md` 当前阶段、已批准规格相关部分。

提取：核心范围、验收标准、约束、非功能需求、集成点、关键需求编号、会影响架构选择的开放问题。

规格中若有阻塞架构判断的未决问题：
- 会改变范围/验收标准/约束/接口的 → 回到 `ahe-workflow-router`
- 属于实现上下文级澄清、不改变需求边界的 → 可在当前轮次补充确认

### 2. 了解最少必要技术上下文

阅读现有架构/项目布局、当前框架与运行时约束、已知部署/集成/兼容限制、可复用模块与边界。

识别架构模式（按 `references/architecture-patterns.md` 的维度判断）。

不提前进入实现规划。

### 3. 提出 2-3 个候选方案并形成结构化决策

对每个候选方案说明：如何工作、适合原因、主要优缺点、对约束和 NFR 的影响、关键风险。

推荐方案时使用 ADR 格式记录关键决策（按 `references/adr-template.md`）。

若是因 `ahe-design-review` 打回而重入：先读评审 findings → 修复阻塞问题 → 不重做未受影响的部分。

### 4. 校验设计原则

选定方案后、编写设计文档前，校验以下维度：

若 `AGENTS.md` 声明了项目级设计原则、architecture principles、soul docs 或等价价值锚点，先按声明路径读取，并把它作为候选方案筛选准则；不要假设固定目录、固定文件名或 Garage 特定路径。

- **YAGNI 校验**：决策是否由当前已确认需求驱动？"未来可能需要"标记为过度工程候选
- **复杂度适配**：Solo + 本地运行 → 不引入微服务/消息队列/分布式数据库；文档型 → 不引入重型框架；组件 < 10 → 不需要服务发现
- **模块边界**：依赖单向（内层不依赖外层）、最小知识（接口只暴露最小必要信息）、开闭原则
- **失败模式**：按 `references/failure-modes.md` 分析关键路径，确认单点故障、错误处理四层次
- **可测试性**：关键行为可隔离验证；存在 Walking Skeleton 最薄端到端路径

### 5. 编写设计文档

按 `references/design-doc-template.md` 的默认结构（或 `AGENTS.md` 覆盖的模板）。

明确区分规格层（做什么）、设计层（如何实现）、任务层（分步实施，属于 `ahe-tasks`）。

对非 trivial 设计，提供 2-3 类最少必要视图（逻辑架构、组件/接口关系、关键交互、数据视图），优先 Mermaid。

### 6. 评审前自检与 handoff

交 `ahe-design-review` 前确认：

- [ ] 设计不是规格复述，也不是实现说明
- [ ] 至少比较了两个可行方案并说明选定理由
- [ ] 关键决策用 ADR 格式记录（含可逆性评估）
- [ ] NFR 逐项落实到具体模块/机制（按 `references/nfr-checklist.md`）
- [ ] 失败模式覆盖关键路径
- [ ] 明确列出排除项和延后项
- [ ] 设计草稿已保存到约定路径
- [ ] `task-progress.md` 已更新 Current Stage 和 Next Action

准备好后，启动独立 reviewer subagent 执行 `ahe-design-review`，不在父会话内联评审。

## Reference Guide

按需加载详细参考内容：

| 主题 | Reference | 加载时机 |
|------|-----------|---------|
| 项目级设计原则锚点 | `AGENTS.md`（查找 design principles / architecture principles / soul docs 的声明路径） | 项目存在这类价值锚点时，先按声明路径加载并用于筛选候选方案 |
| ADR 模板 | `references/adr-template.md` | 记录关键决策时 |
| NFR 检查清单 | `references/nfr-checklist.md` | 处理非功能需求时 |
| 失败模式分析 | `references/failure-modes.md` | 分析关键路径韧性时 |
| 架构模式选择 | `references/architecture-patterns.md` | 识别架构模式时 |
| 设计文档模板 | `references/design-doc-template.md` | 编写设计文档时 |

## Red Flags

- 设计文档写成实现伪代码
- 复制需求规格而无设计决策
- 只给一个方案不讨论权衡
- 设计文档里直接拆任务
- 只写模块名不写边界、交互和契约
- NFR 只在概述中出现，没落实到具体模块
- 决策理由含"未来可能需要"而无当前需求支撑
- 没分析关键路径失败模式
- handoff 缺失却声称"设计可以直接往下走"

## Output Contract

完成时产出：

- 可评审设计草稿（保存到约定路径）
- 设计驱动因素、关键决策、边界与最少必要视图
- `task-progress.md` 更新：Current Stage → 设计草稿已完成、等待评审；Next Action → `ahe-design-review`

推荐输出：

```markdown
设计文档草稿已起草完成，下一步应派发独立 reviewer subagent 执行 `ahe-design-review`。

推荐下一步 skill: `ahe-design-review`
```

如果设计稿仍未达评审门槛，不伪造 handoff；明确还缺什么，继续修订。
