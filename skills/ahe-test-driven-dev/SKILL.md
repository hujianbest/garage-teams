---
name: ahe-test-driven-dev
description: 作为 AHE 系列唯一实现入口使用。适用于任务计划已批准后的单任务实现、受控 hotfix 已进入修复实现、或 review / gate 回流后的受控修订；本 skill 负责锁定唯一活跃任务、完成真人测试设计确认、执行有效 TDD、写回 fresh evidence 与实现交接块，并写明 canonical 下一步 `ahe-*` 节点，由父会话或 `ahe-workflow-router` 恢复后续编排。若阶段不清或状态工件冲突，先回到 `ahe-workflow-router`。
---

# AHE 测试驱动开发与实现入口

这是 AHE workflow family 里的唯一实现入口。它不是 review / gate 的替代品，也不是一个会私自重排质量链的子流程。

## Overview

这个 skill 承担三层职责：

1. 作为 `ahe` 系列唯一的实现入口
2. 作为实现阶段内部统一的 TDD 执行入口
3. 作为实现完成后向后续 review / gate 输出实现证据与显式 handoff 的交接入口

它负责把单个活跃任务从“准备实现”推进到“已写回新鲜证据与 canonical 下一步”。

## When to Use

在这些场景使用：

- full / standard / lightweight profile 中，任务计划获批后进入本 skill
- 受控热修复在进入实际修复实现时进入本 skill
- 来自 `ahe-bug-patterns`、`ahe-test-review`、`ahe-code-review`、`ahe-traceability-review`、`ahe-regression-gate`、`ahe-completion-gate` 的回流修订，只要仍属于当前活跃任务，也重新进入本 skill
- 用户明确要求“开始实现这个 active task”或“按 TDD 修这个任务 / hotfix / 回流项”

不要在这些场景使用：

- 主链任务计划未批准
- hotfix 还没有来自 `ahe-hotfix` 的复现路径、最小修复边界和 handoff
- 当前需要的是 review / gate 本身，改用对应质量节点
- 当前想并行推进多个任务，先回到 `ahe-workflow-router`

## Standalone Contract

当用户直接点名 `ahe-test-driven-dev` 时，至少确认以下条件：

- 当前存在唯一活跃任务
- 有已批准任务计划，或有来自 `ahe-hotfix` 的最小修复边界与 handoff，或有明确的回流 findings
- 能读取 `task-progress.md` 或等价状态工件
- 能读取必要的规格 / 设计锚点与测试设计种子

如果出现以下任一情况，不要强行继续：

- `task-progress.md`、任务计划、规格 / 设计批准状态彼此冲突
- 当前请求其实属于 review / gate / 上游重编排
- 当前没有唯一活跃任务

这些情况都先按更保守的上游证据处理，并回到 `ahe-workflow-router`。

## Chain Contract

作为主链节点被串联调用时，默认读取：

- `AGENTS.md` 中与当前任务相关的 testing / coding 约定
- 已批准任务计划，或 `ahe-hotfix` 产出的复现路径、最小修复边界与 handoff
- `task-progress.md` 中的 `Current Stage`、`Current Active Task`、`Pending Reviews And Gates`、`Next Action Or Recommended Skill`
- 当前任务对应的规格和设计片段
- 若当前是回流修订，追加读取来源节点的发现项、失败用例、复现路径或阻塞证据

本节点完成后应写回：

- 新鲜的 RED / GREEN 证据
- 稳定的实现交接块
- 当前任务的状态更新
- canonical `Next Action Or Recommended Skill`

本 skill 不在内部私自重排质量链；由父会话 / `ahe-workflow-router` 按当前 profile 恢复后续编排。

## Hard Gates

- 主链实现时，任务计划未获批准前，不得开始实现。
- hotfix 实现时，至少要有来自 `ahe-hotfix` 的复现路径、最小修复边界和显式 handoff。
- 当前任务在实现、评审、验证完成之前，不得切换到下一个任务。
- 在进入 Red-Green-Refactor 之前，必须先让真人确认当前任务的测试用例设计满足预期。
- 在写回 fresh evidence 和 canonical handoff 之前，不得声称“当前任务已完成”。

## Quality Bar

高质量的 `ahe-test-driven-dev` 执行结果，至少应满足：

- 全程只围绕一个已批准、可追溯的活跃任务推进
- 动手实现前，已读取任务计划、状态记录、相关规格 / 设计锚点，以及必要的回流来源记录
- 测试设计不仅经过真人确认，而且能说明要验证的行为、边界、反向场景和预期失败点
- RED 和 GREEN 都有当前会话中的新鲜证据，而不是靠口头描述或旧日志
- 实现完成后能产出稳定的“实现交接块”，让下游 review / gate 直接消费
- 明确知道自己不替代 `ahe-bug-patterns`、`ahe-test-review`、`ahe-regression-gate`

## Inputs / Required Artifacts

进入实现阶段后，先检查 `AGENTS.md` 是否为当前项目声明了 testing 规范，优先读取：

- 测试命令与执行顺序
- 单测 / 集成测 / 端到端测试的分层要求
- mock、fixture、外部依赖替身的边界
- 覆盖率门槛或必须覆盖的风险类型
- 哪些非代码或纯配置变更可例外豁免 fail-first 纪律

实现阶段的活跃任务不应依赖聊天记忆推断。优先从 `task-progress.md` 或等价状态工件读取：

- `Current Stage`
- `Current Active Task`
- `Pending Reviews And Gates`
- `Next Action Or Recommended Skill`

若项目不是 C++ / GoogleTest，也不能把当前 skill 降级成“先随便实现，再看情况”：

- 仍然必须锁定唯一活跃任务
- 仍然必须先做测试设计并等待真人确认
- 仍然必须完成有效 RED / GREEN / REFACTOR
- 仍然必须写回 fresh evidence、剩余风险和 canonical 下一步
- 仍然必须在交接块中写明当前语言 / 框架 / 命令入口

如果项目为“实现交接块”定义了稳定落点，优先遵循 `AGENTS.md`；否则把交接块写进当前任务可被下游稳定读取的状态工件或实现记录中。

## Workflow

### 1. 对齐上下文并锁定唯一活跃任务

默认顺序：

1. 先读 `task-progress.md` 中的 `Current Active Task`
2. 若当前是主链实现，再用已批准任务计划校验该任务是否真实存在、仍然有效，并读取其中的测试设计种子
3. 若当前是 hotfix 实现，则用 `ahe-hotfix` 产出的复现路径、最小修复边界和 handoff 记录校验当前任务；只有当该 hotfix 已关联任务计划时，才补读对应测试设计种子
4. 如果当前是回流修订，再补读来源节点的发现项、失败用例或阻塞证据
5. 若这些证据冲突，暂停实现并先修正状态记录或回到上游编排，不直接继续编码

### 2. 产出测试设计，并先做轻量自检

在进入 TDD 之前，先输出当前任务的测试设计，至少说明：

- 要验证哪些行为
- 关键正向 / 反向场景
- 边界条件
- 预期输入与输出
- 哪些测试应先失败
- 若 `AGENTS.md` 要求分层测试，当前哪些测试属于单测 / 集成测 / 其它层次
- 若任务计划中已给出测试设计种子，当前设计与种子是否一致；若不一致，差异是什么

在把测试设计展示给真人前，先做一轮轻量自检：

- 是否覆盖了当前任务最关键的成功行为
- 是否覆盖了关键反向或边界场景（如果适用）
- 当前测试能抓住哪类“错误但看起来像是完成了”的实现
- 是否把 mock 限定在真正的边界，而不是 mock 自己的逻辑

### 3. 让真人确认测试设计

1. 把测试用例设计展示给真人
2. 邀请真人确认“这些测试是否满足当前预期”
3. 如果真人提出意见，继续对话并修改测试设计
4. 只有在真人明确确认后，才能进入下一步

### 4. 执行有效 TDD

对于当前任务：

1. 先写失败测试
2. 运行并确认失败原因符合预期
3. 写最小实现让测试通过
4. 运行当前任务级证明命令，并确认新的通过结果来自本次会话
5. 在全绿后做必要的最小重构

有效 RED 至少满足：

- 当前会话里真的执行过测试或等价验证命令
- 失败直接对应当前要实现 / 修复的行为缺口
- 你能说清失败为何符合预期，并留下可复用的失败摘要

以下情况不算有效 RED：

- 只写了测试，但没有运行
- 测试一跑就是绿的
- 与当前任务无关的旧失败、环境故障或无关编译错误
- 你看不出失败到底在证明什么

有效 GREEN 至少满足：

- 当前任务对应的测试已经转绿
- `AGENTS.md` 或当前项目要求的最小证明命令在本次会话里成功执行
- 你保留了 fresh evidence，而不是引用旧的通过结果

### 5. 生成实现交接块并同步状态

在声称任务完成之前，至少写回一个稳定的实现交接块，供后续 review / gate 直接消费。

```md
## 实现交接块

- Task ID:
- 回流来源: 主链实现 | `ahe-hotfix` | `ahe-bug-patterns` | `ahe-test-review` | `ahe-code-review` | `ahe-traceability-review` | `ahe-regression-gate` | `ahe-completion-gate`
- 触碰工件:
- 测试设计确认证据:
- RED 证据: <命令 + 失败摘要 + 为什么这是预期失败>
- GREEN 证据: <命令 + 通过摘要 + 关键结果>
- 与任务计划测试种子的差异:
- 剩余风险 / 未覆盖项:
- Pending Reviews And Gates:
- Next Action Or Recommended Skill:
```

交接块中的 `Next Action Or Recommended Skill` 应使用 canonical skill ID：

- 正常主链实现完成后：
  - full / standard 通常写 `ahe-bug-patterns`
  - lightweight 通常写 `ahe-regression-gate`
- 若当前是下游 quality node 回流修订完成后再恢复，则通常写回触发回流的那个 node

当后续 canonical 下一步是 review 节点时，含义是：

- 父会话应把该节点视为 review dispatch 目标
- 由当前父会话派发独立 reviewer subagent
- 当前父会话可以是 `ahe-workflow-router`，也可以是当前上游产出 skill
- reviewer subagent 消费当前实现交接块并执行对应 `ahe-*review`

同步更新 `task-progress.md` 中当前任务的进展与待处理质量节点，但不要在本 skill 内替代 starter 做完整路由判断。

### 6. 回流修订协议

如果当前是因为 hotfix、review 或 gate 回流重新进入本 skill：

1. 明确回流来源
2. 明确当前只修哪一个活跃任务、哪一组发现项或失败用例
3. 若修订改变了行为预期或测试设计，需要重新做测试设计确认
4. 若只是修正文档化缺陷、实现遗漏或已知错误实现，则在当前任务范围内补 RED / GREEN 证据
5. 修订完成后，把新的 fresh evidence 和 canonical 下一步写回交接块，而不是把质量链从头再走一遍

## Output Contract

本节点完成时，至少应产出：

- fresh RED / GREEN evidence
- 稳定的实现交接块
- 当前任务的状态更新
- canonical `Next Action Or Recommended Skill`

常见合法值包括：

- `ahe-bug-patterns`
- `ahe-test-review`
- `ahe-code-review`
- `ahe-traceability-review`
- `ahe-regression-gate`
- `ahe-completion-gate`

对下游质量节点，这个交接块就是 reviewer / gate 的最小核心输入之一。本 skill 只负责把输入准备好，不代它们出 verdict。

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| “这个任务很小，直接改掉更快” | 任务再小，也必须先经过本 skill 的 fail-first 纪律。 |
| “测试用例大概可以，先跑起来再说” | 先让真人确认测试用例设计，再进入 TDD。 |
| “测试后面再补也行” | 先有失败测试，再写生产代码。 |
| “我先顺手把相邻任务一起做了” | 一次只允许一个活跃任务。 |
| “不是 C++，那这套规则先不管了” | 非 C++ 也必须遵守同一实现契约，只是深度参考不同。 |
| “下一步先写成一句自然语言，starter 自己会猜” | `Next Action Or Recommended Skill` 优先写 canonical `ahe-*` skill ID。 |
| “现在已经差不多了，可以先说完成” | 完成要等评审、回归和完成门禁都走完。 |
| “这些 review 太重了，先跳过一个” | 后续质量能力与门禁由 `ahe-workflow-router` 恢复编排，不能在本节点内擅自省略或重排。 |
| “旧的绿测结果也能证明这次改动没问题” | 必须有当前任务对应的新鲜证据。 |
| “TDD 太慢了，先写完再补测试” | 后补的测试直接通过，什么也证明不了。 |

## Red Flags

- 并行处理多个任务
- 未经真人确认测试用例设计，就直接开始写失败测试
- 不经过 fail-first 过程就直接开始实现
- 先写实现，再补失败测试
- 把旧的绿测结果当成当前证据
- 在完成门禁前就说“做完了”
- 因为当前任务变麻烦就切换任务
- 因为赶进度而跳过缺陷模式排查、评审或门禁
- 不读取 `task-progress.md` 就靠会话印象决定当前活跃任务
- 测试直接通过却没有重新定义它要抓的行为

## Supporting References

- `testing-anti-patterns.md`
- `references/cpp-gtest-deep-guide.md`

只有在当前项目是 C++ / GoogleTest / CMake 栈，且确实需要语言级细节时，再加载 C++ 深度参考。

## Verification

只有在测试设计已经过真人确认，且当前任务已经完成实现，并把 fresh verification evidence、剩余风险和 canonical 推荐下一步写回实现交接块与状态工件，或明确报告了阻塞问题后，这个 skill 才算完成。

交接前确认：

- [ ] 当前只围绕一个活跃任务推进
- [ ] 测试设计已完成轻量自检并经过真人确认
- [ ] 当前任务已留下有效 RED 与 GREEN 证据
- [ ] 已写回实现交接块，并包含 canonical `Next Action Or Recommended Skill`
- [ ] `task-progress.md` 或等价状态工件已同步当前任务进展与待处理质量节点
- [ ] 没有在本节点内私自重排后续质量链
