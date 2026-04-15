---
name: using-ahe-workflow
description: AHE workflow family 的公开入口层。用于新会话发现、/ahe-* 命令解释、判断 direct invoke vs route-first。若需要 authoritative routing，交给 ahe-workflow-router。
---

# Using AHE Workflow

AHE workflow family 的 **public shell**。帮助你决定：

- `direct invoke`：当前节点已明确，直接进入 leaf skill
- `route-first`：阶段/profile/证据不稳定，交给 `ahe-workflow-router`

本 skill 是 public entry，不是 runtime handoff。不替代 router 的 authoritative routing。

## When to Use

适用：
- 新 AHE 工作周期，不确定从哪进入
- 用户说"继续""推进""开始做"但当前节点未确认
- 用户用 `/ahe-spec`、`/ahe-build`、`/ahe-review` 等命令意图
- 需判断 direct invoke 还是 route-first
- 用户要求 `auto mode` 但还没确定交给哪个节点

不适用：已在 leaf skill 内部 → 继续当前 skill；需要 authoritative routing → 直接交给 `ahe-workflow-router`；还在判断产品 thesis → `using-ahe-product-workflow`。

## Boundary With Product Skills

若问题仍在产品 thesis/wedge/probe 层面 → 先去 `using-ahe-product-workflow`。
若已产出 `docs/insights/*-spec-bridge.md` 且目标是 formal spec/design/tasks → 可进入 coding family。

## Workflow

### 1. 判断 entry vs runtime recovery

entry（用本 skill）：新会话、高层意图、命令 bias、direct vs route 选择。
runtime recovery（交给 router）：review/gate 刚完成、evidence 冲突、需切支线、需消费 gate 结论 → `ahe-workflow-router`。

### 2. 识别主意图

归到以下之一：新需求、继续推进、review-only、gate-only、当前任务实现、规格相关、hotfix、increment、closeout、Execution Mode 偏好。

### 3. 提取 Execution Mode 偏好

用户说 `auto mode`/`自动执行`/`不用等我确认` → 视为 Execution Mode 偏好，不是新 Profile，不是跳过 approval 的理由，不是 direct invoke 的充分条件。随 handoff 带给下游。

### 4. 判断是否允许 direct invoke

同时满足才可：节点已明确、请求属于该 skill 职责、工件存在可读、无 route/stage/profile 冲突、Execution Mode 偏好已传递。任一不满足 → route-first 交给 router。

### 5. 应用 entry bias

| 用户意图 | 可优先尝试 | 不明确时回退 |
|---------|----------|-----------|
| 规格澄清/修订 | `ahe-specify` | `ahe-workflow-router` |
| 当前活跃任务实现 | `ahe-test-driven-dev` | `ahe-workflow-router` |
| review/gate 请求 | 具体 review/gate skill | `ahe-workflow-router` |
| closeout/finalize | `ahe-completion-gate` / `ahe-finalize` | `ahe-workflow-router` |
| 线上问题修复 | `ahe-hotfix` | `ahe-workflow-router` |
| 范围/验收/约束变化 | `ahe-increment` | `ahe-workflow-router` |

### 6. 命令当作 bias，不当作 authority

`/ahe-spec` → 偏向 `ahe-specify`；`/ahe-build` → 偏向 `ahe-test-driven-dev`；`/ahe-review` → 偏向 review skill；`/ahe-closeout` → 偏向 completion/finalize。命令不替代工件检查和 profile 判断。

### 7. 正确结束

输出只有两类：1) 明确进入合法 leaf skill；2) 明确交给 `ahe-workflow-router`。不在这里展开 transition map、做 review recovery、或把 `using-ahe-workflow` 写进 handoff。

### 8. Clear-case fast path

唯一确定下一步时用 3 行编号格式：
1. `Entry Classification`：`direct invoke` 或 `route-first`
2. `Target Skill`：canonical skill 名
3. `Why`：1-2 条最关键证据

不回放 entry matrix、不重讲分层历史、不展开不相关的备选。route-first 时只说明"为什么不能 direct invoke"然后立即转交。

## Red Flags

- 把 `using-ahe-workflow` 写成完整状态机
- route 不清时硬做 direct invoke
- 把本 skill 写进 `Next Action Or Recommended Skill`
- 因用户点名就跳过工件检查
- review/gate 完成后仍在做恢复编排
- 复制 router 的 transition map 或 pause-point rules

## Supporting References

| 文件 | 用途 |
|------|------|
| `docs/ahe-workflow-entrypoints.md` | public entry 与 direct invoke 边界 |
| `docs/ahe-command-entrypoints.md` | `/ahe-*` 命令解释 |
| `ahe-workflow-router/SKILL.md` | authoritative runtime routing |

## Verification

- [ ] 已判断 entry vs runtime recovery
- [ ] 已区分 direct invoke vs route-first
- [ ] clear case 使用 3 行编号快路径
- [ ] 节点明确 → 进入合法 leaf skill
- [ ] 节点不明确 → 交给 `ahe-workflow-router`
- [ ] Execution Mode 偏好已传递给下游
- [ ] 未把本 skill 写入 runtime handoff
