# 高保障嵌入式团队 Harness Engineering 框架设计说明书

## 1. 文档定位

本文档用于为高保障嵌入式软件团队设计一套可直接落地的 Harness Engineering 框架，使 AI 可以在高约束、高追溯、高验证要求下参与软件系统开发。

本文档不是单个 Prompt、单个 Agent 或单个命令的说明，而是后续 AI 生成完整框架仓库时应遵循的设计规范。其目标是同时服务于两类使用者：

- 人类团队：用于统一框架目标、边界、流程、职责和质量标准。
- AI 生成器：用于直接生成目录结构、规则集、技能、命令、Hook、Schema、模板、验证脚本和样例项目。

本文档面向以下场景：

- 团队以 C、C++、Python 工具链为主，从事 MCU、RTOS、裸机、Linux、QNX 或 SoC 平台软件开发。
- 研发过程强调需求追溯、设计评审、测试证据、变更控制和发布审计。
- 软件质量要求特别高，不能接受 AI 在缺少约束和证据的情况下自由进入编码或放行。
- 期望 AI 不仅辅助写代码，还辅助完成需求澄清、设计分析、实现、验证、发布和复盘。

## 2. 设计输入与来源映射

本方案基于 `docs/` 目录下 5 篇高星 GitHub Harness Engineering 框架分析抽象而来：

- `docs/get-shit-done-main-harness-engineering-analysis.md`
- `docs/longtaskforagent-main-harness-engineering-analysis.md`
- `docs/superpowers-main-harness-engineering-analysis.md`
- `docs/gstack-main-harness-engineering-analysis.md`
- `docs/everything-claude-code-main-harness-engineering-analysis.md`

### 2.1 共性结论

从这 5 份分析中，可以抽象出 8 条稳定工程规律：

1. 先路由后执行，不能让 AI 直接跳到编码。
2. 长期状态必须外置为工件，不能依赖会话记忆。
3. 工作必须阶段化，且每阶段有输入、输出和门禁。
4. AI 必须角色化，不能依赖一个万能 Agent。
5. 验证和证据必须位于主流程，而不是收尾附属动作。
6. 规则、技能、命令、Hook、连接器必须分层治理。
7. 宿主和工具差异必须沉到底层适配，不能污染核心流程。
8. Harness 本身必须可测试、可审计、可演进。

### 2.2 来源洞察到生成资产映射

| 来源框架 | 关键洞察 | 本方案要求 | 对应生成资产 |
|---|---|---|---|
| get-shit-done | 阶段化 workflow、文件态状态、薄编排器、验证闭环 | 建立阶段路由、状态目录、可恢复工作流、验证闭环 | `skills/stage-router/`、`.ai-harness/state/`、`commands/verify.md` |
| longtaskforagent | JSON + Markdown 双工件、强门禁链、跨会话恢复 | 结构化状态工件与人工可读工件并存，Gate 失败必须回退 | `schemas/*.json`、`templates/*.md`、`scripts/gate_check.py` |
| superpowers | bootstrap skill、session-start 注入、顺序化 review gate | 统一 bootstrap 契约，所有会话先学习框架再执行任务 | `skills/using-embedded-harness/`、`hooks/session-start/` |
| gstack | 模板生成、统一 preamble、registry 单一事实源、diff-aware 验证 | 技能与注册表可生成，工具定义单一来源，分层分级验证 | `templates/`、`registry/connectors.yaml`、`scripts/select_checks.py` |
| everything-claude-code | rules/skills/commands/hooks/agents 分层、profile/module、治理优先 | 形成稳定控制面分层，支持按风险和团队场景切换 profile | `rules/`、`skills/`、`commands/`、`hooks/`、`profiles/` |

### 2.3 面向高保障嵌入式团队的特化要求

在上述共性基础上，嵌入式高质量团队必须额外满足以下要求：

- 资源、实时性、异常处理、并发、中断和启动顺序必须前移到设计阶段。
- 任何设计和实现结论都必须能追溯到需求、约束和验证证据。
- 高风险模块默认禁止 AI 直接放行，只允许 `propose-only` 或 `controlled-edit`。
- 验证策略必须按成本和可信度分层，避免把昂贵验证变成无法长期执行的流程负担。
- 框架要支持离线或内网环境，不强依赖公网服务。

## 3. 设计目标与非目标

### 3.1 设计目标

1. 形成一套适用于高保障嵌入式团队的 Harness Engineering 标准框架。
2. 支持 AI 参与需求、设计、实现、验证、发布和变更闭环。
3. 保证所有阶段可追溯、可恢复、可审计、可验证。
4. 支持多宿主接入，但保持核心流程资产稳定。
5. 支持按风险等级切换流程强度。
6. 让本文档足以直接指导 AI 生成完整框架仓库。

### 3.2 非目标

1. 不试图一次性替代现有 ALM、CI、仿真、板级台架或发布平台。
2. 不允许 AI 独立批准架构、发布、残余风险接受和偏差豁免。
3. 不把所有研发活动都自动化，人工评审仍然是高风险环节的必需动作。
4. 不要求所有项目一开始就采用全部模块，可按 profile 渐进接入。

## 4. 质量属性与系统级约束

框架必须围绕以下质量属性设计：

| 质量属性 | 说明 | 设计约束 |
|---|---|---|
| 可审计性 | 任意结论都能找到输入、执行、证据和批准记录 | 所有阶段状态与结果必须落地为工件 |
| 可追溯性 | 需求、设计、代码、测试、发布必须形成链路 | 必须维护结构化追溯链接 |
| 可恢复性 | 会话中断后能从工件恢复上下文和阶段 | 禁止把长期状态只保存在聊天上下文 |
| 可重复性 | 相同输入应得到可复查的相似输出 | 模板、Schema、命名规则和工具注册表必须稳定 |
| 安全边界 | 高风险行为必须被约束和拦截 | 危险命令、高风险目录、敏感数据使用 Hook 拦截 |
| 低漂移性 | 文档、模板、规则、生成结果不能长期漂移 | 生成链路、freshness 校验和回归测试必须存在 |
| 低运维摩擦 | 团队能长期维护，不因流程过重而弃用 | 验证按 fast、gate、scenario、periodic 分层 |

## 5. 总体架构

框架采用“核心控制面 + 执行面 + 扩展面 + 证据面”四域架构。

### 5.1 核心控制面

用于定义框架的稳定行为，不随项目类型频繁变化。

- Bootstrap/Preamble
- Governance Policy
- Stage Router
- Rules / Skills / Commands / Hooks
- Artifact Registry
- Traceability Engine
- Gate Engine
- Approval Ledger

### 5.2 执行面

用于承接实际开发活动。

- AI 角色执行器
- Controlled Edit Runner
- Verification Runner
- Sandboxed Build Runner
- Release Packager

### 5.3 扩展面

用于隔离可变因素。

- Host Adapters
- Tool Connectors
- Profile Definitions
- Domain Packs
- Project Integration State

### 5.4 证据面

用于沉淀新鲜验证证据和审批链。

- Evidence Vault
- Review Records
- Gate Results
- Approval Records
- Release Decision Pack

## 6. 生命周期与流程模型

### 6.1 主流程

建议基础版本采用 6 阶段主流程：

| 阶段 | 目标 | 主要输出 |
|---|---|---|
| S0 Intake | 确认范围、风险、输入是否完整 | Work Packet、风险分级、Profile 选择 |
| S1 Requirements | 形成可验证需求与约束 | Requirement Pack、Acceptance Criteria |
| S2 Design | 形成架构与详细设计 | Architecture Pack、Detailed Design、Test Strategy |
| S3 Implement | 在受控边界内实现并提交草稿 | Code Change Pack、Unit Tests、Review Record |
| S4 Verify | 形成验证证据与闭环判断 | Verification Record、Evidence Manifest、Gate Result |
| S5 Release/Maintain | 形成发布包或变更闭环 | Release Pack、Change Log、Lessons Learned |

### 6.2 支线流程

必须支持以下支线：

- Change Request：针对新增需求、规格变化、接口变化。
- Hotfix：针对已交付版本缺陷，要求最小变更和强化影响分析。
- Investigation：针对故障定位、异常追踪、根因分析。

### 6.3 风险 Profile

建议定义 4 级 profile：

| Profile | 适用对象 | 特征 |
|---|---|---|
| P0 探索型 | 内部工具、实验脚本 | 轻量工件、最小验证 |
| P1 标准型 | 常规嵌入式模块 | 完整主流程、标准验证 |
| P2 强约束型 | 平台、驱动、通信、关键接口 | 强化追溯、强化评审、强化回归 |
| P3 高保障型 | 安全关键、升级链路、启动链、关键控制逻辑 | 最严格门禁、只允许受限自动化 |

Profile 切换输入至少包括：

- 模块关键性
- 变更类型
- 运行环境风险
- 是否影响启动、升级、安全或通信链路
- 是否影响资源与实时预算

## 7. 人类角色与 AI 角色

### 7.1 人类核心角色

| 角色 | 主要职责 | AI 是否可辅助 | AI 是否可替代 |
|---|---|---|---|
| 系统/需求负责人 | 定义需求、边界和验收标准 | 是 | 否 |
| 架构师 | 架构方案、接口、资源和异常流设计 | 是 | 否 |
| 模块负责人 | 详细设计、实现、缺陷修复 | 是 | 否 |
| 测试负责人 | 测试策略、覆盖目标、验证结论 | 是 | 否 |
| 质量/流程负责人 | 门禁、偏差、审计和流程合规 | 是 | 否 |
| 配置/发布负责人 | 基线、版本和发布放行 | 是 | 否 |
| Harness Owner | 规则、技能、Hook、模板和生成链路维护 | 是 | 否 |

### 7.2 AI 角色

| AI 角色 | 输入 | 输出 | 权限边界 |
|---|---|---|---|
| Router | 用户请求、项目状态、Profile | Stage 决策、流程建议 | 不修改业务工件 |
| Researcher | 需求、标准、上下文 | 约束摘要、问题清单 | 只读 |
| Architect | 需求、平台限制、历史设计 | 架构草案、设计草案、权衡分析 | 不可批准设计 |
| Planner | 设计、风险、验证要求 | 任务拆解、验证计划 | 不可跳过上游工件 |
| Implementer | 已批准设计、任务包 | 代码草稿、文档草稿、测试草稿 | 只改白名单目录 |
| Reviewer | 变更包、规则、证据 | 评审结论、缺口清单 | 不可自我批准 |
| Verifier | 测试报告、日志、证据 | 验证记录、Gate 建议 | 不可伪造证据 |
| Release Assistant | 验证结果、审批记录 | 发布包草稿、变更说明 | 不可独立放行 |

### 7.3 AI 执行模式

| 模式 | 说明 | 典型场景 |
|---|---|---|
| readonly-analyze | 只读分析 | 调研、审查、根因定位 |
| draft-generate | 生成草稿但不推进状态 | 需求草稿、设计草稿、测试草稿 |
| controlled-edit | 在白名单目录内受控修改 | 文档修改、代码 patch |
| controlled-verify | 执行白名单验证工具 | 构建、静态分析、单测 |
| propose-only | 只能给建议 | 高风险模块、关键发布链路 |

## 8. 工作包、结果包与工件体系

### 8.1 Work Packet

每次 AI 执行必须由结构化工作包驱动，字段至少包括：

- `work_id`
- `request_type`
- `stage`
- `profile`
- `component`
- `platform`
- `criticality`
- `scope_in`
- `scope_out`
- `source_artifacts`
- `allowed_tools`
- `required_outputs`
- `required_evidence`
- `required_reviewers`
- `required_approvers`
- `execution_mode`

### 8.2 Result Packet

每次 AI 执行必须输出结构化结果包，字段至少包括：

- `work_id`
- `summary`
- `changed_artifacts`
- `assumptions`
- `known_gaps`
- `risks`
- `trace_updates`
- `verification_performed`
- `verification_pending`
- `evidence_manifest`
- `required_human_actions`
- `next_stage`
- `confidence`

### 8.3 工件分类

建议分为 7 类：

1. 需求类工件
2. 设计类工件
3. 实现类工件
4. 测试类工件
5. 证据类工件
6. 发布类工件
7. 变更与偏差类工件

### 8.4 Markdown 与结构化文件分工

- Markdown：面向人类阅读的需求、设计、评审、验证说明。
- YAML/JSON：面向机器校验的状态、Gate、追溯链接、Manifest、Registry。
- 二者必须通过 ID 关联，而不是靠自然语言猜测。

## 9. 追溯模型

### 9.1 基础追溯链

至少维护以下关系：

- 需求 -> 设计
- 设计 -> 任务
- 任务 -> 代码变更
- 需求 -> 测试
- 代码变更 -> 构建结果
- 测试 -> 证据
- 证据 -> Gate 结论
- Gate 结论 -> 批准记录

### 9.2 AI 运行追溯链

新增以下专用链路：

- AI Run -> Work Packet -> Tool Calls -> Changed Artifacts -> Evidence -> Reviewer -> Approver

### 9.3 追溯检查规则

必须满足：

- 进入设计阶段的需求必须有设计映射。
- 进入实现阶段的设计必须有任务映射。
- 声称完成的任务必须有验证和证据映射。
- 准备发布的版本必须能追溯到所有纳入变更的来源、验证和审批记录。

## 10. 质量门禁与验证策略

### 10.1 基础 Gate

| Gate | 名称 | 进入条件 | 退出条件 | 人工批准要求 |
|---|---|---|---|---|
| G0 | Intake Gate | 请求完整、范围清晰 | Work Packet 可执行 | 模块负责人 |
| G1 | Requirement Gate | 需求已成稿 | 需求可验证、边界清晰 | 需求负责人 |
| G2 | Design Gate | 需求稳定 | 设计完整、资源和异常流明确 | 架构师 |
| G3 | Implement Gate | 设计和测试策略齐备 | 实现任务可执行 | 模块负责人 |
| G4 | Unit Quality Gate | 代码已提交 | 构建、静态检查、单测通过 | 模块负责人/质量负责人 |
| G5 | Integration Gate | 单元质量通过 | 集成与接口验证通过 | 测试负责人 |
| G6 | System/Release Gate | 验证和追溯完整 | 审批齐备、可发布或可关闭 | 发布负责人 |

### 10.2 验证分层

必须按成本和可信度分层：

- Fast Checks：Schema、命名、引用、规则静态检查。
- Gate Checks：编译、静态分析、单元测试、覆盖率、关键接口测试。
- Scenario Checks：SIL、仿真、板级测试、关键场景测试。
- Periodic Checks：长稳测试、故障注入、鲁棒性和回归测试。

### 10.3 Diff-aware 验证原则

验证选择必须考虑变更范围：

- 只改文档和模板时，允许只跑 fast checks。
- 改规则、Hook、Router 时，必须跑框架自身回归。
- 改连接器和验证脚本时，必须跑对应模块和代表性 E2E。
- 改高风险模块时，必须升级到 profile 对应的 scenario 或 periodic 检查。

### 10.4 Gate 失败动作

任一 Gate 失败时，系统必须输出：

- 缺口清单
- 回退阶段
- 必补证据
- 必需人工动作

禁止“带缺口默默继续”。

## 11. 模块规格定义

这是 AI 直接生成框架时的核心章节。每个模块都必须被视为一个可生成单元。

### 11.1 Bootstrap 模块

- 目标：确保每个会话在行动前先装载框架总则。
- 输入：`AGENTS.md`、当前项目状态、Profile。
- 输出：统一 preamble、当前阶段摘要、风险提醒。
- 依赖：Stage Router、Profile Loader。
- 失败行为：退化到只读模式并提示缺失输入。

### 11.2 Stage Router 模块

- 目标：根据请求和现有工件判断当前阶段与推荐流程。
- 输入：Work Packet、状态目录、现有工件索引。
- 输出：阶段判定、推荐命令、禁止动作列表。
- 依赖：Artifact Registry、Profile Definition。
- 失败行为：进入 `intake-required` 状态，不允许继续编码。

### 11.3 Governance/Profile 模块

- 目标：定义哪些动作允许自动化，哪些必须人工批准。
- 输入：风险等级、模块类别、变更类型。
- 输出：权限矩阵、Gate 强度、审批矩阵。
- 依赖：Profile 文件、Rule Manifest。

### 11.4 Artifact Registry 模块

- 目标：管理所有工件路径、ID、类型、状态和引用关系。
- 输入：工件清单、模板、命名规则。
- 输出：`artifact-index.yaml`、工件解析接口。
- 依赖：Artifact Schema、Naming Rules。

### 11.5 Traceability Engine 模块

- 目标：维护需求到发布的追溯关系。
- 输入：工件 ID、Trace Link、Gate Result。
- 输出：追溯矩阵、缺失追溯报告。
- 依赖：Trace Link Schema、Artifact Registry。

### 11.6 Rule/Skill/Command/Hook Loader 模块

- 目标：形成稳定控制面装配机制。
- 输入：Manifest、模板、宿主适配配置。
- 输出：可安装资产、宿主可识别目录结构。
- 依赖：Host Adapter、Template Generator。

### 11.7 Connector Registry 模块

- 目标：把外部系统能力定义为单一事实源。
- 输入：工具定义、参数 Schema、权限级别。
- 输出：`registry/connectors.yaml`、连接器说明文档。
- 依赖：Connector Schema、Hook 权限策略。

### 11.8 Verify Runner 模块

- 目标：统一执行 fast/gate/scenario/periodic 检查。
- 输入：变更范围、Profile、Connector Registry。
- 输出：验证结果、证据索引、Gate 建议。
- 依赖：Evidence Schema、Gate Schema。

### 11.9 Approval Ledger 模块

- 目标：保存人工审批、偏差、残余风险接受记录。
- 输入：Gate Result、人工动作、偏差单。
- 输出：`approval-ledger.yaml`、`exception-ledger.yaml`。
- 依赖：Approval Schema。

### 11.10 Release Packager 模块

- 目标：在追溯和验证完整后形成发布包草稿。
- 输入：版本清单、二进制清单、Gate 记录、审批记录。
- 输出：Release Pack、Compatibility Matrix、Release Notes。
- 依赖：Artifact Registry、Approval Ledger。

## 12. 仓库蓝图与文件生成清单

### 12.1 框架仓库目录

```text
harness-framework/
  AGENTS.md
  README.md
  rules/
  skills/
  commands/
  hooks/
  agents/
  adapters/
  profiles/
  registry/
  schemas/
  templates/
  scripts/
  tests/
  docs/
  examples/
```

### 12.2 项目接入目录

```text
.ai-harness/
  state/
  artifacts/
  evidence/
  traces/
  approvals/
  runtime/
```

### 12.3 关键文件清单

| 路径 | 类型 | 生成方式 | 说明 |
|---|---|---|---|
| `AGENTS.md` | Markdown | 首次手写 + AI 填充 | 框架总则与行为宪法 |
| `rules/common/*.md` | Markdown | 模板生成 | 通用约束 |
| `rules/embedded-c/*.md` | Markdown | 模板生成 | C 语言嵌入式约束 |
| `rules/embedded-cpp/*.md` | Markdown | 模板生成 | C++ 嵌入式约束 |
| `skills/using-embedded-harness/SKILL.md` | Markdown | 模板生成 | bootstrap 技能 |
| `skills/stage-router/SKILL.md` | Markdown | 模板生成 | 阶段路由技能 |
| `commands/plan.md` | Markdown | 模板生成 | 规划入口 |
| `commands/verify.md` | Markdown | 模板生成 | 验证入口 |
| `hooks/session-start/*` | Script | 首次手写 + AI 填充 | 注入 bootstrap 和状态摘要 |
| `hooks/pre-tool-use/*` | Script | 首次手写 + AI 填充 | 危险命令与越界编辑拦截 |
| `registry/connectors.yaml` | YAML | 模板生成 | 工具定义单一事实源 |
| `profiles/base.yaml` | YAML | 模板生成 | 基础 profile |
| `profiles/high-assurance.yaml` | YAML | 模板生成 | 高保障 profile |
| `schemas/work-packet.schema.json` | JSON Schema | 模板生成 | 工作包契约 |
| `schemas/result-packet.schema.json` | JSON Schema | 模板生成 | 结果包契约 |
| `schemas/gate.schema.json` | JSON Schema | 模板生成 | Gate 契约 |
| `schemas/evidence.schema.json` | JSON Schema | 模板生成 | 证据契约 |
| `schemas/approval.schema.json` | JSON Schema | 模板生成 | 审批契约 |
| `schemas/trace-link.schema.json` | JSON Schema | 模板生成 | 追溯契约 |
| `templates/*.md` | Markdown Template | 模板生成 | 需求/设计/评审/验证模板 |
| `scripts/validate_artifacts.py` | Python | AI 生成 | 工件完整性检查 |
| `scripts/validate_trace.py` | Python | AI 生成 | 追溯检查 |
| `scripts/gate_check.py` | Python | AI 生成 | Gate 前置条件检查 |
| `scripts/select_checks.py` | Python | AI 生成 | diff-aware 检查选择 |
| `tests/schemas/*` | Test | AI 生成 | Schema 校验回归 |
| `tests/routing/*` | Test | AI 生成 | Router 回归 |
| `tests/hooks/*` | Test | AI 生成 | Hook 行为回归 |
| `examples/minimal-project/` | Sample | AI 生成 | 最小闭环接入示例 |

## 13. 机器可读契约

后续 AI 生成框架时，必须至少实现以下 Schema 或 Manifest：

- Work Packet Schema
- Result Packet Schema
- Artifact Schema
- Gate Schema
- Evidence Schema
- Approval Schema
- Trace Link Schema
- Rule Manifest Schema
- Skill Manifest Schema
- Command Manifest Schema
- Hook Manifest Schema
- Connector Registry Schema
- Profile Definition Schema

### 13.1 Work Packet 示例

```yaml
work_id: HW-0001
request_type: change_request
stage: S2_design
profile: P2
component: communication_manager
platform:
  kind: mcu
  os: rtos
criticality: high
scope_in:
  - REQ-COM-001
source_artifacts:
  - .ai-harness/artifacts/requirements/REQ-COM-001.md
allowed_tools:
  - repo.read
  - repo.edit
  - build.compile
required_outputs:
  - detailed_design
required_evidence:
  - trace_update
execution_mode: controlled-edit
```

### 13.2 Result Packet 示例

```yaml
work_id: HW-0001
summary: 完成通信管理模块详细设计草稿与任务拆解
changed_artifacts:
  - .ai-harness/artifacts/design/DD-COM-001.md
assumptions:
  - 复用现有消息队列接口
known_gaps:
  - 超时参数尚未完成评审
risks:
  - 异常路径仍需板级验证
trace_updates:
  - REQ-COM-001 -> DD-COM-001
verification_performed:
  - schema_check
verification_pending:
  - architecture_review
required_human_actions:
  - approve_design
next_stage: G2
confidence: medium
```

### 13.3 Connector Registry 示例

```yaml
connectors:
  - id: build.compile
    class: build
    risk: medium
    adapter: local-shell
    inputs:
      - source_root
      - build_profile
    outputs:
      - build_log
  - id: test.unit
    class: verify
    risk: medium
    adapter: local-shell
    inputs:
      - test_target
    outputs:
      - unit_report
```

## 14. AI 生成契约

本章是本文档的规范性核心。后续任何 AI 生成框架时，必须遵循以下约束。

### 14.1 MUST

AI 必须：

1. 先生成目录、Schema、模板，再生成技能、命令、Hook 和脚本。
2. 把规则、技能、命令、Hook、连接器分目录管理，不得混写。
3. 让所有跨阶段状态落到 `.ai-harness/` 目录或框架仓库控制面目录。
4. 为每个 Gate、Schema、Hook 和 Router 生成最小回归测试。
5. 使用单一 `registry/connectors.yaml` 作为工具定义真相源。
6. 为高风险动作提供 Hook 拦截或至少 `propose-only` 限制。
7. 为每个生成文件提供可解释命名和最小注释。

### 14.2 SHOULD

AI 应当：

1. 优先复用模板生成而不是手写重复内容。
2. 先实现最小闭环，再补强高级 profile 和领域包。
3. 让验证脚本只跑高信号检查，不跑无关全量检查。
4. 对缺失输入给出问题清单，而不是猜测关键约束。

### 14.3 MAY

AI 可以：

1. 在不破坏核心契约的前提下增加辅助文档或示例。
2. 为不同宿主生成薄适配层。
3. 在 `profiles/` 和 `docs/` 中增加领域专用包。

### 14.4 MUST NOT

AI 不得：

1. 在缺少阶段工件时直接生成实现代码。
2. 创建“已批准”状态或伪造验证通过记录。
3. 绕过 Hook、Gate 和审批矩阵。
4. 把连接器定义散落到多个文档中。
5. 将高风险领域规则硬编码进基础 profile，而不通过扩展 profile 表达。

### 14.5 生成顺序

推荐按以下顺序生成：

1. 目录结构
2. Schema 与 Registry
3. 模板
4. Bootstrap 与 Router
5. 基础 Rules
6. MVP Skills
7. MVP Commands
8. Hooks
9. 验证脚本
10. Harness 回归测试
11. 最小样例项目

## 15. 实施 Prompt 套件

为了减少后续 AI 生成偏差，建议直接使用以下 Prompt 结构。

### 15.1 顶层生成 Prompt

“基于 `designs/high-assurance-embedded-harness-engineering-framework-design.md`，生成一套高保障嵌入式团队 Harness Engineering 框架仓库。严格遵循文档中的目录、模块、Schema、生成契约和验收矩阵。先生成控制面骨架，再生成模板、技能、命令、Hook、脚本、测试和样例项目。不得跳过 Schema、Registry 和测试文件。”

### 15.2 模块生成 Prompt

“只生成 `<module-name>` 模块。输入是本文档对应章节。输出必须包含：文件清单、核心内容、依赖、最小测试。不得修改未授权目录。”

### 15.3 修复 Prompt

“根据失败的测试或 Schema 校验结果，仅修复直接相关文件。不得重写无关模块。修复后重新运行对应最小测试。”

## 16. 验收矩阵与 Golden Paths

### 16.1 最小闭环验收场景

| 场景 | 输入 | 预期产物 | 通过标准 |
|---|---|---|---|
| A1 新功能最小闭环 | 需求草稿 | Work Packet、设计草稿、验证记录 | 能从 `route -> plan -> design -> verify` 跑通 |
| A2 变更请求 | 已有需求与设计 | 影响分析、更新后的追溯链接 | 变更影响可定位且 Gate 正确升级 |
| A3 热修复 | 缺陷记录、目标版本 | Hotfix Record、最小回归结果 | 不绕过审批和回归 |
| A4 Hook 拦截 | 危险命令或越界修改 | 拦截日志、失败说明 | 高风险动作被阻止 |
| A5 Schema 校验 | 样例工件集合 | 校验报告 | 无非法字段、无缺失必填项 |
| A6 Router 回归 | 多种项目状态 | 阶段判定结果 | 判定与工件状态一致 |

### 16.2 Harness 自身回归

必须至少包含：

- Schema 解析测试
- Router 状态迁移测试
- Hook 拦截测试
- Connector Registry 一致性测试
- `verify` 命令最小工作流测试

## 17. Domain Profile 机制

基础框架只定义通用高保障嵌入式能力。行业或领域特殊要求必须通过 Profile 或 Domain Pack 扩展。

### 17.1 基础 Profile

基础 Profile 必须覆盖：

- 嵌入式 C/C++ 开发规范
- 需求-设计-实现-验证闭环
- 资源和异常处理设计
- 追溯与审批
- 受控验证

### 17.2 Automotive Profile 示例

如果团队处于车载场景，可在扩展层增加：

- 功能安全规则包
- 网络安全规则包
- 诊断与升级规则包
- MCU/SoC 双模约束
- HIL/台架分层验证
- 更严格的人工批准矩阵

### 17.3 其他可选 Profile

- Medical
- Industrial Control
- Rail Transit
- Avionics Support Tools

## 18. 分阶段落地建议

### 18.1 阶段一：控制面骨架

优先交付：

- 目录、Schema、Registry、模板
- Bootstrap 和 Router
- 基础 Rules

### 18.2 阶段二：主流程最小闭环

优先交付：

- plan
- design
- implement
- verify
- release

### 18.3 阶段三：验证与审计补强

优先交付：

- Traceability Engine
- Gate Runner
- Approval Ledger
- Hook 行为测试

### 18.4 阶段四：领域扩展与宿主适配

优先交付：

- Host Adapters
- Domain Packs
- 高风险 Profile

## 19. 成功标准

一套成功的高保障嵌入式团队 Harness Engineering 框架，至少应具备以下可观察特征：

- AI 不会在缺少需求、设计或审批时直接进入编码。
- 任意阶段都能从工件恢复当前状态。
- 任意结论都能追溯到原始证据。
- 高风险动作受到 Hook 或 Profile 约束。
- 框架自身具备最小回归测试和可验证生成链路。
- 团队可从本文档直接生成可运行的框架仓库骨架。

## 20. 结论

对于高保障嵌入式团队，Harness Engineering 的核心不是“组织一批更强提示词”，而是建立一套受控的软件交付系统，让 AI 在强约束、高追溯和高验证前提下稳定参与研发。

本说明书给出了该系统的设计输入、质量目标、总体架构、生命周期、角色模型、工件体系、追溯模型、质量门禁、模块规格、文件清单、机器可读契约、生成契约、实施 Prompt 和验收矩阵。后续 AI 应基于本文档先生成控制面骨架，再逐步生成流程资产与验证资产，从而形成一套团队可用、可审计、可扩展的 Harness Engineering 框架。
