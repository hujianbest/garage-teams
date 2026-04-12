# D121: Governance Surface Design

- Design ID: `D121`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 展开 review、approval、archive 与治理表面的具体设计。
- 关联文档:
  - `docs/design/D12-governance-and-growth-operations-designs.md`
  - `docs/features/F134-governance-gates-approval-and-archive.md`

## 1. 设计目标

- 说明治理动作如何对人类和团队可见
- 说明治理表面如何与 evidence 和 workspace facts 绑定

## 2. 最小治理表面

治理表面至少应让用户看到：

- 当前哪些动作被允许
- 哪些动作被阻断
- 哪些动作需要 review
- 哪些动作需要 approval
- 哪些工作已进入 archive-ready / archived 状态

## 3. 主要交互对象

- gate verdict
- approval request
- review item
- archive state
- supporting evidence refs

## 4. 与 workspace/evidence 的关系

- 治理表面不能只显示抽象 verdict，还必须能回指相关 evidence
- 重要治理结果应能回到 workspace facts 中被检查
- archive 结果必须可见、可追溯

## 5. 人与团队的分工

- 人负责判断和审批
- 团队负责执行和提交材料
- 系统负责显式显示当前治理状态与阻断原因

## 6. 非目标

- 不把治理表面做成管理后台大全
- 不让治理逻辑只存在于 UI 说明中
- 不让 archive 退化成隐藏系统副作用

## 7. 设计完成标准

- review / approval / archive 的最小产品表面清楚
- 这些表面和 evidence / workspace facts 的关系清楚
- 下游 task 可以据此切出治理实现和 UI/CLI work
