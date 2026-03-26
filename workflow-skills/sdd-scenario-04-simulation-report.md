# SDD 场景 04 模拟运行报告

## 场景信息

- 场景目录：`workflow-skills/sdd-eval-sample-pack/04-change-request/`
- 场景名称：需求变更进入 increment 支线
- 用户 Prompt：

```text
需求有变化。审批通过以后，除了通知申请人，还要自动抄送项目经理。你按正确流程处理，不要直接偷偷改代码。
```

## 本次检查方式

本次继续采用**规则级模拟检查**：

1. 读取场景 04 的前置工件
2. 对照 `sdd-workflow-starter` 的路由顺序逐项判断
3. 对照 `sdd-work-increment` 的进入条件、影响分析和回流规则判断是否连贯

## 前置工件判断

场景 04 中存在：

- approved requirement spec
- approved design doc
- approved task plan
- `change-request.json`

其中 `change-request.json` 明确给出：

- `change_type = new-requirement`
- `summary = 审批通过后，需要自动抄送项目经理`
- `affected_artifacts = requirement-spec, design-doc, task-plan`

这意味着：

- 当前不是普通实现继续
- 这是一次明确的范围追加
- 影响范围至少跨 spec、design、tasks 三类工件

## 对 `sdd-workflow-starter` 的路由推导

starter 的规则顺序是：

1. `hotfix-request.json` 存在 -> `sdd-work-hotfix`
2. `change-request.json` 存在 -> `sdd-work-increment`
3. 之后才判断 spec / design / tasks / implement

当前场景中：

- 没有 `hotfix-request.json`
- 有 `change-request.json`

因此应在主链判断之前就命中：

`sdd-work-increment`

## 对 `sdd-work-increment` 的进入适配性检查

`sdd-work-increment` 的前置条件与场景 04 完全匹配：

- `change-request.json` 存在
- 用户明确提出修改已批准需求

其预期行为也与场景目标一致：

- 先读取 change request
- 读取 approved spec / design / task plan
- 做 impact analysis
- 识别哪些工件受影响
- 路由回 `sdd-spec-review`、`sdd-design-review`、`sdd-tasks-review` 或实现阶段

特别重要的一点是，它明确禁止：

- 直接跳到实现
- 把需求变更当成纯任务变更
- 默认旧批准仍然有效

## 模拟结果

### 实际首个应命中 skill

`sdd-workflow-starter`

### 实际下游应命中 skill

`sdd-work-increment`

### 预期回流方向

由于当前变更明确影响 requirement spec，并且很可能影响 design 与 tasks，因此最保守、最合理的下一步应是：

- 先更新 requirement spec
- 再回到 `sdd-spec-review`

随后视设计与任务计划是否实质变化，再进入：

- `sdd-design-review`
- `sdd-tasks-review`

## 结论

PASS

## 通过项

- `starter` 对支线信号的优先级设计是正确的
- `change-request.json` 会在主链判断之前被识别
- 不会误把该场景送进 `sdd-work-implement`
- `sdd-work-increment` 明确要求 impact analysis 和工件同步
- 支线并没有绕过主链的 review discipline

## 未发现的严重问题

本场景下，未发现以下严重问题：

- 变更场景被当作普通继续开发
- 只改 task plan 不改 spec
- 变更后默认旧批准依然有效

## 残余风险

有一个后续值得继续观察的点：

- `sdd-work-increment` 已经定义了回流规则，但还没有更具体的“变更严重度分级模板”。未来如果需求变更很小，团队可能希望有更明确的判断标准来区分“只回 tasks-review”还是“必须回 spec-review”。

## 建议下一步

继续进行场景 05 的模拟检查，验证热修复支线是否也能像 increment 一样优先命中，并且不会以“紧急”为理由跳过复现、回归和 completion gate。
