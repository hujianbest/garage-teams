# SDD 场景 03 模拟运行报告

## 场景信息

- 场景目录：`workflow-skills/sdd-eval-sample-pack/03-approved-plan-ready-implement/`
- 场景名称：任务计划已批准，可进入实现
- 用户 Prompt：

```text
继续这个项目。按照已经确认好的任务计划，先做当前该做的那一项，不要自己扩 scope。
```

## 本次检查方式

本次继续采用**规则级模拟检查**：

1. 读取场景 03 的前置工件
2. 对照 `sdd-workflow-starter` 的路由顺序逐项判断
3. 对照 `sdd-work-implement` 的执行规则、handoff 顺序和门禁判断是否连贯

## 前置工件判断

场景 03 中存在：

- approved requirement spec
- approved design doc
- approved task plan
- `workflow-state.json`

其中 `workflow-state.json` 明确给出：

- `phase: "implement"`
- `approved_artifacts.requirement_spec = true`
- `approved_artifacts.design_doc = true`
- `approved_artifacts.task_plan = true`
- `current_task = TASK-001`
- `next_skill = sdd-work-implement`

这意味着：

- 主链 requirements、design、tasks 三个上游阶段都已完成
- 当前存在唯一活动任务
- 当前最合理的下一阶段应是 implement

## 对 `sdd-workflow-starter` 的路由推导

将当前场景套入 starter 规则：

1. `hotfix-request.json` 不存在，不命中
2. `change-request.json` 不存在，不命中
3. 不满足“没有 approved requirement spec”
4. 不满足“没有 approved implementation design”
5. 不满足“没有 approved task plan”
6. 满足“there are unfinished planned tasks”

因此正确下游应为：

`sdd-work-implement`

## 对 `sdd-work-implement` 的进入适配性检查

`sdd-work-implement` 的关键前置条件与场景 03 一致：

- task plan 已通过 review
- 一次只做一个 active task
- 必须按 TDD 进行
- 完成后不能直接宣称 done，必须经过固定门禁链

其明确规定的顺序是：

```text
Implement -> test-review -> code-review -> regression-gate -> completion-gate
```

这与场景 03 的期望完全一致。

## 模拟结果

### 实际首个应命中 skill

`sdd-workflow-starter`

### 实际下游应命中 skill

`sdd-work-implement`

### 预期后续顺序

`sdd-work-implement -> sdd-test-review -> sdd-code-review -> sdd-regression-gate -> sdd-completion-gate`

## 结论

PASS

## 通过项

- `starter` 能在 spec、design、task plan 都 approved 的情况下继续往后推进
- `workflow-state.json` 中的 `phase` 和 `current_task` 与路由方向一致
- `work-implement` 明确约束了一次只处理一个 active task
- `work-implement` 之后的 review / gate 顺序是明确且固定的
- 不会在实现后直接跳到 finalize 或直接宣称完成

## 未发现的严重问题

本场景下，未发现以下严重问题：

- 已有 approved task plan 仍被错误送回 `sdd-work-tasks`
- 实现阶段没有 TDD 约束
- review / gate 顺序缺失
- 在没有 completion gate 的情况下允许任务结束

## 残余风险

场景 03 虽然通过，但仍有两个值得继续验证的点：

1. 目前 `work-implement` 更像“执行规范”，还没有更细的项目级任务状态模板；后续如果任务状态记录不统一，实际执行时可能会出现“active task 不明确”的问题。
2. 当前验证是规则级模拟，还没有对真实多轮对话中的 handoff 用语做一致性测试，例如实现阶段结束时是否真的会清楚地点名下一个 gate skill。

## 建议下一步

主链前三段模拟都通过后，下一轮最有价值的是：

1. 模拟场景 04：需求变更，验证 `sdd-work-increment`
2. 模拟场景 05：热修复，验证 `sdd-work-hotfix`

这样可以把主链与两条支线都跑一遍，确认这套 SDD skills 在最典型的 5 个场景下都能自洽工作。
