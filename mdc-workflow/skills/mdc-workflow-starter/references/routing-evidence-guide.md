# 路由证据指南

当项目已采用这套 skills 作业体系，但尚未统一工件布局或路由证据时，可使用本指南。

本指南回答 3 个问题：

1. 路由时优先看什么。
2. 什么证据算有效，什么证据不够。
3. 当证据冲突时，应该保守地退回到哪里。

## 推荐工件布局

除非项目已有已批准的等价路径，否则默认按 artifact model 组织理解：

| 类别 | 推荐路径 | 说明 |
|---|---|---|
| `baseline artifacts` | 已批准 `docs/specs/`、已批准 `docs/designs/`、稳定团队规范 | 定义当前长期事实 |
| `change workspace` | 当前变更对应的 spec / design delta、`docs/tasks/`、`task-progress.md`、`docs/reviews/`、`docs/verification/`、`RELEASE_NOTES.md` | 承载当前在制工作 |
| `archive` | 团队约定的归档目录或历史 review / verification / release 记录 | 保存已完成 change 的闭环证据 |

## 最小路由证据

优先使用项目已有工件，不要额外依赖根目录 JSON 信号文件。

推荐的路由证据包括：

- 当前 change workspace 中需求规格、设计文档、任务计划的批准状态
- `task-progress.md` 这类进度记录
- `docs/reviews/` 下的评审记录
- `docs/verification/` 下的验证记录
- 用户明确提出的变更请求或热修复请求

## 路由时的证据优先级

在会话开始时，`mdc-workflow-starter` 应按以下顺序判断：

1. `AGENTS.md` 中与 `mdc-workflow` 相关的 artifact 映射与审批约定
2. 当前 change workspace 的规格 / 设计 / 任务工件存在情况与批准状态
3. `task-progress.md`
4. `docs/reviews/`
5. `docs/verification/`
6. `RELEASE_NOTES.md`
7. 必要时读取 archive 中最近一次闭环记录
8. 用户当前请求

若较高优先级工件与较低优先级工件冲突，应优先相信更基础、更上游的工件状态。

## 推荐路由输入

在会话开始时，`mdc-workflow-starter` 应优先只检查：

1. `AGENTS.md` 中的 `mdc-workflow` 配置段，先识别 baseline / change workspace / archive 的映射
2. 当前请求归属的 `change workspace` 是什么，是否是继续已有 workspace 或新建 workspace
3. 当前 change workspace 的规格 / 设计 / 任务工件存在情况和批准状态
4. 当前 workspace 下的进度、评审、验证、发布与收尾记录
5. 仍然有效的 baseline artifacts
6. 仅在需要恢复历史闭环时读取 archive 记录
7. 用户当前请求

在完成阶段路由前，避免大范围代码探索。

## 哪些证据不够

以下情况默认不能视为已批准或可继续下游：

- 聊天里说“这个已经确认过了”，但工件中没有对应证据
- 只存在草稿文档，没有状态字段或批准记录
- review 结论是 `通过`，但没有真人确认
- `task-progress.md` 写着“继续实现”，但规格 / 设计 / 任务工件没有批准证据
- 只凭 `RELEASE_NOTES.md` 或零散提交信息推断阶段已经结束

## 批准信号

优先寻找显式批准标记，例如：

- 若 `AGENTS.md` 已声明项目别名，优先采用其中的 approved / pass / revise / blocked 映射
- `状态: 已批准`
- 兼容旧写法：`Status: Approved`
- 带有 `通过` 结论的评审章节
- 兼容旧写法：带有 `PASS` 结论的评审章节
- 进度或验证记录中的阶段标记

对规格和设计而言，仅有评审通过还不够；还应能看出真人确认已经完成。

如果批准状态不明确，应回路由到上游评审 skill，而不是直接假设已批准。

补充判断：

- 规格评审通过但缺少真人确认，不算已批准，应继续按需求阶段处理
- 设计评审通过但缺少真人确认，不算已批准，应继续按设计阶段处理

## 证据冲突时的保守规则

出现以下冲突时，采用保守处理：

- `task-progress.md` 显示“进入实现”，但任务计划没有批准证据
- 评审记录显示 `通过`，但工件状态仍是草稿
- 用户说“继续编码”，但更上游工件仍未批准

保守处理原则：

1. 不选择更激进的下游阶段
2. 回到更上游、证据更完整的阶段
3. 在路由输出中显式说明冲突点和处理方式

## review-only 场景的证据示例

- 用户明确要求“只做规格评审”：
  - 需求规格草稿存在
  - 当前请求仅要求 review
  - 路由到 `mdc-spec-review`
- 用户明确要求“只做设计评审”：
  - 设计草稿存在
  - 当前请求仅要求 review
  - 路由到 `mdc-design-review`
- 用户明确要求“只做任务评审”：
  - 任务计划草稿存在
  - 当前请求仅要求 review
  - 路由到 `mdc-tasks-review`

## 变更 / 热修场景的证据示例

- increment：
  - 用户明确提出新增、删改需求
  - 或现有工件表明范围 / 验收标准变化
  - 路由到 `mdc-increment`
- hotfix：
  - 用户明确提出紧急缺陷修复
  - 或验证结果表明已有线上 / 交付前缺陷
  - 路由到 `mdc-hotfix`

## 主链流程

```text
mdc-workflow-starter
-> mdc-specify
-> mdc-spec-review
-> 规格真人确认
-> mdc-design
-> mdc-design-review
-> 设计真人确认
-> mdc-tasks
-> mdc-tasks-review
-> mdc-implement
-> mdc-bug-patterns
-> mdc-test-review
-> mdc-code-review
-> mdc-traceability-review
-> mdc-regression-gate
-> mdc-completion-gate
-> mdc-finalize
```

## 支线流程

- 明确的变更请求 -> `mdc-increment`
- 明确的热修复请求 -> `mdc-hotfix`

两条支线都必须把项目带回正确的评审或实现阶段，不能绕过主链纪律。
