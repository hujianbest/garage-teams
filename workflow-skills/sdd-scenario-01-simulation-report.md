# SDD 场景 01 模拟运行报告

## 场景信息

- 场景目录：`workflow-skills/sdd-eval-sample-pack/01-new-requirement/`
- 场景名称：全新需求进入规格阶段
- 用户 Prompt：

```text
我们准备做一个内部发布审批系统。第一期只支持员工提交发布申请、直属主管审批、审批通过后通知申请人。先帮我开始推进这件事，后面会按你说的流程走。
```

## 本次检查方式

本次不是运行外部自动化 harness，而是做一次**规则级模拟检查**：

1. 读取该场景的前置工件说明
2. 对照 `sdd-workflow-starter` 的路由规则逐项判断
3. 对照 `sdd-work-specify` 的进入条件与预期行为判断 handoff 是否合理

## 前置工件判断

根据场景 README，这个目录故意不提供：

- `workflow-state.json`
- `change-request.json`
- `hotfix-request.json`
- 已批准 spec
- 已批准 design
- 已批准 task plan

这意味着：

- 不存在 change / hotfix 支线信号
- 不存在任何已批准主链工件
- 当前应被判定为一个真正的 SDD 起点

## 对 `sdd-workflow-starter` 的路由推导

`sdd-workflow-starter` 当前规则是：

1. 有 `hotfix-request.json` -> `sdd-work-hotfix`
2. 有 `change-request.json` -> `sdd-work-increment`
3. 没有 approved requirement spec -> `sdd-work-specify`
4. 没有 approved design -> `sdd-work-design`
5. 没有 approved task plan -> `sdd-work-tasks`
6. 有未完成 task -> `sdd-work-implement`
7. 缺完成证据 -> `sdd-completion-gate`
8. 否则 -> `sdd-work-finalize`

将场景 01 套进去后：

- 第 1 条不命中
- 第 2 条不命中
- 第 3 条命中，因为没有 approved requirement spec

因此正确下游应为：

`sdd-work-specify`

## 对 `sdd-work-specify` 的进入适配性检查

`sdd-work-specify` 的预期是：

- 先探索上下文
- 先做澄清
- 不进入设计、任务、实现
- 产出 requirement spec draft
- handoff 到 `sdd-spec-review`

这与场景 01 完全匹配，因为用户给的是新需求起点，而不是：

- 继续设计
- 继续实现
- 做变更
- 做热修复

## 模拟结果

### 实际首个应命中 skill

`sdd-workflow-starter`

### 实际下游应命中 skill

`sdd-work-specify`

### 预期 handoff

`sdd-work-specify -> sdd-spec-review`

## 结论

PASS

## 通过项

- `starter` 的主入口路由对这个场景是清晰的
- 不会误入 `increment` 或 `hotfix`
- 不会直接落到 design / tasks / implement
- `work-specify` 的职责边界与该场景高度一致

## 未发现的严重问题

本场景下，未发现以下严重问题：

- 直接进入实现
- 绕过 requirements
- handoff 到错误阶段

## 仍值得关注的残余风险

虽然场景 01 本身通过，但有两个后续值得继续验证的点：

1. `starter` 当前更偏“工件存在性路由”，对“纯概念咨询”和“只做 review”的近似场景还需要靠后续演练验证是否会过触发。
2. 场景 01 的通过建立在“没有任何工件”的前提下；如果未来项目里遗留了一个 draft spec，但没有明确标记，可能会影响路由判断。

## 建议下一步

建议继续按顺序演练：

1. 场景 02：已批准规格，应该进入设计
2. 场景 03：已批准任务计划，应该进入实现

这样可以尽快验证主链从 `specify` 到 `implement` 的连续性。
