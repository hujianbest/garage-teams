---
name: ahe-finalize
description: 正式关闭当前 AHE 工作周期。汇总 gate 证据、进度状态、发布说明、文档一致性和 handoff pack。不替代 review/gate 节点，不做新实现。
---

# AHE Finalize

正式关闭当前 AHE 工作周期。把 completion/regression 证据与 profile-specific 证据串起来，更新进度状态和发布说明，产出可交付的 handoff pack。

不做：新实现工作、替代 review/gate、替代 router 编排。

## When to Use

适用：所有 approved tasks 通过 completion gate 后、需要关闭工作周期、更新项目 release notes / changelog 和进度状态。

不适用：有剩余 approved tasks → 继续 completion 路径；需要新实现 → `ahe-test-driven-dev`；阶段不清 → `ahe-workflow-router`。

## Hard Gates

- 无 on-disk completion/regression 记录不得声称已完成
- 不混入新实现；发现需改动则停并回到 router
- 不在有剩余 approved tasks 时进入 finalize
- 必须记录 worktree 最终 disposition

## Workflow

### 1. 读取 gate 记录和当前状态

读 completion records、regression records、profile-applicable review/verification records、已批准任务计划、task-progress.md（含 worktree 字段）、项目 release notes / changelog（优先遵循 `AGENTS.md` 声明路径；若无覆写，默认 `RELEASE_NOTES.md`）、受影响的入口文档。

Profile-aware 证据矩阵：full/standard 需全部 reviews+gates；lightweight 需 regression+completion gates。记录必须 on-disk。

### 2. 更新进度状态和状态字段

task-progress.md → closeout 状态。当前 stage 标记为完成。Current Active Task 写为 null 或显式关闭。worktree 记录最终 disposition（保留/清理）。

### 3. 更新 release notes / changelog 和最小文档一致性

release notes / changelog 写入用户可见变化。检查规格/设计/任务计划等入口文档状态字段是否一致。

### 4. 记录证据矩阵和证据位置

每条证据写明记录路径或 `N/A（按 profile 跳过）`。确认无事实冲突。

### 5. 产出交付/handoff pack

至少包含：已完成工作摘要、更新过的记录、证据矩阵、交付与 handoff（含限制、分支/PR 状态、worktree 状态、当前 stage、active task、next action）。

### 6. 维护状态闭合

canonical next action 为 null（工作周期结束）或显式写出。下一个会话能继续而不需要猜测。

## Red Flags

- 不更新项目状态就声称 done
- 剩余 next task 留成隐含信息
- 用户可见变化没写 release notes / changelog
- 混入新实现
- 用会话记忆代替 on-disk 记录
- 忘记 worktree 最终 disposition

## Verification

- [ ] gate 证据已引用
- [ ] 无剩余 approved tasks
- [ ] task-progress / release notes / docs 已同步
- [ ] handoff pack 已形成
- [ ] worktree 状态已同步
- [ ] canonical next action 已填或显式 null
- [ ] 下一个会话能继续而不需猜测
