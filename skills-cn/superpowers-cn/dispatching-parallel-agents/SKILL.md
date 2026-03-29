---
name: dispatching-parallel-agents
description: 当存在 2 个及以上彼此独立、可在无共享状态或顺序依赖下并行处理的任务时使用
---

# 派发并行代理

## 概述

你将任务委托给上下文隔离的专业化代理。通过精确编写它们的指令与上下文，使其保持专注并完成任务。它们不应继承你会话的上下文或历史 — 你只构造它们所需的内容。这也能为你保留上下文，便于协调工作。

当你遇到多个互不相关的失败（不同测试文件、不同子系统、不同缺陷）时，按顺序排查会浪费时间。每次排查彼此独立，可以并行进行。

**核心原则：** 每个独立问题域派发一个代理。让它们并发工作。

## 何时使用

```dot
digraph when_to_use {
    "Multiple failures?" [shape=diamond];
    "Are they independent?" [shape=diamond];
    "Single agent investigates all" [shape=box];
    "One agent per problem domain" [shape=box];
    "Can they work in parallel?" [shape=diamond];
    "Sequential agents" [shape=box];
    "Parallel dispatch" [shape=box];

    "Multiple failures?" -> "Are they independent?" [label="yes"];
    "Are they independent?" -> "Single agent investigates all" [label="no - related"];
    "Are they independent?" -> "Can they work in parallel?" [label="yes"];
    "Can they work in parallel?" -> "Parallel dispatch" [label="yes"];
    "Can they work in parallel?" -> "Sequential agents" [label="no - shared state"];
}
```

**适用于：**
- 3 个以上测试文件失败，且根因不同
- 多个子系统彼此独立地损坏
- 每个问题可在不依赖其他问题上下文的情况下理解
- 排查之间无共享状态

**不适用于：**
- 失败彼此相关（修一个可能连带修好别的）
- 需要理解完整系统状态
- 代理会互相干扰

## 模式

### 1. 识别独立域

按「什么坏了」对失败分组：
- 文件 A 的测试：工具审批流
- 文件 B 的测试：批处理完成行为
- 文件 C 的测试：中止功能

各域彼此独立 — 修工具审批不会影响中止测试。

### 2. 构造聚焦的代理任务

每个代理获得：
- **明确范围：** 一个测试文件或一个子系统
- **清晰目标：** 让这些测试通过
- **约束：** 不要改动其他代码
- **期望输出：** 你发现并修复了什么的摘要

### 3. 并行派发

```typescript
// In Claude Code / AI environment
Task("Fix agent-tool-abort.test.ts failures")
Task("Fix batch-completion-behavior.test.ts failures")
Task("Fix tool-approval-race-conditions.test.ts failures")
// All three run concurrently
```

### 4. 审阅与集成

代理返回后：
- 阅读每份摘要
- 确认修复之间无冲突
- 运行完整测试套件
- 集成所有变更

## 代理提示结构

良好的代理提示具备：
1. **聚焦** — 一个清晰的问题域
2. **自包含** — 理解问题所需的全部上下文
3. **输出明确** — 代理应返回什么？

```markdown
Fix the 3 failing tests in src/agents/agent-tool-abort.test.ts:

1. "should abort tool with partial output capture" - expects 'interrupted at' in message
2. "should handle mixed completed and aborted tools" - fast tool aborted instead of completed
3. "should properly track pendingToolCount" - expects 3 results but gets 0

These are timing/race condition issues. Your task:

1. Read the test file and understand what each test verifies
2. Identify root cause - timing issues or actual bugs?
3. Fix by:
   - Replacing arbitrary timeouts with event-based waiting
   - Fixing bugs in abort implementation if found
   - Adjusting test expectations if testing changed behavior

Do NOT just increase timeouts - find the real issue.

Return: Summary of what you found and what you fixed.
```

## 常见错误

**❌ 过宽：** 「修所有测试」— 代理会迷失  
**✅ 具体：** 「修 agent-tool-abort.test.ts」— 范围聚焦

**❌ 无上下文：** 「修竞态」— 代理不知道位置  
**✅ 有上下文：** 粘贴错误信息与测试名

**❌ 无约束：** 代理可能大重构  
**✅ 有约束：** 「不要改生产代码」或「只修测试」

**❌ 输出模糊：** 「修好它」— 你不知道改了什么  
**✅ 输出具体：** 「返回根因与变更摘要」

## 何时不要用

**相关失败：** 修一个可能修好多个 — 先一起排查  
**需要全局上下文：** 理解依赖看到整个系统  
**探索式调试：** 还不清楚哪里坏了  
**共享状态：** 代理会互相干扰（改同一文件、争用同一资源）

## 会话中的真实示例

**场景：** 大规模重构后，3 个文件共 6 个测试失败

**失败：**
- agent-tool-abort.test.ts：3 个失败（时序问题）
- batch-completion-behavior.test.ts：2 个失败（工具未执行）
- tool-approval-race-conditions.test.ts：1 个失败（执行次数 = 0）

**决策：** 独立域 — 中止逻辑、批处理完成、竞态条件彼此分离

**派发：**
```
Agent 1 → Fix agent-tool-abort.test.ts
Agent 2 → Fix batch-completion-behavior.test.ts
Agent 3 → Fix tool-approval-race-conditions.test.ts
```

**结果：**
- Agent 1：用基于事件的等待替换超时
- Agent 2：修复事件结构缺陷（threadId 位置错误）
- Agent 3：增加等待异步工具执行完成

**集成：** 所有修复彼此独立、无冲突，全套件通过

**节省时间：** 3 个问题并行解决，而非顺序解决

## 主要收益

1. **并行化** — 多项调查同时进行
2. **聚焦** — 每个代理范围窄，要跟踪的上下文更少
3. **独立性** — 代理互不干扰
4. **速度** — 用一份时间解决多个问题

## 验证

代理返回后：
1. **审阅每份摘要** — 理解变更内容
2. **检查冲突** — 是否改了同一处代码？
3. **跑全量套件** — 确认所有修复可共存
4. **抽查** — 代理也可能犯系统性错误

## 实际影响

来自调试会话（2025-10-03）：
- 3 个文件共 6 处失败
- 并行派发 3 个代理
- 所有调查并发完成
- 所有修复成功集成
- 代理变更之间零冲突
