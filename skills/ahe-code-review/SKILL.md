---
name: ahe-code-review
description: 适用于 test review 通过后评审代码质量、用户要求 code review 的场景。不适用于评审测试（→ ahe-test-review）、写/修代码（→ ahe-test-driven-dev）、阶段不清（→ ahe-workflow-router）。
---

# AHE Code Review

评审实现代码质量。判断正确性、设计一致性、状态/错误/安全、可读性和下游追溯就绪度。运行在 `ahe-test-review` 之后，决定是否可进入 `ahe-traceability-review`。

## Methodology

本 skill 融合以下已验证方法：

- **Fagan Code Inspection (adapted)**: 结构化检查正确性、设计一致性、状态安全、可读性四个维度，而非自由形式代码阅读。
- **Design Conformance Check**: 实现必须遵循已批准设计，偏离需有理由且可追溯——防止实现与设计漂移。
- **Defense-in-Depth Review**: 错误处理、状态转换、安全性逐层检查，确保不因"测试通过"掩盖实现隐患。
- **Separation of Author/Reviewer Roles**: 评审者不改代码，只产出具名 findings 和 verdict。

## When to Use

适用：test review 通过后评审代码、用户要求 code review。

不适用：评审测试 → `ahe-test-review`；写/修代码 → `ahe-test-driven-dev`；阶段不清 → `ahe-workflow-router`。

## Hard Gates

- code review 通过前不得进入 traceability review
- 输入工件不足不得开始
- reviewer 不改代码、不继续实现

## Workflow

### 1. 建立证据基线

读实现交接块、代码变更、test-review 记录、AGENTS.md coding 约定、规格/设计片段、task-progress.md。

### 2. 多维评分与挑战式审查

5 维度 0-10 评分：正确性、设计一致性、状态/错误/安全、可读性、下游追溯就绪度。任一关键维度 < 6 不得通过。

### 3. 正式 checklist 审查

3.1 **正确性**：实现是否真正完成了任务目标？逻辑是否有 off-by-one、边界遗漏？
3.2 **设计一致性**：实现是否遵循已批准设计？偏离是否有理由且可追溯？
3.3 **状态/错误/安全**：错误处理是否完备？状态转换是否安全？是否有安全隐患？
3.4 **可读性**：命名是否清晰？结构是否合理？是否有过早优化或死代码？
3.5 **下游就绪度**：代码是否足以让 traceability-review 做可信判断？实现交接块是否完整？

### 4. 形成 verdict

- `通过`：所有维度 >= 6，代码足以支持追溯评审 → `next_action_or_recommended_skill=ahe-traceability-review`，`needs_human_confirmation=false`
- `需修改`：findings 可 1-2 轮定向修订 → `next_action_or_recommended_skill=ahe-test-driven-dev`，`needs_human_confirmation=false`
- `阻塞`：核心逻辑错误/安全漏洞/findings 无法定向回修 → `next_action_or_recommended_skill=ahe-test-driven-dev`，`needs_human_confirmation=false`；若问题本质是 stage/route/profile/上游证据冲突 → `next_action_or_recommended_skill=ahe-workflow-router`，`reroute_via_router=true`

Findings 带 severity 和 USER-INPUT/LLM-FIXABLE 分类。给出代码风险和追溯评审提示。

### 5. 写 review 记录

保存到 `AGENTS.md` 声明的 review record 路径；若无项目覆写，默认使用 `docs/reviews/code-review-<task>.md`。若项目无专用格式，可使用当前 skill pack 的共享模板 `templates/review-record-template.md`。

回传结构化摘要时遵循当前 skill pack 中 `ahe-workflow-router/references/reviewer-return-contract.md`：`next_action_or_recommended_skill` 只写一个 canonical 值；workflow blocker 必须显式写 `reroute_via_router=true`。

## 和其他 Skill 的区别

| Skill | 区别 |
|-------|------|
| `ahe-test-review` | 评审测试设计与覆盖度；本 skill 评审实现代码质量 |
| `ahe-traceability-review` | 评审规格→设计→实现的可追溯性；本 skill 聚焦代码正确性与设计一致性 |
| `ahe-bug-patterns` | 基于缺陷模式做专项排查；本 skill 做多维代码质量评审 |
| `ahe-test-driven-dev` | 写/修代码；本 skill 只审不改 |

## Reference Guide

| 文件 | 用途 |
|------|------|
| `templates/review-record-template.md` | 当前 skill pack 共享的 review record 模板 |
| `ahe-workflow-router/references/reviewer-return-contract.md` | 当前 skill pack 共享的 reviewer 返回契约 |

## Red Flags

- 不读实现交接块就审代码
- "测试通过"等同于"代码正确"
- 忽略错误处理/安全风险
- 评审中改代码
- 返回多个候选下一步

## Verification

- [ ] review record 已落盘
- [ ] 给出明确结论、findings、code risks 和唯一下一步
- [ ] 结构化摘要含 record_path 和 next_action_or_recommended_skill
- [ ] workflow blocker 时已显式写明 reroute_via_router
