# T090: Garage Phase 1 Coding Pack

- Task ID: `T090`
- 状态: 待执行
- 日期: 2026-04-11
- 定位: 把 `Coding Pack` 作为 `Garage` 的下游 reference pack 落地，重点实现 intake、specify、design、tasking、implement、review、verify、closeout 这条构建主链。
- 当前阶段: phase 1
- 关联设计文档:
  - `docs/design/D120-garage-coding-pack-design.md`
  - `docs/features/F110-reference-packs.md`
  - `docs/features/F120-cross-pack-bridge.md`
  - `docs/features/F070-continuity-mapping-and-promotion.md`

## 1. 任务目标

把 `Coding Pack` 从设计文档变成可注册、可接受 bridge 输入、可实现 review / verification / closeout 主链的下游 pack。

## 2. 输入设计文档

这一篇主要承接：

- `Coding Pack` 的 mission、roles、nodes
- artifact taxonomy 与 evidence model
- bridge intake 规则
- closeout 语义
- continuity candidates 的来源约束

## 3. 本文范围

- intake to closeout node graph
- accepted bridge inputs
- artifact mappings
- evidence mappings
- governance overlay
- continuity candidate emission

## 4. 非目标

- 不实现 `Product Insights Pack`
- 不实现所有语言 / 框架支持
- 不把现有所有 `ahe-coding-skills` 一次性迁完

## 5. 交付物

- `Coding Pack` manifest
- 关键 roles / nodes definitions
- 下游 artifact family
- 下游 evidence family
- review / verification / closeout 主链

## 6. 实施任务拆解

### 6.1 先落 pack shell 填充

- 基于 `07` 的 shell，填写 `packId = coding`
- 明确 intake 与 closeout 所在节点
- 补齐 roleRefs、nodeRefs、artifact mappings

### 6.2 落构建主链节点

- `Intake`
- `Specify`
- `Design`
- `Tasking`
- `Implement`
- `Review`
- `Verify`
- `Closeout`

每个节点只需先冻结最小 intent、输入、输出与转移条件。

### 6.3 落下游 artifacts

- `spec`
- `design`
- `task-board`
- `implementation-delta`
- `review-record`
- `verification-record`
- `closeout-summary`

### 6.4 落下游 evidence 与治理

- 设计取舍记录
- review verdict
- verification result
- rework 原因
- closeout 判断依据
- pack-local governance overlay

### 6.5 接 continuity candidates

- 让长期工程偏好类候选留出 `memory` 候选口
- 让复用方法类候选留出 `skill` 候选口
- 默认仍先进入 `evidence`

## 7. 依赖与并行建议

- 依赖 `04`、`05`、`06`、`07`
- 可与 `08` 并行，但 `10` 需要两边都完成

## 8. 验收与验证

完成这篇任务后，应能验证：

- `Coding Pack` 能被 registry 发现和加载
- 下游主链能生成结构化 artifacts 与 evidence
- pack 能接受合格的 bridge 输入
- closeout 不再只是“代码写完了”，而是结构化完成语义

## 9. 完成后进入哪一篇

- `docs/tasks/T100-garage-cross-pack-bridge-and-walkthrough.md`
