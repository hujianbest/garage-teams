# Garage Phase 1 Core Runtime Records

- 状态: 草稿
- 日期: 2026-04-11
- 定位: 在 `garage-core-subsystems-architecture.md` 已定义 `Garage Core` 五个稳定子系统的基础上，进一步冻结 phase 1 的 core 运行时对象、持久记录与写入语义，避免后续实现时各自发明不同的 session、governance、artifact routing 与 evidence 记录形状。
- 当前阶段: phase 1
- 关联文档:
  - `docs/garage/README.md`
  - `docs/garage/garage-core-subsystems-architecture.md`
  - `docs/garage/garage-phase1-session-lifecycle-and-handoffs.md`
  - `docs/garage/garage-phase1-governance-model.md`
  - `docs/garage/garage-phase1-artifact-and-evidence-surface.md`
  - `docs/garage/garage-phase1-shared-contract-schemas.md`

## 1. 文档目标与范围

这篇文档只回答一个问题：

**phase 1 中，`Garage Core` 自己有哪些必须稳定存在的运行时对象与记录对象，它们如何被写入、如何互相引用、哪些是当前权威位、哪些是追加式历史。**

本文覆盖：

- core 对象分层
- 关键 record 的存在目的
- 当前位对象与追加式对象的区别
- 最小引用关系
- 写入语义与更新边界

本文不覆盖：

- 完整 JSON Schema
- 具体文件路径模板
- 具体代码结构

## 2. 为什么需要这份文档

前面的文档已经冻结了：

- 总架构
- core 子系统边界
- session lifecycle
- governance 语义
- artifact / evidence 文件表面
- shared contract shape

但 `Garage Core` 内部仍存在一个容易漂移的空白：

- `SessionIntent`
- `SessionState`
- `SessionSnapshot`
- `ContextPointer`
- `HandoffRecord`
- `ArtifactIntent`
- `ArtifactDescriptor`
- `AuthorityMarker`
- `PolicySet`
- `GateDecision`
- `ExceptionRecord`
- `EvidenceRecord`
- `LineageLink`

如果这些对象不先冻结，后续实现会在：

- session persistence
- evidence logging
- lineage linking
- routing
- governance enforcement

上各自长出不同 shape。

## 3. Core runtime objects 的分层

phase 1 建议把 core runtime objects 分成 4 层：

| 层级 | 作用 | 对象 |
| --- | --- | --- |
| `Intent` 层 | 描述“想做什么” | `SessionIntent`、`ArtifactIntent` |
| `Current State` 层 | 描述“现在是什么状态” | `SessionState`、`ContextPointer`、`AuthorityMarker` |
| `Snapshot / Record` 层 | 描述“某一时刻发生过什么” | `SessionSnapshot`、`HandoffRecord`、`GateDecision`、`ExceptionRecord`、`EvidenceRecord` |
| `Descriptor / Link` 层 | 描述“对象是谁、彼此如何连起来” | `ArtifactDescriptor`、`LineageLink`、`PolicySet` |

这个分层的重点是：

- 意图对象不是状态对象
- 当前位对象不是历史对象
- 历史记录默认追加，不静默覆盖

## 4. `SessionIntent`

### 4.1 存在目的

描述一次 session 打算做什么，以及它从哪里进入。

### 4.2 最小语义

- 谁发起
- 要解决什么类型的问题
- 入口 `pack / node`
- 当前目标与边界

### 4.3 写入语义

- 创建 session 时写入
- 它可以被澄清，但不应在历史上被无痕重写
- 若目标发生本质变化，应形成新的 snapshot 或新 session，而不是把 intent 偷偷改义

## 5. `SessionState`

### 5.1 存在目的

表达当前 session 的当前权威状态。

### 5.2 最小语义

- 当前 `sessionStatus`
- 当前 `pack`
- 当前 `node`
- 当前主线摘要
- 当前未决 gate

### 5.3 写入语义

- 它是“当前位”对象
- 任一时刻只有一个当前版本
- 每次关键状态转移都应同时生成新的相关 record

## 6. `SessionSnapshot`

### 6.1 存在目的

保留某一时刻的 session 快照，供 resume、复查和 closeout 使用。

### 6.2 最小语义

- 对应哪个 session
- 截止到哪个时点
- 当时的主状态摘要
- 当时的重要指针

### 6.3 写入语义

- `pause`
- `review-hold`
- `handoff`
- `closeout`
- `archive-ready`

这类节点都应允许产出 snapshot。

`SessionSnapshot` 是追加式对象，不替代 `SessionState`。

## 7. `ContextPointer`

### 7.1 存在目的

表达当前 session 在 phase 1 下真正依赖哪些上下文入口，而不是把上下文混成一个大桶。

### 7.2 最小语义

- 当前主要 artifact refs
- 当前关键 evidence refs
- 当前 active node refs
- 当前 handoff 或 review 相关 refs

### 7.3 写入语义

- 它跟随 `SessionState` 更新
- 只保留当前恢复真正需要的指针
- 不负责长期沉淀

## 8. `HandoffRecord`

### 8.1 存在目的

记录一次节点间或 pack 间交接。

### 8.2 最小语义

- 源侧是谁
- 目标是谁
- 交接范围
- 交接时附带的 artifact / evidence refs
- acceptance 或回流结论

### 8.3 写入语义

- handoff 是 record，而不是只改一个状态字段
- 每次 handoff 都应追加新记录
- record 必须能回指到相关 session snapshot 与 bridge evidence

## 9. `ArtifactIntent`

### 9.1 存在目的

表达某个节点准备产出或更新哪类 artifact。

### 9.2 最小语义

- 目标 artifact role
- 产出目的
- 来源 node
- 与哪个 session 相关

### 9.3 写入语义

- 它是写入前的意图对象
- 主要用于 routing、governance 和 authority 决策前置对齐
- 不等于 artifact 本体

## 10. `ArtifactDescriptor` 与 `AuthorityMarker`

### 10.1 `ArtifactDescriptor`

描述某个 artifact 是谁。

最小语义：

- 稳定 id
- artifact role
- pack 归属
- 格式与主要 locator

### 10.2 `AuthorityMarker`

描述某个 artifact 当前是否处于当前权威位。

最小语义：

- 当前是否 authoritative
- 被谁 supersede
- 是否已 archive

### 10.3 写入语义

- `ArtifactDescriptor` 是对象身份面，通常稳定
- `AuthorityMarker` 是当前位判断面，可随版本推进变化
- 二者分离，是为了避免把“对象是谁”和“现在谁有效”写成同一个字段桶

## 11. `PolicySet`、`GateDecision` 与 `ExceptionRecord`

### 11.1 `PolicySet`

描述当前动作依赖的治理规则集合。

最小语义：

- 规则来源层级
- 适用范围
- 当前动作引用了哪些规则

### 11.2 `GateDecision`

记录某次 gate 的结果。

最小语义：

- 对哪个动作判断
- verdict 是什么
- 缺什么
- 为什么

### 11.3 `ExceptionRecord`

记录某次显式豁免。

最小语义：

- 豁免了什么
- 为什么豁免
- 谁批准
- 何时失效

### 11.4 写入语义

- `PolicySet` 可被复用引用
- `GateDecision` 与 `ExceptionRecord` 都应追加式记录
- 不能只在当前状态里写一句“已放行”而没有 record

## 12. `EvidenceRecord` 与 `LineageLink`

### 12.1 `EvidenceRecord`

表达一条正式 evidence 的 record 形态。

最小语义：

- evidence 类型
- 关联 session / node / artifacts
- outcome 或 verdict
- 来源指针

### 12.2 `LineageLink`

表达两个对象之间的稳定关系。

最小语义：

- link type
- source ref
- target ref

### 12.3 写入语义

- `EvidenceRecord` 默认追加
- `LineageLink` 可视为轻量关系对象或 sidecar 关系声明
- 任何关键 closeout、approval、supersede、archive 都应能通过 lineage 被追回

## 13. 当前位对象与追加式对象

phase 1 建议明确区分：

### 13.1 当前位对象

- `SessionState`
- `ContextPointer`
- `AuthorityMarker`

这类对象回答的是：

- 现在什么有效

### 13.2 追加式对象

- `SessionSnapshot`
- `HandoffRecord`
- `GateDecision`
- `ExceptionRecord`
- `EvidenceRecord`
- `LineageLink`

这类对象回答的是：

- 发生过什么

这种区分很重要，因为 phase 1 最容易犯的错误之一，就是把“当前状态”和“历史记录”混写成一个文件。

## 14. 最小引用关系

phase 1 建议固定下面这组最小引用关系：

- `SessionState -> SessionIntent`
- `SessionState -> ContextPointer`
- `SessionSnapshot -> SessionState`
- `HandoffRecord -> SessionSnapshot`
- `ArtifactDescriptor -> ArtifactIntent`
- `AuthorityMarker -> ArtifactDescriptor`
- `GateDecision -> PolicySet`
- `EvidenceRecord -> related session / node / artifacts`
- `LineageLink -> source / target object`

这些关系的目标，是保证：

- resume 能恢复
- governance 能复查
- bridge 能追溯
- closeout 能归档

## 15. Phase 1 收敛范围

phase 1 只需要做到：

- 冻结这些 core runtime objects 的存在目的
- 冻结它们是当前位还是追加式
- 冻结它们的最小引用关系
- 冻结关键写入语义

phase 1 不要求：

- 写出完整 JSON Schema
- 做复杂索引服务
- 做数据库事务层
- 做分布式并发控制

## 16. 对后续开发的意义

有了这篇文档，开发任务拆解时才可以稳定落到下面这些方向：

- `SessionState` 如何持久化
- `SessionSnapshot` 何时写
- `HandoffRecord` 怎样回指 bridge
- `GateDecision` 与 `ExceptionRecord` 怎样落盘
- `ArtifactDescriptor` 与 `AuthorityMarker` 怎样支撑当前权威位

也就是说，它把“platform semantics”真正推进成“core runtime record semantics”。

## 17. 遵循的设计原则

- Intent / state / record 分层：想做什么、现在是什么、发生过什么必须分开。
- 当前位与历史位分离：`current authority` 和 `append-only history` 不应混成一个对象。
- `Session` 与 `Evidence` 分离：运行时协调对象不能替代正式追溯记录。
- `Artifact identity` 与 `artifact authority` 分离：对象身份和当前有效性分别建模。
- Governance 留痕：`GateDecision`、`ExceptionRecord` 等治理动作必须形成显式 record。
- Lineage by default：关键对象之间默认保留可追溯关系。
- `Markdown-first` / `file-backed`：phase 1 的 record 语义优先服务可见文件面，而不是隐藏式服务状态。
- phase 1 克制：先冻结最小对象集合和写入语义，再扩展更复杂的数据层。
