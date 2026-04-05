# 优化 `ahe-tasks` 方案

## 目标

把 `skills/ahe-tasks/SKILL.md` 从“能把设计拆成任务计划”的 skill，提升为“能稳定产出高质量、可执行、可追溯、可验证任务计划”的 skill。

本次优化不改变 AHE 主链契约：

- 仍然只在需求规格和设计都已批准时使用
- 仍然在 `ahe-tasks-review` 前禁止进入实现
- 仍然由 `ahe-workflow-starter` 管理下游编排
- 仍然在 `ahe-tasks-review` 通过并写入批准记录后，才进入 `ahe-test-driven-dev`

## 当前问题

当前 `ahe-tasks` 已具备正确门禁和基本任务拆解流程，但仍偏“可用计划生成器”，主要短板是：

- 任务粒度有要求，但缺少稳定任务单元模板，容易出现“听起来像任务，实际不好执行”的条目
- 没有把文件 / 工件影响面显式列出来，导致任务容易脱离代码库真实边界
- `ahe-tasks-review` 会检查可追溯性，但 `ahe-tasks` 本身没有把“规格 / 设计 -> 任务”的映射做成显式产物
- 只要求验证方式与完成条件，但缺少更可执行的命令 / 证据 / 预期结果意识
- 与 `ahe-test-driven-dev` 的衔接较弱，没有把“测试设计种子”提前嵌入任务计划
- `task-progress-template.md` 的通用字段名与 AHE 下游技能使用的字段名存在表达差异，当前 skill 没有明确说明映射

## 优化方向

### 1. 增加“文件 / 工件影响图”

在正式拆任务前，先要求列出：

- 会创建哪些文件
- 会修改哪些文件 / 工件
- 会验证哪些测试或记录文件

为什么这么改：

- 高质量任务计划不能只按功能点切，还要锚定到实际工件边界
- 这能显著减少“实现某模块”这类空泛任务

主要参考：

- `references/superpowers-main/skills/writing-plans/SKILL.md`
- `skills/ahe-tasks/SKILL.md`

### 2. 引入稳定任务单元模板

每个任务至少明确：

- 任务 ID
- 目标
- 依赖
- 触碰工件
- 验证方式 / 预期证据
- 完成条件
- 测试设计种子

为什么这么改：

- 这能把“任务条目”升级成“可直接执行的工作单元”
- 也更方便后续 `Current Active Task` 的唯一选择

主要参考：

- `references/superpowers-main/skills/writing-plans/SKILL.md`
- `references/everything-claude-code-main/skills/blueprint/SKILL.md`

### 3. 强化任务级可执行性

把当前的“验证方式”升级为更具体的要求，例如：

- 尽量写明命令入口
- 写明预期结果 / 新鲜证据
- 区分 fail-first、实现、验证、状态更新类步骤

为什么这么改：

- 高质量任务计划应能被冷启动执行，而不是依赖会话记忆

主要参考：

- `references/superpowers-main/skills/writing-plans/SKILL.md`
- `references/superpowers-main/skills/executing-plans/SKILL.md`

### 4. 增加追溯矩阵

要求任务计划显式说明：

- 关键需求 / 设计决策分别落到哪些里程碑和任务
- 哪些任务是在消化风险或验证高风险区域

为什么这么改：

- 这能让 `ahe-tasks-review` 的“可追溯性”检查变得可机械核对
- 也能避免任务 quietly 偏离规格与设计

主要参考：

- `skills/ahe-tasks-review/SKILL.md`
- `references/longtaskforagent-main/skills/long-task-feature-design/SKILL.md`

### 5. 补强与 `ahe-test-driven-dev` 的衔接

在任务计划中要求每个关键任务至少给出：

- 主要行为
- 边界 / 反向场景
- 建议优先验证的点

为什么这么改：

- 这不是替代 `ahe-test-driven-dev` 的真人测试设计确认
- 是为后续测试设计确认准备更好的种子

主要参考：

- `skills/ahe-test-driven-dev/SKILL.md`
- `references/longtaskforagent-main/skills/long-task-feature-design/SKILL.md`

### 6. 增加评审前自检

在交 `ahe-tasks-review` 前，要求自检：

- 是否存在过大任务
- 是否存在缺依赖 / 缺验证 / 缺完成条件
- 是否存在无法追溯到规格或设计的任务
- 是否已经给出唯一 `Current Active Task` 选择规则

为什么这么改：

- 这能减少低质量计划直接被 review 打回

主要参考：

- `skills/ahe-tasks-review/SKILL.md`
- `references/superpowers-main/skills/writing-plans/SKILL.md`

### 7. 明确进度字段映射

在使用通用 `templates/task-progress-template.md` 时，明确说明：

- `Current Active Task` 对应 `Current Task`
- `Next Action Or Recommended Skill` 对应 `Next Action`

为什么这么改：

- 当前 AHE 下游实现 skill 读取的是 AHE 字段名
- 如果不说明映射，跨模板 / 跨项目时容易出现状态字段漂移

主要参考：

- `templates/task-progress-template.md`
- `skills/ahe-test-driven-dev/SKILL.md`

## 明确不做的事

- 不把 `ahe-tasks` 变成 `ahe-tasks-review`
- 不把任务计划写成设计文档副本
- 不把任务计划直接变成实现日志
- 不提前消化 `ahe-test-driven-dev` 的真人测试设计确认门禁

## 计划中的实际改动

会对 `skills/ahe-tasks/SKILL.md` 做一轮聚焦重构，预计包括：

- 收紧 `description`
- 增加高质量任务计划基线
- 增加文件 / 工件影响图要求
- 引入更稳定的任务单元模板
- 强化可执行验证与新鲜证据要求
- 增加追溯矩阵和测试设计种子
- 增加评审前自检
- 明确 `task-progress` 字段映射与 handoff 文案

## 预期效果

优化后的 `ahe-tasks` 应该具备这些特征：

- 不是只“列出任务”，而是产出可直接执行和评审的任务计划
- 更容易通过 `ahe-tasks-review`
- 更容易让 `ahe-test-driven-dev` 在单任务推进时少补脑、少返工
- 更稳定地把规格、设计、任务、实现四层串起来
