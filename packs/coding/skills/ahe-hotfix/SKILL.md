---
name: ahe-hotfix
description: 适用于线上/紧急缺陷需要修复、用户要求 hotfix 分析、缺陷需要复现路径和最小修复边界的场景。不适用于写/修代码（→ ahe-test-driven-dev）、需求变更/范围调整（→ ahe-increment）、阶段不清（→ ahe-workflow-router）。
---

# AHE Hotfix

在不放弃验证纪律的前提下处理紧急缺陷。本 skill 不写生产代码——负责分析、根因收敛、状态同步，然后 handoff 给 `ahe-test-driven-dev`。

## Methodology

本 skill 融合以下已验证方法：

- **Root Cause Analysis (RCA / 5 Whys)**: 从缺陷表象逐层追问到根因，而非只修复表象。确保修复针对根因而非症状。
- **Minimal Safe Fix Boundary**: 显式定义修复边界（改什么/不改什么/影响什么），防止 hotfix 蔓延成大范围重构。
- **Blameless Post-Mortem Mindset**: 关注机制和系统性原因，而非归咎个人。缺陷分析为未来 bug-patterns 积累知识。

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

## 和其他 Skill 的区别

| Skill | 区别 |
|-------|------|
| `ahe-test-driven-dev` | 写/修代码、TDD 实现；本 skill 只做分析和根因收敛，不写生产代码 |
| `ahe-increment` | 处理需求变更/范围调整；本 skill 处理已上线功能的缺陷修复 |
| `ahe-workflow-router` | 编排/路由/阶段判断；本 skill 专注于紧急缺陷的分析与 handoff |
| `ahe-bug-patterns` | 基于缺陷模式做结构化排查；本 skill 聚焦单个缺陷的复现与根因 |

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
