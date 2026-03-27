---
name: long-task-feature-st
description: "在 long-task 项目中质量门禁通过后使用 — 独立管理测试环境生命周期（启动/清理），通过 Chrome DevTools MCP 按特性执行黑盒验收测试，生成符合 ISO/IEC/IEEE 29119 的测试用例文档"
---

# Feature-ST — SubAgent 分派

将黑盒验收测试委托给具备干净上下文的 SubAgent。主 Agent **仅**负责分派并解析结构化结果 — **不得**自行阅读 SRS/Design/UCD 章节、测试用例文档或执行输出。

**开始时宣告：**「我正在使用 long-task-feature-st skill，通过 SubAgent 执行验收测试。」

## 第 1 步：收集路径参数

从当前会话状态收集路径（**不要**自行读取文件正文）：

- `feature_id` — 当前特性 ID
- `feature_json` — 来自 feature-list.json 的当前特性对象（紧凑 JSON）
- `design_doc_path` — `docs/plans/*-design.md` 路径
- `srs_doc_path` — `docs/plans/*-srs.md` 路径
- `ucd_doc_path` — `docs/plans/*-ucd.md`（仅当 `"ui": true`；否则省略）
- `ats_doc_path` — `docs/plans/*-ats.md`（若存在；否则省略）
- `plan_doc_path` — `docs/features/YYYY-MM-DD-<feature-name>.md`（来自 Feature Design 步骤）
- `env_guide_path` — `env-guide.md`（若存在）
- `quality_gates_json` — feature-list.json 中的 quality_gates 阈值
- `tech_stack_json` — feature-list.json 中的 tech_stack
- `working_dir` — 项目工作目录
- `st_case_template_path` — feature-list.json 根级（可选）
- `st_case_example_path` — feature-list.json 根级（可选）

## 第 2 步：构造 SubAgent 提示词

```
You are a Feature-ST execution SubAgent for black-box acceptance testing.

## Your Task
1. Read the execution rules: Read {skills_root}/long-task-feature-st/references/feature-st-execution.md
2. Follow the checklist exactly (Steps 1-7): Load Context → Load Template → Derive Test Cases → Write Document → Validate → Execute → Cleanup
3. For UI features (ui: true), also read: {skills_root}/long-task-feature-st/prompts/e2e-scenario-prompt.md
4. Return your result using the Structured Return Contract at the end of the execution rules

## Input Parameters
- Feature ID: {feature_id}
- Feature: {feature_json}
- quality_gates: {quality_gates_json}
- tech_stack: {tech_stack_json}
- Working directory: {working_dir}

## Document Paths (read these yourself using the Read tool)
- Design doc: {design_doc_path}
- SRS doc: {srs_doc_path}
- UCD doc: {ucd_doc_path} (omit if not UI)
- ATS doc: {ats_doc_path} (omit if not present)
- Feature design plan: {plan_doc_path}
- Environment guide: {env_guide_path}

## Template/Example (optional)
- ST case template: {st_case_template_path} (omit if not set)
- ST case example: {st_case_example_path} (omit if not set)

## Key Constraints
- Do NOT mark the feature as "passing" in feature-list.json — only report results
- You MUST manage service lifecycle: start before tests, cleanup after all tests
- UI test cases MUST use Chrome DevTools MCP — no skip, no alternative
- If environment cannot start after 3 attempts, set Verdict to BLOCKED
- ALL test cases must be executed one by one — no skipping
```

## 第 3 步：分派 SubAgent

**Claude Code：** 使用 `Agent` 工具：
```
Agent(
  description = "Feature-ST for feature #{feature_id}",
  prompt = [the constructed prompt above]
)
```

**OpenCode：** 使用 `@mention` 或平台原生 subagent 机制，提示词内容相同。

## 第 4 步：解析结果

读取 SubAgent 返回文本并定位 `### Verdict:` 行：

- **`### Verdict: PASS`**
  1. 提取 Next Step Inputs：`st_case_path`、`st_case_count`、`environment_cleaned`
  2. 在 `task-progress.md` 记录：「Feature-ST: PASS ({N} cases, all passed)」
  3. 若 `environment_cleaned` 为 false，按 `env-guide.md` 自行执行清理
  4. 进入下一步（Inline Check + Persist）

- **`### Verdict: FAIL`**
  1. 阅读 Issues 表 — 定位失败用例（用例 ID、实际 vs 预期）
  2. 通过 `AskUserQuestion` 上报用户：
     - 含失败用例 ID、步骤细节、Issues 表中的实际 vs 预期
     - 选项：「修复代码并重新执行」/「通过 long-task-increment skill 修改用例」/「终止本周期」
  3. 若用户选择修复：应用修复后重新分派 SubAgent
  4. **不允许绕过** — 此处 FAIL 会阻塞特性进入 Persist

- **`### Verdict: BLOCKED`**
  1. 阅读 Issues 表 — 定位阻塞（服务无法启动、MCP 不可用等）
  2. 通过 `AskUserQuestion` 上报阻塞详情
  3. 阻塞解除后重新分派 SubAgent

## 集成

**调用方：** `long-task-work`（第 9 步）  
**需要：** 质量门禁已通过（long-task-quality 完成）  
**产出：** `docs/test-cases/feature-{id}-{slug}.md`（含执行结果与结构化摘要）  
**衔接：** Inline Check + Persist（Worker 第 10、11 步）
