# T060: Garage Phase 1 Continuity And Promotion

- Task ID: `T060`
- 状态: 待执行
- 日期: 2026-04-11
- 定位: 把 phase 1 中 `memory`、`session`、`skill`、`evidence` 的分层、候选来源、promotion 规则与治理检查点落成可执行的 continuity 骨架。
- 当前阶段: phase 1
- 关联设计文档:
  - `docs/architecture/A130-garage-continuity-memory-skill-architecture.md`
  - `docs/features/F070-continuity-mapping-and-promotion.md`
  - `docs/features/F050-governance-model.md`
  - `docs/features/F060-artifact-and-evidence-surface.md`

## 1. 任务目标

让 `Garage` 在 phase 1 中具备最小 continuity 能力：

- 当前工作留在 `session`
- 关键记录留在 `evidence`
- 少量长期事实进入 `memory`
- 少量稳定方法进入 `skill`

并且整个 promotion 过程默认保守、可追溯、可被治理。

## 2. 输入设计文档

这一篇主要承接：

- continuity 四层分离
- `Product Insights Pack` 与 `Coding Pack` 的候选来源
- promotion 的允许路径与禁止路径

## 3. 本文范围

- continuity candidate 的产生时机
- `Evidence -> Memory`
- `Evidence -> Skill`
- 禁止自动晋升路径
- promotion 的 review / approval checkpoints

## 4. 非目标

- 不做自动学习系统
- 不做向量检索层
- 不做自动 skill 生成流水线
- 不做大规模 personalization

## 5. 交付物

- 一套 continuity candidate 表达方式
- 一套 promotion 请求与决策流程
- 一套禁止自动晋升的 guardrails
- 两个 reference packs 的最小候选输出接口

## 6. 实施任务拆解

### 6.1 明确默认落点

- `Session` 默认只承接当前运行时上下文。
- `Evidence` 默认承接绝大多数候选结果。
- `Memory` 与 `Skill` 只接受显式、保守、可追溯的晋升。

### 6.2 定义 continuity candidate

- 明确哪些对象可以成为 candidate。
- 明确 candidate 至少要回指哪些 source artifacts 与 evidence。
- 明确 candidate 仍然不是已晋升对象。

### 6.3 落 promotion 流程

- `Evidence -> Memory` 的判断入口
- `Evidence -> Skill` 的判断入口
- review 与 approval 的挂点
- exception 在 continuity 上的最小作用边界

### 6.4 明确禁止路径

- 禁止 `Session -> Memory` 自动晋升
- 禁止 `Session -> Skill` 自动晋升
- 禁止无门槛 `Evidence -> Memory / Skill`
- 禁止把聊天记录、临时计划、一次性 workaround 直接固化

### 6.5 给 packs 预留发射口

- `Product Insights Pack` 输出其 continuity candidates
- `Coding Pack` 输出其 continuity candidates
- 两个 packs 使用同一套 promotion 语汇，而不是各自发明机制

## 7. 依赖与并行建议

- 依赖 `02`、`04`、`05`
- 是 `08`、`09`、`10` 的前置约束之一

## 8. 验收与验证

完成这篇任务后，应能验证：

- continuity 不会退化成一个大桶
- 候选对象与已晋升对象能被清晰区分
- 错误内容不会被静默固化成 `memory` 或 `skill`
- 两个 reference packs 可以共用同一套 promotion 语义

## 9. 完成后进入哪一篇

- `docs/tasks/T080-garage-phase-1-product-insights-pack.md`
- `docs/tasks/T090-garage-phase-1-coding-pack.md`
