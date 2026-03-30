---
name: mdc-hotfix
description: 在不放弃验证纪律的前提下处理紧急缺陷修复。适用于用户明确提出紧急修复，或某个缺陷必须尽快修复但仍需要通过 `mdc-test-driven-dev` 完成复现与最小修复、并保留回归检查和完成门禁的场景。
---

# MDC 热修复

处理紧急缺陷，但不能绕过工程纪律。

## 目的

这个 skill 适用于速度重要、但正确性和证据仍然更重要的紧急修复场景。

它不是绕过 `mdc-test-driven-dev`、TDD 或验证流程的捷径。

## 硬性门禁

不要仅凭直觉打热修复。

必须先复现，再修复，再重新验证。

## TDD 规则

热修复中的测试驱动修复统一委托给现有的 `mdc-test-driven-dev` skill。

除非当前问题明确无法立即自动化且该例外已被记录，否则不得绕过 `mdc-test-driven-dev` 直接修改生产代码。

## 红旗信号

出现以下想法时，先停下。这通常说明你正在为“紧急情况下跳过流程”找理由：

| 想法 | 实际要求 |
|---|---|
| “这是线上问题，先改了再说” | 热修复也必须先复现，再修复。 |
| “现在来不及写失败测试” | 能自动化时必须先通过 `mdc-test-driven-dev` 建立失败证据。 |
| “先把问题压住，回头再补验证” | 修复后必须立即重新验证，并进入后续门禁。 |
| “顺手把附近老问题一起清掉” | 只做与当前缺陷直接相关的最小安全修复。 |
| “测试没变，就不用走后续检查了” | 是否进入某个具体质量能力可按实际判断，但不能擅自省略必要的实现质量、追溯、回归和完成判断。 |
| “太急了，不用同步文档或状态” | 若缺陷暴露出工件已过时，稳定后仍需同步。 |

## 前置条件

在以下情况下使用本 skill：

- 用户明确要求紧急修复缺陷或上线前修复问题
- 现有工件、线上反馈或验证结果已经明确表明当前属于热修复场景

## 参考资料

如果团队还没有统一的热修复闭环记录格式，可先使用以下模板：

- `references/hotfix-repro-and-sync-record-template.md`

## 记录与状态要求

热修复过程中，至少应把关键信息落到以下工件之一：

- `docs/reviews/` 下的热修复记录
- 项目既有的缺陷修复记录
- `task-progress.md`

修复稳定后，还应同步：

- `task-progress.md`
- 必要时 `RELEASE_NOTES.md`
- 必要时受影响的规格、设计、任务记录

## Artifact Model 与 starter 交接

热修复默认发生在当前 `change workspace` 内，或由 `mdc-workflow-starter` 识别出的 hotfix workspace 内。

进入本 skill 时，先区分：

- `baseline artifacts`：当前仍有效的已批准规格、设计和稳定规则
- `change workspace`：本次热修复的复现记录、修复改动、review、verification、进度和发布记录
- `archive`：历史缺陷与历史收尾记录，只用于比较或恢复上下文

热修复期间优先把复现、修复和同步结果写回当前 `change workspace`；是否把其中某些结果提升为新的 baseline，或归档进入 archive，由 `mdc-finalize` 和团队规则决定。

如果当前调用来自 `mdc-workflow-starter`，应对齐其内部 payload：

- `currentWorkspace`：当前 hotfix workspace
- `requiredReads`：必须读取的缺陷证据、关键 baseline 与状态信息
- `expectedWrites`：热修复记录、`task-progress.md`、verification、必要时 `RELEASE_NOTES.md`
- `blockingReasons`：若无法安全复现、无法定位影响面或缺少关键输入，先阻塞并返回

## 工作流

### 1. 阅读热修复请求

阅读：

- 缺陷描述
- 当前 `change workspace` 的记录（如 `task-progress.md`、热修复记录）
- 当前相关的规格、设计、任务上下文（如有）
- 已存在的失败证据
- 当前仍有效的 `baseline artifacts`
- 仅在需要回看历史缺陷时读取 `archive`

明确：

- 期望行为
- 实际行为
- 受影响区域

### 2. 使用 `mdc-test-driven-dev` 复现问题

通过 `mdc-test-driven-dev` 创建最小且可靠的复现方式：

- 尽量用自动化失败测试复现
- 否则至少提供一个清晰的手工验证步骤，后续可再自动化

在证明问题真实存在之前，不要开始修复实现。

### 3. 使用 `mdc-test-driven-dev` 应用最小安全修复

只做足以修复已复现失败的最小改动，并在 `mdc-test-driven-dev` 的闭环里确认失败测试、最小实现、通过验证和必要重构都有对应证据。

除非确实是为了安全完成修复，否则不要顺手做机会式重构。

### 4. 执行后续质量能力与门禁

修复之后，在 workflow 中通常按以下顺序交给后续质量能力与门禁：

1. 确认复现路径现在已经通过
2. 使用 `mdc-bug-patterns`
3. 如果测试有变化，则使用 `mdc-test-review`
4. 使用 `mdc-code-review`
5. 使用 `mdc-traceability-review`
6. 使用 `mdc-regression-gate`
7. 使用 `mdc-completion-gate`

### 5. 必要时同步工件

如果该缺陷暴露出规格、设计、任务、发布说明或状态记录已过时或不正确，应在修复稳定后同步更新相关工件。

优先顺序是：

- 先在当前 `change workspace` 记录 delta 与状态变化
- 再由后续 `mdc-finalize` 判断哪些结果回写 baseline、哪些进入 archive

同步后还应明确：

- 当前热修已回流到主链的哪个阶段
- `task-progress.md` 中记录的下一步动作或推荐 skill 是什么
- 是否还需要后续 review / gate 之外的文档回写

## 输出格式

请严格使用以下结构：

```markdown
## 热修复摘要

- 摘要

## 复现方式

- 复现说明

## 修复范围

- 变更内容

## 状态同步

- 已更新工件

## 下一步

`进入后续质量检查` | `进入后续验证` | `进入最终完成判断` | `回到实现修订`

## 结构化交接

- currentWorkspace: <当前 workspace>
- nextNode: <唯一下一节点>
- requiredReads: <本轮实际读取的最少证据>
- expectedWrites: <热修记录路径>, `task-progress.md`, <verification / release path>
- blockingReasons: 无 | <阻塞原因>
- writesScope: `change workspace`
```

## 反模式

- 先打补丁，后补解释
- 不通过 `mdc-test-driven-dev` 就直接修改实现
- 未先复现就声称问题已修复
- 以“很紧急”为理由跳过回归检查
- 在热修复中夹带无关清理工作
- 还没确认复现路径转绿，就提前宣称修复完成
- 热修做完后不更新 `task-progress.md`，导致主链状态失真

## 完成条件

只有在缺陷被成功复现、用最小安全改动修复，并被正确送入后续质量能力与门禁流程后，这个 skill 才算完成。
