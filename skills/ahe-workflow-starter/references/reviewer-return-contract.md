# Reviewer Return Contract

## 目的

这份协议定义 reviewer subagent 评审完成后，回传给父会话的最小结构化摘要。

## 最小返回格式

```json
{
  "conclusion": "通过|需修改|阻塞",
  "next_action": "推荐下一步 skill 或动作",
  "record_path": "实际写入的 review 记录路径",
  "key_findings": [
    "关键发现 1",
    "关键发现 2"
  ],
  "needs_human_confirmation": false,
  "reroute_via_starter": false
}
```

## 字段说明

| 字段 | 说明 |
| --- | --- |
| `conclusion` | 当前 review 的正式结论 |
| `next_action` | reviewer 基于当前结果建议的下一步 |
| `record_path` | 已写入的 review 记录路径 |
| `key_findings` | 父会话需要向用户展示或用于回修的关键发现 |
| `needs_human_confirmation` | 是否必须由父会话继续发起真人确认 |
| `reroute_via_starter` | 是否要求先回到 `ahe-workflow-starter` 重编排 |

## 使用规则

### `conclusion`

只能使用：

- `通过`
- `需修改`
- `阻塞`

### `next_action`

优先返回 canonical `ahe-*` skill ID，或保留节点：

- `ahe-specify`
- `ahe-spec-review`
- `规格真人确认`
- `ahe-design`
- `ahe-design-review`
- `设计真人确认`
- `ahe-tasks`
- `ahe-tasks-review`
- `ahe-test-driven-dev`
- `ahe-bug-patterns`
- `ahe-test-review`
- `ahe-code-review`
- `ahe-traceability-review`
- `ahe-regression-gate`
- `ahe-completion-gate`
- `ahe-finalize`
- `ahe-workflow-starter`

### `needs_human_confirmation`

通常按以下约定：

| review skill | 默认值 |
| --- | --- |
| `ahe-spec-review` | `true` |
| `ahe-design-review` | `true` |
| `ahe-tasks-review` | `false` |
| `ahe-test-review` | `false` |
| `ahe-code-review` | `false` |
| `ahe-traceability-review` | `false` |

### `reroute_via_starter`

以下情况建议返回 `true`：

- 当前 review 暴露出缺少上游已批准工件
- 当前输入证据与 profile / stage 明显冲突
- 当前问题本质上需要回到 `ahe-workflow-starter` 重新决定分支

## 父会话消费规则

父会话收到该摘要后，按以下顺序处理：

1. 若 `reroute_via_starter=true`，先经 `ahe-workflow-starter` 重编排。
2. 否则若 `conclusion=通过` 且 `needs_human_confirmation=true`，进入真人确认。
3. 否则若 `conclusion=通过` 且无需真人确认，进入 `next_action`。
4. 否则若 `conclusion=需修改` 或 `阻塞`，按 `next_action` 回修或补条件。

## 边界

这个 return contract 只定义“reviewer 回给父会话的摘要”，不替代 review 记录正文。

review 正文仍应按各 `ahe-*review` skill 自身要求写入仓库路径。
