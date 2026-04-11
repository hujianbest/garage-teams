# T070: Garage Phase 1 Reference Pack Shells

- Task ID: `T070`
- 状态: 待执行
- 日期: 2026-04-11
- 定位: 在真正实现两个 reference packs 之前，先搭出它们共享的 pack shell、注册入口、manifest 结构、contract 对接面和验证清单。
- 当前阶段: phase 1
- 关联设计文档:
  - `docs/features/F110-reference-packs.md`
  - `docs/features/F010-shared-contracts.md`
  - `docs/features/F020-shared-contract-schemas.md`
  - `docs/features/F060-artifact-and-evidence-surface.md`
  - `docs/features/F120-cross-pack-bridge.md`

## 1. 任务目标

先搭一层稳定的 pack 外壳，让 `Product Insights Pack` 和 `Coding Pack` 在进入各自领域实现之前，就已经共享：

- 目录形状
- manifest 入口
- role / node / artifact / evidence 的接入方式
- governance overlay 与 continuity hooks 的挂点

## 2. 输入设计文档

这一篇主要承接：

- reference packs 的共同形状
- shared contracts 的接入方式
- file-backed artifact / evidence surface

## 3. 本文范围

- pack 目录结构
- `PackManifest`
- pack-local roles / nodes / artifacts / evidence 的挂载位
- bridge hooks 的最小挂载位
- pack registration 流程
- phase 1 pack validation checklist

## 4. 非目标

- 不实现 `Product Insights Pack` 的具体节点
- 不实现 `Coding Pack` 的具体节点
- 不实现 cross-pack bridge 逻辑

## 5. 交付物

- 两个 reference packs 共用的 shell 约定
- pack manifest skeleton
- 最小 role / node / artifact / evidence 壳
- 最小 bridge-ready manifest hooks
- 一个 pack-level validation checklist

## 6. 实施任务拆解

### 6.1 冻结 pack 目录形状

- 明确 pack 根目录中至少包含什么。
- 明确 manifest、roles、nodes、artifacts、evidence、policies 的相对位置。
- 避免 pack 内部再长出第二套平台骨架。

### 6.2 落 `PackManifest` skeleton

- 冻结 `packId`、`packVersion`、`contractVersion`
- 明确 `entryNodeRefs`
- 明确 `roleRefs`、`nodeRefs`
- 明确 `supportedArtifactRoles`
- 预留 `bridgeRefs` 与 `handoffTargets` 这类 phase 1 bridge hooks

### 6.3 落 pack-local contract 挂点

- 给 roles 预留最小 contract 位置
- 给 nodes 预留最小 contract 位置
- 给 artifact / evidence mappings 预留位置
- 给 bridge-ready node 与 bridge artifact 预留最小挂点
- 给 governance overlay 与 continuity hooks 预留位置

### 6.4 接上 registry

- 让 pack shells 能被 discovery
- 让 shells 能通过 validation
- 让 pack-local ids 能进入 registry 索引

### 6.5 形成共同验收清单

- manifest 是否完整
- refs 是否闭合
- pack-specific 语义是否还留在 pack 内
- artifact / evidence surface 是否对齐平台语义
- bridge hooks 是否已被预留但尚未越权实现目标 pack 逻辑

## 7. 依赖与并行建议

- 依赖 `03`、`05`
- 可在 `06` 完成后继续加 continuity hooks
- 是 `08` 和 `09` 的直接前置

## 8. 验收与验证

完成这篇任务后，应能验证：

- 两个 reference packs 已有统一接入外壳
- pack-specific 细节还没有污染 core
- 后续只需往 shell 中填充 pack 自己的节点与治理层

## 9. 完成后进入哪一篇

- `docs/tasks/T080-garage-product-insights-pack.md`
- `docs/tasks/T090-garage-coding-pack.md`
