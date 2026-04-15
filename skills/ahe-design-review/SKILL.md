---
name: ahe-design-review
description: 评审 AHE 实现设计，判断它是否已经足够清晰、可追溯、可测试并可进入 approval step 与后续任务规划。适用于设计草稿已完成、需要正式 review verdict 的场景；若当前阶段不清或证据冲突，先回到 `ahe-workflow-router`。
---

# AHE 设计评审

评审设计文档，判断它是否可以提交给 approval step。核心职责是防止过早拆解任务——确保设计真正锚定规格、决策站得住、接口边界清楚到足以进入任务规划。

## When to Use

使用：

- `ahe-design` 已完成设计草稿，需要正式 review verdict
- 用户明确要求"review 这份 design"
- reviewer subagent 被父会话派发来执行设计评审

不使用：

- 需要继续写或修设计 → `ahe-design`
- 需要任务拆解或编码 → 相应下游节点
- 阶段不清或证据冲突 → `ahe-workflow-router`

直接调用信号："review 这份设计"、"设计评审"、"帮我看一下这个设计"。

前提条件：存在当前设计草稿、已批准规格、`AGENTS.md` 相关约定。缺设计草稿 → `ahe-design`；缺已批准规格或阶段不清 → `ahe-workflow-router`。

## Chain Contract

读取：已批准规格、被评审设计文档、`AGENTS.md` 评审约定、`task-progress.md` 当前状态、最少必要技术上下文。

产出：review 记录正文 + 结构化 reviewer 返回摘要。

评审记录落盘由 reviewer 负责；approval step 和主链推进由父会话负责。

## Hard Gates

- 设计未通过评审并完成 approval step 前，不得进入 `ahe-tasks`
- 输入工件不足以判定 stage/route 时，不直接开始评审
- reviewer 不代替父会话完成 approval step，不提前拆任务或写代码

## Iron Laws

1. **总是在实现前评审设计** — 实现后发现架构问题的修复成本是设计阶段的 10-100 倍
2. **不得放过未记录的单点故障** — 每个 SPOF 必须被识别并有缓解计划
3. **NFR 评估不可跳过** — 性能、安全、可扩展、可维护不是可选项，功能正确但 NFR 不达标 = 设计不完整
4. **权衡必须显式文档化** — 隐藏的 trade-off 是未来的意外和未认领的技术债

## Core Workflow

### 1. 建立证据基线

读取并固定证据来源：已批准规格、当前设计文档、`AGENTS.md` 约定、`task-progress.md` 状态、必要技术上下文。

不要只根据会话记忆或零散聊天内容判断"已批准"或"设计已经讲清楚"。

### 2. 多维评分与挑战式审查

对 6 个维度做内部评分（`0-10`）：需求覆盖与追溯、架构一致性、决策质量、约束与 NFR 适配、接口与任务规划准备度、测试准备度与隐藏假设。

评分辅助区分：轻微缺口 vs 需修改 vs 阻塞。按 `references/review-checklist.md` 逐项审查。

### 3. 形成结论、severity 与下一步

判定规则（详见 `references/review-record-template.md`）：

- **通过**：可追溯规格、决策清晰、约束 NFR 被吸收、无阻塞任务规划的设计空洞
- **需修改**：核心可用，局部缺口可通过一轮定向修订补齐
- **阻塞**：无法支撑需求规格、存在无法追溯的关键新增内容、或证据链冲突

severity：`critical`（阻塞任务规划）> `important`（应修复）> `minor`（建议改进）。

### 4. 写 review 记录并回传

按 `references/review-record-template.md` 写评审记录，并返回结构化 JSON 给父会话。

下一步映射：
- `通过` → `设计真人确认`（`needs_human_confirmation=true`）
- `需修改` → `ahe-design`
- `阻塞`（设计内容） → `ahe-design`
- `阻塞`（需求漂移/规格冲突） → `ahe-workflow-router`（`reroute_via_router=true`）

## Reference Guide

按需加载详细参考内容：

| 主题 | Reference | 加载时机 |
|------|-----------|---------|
| 评审检查清单 | `references/review-checklist.md` | 执行 Step 2 多维审查时 |
| 评审记录模板 | `references/review-record-template.md` | 执行 Step 4 写评审记录时 |

## Red Flags

- 因"实现时再说"就直接通过
- 把设计评审变成底层编码建议
- 接受只是复述需求、没有设计决策的文档
- 忽略缺失的接口或模块边界
- 忽略无法追溯到已批准规格的新增设计内容
- 设计评审刚"通过"就直接进入 `ahe-tasks`（跳过 approval step）
- 文档长度长就认为设计充分
- 顺手把任务也列出来"更完整"（reviewer 是 gate，不是拆任务）

## Verification

完成条件：

- [ ] 评审记录已落盘
- [ ] 给出明确结论、发现项、薄弱点和唯一下一步
- [ ] 结构化返回已使用 `next_action_or_recommended_skill`
- [ ] 若结论为 `通过`，已明确要求进入 `设计真人确认`
- [ ] 若由 reviewer subagent 执行，已完成对父会话的结构化结果回传
