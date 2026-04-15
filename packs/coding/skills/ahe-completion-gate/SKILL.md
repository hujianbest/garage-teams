---
name: ahe-completion-gate
description: 执行正式完成门禁。用 fresh completion evidence 判断当前任务是否可宣告完成，给出 canonical 下一步。若上游证据链缺失，先回到 ahe-workflow-router。
---

# AHE 完成门禁

在宣告任务完成前，确认有足够、最新且与当前任务同范围的证据。不是 regression gate（广义回归），也不是 finalize（文档/状态收尾）。判断"当前 task 完成是否成立"，不自动等同于"整个 workflow 已完成"。

## When to Use

适用：regression gate 之后需判断当前任务完成后的走向；确认任务可宣告完成；准备更新 task-progress 与项目 release notes / changelog；用户要求"能不能算完成"。

不适用：缺 regression 记录/实现交接块 → 补齐；需回归验证 → `ahe-regression-gate`；需状态收尾 → `ahe-finalize`；阶段不清 → `ahe-workflow-router`。

## Hard Gates

- 没有针对最新代码的验证证据就不能宣称完成
- 本轮没运行验证命令就不能诚实宣称完成
- 缺实现交接块或 regression 记录不得返回 `通过`
- worktree-active 时 completion evidence 必须锚定同一 Worktree Path
- 不得把"task 完成"等同于"workflow 可 finalize"

## Workflow

### 1. 明确完成宣告范围

写出准备宣告什么：测试通过、功能行为正常、缺陷已修复、任务已完成。

### 2. 对齐上游结论与 profile 条件

确认：当前 profile 必需的 review/gate 记录齐全 → regression gate 结论允许继续 → 实现交接块/task-progress/完成声明在同一任务范围 → 任务计划足以判断剩余任务。

Profile-aware 上游证据矩阵：

| Profile | 需确认的上游记录 |
|---------|---------------|
| `full` / `standard` | bug-patterns、test-review、code-review、traceability-review、regression-gate、实现交接块 |
| `lightweight` | regression-gate、实现交接块；其余写 `N/A（按 profile 跳过）` |

full/standard 记录缺失/过旧 → `阻塞`。

### 3-4. 确定、执行验证命令

选择能直接证明结论的命令，立即运行完整验证。不用更弱证据替代。

### 5. 阅读完整结果

检查退出码、失败数量、输出是否支持结论、结果是否属于当前最新代码。

### 6. 形成 completion evidence bundle

记录：完成范围、命令、退出码、结果摘要、新鲜度锚点、未覆盖什么。

### 7. 门禁判断

- 证据支持完成 + 有唯一 next-ready task → `通过`，下一步 `ahe-workflow-router`
- 证据支持完成 + 无剩余任务 → `通过`，下一步 `ahe-finalize`
- 证据不足/仍需实现 → `需修改`，下一步 `ahe-test-driven-dev`
- 环境/工具链问题 → `阻塞`，下一步 `ahe-completion-gate`
- 上游编排/profile/证据链问题，或剩余任务不唯一 → `阻塞`，下一步 `ahe-workflow-router`

## Output Contract

记录保存到 `AGENTS.md` 声明的 verification 路径；若无项目覆写，默认使用 `docs/verification/completion-<task>.md`。结构包含：结论、已消费上游结论、上游证据矩阵、完成宣告范围、剩余任务判断、已验证结论、证据、覆盖边界、明确不在范围内的项、下一步。

在 task-progress.md 写回 canonical Next Action。

## Red Flags

- 说"应该算完成了"
- 依赖旧输出
- 把主观感觉当证据
- 认为 review 通过就等于运行成功
- 不读 regression 记录就宣告完成
- worktree-active 但 completion record 没写 Worktree Path

## Verification

- [ ] completion verification record 已落盘
- [ ] 上游证据矩阵、完成范围、剩余任务判断、evidence bundle 已写清
- [ ] 基于最新证据给出唯一门禁结论
- [ ] worktree 状态已写出（若适用）
- [ ] task-progress.md 已同步 canonical Next Action
