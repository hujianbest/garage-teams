# AHE Agent Platform Long-Term Roadmap And ADR Backlog

- 状态: 草稿
- 日期: 2026-04-09
- 定位: 基于现有平台优先架构判断，整理 AHE 演进为长期多 agent working system 所需的能力路线图与 ADR 清单。
- 用途: 本文不定义完整系统拓扑，也不承担 Phase 1 实现细节；它只回答“长期要建设哪些能力、按什么顺序推进、哪些关键架构决策必须单独立 ADR”。
- 关联文档:
  - `README.md`
  - `AGENTS.md`
  - `docs/architecture/ahe-platform-first-multi-agent-architecture.md`
  - `docs/architecture/ahe-workflow-skill-anatomy.md`
  - `docs/analysis/clowder-ai-harness-engineering-analysis.md`

## 1. 概述

当前仓库已经形成一个明确方向：

- 平台层必须使用 pack-neutral vocabulary
- `ahe-coding-skills/` 只保留为首个 coding pack
- 当前仓库仍然是 Markdown-first 的 harness engineering 工作台

真正缺少的，不再是“再写一份更大的架构文档”，而是：

- 哪些长期能力是必须建设的
- 它们的先后顺序是什么
- 哪些问题必须通过 ADR 单独冻结

因此本文把之前 working-system 级思考收敛成两个更可执行的产物：

1. `Long-Term Capability Roadmap`
2. `ADR Backlog`

---

## 2. 使用方式

本文应与 `docs/architecture/ahe-platform-first-multi-agent-architecture.md` 配合阅读：

- 架构文档回答“平台边界、核心对象与中立契约是什么”
- 本文回答“长期能力如何演进，以及哪些架构决策需要被正式记录”

本文不替代：

- 具体实现设计
- 逐步编码任务分解
- 某个单独 phase 的详细交付计划

---

## 3. 路线图设计原则

1. `Capability before implementation detail`
   路线图先按能力建设排序，而不是按文件改造顺序排序。

2. `Platform before pack proliferation`
   在第二个 pack 接入之前，先把 registry、governance、approval、evidence 等平台基线打稳。

3. `Human-in-the-loop remains first-class`
   审批、仲裁、回滚、归档和 release provenance 必须作为系统能力存在。

4. `Service-backed is the long-term destination`
   本仓当前可以 local-first，但 roadmap 必须明确哪些能力最终需要 service-backed。

5. `Operational reality over architecture prose`
   每个 phase 都需要有退出条件，不能只停留在术语或 Mermaid 图上。

---

## 4. 长期能力地图

### 4.1 能力流 A: 工作入口与协作模型

目标：

- 不再只有“触发一个 skill”
- 升级为 mission / thread / session 级的长期协作模型

包含能力：

- operator-facing ingress
- mission lifecycle
- thread isolation
- multi-session coordination
- human approval checkpoints

### 4.2 能力流 B: 控制面与编排

目标：

- 从 docs-driven routing 升级为真正的 orchestration substrate

包含能力：

- session routing
- pack registry
- node scheduling
- approval / pause / resume
- evidence / archive orchestration
- failure handling

### 4.3 能力流 C: 执行面与隔离

目标：

- 把“agent 执行在哪里、如何隔离、如何恢复”变成正式系统设计

包含能力：

- local runner
- remote runner
- worktree / sandbox management
- host adapter gateway
- tool / model adapter contracts
- resource quota and cleanup

### 4.4 能力流 D: 数据、记忆与可检索状态

目标：

- 从 file-backed state 逐步走向可查询、可回放、可审计的数据面

包含能力：

- metadata store
- event log
- evidence store
- archive store
- memory / search index
- config / secret management

### 4.5 能力流 E: 治理、安全与审计

目标：

- 把 repo-local governance 扩展为系统级 policy / authz / audit 模型

包含能力：

- identity
- authorization
- approval authority
- provenance
- policy layering
- exception handling

### 4.6 能力流 F: Pack 生态与运营

目标：

- 让 AHE 成为第一个 pack，而不是最后一个 pack

包含能力：

- pack lifecycle
- version / compatibility policy
- publishing contract
- capability discovery
- operator observability
- environment topology

---

## 5. 路线图阶段

### Phase 0: Control Plane Baseline

目标：

- 稳定当前平台优先边界
- 清除 AHE 私有语言对共享契约的反向绑死

关键结果：

- `docs/architecture/ahe-platform-first-multi-agent-architecture.md` 成为唯一主架构入口
- platform-neutral vocabulary 固化
- governance / artifact surface / evidence 的核心边界稳定

退出条件：

- 主要对象与术语不再依赖 `ahe-*` 命名
- pack boundary 可被第二个 pack 复用
- 主架构文档不再依赖已删除的上位 / 下位设计稿

### Phase 1: Reference Runtime Hardening

目标：

- 在当前仓库约束下，验证最小 reference runtime 能成立

关键结果：

- board / attempt / approval / archive 的最小 runtime contract 被验证
- progress projection 与 evidence append-only 行为清晰
- host adapter 与 pack integration 的接口轮廓稳定

退出条件：

- 可以稳定表达 create / resume / approve / archive 的最小控制流
- pack integration 不再把 router 语义硬编码到平台术语里
- phase-1 假设被清楚标记为阶段性，而非长期承诺

### Phase 2: Service Skeleton

目标：

- 从纯 repo-local 设计迈向最小常驻控制面

关键结果：

- session / orchestration / approval / evidence 的最小服务骨架
- evented state transition baseline
- 基础 API / callback contract

退出条件：

- 会话与审批不再只能靠本地文件状态恢复
- 至少存在一个 service-backed state path
- replay / audit 的基础数据链条可追踪

### Phase 3: Collaboration System

目标：

- 从“运行节点”升级为“协作系统”

关键结果：

- mission / thread / agent identity 模型落地
- operator review / approval / status visibility 基线可用
- 多 agent 协作和 fan-out / barrier 行为可表达

退出条件：

- 长期任务不再只能用单 session 表达
- 人与 agent 的职责边界在系统对象中可见
- review / gate / audit 可作为独立 worker 存在

### Phase 4: Data And Governance Platform

目标：

- 建立长期运行必需的数据面与治理面

关键结果：

- metadata / event / archive / evidence / search 的分层
- system policy + workspace policy + repo-local governance 三层模型
- identity / authz / provenance 基线

退出条件：

- 审计链条可回答“谁做了什么、为何被放行、由谁批准”
- 多环境状态不再依赖单仓 Markdown 文件
- secret / config / policy 拥有清晰承载面

### Phase 5: Multi-Pack Platform And Operations

目标：

- 从 AHE 单 pack 走向可运营的多 pack 平台

关键结果：

- 第二个非 coding pack 接入
- pack publishing / compatibility / upgrade contract 成形
- observability、incident response、backup、rollback 成为正式运营能力

退出条件：

- 平台不再与 AHE pack 强绑定
- 环境拓扑、发布流程、恢复流程可以单独演练
- pack ecosystem 能在不重写控制面的情况下扩展

---

## 6. 近期优先级

若只看最近几轮架构演进，优先顺序应是：

1. 稳定平台中立词汇与 pack boundary。
2. 冻结最小控制面对象与状态转移语义。
3. 冻结 approval / evidence / archive 的 authority 边界。
4. 冻结 execution isolation 与 host adapter 接口。
5. 再讨论 Web、shared runtime、多 pack 运营面。

理由：

- 如果前四项不稳，后续所有 UI、service、multi-pack 讨论都会建立在漂移对象模型之上。

---

## 7. ADR Backlog

以下 ADR 不应混在单个大文档里隐式成立，而应逐项冻结。

| ADR | 主题 | 目标 Phase | 需要冻结的问题 |
| --- | --- | --- | --- |
| `ADR-001` | 核心领域对象模型 | Phase 0-1 | `project / repo / mission / thread / session / node / artifact / evidence` 的边界如何定义 |
| `ADR-002` | 控制面服务拆分 | Phase 1-2 | session、orchestration、approval、evidence、archive 是否拆分为独立服务 |
| `ADR-003` | 状态真相源分层 | Phase 1-2 | 哪些状态属于 artifact、metadata、event log、projection、cache |
| `ADR-004` | 执行隔离模型 | Phase 1-2 | local runner、remote runner、worktree、sandbox 的最小隔离单元是什么 |
| `ADR-005` | Host Adapter Gateway contract | Phase 1-2 | 平台如何抽象 Cursor、CLI、subagent、future host 的差异 |
| `ADR-006` | Approval authority model | Phase 1-3 | approval checkpoint、override、human confirmation、auto approval 的权限边界是什么 |
| `ADR-007` | Governance layering | Phase 1-4 | system policy、workspace policy、repo-local governance 如何合并与冲突裁决 |
| `ADR-008` | Identity and authorization | Phase 2-4 | operator、agent、pack author、system operator 的身份与授权模型是什么 |
| `ADR-009` | Mission / thread collaboration model | Phase 2-3 | 何时需要 mission、thread、session 三层对象，它们如何关联 |
| `ADR-010` | Pack registry and lifecycle | Phase 2-5 | pack 的注册、版本、兼容、发布、弃用规则如何定义 |
| `ADR-011` | Data platform shape | Phase 3-4 | metadata、evidence、archive、search、secret/config 各自的承载面是什么 |
| `ADR-012` | Environment topology | Phase 3-5 | local、alpha、shared、production 的职责边界与 promotion 路径是什么 |
| `ADR-013` | Observability and replay | Phase 3-5 | logs、metrics、trace、audit、replay 应如何关联 |
| `ADR-014` | External interface strategy | Phase 3-5 | CLI、API、Web、chat connector、MCP 哪些是正式入口，哪些只是 adapter |

---

## 8. ADR 排期建议

### 第一批必须先定

- `ADR-001` 核心领域对象模型
- `ADR-003` 状态真相源分层
- `ADR-004` 执行隔离模型
- `ADR-006` Approval authority model

原因：

- 这四项直接决定对象边界、控制权边界和风险边界。

### 第二批紧随其后

- `ADR-002` 控制面服务拆分
- `ADR-005` Host Adapter Gateway contract
- `ADR-007` Governance layering
- `ADR-009` Mission / thread collaboration model

原因：

- 这批 ADR 决定系统从“单仓 runtime”向“长期协作平台”转型时的结构稳定性。

### 第三批在平台化进入中后期再冻结

- `ADR-008`
- `ADR-010`
- `ADR-011`
- `ADR-012`
- `ADR-013`
- `ADR-014`

原因：

- 它们重要，但需要以前两批 ADR 为前提，否则容易过早抽象。

---

## 9. 完成标准

如果未来说 AHE 已经从“skill family”演进成“长期多 agent working system”，至少要能满足：

- 平台不再依赖单一 pack 才能解释自身
- 长期协作可以用 mission / thread / session 等正式对象表达
- approval、evidence、archive、audit 由系统能力承接，而不是只在 prose 中描述
- 至少有一部分关键状态已经 service-backed
- pack 可以独立演进，而不会反向重写平台 vocabulary
- operator 能看到系统状态、审批链和关键恢复信息

---

## 10. 一句话结论

下一阶段最重要的不是继续堆更大的“总设计文档”，而是围绕 `docs/architecture/ahe-platform-first-multi-agent-architecture.md`，按能力流推进平台演进，并把对象模型、状态真相源、执行隔离、审批权限、治理分层和 pack 生命周期这些关键问题逐项沉淀成 ADR。
