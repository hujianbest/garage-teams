---
name: ahe-traceability-review
description: 评审规格→设计→任务→实现→测试/验证的证据链追溯完整性。防止"代码能跑但不再匹配已批准工件"。运行在 ahe-code-review 之后。
---

# AHE Traceability Review

评审证据链追溯完整性：spec→design→tasks→impl→test/verification→status。防止"代码能跑但不再匹配已批准工件"。运行在 `ahe-code-review` 之后，决定是否可进入 `ahe-regression-gate`。

## When to Use

适用：code review 通过后判断追溯完整性、用户要求追溯评审。

不适用：评审代码质量 → `ahe-code-review`；评审测试质量 → `ahe-test-review`；阶段不清 → `ahe-workflow-router`。

## Hard Gates

- traceability review 通过前不得进入 regression gate
- 输入工件不足不得开始评审
- reviewer 不修代码、不继续实现

## Workflow

### 1. 建立证据基线

读已批准规格、设计、任务计划、实现交接块、test-review/code-review 记录、AGENTS.md、task-progress.md。

### 2. 多维评分与挑战式审查

5 维度 0-10 评分：规格-设计追溯、设计-任务追溯、任务-实现追溯、实现-验证追溯、整体证据链闭合度。任一关键维度 < 6 不得通过。

### 3. 正式 checklist 审查

3.1 **规格-设计链**：设计决策是否可追溯到规格需求？
3.2 **设计-任务链**：任务是否覆盖设计中的关键决策？
3.3 **任务-实现链**：实现是否完成任务的完成条件？触碰工件是否一致？
3.4 **实现-验证链**：验证证据是否锚定到当前实现？RED/GREEN 是否可追溯？
3.5 **整体闭合**：有没有断链？approved 工件与当前代码是否仍然一致？

### 4. 形成 verdict

- `通过`：证据链完整，可进入 regression gate
- `需修改`：findings 可定向补齐追溯
- `阻塞`：核心链路断裂/工件与代码严重不一致

### 5. 写 review 记录

保存到 `AGENTS.md` 声明的 review record 路径；若无项目覆写，默认使用 `docs/reviews/traceability-review-<task>.md`。参考 `references/traceability-review-record-template.md`。

## Red Flags

- 不读上游工件就做追溯判断
- "代码能跑"等同于"追溯完整"
- 忽略规格/设计与代码的不一致
- 返回多个候选下一步

## Verification

- [ ] review record 已落盘
- [ ] 链接矩阵已建立
- [ ] 给出明确结论、findings 和唯一下一步
- [ ] 结论足以让父会话路由
