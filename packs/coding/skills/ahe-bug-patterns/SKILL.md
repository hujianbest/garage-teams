---
name: ahe-bug-patterns
description: 适用于实现完成后、test review 前的缺陷模式专项排查，或用户要求 bug pattern 检查。不适用于写/修代码（→ ahe-test-driven-dev）、评审测试（→ ahe-test-review）、阶段不清（→ ahe-workflow-router）。
---

# AHE Bug Patterns

基于团队历史错误案例和通用缺陷模式对当前改动做专项排查。运行在 `ahe-test-driven-dev` 之后，决定是否可进入 `ahe-test-review`。

## Methodology

本 skill 融合以下已验证方法：

- **Defect Pattern Catalog (Beizer/Ostrand)**: 将历史缺陷分类为可复用的模式家族（边界/null、状态/时序、资源泄露、AI盲点），让团队从错误中系统性学习。
- **Checklist-Based Review (NASA/SEI)**: 基于模式目录的结构化排查，防止"想到了就查没想到就漏"的随机性。
- **Severity-Confidence Matrix**: 每条命中按 severity 和 confidence 双维度评估，区分"已确认风险"和"弱信号"，避免资源错配。

## When to Use

适用：实现完成后、test review 前的缺陷模式排查；用户要求 bug pattern 检查。

不适用：写/修代码 → `ahe-test-driven-dev`；评审测试 → `ahe-test-review`；阶段不清 → `ahe-workflow-router`。

## Hard Gates

- 排查必须基于当前代码变更，不是泛泛而谈
- 发现高风险模式必须在 findings 中记录
- reviewer 不改代码、不继续实现

## Workflow

### 1. 建立证据基线

读实现交接块、代码变更、参考 `references/bug-pattern-catalog-template.md` 中的模式家族、AGENTS.md、task-progress.md。

### 2. 选择适用的模式家族

根据当前改动类型选择要检查的家族：
- 历史重复缺陷
- 边界/null/默认值
- 状态/时序/重入/幂等
- 资源释放/异常恢复/配置读取
- AI 辅助盲点（双路径不一致、跨层传播、未同步 guard 分支）

### 3. 结构化记录命中

每条 hit 记录：Pattern ID、机制、证据锚点、severity（critical/important/minor）、可重复性、confidence（demonstrated/probable/weak-signal）。

### 4. 形成 verdict

- `通过`：未发现高风险模式，或已识别的模式已有保护 → `ahe-test-review`
- `需修改`：发现需修复的模式 → `ahe-test-driven-dev`
- `阻塞`：根因不明确/需上游决策 → `ahe-test-driven-dev` 或 `ahe-workflow-router`

### 5. 写记录

保存到 `AGENTS.md` 声明的 verification 路径；若无项目覆写，默认使用 `docs/verification/bug-patterns-<task>.md`。回传结构化摘要。

## 和其他 Skill 的区别

| Skill | 区别 |
|-------|------|
| `ahe-test-driven-dev` | 写/修代码、TDD 实现；本 skill 只排查不改代码 |
| `ahe-test-review` | 评审测试设计与覆盖度；本 skill 检查代码中的缺陷模式 |
| `ahe-code-review` | 评审代码质量（正确性/设计一致性/安全）；本 skill 聚焦历史缺陷模式匹配 |

## Reference Guide

| 文件 | 用途 |
|------|------|
| `references/bug-pattern-catalog-template.md` | 缺陷模式目录模板（276 行） |

## Red Flags

- 不读代码变更就做模式检查
- "测试通过"就跳过模式排查
- 发现高风险模式但不记录
- 返回多个候选下一步

## Verification

- [ ] bug patterns record 已落盘
- [ ] 命中模式已结构化记录
- [ ] 给出明确结论和唯一下一步
