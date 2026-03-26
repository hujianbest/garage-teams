# SDD 场景 02 模拟运行报告

## 场景信息

- 场景目录：`workflow-skills/sdd-eval-sample-pack/02-approved-spec-no-design/`
- 场景名称：规格已批准，但尚无设计
- 用户 Prompt：

```text
继续这个发布审批系统。需求规格已经确认过了，下一步该怎么走就怎么走。
```

## 本次检查方式

本次继续采用**规则级模拟检查**：

1. 读取场景 02 的前置工件
2. 对照 `sdd-workflow-starter` 的路由顺序逐项判断
3. 对照 `sdd-work-design` 的进入条件和 handoff 规则判断是否连贯

## 前置工件判断

场景 02 中存在：

- `docs/specs/2026-03-26-release-approval-srs.md`

并且该文档包含：

- `Status: Approved`

场景 02 中不存在：

- `change-request.json`
- `hotfix-request.json`
- 已批准 design doc
- 已批准 task plan

这意味着：

- 主链已经完成 requirements 并通过
- 当前最合理的下一阶段应是 design

## 对 `sdd-workflow-starter` 的路由推导

将当前场景套入 `sdd-workflow-starter` 的规则：

1. `hotfix-request.json` 不存在，不命中
2. `change-request.json` 不存在，不命中
3. 不满足“没有 approved requirement spec”，因为 spec 已存在且 `Status: Approved`
4. 满足“没有 approved implementation design”

因此正确下游应为：

`sdd-work-design`

## 对 `sdd-work-design` 的进入适配性检查

`sdd-work-design` 的前置条件是：

- requirement spec 存在
- spec 已通过 review 或被明确批准

当前场景完全满足。

同时它的行为约束也与场景目标一致：

- 不应回到 requirements
- 不应直接进入 task planning
- 不应直接进入 implementation
- 应先读取 approved spec
- 应提出 2 到 3 个方案并做取舍
- 产出 design doc 后 handoff 到 `sdd-design-review`

## 模拟结果

### 实际首个应命中 skill

`sdd-workflow-starter`

### 实际下游应命中 skill

`sdd-work-design`

### 预期 handoff

`sdd-work-design -> sdd-design-review`

## 结论

PASS

## 通过项

- `starter` 能利用 approved spec 识别当前不是 requirements 阶段
- 不会误路由回 `sdd-work-specify`
- 不会跳过设计直接进入 `sdd-work-tasks`
- `sdd-work-design` 的前置条件、目标和 handoff 与该场景完全对齐

## 未发现的严重问题

本场景下，未发现以下严重问题：

- 把 approved spec 当成 draft
- 跳过 design 直接拆 tasks
- 直接进入 implementation

## 残余风险

虽然场景 02 通过，但仍有一个值得后续补测的点：

- 当前 starter 主要根据工件存在性与 `Status: Approved` 判断阶段。如果未来团队使用别的批准标记方式，可能需要通过 SDD contract 显式映射 approval signal。

## 建议下一步

继续进行场景 03 的模拟检查，验证在 spec、design、task plan 都已批准时，主链是否能顺畅落到 `sdd-work-implement`，并且后续 review / gate 顺序是否清楚。
