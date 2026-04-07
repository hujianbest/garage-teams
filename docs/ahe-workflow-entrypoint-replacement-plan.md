# AHE workflow entrypoint replacement plan

## Purpose

本文定义一条新的替换路径：

- 把 `using-ahe-workflow` 引入为新的 **公开命令入口 / family entrypoint**
- 逐步移除 `ahe-workflow-starter` 作为公开入口的角色
- 但**不直接删除当前 runtime routing kernel**

目标不是单纯把 starter 改个名字，而是把 AHE 现在混在一起的两类职责拆开：

1. 对外入口与使用心智
2. runtime 路由与恢复编排 authority

## Decision Summary

本方案的核心决策如下：

1. 新增 `using-ahe-workflow`，作为 AHE workflow family 的公开入口、命令入口和 family explainer。
2. 将当前 `ahe-workflow-starter` 所承载的 runtime kernel 职责，收敛到新的 `ahe-workflow-router`。
3. `ahe-workflow-starter` 在迁移期保留为 compatibility alias，而不是立即删除。
4. `using-ahe-workflow` 只负责“如何进入 AHE”，不负责 profile 选择、stage 判断、review dispatch 或 transition map。
5. runtime handoff、`Next Action Or Recommended Skill`、reviewer return contract 中，未来 canonical 值应写 `ahe-workflow-router`，而不是 `using-ahe-workflow`。

一句话概括：

- **`using-ahe-workflow` 取代 starter 的公开入口角色**
- **`ahe-workflow-router` 取代 starter 的 runtime kernel 角色**
- **`ahe-workflow-starter` 作为过渡层逐步退场**

## Why This Is Different From The Earlier Defer

`docs/ahe-p1-optional-assets-decision.md` 曾明确 defer `using-ahe-skills`，原因成立：

- 当时如果直接新增一个 family meta-skill，它很容易和 starter 职责重叠
- 它会变成“第二个入口 kernel”
- 它会增加触发歧义和维护税

当前这份方案与那次 defer 的前提不同：

1. 这次不是新增一个模糊的 `using-ahe-skills`，而是新增**workflow 专用**的 `using-ahe-workflow`
2. 它有明确边界：只承担 public entry，不承担 runtime routing
3. 同时引入 `ahe-workflow-router`，把 kernel 从 starter 中显式抽出来

因此，这不是“再加一个 starter”，而是把：

- **公开入口**
- **运行时权威路由**

从一个过重的 starter 中拆成两层。

## Problem Statement

当前 AHE 的真实状态已经不是“有没有入口”，而是“入口和 kernel 绑在同一个 skill 上”。

这带来几个结构问题：

- `ahe-workflow-starter` 既是家族入口，又是 runtime router，又承担大量 family explainer 文本，主文件过重
- `docs/ahe-workflow-entrypoints.md` 与 `docs/ahe-command-entrypoints.md` 已经在尝试描述更低摩擦入口，但公开入口仍然直接暴露 starter
- leaf skills、reviewer return contract、transition map 和 execution semantics 都把 starter 当作 reroute 目标，使 starter 同时承担“public shell”和“runtime kernel”两层语义
- 若未来真的想让 AHE 更像 `agent-skills-main` 那样有一个更稳定的 family entrypoint，目前 starter 的命名和职责都不够适合作为那层产品化外壳

因此，本方案要解决的不是“把 starter 换个更好听的名字”，而是：

- 让 AHE 拥有一个更像 `using-agent-skills` 的公开入口
- 同时保留 AHE 当前最强的 route-first / evidence-first workflow kernel

## Goals

本方案的目标：

1. 让 `using-ahe-workflow` 成为新的 family public entrypoint
2. 保留 AHE 当前的 workflow kernel，不削弱 route-first、evidence-first 和 gate-first
3. 把“公开入口语义”和“runtime 路由语义”拆开，减少 starter 的混合职责
4. 降低新会话和命令入口的认知摩擦
5. 为未来真实的命令资产、setup 资产和对外 adopt 预留稳定入口
6. 以最小 breakage 完成迁移，不在第一轮就全仓暴力改名

## Non-Goals

本方案不做以下事情：

- 不在第一轮直接删除 `ahe-workflow-starter`
- 不把 `using-ahe-workflow` 做成第二个重型 kernel
- 不让 `using-ahe-workflow` 进入 `Next Action Or Recommended Skill`
- 不削弱 `ahe-workflow-starter` 当前承载的 pause points、review dispatch、profile-aware transition 和 reroute authority
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
| Compatibility alias | `ahe-workflow-starter` | 迁移期兼容旧文档、旧 handoff、旧 reroute target | 长期继续作为 canonical runtime 名称 |
| Leaf skills | `ahe-specify` / `ahe-design` / `ahe-test-driven-dev` 等 | 完成本节点职责，写回 local output 与 canonical handoff | 决定 profile、决定整个主链下一步 |

## Naming Decision

### Why `using-ahe-workflow`

优先使用 `using-ahe-workflow`，而不是 `using-ahe-skills`：

- AHE 当前要解决的是 **workflow family entrypoint**，不是整个仓库所有 skill 的总导航
- 它与 `references/agent-skills-main/skills/using-agent-skills/SKILL.md` 的相似点在“入口层角色”，但作用域应更窄、更贴近 AHE 实际目标
- 它天然适合作为 README、命令入口、future setup 文档中的对外名称

### Why `ahe-workflow-router`

优先使用 `ahe-workflow-router`，而不是继续沿用 starter 或改成 `kernel`：

- 当前 live contracts 里频繁出现的是 route / reroute / stage / next step 语义
- `router` 比 `starter` 更准确表达它在 workflow 内部的权威职责
- `kernel` 虽然也准确，但更抽象；`router` 更贴近 leaf skill 的 fallback 语言和 shared conventions

### Alias policy

迁移期采用以下策略：

- **公开入口写法**：优先 `using-ahe-workflow`
- **runtime canonical 写法**：优先 `ahe-workflow-router`
- **兼容旧写法**：读时继续接受 `ahe-workflow-starter`
- **新文档 / 新 handoff**：逐步停止继续写 `ahe-workflow-starter`

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

### Rule 3. `ahe-workflow-starter` 迁移期只做 alias

迁移期允许：

- 旧 leaf skill 继续回 `ahe-workflow-starter`
- 旧 reviewer return contract 继续写 `ahe-workflow-starter`
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
   - 把 `using-ahe-workflow` 当成新 starter kernel
   - 在 route 不清时硬做 direct invoke
   - 把 runtime handoff 写成 `using-ahe-workflow`

这个 skill 的正确结尾行为通常是：

- direct invoke 一个明确的 leaf skill
- 或明确交给 `ahe-workflow-router`

而不是自己展开完整 transition map。

## Proposed `ahe-workflow-router` Contract

`ahe-workflow-router` 应承接当前 starter 的 runtime authority，核心包括：

- Workflow Profile 选择
- canonical 当前节点判断
- mainline / `ahe-hotfix` / `ahe-increment` 分支切换
- review dispatch
- reviewer return contract 消费
- pause points / non-pause points
- result-driven transition map
- execution semantics 与恢复编排

它应保留当前 starter 最强的那部分能力，但把：

- family explainer
- public onboarding
- command-facing guidance

尽量移出主文件，交给 `using-ahe-workflow` 和外围 docs。

## Migration Plan

### Phase 0. Freeze the design

先冻结以下结论：

- `using-ahe-workflow` 是 public entrypoint
- `ahe-workflow-router` 是 runtime kernel
- `ahe-workflow-starter` 是 compatibility alias
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
- runtime fallback 仍然先维持 `ahe-workflow-starter`

完成标志：

- AHE 已拥有新的公开入口
- 但 runtime contracts 尚未破坏

### Phase 2. Split starter into router

新增：

- `skills/ahe-workflow-router/SKILL.md`

处理方式：

- 将 `ahe-workflow-starter` 的 runtime authority 收敛为 router 写法
- `ahe-workflow-starter/SKILL.md` 先变成 thin compatibility wrapper，说明其 canonical successor 是 `ahe-workflow-router`
- starter 里偏 public-explainer 的内容迁移到 `using-ahe-workflow`

这一步不要求一次搬空所有 reference files。

优先原则：

- 先稳定语义
- 再决定物理路径是否整体改名

完成标志：

- AHE 中“公开入口”和“runtime router”首次被显式拆开

### Phase 3. Migrate runtime vocabulary

更新以下位置的 canonical 写法：

- `docs/ahe-workflow-shared-conventions.md`
- router / starter references
- reviewer return contract
- transition map
- execution semantics
- leaf skill 的 reroute 语句

写法变化：

- 旧：回 `ahe-workflow-starter`
- 新：回 `ahe-workflow-router`

兼容策略：

- 读时接受 starter
- 写时优先 router

完成标志：

- 新生成的 runtime artifacts 不再写 starter
- starter 仅用于兼容读取旧契约

### Phase 4. Sweep leaf skills

这一轮统一修改 leaf skills：

- Authoring：`ahe-specify`、`ahe-design`、`ahe-tasks`
- Review：`ahe-spec-review`、`ahe-design-review`、`ahe-tasks-review`、`ahe-test-review`、`ahe-code-review`、`ahe-traceability-review`
- Implementation / branch：`ahe-test-driven-dev`、`ahe-hotfix`、`ahe-increment`
- Gates / finalize：`ahe-regression-gate`、`ahe-completion-gate`、`ahe-finalize`

统一目标：

- direct invoke 不清时，回 router
- chain contract 的 reroute target 改为 router
- reviewer / gate 结论恢复编排时，引用 router 而不是 starter

完成标志：

- live family 的 canonical reroute target 已统一

### Phase 5. Retire starter

最后才考虑：

- 保留 `ahe-workflow-starter` 为 deprecated alias
- 或在确认全家族已不再写 starter 后删除

进入条件：

- 新文档不再写 starter
- 新 skill / template / examples 不再写 starter
- 历史工件不需要批量回写
- read-time alias 规则已稳定

## File Categories To Update

### Public entry layer

- `README.md`
- `skills/README.md`
- `docs/ahe-workflow-entrypoints.md`
- `docs/ahe-command-entrypoints.md`

### Router layer

- `skills/ahe-workflow-starter/SKILL.md`
- `skills/ahe-workflow-starter/references/review-dispatch-protocol.md`
- `skills/ahe-workflow-starter/references/reviewer-return-contract.md`
- `skills/ahe-workflow-starter/references/execution-semantics.md`
- `skills/ahe-workflow-starter/references/profile-node-and-transition-map.md`
- future `skills/ahe-workflow-router/SKILL.md`

### Leaf skill contracts

- 所有 `skills/ahe-*/SKILL.md`
- 尤其是写有“若阶段不清 / route 冲突则回 starter”的那些 skill

### Shared conventions and templates

- `docs/ahe-workflow-shared-conventions.md`
- review / verification 模板示例
- any example that writes `Next Action Or Recommended Skill: ahe-workflow-starter`

### Analysis, decision and plan docs

- `docs/agent-skills-main-vs-ahe-workflow-report.md`
- `docs/ahe-workflow-family-optimization-execution-plan.md`
- `docs/ahe-review-subagent-implementation-checklist.md`
- `docs/ahe-p1-optional-assets-decision.md`

## Risks And Controls

| 风险 | 说明 | 控制方式 |
| --- | --- | --- |
| `using-ahe-workflow` 重新长胖 | public entry 又变成第二个 starter | 明确禁止它承载 profile、transition map、pause-point machine contract |
| runtime handoff 被污染 | `using-ahe-workflow` 被写进 `Next Action Or Recommended Skill` | 在 shared conventions 中明确禁用，并在 examples 中只写 router |
| starter 改名导致大范围 breakage | leaf skills、review docs、transition map 还在写 starter | 分阶段 alias 迁移，读时兼容 starter |
| path churn 过大 | starter references 物理路径改动过早，导致 repo 大量引用失效 | 先改语义与 canonical name，再决定是否搬物理路径 |
| 旧决策文档与新方案冲突 | 外部读者看到旧 defer 结论会困惑 | 在后续 decision sweep 中明确：旧 defer 针对的是无 router 分层的 meta-skill 方案 |
| 入口层和命令层重复 | `using-ahe-workflow` 与 `/ahe-*` 命令文档相互复制 | 命令只保留 bias；family explainer 统一放在 `using-ahe-workflow` |

## Rejected Alternative

### Alternative A. Direct delete starter and repoint everything to `using-ahe-workflow`

不推荐。

原因：

- discovery layer 和 runtime router 被迫使用同一个名字
- `using-*` 命名天然更像 public shell，不像 canonical reroute target
- leaf skills、reviewer return contract、transition map 和 execution semantics 都会立即大面积 break
- 最终不是得到更清晰的架构，而是把 starter 的重量原样搬到另一个名字上

### Alternative B. Keep starter as the only entrypoint and merely add more docs

也不推荐作为最终方案。

原因：

- 这能继续维持现状，但无法真正解决“starter 同时承担公开入口和 runtime kernel”的混合职责
- 也无法满足“用新的 `using-ahe-workflow` 替代 starter 作为命令入口”的目标

## Acceptance Criteria

当本方案真正完成时，至少应满足：

- 新会话与命令入口默认从 `using-ahe-workflow` 进入
- `using-ahe-workflow` 没有复制 router 的 machine contract
- runtime reroute 统一写 `ahe-workflow-router`
- `Next Action Or Recommended Skill` 不写 `using-ahe-workflow`
- `ahe-workflow-starter` 已降级成 alias，而不是继续承担 canonical runtime authority
- leaf skills、reviewer return contract、transition map 和 execution semantics 不再依赖 starter 作为唯一 canonical 名称

## Recommended Immediate Next Batch

如果紧接着执行下一批，而不是继续停留在讨论层，推荐顺序如下：

1. 新增 `skills/using-ahe-workflow/SKILL.md`
2. 更新 `docs/ahe-workflow-entrypoints.md`
3. 更新 `docs/ahe-command-entrypoints.md`
4. 新增 `skills/ahe-workflow-router/SKILL.md`
5. 将 `ahe-workflow-starter` 改成 thin alias
6. 最后再做 family-wide reroute vocabulary sweep

## One-Sentence Recommendation

最佳路径不是“直接删 starter”，而是“先让 `using-ahe-workflow` 接管公开入口，再把 starter 显式收缩为 `ahe-workflow-router`，最后再退休 starter”。
