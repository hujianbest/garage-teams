# AHE 平台优先 Multi-Agent 实现设计评审记录

## 结论

阻塞

## 发现项

- [critical] 当前仓库中不存在可回读的已批准需求规格工件。`docs/specs/` 不存在，且 `AGENTS.md` 未声明等价 requirement spec 映射；因此被评审设计无法满足“锚定已批准规格”的前提条件。
- [critical] 被评审设计的直接上游 `docs/architecture/ahe-platform-first-multi-agent-architecture.md` 当前仍标记为 `状态: 草稿`，也没有可回读的 approval record。现状是“基于草稿架构继续产出草稿实现设计”，存在明确的 stage / approval evidence 冲突。
- [important] 当前仓库里也不存在 `task-progress.md` 或等价 progress state surface，导致本次设计评审的 canonical `Current Stage`、`Workflow Profile` 与 `Next Action Or Recommended Skill` 无法写回稳定状态面，后续 re-entry 仍会依赖聊天上下文。
- [important] 设计正文本身已经接近可任务规划输入，但 `16.2` 仍保留 `.platform-runtime` 目录组织、platform role assets 是否实体化、progressView 字段扩展等实现前待定项。在缺少上游批准输入的情况下，这些未定项进一步放大了任务拆解顺序的不稳定性。

## 薄弱或缺失的设计点

- 缺少 requirement spec / approval artifact，导致“需求覆盖与追溯”只能回指架构文，而不是回指已批准规格。
- 缺少 architecture-level approval evidence，导致实现设计无法作为进入 approval step 的候选输入。
- 缺少 progress state surface，导致 review 结果无法稳定回写到可恢复状态工件。
- `docs/designs/ahe-platform-first-multi-agent-implementation-design.md` 已具备较完整的 platform runtime contract，但仍需要在上游证据补齐后再判断这些待定项是 design-level blocking 还是 tasks-level follow-up。

## 下一步

- `阻塞`：`ahe-workflow-router`

## 记录位置

- `docs/reviews/design-review-ahe-platform-first-multi-agent-implementation-design.md`

## 交接说明

- `ahe-workflow-router`：当前阻塞主要来自 requirement spec 缺失、上游 approval evidence 缺失和 progress state surface 缺失，属于 route / stage / 证据链冲突。应先由 router 重编排，决定是否需要补 `ahe-specify` / `ahe-spec-review`、补 approval 记录，或显式声明 `docs/architecture/ahe-platform-first-multi-agent-architecture.md` 作为新的上游权威输入并补齐 approval evidence。
- `ahe-design`：只有在上游 requirement / approval / progress 证据面补齐之后，才建议回到 `ahe-design` 对正文中的待定项做定向修订；当前不应直接进入 `ahe-tasks` 或 approval step。
