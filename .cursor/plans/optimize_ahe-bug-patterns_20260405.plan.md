# 优化 `ahe-bug-patterns` 方案

## 目标

把 `skills/ahe-bug-patterns/SKILL.md` 从“做一轮缺陷模式 checklist”的 skill，提升为“能稳定产出高质量缺陷模式发现、结构化风险记录和可被后续质量链直接消费的 handoff 工件”的 skill。

本次优化不改变 AHE 主链契约：

- 仍然由 `ahe-bug-patterns` 作为 full / standard 实现后的首个缺陷模式专项检查节点
- 仍然不替代 `ahe-test-review`、`ahe-code-review` 或 `ahe-regression-gate`
- 仍然在给出唯一下一步后由 `ahe-workflow-starter` 恢复后续编排

## 当前问题

当前 `ahe-bug-patterns` 已经能做一轮专项排查，但仍存在几个短板：

- 模式分类还偏松散，容易退化成“泛泛风险列表”
- 没有强要求消费 `ahe-test-driven-dev` 的实现交接块，导致上游上下文可能断裂
- 对 `ahe-test-review` / `ahe-code-review` / `ahe-regression-gate` 的下游 handoff 还不够可执行
- 缺少“回归假设 / 如何证伪”的结构化输出
- 当前引用的 pattern catalog 模板路径不够明确，容易读错位置
- 没有明确说明 lightweight profile 默认跳过本节点

## 优化方向

### 1. 增加 pre-flight 输入要求

要求至少读取：

- 当前改动 diff / 触碰工件
- `ahe-test-driven-dev` 的实现交接块
- 当前相关的团队缺陷模式目录（如有）

为什么这么改：

- 缺陷模式排查不应脱离具体改动和上游已证明内容

主要参考：

- `skills/ahe-test-driven-dev/SKILL.md`
- `references/longtaskforagent-main/skills/long-task-quality/SKILL.md`

### 2. 引入结构化 pattern taxonomy

每个命中模式至少记录：

- Pattern ID / 名称
- 机制
- 证据锚点
- 严重级别
- 是否是重复缺陷 / 近似缺陷 / 新风险
- 置信度

为什么这么改：

- 这能避免输出退化成“想到什么写什么”的 checklist

主要参考：

- `references/everything-claude-code-main/skills/quality-nonconformance/SKILL.md`
- `references/everything-claude-code-main/skills/click-path-audit/SKILL.md`

### 3. 增加 AI-assisted blind spot 子清单

补强一些 AI 辅助开发常见风险，例如：

- 双路径不一致
- 层间传播不完整
- 只修主路径不修旁支

为什么这么改：

- 这类模式在 AI 辅助实现里很高频，值得在 bug-patterns 单独提醒

主要参考：

- `references/everything-claude-code-main/skills/ai-regression-testing/SKILL.md`

### 4. 增加“回归假设与证伪建议”

每个重要发现都要求说明：

- 可能在哪些相邻路径再次出现
- 建议补哪类测试 / 防护 / 观察点
- 哪个命令或哪类验证最能证伪这个担忧

为什么这么改：

- `ahe-bug-patterns` 不负责跑完整回归，但应把后续验证提示说清楚

主要参考：

- `references/everything-claude-code-main/skills/ai-regression-testing/SKILL.md`
- `references/everything-claude-code-main/skills/verification-loop/SKILL.md`

### 5. 强化与下游节点的边界

显式说明：

- `ahe-test-review` 负责一般测试质量与 fail-first 裁决
- `ahe-code-review` 负责更广泛的实现质量判断
- `ahe-regression-gate` 负责更广义的验证执行与 gate 结论

为什么这么改：

- 这样 bug-patterns 才不会变成“第二次 test review / code review”

主要参考：

- `skills/ahe-test-review/SKILL.md`
- `skills/ahe-code-review/SKILL.md`
- `skills/ahe-regression-gate/SKILL.md`

### 6. 修正 pattern catalog 路径并补充 profile 说明

明确：

- pattern catalog 模板使用 skill-local `references/bug-pattern-catalog-template.md`
- lightweight profile 默认跳过本节点，除非用户手动要求

为什么这么改：

- 当前路径歧义会直接影响可用性
- profile 说明能减少误以为所有主链都必须经过本节点

主要参考：

- `skills/ahe-workflow-starter/SKILL.md`
- `skills/ahe-bug-patterns/SKILL.md`

## 明确不做的事

- 不把 `ahe-bug-patterns` 写成通用代码评审
- 不把它写成完整 regression gate
- 不在本节点重跑整个 TDD 或完整验证套件
- 不改动其它质量节点的职责边界

## 计划中的实际改动

会对 `skills/ahe-bug-patterns/SKILL.md` 做一轮聚焦增强，预计包括：

- 增加 pre-flight 输入和上游交接块消费
- 引入结构化缺陷模式 taxonomy
- 补强 AI-assisted blind spot 子清单
- 增加回归假设 / 证伪建议
- 强化与 test-review / code-review / regression-gate 的边界
- 修正 catalog 路径并补充 profile 说明

## 预期效果

优化后的 `ahe-bug-patterns` 应该具备这些特征：

- 不只是列风险，而是产出结构化 defect-pattern findings
- 更容易被 `ahe-test-review`、`ahe-code-review`、`ahe-regression-gate` 继续消费
- 更少出现路径歧义、profile 误用和重复评审
