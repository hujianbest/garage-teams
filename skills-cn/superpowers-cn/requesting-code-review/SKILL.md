---
name: requesting-code-review
description: 在完成任务、实现重大功能或合并进主分支前使用，用于核实工作是否满足要求
---

# 请求代码评审

派发 `superpowers:code-reviewer` 子代理，在问题连锁放大之前发现问题。评审者会收到精心裁剪的上下文用于评估——绝不塞入本会话的历史。这样评审者专注于产出物，而非你的思路过程，也为你保留上下文以便继续工作。

**核心原则：** 早评审、常评审。

## 何时请求评审

**必须：**
- 子代理驱动开发中每完成一个任务后
- 完成重大功能后
- 合并进 main 之前

**可选但很有价值：**
- 卡住时（换视角）
- 重构前（建立基线）
- 修复复杂缺陷后

## 如何请求

**1. 获取 git SHA：**
```bash
BASE_SHA=$(git rev-parse HEAD~1)  # 或 origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

**2. 派发 code-reviewer 子代理：**

使用 Task 工具，类型为 `superpowers:code-reviewer`，按 `code-reviewer.md` 中的模板填写。

**占位符：**
- `{WHAT_WAS_IMPLEMENTED}` — 你刚完成的内容
- `{PLAN_OR_REQUIREMENTS}` — 预期行为/需求
- `{BASE_SHA}` — 起始提交
- `{HEAD_SHA}` — 结束提交
- `{DESCRIPTION}` — 简短摘要

**3. 处理反馈：**
- 严重（Critical）问题立即修复
- 重要（Important）问题在继续前修复
- 次要（Minor）问题记下来稍后处理
- 若评审有误，有理有据地反驳

## 示例

```
[刚完成任务 2：添加校验函数]

你：继续前先请求代码评审。

BASE_SHA=$(git log --oneline | grep "Task 1" | head -1 | awk '{print $1}')
HEAD_SHA=$(git rev-parse HEAD)

[派发 superpowers:code-reviewer 子代理]
  WHAT_WAS_IMPLEMENTED: 会话索引的校验与修复函数
  PLAN_OR_REQUIREMENTS: docs/superpowers/plans/deployment-plan.md 中的任务 2
  BASE_SHA: a7981ec
  HEAD_SHA: 3df7661
  DESCRIPTION: 新增 verifyIndex() 与 repairIndex()，覆盖 4 类问题

[子代理返回]：
  优点：架构清晰、有真实测试
  问题：
    重要：缺少进度指示
    次要：上报间隔使用魔数 100
  评估：可以继续推进

你：[修复进度指示]
[继续任务 3]
```

## 与工作流集成

**子代理驱动开发：**
- 每个任务后都评审
- 在问题叠加前拦截
- 进入下一任务前先修好

**执行计划：**
- 每批（例如 3 个任务）后评审
- 获取反馈、应用、再继续

**临时开发：**
- 合并前评审
- 卡住时评审

## 危险信号

**绝不：**
- 因为「很简单」就跳过评审
- 忽略严重（Critical）问题
- 重要（Important）问题未修就继续
- 对有效的技术反馈抬杠

**若评审有误：**
- 用技术理由反驳
- 用代码/测试证明可行
- 请求澄清

模板见：`requesting-code-review/code-reviewer.md`
