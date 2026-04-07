# Review Dispatch Protocol

## 目的

这份协议说明 `ahe-workflow-router` 与各上游产出 skill 在遇到 review 节点时，如何把评审动作派发给独立 reviewer subagent，而不是在父会话里内联执行 review。

## 核心原则

1. review 节点仍然是 workflow 的 canonical 节点。
2. 进入 review 节点时，父会话不直接执行评审判断。
3. 父会话要构造 review request，并启动独立 reviewer subagent。
4. reviewer subagent 在 fresh context 中读取对应 `ahe-*review` skill 与最小必要工件。
5. reviewer subagent 负责写 review 记录并回传结构化摘要。
6. 父会话消费该摘要，继续主链推进或进入真人确认。

其中 reviewer 摘要里的 canonical handoff 字段应与 family vocabulary 对齐，统一使用 `next_action_or_recommended_skill`。

## 当前适用节点

| Canonical review 节点 | reviewer subagent 调用的 skill |
| --- | --- |
| `ahe-spec-review` | `ahe-spec-review` |
| `ahe-design-review` | `ahe-design-review` |
| `ahe-tasks-review` | `ahe-tasks-review` |
| `ahe-test-review` | `ahe-test-review` |
| `ahe-code-review` | `ahe-code-review` |
| `ahe-traceability-review` | `ahe-traceability-review` |

## review request 最小字段

建议父会话至少构造以下字段：

```json
{
  "review_type": "spec|design|tasks|test|code|traceability",
  "review_skill": "ahe-xxx-review",
  "topic": "本次评审主题",
  "artifact_paths": [
    "被检视交付件路径"
  ],
  "supporting_context_paths": [
    "最小必要辅助上下文路径"
  ],
  "expected_record_path": "docs/reviews/... 或项目映射路径",
  "current_profile": "full|standard|lightweight"
}
```

## 父会话职责

父会话负责：

- 判断当前是否应进入 review 节点
- 选择正确的 review skill
- 组装最小 review request
- 启动 reviewer subagent
- 消费 reviewer 返回摘要
- 在需要时发起真人确认
- 根据摘要继续推进或回流修订

父会话在消费 reviewer 摘要时，应直接读取 `next_action_or_recommended_skill` 并进入迁移判断。

父会话不负责：

- 在当前上下文直接执行 review 判断
- 代替 reviewer 写 review 记录

## reviewer subagent 职责

reviewer subagent 负责：

- 读取对应 `ahe-*review` skill
- 读取 review request 指定的最小必要工件
- 按 skill 要求执行评审
- 把评审记录写到约定路径
- 按统一 return contract 回传摘要

reviewer subagent 不负责：

- 推进整个 workflow 到下一主链节点
- 代替父会话做真人确认

## Human confirmation 归属

以下场景中，reviewer 只返回“已经达到可确认状态”，真人确认动作仍由父会话执行：

- `ahe-spec-review`
- `ahe-design-review`
- `ahe-tasks-review`

## 失败与重编排

如果 reviewer 发现当前问题不是简单回修，而是：

- 缺少上游已批准工件
- 当前 profile 不再成立
- 当前 review 输入与 workflow 状态冲突

则 reviewer 应在返回摘要中明确要求父会话经 `ahe-workflow-router` 重编排，而不是让下游 skill 自行补位推进。
