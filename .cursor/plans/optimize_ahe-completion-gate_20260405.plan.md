# 优化 `ahe-completion-gate` 方案

## 目标

把 `skills/ahe-completion-gate/SKILL.md` 从“能用最新验证判断是否完成”的 skill，提升为“能基于当前 profile、已通过的 regression 记录和 fresh completion evidence，稳定判断当前任务是否允许宣告完成并进入 `ahe-finalize` 的高质量完成门禁 skill”。

本次优化不改变 AHE 主链契约：

- 仍然由 `ahe-completion-gate` 负责“是否允许宣告当前任务完成”的最终 gate
- 仍然在 `ahe-regression-gate` 之后、`ahe-finalize` 之前使用
- 仍然通过 `通过 | 需修改 | 阻塞` 给出唯一下一步

## 当前问题

当前 `ahe-completion-gate` 已经强调“没有最新证据就不能宣告完成”，但还存在几个高价值短板：

- 缺少清晰角色定位，与 `ahe-regression-gate` / `ahe-finalize` 的边界不够明确
- 没有明确消费 `ahe-regression-gate` 记录、profile-aware 上游 review 记录和 `ahe-test-driven-dev` handoff 的要求
- 没有 profile-aware 完成条，难以区分哪些证据是 mandatory，哪些在 lightweight 下可写 N/A
- fresh evidence 还停留在原则层面，没有形成结构化 evidence bundle
- 输出还不够像 downstream 可消费的 completion artifact
- blocker 类型没有细分，容易把环境问题、编排问题和实现问题混在一起

## 优化方向

### 1. 增加角色定位与边界

明确：

- 本 skill 负责判断“当前任务是否允许宣告完成”
- 不替代 `ahe-regression-gate` 的更广义回归判断
- 不替代 `ahe-finalize` 的文档 / 状态收尾

为什么这么改：

- completion gate 的价值在于“允许宣告完成”，不是重复跑回归或提前做 finalize

主要参考：

- `skills/ahe-regression-gate/SKILL.md`
- `skills/ahe-finalize/SKILL.md`
- `references/superpowers-main/skills/verification-before-completion/SKILL.md`

### 2. 增加 pre-flight 输入与上游证据消费要求

要求至少读取：

- `AGENTS.md` 中声明的验证入口、完成判断约定和状态字段
- `ahe-regression-gate` 记录
- `ahe-test-driven-dev` 的实现交接块
- `task-progress.md` 当前状态
- 当前 profile 下实际要求存在的 review / gate 记录

为什么这么改：

- completion gate 不应脱离 regression 结果和实现 handoff 单独宣告“完成”

主要参考：

- `skills/ahe-test-driven-dev/SKILL.md`
- `skills/ahe-regression-gate/SKILL.md`
- `skills/ahe-finalize/SKILL.md`

### 3. 增加 profile-aware 完成条

明确：

- full / standard 下哪些 review / gate 记录必须存在
- lightweight 下哪些记录可写 `N/A（按 profile 跳过）`

为什么这么改：

- 这样 completion gate 和 finalize 的证据矩阵才不会互相矛盾

主要参考：

- `skills/ahe-finalize/SKILL.md`
- `skills/ahe-workflow-starter/SKILL.md`

### 4. 把 fresh evidence 升级为结构化 completion evidence bundle

要求至少显式记录：

- 正在宣告的完成范围
- 命令
- 退出码
- 结果摘要
- 新鲜度锚点
- 这些证据为什么足以支撑“允许宣告完成”

为什么这么改：

- 这样 finalize 才能直接消费 completion gate 的记录，而不是重新猜“完成”到底指什么

主要参考：

- `skills/ahe-regression-gate/SKILL.md`
- `references/everything-claude-code-main/skills/verification-loop/SKILL.md`

### 5. 升级输出为 completion artifact

要求输出里至少有：

- 已消费的上游结论
- 完成宣告范围
- completion evidence bundle
- 覆盖 / 声明边界
- 明确不在本轮范围内

为什么这么改：

- 这样 completion gate 的输出才是一个可审计的 gate artifact，而不是一段口头判词

主要参考：

- `skills/ahe-finalize/SKILL.md`
- `references/longtaskforagent-main/skills/long-task-quality/SKILL.md`

### 6. 收紧 canonical handoff 与 blocker 分类

要求 `Next Action Or Recommended Skill` 优先写：

- `ahe-finalize`
- `ahe-test-driven-dev`
- `ahe-completion-gate`（仅环境 / 工具链阻塞重试）

为什么这么改：

- 这能让 starter 和 finalize 都能按显式状态恢复，而不是靠自然语言猜

主要参考：

- `skills/ahe-workflow-starter/SKILL.md`
- `skills/ahe-regression-gate/SKILL.md`

### 7. 补充 blocker / need-modify 恢复规则

明确：

- 证据不支持完成 -> `需修改`
- 环境 / 工具链损坏 -> `阻塞` 并重试 completion gate
- 上游编排 / profile / 证据链问题 -> 在记录里明确要求经 `ahe-workflow-starter` 重编排

为什么这么改：

- 这样能减少“不是实现没完成，却被一律送回继续编码”的错路由

主要参考：

- `skills/ahe-regression-gate/SKILL.md`
- `skills/ahe-code-review/SKILL.md`

## 明确不做的事

- 不把 `ahe-completion-gate` 写成第二个 regression gate
- 不把它写成第二个 finalize
- 不要求所有项目都重复跑同一组固定命令
- 不改动其它质量节点职责

## 计划中的实际改动

会对 `skills/ahe-completion-gate/SKILL.md` 做一轮聚焦增强，预计包括：

- 增加角色边界和 pre-flight 输入
- 增加 profile-aware 完成条
- 升级 fresh evidence 为 completion evidence bundle
- 输出升级为 completion artifact
- 收紧 canonical handoff
- 补充 blocker 分类与恢复规则

## 预期效果

优化后的 `ahe-completion-gate` 应该具备这些特征：

- 更像正式完成 gate，而不是“再确认一下差不多完成了”
- 更容易与 `ahe-regression-gate`、`ahe-finalize` 串成一致链路
- 更少出现“验证是绿的，但其实还不该宣告完成”的漏判
