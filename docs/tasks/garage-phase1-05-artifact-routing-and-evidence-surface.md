# Garage Phase 1 05 Artifact Routing And Evidence Surface

- 状态: 待执行
- 日期: 2026-04-11
- 定位: 把 `Garage` 在 phase 1 的 `Markdown-first`、`file-backed` artifact / evidence surface 落成稳定的目录、权威、sidecar、archive 与 lineage 机制。
- 当前阶段: phase 1
- 关联设计文档:
  - `docs/garage/garage-phase1-artifact-and-evidence-surface.md`
  - `docs/garage/garage-phase1-core-runtime-records.md`
  - `docs/garage/garage-shared-contracts.md`
  - `docs/garage/garage-phase1-governance-model.md`

## 1. 任务目标

让 `Garage` 的 artifact 与 evidence 不只是概念层对象，而是把 `04` 已冻结的 record 触发点真正 materialize 成稳定文件表面、权威规则和可追溯变更语义的主事实面。

## 2. 输入设计文档

这一篇主要承接：

- canonical directories
- authoritative slot 规则
- sidecar 职责边界
- archive 与 supersede 语义
- lineage linking 语义

## 3. 本文范围

- `artifacts/`
- `evidence/`
- `sessions/`
- `archives/`
- `.garage/`
- artifact routing
- evidence emission
- archive placement

## 4. 非目标

- 不实现富媒体资产平台
- 不实现数据库控制面
- 不实现复杂多人并发写入
- 不重新定义 session lifecycle 或 gate 语义

## 5. 交付物

- 一套稳定的 canonical directory 约定
- artifact descriptor 与 authority resolution 逻辑
- evidence 写入、materialization 与 lineage 链接逻辑
- supersede / archive 的最小流程

## 6. 实施任务拆解

### 6.1 冻结 canonical directories

- 明确 `artifacts / evidence / sessions / archives / .garage` 的角色。
- 明确哪些目录承载当前位，哪些目录承载历史位。
- 明确 pack 维度如何进入这些 surface，而不是自造顶层目录。

### 6.2 落 artifact routing

- 根据 `ArtifactContract` 与 routing 规则决定 artifact 去哪一面。
- 把 artifact identity 与 authority 分开处理。
- 避免把 session 当成 artifact 的长期宿主。

### 6.3 落 evidence emission

- 将 `04` 中定义的 review、approval、verification、bridge、closeout 等关键事件统一 materialize 到 evidence surface。
- 让 evidence 默认 append-only，而不是静默回写。
- 让 evidence 能回指 session、node 和 artifact。

### 6.4 落 sidecar 与 lineage

- 只在 sidecar 中承接机器可读 identity、status、route metadata。
- 避免把主语义写进 sidecar。
- 用 `LineageLink` 或等价关系声明把 `session -> artifact -> evidence -> archive` 串起来。

### 6.5 落 supersede / archive

- 明确当前版本被替换时如何更新 authoritative slot。
- 明确 archive 后如何保留可查历史。
- 明确 destructive overwrite 在 phase 1 中如何被禁止。

## 7. 依赖与并行建议

- 依赖 `02`、`03`、`04`
- `04` 先冻结语义与触发点，`05` 再冻结文件表面与写入细节
- 是 `06`、`07`、`08`、`09`、`10` 的前置

## 8. 验收与验证

完成这篇任务后，应能验证：

- artifact 与 evidence 不会混桶
- 当前版本与历史版本可以区分
- sidecar 不会替代主文档
- archive、supersede 与 lineage 都可追溯

## 9. 完成后进入哪一篇

- `docs/tasks/garage-phase1-06-continuity-and-promotion.md`
- `docs/tasks/garage-phase1-07-reference-pack-shells.md`
