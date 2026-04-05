# 优化 `ahe-test-review` 方案

## 目标

把 `skills/ahe-test-review/SKILL.md` 从“能检查测试是否有价值”的 skill，提升为“能稳定判断 fail-first 是否有效、测试是否足以支撑信任、以及其结论能否安全交给 `ahe-code-review` 和后续 gate 的高质量测试评审 skill”。

本次优化不改变 AHE 主链契约：

- 仍然由 `ahe-test-review` 负责测试质量判断，而不是替代 `ahe-code-review` / `ahe-regression-gate`
- 仍然在 `ahe-bug-patterns` 之后、`ahe-code-review` 之前使用（full / standard）
- 仍然通过 `通过 | 需修改 | 阻塞` 给出唯一下一步

## 当前问题

当前 `ahe-test-review` 已经覆盖 fail-first、行为价值和测试质量风险，但还存在几个高价值短板：

- 缺少明确消费 `ahe-test-driven-dev` 实现交接块和 `ahe-bug-patterns` 记录的要求
- fail-first 仍偏短 checklist，没有把“什么算有效 RED / GREEN”说透
- 对 adequacy、flake、mock 边界、AI-assisted blind spots 的判断还不够系统
- 输出还不够像可继续交接的 review artifact
- `Next Action` 仍偏自然语言，不够贴合 canonical `ahe-*` handoff
- 没有明确说明 lightweight profile 下本节点默认被跳过

## 优化方向

### 1. 增加角色定位与边界

明确：

- 本 skill 负责测试质量、fail-first 和测试 adequacy 判断
- 不替代 `ahe-code-review`
- 不替代 `ahe-regression-gate`

为什么这么改：

- 高质量 test-review 的关键是边界清晰，否则很容易和相邻 gate 混线

主要参考：

- `skills/ahe-code-review/SKILL.md`
- `skills/ahe-regression-gate/SKILL.md`

### 2. 增加 pre-flight 输入

要求至少读取：

- `ahe-test-driven-dev` 的实现交接块
- `ahe-bug-patterns` 记录（如当前链路要求）
- 当前 profile
- 当前任务对应的测试改动与目标行为

为什么这么改：

- test-review 不应脱离上游 TDD 与 defect findings 独立飘着做判断

主要参考：

- `skills/ahe-test-driven-dev/SKILL.md`
- `skills/ahe-bug-patterns/SKILL.md`

### 3. 把 fail-first 升级成 valid RED / GREEN rubric

明确：

- RED 必须真正执行过
- 失败要能准确代表缺失行为
- GREEN 要有当前会话的新鲜通过证据
- 必要时补充“没有 fix 时应继续失败”的证伪思路

为什么这么改：

- 这能让 test-review 真正判断测试是否可信，而不是只看“有没有 red 的痕迹”

主要参考：

- `references/everything-claude-code-main/skills/tdd-workflow/SKILL.md`
- `references/superpowers-main/skills/test-driven-development/SKILL.md`
- `references/superpowers-main/skills/verification-before-completion/SKILL.md`

### 4. 增加 adequacy / AI blind spot 检查

补强如下维度：

- 断言强度
- mock 边界
- flake / 不稳定性
- 双路径 / 多层传播不一致
- 测试是否真正编码了 `ahe-bug-patterns` 中命中的风险

为什么这么改：

- 这是 AI 辅助实现里最容易漏掉的测试弱点之一

主要参考：

- `references/everything-claude-code-main/skills/ai-regression-testing/SKILL.md`
- `skills/ahe-bug-patterns/SKILL.md`

### 5. 升级输出为可继续交接的 review artifact

要求至少显式说明：

- 上游已消费证据
- 测试 ↔ 行为 / 验收映射
- 测试质量缺口
- 证伪建议或补强建议
- 给 `ahe-code-review` 的简短提示

为什么这么改：

- 这样 test-review 的结果才不只是 verdict，而是后续链路可消费的输入

主要参考：

- `references/everything-claude-code-main/skills/verification-loop/SKILL.md`
- `references/longtaskforagent-main/skills/long-task-quality/SKILL.md`

### 6. 收紧 canonical handoff

要求 `Next Action Or Recommended Skill` 优先写：

- `ahe-code-review`
- `ahe-test-driven-dev`

为什么这么改：

- starter 和其它 AHE 节点都已经在收紧 canonical `ahe-*` handoff

主要参考：

- `skills/ahe-workflow-starter/SKILL.md`

### 7. 补充 profile 说明

明确：

- full / standard 主链默认包含 test-review
- lightweight 默认不经过本节点；若手动调用，应视为补充性评审

为什么这么改：

- 这能减少“lightweight 为什么没有 test-review 记录”的误解

主要参考：

- `skills/ahe-workflow-starter/SKILL.md`

## 明确不做的事

- 不把 `ahe-test-review` 写成第二个 regression gate
- 不把它写成通用 code review
- 不引入与 project policy 冲突的统一 coverage 门槛
- 不改动其它质量节点职责

## 计划中的实际改动

会对 `skills/ahe-test-review/SKILL.md` 做一轮聚焦增强，预计包括：

- 增加角色边界和 pre-flight 输入
- 升级 fail-first 为 valid RED / GREEN rubric
- 增加 adequacy / AI blind spot 检查
- 输出升级为可继续交接的 review artifact
- 收紧 canonical handoff
- 增加 profile 说明

## 预期效果

优化后的 `ahe-test-review` 应该具备这些特征：

- 更像测试质量 gate，而不是浅层 checklist
- 更容易与 `ahe-test-driven-dev`、`ahe-bug-patterns`、`ahe-code-review` 串成一致链路
- 更少出现“测试存在，但并不足以让人信任”的漏判
