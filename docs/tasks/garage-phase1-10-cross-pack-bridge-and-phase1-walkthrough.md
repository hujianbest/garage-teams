# Garage Phase 1 10 Cross-Pack Bridge And Phase 1 Walkthrough

- 状态: 待执行
- 日期: 2026-04-11
- 定位: 在两个 reference packs 都具备最小实现形状后，打通 `Product Insights Pack -> Coding Pack` 的 bridge seam，并用一条端到端主链验证 phase 1 是否成立。
- 当前阶段: phase 1
- 关联设计文档:
  - `docs/garage/garage-phase1-cross-pack-bridge.md`
  - `docs/garage/garage-phase1-session-lifecycle-and-handoffs.md`
  - `docs/garage/garage-phase1-governance-model.md`
  - `docs/garage/garage-product-insights-pack-design.md`
  - `docs/garage/garage-coding-pack-design.md`

## 1. 任务目标

证明 `Garage` 的 phase 1 不是两套孤立 pack，而是一条真实可走通的主桥：

- 上游能交出 bridge artifact 与 bridge evidence
- 下游能做 acceptance verdict
- 不足时能显式回流
- 通过一条端到端 walkthrough 验证平台语义闭环

## 2. 输入设计文档

这一篇主要承接：

- `bridge seam` 的组合表达
- acceptance 结果语义
- rework 回流语义
- cross-pack lifecycle 与 governance checkpoints

## 3. 本文范围

- bridge payload 最小面
- acceptance verdict
- rework 回流
- cross-pack lineage
- 一条 phase 1 walkthrough

## 4. 非目标

- 不实现复杂多 pack 编排引擎
- 不扩展更多 pack 间桥接
- 不做 production-grade 自动化 orchestration

## 5. 交付物

- 一套最小 bridge artifact / evidence 组合
- 一套 `accepted / accepted-with-gaps / needs-clarification / rejected-return-upstream` 结果面
- 一条可追溯的上游到下游 walkthrough
- 一份 phase 1 defer list

## 6. 实施任务拆解

### 6.1 冻结 bridge payload

- 明确 bridge artifact 至少要包含什么。
- 明确 bridge evidence 至少要补充什么。
- 确保 bridge 仍通过现有 contracts 组合表达，而不是新增特例 contract。

### 6.2 落 acceptance verdict

- `accepted`
- `accepted-with-gaps`
- `needs-clarification`
- `rejected-return-upstream`

每种 verdict 都要明确：

- 写入哪些 records
- session 如何转移
- evidence 如何留痕

### 6.3 落 rework 回流

- 下游发现输入不足时，如何回流给上游
- 回流时必须带哪些缺口信息
- 如何避免“目标 pack 悄悄补锅”

### 6.4 打 cross-pack lineage

- bridge artifact 如何回指上游 artifacts
- coding intake 如何回指 bridge evidence
- closeout 如何保留整条链的 lineage

### 6.5 做 phase 1 walkthrough

- 选一条最小但真实的 `product-insights -> coding` 路径
- 走一遍上游主链、bridge、下游 intake、review、closeout
- 同时覆盖至少一条 acceptance 成功路径和一条回流路径

## 7. 依赖与并行建议

- 强依赖 `08` 和 `09`
- 同时依赖 `04`、`05`
- 是当前 phase 1 任务链的最后一篇

## 8. 验收与验证

完成这篇任务后，应能验证：

- bridge 不依赖隐式聊天上下文
- acceptance 是显式 verdict，而不是默认继续
- 回流是受控动作，不是异常补丁
- 一条端到端主链已经能证明 phase 1 的平台语义成立

## 9. 完成后进入哪一篇

- 进入实际开发执行与里程碑跟踪
- 或单独新增 `implementation sequencing / acceptance matrix` 文档
