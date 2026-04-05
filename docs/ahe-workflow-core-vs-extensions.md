# AHE Workflow Core Vs Extensions

## Purpose

本文划清 AHE workflow family 的 **core surface** 与 **extension surface**。

目标是避免两种常见误解：

1. 把大量辅助文档、命令、persona、包装层误当成“没有这些就不能跑 AHE”
2. 把真正必须存在的 runtime contract 也误当成“可有可无”

## Core Rule

**Core** 指：没有它，AHE 就会失去可路由、可验证、可恢复的基本能力。  
**Extension** 指：没有它，AHE 仍能工作，只是可用性、可移植性或维护体验下降。

## Core Surface

### 1. Routing kernel

以下属于 core：

- `skills/ahe-workflow-starter/`
- profile 规则
- canonical route / reroute semantics
- pause point / human confirmation semantics

原因：

- 没有 routing kernel，就无法判断当前节点
- 没有 profile 规则，就无法知道该走多重的链路
- 没有 reroute 语义，就无法在 review / gate / branch 之后恢复主链

### 2. Canonical contracts

以下属于 core：

- canonical progress schema
- canonical verdict vocabulary
- canonical `Next Action Or Recommended Skill`
- reviewer return contract
- review dispatch protocol

原因：

- 没有这些 contract，节点之间只能靠自由文本 handoff
- 一旦 handoff 变成自由文本，starter、review、gate 与 branch 就无法稳定协作

### 3. Main runtime nodes

按 profile 而言，以下节点属于 core：

#### Always-available core family nodes

这些节点不一定出现在每一次运行里，但都属于 AHE family 必须保留的 core runtime surface：

- `ahe-workflow-starter`
- `ahe-tasks`
- `ahe-tasks-review`
- `任务真人确认`
- `ahe-test-driven-dev`
- `ahe-regression-gate`
- `ahe-completion-gate`
- `ahe-finalize`
- `ahe-hotfix`
- `ahe-increment`

#### Full-profile core nodes

- `ahe-specify`
- `ahe-spec-review`
- `规格真人确认`
- `ahe-design`
- `ahe-design-review`
- `设计真人确认`
- `ahe-bug-patterns`
- `ahe-test-review`
- `ahe-code-review`
- `ahe-traceability-review`

#### Standard-profile additional core nodes

standard profile 在质量层上与 full profile 共享以下 core nodes：

- `ahe-bug-patterns`
- `ahe-test-review`
- `ahe-code-review`
- `ahe-traceability-review`

#### Lightweight-profile core nodes

- lightweight 允许跳过 `ahe-bug-patterns`、`ahe-test-review`、`ahe-code-review`、`ahe-traceability-review`
- 但不能跳过 `ahe-tasks-review` / `任务真人确认` / `ahe-regression-gate` / `ahe-completion-gate`

### 4. Artifact surface

以下属于 core：

- requirement spec / design doc / task plan（按当前 profile 需要）
- progress state
- review records
- verification records

说明：

- release notes 对存在用户可见变更的项目几乎也是 core
- 如果项目完全没有用户可见变更面，可把 release notes 视作弱核心，但不能用它替代 progress / verification

### 5. Fresh evidence discipline

以下属于 core：

- `ahe-test-driven-dev` 的 fresh RED / GREEN evidence
- `ahe-regression-gate` 的 fresh regression evidence
- `ahe-completion-gate` 的 fresh completion evidence

没有这些，quality chain 会退化成“我感觉已经好了”。

## Extension Surface

### 1. Docs-first helper layer

以下属于 extension：

- `docs/ahe-workflow-shared-conventions.md`
- `docs/ahe-workflow-entrypoints.md`
- `docs/ahe-review-persona-matrix.md`
- `docs/ahe-command-entrypoints.md`
- `docs/ahe-p0-batch-verification.md`

它们提升理解和维护效率，但 runtime 不直接依赖它们存在。

### 2. Thin wrapper commands

以下属于 extension：

- `/ahe-spec`
- `/ahe-build`
- `/ahe-review`
- `/ahe-closeout`

原因：

- 它们只降低入口摩擦
- 不拥有独立状态机
- 即使没有这些命令，starter 与各 skill 仍可直接工作

### 3. Optional personas and meta-assets

以下属于 extension：

- `using-ahe-skills` family meta-skill（当前 defer；见 `docs/ahe-p1-optional-assets-decision.md`）
- reviewer / gate `agents/*.md`
- persona-specific wrappers

这些资产只有在真实复用频率足够高时才值得新增。

### 4. Packaging / install / hook examples

以下属于 extension：

- setup / install 文档
- hook / plugin 示例
- packaging 辅助层

这些都不影响 AHE 本身的 workflow contract 是否成立。

## Adoption Tiers

### Tier 1: Minimal viable AHE

需要：

- starter
- canonical contracts
- progress state
- tasks review / human confirmation / implementation / regression gate / completion gate / finalize 主线
- branch nodes

适合：

- 先在外部仓库验证 AHE 是否能闭环

### Tier 2: Full-quality AHE

需要：

- Tier 1 全部内容
- full / standard 的 quality layer：bug-patterns / test-review / code-review / traceability-review
- upstream spec / design authoring + review + human confirmation

适合：

- 高风险或长期维护项目

### Tier 3: Experience layer

增加：

- shared docs
- entrypoint docs
- command wrappers
- persona matrix
- optional meta-skill / agents

适合：

- 多人维护
- 多仓复用
- 需要降低 onboarding 成本

## What Not To Externalize First

若外部仓库刚开始采用 AHE，不建议先做这些：

- 先做很多命令包装，却还没有稳定 progress state
- 先做 reviewer persona files，却还没有统一 shared conventions
- 先做 packaging / hook 集成，却还没有跑通 starter
- 先复制一堆文档名字，却没有真正声明映射关系

## Practical Decision Table

| 如果你现在想做的是 | 先做 core 还是 extension | 原因 |
|---|---|---|
| 让外部仓库第一次跑通 AHE | core | 先保证 route / review / gate / finalize 可闭环 |
| 降低新会话进入摩擦 | extension | 这是体验优化，不是运行前提 |
| 让 reviewer 角色更稳定复用 | 先 core，后 extension | 先证明 contract 稳定，再抽 persona 资产 |
| 做安装、分发、hook 接入 | extension | 不影响 AHE workflow 是否成立 |

## Bottom Line

对外部仓库来说，最小正确问题不是“有没有命令入口”，而是：

- 有没有 starter
- 有没有 stable contracts
- 有没有 progress state
- 有没有 review / verification evidence
- 有没有 human confirmation 与 finalize 语义

这些成立之后，extension 才值得慢慢叠加。

## Related Docs

- `docs/ahe-workflow-externalization-guide.md`
- `docs/ahe-path-mapping-guide.md`
- `docs/ahe-p1-optional-assets-decision.md`
- `docs/ahe-workflow-shared-conventions.md`
