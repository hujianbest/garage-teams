# 车载嵌入式团队 Harness Engineering 框架设计说明书

## 1. 文档目的

本文档用于为车载嵌入式软件团队设计一套可落地的 Harness Engineering 框架，使 AI 可以在高约束、强追溯、重验证的前提下参与软件系统开发。文档目标不是描述单个提示词或单个 Agent 的用法，而是给出一套可直接驱动 AI 继续生成框架资产的完整蓝图，包括目录结构、流程、角色、工件、质量门禁、工具适配、证据模型和安全边界。

本文档适用于以下场景：

- 团队主要在 MCU 和 SoC 平台上开发嵌入式软件。
- 业务领域属于车载电子和智能汽车软件。
- 团队整体采用 IPD 流程，要求研发过程可审计、可追溯、可验证。
- 软件质量要求高，需要兼顾功能安全、网络安全、可靠性、实时性和配置管理。
- 期望 AI 不只是辅助写代码，而是参与需求分析、设计、实现、验证、交付和变更闭环。

## 2. 设计输入与抽象结论

本设计基于 `docs/` 目录下 5 篇高星 Harness Engineering 框架分析的共同模式抽象而来：

- `get-shit-done-main-harness-engineering-analysis.md`
- `longtaskforagent-main-harness-engineering-analysis.md`
- `superpowers-main-harness-engineering-analysis.md`
- `everything-claude-code-main-harness-engineering-analysis.md`
- `gstack-main-harness-engineering-analysis.md`

从这 5 篇分析中可以抽象出 10 条共性原则：

1. 先路由后执行，不能让 AI 直接跳到编码。
2. 长期状态必须落到可读工件，不能依赖会话记忆。
3. 工作必须阶段化，每一阶段要有明确输入、输出和门禁。
4. AI 需要角色化和职责分离，而不是一个万能 Agent。
5. 验证和证据必须成为主流程，而不是收尾附属动作。
6. 规则、技能、命令、Hook、工具适配层必须分层。
7. 宿主差异要下沉到适配层，不能污染核心流程资产。
8. Harness 本身必须可测试、可审计、可演进。
9. 安全与注入风险必须前置处理，而不是事后补救。
10. 昂贵验证要分层分级，按风险和变更范围控制成本。

这些原则适用于通用软件团队，但车载嵌入式场景有更强约束，因此本文档在此基础上加入以下专门扩展：

- 面向 MCU 与 SoC 的双平台模型。
- 面向 IPD 的阶段映射和交付门。
- 面向 ISO 26262、ASPICE、ISO/SAE 21434 的证据与审批要求。
- 面向车载通信、诊断、升级、资源约束、台架测试的领域包。
- 面向高质量交付的工件追溯、偏差管理和发布决策包。

### 2.1 设计来源映射

为避免“只借鉴结论，不借鉴结构”，本方案将 5 个框架的代表性机制映射如下：

| 来源框架 | 主要借鉴点 | 在本方案中的落点 |
|---|---|---|
| get-shit-done | 阶段化 workflow、文件态状态、薄编排器、多角色执行、UAT/验证闭环 | 生命周期蓝图、工件层、AI 角色模型、质量门禁、项目接入状态目录 |
| longtaskforagent | 会话启动路由、JSON+Markdown 双工件、强门禁链、增量/热修支线、外部循环控制 | Stage Router、Work Packet、主流程/变更/热修流程、Gate 设计、状态与信号工件 |
| superpowers | bootstrap 总入口、主路径 skills、顺序化 review gate、跨宿主薄适配、skill system 测试 | `using-automotive-harness`、MVP skills、adapters 目录、harness 自身验证 |
| everything-claude-code | rules/skills/commands/hooks/agents 分层、模块化安装、显式 verify command、生命周期治理 | 分层架构、Rules/Skills/Commands/Hooks 目录、MVP commands、后续 profile/module 扩展 |
| gstack | skill 生成链路、统一 preamble、工具单一事实源、diff-aware 分层验证、worktree/隔离执行 | 模板与 schema、bootstrap、connectors registry、验证策略分层、执行沙箱层 |

因此，本文档并不是把 5 套框架拼接，而是将它们共同验证过的稳定工程模式重组为一套更适合车载嵌入式和 IPD 流程的企业级框架。

## 3. 框架总体定位

本框架不是“让 AI 自动写完软件”的工具集，而是“让 AI 在企业级工程约束下稳定参与研发”的交付操作层。

框架对上承接：

- IPD 生命周期和评审制度。
- 组织级研发规范、编码规范、测试规范、发布规范。
- 功能安全、网络安全、合规与审计要求。

框架对下连接：

- 代码仓库和配置仓库。
- 需求、缺陷、任务、评审、发布系统。
- 编译、静态分析、单元测试、集成测试、SIL、PIL、HIL、板级台架。
- 诊断、总线、升级、性能、资源和日志工具。

框架的核心目标是把 AI 生成、AI 分析、AI 校验、AI 编排纳入受控流程，使任何一项结论都能回答四个问题：

- 这项工作属于哪个阶段。
- 它基于哪些输入工件。
- 它产生了哪些输出和证据。
- 谁批准它进入下一阶段。

## 4. 设计目标与非目标

### 4.1 设计目标

1. 形成一套面向车载嵌入式研发的 Harness Engineering 标准框架。
2. 支持 AI 参与需求、设计、实现、验证、发布和变更闭环。
3. 使所有阶段可追溯、可恢复、可审计、可验证。
4. 兼容 MCU、RTOS、裸机、Linux、AUTOSAR Classic、AUTOSAR Adaptive、SoC 平台。
5. 支持 IPD 主流程、变更流程、热修复流程。
6. 将功能安全、网络安全、资源约束和测试策略前置到流程内生层。
7. 提供可直接生成目录、模板、schema、技能和脚本的说明依据。

### 4.2 非目标

1. 不试图一次性替代现有 ALM、PLM、CI、HIL 平台。
2. 不让 AI 直接批准关键决策、直接放行发布、直接操作量产环境。
3. 不把所有研发活动都自动化，人工评审和批准仍然是必须步骤。
4. 不假定所有项目都要使用完整框架，可按风险和项目类型裁剪。

## 5. 适用范围

### 5.1 适用产品类型

- ECU 软件
- 域控制器软件
- 车身电子软件
- 底盘控制软件
- 动力与能量管理软件
- 智能座舱和网关软件
- Bootloader、诊断、升级和平台软件

### 5.2 适用技术栈

- C
- C++
- Python 辅助工具
- RTOS
- Bare Metal
- Linux
- QNX
- AUTOSAR Classic
- AUTOSAR Adaptive

### 5.3 适用研发活动

- 需求分析
- 软件架构设计
- 详细设计
- 实现与重构
- 缺陷分析与修复
- 测试设计与执行
- 发布与回归
- 变更影响分析
- 过程审计与复盘

## 6. 设计原则

### 6.1 先工件后对话

AI 不以聊天上下文为真相源，所有跨阶段状态必须外置到工件。

### 6.2 先阶段后行动

任何任务都要先识别所处研发阶段，再决定是否允许 AI 继续执行。

### 6.3 先证据后完成

AI 不能宣称完成，除非存在新鲜验证证据并绑定具体结论。

### 6.4 先约束后智能

规则、权限、工具边界、审批点、审计要求优先于生成能力。

### 6.5 领域知识内建

车载嵌入式的安全、实时性、资源、诊断、升级、通信等约束必须写进框架，而不是依赖临时补充。

### 6.6 多层验证

静态检查、单元测试、台架测试、系统验证、人工评审必须协同存在。

### 6.7 人工职责不被替代

AI 只能辅助职责履行，不能替代功能安全工程师、架构师、质量负责人、发布经理等正式职责角色。

## 7. 总体架构

建议将框架划分为 8 个主层和 2 个横切能力。

### 7.1 治理与策略层

职责：

- 定义 AI 权限和禁止行为。
- 定义各类任务的流程强度。
- 定义审批点、偏差管理和风险接受边界。
- 定义按项目、平台、ASIL、变更类型切换的 profile。

核心对象：

- Governance Policy
- Approval Policy
- Risk Policy
- Deviation Policy
- Profile Matrix

### 7.2 流程编排层

职责：

- 对任务进行阶段路由。
- 组织主流程、变更流程、热修复流程。
- 管理暂停点、回退点和闭环点。

核心对象：

- Stage Router
- Workflow Engine
- Pause Point Manager
- Rework Loop Controller
- Completion Gate Orchestrator

### 7.3 工件与追溯层

职责：

- 管理需求、设计、代码、测试、证据和发布工件。
- 建立需求到实现到测试到发布的追溯链。
- 管理基线、版本、影响分析和差异包。

核心对象：

- Artifact Registry
- Traceability Graph
- Baseline Manager
- Change Impact Engine
- Evidence Vault

### 7.4 领域知识与规则包层

职责：

- 沉淀车载嵌入式领域知识。
- 提供编码、测试、安全、平台和通信规则。
- 为 AI 提供结构化约束上下文。

核心对象：

- Platform Pack
- Safety Pack
- Cybersecurity Pack
- Diagnostics Pack
- Performance Pack
- Coding Rules Pack
- Testing Rules Pack

### 7.5 工具与连接器层

职责：

- 将外部系统暴露为受控工具。
- 统一 Git、ALM、构建、测试、仿真、HIL、日志和总线工具的调用界面。

核心对象：

- Repo Connector
- ALM Connector
- Build Connector
- Static Analysis Connector
- Bench Connector
- Simulation Connector
- Release Connector

### 7.6 执行沙箱层

职责：

- 在隔离环境中执行 AI 生成、修改、构建和验证动作。
- 根据风险等级限制 AI 执行动作。

核心对象：

- Draft Sandbox
- Code Edit Sandbox
- Build Sandbox
- Virtual Target Sandbox
- Bench Proxy Executor

### 7.7 质量门禁与证据层

职责：

- 对各阶段输出进行评审和验证。
- 统一存放日志、报告、覆盖率、波形、trace 和审批证据。

核心对象：

- Review Gate
- Verification Gate
- Regression Gate
- Release Gate
- Evidence Aggregator

### 7.8 审批与发布层

职责：

- 记录人工审批。
- 管理残余风险接受。
- 形成发布决策包和审计链。

核心对象：

- Approval Ledger
- Release Decision Pack
- Audit Trail
- Exception Ledger

### 7.9 横切能力 A：可观测性与度量

建议采集以下度量：

- AI 参与率
- AI 输出采纳率
- 返工率
- 缺陷逃逸率
- 需求测试追溯完整率
- 质量门一次通过率
- 审批等待时间
- 各阶段证据完备率

### 7.10 横切能力 B：配置与变体管理

建议单独建模以下维度：

- 车型变体
- 区域变体
- ECU 变体
- 编译配置
- 供应商版本
- 第三方中间件版本
- Bootloader 和应用兼容关系

## 8. IPD 映射与生命周期蓝图

框架建议覆盖 9 个研发阶段和 2 条支线流程。

### 8.1 主流程阶段

| 阶段 | 目标 | 主要输入 | 主要输出 |
|---|---|---|---|
| P0 项目边界定义 | 明确产品、平台、范围、风险 | 项目立项信息、产品目标 | 项目边界包、平台矩阵、风险等级 |
| P1 需求与约束 | 形成可验证的软件需求 | 系统需求、安全输入、网络安全输入 | SRS、接口需求、约束清单 |
| P2 架构设计 | 形成组件划分与系统设计 | SRS、平台约束、资源要求 | 软件架构说明、ICD、资源预算 |
| P3 详细设计 | 形成模块级设计与任务拆解 | 架构设计、接口、约束 | 详细设计、任务包、测试设计 |
| P4 实现与单元质量 | 形成可编译、可测试实现 | 详细设计、编码规则 | 代码、单元测试、静态分析报告 |
| P5 集成与平台验证 | 完成组件和平台联调 | 代码、集成计划、构建配置 | 集成记录、SIL/PIL/板级报告 |
| P6 系统与场景验证 | 完成系统级与台架验证 | 集成版本、系统测试计划 | HIL/系统测试报告、回归报告 |
| P7 发布与基线 | 形成可发布交付包 | 验证证据、审批记录 | 发布包、版本基线、发布说明 |
| P8 运行维护与复盘 | 支撑变更、热修、复盘 | 现场问题、变更请求 | 热修复记录、影响分析、改进项 |

### 8.2 支线流程

#### 变更流程

适用于新增需求、规格修改、接口变化、配置变化。必须从变更请求进入，完成影响分析后决定回到 P1、P2 或 P3。

#### 热修复流程

适用于现场缺陷、量产后问题、紧急补丁。必须通过最小变更策略执行，并补齐影响分析、回归和发布记录。

## 9. 风险分级与流程 Profile

建议定义 4 级流程 profile。

| Profile | 适用范围 | 典型对象 | 要求 |
|---|---|---|---|
| L0 探索型 | 非量产、工具脚本、内部验证件 | 辅助脚本、实验工具 | 轻量工件、最小验证 |
| L1 标准型 | 常规 QM 模块 | 非安全关键功能模块 | 完整主流程、标准验证 |
| L2 强约束型 | 高复杂度模块或高影响接口 | 平台服务、诊断、通信栈 | 强追溯、强化评审、强化回归 |
| L3 安全关键型 | ASIL 相关、Bootloader、安全模块 | 安全机制、升级链路、关键控制模块 | 最严格审批、最强证据、只允许受限自动化 |

Profile 切换输入建议包括：

- ASIL 等级
- 网络安全等级
- 模块关键性
- 变更类型
- 平台类型
- 是否涉及量产版本
- 是否涉及升级链路

## 10. 角色模型与职责边界

建议采用以下角色集合。

| 角色 | 主要职责 | 是否可由 AI 辅助 | 是否可由 AI 替代 |
|---|---|---|---|
| 项目负责人 | 边界、优先级、资源协调 | 是 | 否 |
| 系统工程师 | 系统需求、接口边界、验收标准 | 是 | 否 |
| 软件架构师 | 架构方案、设计权衡、资源预算 | 是 | 否 |
| 模块负责人 | 模块设计、实现和缺陷处理 | 是 | 否 |
| 功能安全工程师 | 安全输入、评审和确认 | 是 | 否 |
| 网络安全工程师 | 网络安全输入和审查 | 是 | 否 |
| 测试负责人 | 测试策略、覆盖目标、系统验证 | 是 | 否 |
| 质量/流程工程师 | 流程符合性和门禁审查 | 是 | 否 |
| 配置/发布经理 | 基线、版本和发布放行 | 是 | 否 |
| 工具链负责人 | 编译器、静态分析、仿真/HIL 工具可信度 | 是 | 否 |
| AI Harness Owner | 规则、技能、工具、Hook、审计模型维护 | 是 | 否 |

基本原则：

- AI 可以生成草稿、分析差异、执行受控工具、汇总证据。
- AI 不得独立批准规格、架构、发布、残余风险接受和偏差豁免。
- AI 不得替代独立审查职责。

## 11. AI 工作模型

### 11.1 AI 角色集合

建议首版定义以下 AI 角色：

- Router：识别阶段、风险等级和应走流程。
- Researcher：提炼需求、约束、标准和上下文。
- Architect：生成架构草案、权衡分析和接口设计。
- Planner：生成任务拆解、依赖和验证计划。
- Implementer：在受控范围内生成代码或文档草稿。
- Reviewer：执行设计、代码、追溯和质量预审。
- Verifier：汇总验证证据并形成验证结论草稿。
- Release Assistant：整理发布包、发布说明和影响分析。
- Retrospective Assistant：归纳流程缺陷和改进建议。

### 11.2 AI 执行模式

| 模式 | 能力 | 适用场景 |
|---|---|---|
| Readonly Analyze | 只能读，不改工件 | 需求分析、问题调查、审查 |
| Draft Generate | 生成草稿，不写正式状态 | 需求草稿、设计草稿、测试草稿 |
| Controlled Edit | 在限定目录和限定工件中修改 | 文档修改、代码 patch、配置变更 |
| Controlled Verify | 执行白名单验证工具 | 构建、静态分析、单测、仿真 |
| Proxy Bench | 通过代理执行台架动作 | SIL、PIL、HIL、总线测试 |

### 11.3 AI 工作包

每次 AI 执行都必须由结构化工作包驱动。

建议字段：

- `work_id`
- `request_type`
- `lifecycle_stage`
- `project_id`
- `product_line`
- `ecu_or_domain`
- `component`
- `platform_type`
- `os_or_rtos`
- `compiler`
- `criticality_level`
- `cybersecurity_level`
- `scope_in`
- `scope_out`
- `source_artifacts`
- `allowed_tools`
- `required_outputs`
- `required_evidence`
- `required_reviewers`
- `required_approvers`
- `execution_mode`
- `data_classification`
- `timebox_or_budget`

### 11.4 AI 输出包

AI 产出必须结构化，建议字段：

- `work_id`
- `summary`
- `decision_or_recommendation`
- `changed_artifacts`
- `assumptions`
- `known_gaps`
- `risks`
- `trace_updates`
- `verification_performed`
- `verification_pending`
- `evidence_manifest`
- `required_human_actions`
- `residual_risk`
- `next_stage`
- `confidence`

## 12. 工件模型

建议将工件分为 7 大类。

### 12.1 需求类工件

- Item Scope
- Project Constraints
- System Requirement
- Software Requirement
- Interface Requirement
- NFR Requirement
- Acceptance Criteria

### 12.2 安全与网络安全类工件

- HARA
- Safety Goal
- FSC
- TSC
- TARA
- Cybersecurity Goal
- Cybersecurity Requirement
- Safety Mechanism Spec
- Security Mechanism Spec

### 12.3 设计类工件

- Software Architecture Document
- Interface Control Document
- Detailed Design Spec
- State Machine
- Sequence Design
- Resource Budget
- Fault Handling Strategy
- Degradation Strategy

### 12.4 实现类工件

- Task Breakdown
- Code Change Pack
- Build Config
- Variant Config
- Static Analysis Report
- Code Review Record

### 12.5 测试与验证类工件

- Test Strategy
- Unit Test Spec
- Integration Test Spec
- SIL Report
- PIL Report
- Board Test Report
- HIL Report
- Coverage Report
- Mutation Report
- Fault Injection Report
- Verification Record
- Trace Matrix

### 12.6 发布类工件

- Release Notes
- Release Checklist
- Binary Manifest
- Artifact Hash Manifest
- Compatibility Matrix
- Residual Risk Statement
- Approval Package

### 12.7 变更与运维类工件

- Change Request
- Hotfix Request
- Bug Analysis
- Change Impact Report
- Deviation Record
- Lessons Learned

## 13. 追溯模型

### 13.1 标准追溯链

要求至少维护以下链路：

- 需求 -> 架构
- 架构 -> 详细设计
- 详细设计 -> 代码
- 需求 -> 测试用例
- 代码 -> 构建版本
- 测试 -> 验证证据
- 发布 -> 批准记录

### 13.2 安全追溯链

要求补充以下链路：

- Safety Goal -> Safety Requirement -> Design -> Safety Mechanism -> Test -> Evidence
- Cybersecurity Goal -> CS Requirement -> Control Design -> Test -> Evidence

### 13.3 AI 追溯链

新增一条 AI 运行追溯链：

- AI Run -> Input Manifest -> Tool Calls -> Changed Artifacts -> Evidence -> Reviewer -> Approver

### 13.4 追溯检查规则

- 任何已进入设计阶段的需求必须有设计映射。
- 任何已进入实现阶段的设计必须有任务和代码映射。
- 任何准备关闭的需求必须有验证和证据映射。
- 任何发布基线必须能回溯到版本内所有变更的来源、验证和审批记录。

## 14. 质量门禁设计

建议定义 10 个门禁。

| Gate | 名称 | 进入条件 | 退出条件 | 必需批准角色 |
|---|---|---|---|---|
| G0 | 入口门 | 请求完整，识别平台和范围 | 工作包可执行 | 项目负责人/模块负责人 |
| G1 | 需求基线门 | 需求已成稿 | 需求可验证、边界清晰 | 系统工程师 |
| G2 | 安全输入门 | 安全和网络安全输入已建模 | 风险与约束已关联需求 | 功能安全/网络安全工程师 |
| G3 | 架构基线门 | 需求稳定 | 架构完整、资源和异常流完整 | 架构师 |
| G4 | 详细设计门 | 架构已冻结到可设计粒度 | 模块设计可实现、可测试 | 模块负责人/架构师 |
| G5 | 实现就绪门 | 设计和测试策略已准备 | 编码任务和验证策略齐备 | 模块负责人 |
| G6 | 单元质量门 | 代码已提交 | 构建、静态分析、单测、覆盖率达标 | 模块负责人/质量工程师 |
| G7 | 集成质量门 | 单元质量通过 | 集成、接口、资源、异常路径达标 | 测试负责人 |
| G8 | 系统验证门 | 集成版本稳定 | HIL/系统场景/回归通过 | 测试负责人/项目负责人 |
| G9 | 发布门 | 验证和追溯完整 | 审批齐备、残余风险可接受 | 发布经理/批准人 |

### 14.1 关键补充规则

- 对 L3 安全关键型 profile，G6 以上不允许 AI 自动推进状态。
- G2、G3、G9 必须要求人工明确批准记录。
- 任一 Gate 失败时必须形成回退建议和缺口清单，而不是直接继续。

## 15. 车载嵌入式专用领域设计

### 15.1 MCU 与 SoC 双模建模

框架必须区分两类目标平台。

#### MCU 模式关注点

- 中断
- 寄存器访问
- 裸机或 RTOS 调度
- 栈/堆限制
- WCET
- 启动顺序
- 内存映射
- 诊断与升级安全

#### SoC 模式关注点

- Linux/QNX/Adaptive 平台服务
- 进程与线程模型
- IPC 和中间件
- 安全域
- 容器或分区
- 启动链
- 性能和资源隔离

### 15.2 通信与诊断包

必须内建以下约束：

- CAN/LIN/FlexRay/Ethernet 报文接口
- SOME/IP、UDS、DoIP 协议约束
- 超时、重试、故障码和 DTC 管理
- 诊断会话、刷写状态机、回滚策略

### 15.3 功能安全包

必须覆盖：

- HARA 输入
- ASIL 分配
- 安全机制设计
- 故障检测、故障处理和降级逻辑
- 独立审查与确认点

### 15.4 网络安全包

必须覆盖：

- TARA 输入
- 安全启动
- 安全刷写
- 证书和密钥约束
- 诊断权限控制
- 安全日志与审计

### 15.5 资源与实时性包

必须前移到设计阶段：

- CPU 预算
- 内存预算
- 栈预算
- 启动时间预算
- 总线带宽预算
- 功耗预算
- 实时路径时延预算

### 15.6 测试台架包

建议按可信度分层：

1. Host Unit Test
2. SIL
3. PIL
4. Board Test
5. HIL
6. ECU Bench
7. Vehicle Simulation

不同层的证据可信度和门禁权重必须不同。

## 16. 规则、技能、命令、Hook、连接器分层

这是框架能否长期维护的关键分层。

### 16.1 Rules

存放始终生效的约束，按以下维度分层：

- `rules/common/`
- `rules/embedded-c/`
- `rules/embedded-cpp/`
- `rules/autosar-classic/`
- `rules/autosar-adaptive/`
- `rules/safety/`
- `rules/cybersecurity/`
- `rules/testing/`

### 16.2 Skills

存放按需激活的知识和流程说明，例如：

- 路由类 skill
- 需求类 skill
- 架构类 skill
- 详细设计类 skill
- TDD/验证类 skill
- 评审类 skill
- 发布类 skill

### 16.3 Commands

存放显式工作流入口，建议首版包含：

- `/intake`
- `/route`
- `/requirements`
- `/architecture`
- `/design`
- `/plan`
- `/implement`
- `/verify`
- `/trace`
- `/review`
- `/release`
- `/hotfix`
- `/retro`

### 16.4 Hooks

存放运行时门禁和自动化，建议首版包含：

- SessionStart：注入 bootstrap 和当前状态摘要
- PreToolUse：拦截危险命令、危险目录编辑、量产环境操作
- PostToolUse：修改后触发快速检查
- Stop：检查是否遗漏证据、未记录状态、未完成审查
- SessionEnd：写回会话摘要、状态更新和行动建议

### 16.5 Connectors

以受控适配层暴露工具能力，禁止 AI 直接自由操作外部系统。

建议首版适配：

- Git
- Build
- Static Analysis
- Unit Test
- Coverage
- Simulation
- Bench Proxy
- ALM
- Release Artifact Store

## 17. 推荐目录结构

框架建议拆为两类仓库资产。

### 17.1 框架仓库目录

```text
harness-framework/
  AGENTS.md
  README.md
  rules/
    common/
    embedded-c/
    embedded-cpp/
    safety/
    cybersecurity/
    testing/
  skills/
    using-automotive-harness/
    ipd-router/
    requirements-engineering/
    architecture-design/
    detailed-design/
    implementation-control/
    verification-before-completion/
    release-package/
    hotfix-control/
    retrospective/
  commands/
    intake.md
    route.md
    plan.md
    verify.md
    review.md
    release.md
    hotfix.md
  hooks/
    session-start/
    pre-tool-use/
    post-tool-use/
    stop/
    session-end/
  adapters/
    cursor/
    claude-code/
    codex/
    opencode/
  schemas/
    work-packet.schema.json
    result-packet.schema.json
    artifact.schema.json
    gate.schema.json
    evidence.schema.json
    approval.schema.json
    trace-link.schema.json
  templates/
    work-packet.yaml
    requirement-template.md
    architecture-template.md
    detailed-design-template.md
    task-template.md
    review-record-template.md
    verification-record-template.md
    release-package-template.md
    deviation-template.md
  scripts/
    validate_artifacts.py
    validate_trace.py
    gate_check.py
    package_release.py
    generate_skill_docs.py
  tests/
    harness/
    hooks/
    routing/
    schemas/
    adapters/
  docs/
    framework/
    playbooks/
```

### 17.2 项目接入目录

在具体产品项目中建议增加独立状态目录：

```text
.ai-harness/
  state/
    project.yaml
    current-stage.yaml
    active-work-items.yaml
  artifacts/
    requirements/
    architecture/
    design/
    tasks/
    reviews/
    verification/
    release/
    deviations/
  evidence/
    build/
    static-analysis/
    unit/
    integration/
    sil/
    pil/
    hil/
    performance/
  traces/
    requirement-to-design.yaml
    design-to-code.yaml
    requirement-to-test.yaml
  approvals/
    approval-ledger.yaml
  runtime/
    sessions/
    ai-runs/
    status/
```

## 18. 机器可读 Schema 设计

以下 schema 是后续让 AI 自动生成框架时的核心锚点。

### 18.1 Work Packet Schema

```yaml
work_id: HW-2026-0001
request_type: new_feature
lifecycle_stage: P3_detailed_design
project_id: VC-PLAT-A
product_line: domain_controller
ecu_or_domain: ADAS-DCU
component: diag_manager
platform:
  type: MCU
  chip: TC397
  os: AUTOSAR_Classic
  compiler: TASKING
criticality:
  safety: ASIL_B
  cybersecurity: HIGH
scope_in:
  - software requirement SWR-DIAG-013
  - interface ICD-DIAG-004
scope_out:
  - bootloader
source_artifacts:
  - .ai-harness/artifacts/requirements/SWR-DIAG-013.md
  - .ai-harness/artifacts/architecture/DIAG-ARCH-002.md
allowed_tools:
  - repo.read
  - repo.edit
  - build.compile
  - test.unit
required_outputs:
  - detailed-design
  - task-breakdown
required_evidence:
  - trace-update
  - review-record
required_reviewers:
  - software_architect
required_approvers:
  - module_owner
execution_mode: controlled_edit
data_classification: internal_confidential
```

### 18.2 Result Packet Schema

```yaml
work_id: HW-2026-0001
summary: 完成诊断管理模块详细设计草稿与任务拆解。
decision_or_recommendation: 建议进入模块评审。
changed_artifacts:
  - .ai-harness/artifacts/design/DD-DIAG-005.md
  - .ai-harness/artifacts/tasks/TASK-DIAG-005.yaml
assumptions:
  - 复用现有 UDS 会话管理组件
known_gaps:
  - 未完成超时参数标定评审
risks:
  - 会话切换异常路径尚未经 SIL 验证
trace_updates:
  - SWR-DIAG-013 -> DD-DIAG-005
verification_performed:
  - schema_check
verification_pending:
  - architecture_review
  - SIL_timeout_case
evidence_manifest:
  - .ai-harness/evidence/reviews/REVIEW-DD-DIAG-005-draft.md
required_human_actions:
  - architecture_review_approval
residual_risk: low
next_stage: G4_detailed_design_gate
confidence: medium
```

### 18.3 Gate Schema

```yaml
gate_id: G6
name: unit_quality_gate
profile: L2
entry_conditions:
  - code_change_exists
  - unit_tests_available
required_evidence:
  - build_log
  - static_analysis_report
  - unit_test_report
  - coverage_report
exit_criteria:
  - build_passed
  - blocker_rule_zero
  - unit_tests_passed
  - threshold_coverage_met
reviewers:
  - module_owner
approvers:
  - quality_engineer
ai_can_autoproceed: false
failure_action:
  - open_gap_list
  - rollback_to_P4
```

### 18.4 Evidence Schema

```yaml
evidence_id: EVD-G6-0009
claim: 诊断管理模块单元测试通过并满足覆盖率阈值
method:
  tool: unit_test_runner
  command: run_diag_unit_tests --target host
raw_output:
  path: .ai-harness/evidence/unit/diag_manager/unit_test.log
summary:
  passed: 128
  failed: 0
  coverage_line: 92
  coverage_branch: 87
conclusion: pass
reviewed_by: quality_engineer
timestamp: 2026-03-29T10:00:00Z
```

## 19. 审批与偏差管理

### 19.1 审批规则

以下事项必须人工批准：

- 需求基线冻结
- 架构基线冻结
- 安全和网络安全关键结论
- 测试策略冻结
- 发布放行
- 残余风险接受
- 偏差单关闭

### 19.2 偏差管理

任何未满足规则但需要继续推进的场景必须创建偏差工件，至少包含：

- 偏差编号
- 偏差原因
- 影响范围
- 风险等级
- 临时补偿措施
- 到期关闭条件
- 批准人

### 19.3 AI 限制

- AI 不得创建“已批准”状态。
- AI 不得关闭偏差单。
- AI 不得接受残余风险。
- AI 不得修改审批记录的批准结论。

## 20. 安全边界

### 20.1 默认禁止项

- 直接操作量产环境
- 直接访问生产密钥
- 直接刷写量产 ECU
- 直接修改受保护发布分支
- 未经授权访问客户敏感数据
- 未经批准访问外部第三方模型和网站

### 20.2 风险控制项

- 工具白名单
- 目录白名单
- 数据分级
- Prompt 注入扫描
- 生成内容审查
- 敏感字段脱敏
- 工件完整性和 hash 校验

### 20.3 高风险模块策略

以下模块默认使用 `propose-only` 模式：

- Bootloader
- 安全启动
- 密钥管理
- 升级链路
- 关键安全机制
- ASIL-D 控制逻辑

## 21. 验证策略

### 21.1 Harness 自身验证

框架本身必须被验证，建议分为 4 层：

1. Schema 校验
2. 路由测试
3. Hook 行为测试
4. 代表性流程 E2E 测试

### 21.2 项目接入验证

项目接入后建议执行以下校验：

- 目录和模板完整性检查
- 工件命名和 schema 检查
- 追溯链一致性检查
- Gate 条件检查
- 连接器可用性检查
- 代表性阶段 walkthrough 检查

### 21.3 业务验证分层

业务验证建议按以下层次组织：

- Fast checks：schema、命名、引用、静态校验
- Gate checks：编译、静态分析、单元测试、关键覆盖率
- Scenario checks：SIL/PIL/HIL/诊断/升级/资源场景
- Periodic checks：系统回归、故障注入、鲁棒性和非确定性评估

## 22. 初始 Skills、Commands、Hooks 清单

### 22.1 MVP Skills

- `using-automotive-harness`
- `ipd-router`
- `requirements-synthesis`
- `architecture-design`
- `detailed-design`
- `implementation-control`
- `verification-before-completion`
- `traceability-maintenance`
- `release-package`
- `hotfix-control`

### 22.2 MVP Commands

- `/route`
- `/plan`
- `/design`
- `/implement`
- `/verify`
- `/trace`
- `/review`
- `/release`
- `/hotfix`

### 22.3 MVP Hooks

- `session-start`: 注入 bootstrap、状态摘要、profile
- `pre-tool-use`: 拦截危险命令和越界修改
- `post-tool-use`: 触发快速校验
- `stop`: 检查证据与状态是否缺失
- `session-end`: 写回运行摘要

## 23. AI 生成框架的交付要求

如果使用 AI 按本文档生成实际框架，要求至少交付以下内容。

### 23.1 必需交付物

1. 框架仓库目录骨架。
2. `AGENTS.md` 和总入口说明。
3. `rules/` 初始规则集。
4. `skills/` 的 MVP 技能集合。
5. `commands/` 的 MVP 命令集合。
6. `hooks/` 的 MVP 事件脚本或适配壳。
7. `schemas/` 与 `templates/`。
8. `scripts/validate_*` 和 `gate_check.py`。
9. `tests/` 中至少包含 schema、routing、hooks 三类验证。
10. 一个项目接入样例。

### 23.2 生成顺序要求

建议 AI 按以下顺序生成：

1. 目录结构和 schema
2. 模板和工件命名规范
3. 统一 bootstrap 文档
4. routing、rules 和 profile
5. MVP skills
6. MVP commands
7. hooks 和 adapters
8. validation scripts
9. tests
10. sample project integration

### 23.3 验收标准

- 所有 schema 可被验证脚本解析。
- 所有模板可实例化成有效工件。
- 路由器能根据阶段工件和风险 profile 给出正确流程建议。
- Hook 能拦截至少 3 类高风险行为。
- 验证脚本能检查工件完整性、追溯关系和 Gate 前置条件。
- 样例项目能够演示从需求到验证的最小闭环。

## 24. 分阶段落地建议

### 24.1 第一阶段：建立控制面骨架

优先交付：

- 目录、schema、模板
- bootstrap
- routing
- 基础 rules

### 24.2 第二阶段：建立主流程最小闭环

优先交付：

- requirements
- design
- implement
- verify
- release

### 24.3 第三阶段：补强车载特化能力

优先交付：

- safety pack
- cybersecurity pack
- diagnostics pack
- performance pack
- traceability checks

### 24.4 第四阶段：接入工具和台架

优先交付：

- build connector
- static analysis connector
- simulation connector
- bench proxy

### 24.5 第五阶段：运营与优化

优先交付：

- metrics dashboard
- exception analytics
- periodic verification
- retrospective assets

## 25. 关键设计决策

建议在正式实现前冻结以下决策：

1. 主宿主环境是什么，是否需要多宿主。
2. 项目状态目录统一使用何种路径。
3. Gate 与审批矩阵是否按 ASIL 和模块类型区分。
4. 追溯是否落在文件工件、数据库或二者混合。
5. Bench/HIL 是否通过代理层而不是直接开放给 AI。
6. 哪些高风险模块只允许 `propose-only`。
7. 哪些验证属于每次 Gate 必跑，哪些属于周期性运行。

## 26. 成功标准

一套成功的团队级车载嵌入式 Harness Engineering 框架，至少应具备以下可观察特征：

- AI 不会在缺少需求、设计或审批时直接进入编码。
- 任意阶段都可以从工件恢复当前状态。
- 任意结论都能追溯到原始证据。
- 需求、设计、代码、测试之间存在可检查的追溯链。
- 关键发布活动必须经过人工批准，AI 不可越权。
- 高风险模块默认受到更严格的自动化限制。
- 框架本身具备自验证能力和可持续演进机制。

## 27. 结论

针对车载嵌入式软件团队，Harness Engineering 的本质不是“组织一批强提示词”，而是建立一套受控的软件交付系统，使 AI 可以在 IPD、功能安全、网络安全、实时性、资源约束和高质量研发要求下稳定工作。

与通用软件团队相比，车载嵌入式场景需要更强的阶段约束、更严格的证据模型、更清晰的审批边界、更早的测试策略前移，以及对 MCU/SoC、通信诊断、升级、安全和台架验证的专门建模。

因此，推荐采用本文档定义的框架：以治理、流程、工件、规则、工具、证据、审批七大核心要素为主线，以 schema、模板、技能、命令、Hook、连接器为落地资产，使后续 AI 能基于该说明书直接生成一套团队可用、可审计、可扩展的 Harness Engineering 框架。
