---
name: mdc-increment
description: 在不绕过规格与设计纪律的前提下处理 MDC 项目的需求变更。适用于存在 `change-request.json`、用户明确要求增删改需求，或已批准范围发生变化、必须在继续实现前先同步更新的场景。
---

# MDC 增量变更

在不破坏主 MDC 流程的前提下处理需求变更。

## 目的

这个 skill 处理以下变更请求：

- 新增需求
- 修改范围
- 修改验收标准
- 重新纳入之前延期的工作

它的作用是防止“随手改需求”直接渗透到设计或实现层。

## 硬性门禁

不要从变更请求直接跳进编码。

任何变更都必须先分析它对规格、设计和任务计划的影响。

## 前置条件

在以下情况下使用本 skill：

- 存在 `change-request.json`
- 用户明确要求修改已批准范围或需求

## 工作流

### 1. 阅读变更请求

阅读：

- 变更请求本身
- 已批准需求规格
- 已批准设计
- 当前任务计划（如有）

明确：

- 具体变了什么
- 哪些内容仍然有效
- 哪些工件会受影响

### 2. 执行影响分析

评估对以下内容的影响：

- 范围与需求
- 约束或验收标准
- 架构或接口
- 任务顺序与依赖
- 已完成实现

对变更进行分类：

- 仅更新规格
- 更新规格与设计
- 更新规格、设计与任务计划
- 已实现行为因此失效

### 3. 更新正确的工件

用最小必要改动保持各类工件一致。

规则如下：

- 需求变更先落到需求规格
- 只有当需求变化影响“如何实现”时，才继续更新设计
- 只有当设计或范围变化影响执行时，才更新任务计划

### 4. 路由回正确阶段

更新完成后：

- if the spec changed materially and needs re-review -> `mdc-spec-review`
- if the design changed materially and needs re-review -> `mdc-design-review`
- if only task sequencing changed -> `mdc-tasks-review`
- if all relevant docs remain approved -> return to the appropriate implementation phase

## 输出格式

请严格使用以下结构：

```markdown
## Change Summary

- summary

## Impact

- affected artifact

## Required Updates

- update

## Next Step

`mdc-spec-review` | `mdc-design-review` | `mdc-tasks-review` | `mdc-implement`
```

## 反模式

- 先改实现，后补文档
- 把需求变更误当成单纯任务调整
- 范围发生实质变化后，仍假定旧批准有效
- 让多个工件处于不同步状态

## 完成条件

只有在变更已完成分析、受影响工件已更新或被明确标记待更新，并且已经选定唯一正确下一步之后，这个 skill 才算完成。
