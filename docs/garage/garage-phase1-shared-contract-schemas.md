# Garage Phase 1 Shared Contract Schemas

- 状态: 草稿
- 日期: 2026-04-11
- 定位: 在 `garage-shared-contracts.md` 已定义共享 contract 语义的前提下，冻结 phase 1 六类 contract 的 schema shape、版本边界、引用方式与兼容演进规则。
- 当前阶段: phase 1
- 关联文档:
  - `docs/garage/garage-shared-contracts.md`
  - `docs/garage/garage-core-subsystems-architecture.md`
  - `docs/garage/garage-phase1-reference-packs.md`
  - `docs/garage/garage-phase1-session-lifecycle-and-handoffs.md`
  - `docs/garage/garage-phase1-governance-model.md`
  - `docs/garage/garage-phase1-artifact-and-evidence-surface.md`

## 1. 文档目标与范围

这篇文档只回答一个问题：

**phase 1 里，`PackManifest`、`RoleContract`、`WorkflowNodeContract`、`ArtifactContract`、`EvidenceContract`、`HostAdapterContract` 的最小 shape 应如何冻结。**

本文覆盖：

- 必需维度
- 可选维度
- 版本化
- 最小 shape 示例
- 组合规则
- 向后兼容演进

本文不覆盖：

- 完整 JSON Schema
- 字段级验证器语法
- pack 内部 prompt / template 原文
- 运行时状态实现细节

## 2. 与语义文档的关系

`garage-shared-contracts.md` 负责定义：

- 为什么需要这些 contract
- 各自语义边界是什么

本文只负责定义：

- 这些 contract 在 phase 1 至少要长成什么样
- 消费者依赖哪些维度
- 哪些维度必须保持稳定

所有示例都只是“字段骨架”，不是可执行规范。

## 3. Phase 1 schema 冻结边界

phase 1 只冻结 6 类 contract：

- `PackManifest`
- `RoleContract`
- `WorkflowNodeContract`
- `ArtifactContract`
- `EvidenceContract`
- `HostAdapterContract`

phase 1 明确不新增第七个 `BridgeContract`。

冻结的是：

- 最小可互操作 shape

而不是：

- 未来所有字段全集

## 4. 通用 schema 约定

每类 contract 都建议按同一组维度去理解：

- `Identity`
- `Version`
- `Ownership`
- `Refs`
- `Lifecycle / Governance Hints`
- `Extension Slots`

### 4.1 必需维度

缺失后会导致：

- 无法注册
- 无法路由
- 无法协作
- 无法追溯

### 4.2 可选维度

缺失后仍能完成最小互操作，只影响：

- overlay
- hints
- 宿主特化
- 增强能力

### 4.3 引用约定

引用优先用稳定 `id / ref`，而不是内联展开完整对象。

### 4.4 可选扩展约定

未识别的可选维度在 phase 1 应默认可忽略，避免增量扩展变成 breaking change。

## 5. 版本化策略

建议区分三层版本：

### 5.1 文档级

- `phase1` 作为 schema profile

### 5.2 对象级

- 所有 contract 带 `contractVersion`
- 建议从 `v1alpha1` 起步

### 5.3 pack 级

- 只有 `PackManifest` 额外带 `packVersion`
- 用于表达 pack 发布节奏
- 不等于共享 contract 的兼容版本

### 5.4 兼容演进规则

兼容 minor 变更：

- 新增可选维度
- 追加 capability
- 追加 taxonomy 值
- 追加 refs

破坏 major 变更：

- 删除或重命名必需维度
- 改变既有字段语义
- 把可选维度升级成必需维度
- 改变既有 ref 的解释方式

phase 1 先坚持：

- 先弃用
- 后移除

## 6. `PackManifest`

### 6.1 存在目的

- 定义 pack 最小身份与接入面

### 6.2 必需维度

- `packId`
- `packVersion`
- `contractVersion`
- `entryNodeRefs`
- `roleRefs`
- `nodeRefs`
- `supportedArtifactRoles`

### 6.3 可选维度

- `policyRefs`
- `templateRefs`
- `bridgeRefs`
- `handoffTargets`
- `displayName`

### 6.4 最小 shape 示例

- `packId + packVersion + contractVersion + entryNodeRefs + roleRefs + nodeRefs + supportedArtifactRoles`

### 6.5 组合规则

- 它是装配入口
- 只聚合 refs
- 不内联角色逻辑、节点逻辑或 artifact 细节

## 7. `RoleContract`

### 7.1 存在目的

- 定义角色如何进入系统

### 7.2 必需维度

- `roleId`
- `packId`
- `contractVersion`
- `responsibility`
- `readableArtifactRoles`
- `writableArtifactRoles`
- `triggerableNodes`
- `handoffScope`

### 7.3 可选维度

- `policyRefs`
- `templateRefs`
- `profileHints`

### 7.4 最小 shape 示例

- `roleId + packId + contractVersion + responsibility + readableArtifactRoles + writableArtifactRoles + triggerableNodes + handoffScope`

### 7.5 组合规则

- 角色只声明协作边界
- 不承载 prompt、模型选择或复杂权限系统

## 8. `WorkflowNodeContract`

### 8.1 存在目的

- 定义节点协作边界

### 8.2 必需维度

- `nodeId`
- `packId`
- `contractVersion`
- `intent`
- `inputArtifactRoles`
- `outputArtifactRoles`
- `allowedTransitions`
- `humanConfirmationRequired`
- `parallelizable`

### 8.3 可选维度

- `evidenceRequirements`
- `policyRefs`
- `handoffHints`

### 8.4 最小 shape 示例

- `nodeId + packId + contractVersion + intent + inputArtifactRoles + outputArtifactRoles + allowedTransitions + humanConfirmationRequired + parallelizable`

### 8.5 组合规则

- 节点是协作 seam
- 连接角色、artifact 与 evidence
- 不承载执行引擎细节

## 9. `ArtifactContract`

### 9.1 存在目的

- 定义中立工件接口

### 9.2 必需维度

- `artifactRole`
- `contractVersion`
- `primaryFormat`
- `authorityRule` 或 `pathRule`
- `readWriteSemantics`

### 9.3 可选维度

- `sidecarConvention`
- `lifecycleHint`
- `bridgeHints`

### 9.4 最小 shape 示例

- `artifactRole + contractVersion + primaryFormat + authorityRule/pathRule + readWriteSemantics`

### 9.5 组合规则

- artifact 是中立事实面
- 供 manifest 声明、node 引用、evidence 追溯
- phase 1 不必在此冻结完整目录规范

## 10. `EvidenceContract`

### 10.1 存在目的

- 定义追溯记录接口

### 10.2 必需维度

- `evidenceType`
- `contractVersion`
- `sourcePointer`
- `relatedSession`
- `relatedNode`
- `relatedArtifacts`
- `outcome` 或 `verdict`
- `lineageLinks`

### 10.3 可选维度

- `archiveState`
- `approvalRef`
- `exceptionRefs`
- `reviewerRef`

### 10.4 最小 shape 示例

- `evidenceType + contractVersion + sourcePointer + relatedSession + relatedNode + relatedArtifacts + outcome/verdict + lineageLinks`

### 10.5 组合规则

- evidence 是追加式记录面
- 不替代 session
- 不替代 memory

## 11. `HostAdapterContract`

### 11.1 存在目的

- 定义宿主如何与 core 交互

### 11.2 必需维度

- `adapterId` 或 `hostKind`
- `contractVersion`
- `capabilities`
- `createSession`
- `resumeSession`
- `submitStep`

### 11.3 可选维度

- `requestApproval`
- `requestPublish`
- `requestCloseout`
- `interruptOrHandoffHooks`

### 11.4 最小 shape 示例

- `adapterId/hostKind + contractVersion + capabilities + createSession + resumeSession + submitStep`

### 11.5 组合规则

- adapter 只吸收宿主差异
- 不绕过 `Session`
- 不改写 artifact / evidence 语义

## 12. Contract 组合规则

phase 1 建议固定下面这组组合关系：

- `PackManifest` 是装配入口
- `RoleContract + WorkflowNodeContract` 构成协作骨架
- `ArtifactContract + EvidenceContract` 构成主事实面
- `HostAdapterContract` 构成外部接入面

`Bridge seam` 仍由：

- `WorkflowNodeContract`
- `ArtifactContract`
- `EvidenceContract`
- 必要时由 `PackManifest` 追加 `bridgeRefs / handoffTargets`

共同表达。

## 13. 向后兼容演进规则

phase 1 内：

- 旧的最小 shape 在后续 minor 版本里仍应可被读取和理解
- 新字段优先作为可选维度或 sidecar 扩展
- 已发布的稳定 id 不复用、不改义
- 新增 taxonomy 值前，应保证旧消费者可安全忽略

若必须引入 breaking change：

- 需要 major bump
- 需要弃用窗口
- 需要迁移说明

## 14. Phase 1 非目标

- 不写成完整 JSON Schema 文档
- 不冻结完整目录树、路径模板全集、宿主 UI 协议
- 不把 prompt、template、rule 正文塞进 contract shape
- 不提前做远程 registry、在线市场、重型资产系统或复杂权限模型

## 15. 遵循的设计原则

- 平台中立：core 只理解中立对象，不理解领域术语。
- `Contract-first`：先冻结边界和 shape，再讨论实现。
- 必需维度最小化：只冻结互操作所必需的维度。
- 可选维度可追加：扩展优先通过 optional refs、hints、capabilities 进入。
- 引用优先于内联：对象之间通过稳定 `id / ref` 组合，而不是互相嵌套复制。
- 组合优先于特例：`Bridge`、治理、handoff 都优先通过既有 contract 组合表达。
- `Markdown-first` / `file-backed`：面向人的主事实面保持可读、可落盘、可追溯。
- `Session` 与 `Evidence` 分离：运行时状态与追溯记录不可混桶。
- 宿主中立：宿主差异留在 adapter，不扩散进 core 和 pack 语义。
- phase 1 克制：先冻结小而稳的 schema 骨架，再扩展能力面。
