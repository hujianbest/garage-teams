---
name: long-task-finalize
description: "在 ST 判定为 Go 之后使用 — 通过 SubAgent 生成使用示例并定稿发布文档"
---

# Finalize — ST 之后的文档与示例

在系统测试通过且判定为 Go/Conditional-Go 后，生成基于场景的使用示例并完成发布文档定稿。

**开始时宣告：**「我正在使用 long-task-finalize skill。ST 已通过 — 正在生成示例并完成文档定稿。」

**幂等：** 在 ST 缺陷修复循环后再次调用也安全。每次运行会干净覆盖 `examples/` 内容。

<HARD-GATE>
除非 ST 判定为 Go 或 Conditional-Go，否则**不得**调用本 skill。若为 No-Go，应回到 Worker 修复而非执行 Finalize。
</HARD-GATE>

## 检查清单

**必须**为每一步创建 TodoWrite 任务并按顺序完成：

### 1. 收集上下文

- 读取 `feature-list.json` — 全部通过且未弃用的功能、`tech_stack`、`quality_gates`
- 读取 SRS（`docs/plans/*-srs.md`）— 需求描述、用户画像
- 读取 Design（`docs/plans/*-design.md`）— 架构、对外 API 面
- 读取 UCD（`docs/plans/*-ucd.md`）— 仅当存在 UI 功能时
- 读取 `task-progress.md` — 用于 ST 摘要条目
- 读取 `RELEASE_NOTES.md` — 当前版本条目状态
- 记下 SubAgent 分派所需路径

### 2. 生成示例（SubAgent）

分派 example-generator SubAgent，产出基于场景的使用示例。

1. 构造 SubAgent 提示词：
   ```
   You are an Example Generator SubAgent.

   ## Your Task
   1. Read the agent definition: Read <skills_root>/../agents/example-generator.md
   2. Follow the process to generate scenario-based usage examples
   3. Return your result using the Structured Return Contract

   ## Input Parameters
   - feature-list.json: <path>
   - SRS: <srs_path>
   - Design: <design_path>
   - UCD: <ucd_path> (or "none")
   - tech_stack: <tech_stack_json>
   - Working directory: <project_root>
   ```

2. 分派：
   ```
   Agent(
     description = "Generate usage examples for all features",
     prompt = [constructed prompt]
   )
   ```

3. 解析返回约定：
   - **PASS**：计划内场景均已生成并校验
   - **PARTIAL**：部分示例已生成；对缺口记警告
   - **FAIL**：记错误；仍继续 — 示例为**非阻塞**

在 `task-progress.md` 中记录：
```
- Examples: <verdict> — N scenarios, N examples generated, N features covered
```

### 3. 更新 RELEASE_NOTES.md

添加 ST 完成与版本条目（自 ST Persist 移入）：
- 在 `[Unreleased]` 下添加条目，或视情况创建版本小节
- 包含：ST 判定、日期、测试摘要（执行的类别、发现/修复的缺陷）
- 引用 ST 报告文档路径

### 4. 更新 task-progress.md

添加 ST 会话摘要条目（自 ST Persist 移入）：
- 已执行的 ST 类别、通过/失败计数
- 发现与修复的缺陷（含严重程度）
- 完整变异测试分数
- 最终质量指标
- 第 2 步的示例生成结果

### 5. 持久化

- Git 提交全部文档产物：
  ```
  git add examples/ RELEASE_NOTES.md task-progress.md
  git commit -m "docs: finalize release — examples, release notes, progress update"
  ```
- 校验：
  ```bash
  python scripts/validate_features.py feature-list.json
  ```

### 6. 摘要

输出完成摘要：
> **Finalize — DONE**
>
> Examples: N scenarios generated (N features covered, N skipped)
> RELEASE_NOTES.md: Updated with ST completion
> task-progress.md: Updated with ST session summary

## 关键规则

- **非阻塞** — 示例生成失败**不会**追溯改变 Go 判定
- **幂等** — 可安全重跑；干净覆盖 `examples/`
- **仅示例走 SubAgent** — RELEASE_NOTES 与 task-progress 由本 skill 直接更新（不由 SubAgent）
- **不新增功能** — 不得添加、修改或测试功能；仅限文档
- **遵循项目约定** — 示例与项目语言、风格、模式一致

## 集成

**调用方：** `long-task-st`（第 13 步，Go/Conditional-Go 判定之后）  
**读取：** `feature-list.json`、`docs/plans/*-srs.md`、`docs/plans/*-design.md`、`docs/plans/*-ucd.md`（若有 UI）、`task-progress.md`、`RELEASE_NOTES.md`、实现代码  
**产出：** `examples/`（使用示例 + README.md）、更新后的 `RELEASE_NOTES.md`、`task-progress.md`  
**Agent：** `agents/example-generator.md`
