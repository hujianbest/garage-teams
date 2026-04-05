# 优化 `ahe-regression-gate` 方案

## 目标

把 `skills/ahe-regression-gate/SKILL.md` 从“能跑一组回归检查”的 skill，提升为“能基于当前 profile、已批准链路和 fresh verification evidence 稳定判断更广义回归面是否健康，并把结论安全交给 `ahe-completion-gate` 或正确回流节点的高质量回归门禁 skill”。

本次优化不改变 AHE 主链契约：

- 仍然由 `ahe-regression-gate` 负责更广义的回归验证，而不是替代 `ahe-traceability-review` / `ahe-completion-gate`
- 仍然在 `ahe-traceability-review` 之后、`ahe-completion-gate` 之前使用（full / standard）
- lightweight 仍然保留 `ahe-test-driven-dev -> ahe-regression-gate -> ahe-completion-gate` 主链
- 仍然通过 `通过 | 需修改 | 阻塞` 给出唯一下一步

## 当前问题

当前 `ahe-regression-gate` 已经覆盖“最新运行、读取结果、判断回归面是否健康”，但还存在几个高价值短板：

- 缺少明确角色定位，与 `ahe-traceability-review`、`ahe-completion-gate` 的边界不够清楚
- 没有明确消费上游 traceability / implementation handoff / task-progress 状态的要求
- 没有 profile-aware 规则，难以区分 full / standard / lightweight 下“最小必要回归面”各是什么
- fresh evidence 规则还不够结构化，输出里缺少稳定的证据表
- canonical handoff 与 `Next Action Or Recommended Skill` 写回要求还不够明确
- 对 `阻塞` 的类型没有细分，容易把环境 / 编排问题和真实回归失败混在一起

## 优化方向

### 1. 增加角色定位与边界

明确：

- 本 skill 负责判断更广义回归面是否健康
- 不替代 `ahe-traceability-review` 的工件链路检查
- 不替代 `ahe-completion-gate` 的最终完成声明判断

为什么这么改：

- 回归 gate 的价值在于“这次改动有没有伤到周边”，不是重复追溯或重复宣布完成

主要参考：

- `skills/ahe-traceability-review/SKILL.md`
- `skills/ahe-completion-gate/SKILL.md`
- `references/superpowers-main/skills/verification-before-completion/SKILL.md`

### 2. 增加 pre-flight 输入与上游证据消费要求

要求至少读取：

- `AGENTS.md` 中声明的验证命令、分层验证入口和环境要求
- `ahe-test-driven-dev` 的实现交接块
- `ahe-traceability-review` 记录（full / standard）
- 当前 task / profile / 当前回归面假设
- `task-progress.md` 中的 Pending Reviews And Gates / 当前状态

为什么这么改：

- 高质量 regression gate 不能脱离上游 handoff 和 profile 语境单独跑命令

主要参考：

- `skills/ahe-test-driven-dev/SKILL.md`
- `skills/ahe-traceability-review/SKILL.md`
- `references/everything-claude-code-main/skills/verification-loop/SKILL.md`

### 3. 增加 profile-aware 回归面规则

明确：

- full / standard 下，回归面应覆盖 traceability 已确认的相邻模块、共享能力、构建 / 类型 / 集成入口
- lightweight 下，虽然链路更短，但不能把回归缩成“只跑新测试”

为什么这么改：

- profile 影响链路复杂度，但不应成为虚假通过的借口

主要参考：

- `skills/ahe-workflow-starter/SKILL.md`
- `skills/ahe-finalize/SKILL.md`

### 4. 把 fresh evidence 升级为结构化证据契约

要求至少显式记录：

- 命令
- 退出码
- 结果摘要
- 覆盖的回归面
- 该证据为何属于当前最新代码状态

为什么这么改：

- 这样 finalize 和 completion gate 才能直接消费 regression 记录，而不是依赖对话记忆

主要参考：

- `references/everything-claude-code-main/skills/verification-loop/SKILL.md`
- `references/longtaskforagent-main/skills/long-task-quality/SKILL.md`

### 5. 收紧 canonical handoff

要求 `Next Action Or Recommended Skill` 优先写：

- `ahe-completion-gate`
- `ahe-test-driven-dev`

为什么这么改：

- starter 已经用 canonical `ahe-*` handoff 恢复编排，regression gate 也应一致

主要参考：

- `skills/ahe-workflow-starter/SKILL.md`

### 6. 补充 blocker 分类与恢复规则

明确：

- 回归真实失败 -> `需修改`，回到 `ahe-test-driven-dev`
- 环境 / 工具链 / 命令入口损坏 -> `阻塞`
- 若 `阻塞` 实际暴露的是 profile / 编排 / 上游证据问题，应在记录里明确要求经 `ahe-workflow-starter` 重编排

为什么这么改：

- 这能减少“不是代码坏了，却被硬送回继续编码”的错路由

主要参考：

- `skills/ahe-code-review/SKILL.md`
- `skills/ahe-traceability-review/SKILL.md`

### 7. 升级输出为 gate artifact

要求输出里至少有：

- 已消费的上游结论
- 回归面定义
- fresh evidence 表
- 覆盖缺口 / remaining risk
- 明确不在本轮范围内

为什么这么改：

- 这样 regression gate 的记录才能成为 completion / finalize 的稳定输入

主要参考：

- `skills/ahe-finalize/SKILL.md`
- `references/everything-claude-code-main/skills/ai-regression-testing/SKILL.md`

## 明确不做的事

- 不把 `ahe-regression-gate` 写成第二个 completion gate
- 不把它写成第二个 traceability review
- 不要求所有项目都强制跑同一组固定命令
- 不改动其它质量节点职责

## 计划中的实际改动

会对 `skills/ahe-regression-gate/SKILL.md` 做一轮聚焦增强，预计包括：

- 增加角色边界和 pre-flight 输入
- 增加 profile-aware 回归面规则
- 升级 fresh evidence 为结构化证据契约
- 输出升级为 gate artifact
- 收紧 canonical handoff
- 补充 blocker 分类与恢复规则

## 预期效果

优化后的 `ahe-regression-gate` 应该具备这些特征：

- 更像正式 regression gate，而不是“跑几条命令看看”
- 更容易与 `ahe-traceability-review`、`ahe-completion-gate`、`ahe-finalize` 串成一致链路
- 更少出现“验证命令跑了，但无法证明当前回归面真的健康”的漏判
