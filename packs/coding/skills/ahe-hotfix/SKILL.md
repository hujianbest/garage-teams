---
name: ahe-hotfix
description: 在不放弃验证纪律的前提下处理紧急缺陷修复。负责分析、根因收敛和状态同步，然后 handoff 给 ahe-test-driven-dev 执行修复。不写生产代码。
---

# AHE Hotfix

在不放弃验证纪律的前提下处理紧急缺陷。本 skill 不写生产代码——负责分析、根因收敛、状态同步，然后 handoff 给 `ahe-test-driven-dev`。

## When to Use

适用：线上/紧急缺陷需要修复；用户要求 hotfix 分析；缺陷需要复现路径和最小修复边界。

不适用：写/修代码 → `ahe-test-driven-dev`；需求变更/范围调整 → `ahe-increment`；阶段不清 → `ahe-workflow-router`。

## Hard Gates

- 必须有复现路径才能 handoff 给 `ahe-test-driven-dev`
- 必须确认根因 + 最小安全修复边界才能进入实现
- 不得把 hotfix 当成跳过质量链的理由

## Workflow

### 1. 建立证据基线

读缺陷报告、用户描述、相关代码/日志、AGENTS.md、task-progress.md。

### 2. 构建最小复现

确认复现方法。记录步骤、环境、预期 vs 实际。若无法复现 → 标为阻塞并说明原因。

### 3. 收敛根因与修复边界

定位根因。确定最小安全修复范围：改什么文件、影响什么行为、不改什么。显式写出修复边界，不扩大也不缩小。

### 4. 决定重入节点

- 有复现路径 + 根因确认 + 修复边界清晰 → handoff `ahe-test-driven-dev`
- 实际是需求变更/范围调整 → `ahe-increment`
- 证据不足以确认根因 → `ahe-workflow-router`

### 5. 写回证据和状态同步

记录保存到 `AGENTS.md` 声明的 verification 路径；若无项目覆写，默认使用 `docs/verification/hotfix-<topic>.md`。同步 task-progress.md。若使用 worktree 记录 Worktree Path/Branch。

## Red Flags

- 不复现就给修复方案
- 修了一大片"顺便优化"
- 把 hotfix 当借口跳过 review/gate
- 根因没确认就进入实现

## Verification

- [ ] 复现路径已记录
- [ ] 根因和最小修复边界已确认
- [ ] handoff 包含足够信息给 `ahe-test-driven-dev`
- [ ] task-progress.md 已同步
