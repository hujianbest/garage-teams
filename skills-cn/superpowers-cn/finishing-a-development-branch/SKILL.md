---
name: finishing-a-development-branch
description: 当实现已完成、测试全部通过且需决定如何集成工作时使用——通过结构化选项（合并、PR 或清理）引导开发收尾
---

# 完成开发分支

## 概述

通过呈现清晰选项并执行所选工作流，引导开发工作收尾。

**核心原则：** 验证测试 → 呈现选项 → 执行选择 → 清理。

**开场声明：** 「我正在使用 finishing-a-development-branch 技能来完成这项工作。」

## 流程

### 第 1 步：验证测试

**在呈现选项之前，确认测试通过：**

```bash
# Run project's test suite
npm test / cargo test / pytest / go test ./...
```

**若测试失败：**
```
测试失败（<N> 处）。必须先修复再收尾：

[展示失败信息]

在测试通过前，不得继续合并或创建 PR。
```

停止。不要进入第 2 步。

**若测试通过：** 继续第 2 步。

### 第 2 步：确定基准分支

```bash
# Try common base branches
git merge-base HEAD main 2>/dev/null || git merge-base HEAD master 2>/dev/null
```

或询问：「本分支是从 main 分出来的 — 对吗？」

### 第 3 步：呈现选项

恰好呈现以下 4 个选项：

```
实现已完成。你希望如何处理？

1. 本地合并回 <base-branch>
2. 推送并创建 Pull Request
3. 保留分支现状（稍后我自己处理）
4. 丢弃本次工作

请选择？
```

**不要附加解释** — 保持选项简短。

### 第 4 步：执行选择

#### 选项 1：本地合并

```bash
# Switch to base branch
git checkout <base-branch>

# Pull latest
git pull

# Merge feature branch
git merge <feature-branch>

# Verify tests on merged result
<test command>

# If tests pass
git branch -d <feature-branch>
```

然后：清理 worktree（第 5 步）

#### 选项 2：推送并创建 PR

```bash
# Push branch
git push -u origin <feature-branch>

# Create PR
gh pr create --title "<title>" --body "$(cat <<'EOF'
## Summary
<2-3 bullets of what changed>

## Test Plan
- [ ] <verification steps>
EOF
)"
```

然后：清理 worktree（第 5 步）

#### 选项 3：保持原样

汇报：「保留分支 <name>。Worktree 仍位于 <path>。」

**不要清理 worktree。**

#### 选项 4：丢弃

**先确认：**
```
以下将被永久删除：
- 分支 <name>
- 全部提交：<commit-list>
- 位于 <path> 的 worktree

请键入 discard 以确认。
```

等待用户准确确认。

若已确认：
```bash
git checkout <base-branch>
git branch -D <feature-branch>
```

然后：清理 worktree（第 5 步）

### 第 5 步：清理 Worktree

**对选项 1、2、4：**

检查是否处于 worktree：
```bash
git worktree list | grep $(git branch --show-current)
```

若是：
```bash
git worktree remove <worktree-path>
```

**对选项 3：** 保留 worktree。

## 速查表

| 选项 | 合并 | 推送 | 保留 Worktree | 清理分支 |
|--------|-------|------|---------------|----------------|
| 1. 本地合并 | ✓ | - | - | ✓ |
| 2. 创建 PR | - | ✓ | ✓ | - |
| 3. 保持原样 | - | - | ✓ | - |
| 4. 丢弃 | - | - | - | ✓（强制） |

## 常见错误

**跳过测试验证**
- **问题：** 合并坏代码、创建会失败的 PR
- **修复：** 提供选项前始终验证测试

**开放式提问**
- **问题：** 「接下来做什么？」→ 含糊
- **修复：** 恰好呈现 4 个结构化选项

**自动清理 worktree**
- **问题：** 在仍可能需要时移除 worktree（选项 2、3）
- **修复：** 仅对选项 1 和 4 清理

**丢弃无确认**
- **问题：** 误删工作成果
- **修复：** 选项 4 要求用户键入 `discard` 确认

## 红线

**绝不：**
- 在测试仍失败时继续
- 合并未在合并结果上验证测试
- 未经确认删除工作
- 未经明确要求 force-push

**务必：**
- 提供选项前先验证测试
- 恰好呈现 4 个选项
- 选项 4 取得键入确认
- 仅对选项 1 与 4 清理 worktree

## 集成

**由以下技能调用：**
- **subagent-driven-development**（第 7 步）— 全部任务完成后
- **executing-plans**（第 5 步）— 全部批次完成后

**常与以下技能配合：**
- **using-git-worktrees** — 清理由该技能创建的 worktree
