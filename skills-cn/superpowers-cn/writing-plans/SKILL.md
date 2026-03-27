---
name: writing-plans
description: 当你已有规格或多步骤任务的需求、且尚未动代码时使用
---

# 撰写计划

## 概述

撰写完整的实现计划时，假定工程师对我们的代码库零上下文，且品味可疑。写清他们需要的全部信息：每项任务要动哪些文件、代码、测试、可能要查的文档、如何测试。把整个计划拆成一口大小的任务。DRY。YAGNI。TDD。频繁提交。

假定他们是熟练开发者，但几乎不了解我们的工具链或问题域。假定他们对良好测试设计不太熟。

**开场须声明：**「我正在使用 writing-plans 技能来编写实现计划。」

**上下文：** 应在专用 worktree 中运行（由 brainstorming 技能创建）。

**计划保存到：** `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md`
- （用户对计划路径的偏好优先于此默认）

## 范围检查

若规格涵盖多个相互独立的子系统，应在头脑风暴阶段已拆成子项目规格。若尚未拆分，建议拆成多份计划——每个子系统一份。每份计划应能单独产出可运行、可测试的软件。

## 文件结构

在定义任务之前，先列出将创建或修改哪些文件，以及各自职责。分解决策在此定型。

- 设计边界清晰、接口明确的单元。每个文件职责单一。
- 你能同时装进上下文的代码，推理最清楚；文件聚焦时编辑更可靠。优先小而专的文件，而不是大包大揽的大文件。
- 经常一起变的文件应放在一起。按职责拆分，而不是按技术分层。
- 在现有代码库中遵循既有模式。若代码库惯用大文件，不要单方面大重构——但若你正在改的文件已经臃肿，在计划里包含拆分是合理的。

该结构指导任务分解。每项任务应产生自成一体、单独也说得通的变更。

## 一口大小任务的粒度

**每一步是一个动作（约 2–5 分钟）：**
- 「写失败测试」— 一步
- 「运行确认确实失败」— 一步
- 「写最少代码让测试通过」— 一步
- 「运行测试确认通过」— 一步
- 「提交」— 一步

## 计划文档页眉

**每份计划必须以该页眉开头：**

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

## 任务结构

````markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

- [ ] **Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

- [ ] **Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## 记住
- 始终写确切文件路径
- 计划中写完整代码（不要只写「加校验」）
- 写确切命令与期望输出
- 用 @ 语法引用相关技能
- DRY、YAGNI、TDD、频繁提交

## 计划评审循环

写完完整计划后：

1. 派发**单个** plan-document-reviewer 子代理（见 plan-document-reviewer-prompt.md），附上精心编写的评审上下文——**不要**甩整个会话历史。这样评审者聚焦计划，而非你的思路。
   - 提供：计划文档路径、规格文档路径
2. 若 ❌ 发现问题：修复后，**整份计划**再次派发评审者
3. 若 ✅ 通过：进入执行交接

**评审循环指引：**
- 同一名写计划的代理负责修改（保留上下文）
- 若循环超过 3 轮，提请人类决策
- 评审者是建议性的——若你认为反馈不对，说明分歧

## 执行交接

保存计划后，提供执行选项：

**「计划已完成并保存到 `docs/superpowers/plans/<filename>.md`。两种执行方式：**

**1. 子代理驱动（推荐）** — 每项任务派新子代理，任务间评审，迭代快

**2. 本会话内执行** — 用 executing-plans 在本会话执行任务，批量执行并设检查点

**选哪种？」**

**若选子代理驱动：**
- **必选子技能：** 使用 superpowers:subagent-driven-development
- 每项任务新子代理 + 两阶段评审

**若选本会话内执行：**
- **必选子技能：** 使用 superpowers:executing-plans
- 批量执行并设检查点供评审
