# AHE Workflow Externalization Guide

## Purpose

本文说明外部仓库采用 AHE workflow family 时，最少需要准备什么。

重点不是“把外部仓库改得和本仓库一模一样”，而是保证以下能力存在：

- starter 能找到足够的路由证据
- review / gate 能找到可消费的上游工件
- approval 与 verification 能留下可回读的证据
- direct invoke 不会因为缺少状态面而变成瞎猜

## Externalization Principle

外部仓库采用 AHE 时，优先做 **逻辑映射**，不是 **路径复制**。

换句话说：

- 可以保留外部仓库原本的文件结构
- 但要让 `AGENTS.md` 或等价约定明确告诉 AHE：这些逻辑工件实际放在哪里、如何判断已批准、哪些 review / verification 路径是权威来源

如果做不到这点，AHE 会退化成依赖聊天上下文和猜测推进，这正是它想避免的情况。

## Minimal Capability Set

外部仓库最少应提供以下能力。

### 1. Routeable artifact surface

至少要能定位当前 profile 所需的大部分逻辑工件：

- requirement spec
- design doc
- task plan
- progress state
- review records
- verification records
- release notes（若项目存在用户可见变更）

不要求这些路径与本仓库一致，但必须能被唯一映射。

### 2. Explicit approval surface

外部仓库必须能明确区分：

- 草稿
- review 通过
- 真人确认完成
- 尚未批准

如果只能看出“有人大概同意过”，而没有可回读证据，starter 仍应按未批准处理。

### 3. Stable progress state

至少需要一个可持续更新的状态面，承载：

- `Current Stage`
- `Workflow Profile`
- `Current Active Task`
- `Pending Reviews And Gates`
- `Next Action Or Recommended Skill`

如果外部仓库不愿采用这组字段名，也必须在 `AGENTS.md` 中声明映射。

### 4. Verifiable evidence surface

对于需要 fresh evidence 的节点，外部仓库必须允许：

- 写入验证记录
- 记录命令 / 结果摘要 / 新鲜度锚点
- 让后续 gate / finalize 回读这些记录

如果验证证据只能停留在对话里，AHE 的 gate 和 finalize 就无法诚实工作。

### 5. Controlled handoff surface

外部仓库必须允许节点把下一步显式写回状态面，而不是只靠聊天里的“继续”。

最少应支持：

- 写回 canonical `Next Action Or Recommended Skill`
- 写回当前任务与待处理 review / gate
- 写回 re-entry 或 reroute 信息

## Minimum Artifacts By Profile

### `full`

最少应能稳定提供：

- requirement spec
- design doc
- task plan
- progress state
- review records
- verification records
- release notes（如适用）

### `standard`

最少应能稳定提供：

- 已批准 requirement spec / design doc
- task plan
- progress state
- review records
- verification records
- release notes（如适用）

### `lightweight`

最少应能稳定提供：

- task plan
- progress state
- task review records（至少包括 `ahe-tasks-review`）
- approval evidence（至少能回读 `任务真人确认`）
- verification records
- release notes（如适用）

注意：

- lightweight 可以跳过部分质量 review 节点（如 `ahe-bug-patterns`、`ahe-test-review`、`ahe-code-review`、`ahe-traceability-review`），不等于可以跳过 `ahe-tasks-review`、`任务真人确认`、状态工件或完成证据
- 若执行中发现缺少上游依据，仍应升级 profile，而不是继续假装 lightweight 足够

## Approval Points You Cannot Remove

### Always keep

无论外部仓库路径怎么映射，以下批准 / 门禁语义不能丢：

- `ahe-tasks-review` 通过后，仍需 `任务真人确认`
- `ahe-regression-gate` 通过后，才允许进入 `ahe-completion-gate`
- `ahe-completion-gate` 通过后，才允许进入 `ahe-finalize`

### `full` profile additionally requires

- `ahe-spec-review` 通过后，`规格真人确认`
- `ahe-design-review` 通过后，`设计真人确认`

### Meaning

这些点可以换路径、换模板、换状态词别名，但不能删成“聊天里说过一声就算通过”。

## Direct Invoke Prerequisites In External Repos

外部仓库允许 direct invoke，但前提比本仓库更严格，因为上下文更不熟悉。

至少同时满足：

1. 目标节点已经明确
2. 所需逻辑工件路径已能通过 `AGENTS.md` 或等价约定定位
3. 批准状态、profile 和当前阶段没有冲突
4. 节点所需最小证据已经存在
5. 调用方理解该节点只完成本地职责，后续编排仍回到父会话 / starter

若任一条件不满足，先走 `ahe-workflow-router`。

### Direct invoke examples

- 外部仓库已有明确 spec 草稿，用户只想继续写 spec -> 可 direct invoke `ahe-specify`
- 外部仓库已有唯一活跃任务、批准任务计划与 task progress -> 可 direct invoke `ahe-test-driven-dev`
- 外部仓库已有 completion / regression 记录，且只需做收尾 -> 可 direct invoke `ahe-finalize`

### Not safe to direct invoke

- 文件路径要靠猜
- 批准状态只能从聊天里推断
- `Current Stage` 与工件状态冲突
- review / gate 刚结束但没人写回状态
- 用户说“继续”，但实际上不知道当前节点

## Recommended `AGENTS.md` Additions

若要把 AHE 带到外部仓库，建议在外部仓库的 `AGENTS.md` 中至少声明：

- 逻辑工件 -> 实际路径映射
- 批准状态别名
- review verdict 别名
- progress schema 映射
- review / verification / release artifacts 的权威路径
- profile 强制条件（如哪些模块必须 `full`）

## Migration Strategy

建议按以下顺序落地，而不是一次改全仓：

1. 先声明 `AGENTS.md` 映射
2. 再确定 progress state 的最小字段
3. 再确定 review / verification 路径
4. 再让 starter 在该仓库里跑通
5. 最后才逐步开放 direct invoke 或薄命令入口

## Externalization Checklist

- [ ] 外部仓库已提供或映射 requirement spec / design doc / task plan
- [ ] 外部仓库已提供或映射 progress state
- [ ] 外部仓库已提供或映射 review / verification 路径
- [ ] 批准状态、review verdict 与 progress 字段已声明映射
- [ ] 至少一个 profile 可以在该仓库里闭环运行
- [ ] direct invoke 的前置条件已被文档化，而不是依赖口头共识

## Related Docs

- `docs/ahe-workflow-shared-conventions.md`
- `docs/ahe-workflow-entrypoints.md`
- `docs/ahe-command-entrypoints.md`
- `docs/ahe-path-mapping-guide.md`
- `docs/ahe-workflow-core-vs-extensions.md`
