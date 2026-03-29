---
name: long-task-feature-design
description: "在 long-task 项目中 TDD 之前使用 — 产出含接口契约、算法伪代码、图表与测试清单的特性级详细设计"
---

# 特性级详细设计 — SubAgent 分派

将特性详细设计产出委托给具备干净上下文的 SubAgent。主 Agent 仅负责分派并解析结构化结果 — **不得**自行阅读设计/SRS/UCD 文档章节或直接撰写设计文档。

**开始时宣告：**「我正在使用 long-task-feature-design skill，通过 SubAgent 产出详细设计。」

## 何时运行

- Worker 第 4 步，TDD（第 5–7 步）之前
- 每个特性均需执行（`category: "bugfix"` 时可采用精简版）
- 由 `long-task-work` 作为子 skill 调用（非路由器直接调用）

> **对于 `category: "bugfix"` 的特性**：SubAgent 应侧重：(1) 根因说明（来自 `root_cause` 字段），(2) 针对性修复思路，(3) 基于 SRS 验收标准（经 `srs_trace`）的回归测试清单。除非缺陷直接触及这些面，否则跳过完整接口契约、数据流图与状态图。

## 第 1 步：收集路径参数

从当前会话状态收集下列信息。**不要**自行读取文档正文：

- `feature_json` — `feature-list.json` 中当前特性对象（紧凑 JSON）
- `quality_gates_json` — `feature-list.json` 中的 quality_gates（紧凑 JSON）
- `tech_stack_json` — `feature-list.json` 中的 tech_stack（紧凑 JSON）
- `design_doc_path` — 设计文档路径（`docs/plans/*-design.md`）
- `design_start` / `design_end` — §4.N 小节的行号范围（来自 Orient Document Lookup）
- `srs_doc_path` — SRS 路径（`docs/plans/*-srs.md`）
- `srs_start` / `srs_end` — FR-xxx 小节的行号范围（来自 Orient Document Lookup）
- `ucd_doc_path` — UCD 路径（仅当 `"ui": true`；否则省略）
- `ucd_start` / `ucd_end` — 相关 UCD 小节行号（若适用）
- `ats_doc_path` — ATS 文档路径（`docs/plans/*-ats.md`），若存在；否则省略
- `constraints` — `feature-list.json` 根级 `constraints[]`
- `assumptions` — `feature-list.json` 根级 `assumptions[]`
- `output_path` — 目标文件：`docs/features/YYYY-MM-DD-<feature-name>.md`
- `working_dir` — 项目工作目录

## 第 2 步：构造 SubAgent 提示词

```
You are a Feature Design execution SubAgent.

## Your Task
1. Read the execution rules: Read {skills_root}/long-task-feature-design/references/feature-design-execution.md
2. Read the template: Read {skills_root}/long-task-feature-design/references/feature-design-template.md
3. Read design section: Read {design_doc_path} lines {design_start} to {design_end}
4. Read SRS section: Read {srs_doc_path} lines {srs_start} to {srs_end}
5. Read UCD sections: Read {ucd_doc_path} lines {ucd_start} to {ucd_end} (only if ui:true)
5b. Read ATS mapping table: Read {ats_doc_path} (only if ATS doc exists) — locate the mapping rows for the feature's requirement ID(s) (from srs_trace); extract required categories
6. Follow the execution rules to produce the detailed design document
7. Write the document to: {output_path}
8. Return your result using the Structured Return Contract in the execution rules

## Input Parameters
- Feature: {feature_json}
- quality_gates: {quality_gates_json}
- tech_stack: {tech_stack_json}
- Constraints: {constraints}
- Assumptions: {assumptions}
- ATS doc path: {ats_doc_path} (or "none" if no ATS doc exists)
- Working directory: {working_dir}

## Key Constraints
- Write the complete design document to {output_path}
- Every section (§2-§6) must be COMPLETE or have "N/A — [reason]"
- Test Inventory negative ratio must be >= 40%
- Test Inventory main categories (FUNC/BNDRY/SEC/UI/PERF) must cover all ATS-required categories for this feature's requirement(s)
- Do NOT start TDD — only produce the design document
```

## 第 3 步：分派 SubAgent

**Claude Code：** 使用 `Agent` 工具：
```
Agent(
  description = "Feature Design for feature #{feature_id}",
  prompt = [the constructed prompt above]
)
```

**OpenCode：** 使用 `@mention` 或平台原生 subagent 机制，提示词内容相同。

## 第 4 步：解析结果

读取 SubAgent 返回文本并定位 `### Verdict:` 行：

- **`### Verdict: PASS`**
  1. 确认设计文档存在于 `output_path`
  2. 提取 Next Step Inputs：`feature_design_doc`、`test_inventory_count`、`tdd_task_count`
  3. 在 `task-progress.md` 记录：「Feature Design: PASS ({N} test scenarios, {M} TDD tasks)」
  4. 进入 TDD（第 5–7 步）

- **`### Verdict: FAIL`**
  1. 阅读 Issues 表 — 定位未完成的小节
  2. 必要时带补充上下文重新分派 SubAgent（最多 2 次重试）
  3. 仍失败则通过 `AskUserQuestion` 上报用户

- **`### Verdict: BLOCKED`**
  1. 阅读 Issues 表 — 定位阻塞项
  2. 通过 `AskUserQuestion` 上报用户

## 集成

**调用方：** long-task-work（第 4 步）  
**需要：** 系统设计文档、SRS、`feature-list.json`  
**产出：** `docs/features/YYYY-MM-DD-<feature-name>.md`（由 SubAgent 写入）  
**衔接：** long-task-tdd（经工作流第 5–7 步）
