# AHE Command Entrypoints

## Purpose

本文定义一组面向高频场景的薄命令入口约定：

- `/ahe-spec`
- `/ahe-build`
- `/ahe-review`
- `/ahe-closeout`

这些命令当前是 **docs-only contract**，不是已落地的真实命令文件。

目标是：

- 降低高频场景的进入摩擦
- 让新会话更容易命中正确的 family 入口
- 让命令入口先通过 `using-ahe-workflow` 解析，再决定 direct invoke 还是交给当前 router
- 但不复制 `ahe-workflow-starter` 的状态机逻辑

## Resolution Layers

命令入口的目标结构是：

```text
/ahe-* command
  -> using-ahe-workflow
       -> if current node is clear and local preconditions hold:
            direct invoke target leaf skill
       -> else:
            ahe-workflow-starter
```

因此，命令层负责表达高频用户意图，`using-ahe-workflow` 负责 family entry discovery，而 `ahe-workflow-starter` 仍负责当前 runtime authority。

## Thin Wrapper Principles

所有 `/ahe-*` 命令都应遵守：

1. **Command is bias, not authority**
命令只表达“偏向哪个入口意图”，不拥有独立路由权。

2. **`using-ahe-workflow` is the command-facing shell**
所有 `/ahe-*` 命令都先进入 `using-ahe-workflow`，再由它判断是否 direct invoke 具体节点。

3. **Starter remains the current routing kernel**
一旦出现 route / stage / profile 不清、工件冲突、批准状态不明，`using-ahe-workflow` 必须把 authoritative 判断交给 `ahe-workflow-starter`。

4. **Direct invoke is optional, not mandatory**
命令可以优先尝试 direct invoke 某个具体 skill，但只有在前置条件满足时才允许这样做。

5. **No duplicate machine contract**
命令文档不重新定义 verdict、handoff、progress schema、review return contract；这些统一引用共享文档。

6. **One command, one dominant user intent**
命令应优先服务一个高频意图，而不是变成“万能别名”。

7. **Leaf skill gates still apply**
即使命令偏向 direct invoke，具体 leaf skill 的 standalone contract 与 hard gates 仍然生效。

## Shared Resolution Pattern

命令入口的统一解析顺序建议如下：

1. 先把命令请求交给 `using-ahe-workflow`
2. 识别命令的主意图
3. 检查最小前置条件是否满足
4. 若当前节点已经足够明确，可 direct invoke 对应 skill
5. 若阶段不清、证据冲突、profile 不稳，由 `using-ahe-workflow` 交给 `ahe-workflow-starter`
6. 后续编排、暂停点、review dispatch 仍按 live workflow contract 执行

## Command Matrix

| 命令 | 主意图 | 先进入 | 偏向 direct invoke 的节点 | 遇到不确定时回哪里 |
|---|---|---|---|---|
| `/ahe-spec` | 规格澄清 / 规格修订 / 规格入口 | `using-ahe-workflow` | `ahe-specify` | `ahe-workflow-starter` |
| `/ahe-build` | 当前活跃任务实现 / 受控修订实现 | `using-ahe-workflow` | `ahe-test-driven-dev` | `ahe-workflow-starter` |
| `/ahe-review` | review / gate 请求分发 | `using-ahe-workflow` | 具体 review / gate 节点 | `ahe-workflow-starter` |
| `/ahe-closeout` | 完成判断与收尾 | `using-ahe-workflow` | `ahe-completion-gate` 或 `ahe-finalize` | `ahe-workflow-starter` |

## `/ahe-spec`

### Primary Intent

让用户以最低摩擦进入“需求规格”相关工作。

### Default Bias

默认偏向：

- `using-ahe-workflow`，作为命令入口的 family shell
- `ahe-specify`，如果当前明确是写规格、补规格或按 review findings 修规格

### Resolution Rules

- 若当前请求明确是规格正文产出 / 修订，且不存在 route / stage 冲突，可由 `using-ahe-workflow` direct invoke `ahe-specify`
- 若用户其实要 review spec，而不是继续写 spec，应改走 `/ahe-review` 或直接进入 `ahe-spec-review`
- 若当前已存在批准规格，且问题已经进入设计 / 任务 / 实现层，不强行停在 `/ahe-spec`
- 若用户说“先做 spec”，但当前其实混入 hotfix / increment / review-only / 阶段不清信号，由 `using-ahe-workflow` 把 authoritative 判断交给 `ahe-workflow-starter`

### Minimum Inputs

- 用户请求
- 当前规格草稿 / 评审记录（如有）
- `AGENTS.md` 中与规格路径、模板、状态词有关的约定

### Expected Output Shape

- 一份规格草稿，或
- 一个明确的 review handoff（通常是 `ahe-spec-review`），或
- 返回 `ahe-workflow-starter` 重新编排

### Non-Goal

- 不负责实现设计、任务或代码
- 不把 spec 评审和 spec 产出混成一个命令

## `/ahe-build`

### Primary Intent

让用户以最低摩擦进入“当前活跃任务实现”路径。

### Default Bias

默认偏向：

- `using-ahe-workflow`，作为命令入口的 family shell
- `ahe-test-driven-dev`

### Resolution Rules

- 若当前存在唯一活跃任务，且任务计划已批准，或已有 hotfix / 回流 handoff，可由 `using-ahe-workflow` direct invoke `ahe-test-driven-dev`
- 若当前缺唯一活跃任务、缺批准任务计划、缺 hotfix handoff、或 review / gate 还没过，不得因为命令名是 build 就直接开始实现
- 若用户真正表达的是“先分析 hotfix”或“先做 increment 影响分析”，应改走对应 branch 节点，而不是 `/ahe-build`
- 若当前请求是“继续做实现”，但 stage / profile / 工件状态冲突，由 `using-ahe-workflow` 把 authoritative 判断交给 `ahe-workflow-starter`

### Minimum Inputs

- 当前活跃任务或 hotfix handoff
- `task-progress.md`
- 必要 spec / design / task anchors
- `AGENTS.md` 中的 coding / testing 约定

### Expected Output Shape

- fresh RED / GREEN evidence
- 实现交接块
- canonical `Next Action Or Recommended Skill`

### Non-Goal

- 不替代 `ahe-hotfix` / `ahe-increment`
- 不跳过 review / gate

## `/ahe-review`

### Primary Intent

把 review / gate 请求快速导向正确节点。

### Default Bias

默认偏向：

- `using-ahe-workflow`，作为命令入口的 family shell
- 一个具体 review 节点：`ahe-spec-review` / `ahe-design-review` / `ahe-tasks-review` / `ahe-test-review` / `ahe-code-review` / `ahe-traceability-review`
- 或一个具体 gate 节点：`ahe-regression-gate` / `ahe-completion-gate`

### Resolution Rules

- 若用户已经明确 review 对象，且工件存在，可由 `using-ahe-workflow` direct invoke 对应 review / gate 节点
- 若参数使用 `trace`，默认映射到 `ahe-traceability-review`
- 若 review 对象仍模糊，例如只说“帮我 review 一下”，由 `using-ahe-workflow` 把 authoritative 判断交给 `ahe-workflow-starter`
- 若是 review 节点，无论通过 `/ahe-review` 还是其它入口进入，实际执行仍遵循 `skills/ahe-workflow-starter/references/review-dispatch-protocol.md`
- 若是 gate 节点，则由当前父工作流直接执行，不走 reviewer subagent
- 若 review / gate 请求暴露出 route / stage / profile 冲突，立即由 `using-ahe-workflow` 交给 `ahe-workflow-starter`，不在命令层硬判

### Minimum Inputs

- 当前被 review / gate 的目标对象
- 对应工件或记录
- `AGENTS.md` 中与 review / verification 约定有关的内容

### Expected Output Shape

- review record + structured reviewer summary，或
- verification / gate record，或
- 返回 `ahe-workflow-starter` 重编排

### Non-Goal

- 不代替 `ahe-workflow-starter` 判断“到底该 review 哪个节点”
- 不把 review 和 gate 混写成一个“万能检查”

## `/ahe-closeout`

### Primary Intent

让用户以最低摩擦进入“完成判断 + 收尾”路径。

### Default Bias

默认偏向：

- `using-ahe-workflow`，作为命令入口的 family shell
- 若 completion 证据尚未正式 gate，先走 `ahe-completion-gate`
- 若 completion gate 已通过，再走 `ahe-finalize`

### Resolution Rules

- 若已有 `ahe-regression-gate` 记录、实现交接块与当前完成声明，但尚未正式判断“能否算完成”，可由 `using-ahe-workflow` direct invoke `ahe-completion-gate`
- 若 `ahe-completion-gate` 已给出允许 finalize 的结论，可由 `using-ahe-workflow` direct invoke `ahe-finalize`
- 若 closeout 过程中发现仍需补实现、补验证或 gate 记录不支持 finalize，由 `using-ahe-workflow` 把 authoritative 判断交给 `ahe-workflow-starter`
- 若用户其实只想“跑 gate”，应优先用 `/ahe-review` 或直接进入对应 gate，而不是把 `/ahe-closeout` 当成通用 verification 命令

### Minimum Inputs

- 实现交接块
- regression / completion 记录（视当前子阶段而定）
- `task-progress.md`
- `RELEASE_NOTES.md`

### Expected Output Shape

- completion gate record，或
- finalize closeout pack，或
- 返回 `ahe-workflow-starter` 重编排

### Non-Goal

- 不把 completion gate 和 finalize 融成一个大命令
- 不在 gate 未通过时直接宣布 workflow 完成

## Suggested Syntax Shapes

此阶段先定义语义，不强制固定 CLI 语法；但可优先考虑以下薄形态：

```text
/ahe-spec [topic-or-artifact]
/ahe-build [task-id-or-short-intent]
/ahe-review [spec|design|tasks|test|code|trace|regression|completion] [artifact-or-task]
/ahe-closeout [task-id-or-scope]
```

原则：

- 参数只用于减少歧义
- 参数不能替代工件检查
- 命令名不能覆盖 `using-ahe-workflow` 的入口判断或 starter 的路由职责

## Examples

- `/ahe-spec add-rate-limit-rules`
  - 先进入 `using-ahe-workflow`，若节点明确则偏向进入 `ahe-specify`
- `/ahe-build TASK-003`
  - 先进入 `using-ahe-workflow`；若 `TASK-003` 已是唯一活跃任务且前置工件齐全，偏向进入 `ahe-test-driven-dev`
- `/ahe-review code TASK-003`
  - 先进入 `using-ahe-workflow`，再偏向进入 `ahe-code-review`
- `/ahe-closeout TASK-003`
  - 先进入 `using-ahe-workflow`；若 completion gate 尚未执行，先偏向 `ahe-completion-gate`；若已通过，则偏向 `ahe-finalize`

## References

- `docs/ahe-workflow-entrypoints.md`
- `docs/ahe-workflow-shared-conventions.md`
- `skills/using-ahe-workflow/SKILL.md`
- `skills/ahe-workflow-starter/SKILL.md`
- `skills/ahe-workflow-starter/references/review-dispatch-protocol.md`
