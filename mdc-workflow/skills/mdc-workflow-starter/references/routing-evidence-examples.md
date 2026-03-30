# 路由证据示例

这份文件提供一组轻量示例，适用于不依赖根目录 JSON 信号文件的项目。

当前建议是：不要依赖根目录 JSON 信号文件做路由。

更推荐使用以下证据来源：

- 当前 change workspace 中的规格 / 设计 / 任务工件
- `task-progress.md` 这类进度记录
- `docs/reviews/` 下的评审记录
- `docs/verification/` 下的验证记录
- 当前仍有效的 baseline artifacts
- 仅在需要恢复历史闭环时读取的 archive 记录
- 用户明确表达的变更或热修复意图

## 推荐替代方式

### 进度记录示例

```markdown
## 当前阶段

- workspace: feature-export-csv
- phase: implement
- 活跃任务: TASK-003
- next skill: mdc-bug-patterns

## baseline artifacts

- 需求规格: 已批准
- 设计文档: 已批准

## change workspace

- 任务计划: 已批准
- review: test-review-TASK-003.md
- verification: regression-TASK-003.md
```

### 变更请求示例

```markdown
## 变更摘要

- requested by:
- requested at:
- summary:

## 影响范围

- requirement spec
- design doc
- task plan
```

### 热修复请求示例

```markdown
## 热修复摘要

- severity:
- summary:
- expected behavior:
- actual behavior:
- impact:
```

### archive 不能当当前批准依据的示例

```markdown
## archive snapshot

- workspace: feature-old-export
- spec review: PASS
- finalized at: 2026-03-10

## current workspace

- workspace: feature-new-export
- spec: 草稿
- design: 不存在
```

这种情况下，archive 只能说明“以前有个已完成 change”，不能把它当作当前 workspace 已批准的直接证据。

### starter 内部 payload 示例

```markdown
- currentWorkspace: feature-export-csv
- currentProfile: standard
- currentNode: mdc-code-review
- blockedNodes: mdc-finalize
- blockingReasons: 缺少 traceability review 与 regression evidence
- requiredReads: task-progress.md, code-review-TASK-003.md, relevant design section
- expectedWrites: docs/reviews/code-review-TASK-003.md, task-progress.md
- writesScope: change workspace
```

## 推荐处理规则

1. 优先更新现有项目工件，而不是新增额外路由文件
2. 让路由证据尽量靠近它描述的交付物
3. 避免保留会误导路由的过期旁路触发文件
