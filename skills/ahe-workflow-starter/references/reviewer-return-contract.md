# Reviewer Return Contract

## 目的

这份协议定义 reviewer subagent 评审完成后，回传给父会话的最小结构化摘要。

## 最小返回格式

```json
{
  "conclusion": "通过|需修改|阻塞",
  "next_action_or_recommended_skill": "推荐下一步 canonical 节点",
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
| `next_action_or_recommended_skill` | reviewer 基于当前结果建议的下一步 canonical handoff |
| `record_path` | 已写入的 review 记录路径 |
| `key_findings` | 父会话需要向用户展示或用于回修的关键发现 |
| `needs_human_confirmation` | 是否必须由父会话继续发起真人确认 |
| `reroute_via_starter` | 兼容字段名；若为 `true`，父会话应先回到 `ahe-workflow-router` 重编排 |

## 使用规则

### `conclusion`

只能使用：

- `通过`
- `需修改`
- `阻塞`

### `next_action_or_recommended_skill`

优先返回 canonical `ahe-*` skill ID，或保留节点：

- `ahe-specify`
- `ahe-spec-review`
- `规格真人确认`
- `ahe-design`
- `ahe-design-review`
- `设计真人确认`
- `ahe-tasks`
- `ahe-tasks-review`
- `任务真人确认`
- `ahe-test-driven-dev`
- `ahe-bug-patterns`
- `ahe-test-review`
- `ahe-code-review`
- `ahe-traceability-review`
- `ahe-regression-gate`
- `ahe-completion-gate`
- `ahe-finalize`
- `ahe-hotfix`
- `ahe-increment`
- `ahe-workflow-router`

这个字段是 reviewer 摘要层对仓库 canonical 字段 `Next Action Or Recommended Skill` 的结构化映射。

它必须是一个唯一的 canonical 值，不得把多个候选动作拼成一个字符串。

命名规则：

- live reviewer skills 与相关文档统一使用 `next_action_or_recommended_skill`
- reviewer 摘要必须直接返回该字段，不再使用旧字段别名

### `needs_human_confirmation`

只在 `conclusion=通过` 且当前 review 节点要求真人确认时，才把这个字段设为 `true`。

若 `conclusion=需修改` 或 `阻塞`，默认返回 `false`，并由 `next_action_or_recommended_skill` 指向回修或重编排节点。

`conclusion=通过` 时，通常按以下约定：

| review skill | `conclusion=通过` 时默认值 |
| --- | --- |
| `ahe-spec-review` | `true` |
| `ahe-design-review` | `true` |
| `ahe-tasks-review` | `true` |
| `ahe-test-review` | `false` |
| `ahe-code-review` | `false` |
| `ahe-traceability-review` | `false` |

### `reroute_via_starter`

以下情况建议返回 `true`：

- 当前 review 暴露出缺少上游已批准工件
- 当前输入证据与 profile / stage 明显冲突
- 当前问题本质上需要回到 `ahe-workflow-router` 重新决定分支

说明：

- `reroute_via_starter` 当前仍保留为兼容字段名
- 但它的 canonical 语义已经是“父会话重新进入 `ahe-workflow-router`”

## 父会话消费规则

父会话收到该摘要后，先检查 `references/execution-semantics.md` 中定义的暂停点与“先向用户展示”的义务，再按以下顺序处理：

1. 若 `reroute_via_starter=true`，先经 `ahe-workflow-router` 重编排。
2. 否则若 `conclusion=通过` 且 `needs_human_confirmation=true`，进入真人确认。
3. 否则若 `conclusion=通过` 且无需真人确认，进入 `next_action_or_recommended_skill`。
4. 否则若 `conclusion=需修改` 或 `阻塞`，按 `next_action_or_recommended_skill` 回修或补条件。

补充理解：

- 对 `ahe-spec-review` / `ahe-design-review`，`需修改` 与内容回修型 `阻塞` 仍受暂停点约束，父会话需先向用户展示评审结论与修订重点
- 对 `ahe-spec-review` / `ahe-design-review`，若 `阻塞` 且需要经 router 重编排，父会话需先向用户展示阻塞原因，再回到 `ahe-workflow-router`
- 对其他 review / gate，若修订方向不明确，也应先与用户讨论，而不是机械自动推进

## 边界

这个 return contract 只定义“reviewer 回给父会话的摘要”，不替代 review 记录正文。

review 正文仍应按各 `ahe-*review` skill 自身要求写入仓库路径。
