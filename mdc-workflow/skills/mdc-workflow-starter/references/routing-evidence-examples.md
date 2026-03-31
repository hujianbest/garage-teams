# 路由证据示例

这份文件提供一组轻量示例，适用于不依赖根目录 JSON 信号文件的项目。

当前建议是：不要依赖根目录 JSON 信号文件做路由。

更推荐使用以下证据来源：

- 已批准的规格 / 设计 / 任务工件
- `task-progress.md` 这类进度记录
- `docs/reviews/` 下的评审记录
- `docs/verification/` 下的验证记录
- 用户明确表达的变更或热修复意图

## 推荐替代方式

### 进度记录示例

```markdown
## 当前阶段

- phase: implement
- 活跃任务: TASK-003
- next skill: mdc-bug-patterns

## 已批准工件

- 需求规格: 已批准
- 设计文档: 已批准
- 任务计划: 已批准
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

## 推荐处理规则

1. 优先更新现有项目工件，而不是新增额外路由文件
2. 让路由证据尽量靠近它描述的交付物
3. 避免保留会误导路由的过期旁路触发文件
