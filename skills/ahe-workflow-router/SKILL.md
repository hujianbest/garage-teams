---
name: ahe-workflow-router
description: AHE workflow 的 canonical runtime router。根据最新证据决定阶段、Profile、Execution Mode、branch 切换、review dispatch 与恢复编排。
---

# AHE Workflow Router

AHE workflow family 的 **runtime authority**。负责根据最新证据决定：Workflow Profile、Execution Mode、Workspace Isolation、canonical 节点、是否切支线、review dispatch、恢复编排。

`using-ahe-workflow` 负责 public entry / family discovery；本 skill 负责 runtime routing / recovery。

## When to Use

适用：
- 用户说"继续""推进"，需依据工件判断当前节点
- review / gate 刚完成，需恢复编排
- route / stage / profile 不清
- 工件证据冲突
- 需判断是否进入 `ahe-hotfix` 或 `ahe-increment`
- 需派发 reviewer subagent

不适用 → 先走 `using-ahe-workflow`：
- 新会话还在 family discovery 阶段
- 命令入口只表达 `/ahe-*` 意图

## Workflow

### 1. 确认是否属于 runtime routing

若是 public entry discovery → 回到 `using-ahe-workflow`。否则（恢复编排、profile 判断、消费 review/gate 结论、evidence conflict、切支线）继续。

### 2. 读取最少必要证据

只读路由所需的最少内容：`AGENTS.md` 路径映射、用户请求、工件状态、`task-progress.md`、review/verification artifacts。不先做大范围代码探索。证据冲突时按未批准处理、选择更上游节点、必要时升级 profile。

### 3. 检查支线信号

优先于普通主链推进：紧急缺陷修复 → `ahe-hotfix`；需求变更/范围调整 → `ahe-increment`。

### 4. 决定 Workflow Profile

由 router 决定，不允许下游自行声称。

| Profile | 适用场景 |
|---------|---------|
| `full` | 无已批准规格/设计、架构/接口/数据模型变化、高风险模块 |
| `standard` | 已批准规格+设计，中等复杂度扩展或 bugfix |
| `lightweight` | 纯文档/配置/样式变化，或低风险单文件 bugfix |

判定：先执行 `AGENTS.md` 强制规则 → 沿用已有 profile → 按证据选择 → 冲突选更重。只允许升级，不允许降级。

详细规则：`references/profile-selection-guide.md`

### 5. 决定 Execution Mode

与 Profile 正交，不混写成复合值。归一化顺序：用户显式要求 → `AGENTS.md` 默认 → 已有值 → 默认 `interactive`。

- `interactive`：approval step 等待用户
- `auto`：按 policy 写 approval record 后自动继续
- `auto` 不删除 review、gate 或 approval 节点

详细规则：`references/execution-semantics.md`

### 5A. 决定 Workspace Isolation

可选 coordination state。读取 `task-progress.md` 已有值 + `AGENTS.md` 约定 + 当前请求类型。

决策：已有 worktree-active 且路径一致 → 沿用；进入 `ahe-test-driven-dev` 且命中 full/standard/代码修改/脏状态 → `worktree-required`；仅 lightweight+干净 → `in-place`。不静默降级。

参考：当前 skill pack 共享的 worktree isolation guide（默认 `docs/ahe-worktree-isolation.md`；若 `AGENTS.md` 声明项目等价路径，优先遵循）

### 6. 归一化显式 handoff

`Next Action Or Recommended Skill` 是受控字段。若已有显式 handoff：检查能否归一化 → 是否与最新 evidence 一致 → 是否在当前 profile 合法集合内。全部满足才采用；否则忽略，回退到迁移表。

### 7. 决定 canonical 节点

路由原则：支线优先于主链 → review/gate 恢复优先于实现 → 缺失上游优先于下游 → 冲突选更保守 → task reselection 优先于 finalize。

迁移表：`references/profile-node-and-transition-map.md`

若结论无法映射到唯一节点，重新路由，不自行补脑。

### 8. 处理 review / gate 恢复

读取最新结论 → 确认 Profile/Mode → 检查 handoff → 按 router authority 判定。

关键分支：
- `conclusion=通过` + `needs_human_confirmation=true`：interactive 等待/auto 写 record 再继续
- completion gate 通过后：有唯一 next-ready task → 更新 Current Active Task 进 `ahe-test-driven-dev`；无剩余 task → `ahe-finalize`；候选不唯一 → hard stop
- 用户提出新范围/缺陷 → 重新判断支线

参考：`references/review-dispatch-protocol.md`、`references/reviewer-return-contract.md`

### 9. review 节点派发 reviewer subagent

不在父会话内联 review。构造最小 review request，带入 Workspace Isolation 上下文，派发独立 subagent，消费结构化 summary。

### 10. 连续执行与暂停点

路由结论不是独立用户交互：非暂停点 → 同一轮进入目标 skill；review 节点 → 立刻派发；approval step → 按 Mode 处理；task reselection → 同一轮继续。只有 hard stop 才等待。

参考：`references/execution-semantics.md`

## Output Contract

最小输出：Current Stage、Workflow Profile、Execution Mode、Workspace Isolation、Target Skill。Evidence 足够时用紧凑格式（加 1-2 条决定性 Why）。不回放未命中分支、不复述 authority 说明。

runtime canonical 写法统一：`ahe-workflow-router`、`reroute_via_router`。

## Red Flags

- 没重新经过 router 就跨节点切换
- 因命令名/用户点名跳过 route/profile 判断
- 把 `using-ahe-workflow` 写进 runtime handoff
- 在 route 阶段做大范围代码探索
- 忽略 evidence conflict 沿用旧印象推进
- 把 `auto` 理解成"不写 approval record"
- 父会话内联执行 review
- profile 不再成立却不升级

## Reference Guide

| 文件 | 用途 |
|------|------|
| `references/profile-selection-guide.md` | Profile 判定详细规则 |
| `references/profile-node-and-transition-map.md` | 各 profile 合法节点与迁移表 |
| `references/execution-semantics.md` | Execution Mode、暂停点、连续执行 |
| `references/review-dispatch-protocol.md` | reviewer subagent 派发协议 |
| `references/reviewer-return-contract.md` | reviewer 返回结果契约 |
| `references/routing-evidence-guide.md` | 路由证据收集指南 |
| `references/routing-evidence-examples.md` | 路由判定示例 |

## Verification

- [ ] 已确认在做 runtime routing（非 public entry）
- [ ] 已基于最新 evidence 决定 Workflow Profile
- [ ] 已归一化 Execution Mode 且未违反 policy
- [ ] 已决定 Workspace Isolation
- [ ] 已验证显式 handoff 合法性
- [ ] 推荐节点在当前 profile 合法集合内
- [ ] completion gate 后已做 task reselection 或进入 finalize
- [ ] review 节点已派发 reviewer subagent
- [ ] 非 hard stop 时在同一轮继续执行
- [ ] 统一使用 `ahe-workflow-router` 与 `reroute_via_router`
