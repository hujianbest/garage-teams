# AHE workflow entrypoint replacement plan

## Status (router era)

本文主体为**历史迁移计划**（撰写时 **`ahe-workflow-starter`** 仍将 public entry 与 runtime kernel 合在一处；下文将该 pre-split 形态简称为 **legacy combined skill**）。**当前架构已落地**：`using-ahe-workflow` = 家族公开入口；`ahe-workflow-router` = canonical runtime router / 恢复权威；独立 legacy combined skill 目录已移除。canonical reroute 字段为 `reroute_via_router`（legacy reroute 字段读时同义，映射见 `docs/ahe-workflow-shared-conventions.md`）。下文保留原决策与阶段划分供对照；文中「当前」如无特别说明，指计划撰写时的仓库状态。

## Purpose

本文曾定义一条替换路径：

- 把 `using-ahe-workflow` 引入为新的 **公开命令入口 / family entrypoint**
- 逐步移除 pre-split **legacy combined skill** 作为公开入口的角色
- 但**不在第一轮直接删除当时承载的 runtime routing kernel**（后续已收敛为 `ahe-workflow-router` 并移除独立 legacy skill）

目标不是单纯给 legacy combined skill 改个名字，而是把 AHE 当时混在一起的两类职责拆开：

1. 对外入口与使用心智
2. runtime 路由与恢复编排 authority

## Decision Summary

本方案的核心决策如下：

1. 新增 `using-ahe-workflow`，作为 AHE workflow family 的公开入口、命令入口和 family explainer。
2. 将当前 **legacy combined skill** 所承载的 runtime kernel 职责，收敛到新的 `ahe-workflow-router`。
3. 迁移期曾计划保留历史 skill 名为 compatibility alias；（**现状**：独立 skill 已移除，读时别名由 `ahe-workflow-router` 文档约定覆盖。）
4. `using-ahe-workflow` 只负责“如何进入 AHE”，不负责 profile 选择、stage 判断、review dispatch 或 transition map。
5. runtime handoff、`Next Action Or Recommended Skill`、reviewer return contract 中，未来 canonical 值应写 `ahe-workflow-router`，而不是 `using-ahe-workflow`。

一句话概括：

- **`using-ahe-workflow` 取代 legacy combined skill 的公开入口角色**
- **`ahe-workflow-router` 取代 legacy combined skill 的 runtime kernel 角色**
- **pre-split legacy combined skill 作为过渡层逐步退场**（**已完成**）

## Why This Is Different From The Earlier Defer

`docs/ahe-p1-optional-assets-decision.md` 曾明确 defer `using-ahe-skills`，原因成立：

- 当时如果直接新增一个 family meta-skill，它很容易和 legacy combined skill 职责重叠
- 它会变成“第二个入口 kernel”
- 它会增加触发歧义和维护税

当前这份方案与那次 defer 的前提不同：

1. 这次不是新增一个模糊的 `using-ahe-skills`，而是新增**workflow 专用**的 `using-ahe-workflow`
2. 它有明确边界：只承担 public entry，不承担 runtime routing
3. 同时引入 `ahe-workflow-router`，把 kernel 从 legacy combined skill 中显式抽出来

因此，这不是“再加一个新的合并入口/router”，而是把：

- **公开入口**
- **运行时权威路由**

从一个过重的 legacy combined skill 中拆成两层。

## Problem Statement

在计划撰写时，AHE 的真实状态已经不是“有没有入口”，而是“入口和 kernel 绑在同一个 **legacy combined skill** 上”。

这曾带来几个结构问题：

- **legacy combined skill** 既是家族入口，又是 runtime router，又承担大量 family explainer 文本，主文件过重
- `docs/ahe-workflow-entrypoints.md` 与 `docs/ahe-command-entrypoints.md` 已经在尝试描述更低摩擦入口，但公开入口仍然直接暴露 legacy combined skill
- leaf skills、reviewer return contract、transition map 和 execution semantics 都把 legacy combined skill 当作 reroute 目标，使它同时承担“public shell”和“runtime kernel”两层语义
- 若未来真的想让 AHE 更像 `agent-skills-main` 那样有一个更稳定的 family entrypoint，当时 legacy combined skill 的命名和职责都不够适合作为那层产品化外壳

因此，本方案要解决的不是“给 legacy combined skill 换个更好听的名字”，而是：

- 让 AHE 拥有一个更像 `using-agent-skills` 的公开入口
- 同时保留 AHE 当前最强的 route-first / evidence-first workflow kernel

## Goals

本方案的目标：

1. 让 `using-ahe-workflow` 成为新的 family public entrypoint
2. 保留 AHE 当前的 workflow kernel，不削弱 route-first、evidence-first 和 gate-first
3. 把“公开入口语义”和“runtime 路由语义”拆开，减少 legacy combined skill 的混合职责
4. 降低新会话和命令入口的认知摩擦
5. 为未来真实的命令资产、setup 资产和对外 adopt 预留稳定入口
6. 以最小 breakage 完成迁移，不在第一轮就全仓暴力改名

## Non-Goals

本方案不做以下事情：

- 不在第一轮直接删除 **legacy combined skill**（后续分阶段完成后，独立 skill 已移除）
- 不把 `using-ahe-workflow` 做成第二个重型 kernel
- 不让 `using-ahe-workflow` 进入 `Next Action Or Recommended Skill`
- 不削弱当时由 **legacy combined skill** 承载、现由 `ahe-workflow-router` 承接的 pause points、review dispatch、profile-aware transition 和 reroute authority
- 不在单轮中同步重写所有 `ahe-*` skill
- 不为了统一命名而批量改写历史 progress / review / verification 工件

## Target Architecture

### High-level shape

目标态推荐结构：

```text
User / /ahe-* command / direct invoke
  -> using-ahe-workflow
       -> if current node is truly clear and local preconditions hold:
            direct invoke target leaf skill
       -> else:
            ahe-workflow-router
                -> decide profile
                -> decide canonical node
                -> dispatch reviewer subagent when needed
                -> consume reviewer return / gate result
                -> recover orchestration
```

### Responsibility split

| 层级 | 名称 | 负责什么 | 不负责什么 |
| --- | --- | --- | --- |
| Public entry | `using-ahe-workflow` | family discovery、entrypoint matrix、command bias、何时 direct invoke、何时交给 router | profile 选择、transition map、pause point 规则、reviewer return 消费 |
| Runtime router | `ahe-workflow-router` | profile 选择、canonical node 选择、branch 切换、review dispatch、review return 消费、execution semantics、transition map | family onboarding、面向新用户的入口解释、产品化 quick-start |
| Legacy name (read-time) | `ahe-workflow-starter` | 仅旧文档 / 旧 handoff；曾计划为迁移期 compatibility alias | **非 live skill**；canonical runtime 名为 `ahe-workflow-router`；正文简称见 **legacy combined skill** |
| Leaf skills | `ahe-specify` / `ahe-design` / `ahe-test-driven-dev` 等 | 完成本节点职责，写回 local output 与 canonical handoff | 决定 profile、决定整个主链下一步 |

## Naming Decision

### Why `using-ahe-workflow`

优先使用 `using-ahe-workflow`，而不是 `using-ahe-skills`：

- AHE 当前要解决的是 **workflow family entrypoint**，不是整个仓库所有 skill 的总导航
- 它与 `references/agent-skills-main/skills/using-agent-skills/SKILL.md` 的相似点在“入口层角色”，但作用域应更窄、更贴近 AHE 实际目标
- 它天然适合作为 README、命令入口、future setup 文档中的对外名称

### Why `ahe-workflow-router`

优先使用 `ahe-workflow-router`，而不是继续沿用 legacy combined skill 的旧命名或改成 `kernel`：

- 当前 live contracts 里频繁出现的是 route / reroute / stage / next step 语义
- `router` 比 legacy combined skill 的旧命名更准确表达它在 workflow 内部的权威职责
- `kernel` 虽然也准确，但更抽象；`router` 更贴近 leaf skill 的 fallback 语言和 shared conventions

### Alias policy

迁移期采用以下策略：

- **公开入口写法**：优先 `using-ahe-workflow`
- **runtime canonical 写法**：优先 `ahe-workflow-router`
- **兼容旧写法**：读时继续接受历史 skill 名（见上表 Legacy name 列）
- **新文档 / 新 handoff**：逐步停止继续写该历史名

## Canonical Rules

为避免迁移后再次语义混乱，先冻结以下规则。

### Rule 1. `using-ahe-workflow` 只属于 entry layer

它可以出现在：

- `README.md`
- `skills/README.md`
- `docs/ahe-workflow-entrypoints.md`
- `docs/ahe-command-entrypoints.md`
- future command wrappers / setup docs
- 用户直接点名的 public entry

它不应出现在：

- `Next Action Or Recommended Skill`
- reviewer 摘要里的 `next_action_or_recommended_skill`
- transition map 的 canonical next node
- progress schema 的 runtime reroute 字段

### Rule 2. runtime reroute 只回 router

当出现以下情况时，目标应是 `ahe-workflow-router`：

- route / stage / profile 不清
- 工件证据冲突
- reviewer 显式要求 reroute
- review / gate 刚完成，需要恢复后续编排
- 需要判断是切到 `ahe-hotfix` 还是 `ahe-increment`

### Rule 3. Legacy combined skill 迁移期只做 alias

迁移期允许：

- 旧 leaf skill 继续回历史 router 名（读时归一化，见 `docs/ahe-workflow-shared-conventions.md`）
- 旧 reviewer return contract 同理
- 旧 examples / plans / historical artifacts 保持不动

但新一轮 canonical 文档和 handoff 写法，应逐步改成：

- `using-ahe-workflow` 用于 public entry
- `ahe-workflow-router` 用于 runtime router

## Proposed `using-ahe-workflow` Contract

`using-ahe-workflow` 的目标不是复制 router 的规则，而是提供一个更稳定的 family shell。

建议它至少包含以下部分：

1. `Overview`
   - AHE 是一套什么样的 workflow family
   - 为什么默认 route-first

2. `Workflow Discovery`
   - 新需求 / 继续推进 / review-only / gate-only / hotfix / increment 的入口分流
   - 何时可以 direct invoke 某个 leaf skill

3. `Core Operating Rules`
   - 何时绝不能跳过 router
   - 何时 leaf skill 只完成本地职责
   - 何时命令只是 bias，不是 authority

4. `Entrypoint Matrix`
   - `using-ahe-workflow`
   - direct invoke
   - `/ahe-spec`
   - `/ahe-build`
   - `/ahe-review`
   - `/ahe-closeout`

5. `Failure Modes`
   - 把 `using-ahe-workflow` 当成新的合并 kernel
   - 在 route 不清时硬做 direct invoke
   - 把 runtime handoff 写成 `using-ahe-workflow`

这个 skill 的正确结尾行为通常是：

- direct invoke 一个明确的 leaf skill
- 或明确交给 `ahe-workflow-router`

而不是自己展开完整 transition map。

## Proposed `ahe-workflow-router` Contract

`ahe-workflow-router` 应承接当时 legacy combined skill 的 runtime authority，核心包括：

- Workflow Profile 选择
- canonical 当前节点判断
- mainline / `ahe-hotfix` / `ahe-increment` 分支切换
- review dispatch
- reviewer return contract 消费
- pause points / non-pause points
- result-driven transition map
- execution semantics 与恢复编排

它应保留 legacy combined skill 最强的那部分能力，但把：

- family explainer
- public onboarding
- command-facing guidance

尽量移出主文件，交给 `using-ahe-workflow` 和外围 docs。

## Migration Plan

### Phase 0. Freeze the design

先冻结以下结论：

- `using-ahe-workflow` 是 public entrypoint
- `ahe-workflow-router` 是 runtime kernel
- 历史 skill 名是 compatibility alias（legacy combined skill）
- `using-ahe-workflow` 绝不写入 runtime handoff

产物：

- 当前文档

完成标志：

- 命名、层级和 alias policy 不再摇摆

### Phase 1. Add the new public entrypoint

先新增：

- `skills/using-ahe-workflow/SKILL.md`

然后更新：

- `README.md`
- `skills/README.md`
- `docs/ahe-workflow-entrypoints.md`
- `docs/ahe-command-entrypoints.md`

这一步只改 public entry surface：

- 新会话默认先走 `using-ahe-workflow`
- 命令入口默认先偏向 `using-ahe-workflow`
- 迁移中期曾一度维持 runtime fallback 指向历史 router 名；（**现状**：canonical fallback 为 `ahe-workflow-router`）

完成标志：

- AHE 已拥有新的公开入口
- 但 runtime contracts 尚未破坏

### Phase 2. Split legacy combined skill into router

新增：

- `skills/ahe-workflow-router/SKILL.md`

处理方式：

- 将原 **legacy combined skill** 的 runtime authority 收敛为 router 写法（**现状**：由 `skills/ahe-workflow-router/SKILL.md` 承载）
- 曾计划保留 `skills/ahe-workflow-starter/SKILL.md` 为 thin wrapper；（**现状**：独立 starter 目录已移除，仅 legacy 名称可读）
- 原 legacy combined skill 里偏 public-explainer 的内容迁移到 `using-ahe-workflow`

这一步不要求一次搬空所有 reference files。

优先原则：

- 先稳定语义
- 再决定物理路径是否整体改名

完成标志：

- AHE 中“公开入口”和“runtime router”首次被显式拆开

### Phase 3. Migrate runtime vocabulary

更新以下位置的 canonical 写法：

- `docs/ahe-workflow-shared-conventions.md`
- router / legacy references
- reviewer return contract
- transition map
- execution semantics
- leaf skill 的 reroute 语句

写法变化：

- 旧：回历史 router 名（legacy combined skill）
- 新：回 `ahe-workflow-router`

兼容策略：

- 读时接受历史 skill 名
- 写时优先 router

完成标志：

- 新生成的 runtime artifacts 不再写历史 skill 名
- 历史 skill 名仅用于兼容读取旧契约

### Phase 4. Sweep leaf skills

这一轮统一修改 leaf skills：

- Authoring：`ahe-specify`、`ahe-design`、`ahe-tasks`
- Review：`ahe-spec-review`、`ahe-design-review`、`ahe-tasks-review`、`ahe-test-review`、`ahe-code-review`、`ahe-traceability-review`
- Implementation / branch：`ahe-test-driven-dev`、`ahe-hotfix`、`ahe-increment`
- Gates / finalize：`ahe-regression-gate`、`ahe-completion-gate`、`ahe-finalize`

统一目标：

- direct invoke 不清时，回 router
- chain contract 的 reroute target 改为 router
- reviewer / gate 结论恢复编排时，引用 router 而不是历史 skill 名

完成标志：

- live family 的 canonical reroute target 已统一

### Historical Phase 5. Retire legacy combined skill

**（已执行方向）** 独立 **legacy combined skill**（历史目录 `skills/ahe-workflow-starter/`）已移除；读时 legacy 别名与字段兼容由 `ahe-workflow-router` 及 shared conventions 覆盖。

按当时计划，这一阶段曾列出以下收尾选项：

- 保留历史 skill 名为 deprecated alias（以独立目录形式；**现状**：未采用，目录已移除）
- 或在确认全家族已不再写历史 skill 名后删除

进入条件（供考古）：

- 新文档不再写历史 skill 名
- 新 skill / template / examples 不再写历史 skill 名
- 历史工件不需要批量回写
- read-time alias 规则已稳定

## File Categories To Update

### Public entry layer

- `README.md`
- `skills/README.md`
- `docs/ahe-workflow-entrypoints.md`
- `docs/ahe-command-entrypoints.md`

### Router layer（canonical 物理路径）

- `skills/ahe-workflow-router/SKILL.md`
- `skills/ahe-workflow-router/references/review-dispatch-protocol.md`
- `skills/ahe-workflow-router/references/reviewer-return-contract.md`
- `skills/ahe-workflow-router/references/execution-semantics.md`
- `skills/ahe-workflow-router/references/profile-node-and-transition-map.md`

（历史计划中曾列 `skills/ahe-workflow-starter/...`；该目录已移除，语义由上述 router 路径继承。）

### Leaf skill contracts

- 所有 `skills/ahe-*/SKILL.md`
- 尤其是写有“若阶段不清 / route 冲突则回历史 router 名”的那些 skill

### Shared conventions and templates

- `docs/ahe-workflow-shared-conventions.md`
- review / verification 模板示例
- any example that writes `Next Action Or Recommended Skill: ahe-workflow-starter`（应改为 `ahe-workflow-router`）

### Analysis, decision and plan docs

- `docs/agent-skills-main-vs-ahe-workflow-report.md`
- `docs/ahe-workflow-family-optimization-execution-plan.md`
- `docs/ahe-review-subagent-implementation-checklist.md`
- `docs/ahe-p1-optional-assets-decision.md`

## Risks And Controls

| 风险 | 说明 | 控制方式 |
| --- | --- | --- |
| `using-ahe-workflow` 重新长胖 | public entry 又变成第二个合并 router | 明确禁止它承载 profile、transition map、pause-point machine contract |
| runtime handoff 被污染 | `using-ahe-workflow` 被写进 `Next Action Or Recommended Skill` | 在 shared conventions 中明确禁用，并在 examples 中只写 router |
| legacy 名称迁移导致大范围 breakage | leaf skills、review docs、transition map 还在写历史 skill 名 | 分阶段 alias 迁移，读时兼容历史 skill 名 |
| path churn 过大 | legacy reference paths 物理路径改动过早，导致 repo 大量引用失效 | 先改语义与 canonical name，再决定是否搬物理路径 |
| 旧决策文档与新方案冲突 | 外部读者看到旧 defer 结论会困惑 | 在后续 decision sweep 中明确：旧 defer 针对的是无 router 分层的 meta-skill 方案 |
| 入口层和命令层重复 | `using-ahe-workflow` 与 `/ahe-*` 命令文档相互复制 | 命令只保留 bias；family explainer 统一放在 `using-ahe-workflow` |

## Rejected Alternative

### Alternative A. Direct delete legacy combined skill and repoint everything to `using-ahe-workflow`

不推荐。

原因：

- discovery layer 和 runtime router 被迫使用同一个名字
- `using-*` 命名天然更像 public shell，不像 canonical reroute target
- leaf skills、reviewer return contract、transition map 和 execution semantics 都会立即大面积 break
- 最终不是得到更清晰的架构，而是把 legacy combined skill 的重量原样搬到另一个名字上

### Alternative B. Keep the legacy combined skill as the only entrypoint and merely add more docs

也不推荐作为最终方案。

原因：

- 这能继续维持现状，但无法真正解决“legacy combined skill 同时承担公开入口和 runtime kernel”的混合职责
- 也无法满足“用新的 `using-ahe-workflow` 替代 legacy combined skill 作为命令入口”的目标

## Acceptance Criteria

当本方案真正完成时，至少应满足：

- 新会话与命令入口默认从 `using-ahe-workflow` 进入
- `using-ahe-workflow` 没有复制 router 的 machine contract
- runtime reroute 统一写 `ahe-workflow-router`
- `Next Action Or Recommended Skill` 不写 `using-ahe-workflow`
- 独立 legacy combined skill 已移除；canonical runtime authority 在 `ahe-workflow-router`（legacy 名称读时兼容）
- leaf skills、reviewer return contract、transition map 和 execution semantics 不再依赖历史 skill 名作为唯一 canonical 名称

## Recommended Immediate Next Batch

如果紧接着执行下一批，而不是继续停留在讨论层，推荐顺序如下：

1. 新增 `skills/using-ahe-workflow/SKILL.md`
2. 更新 `docs/ahe-workflow-entrypoints.md`
3. 更新 `docs/ahe-command-entrypoints.md`
4. 新增 `skills/ahe-workflow-router/SKILL.md`
5. **（已完成）** 独立 legacy combined skill 已移除；reroute vocabulary 以 `ahe-workflow-router` / `reroute_via_router` 为准
6. **（已完成）** family-wide reroute 字段收口为 `reroute_via_router`（legacy reroute 字段仅兼容读）

## One-Sentence Recommendation

历史推荐路径是：先让 `using-ahe-workflow` 接管公开入口，再把 pre-split legacy combined skill 的 kernel 显式收缩为 `ahe-workflow-router`，最后退休独立 legacy skill（**已与当前仓库状态一致**）。
