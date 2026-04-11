# T080: Garage Phase 1 Product Insights Pack

- Task ID: `T080`
- 状态: 待执行
- 日期: 2026-04-11
- 定位: 把 `Product Insights Pack` 作为 `Garage` 的上游 reference pack 落地，重点实现 framing、research、opportunity、concept、probe、bridge 这条主链。
- 当前阶段: phase 1
- 关联设计文档:
  - `docs/design/D110-garage-product-insights-pack-design.md`
  - `docs/features/F110-reference-packs.md`
  - `docs/features/F120-cross-pack-bridge.md`
  - `docs/features/F070-continuity-mapping-and-promotion.md`

## 1. 任务目标

把 `Product Insights Pack` 从设计文档变成可注册、可推进、可交接的上游 pack，让它能够稳定地产出：

- 上游判断工件
- 关键 evidence
- 面向 `Coding Pack` 的 bridge outputs

## 2. 输入设计文档

这一篇主要承接：

- `Product Insights Pack` 的 mission、roles、nodes
- artifact taxonomy 与 evidence model
- bridge-ready 输出要求
- continuity candidates 的来源约束

## 3. 本文范围

- roles 带宽
- node graph
- artifact mappings
- evidence mappings
- governance overlay
- continuity candidate emission

## 4. 非目标

- 不实现 `Coding Pack`
- 不打通最终 cross-pack acceptance
- 不展开 `writing` 或 `video`

## 5. 交付物

- `Product Insights Pack` manifest
- 关键 roles / nodes definitions
- 上游 artifact family
- 上游 evidence family
- bridge-ready 输出能力

## 6. 实施任务拆解

### 6.1 先落 pack shell 填充

- 基于 `07` 的 shell，填写 `packId = product-insights`
- 明确 entry nodes
- 补齐 roleRefs、nodeRefs、artifact mappings

### 6.2 落主链节点

- `Framing`
- `Research`
- `Opportunity`
- `Concept`
- `Probe`
- `Bridge`

每个节点只需先冻结最小 intent、输入、输出与转移条件。

### 6.3 落上游 artifacts

- `framing-brief`
- `insight-pack`
- `opportunity-map`
- `concept-brief`
- `probe-plan`
- `bridge-artifact`

### 6.4 落上游 evidence 与治理

- 来源记录
- 判断依据
- 假设与 probe 结果
- bridge-ready 检查点
- pack-local governance overlay

### 6.5 接 continuity candidates

- 让长期偏好类候选留出 `memory` 候选口
- 让研究套路类候选留出 `skill` 候选口
- 默认仍先进入 `evidence`

## 7. 依赖与并行建议

- 依赖 `04`、`05`、`06`、`07`
- 可与 `09` 并行，但 `10` 需要两边都完成

## 8. 验收与验证

完成这篇任务后，应能验证：

- `Product Insights Pack` 能被 registry 发现和加载
- 上游主链能生成结构化 artifacts 与 evidence
- pack 输出已经具备 bridge-ready 基础，但仍不依赖 `Coding Pack` 内部语义

## 9. 完成后进入哪一篇

- `docs/tasks/T100-garage-phase-1-cross-pack-bridge-and-phase-1-walkthrough.md`
