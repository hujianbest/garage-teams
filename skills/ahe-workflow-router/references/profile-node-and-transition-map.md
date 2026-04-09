# Profile Node And Transition Map

这份参考文档集中保存 `ahe-workflow-router` 的 profile 合法节点集合、canonical route map、结果驱动迁移表与恢复编排协议。

当你已经在 router 主文件（`skills/ahe-workflow-router/SKILL.md`）中确认：

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

## Execution Mode Does Not Change The Route Map

`Execution Mode` 只影响 approval step 的解决方式，不改变 profile 的合法节点集合：

- `interactive`：`规格真人确认` / `设计真人确认` / `任务真人确认` 表现为等待用户输入的 approval node
- `auto`：同样保留这些 approval node，但要求先写 approval record，再解锁下游节点
- 不允许把 `ahe-spec-review -> ahe-design`、`ahe-design-review -> ahe-tasks`、`ahe-tasks-review -> ahe-test-driven-dev` 直接折叠成“跳过确认节点”

## Canonical Route Map

把下列主骨架视为默认路由图；任何实际迁移都必须同时满足 profile 合法集合、批准证据和迁移表规则：

```text
full:
  ahe-specify -> ahe-spec-review -> 规格真人确认
  -> ahe-design -> ahe-design-review -> 设计真人确认
  -> ahe-tasks -> ahe-tasks-review -> 任务真人确认 -> ahe-test-driven-dev
  -> ahe-bug-patterns -> ahe-test-review -> ahe-code-review
  -> ahe-traceability-review -> ahe-regression-gate -> ahe-completion-gate
  -> if unique next-ready task exists: ahe-workflow-router -> ahe-test-driven-dev
  -> else: ahe-finalize

standard:
  ahe-tasks -> ahe-tasks-review -> 任务真人确认 -> ahe-test-driven-dev
  -> ahe-bug-patterns -> ahe-test-review -> ahe-code-review
  -> ahe-traceability-review -> ahe-regression-gate -> ahe-completion-gate
  -> if unique next-ready task exists: ahe-workflow-router -> ahe-test-driven-dev
  -> else: ahe-finalize

lightweight:
  ahe-tasks -> ahe-tasks-review -> 任务真人确认 -> ahe-test-driven-dev
  -> ahe-regression-gate -> ahe-completion-gate
  -> if unique next-ready task exists: ahe-workflow-router -> ahe-test-driven-dev
  -> else: ahe-finalize

branches:
  increment -> ahe-increment -> return via router
  hotfix -> ahe-hotfix -> return via router
```

说明：

- `ahe-test-driven-dev` 到 `ahe-completion-gate` 描述的是“单个 `Current Active Task` 的实现与质量闭环”
- `ahe-completion-gate` 返回 `通过` 后，不默认等于“整个 workflow 已完成”；父会话必须先判断是否仍有 approved 且 dependency-ready 的剩余任务
- 若存在唯一 `next-ready task`，先回到 `ahe-workflow-router` 锁定新的 `Current Active Task`，再重新进入 `ahe-test-driven-dev`
- 只有在没有剩余任务时，才进入 `ahe-finalize`

## 结果驱动迁移表

把 review / gate 结论视为显式迁移信号，而不是普通建议。

### full profile 迁移表

| 当前节点 | 结论 | 下一推荐节点 |
|---|---|---|
| `ahe-spec-review` | `通过` | 规格真人确认 |
| `ahe-spec-review` | `需修改` / `阻塞` | `ahe-specify` |
| `ahe-spec-review` | `阻塞`（需重编排） | `ahe-workflow-router` |
| 规格真人确认 | approval step 完成 | `ahe-design` |
| 规格真人确认 | 要求修改 / approval step 未完成 | `ahe-specify` |
| `ahe-design-review` | `通过` | 设计真人确认 |
| `ahe-design-review` | `需修改` / `阻塞` | `ahe-design` |
| `ahe-design-review` | `阻塞`（需重编排） | `ahe-workflow-router` |
| 设计真人确认 | approval step 完成 | `ahe-tasks` |
| 设计真人确认 | 要求修改 / approval step 未完成 | `ahe-design` |
| `ahe-tasks-review` | `通过` | 任务真人确认 |
| `ahe-tasks-review` | `需修改` / `阻塞` | `ahe-tasks` |
| `ahe-tasks-review` | `阻塞`（需重编排） | `ahe-workflow-router` |
| 任务真人确认 | approval step 完成 | `ahe-test-driven-dev` |
| 任务真人确认 | 要求修改 / approval step 未完成 | `ahe-tasks` |
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
| `ahe-completion-gate` | `通过`（仍有唯一 next-ready task） | `ahe-workflow-router` |
| `ahe-completion-gate` | `通过`（主链任务全部完成） | `ahe-finalize` |
| `ahe-completion-gate` | `通过`（仍有剩余任务，但下一任务不唯一或 ready 判定冲突） | `ahe-workflow-router` |
| `ahe-completion-gate` | `需修改` / `阻塞` | `ahe-test-driven-dev` |

### standard profile 迁移表

| 当前节点 | 结论 | 下一推荐节点 |
|---|---|---|
| `ahe-tasks-review` | `通过` | 任务真人确认 |
| `ahe-tasks-review` | `需修改` / `阻塞` | `ahe-tasks` |
| `ahe-tasks-review` | `阻塞`（需重编排） | `ahe-workflow-router` |
| 任务真人确认 | approval step 完成 | `ahe-test-driven-dev` |
| 任务真人确认 | 要求修改 / approval step 未完成 | `ahe-tasks` |
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
| `ahe-completion-gate` | `通过`（仍有唯一 next-ready task） | `ahe-workflow-router` |
| `ahe-completion-gate` | `通过`（主链任务全部完成） | `ahe-finalize` |
| `ahe-completion-gate` | `通过`（仍有剩余任务，但下一任务不唯一或 ready 判定冲突） | `ahe-workflow-router` |
| `ahe-completion-gate` | `需修改` / `阻塞` | `ahe-test-driven-dev` |

### lightweight profile 迁移表

| 当前节点 | 结论 | 下一推荐节点 |
|---|---|---|
| `ahe-tasks-review` | `通过` | 任务真人确认 |
| `ahe-tasks-review` | `需修改` / `阻塞` | `ahe-tasks` |
| `ahe-tasks-review` | `阻塞`（需重编排） | `ahe-workflow-router` |
| 任务真人确认 | approval step 完成 | `ahe-test-driven-dev` |
| 任务真人确认 | 要求修改 / approval step 未完成 | `ahe-tasks` |
| `ahe-test-driven-dev` | 实现完成 | `ahe-regression-gate` |
| `ahe-regression-gate` | `通过` | `ahe-completion-gate` |
| `ahe-regression-gate` | `需修改` / `阻塞` | `ahe-test-driven-dev` |
| `ahe-completion-gate` | `通过`（仍有唯一 next-ready task） | `ahe-workflow-router` |
| `ahe-completion-gate` | `通过`（主链任务全部完成） | `ahe-finalize` |
| `ahe-completion-gate` | `通过`（仍有剩余任务，但下一任务不唯一或 ready 判定冲突） | `ahe-workflow-router` |
| `ahe-completion-gate` | `需修改` / `阻塞` | `ahe-test-driven-dev` |

如果某个下游 skill 给出的结论无法映射到当前 profile 迁移表中的唯一下一推荐节点，或 `ahe-completion-gate=通过` 后仍无法唯一决定“next-ready task vs finalize”，则说明编排信息还不完整，应回到 `ahe-workflow-router` 重新判断，而不是自行补脑推进。

上表主要描述“内容回修型”默认迁移。若 reviewer 返回摘要显式要求 `reroute_via_router=true`，或把 `next_action_or_recommended_skill` 指向 `ahe-workflow-router`，该显式重编排信号优先于表内默认下一步。

## 恢复编排协议

当某个节点完成后，按以下顺序恢复状态机：

1. 读取该节点的最新结论
2. 确认当前 workflow profile（从 `task-progress.md` 读取）
3. 若 `task-progress.md` 或等价工件已经写入合法或可归一化的 `Next Action Or Recommended Skill`，且它来自上一个已完成节点并与最新证据不冲突，优先采用这个显式下一步
4. 否则检查该结论对应的上游 / 下游迁移是否在当前 profile 迁移表中有明确规则
5. 若当前结论是 `ahe-completion-gate=通过`，优先检查已批准任务计划或 `Task Board Path` 指向的等价工件：
   - 若存在唯一 `next-ready task`，先把 `Current Active Task` 切换到该任务，并把显式下一步锁定为 `ahe-test-driven-dev`
   - 若不存在剩余 ready / pending task，才把下一步视为 `ahe-finalize`
   - 若剩余任务候选不唯一、依赖状态冲突或 ready 判定不稳定，回到 `ahe-workflow-router` 作为 hard stop
6. 根据当前会话上下文判断用户是否已经提出了新范围、新缺陷或新阻塞（基于已有信息判断，不主动询问用户）
7. 若有范围变化，优先判断是否切到 `ahe-increment`
8. 若有紧急缺陷，优先判断是否切到 `ahe-hotfix`
9. 若没有新的支线信号，则按当前 profile 迁移表进入唯一下一推荐节点

### 最小示例：T1 完成后切到 T2

前提工件：

```markdown
# task-progress.md

- Current Stage: ahe-completion-gate
- Workflow Profile: standard
- Execution Mode: auto
- Current Active Task: T1
- Next Action Or Recommended Skill: ahe-completion-gate
- Task Board Path: `docs/tasks/2026-04-09-parser-task-board.md`
```

```markdown
# docs/tasks/2026-04-09-parser-task-board.md

## Task Queue

| Task ID | Status | Depends On | Ready When | Selection Priority |
|---|---|---|---|---|
| T1 | in_progress | - | spec / design / tasks approval 已完成 | P1 |
| T2 | pending | T1 | T1=`done` | P2 |
```

当 T1 的 `ahe-completion-gate` 返回 `通过` 后，父会话 / router 恢复顺序应为：

1. 读取 completion gate 结论，确认当前 task 完成为 `T1`
2. 读取 task board，先把 T1 投影为 `done`
3. 根据 `Depends On` + `Ready When` 判断，T2 成为唯一 `next-ready task`
4. 更新 `Current Active Task: T2`
5. 将 `Next Action Or Recommended Skill` 锁定为 `ahe-test-driven-dev`
6. 因为这不是 approval node，也不是 hard stop，所以在同一轮继续进入 `ahe-test-driven-dev`

### 最小示例：最后一个任务完成后进入 finalize

若同样的恢复编排发生在最后一个任务：

```markdown
## Task Queue

| Task ID | Status | Depends On | Ready When | Selection Priority |
|---|---|---|---|---|
| T1 | done | - | spec / design / tasks approval 已完成 | P1 |
| T2 | done | T1 | T1=`done` | P2 |
```

此时 router 读取 queue 后发现不存在剩余 `ready` / `pending` task，才把下一步收敛为 `ahe-finalize`，而不是再回到实现节点。

不要跳过第 2 步、第 3 步和第 4 步。

恢复编排完成后：

- 若下一推荐节点是 `interactive` 下的 approval node，等待用户确认
- 若下一推荐节点是 `auto` 下的 approval node，先写 approval record，再进入该节点解锁后的下游节点
- 若下一推荐节点不是 approval node，也不是 hard stop，立刻在同一轮中进入该节点，不等待用户确认

若该下一推荐节点是 review 节点，则“进入该节点”的含义是：按 `references/review-dispatch-protocol.md` 派发 reviewer subagent，并按 `references/reviewer-return-contract.md` 消费返回摘要，而不是在父会话内联执行 review。
