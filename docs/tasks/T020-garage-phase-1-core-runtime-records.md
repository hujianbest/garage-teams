# T020: Garage Phase 1 Core Runtime Records

- Task ID: `T020`
- 状态: 待执行
- 日期: 2026-04-11
- 定位: 把 `Garage Core` 在 phase 1 的运行时对象、持久记录、当前位对象与追加式对象落成可实现的数据层和写入语义。
- 当前阶段: phase 1
- 关联设计文档:
  - `docs/architecture/A120-garage-core-subsystems-architecture.md`
  - `docs/features/F030-core-runtime-records.md`
  - `docs/features/F040-session-lifecycle-and-handoffs.md`
  - `docs/features/F050-governance-model.md`
  - `docs/features/F060-artifact-and-evidence-surface.md`

## 1. 任务目标

把 phase 1 中已经定义好的 core runtime objects 变成稳定的数据实现面，避免 session、handoff、gate、artifact authority 和 evidence 各自长出不同 shape。

## 2. 输入设计文档

这一篇主要承接：

- core runtime record 的对象集合
- 当前位与历史位分离原则
- session / governance / artifact / evidence 的最小引用关系

## 3. 本文范围

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

## 4. 非目标

- 不实现 6 类 shared contracts
- 不实现 pack-specific artifact roles
- 不实现 reference packs 的节点流

## 5. 交付物

- 一组稳定的 core runtime record 定义
- 当前位对象与追加式对象的写入约束
- 记录对象之间的最小引用关系
- 可用于后续 lifecycle、routing、governance 的读写接口

## 6. 实施任务拆解

### 6.1 按对象职责分组实现

- 将 runtime records 至少按 `session`、`artifact`、`governance`、`evidence` 四类职责分组。
- 保持 `intent / state / record / link` 分层，而不是做成一个巨大的万能状态对象。

### 6.2 先落当前位对象

- 实现 `SessionState`
- 实现 `ContextPointer`
- 实现 `AuthorityMarker`

这一步要先把“当前什么有效”说清楚。

### 6.3 再落追加式记录

- 实现 `SessionSnapshot`
- 实现 `HandoffRecord`
- 实现 `GateDecision`
- 实现 `ExceptionRecord`
- 实现 `EvidenceRecord`
- 实现 `LineageLink`

这一步要把“发生过什么”说清楚。

### 6.4 补齐对象身份与写入意图

- 实现 `SessionIntent`
- 实现 `ArtifactIntent`
- 实现 `ArtifactDescriptor`
- 实现 `PolicySet`

这一步要把“为什么写”和“写到哪个对象”说清楚。

### 6.5 冻结写入规则

- 什么情况下更新 `current slot`
- 什么情况下只能 append-only
- `supersede`、`archive`、`snapshot`、`handoff` 各自产生哪些 records
- 哪些记录必须回指 lineage

### 6.6 提供最小验证夹具

- 至少准备一个 session 创建示例
- 至少准备一个 handoff 示例
- 至少准备一个 gate decision 示例
- 至少准备一个 evidence lineage 示例

## 7. 依赖与并行建议

- 依赖 `01`
- 可与 `03` 并行
- 是 `04`、`05`、`06` 的前置

## 8. 验收与验证

完成这篇任务后，应能验证：

- 当前位对象不会和历史记录混写
- 关键 actions 会生成对应 records
- records 之间可以被追溯地链接起来
- 后续 session lifecycle、governance、artifact routing 都有统一落点

## 9. 完成后进入哪一篇

- `docs/tasks/T040-garage-phase-1-session-lifecycle-and-governance.md`
- `docs/tasks/T050-garage-phase-1-artifact-routing-and-evidence-surface.md`
- `docs/tasks/T060-garage-phase-1-continuity-and-promotion.md`
