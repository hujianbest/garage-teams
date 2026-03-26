# SDD 场景 05 模拟运行报告

## 场景信息

- 场景目录：`workflow-skills/sdd-eval-sample-pack/05-hotfix/`
- 场景名称：紧急热修复进入 hotfix 支线
- 用户 Prompt：

```text
线上有个紧急问题：审批通过以后没发通知，这个今天必须修。你按热修复流程来，但不要省略验证。
```

## 本次检查方式

本次继续采用**规则级模拟检查**：

1. 读取场景 05 的前置工件
2. 对照 `sdd-workflow-starter` 的路由顺序逐项判断
3. 对照 `sdd-work-hotfix` 的进入条件、复现要求和后续 gate 顺序判断是否连贯

## 前置工件判断

场景 05 中存在：

- approved requirement spec
- approved design doc
- approved task plan
- `hotfix-request.json`

其中 `hotfix-request.json` 明确给出：

- `severity = critical`
- `summary = 审批通过后没有发送通知`
- `expected_behavior = 审批通过立即通知申请人`
- `actual_behavior = 审批通过成功，但没有通知消息`
- `known_reproduction` 已提供 4 步复现线索

这意味着：

- 当前不是普通实现继续，也不是需求变更
- 这是一个高优先级缺陷修复场景
- 路由应优先落到 hotfix 支线

## 对 `sdd-workflow-starter` 的路由推导

starter 的规则顺序是：

1. `hotfix-request.json` 存在 -> `sdd-work-hotfix`
2. `change-request.json` 存在 -> `sdd-work-increment`
3. 之后才判断 spec / design / tasks / implement

当前场景中：

- 有 `hotfix-request.json`

因此应直接优先命中：

`sdd-work-hotfix`

而不应继续主链，也不应误入 `sdd-work-increment`。

## 对 `sdd-work-hotfix` 的进入适配性检查

`sdd-work-hotfix` 的前置条件与场景 05 完全匹配：

- `hotfix-request.json` 存在
- 用户明确提出 urgent fix

其核心纪律与该场景的期望一致：

- 先复现问题
- 不允许凭直觉直接 patch
- 做最小安全修复
- 修复后仍需经过 review 和 gates

其后续顺序定义为：

1. 先验证复现已通过
2. `sdd-test-review`（若测试变更）
3. `sdd-code-review`
4. `sdd-regression-gate`
5. `sdd-completion-gate`

这说明热修复并没有因为“紧急”而逃逸出 SDD 的质量约束。

## 模拟结果

### 实际首个应命中 skill

`sdd-workflow-starter`

### 实际下游应命中 skill

`sdd-work-hotfix`

### 预期后续顺序

`sdd-work-hotfix -> sdd-code-review / sdd-regression-gate / sdd-completion-gate`

如果修复过程补充了自动化测试，则还应经过：

`sdd-test-review`

## 结论

PASS

## 通过项

- `starter` 对 `hotfix-request.json` 的优先级高于其它分支判断
- 不会误把该场景送进普通实现或需求变更分支
- `sdd-work-hotfix` 强制要求先复现再修复
- 热修复不会绕过 regression 和 completion gates
- “紧急”没有被当作跳过纪律的理由

## 未发现的严重问题

本场景下，未发现以下严重问题：

- 不复现直接修
- 直接进入 `sdd-work-implement`
- 用 urgency 绕过 completion gate

## 残余风险

有一个后续值得继续验证的点：

- `sdd-work-hotfix` 当前输出格式里的 `Next Step` 列举的是多个可能下游，但真实多轮对话中还需要进一步观察：模型是否会稳定地按“先 code-review，再 regression-gate，再 completion-gate”的顺序表达，而不是只挑其中一个就停下。

## 建议下一步

到这里，5 个核心场景已经都完成了规则级模拟。下一轮最有价值的工作不再是继续加场景，而是：

1. 做一次真实手工演练，观察模型实际是否会按这些 rules 行动
2. 或者为 `sdd-work-increment` / `sdd-work-hotfix` 再各补一组 evals，覆盖更细的分支判断
