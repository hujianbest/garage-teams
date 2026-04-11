# T030: Garage Phase 1 Shared Contracts And Registry

- Task ID: `T030`
- 状态: 待执行
- 日期: 2026-04-11
- 定位: 把 `Garage` 在 phase 1 的 6 类 shared contracts、最小 schema shape、加载校验与 registry discovery 落成可执行平台骨架。
- 当前阶段: phase 1
- 关联设计文档:
  - `docs/features/F010-shared-contracts.md`
  - `docs/features/F020-shared-contract-schemas.md`
  - `docs/architecture/A120-garage-core-subsystems-architecture.md`
  - `docs/features/F110-reference-packs.md`

## 1. 任务目标

让 `Garage` 的 shared contract layer 从“文档里已经冻结”变成“实现里已经可注册、可校验、可加载、可索引”。

## 2. 输入设计文档

这一篇主要承接：

- 6 类 shared contracts 的语义边界
- phase 1 的最小 schema shape
- `Registry` 在平台中的角色

## 3. 本文范围

- `PackManifest`
- `RoleContract`
- `WorkflowNodeContract`
- `ArtifactContract`
- `EvidenceContract`
- `HostAdapterContract`
- contract 版本与兼容校验
- registry discovery 与索引

## 4. 非目标

- 不实现 pack 内部节点逻辑
- 不实现具体 host UI
- 不扩展第七个 `BridgeContract`

## 5. 交付物

- 6 类 contracts 的稳定定义
- 一组最小 schema validators
- pack discovery / loading / indexing 流程
- duplicate id、missing ref、version mismatch 的报错面

## 6. 实施任务拆解

### 6.1 先落 contract type definitions

- 将 6 类 contracts 分别定义清楚。
- 显式区分 required dimensions 与 optional dimensions。
- 先支持 phase 1 需要的最小 shape，不追求字段全集。

### 6.2 实现 schema 校验

- 校验 `contractVersion`
- 校验 required fields
- 校验 refs 的完整性
- 校验未识别扩展字段的兼容策略

### 6.3 落 registry discovery

- 明确 pack manifests 从哪里加载。
- 明确 role / node / artifact / evidence / host adapter 如何被注册。
- 明确 registry 的最小索引面，例如 `packId`、`roleId`、`nodeId`、`artifactRole`。

### 6.4 处理冲突与错误

- 同 id 冲突如何报错
- 缺 refs 如何阻断注册
- 版本不兼容如何阻断加载
- pack 层局部错误如何避免污染全局 registry

### 6.5 给后续 packs 留入口

- 提供 reference pack shells 可复用的 manifest / contract 加载入口。
- 提供 host adapter stubs 未来接入所需的最小 capability 壳。

## 7. 依赖与并行建议

- 依赖 `01`
- 可与 `02` 并行
- 是 `07`、`08`、`09`、`10` 的前置

## 8. 验收与验证

完成这篇任务后，应能验证：

- registry 能发现并加载 phase 1 pack definitions
- contract refs 可以被正确解析
- 错误 pack 不会静默进入 registry
- 后续 reference pack 有统一接入入口

## 9. 完成后进入哪一篇

- `docs/tasks/T040-garage-phase-1-session-lifecycle-and-governance.md`
- `docs/tasks/T050-garage-phase-1-artifact-routing-and-evidence-surface.md`
- `docs/tasks/T070-garage-phase-1-reference-pack-shells.md`
