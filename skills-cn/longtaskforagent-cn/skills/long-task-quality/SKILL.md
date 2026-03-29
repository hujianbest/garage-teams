---
name: long-task-quality
description: "在长任务项目中 TDD 周期完成后使用——强制执行覆盖率门禁、变异门禁，并在将特性标为 passing 前要求新鲜验证证据"
---

# 质量门禁 —— SubAgent 派发

将质量门禁执行委派给**新上下文**的 SubAgent。主代理仅负责派发并解析结构化结果 —— **不得**直接阅读覆盖率报告、变异输出或测试运行器输出。

**开场声明：**「我正在使用 long-task-quality 技能，通过 SubAgent 执行质量门禁。」

## 步骤 1：构造 SubAgent 提示

根据当前会话状态构建提示。**不要**自行阅读任何源码、测试输出或覆盖率报告。

```
You are a Quality Gates execution SubAgent.

## Your Task
1. Read the execution rules: Read {skills_root}/long-task-quality/references/quality-execution.md
2. Read long-task-guide.md in the project root for test/coverage/mutation commands and environment activation
3. Execute all 4 gates in order (Gate 0 → 1 → 2 → 3)
4. If a gate fails, fix and retry per the rules (max 3 attempts per gate)
5. Return your result using the Structured Return Contract at the end of the execution rules

## Input Parameters
- Feature ID: {feature_id}
- Feature: {feature_json}
- quality_gates thresholds: {quality_gates_json}
- tech_stack: {tech_stack_json}
- Working directory: {working_dir}
- Feature test files: {feature_test_files}  (test files written/modified during TDD for this feature — used for mutation_feature scoping)
- Active feature count: {active_feature_count}  (total non-deprecated features — compared against mutation_full_threshold to decide mutation scope)

## Key Constraint
- Do NOT mark the feature as "passing" in feature-list.json — only report results
- If a tool/environment error cannot be resolved after 1 retry, set Verdict to BLOCKED
```

将 `{skills_root}` 替换为 skills 目录路径（如项目内 `skills` 或已安装插件路径）。

## 步骤 2：派发 SubAgent

**Claude Code：** 使用 `Agent` 工具：
```
Agent(
  description = "Quality Gates for feature #{feature_id}",
  prompt = [the constructed prompt above]
)
```

**OpenCode：** 使用 `@mention` 或平台原生子代理机制，提示内容相同。

## 步骤 3：解析结果

阅读 SubAgent 返回文本，定位 `### Verdict:` 行：

- **`### Verdict: PASS`**
  1. 提取 Metrics 表（覆盖率 %、变异分数）
  2. 提取 Next Step Inputs（coverage_line、coverage_branch、mutation_score）
  3. 记入 `task-progress.md`：「Quality Gates: PASS (line {X}%, branch {Y}%, mutation {Z}%)」
  4. 进入下一步（Feature-ST）

- **`### Verdict: FAIL`**
  1. 阅读 Issues 表 —— 确认哪道门禁失败及原因
  2. 若 SubAgent 已按 3 次重试规则尝试过修复，通过 `AskUserQuestion` 向用户上报失败详情
  3. 若可通过再次派发修复（如环境问题已解决），重新构造提示并派发（总计最多 3 次派发）

- **`### Verdict: BLOCKED`**
  1. 阅读 Issues 表 —— 确认阻塞项（工具未安装、环境错误等）
  2. 通过 `AskUserQuestion` 向用户上报阻塞及已尝试操作

## 集成

**由谁调用：** long-task-work（步骤 8）  
**前提：** TDD 周期已完成（long-task-tdd 已通过 —— 测试存在且通过）  
**产出：** 结构化摘要（覆盖率 %、变异 %、各门禁通过/失败）  
**链接至：** long-task-feature-st（Work 步骤 9）
