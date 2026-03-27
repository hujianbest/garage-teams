# 路由证据指南

当项目已采用这套 skills 作业体系，但尚未统一工件布局或路由证据时，可使用本指南。

## 推荐工件布局

除非项目已有已批准的等价路径，否则默认使用以下布局：

| 逻辑工件 | 推荐路径 | 说明 |
|---|---|---|
| 需求规格 | `docs/specs/YYYY-MM-DD-<topic>-srs.md` | 定义做什么 |
| 设计文档 | `docs/designs/YYYY-MM-DD-<topic>-design.md` | 定义怎么做 |
| 任务计划 | `docs/tasks/YYYY-MM-DD-<topic>-tasks.md` | 定义执行顺序 |
| 进度记录 | `task-progress.md` | 支撑跨会话连续推进 |
| 发布说明 | `RELEASE_NOTES.md` | 面向用户的变更说明 |
| 评审记录 | `docs/reviews/` | 可选但建议提供 |
| 验证记录 | `docs/verification/` | 可选但建议提供 |

## 最小路由证据

优先使用项目已有工件，不要额外依赖根目录 JSON 信号文件。

推荐的路由证据包括：

- 需求规格、设计文档、任务计划的批准状态
- `task-progress.md` 这类进度记录
- `docs/reviews/` 下的评审记录
- `docs/verification/` 下的验证记录
- 用户明确提出的变更请求或热修复请求

## 推荐路由输入

在会话开始时，`mdc-workflow-starter` 应优先只检查：

1. 作业合同
2. 规格 / 设计 / 任务工件的存在情况和批准状态
3. 进度、评审和验证记录
4. 用户当前请求

在完成阶段路由前，避免大范围代码探索。

## 批准信号

优先寻找显式批准标记，例如：

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
