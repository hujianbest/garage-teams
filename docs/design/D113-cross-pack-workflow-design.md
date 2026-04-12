# D113: Cross-Pack Workflow Design

- Design ID: `D113`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 展开 reference packs 之间的 cross-pack workflow 设计。
- 关联文档:
  - `docs/design/D11-reference-pack-designs.md`
  - `docs/features/F154-cross-pack-bridge.md`
  - `docs/features/F123-handoff-and-review-boundaries.md`

## 1. 设计目标

- 说明不同 packs 如何显式 handoff
- 说明 acceptance / rework / lineage 如何在产品工作流中被看到

## 2. 典型 workflow

一条典型 cross-pack workflow 至少包括：

1. 上游 pack 产出 bridge-ready artifact
2. 下游 pack 接收 handoff
3. 下游给出 acceptance / rework verdict
4. 系统留下 lineage 与 evidence

## 3. 最小交接对象

- handoff payload
- bridge artifact
- acceptance verdict
- rework request
- lineage link

## 4. 产品可见性

对用户来说，这条 workflow 应该可见：

- 谁把东西交给了谁
- 交接的 scope 是什么
- 被接受了还是被退回
- 为什么被接受或退回

## 5. 和 team 内 handoff 的关系

- team 内 handoff 负责一般协作边界
- cross-pack workflow 负责 capability domain 之间的显式 bridge
- 两者都要显式，但 bridge 需要更强的 artifact/evidence/acceptance 约束

## 6. 非目标

- 不把 cross-pack workflow 退化成聊天延续
- 不让 bridge flow 成为新的核心运行时真相

## 7. 设计完成标准

- cross-pack workflow 的阶段、对象和 verdict 清楚
- acceptance / rework / lineage 可被产品层解释
- 下游任务分解不再需要猜 bridge workflow 的基本走向
