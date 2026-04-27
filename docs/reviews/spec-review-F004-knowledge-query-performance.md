# 规格评审记录：F004 知识查询性能优化

## Metadata

- Review Type: HF Spec Review
- Scope: `docs/features/F004-knowledge-query-performance.md`
- Reviewer: Independent HF Spec Reviewer
- Date: 2026-04-17
- Record Path: `docs/reviews/spec-review-F004-knowledge-query-performance.md`

## Inputs

- Primary Artifact: `docs/features/F004-knowledge-query-performance.md`
- Supporting Context:
  - `AGENTS.md`
  - `task-progress.md`
  - `.garage/benchmark/baseline-20260416.json`
  - `scripts/benchmark.py`
  - `docs/features/F002-garage-live.md`
  - `docs/reviews/design-review-F001-garage-agent-os.md`
  - `docs/soul/design-principles.md`
  - `docs/soul/growth-strategy.md`

## Precheck 结果

**Precheck 通过**，可以进入正式 rubric review：

- 存在稳定、可定位的规格草稿：`docs/features/F004-knowledge-query-performance.md`
- `task-progress.md` 当前阶段为 `hf-specify`，下一步为 `hf-spec-review`
- 规格文档状态为“草稿”，与当前 workflow 状态一致
- 未发现 route / stage / evidence 冲突；无需 reroute 到 `hf-workflow-router`

## 结构契约确认

当前规格符合本仓库 `docs/features/Fxxx` 作为 spec 的约定，也基本遵循了 Garage 当前 feature spec 的常见骨架：

1. 背景与问题陈述
2. 目标与成功标准
3. 用户角色与关键场景
4. 当前轮范围与关键边界
5. 范围外内容
6. 功能需求
7. 非功能需求
8. 外部接口与依赖
9. 约束与兼容性要求
10. 假设与失效影响
11. 开放问题
12. 术语与定义

结构完整，未发现需要因为模板/骨架问题而阻塞评审的情况。

## Rubric 评审摘要

### Group Q: Quality Attributes

- 优点：核心目标、阈值和大部分验收标准已具备可判断性，范围边界也比较清晰。
- 问题：仍有关键 trace anchor 不稳定，且 benchmark overall verdict 规则尚未闭合。

### Group A: Anti-Patterns

- 未发现明显的设计泄漏、占位值残留或只写 happy path 的问题。
- `FR-403` 对缺失/过期/损坏辅助状态的负路径覆盖较好。

### Group C: Completeness And Contract

- 优点：核心 FR/NFR 基本都具备 `ID`、`Statement`、`Acceptance`、`Priority`、`Source`。
- 问题：`11.2.1` 被标为“非阻塞开放问题”，但它实际决定 benchmark 的通过/失败语义，尚不能视为真正闭合。

### Group G: Granularity And Scope-Fit

- 当前规格仍然是可修复的，问题集中且可在 1-2 轮内定向回修。
- 未发现需要整份规格推倒重写的 oversized requirement。

## 结论

**需修改**

该规格已经具备明确的问题背景、可量化的性能目标和较好的范围边界，整体方向是对的；但目前还不能作为稳定的设计输入，主要因为：

- benchmark 的 overall verdict / exit semantics 尚未收敛为单一规则
- 若干核心 requirement 的 source / trace anchor 仍依赖不存在或不稳定的证据

这些问题都集中在协议闭合和追溯性，不需要改写整份 spec，但在进入 approval step 前应补齐。

## 发现项

- [important][LLM-FIXABLE][Q8] `背景`、`FR-401` 和 `ASM-402` 使用了 “`task-progress.md` 记录了 895% 退化” 这一锚点，但当前 evidence baseline 中并不存在该记录；仓库内可核实的退化证据是 `.garage/benchmark/baseline-20260416.json` 中的 `growth_percent = 1091.89`。这会让核心问题陈述和来源回指失真，应改为文件可验证的来源或删除 `895%` 说法。
- [important][USER-INPUT][C3] benchmark 的总体通过规则尚未闭合。`2.2 成功标准` 要求同时满足 `p90@1000 <= 5ms` 和相对退化 `<= 500%`，但 `11.2.1` 仍把“继续沿用相对阈值或绝对阈值二选一通过”列为开放问题，而当前 `scripts/benchmark.py` 也确实使用 `rel_passed or abs_passed`。这不是纯 wording 问题，而是验收口径本身尚未定案，必须收敛为一个明确、可批准的规则。
- [important][USER-INPUT][Q8] `FR-403` 与 `CON-403` 把“用户确认允许内部索引/缓存，但不破坏现有数据格式和兼容性”“用户确认的范围边界”写成来源，但当前 review baseline 中没有任何稳定工件记录这项确认。是否允许 `cache`、是否允许引入任何额外维护动作，属于会影响方案空间的外部决策；需要把该确认落到权威工件中，或收窄为已有文档可直接支持的范围。
- [minor][LLM-FIXABLE][Q8] `FR-404` 将 “`F003` 依赖稳定的运行时检索” 作为来源，但仓库当前不存在 `docs/features/F003*` 规格文件。该 requirement 本身可以保留，但来源需要改成当前可验证的工件锚点，或将这句改写为下游依赖说明而不是当前 requirement 的 source。

## 缺失或薄弱项

- 缺一个单一、可批准的 benchmark verdict 定义：是双阈值都必须满足，还是保留 OR 逻辑，还是区分 hard fail 与 warning。
- 缺一个可回读的性能退化事实锚点，避免 `895%` 与 `1091.89%` 并存但只有后者可验证。
- 缺一个稳定的外部决策记录来支撑“允许内部索引/缓存”这类方案边界。
- `FR-404` 的来源锚点仍偏弱，需要改成仓库内可定位的当前证据。

## 下一步

- `hf-specify`

## 记录位置

- `docs/reviews/spec-review-F004-knowledge-query-performance.md`

## 交接说明

- 当前 verdict 为 **需修改**，不是 workflow blocker，不需要 reroute 到 `hf-workflow-router`
- 回修重点应先处理 USER-INPUT 问题：
  - benchmark overall verdict 的唯一口径
  - 辅助索引/缓存允许边界的权威确认
- 上述外部决策收敛后，再由 authoring 节点完成 LLM-FIXABLE 回修：
  - 清理 `895%` 的错误 trace anchor
  - 修正 `FR-404` 的 source
- 本轮问题集中、修复方向清晰；预计 1-2 轮定向修订后可再次进入 `hf-spec-review`
