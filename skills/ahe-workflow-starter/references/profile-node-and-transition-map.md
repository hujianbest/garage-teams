# Profile Node And Transition Map

这份参考文档集中保存 `ahe-workflow-router` 的 profile 合法节点集合、canonical route map、结果驱动迁移表与恢复编排协议。

当你已经在 starter 主文件中确认：

- 当前请求属于 workflow 场景
- 当前 profile 已确定
- 需要查合法节点、默认链路或结论后的默认下一步

再来这里读取细节。

## 合法状态集合

### full profile 主链推荐节点

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

### standard profile 主链推荐节点

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

### lightweight profile 主链推荐节点

- `ahe-tasks`
- `ahe-tasks-review`
- `任务真人确认`
- `ahe-test-driven-dev`
- `ahe-regression-gate`
- `ahe-completion-gate`
- `ahe-finalize`

### 支线推荐节点

- `ahe-increment`
- `ahe-hotfix`

如果某个用户请求、口头描述或局部记录暗示跳到当前 profile 合法集合之外，按无效迁移处理，回到最近一个有证据支撑的上游节点，或触发 profile 升级。

## Canonical Route Map

把下列主骨架视为默认路由图；任何实际迁移都必须同时满足 profile 合法集合、批准证据和迁移表规则：

```text
full:
  ahe-specify -> ahe-spec-review -> 规格真人确认
  -> ahe-design -> ahe-design-review -> 设计真人确认
  -> ahe-tasks -> ahe-tasks-review -> 任务真人确认 -> ahe-test-driven-dev
  -> ahe-bug-patterns -> ahe-test-review -> ahe-code-review
  -> ahe-traceability-review -> ahe-regression-gate
  -> ahe-completion-gate -> ahe-finalize

standard:
  ahe-tasks -> ahe-tasks-review -> 任务真人确认 -> ahe-test-driven-dev
  -> ahe-bug-patterns -> ahe-test-review -> ahe-code-review
  -> ahe-traceability-review -> ahe-regression-gate
  -> ahe-completion-gate -> ahe-finalize

lightweight:
  ahe-tasks -> ahe-tasks-review -> 任务真人确认 -> ahe-test-driven-dev
  -> ahe-regression-gate -> ahe-completion-gate -> ahe-finalize

branches:
  increment -> ahe-increment -> return via router
  hotfix -> ahe-hotfix -> return via router
```

## 结果驱动迁移表

把 review / gate 结论视为显式迁移信号，而不是普通建议。

### full profile 迁移表

| 当前节点 | 结论 | 下一推荐节点 |
|---|---|---|
| `ahe-spec-review` | `通过` | 规格真人确认 |
| `ahe-spec-review` | `需修改` / `阻塞` | `ahe-specify` |
| `ahe-spec-review` | `阻塞`（需重编排） | `ahe-workflow-router` |
| 规格真人确认 | 确认通过 | `ahe-design` |
| 规格真人确认 | 要求修改 / 未确认 | `ahe-specify` |
| `ahe-design-review` | `通过` | 设计真人确认 |
| `ahe-design-review` | `需修改` / `阻塞` | `ahe-design` |
| `ahe-design-review` | `阻塞`（需重编排） | `ahe-workflow-router` |
| 设计真人确认 | 确认通过 | `ahe-tasks` |
| 设计真人确认 | 要求修改 / 未确认 | `ahe-design` |
| `ahe-tasks-review` | `通过` | 任务真人确认 |
| `ahe-tasks-review` | `需修改` / `阻塞` | `ahe-tasks` |
| `ahe-tasks-review` | `阻塞`（需重编排） | `ahe-workflow-router` |
| 任务真人确认 | 确认通过 | `ahe-test-driven-dev` |
| 任务真人确认 | 要求修改 / 未确认 | `ahe-tasks` |
| `ahe-test-driven-dev` | 实现完成 | `ahe-bug-patterns` |
| `ahe-bug-patterns` | `通过` | `ahe-test-review` |
| `ahe-bug-patterns` | `需修改` / `阻塞` | `ahe-test-driven-dev` |
| `ahe-test-review` | `通过` | `ahe-code-review` |
| `ahe-test-review` | `需修改` / `阻塞` | `ahe-test-driven-dev` |
| `ahe-code-review` | `通过` | `ahe-traceability-review` |
| `ahe-code-review` | `需修改` / `阻塞` | `ahe-test-driven-dev` |
| `ahe-traceability-review` | `通过` | `ahe-regression-gate` |
| `ahe-traceability-review` | `需修改` / `阻塞` | `ahe-test-driven-dev` |
| `ahe-regression-gate` | `通过` | `ahe-completion-gate` |
| `ahe-regression-gate` | `需修改` / `阻塞` | `ahe-test-driven-dev` |
| `ahe-completion-gate` | `通过` | `ahe-finalize` |
| `ahe-completion-gate` | `需修改` / `阻塞` | `ahe-test-driven-dev` |

### standard profile 迁移表

| 当前节点 | 结论 | 下一推荐节点 |
|---|---|---|
| `ahe-tasks-review` | `通过` | 任务真人确认 |
| `ahe-tasks-review` | `需修改` / `阻塞` | `ahe-tasks` |
| `ahe-tasks-review` | `阻塞`（需重编排） | `ahe-workflow-router` |
| 任务真人确认 | 确认通过 | `ahe-test-driven-dev` |
| 任务真人确认 | 要求修改 / 未确认 | `ahe-tasks` |
| `ahe-test-driven-dev` | 实现完成 | `ahe-bug-patterns` |
| `ahe-bug-patterns` | `通过` | `ahe-test-review` |
| `ahe-bug-patterns` | `需修改` / `阻塞` | `ahe-test-driven-dev` |
| `ahe-test-review` | `通过` | `ahe-code-review` |
| `ahe-test-review` | `需修改` / `阻塞` | `ahe-test-driven-dev` |
| `ahe-code-review` | `通过` | `ahe-traceability-review` |
| `ahe-code-review` | `需修改` / `阻塞` | `ahe-test-driven-dev` |
| `ahe-traceability-review` | `通过` | `ahe-regression-gate` |
| `ahe-traceability-review` | `需修改` / `阻塞` | `ahe-test-driven-dev` |
| `ahe-regression-gate` | `通过` | `ahe-completion-gate` |
| `ahe-regression-gate` | `需修改` / `阻塞` | `ahe-test-driven-dev` |
| `ahe-completion-gate` | `通过` | `ahe-finalize` |
| `ahe-completion-gate` | `需修改` / `阻塞` | `ahe-test-driven-dev` |

### lightweight profile 迁移表

| 当前节点 | 结论 | 下一推荐节点 |
|---|---|---|
| `ahe-tasks-review` | `通过` | 任务真人确认 |
| `ahe-tasks-review` | `需修改` / `阻塞` | `ahe-tasks` |
| `ahe-tasks-review` | `阻塞`（需重编排） | `ahe-workflow-router` |
| 任务真人确认 | 确认通过 | `ahe-test-driven-dev` |
| 任务真人确认 | 要求修改 / 未确认 | `ahe-tasks` |
| `ahe-test-driven-dev` | 实现完成 | `ahe-regression-gate` |
| `ahe-regression-gate` | `通过` | `ahe-completion-gate` |
| `ahe-regression-gate` | `需修改` / `阻塞` | `ahe-test-driven-dev` |
| `ahe-completion-gate` | `通过` | `ahe-finalize` |
| `ahe-completion-gate` | `需修改` / `阻塞` | `ahe-test-driven-dev` |

如果某个下游 skill 给出的结论无法映射到当前 profile 迁移表中的唯一下一推荐节点，则说明编排信息还不完整，应回到 `ahe-workflow-router` 重新判断，而不是自行补脑推进。

上表主要描述“内容回修型”默认迁移。若 reviewer 返回摘要显式要求 `reroute_via_starter=true`，或把 `next_action_or_recommended_skill` 指向 `ahe-workflow-router`，该显式重编排信号优先于表内默认下一步。

## 恢复编排协议

当某个节点完成后，按以下顺序恢复状态机：

1. 读取该节点的最新结论
2. 确认当前 workflow profile（从 `task-progress.md` 读取）
3. 若 `task-progress.md` 或等价工件已经写入合法或可归一化的 `Next Action Or Recommended Skill`，且它来自上一个已完成节点并与最新证据不冲突，优先采用这个显式下一步
4. 否则检查该结论对应的上游 / 下游迁移是否在当前 profile 迁移表中有明确规则
5. 根据当前会话上下文判断用户是否已经提出了新范围、新缺陷或新阻塞（基于已有信息判断，不主动询问用户）
6. 若有范围变化，优先判断是否切到 `ahe-increment`
7. 若有紧急缺陷，优先判断是否切到 `ahe-hotfix`
8. 若没有新的支线信号，则按当前 profile 迁移表进入唯一下一推荐节点

不要跳过第 2 步、第 3 步和第 4 步。

恢复编排完成后，若下一推荐节点不是暂停点，立刻在同一轮中进入该节点，不等待用户确认。

若该下一推荐节点是 review 节点，则“进入该节点”的含义是：按 `references/review-dispatch-protocol.md` 派发 reviewer subagent，并按 `references/reviewer-return-contract.md` 消费返回摘要，而不是在父会话内联执行 review。
