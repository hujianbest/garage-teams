# F001: Garage Agent 操作系统

- 状态: 草稿
- 主题: Garage Agent 操作系统
- 日期: 2026-04-15

## 1. 背景与问题陈述

当前 `Garage` 是一个基于 Markdown 的静态 skills 工作区，包含 26 个 AHE workflow skills（coding + product insights）。这些 skills 以文档形式存在，需要用户手动在 Claude Code 等 AI 工具中调用执行。

这种静态模式存在以下核心问题：

1. **缺乏运行时能力**：skills 无法主动执行，必须依赖用户手动调用 AI 工具
2. **知识无法积累**：每次会话都是独立的，agent 无法从历史交互中学习和积累经验
3. **工具对接不足**：虽然定义了丰富的 workflow，但缺乏与 Claude Code 等 coding agent 的深度集成
4. **成长机制缺失**：无法从使用中总结新 skills、产生新 Agent、持续演化
5. **数据分散**：工作成果、经验、配置等散落在不同位置，难以统一管理和迁移

用户期望 Garage 演进为一个「个人 Agent 操作系统」—— 一个可以随身携带、不断成长的能力基座，而不仅仅是静态的技能文档集合。

## 2. 目标与成功标准

### 2.1 核心目标

将 Garage 从静态 markdown skills 演进为一个具有以下能力的 Agent 操作系统：

1. **知识管理**：能够整理和存储知识，在交互中积累经验并形成可复用的知识库
2. **代码开发**：能够对接 Claude Code 等 coding agent，完成开发任务的端到端执行
3. **内容生产**：能够辅助写博客、写文档、做研究等内容生产任务
4. **工具对接**：能够连接更多工具扩展能力，形成可扩展的工具生态
5. **自我成长**：能够总结经验产生新 skills、产生新 Agent、持续积累演化

### 2.2 成功标准

- 用户可以在 Claude Code 中直接调用 Garage 的运行时能力，无需手动切换工具
- Agent 可以从历史会话中学习和积累知识，形成可查询的知识库
- 所有数据存储在 Garage 仓库内部，不依赖第三方平台
- 用户可以轻松迁移整个工作区到不同环境，能力不丢失
- 系统采用渐进式架构，可以从简单开始逐步演进到自建运行时

## 3. 用户角色与关键场景

### 3.1 主要用户角色

- **Solo Creator**：独立开发者、创作者，需要一个能够随工作成长的 AI 能力基座
- **Knowledge Worker**：知识工作者，需要管理和积累领域知识
- **Developer**：开发者，需要在 Claude Code 等 coding agent 环境中使用 AI 辅助开发

### 3.2 关键场景

1. **代码开发场景**：用户在 Claude Code 中开发功能，Garage 自动记录开发过程，积累可复用的开发经验
2. **知识积累场景**：用户与 Agent 交互产生知识，Garage 自动整理并存储到知识库
3. **内容生产场景**：用户需要写技术博客，Garage 基于已有知识和开发经验辅助生成内容
4. **工具扩展场景**：用户需要对接新工具（如 GitHub API），Garage 提供标准化的工具接入方式
5. **自我成长场景**：Garage 从使用中识别重复模式，自动总结并生成新的 skills

## 4. 范围

### 4.1 Phase 1 核心范围

当前规格聚焦于 Phase 1 实现：

1. **运行时基础**：在 Claude Code 环境中建立基本的运行时能力
2. **知识存储**：实现基础的知识存储和检索机制
3. **工具对接**：完成与 Claude Code 的基础对接
4. **数据持久化**：确保所有数据存储在 Garage 仓库内部

### 4.2 功能边界

- **包含**：运行时执行、知识存储、工具对接、基础成长机制
- **不包含**：完整的多 agent 协作、Web UI、数据库、多用户系统、实时服务

## 5. 范围外内容

以下内容明确不在当前规格范围内，将在后续增量中考虑：

- 完整的 WorkflowBoard 实现和 board-first 运行模式
- 多用户、多租户、多环境系统
- Web UI 和可视化管理界面
- 常驻服务和数据库
- 完整的平台控制面和治理系统
- 与 Hermes、OpenClaw、Clowder AI、DeerFlow 等外部系统的深度集成
- 自动化的 skill 生成和 Agent 生成（初期为手动或半自动）

## 6. 术语与定义

| 术语 | 定义 |
|------|------|
| **Garage** | 本项目，一个 skills-driven 的 Agent 工作区和操作系统 |
| **AHE** | Agent-Harness-Engineering，本项目的核心工作流方法论 |
| **Skill** | 可被 Agent 调用的能力单元，以 markdown 或代码形式存在 |
| **Pack** | 一组相关 skills 的集合，如 coding pack、product-insights pack |
| **Agent** | 具有一定自主性、可以执行 skills 和工作流的 AI 实体 |
| **运行时** | 能够执行 skills、管理状态、存储数据的执行环境 |
| **知识库** | 存储结构化知识、经验、模式的持久化存储 |
| **Claude Code** | Anthropic 提供的 coding agent 工具，作为首个运行时宿主 |
| **Workspace** | Garage 仓库，包含所有 skills、知识、配置和数据的根目录 |
| **Evidence** | 可追溯的执行证据，包括会话记录、决策依据、产出物等 |

## 7. 功能需求

### FR-001 运行时执行能力

- **优先级**: Must
- **来源**: 用户需求"让 Garage 成为可运行的 Agent 操作系统"；背景问题陈述
- **需求陈述**: 当用户在 Claude Code 中与 Garage 交互时，系统必须能够执行 AHE workflow skills 并管理执行状态。
- **验收标准**:
  - Given Claude Code 环境中已加载 Garage，When 用户调用 `/ahe-specify`，Then 系统执行需求澄清 workflow 并返回可评审的规格草稿
  - Given workflow 执行过程中，When 需要用户输入，Then 系统暂停并等待用户响应
  - Given workflow 执行完成，When 产出 artefacts，Then 系统将 artefacts 保存到 `docs/features/` 或约定路径
  - Given workflow 执行失败，When 出现错误，Then 系统记录错误信息并提供恢复或重试选项

### FR-002 知识存储与检索

- **优先级**: Must
- **来源**: 核心愿景"知识管理 - 整理和存储知识，agent 在交互中积累经验"
- **需求陈述**: 当 Agent 与用户交互产生知识时，系统必须将知识结构化存储并支持后续检索。
- **验收标准**:
  - Given 会话中产生有价值知识（如技术决策、最佳实践），When 会话结束，Then 系统自动将知识提取并存储到知识库
  - Given 用户查询某个技术问题，When 查询知识库，Then 系统返回相关知识和来源上下文
  - Given 知识库中已存在相关知识，When 新知识与现有知识冲突，Then 系统提示用户确认并记录冲突和决策
  - Given 知识存储，When 知识被写入，Then 系统保留来源锚点（如会话 ID、规格文档、commit hash）

### FR-003 Claude Code 对接

- **优先级**: Must
- **来源**: 设计原则"以 Claude Code 作为第一个运行时"
- **需求陈述**: 当用户使用 Claude Code 时，系统必须提供标准的 skills 调用接口和状态管理。
- **验收标准**:
  - Given Claude Code 环境，When 用户输入 `/skill-name`，Then 系统路由到对应的 AHE workflow skill
  - Given skill 执行需要读取项目文件，When 执行，Then 系统能够访问 Garage 仓库内的所有文件
  - Given skill 执行产出 artefacts，When 完成，Then 系统将 artefacts 写入仓库约定路径
  - Given Claude Code 的 session 状态，When session 中断，Then 系统能够从上次中断点恢复执行

### FR-004 数据仓库内部存储

- **优先级**: Must
- **来源**: 设计原则"所有数据存储在 Garage 仓库内部，不依赖三方平台"
- **需求陈述**: 当系统存储任何数据时，必须将数据保存在 Garage 仓库内的文件系统中。
- **验收标准**:
  - Given 系统需要存储知识，When 存储，Then 知识保存为 `.garage/knowledge/` 下的 markdown 或 JSON 文件
  - Given 系统需要存储会话状态，When 存储，Then 状态保存为 `.garage/sessions/` 下的结构化文件
  - Given 系统需要存储配置，When 存储，Then 配置保存为仓库根目录或 `.garage/config/` 下的配置文件
  - Given 仓库克隆到新环境，When 用户在新环境中使用 Garage，Then 所有数据和配置可正常加载

### FR-005 可迁移性

- **优先级**: Must
- **来源**: 设计原则"可迁移：换工作区、换工具，能力不丢失"
- **需求陈述**: 当用户将 Garage 仓库迁移到不同环境或工具时，所有能力和数据必须保持可用。
- **验收标准**:
  - Given Garage 仓库，When 克隆到新机器，Then 所有 skills、知识、配置可直接使用
  - Given 用户从 Claude Code 切换到其他工具，When 切换，Then skills 和知识可通过标准接口访问
  - Given 仓库迁移，When 迁移完成，Then 所有路径引用和配置保持有效
  - Given 迁移过程中，When 仓库文件完整性验证，Then 关键文件无缺失或损坏

### FR-006 经验积累与模式识别

- **优先级**: Should
- **来源**: 核心愿景"自我成长 - 总结 skills、产生新的 Agent、持续积累"
- **需求陈述**: 当 Agent 执行 tasks 和 workflows 时，系统必须识别重复模式并积累可复用的经验。
- **验收标准**:
  - Given Agent 执行相似任务 3 次以上，When 识别模式，Then 系统将模式记录为可复用经验
  - Given 用户执行某类开发任务，When 执行，Then 系统推荐相关的历史经验和 skills
  - Given 模式被识别为可复用，When 验证，Then 系统将模式整理为 skill 模板或建议
  - Given 经验库积累，When 达到一定规模，Then 系统支持按场景、技术栈、任务类型检索经验

### FR-007 工具扩展接口

- **优先级**: Should
- **来源**: 核心愿景"工具对接 - 连接更多工具扩展能力"
- **需求陈述**: 当系统需要接入新工具时，必须提供标准化的工具注册和调用接口。
- **验收标准**:
  - Given 开发者需要接入新工具（如 GitHub API），When 注册工具，Then 系统提供标准工具定义模板
  - Given 工具已注册，When Agent 需要调用，Then 系统通过统一接口调用工具并返回结果
  - Given 工具调用失败，When 出错，Then 系统捕获错误并提供标准错误处理机制
  - Given 多工具协作，When workflow 需要，Then 系统支持工具链编排和数据传递

### FR-008 渐进式架构演进

- **优先级**: Should
- **来源**: 设计原则"渐进式架构：从简单开始，可逐步演进到自建运行时"
- **需求陈述**: 当系统架构需要演进时，必须保持向后兼容并支持渐进式升级。
- **验收标准**:
  - Given Phase 1 实现（Claude Code 宿主），When 设计架构，Then 为未来自建运行时预留扩展点
  - Given 系统从 markdown-first 演进到 board-first，When 演进，Then 保持现有 skills 和数据兼容
  - Given 架构升级，When 升级，Then 提供迁移路径和兼容性检查
  - Given 新功能添加，When 添加，Then 不破坏现有功能边界和合约

## 8. 非功能需求

### NFR-001 性能与响应速度

- **优先级**: Should
- **来源**: 用户期望"快速响应的 AI 助手"
- **需求陈述**: 当用户调用 skills 或查询知识时，系统必须在合理时间内返回结果。
- **验收标准**:
  - Given 用户调用 skill，When 执行，Then 90% 的调用在 30 秒内开始返回响应
  - Given 用户查询知识库，When 查询，Then 90% 的查询在 5 秒内返回结果
  - Given 知识库规模增长到 1000+ 条目，When 查询，Then 查询性能不降低超过 50%

### NFR-002 可靠性与数据完整性

- **优先级**: Must
- **来源**: 设计原则"所有数据存储在 Garage 仓库内部"
- **需求陈述**: 当系统存储和读取数据时，必须保证数据完整性和一致性。
- **验收标准**:
  - Given 数据写入操作，When 写入失败，Then 系统回滚操作并报告错误
  - Given 并发读写操作，When 发生冲突，Then 系统使用文件锁或等价机制保证一致性
  - Given 数据损坏或丢失，When 检测到，Then 系统提供恢复机制或明确错误提示
  - Given 仓库版本控制，When 提交，Then 关键数据文件应被纳入版本管理

### NFR-003 可维护性与可扩展性

- **优先级**: Should
- **来源**: 项目定位"长期演进的 Agent 操作系统"
- **需求陈述**: 当系统需要添加新功能或修改现有功能时，代码和架构必须支持低成本的维护和扩展。
- **验收标准**:
  - Given 添加新 skill，When 集成，Then 不需要修改核心运行时代码
  - Given 添加新工具适配器，When 集成，Then 遵循现有适配器接口规范
  - Given 架构演进，When 演进，Then 保持模块边界清晰和依赖单向
  - Given 代码和文档，When 维护，Then 提供清晰的开发者文档和示例

### NFR-004 安全性与隐私保护

- **优先级**: Must
- **来源**: 本地存储和 workspace-first 的设计要求
- **需求陈述**: 当系统处理用户数据时，必须保护隐私并防止数据泄露。
- **验收标准**:
  - Given 敏感数据（API keys、凭证），When 存储，Then 系统不将敏感数据明文写入仓库或传输到外部服务
  - Given 仓库分享或公开，When 分享，Then 敏感数据已被排除或加密
  - Given 外部工具调用，When 调用，Then 系统明确告知用户将要传输的数据并征得同意
  - Given 访问控制，When 配置，Then 支持用户配置哪些工具和数据可以被访问

### NFR-005 兼容性

- **优先级**: Should
- **来源**: 目标"在 Claude Code 等 coding agent 环境中使用"
- **需求陈述**: 当系统在不同环境和工具中运行时，必须保持核心功能可用。
- **验收标准**:
  - Given Claude Code CLI 版本，When 使用，Then 所有核心 skills 可正常调用
  - Given 不同操作系统（Linux、macOS、Windows），When 运行，Then 文件路径和数据存储正确处理
  - Given 不同 Git 配置，When 提交，Then 系统能正确检测仓库状态和用户身份
  - Given 未来支持的其他 AI 工具，When 集成，Then 提供标准适配器接口

## 9. 外部接口与依赖

### IFR-001 Claude Code API 集成

- **优先级**: Must
- **来源**: FR-003
- **需求陈述**: 系统必须与 Claude Code 的 skills 调用、文件访问、状态管理 API 集成。
- **接口描述**:
  - Skills 调用：通过 `/skill-name` 命令模式
  - 文件访问：读取和写入仓库内的任何文件
  - 状态管理：session 恢复、执行进度跟踪
- **验收标准**:
  - Given Claude Code API，When 集成，Then 所有 AHE skills 可通过标准命令调用
  - Given API 变更，When 变更，Then 系统提供适配层或兼容性处理

### IFR-002 文件系统存储

- **优先级**: Must
- **来源**: FR-004
- **需求陈述**: 系统必须使用文件系统作为主要数据存储，不依赖数据库或外部存储服务。
- **接口描述**:
  - 知识存储：`.garage/knowledge/` 目录
  - 会话状态：`.garage/sessions/` 目录
  - 配置文件：仓库根目录或 `.garage/config/`
- **验收标准**:
  - Given 数据读写操作，When 执行，Then 所有数据持久化到文件系统
  - Given 文件系统权限，When 访问，Then 系统正确处理只读和写入权限

### IFR-003 Markdown 和 JSON 格式

- **优先级**: Should
- **来源**: 现有 AHE skills 使用 markdown 格式
- **需求陈述**: 系统必须支持 markdown 和 JSON 作为主要数据交换格式。
- **接口描述**:
  - Markdown：skills 文档、规格文档、知识文档
  - JSON：结构化数据、配置文件、元数据
- **验收标准**:
  - Given 数据序列化，When 序列化，Then 系统使用标准 markdown 和 JSON 格式
  - Given 格式解析，When 解析，Then 系统容错处理格式差异和版本变更

### IFR-004 Git 版本控制集成

- **优先级**: Should
- **来源**: 仓库基于 Git 管理的设计要求
- **需求陈述**: 系统应与 Git 版本控制集成，支持数据版本追踪和协作。
- **接口描述**:
  - 读取 Git 状态（branch、commit、remote）
  - 可选：自动提交关键 artefacts
- **验收标准**:
  - Given Git 仓库，When 操作，Then 系统能正确读取仓库状态
  - Given artefact 生成，When 生成，Then 系统可选择性创建 Git commits

## 10. 约束

### CON-001 技术栈约束

- **优先级**: Must
- **来源**: 项目现有基础和设计原则
- **需求陈述**: 系统必须基于现有 AHE workflow skills 和 markdown-first 架构，不引入新的重依赖框架。
- **详细说明**:
  - Phase 1 不引入数据库、常驻服务、Web UI
  - 优先使用 markdown、JSON、文件系统存储
  - 代码执行依赖 Claude Code 提供的运行时
  - 避免引入需要复杂部署和运维的依赖

### CON-002 仓库结构约束

- **优先级**: Must
- **来源**: 现有项目结构和 AGENTS.md 约定
- **需求陈述**: 系统必须遵循现有仓库结构和文档约定。
- **详细说明**:
  - 规格文档存放在 `docs/features/` 目录
  - Skills 存放在 `packs/coding/skills/` 和 `packs/product-insights/skills/`
  - 架构文档存放在 `docs/architecture/`
  - 遵循 `AGENTS.md` 中定义的文档约定和路径映射

### CON-003 向后兼容约束

- **优先级**: Must
- **来源**: 渐进式演进原则
- **需求陈述**: 系统演进必须保持对现有 26 个 AHE skills 的兼容。
- **详细说明**:
  - 现有 skills 的文档格式和调用方式不变
  - 新增运行时能力不破坏现有 skills 的执行
  - 从 markdown-first 到 board-first 的演进保持兼容

### CON-004 资源约束

- **优先级**: Should
- **来源**: Solo creator 和本地运行的设计定位
- **需求陈述**: 系统资源消耗必须适合在个人开发环境中运行。
- **详细说明**:
  - 内存占用：正常运行不超过 2GB
  - 存储占用：知识库增长可控，提供清理和归档机制
  - 计算资源：不依赖昂贵的 API 调用或大量计算资源

## 11. 假设

### ASM-001 Claude Code 持续支持

- **优先级**: Should
- **来源**: Phase 1 以 Claude Code 为首个运行时的设计决策
- **需求陈述**: 假设 Claude Code 在可预见的未来继续提供 skills 调用和文件访问能力。
- **失效风险**: 如果 Claude Code 改变 API 或停止支持，可能需要重新设计运行时适配层
- **缓解措施**: 设计标准化的适配器接口，便于切换到其他工具或自建运行时

### ASM-002 文件系统存储足够

- **优先级**: Should
- **来源**: Phase 1 不引入数据库的设计决策
- **需求陈述**: 假设文件系统存储足够支撑 Phase 1 的数据量和访问需求。
- **失效风险**: 如果知识库规模增长到百万级条目，文件系统可能性能不足
- **缓解措施**: 在架构设计中预留数据库集成点，便于后续升级

### ASM-003 Markdown 格式可扩展

- **优先级**: Could
- **来源**: 现有 AHE skills 大量使用 markdown
- **需求陈述**: 假设 markdown 格式能够支撑未来更复杂的数据结构和交互需求。
- **失效风险**: 如果需要复杂查询、事务处理或实时更新，markdown 可能不足
- **缓解措施**: 混合使用 JSON 和 markdown，逐步引入结构化存储

### ASM-004 Solo Creator 使用模式

- **优先级**: Should
- **来源**: 目标用户定位
- **需求陈述**: 假设主要使用场景是 solo creator 的个人使用，而非多用户协作。
- **失效风险**: 如果需要支持团队协作，可能需要引入多租户和权限管理
- **缓解措施**: 在架构设计中预留协作功能扩展点

## 12. 开放问题

当前无阻塞性开放问题。

以下非阻塞问题可在后续迭代中解决：

1. **知识表示标准化**：知识库的具体 schema 设计需要在使用中迭代优化
2. **经验识别算法**：模式识别和经验积累的具体算法待实验和调优
3. **工具适配器规范**：工具扩展接口的具体设计需要在实际集成中验证
4. **性能优化策略**：随着知识库规模增长，具体的性能优化策略待评估
5. **board-first 迁移路径**：从 markdown-first 到 board-first 的具体迁移时机和方案待定

---

**文档状态**: 本规格草稿已完成，等待 `ahe-spec-review` 评审。

**下一步**: 派发独立 reviewer subagent 执行 `ahe-spec-review`。
