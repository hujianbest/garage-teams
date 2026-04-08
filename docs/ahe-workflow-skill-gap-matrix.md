# AHE workflow skill gap matrix

**Router-era 注：** 矩阵中曾把“过重 orchestrator”记在 pre-split **legacy 合并入口/router** 名下；现应理解为 **`ahe-workflow-router`**（kernel）与 **`using-ahe-workflow`**（公开入口）分层后的剩余 gap。

## 目的

本文基于 `docs/ahe-workflow-skill-anatomy.md` 的目标态 anatomy，评估当前 `skills/ahe-*/SKILL.md` 的结构偏差，并把 `P0-4` / `P0-5` 的改造顺序细化成可直接执行的批次。

它回答 3 个问题：

1. 当前哪些 `ahe-*` skill 离目标态最远
2. 哪些 gap 是家族级共性问题，哪些是局部问题
3. 在不打乱 `docs/ahe-workflow-family-optimization-execution-plan.md` 依赖关系的前提下，后续应该按什么顺序改

本文不是行为正确性审计，也不是当前 skill 的完整 code review；它只聚焦 anatomy 对齐与 skill 设计质量。

## 评估维度

本轮 gap matrix 主要按以下目标态维度评估：

- frontmatter 是否同时说明 `what` 和 `when`
- 是否有清晰的 `When to Use`
- `Workflow` 是否足够具体、可执行
- `Output Contract` 是否明确
- 是否存在高质量的 `Common Rationalizations`
- 是否存在可观察的 `Red Flags`
- `Verification` 是否以证据为中心
- direct invoke / chain invoke 语义是否清楚
- 是否合理使用 progressive disclosure
- 是否体现 evidence-first

## 家族级共性问题

这些问题不属于单个 skill，而是当前 live `ahe-*` 的共性偏差：

- 几乎所有 live skills 都还没有显式写成 `standalone contract` / `chain contract`。
- `Common Rationalizations` 在家族里明显偏弱，只有极少数 skill 接近目标态。
- 许多 skill 已经有强输出语义，但还没有被明确写成 `Output Contract`。
- `Evidence-first` 整体是家族强项，但常常散落在步骤和门禁里，没有被结构化表达。
- progressive disclosure 不均衡，尤其是 `ahe-workflow-router`（及入口层 `using-ahe-workflow`）和 `ahe-test-driven-dev` 仍偏重。

## 偏差最大的 skill

下表按“距离目标态 anatomy 的差距”排序，不等同于“应该立刻先改”的执行顺序。

| 排名 | skill | 主要 gap | 建议归属 |
| --- | --- | --- | --- |
| 1 | `ahe-workflow-router`（+ 入口 `using-ahe-workflow`） | 缺显式 `Verification`、router 主文件过重、section skeleton 不统一、rationalizations 不完整 | `P0-2` + `P0-6` |
| 2 | `ahe-test-driven-dev` | 主文件过大、appendix 应下沉、dual-mode contract 未显式化、输出契约未标准命名 | `P0-4` Batch 5 |
| 3 | `ahe-spec-review` | `When to Use` 不够显式、缺 `Red Flags` / `Common Rationalizations`、dual-mode contract 缺失 | `P0-5` 第一波 |
| 4 | `ahe-design-review` | 与 `ahe-spec-review` 类似，结构更像现状说明而非目标态 reviewer skeleton | `P0-5` 第一波 |
| 5 | `ahe-tasks-review` | 与 spec/design review 同类问题，缺 reviewer archetype 的统一写法 | `P0-5` 第一波 |
| 6 | `ahe-bug-patterns` | 已较强，但 `Red Flags` / `Common Rationalizations` / dual-mode 仍不够显式 | `P0-5` 第二波 |

## 逐项说明

### 1. `ahe-workflow-router`（历史表述：pre-split 合并 router）

当前最大问题不是能力不够，而是 router 主文件过重、与公开入口分层后仍易把解释层堆回 kernel、目标态 skeleton 不够清晰。

最关键缺口：

- 缺一段明确的 `Verification` / 完成退出条件
- orchestrator 角色虽清楚，但没有按目标态 anatomy 显式表达 direct invoke / chain invoke 语义
- 长解释、矩阵、边界说明仍有较多内容留在主文件
- `Common Rationalizations` 只有局部片段，不是独立、稳定的章节

建议动作：

- 先执行 `P0-2`，对齐 router 主文件与 collateral
- 再在 `P0-6` 做第二轮瘦身，把长解释与矩阵继续下沉

### 2. `ahe-test-driven-dev`

这是最强的实现类 skill 之一，但与目标态 anatomy 的差距主要来自“太重”和“太隐式”。

最关键缺口：

- C++ / GoogleTest 等深度内容仍在主文件中，占用主上下文
- 已有强 handoff 与 evidence 约束，但还没有被重组为更标准的 `Output Contract`
- direct invoke / chain invoke 已隐含存在，但没有被显式命名

建议动作：

- 放在 `P0-4` 的后半波
- 先等 `task-progress` schema 与 core contract 统一，再处理它
- 改造时顺手做 progressive disclosure，把大 appendix 下沉到 `references/`

### 3. `ahe-spec-review`

它的核心问题是 reviewer archetype 还没有写成目标态 skeleton。

最关键缺口：

- 缺显式 `When to Use`
- 缺更明确的 `Red Flags`
- 缺 `Common Rationalizations`
- dual-mode contract 没有被结构化表达

建议动作：

- 作为 `P0-5` reviewer 第一波的起点
- 先把它打成 reviewer archetype 模板，再复用到同类 skill

### 4. `ahe-design-review`

与 `ahe-spec-review` 同类，适合和它成对改造。

最关键缺口：

- 缺 reviewer skeleton 的显式章节
- `反模式` 有，但没有形成 anatomy 所期望的 `Red Flags` + `Common Rationalizations` 双层结构
- direct invoke / chain invoke 没有清晰写出来

建议动作：

- 紧跟 `ahe-spec-review`
- 尽量复用同一个 reviewer 结构模板

### 5. `ahe-tasks-review`

这是 reviewer 第一波里第三个最该标准化的 skill。

最关键缺口：

- 与 spec/design review 同样缺 reviewer skeleton
- 输出契约和 review 语义存在，但结构上还不够统一
- dual-mode contract 仍主要靠隐含语义

建议动作：

- 放在 spec/design review 之后
- 三者应作为一个连续 sweep 完成

### 6. `ahe-bug-patterns`

它已经比前三个 reviewer 更接近目标态，但还有明显短板。

最关键缺口：

- `反模式` 已有，但 `Common Rationalizations` 仍偏弱
- `Red Flags` 可观察信号没有被单独结构化
- direct invoke / chain invoke 没有显式写成 contract

建议动作：

- 放在 reviewer 第二波
- 先等通用 reviewer vocabulary 稳定后再改更划算

## 看起来已经比较接近的 skill

这些 skill 仍然需要对齐目标态 anatomy，但不适合成为第一波优先改造对象：

| skill | 原因 |
| --- | --- |
| `ahe-specify` | 已有较强的 `Workflow`、`Red Flags`、`完成条件`，主要缺 dual-mode 显式化与命名统一 |
| `ahe-design` | 与 `ahe-specify` 类似，producer archetype 已较清楚 |
| `ahe-tasks` | producer skeleton 相对较完整，适合作为 core contract 统一批次的一部分 |
| `ahe-regression-gate` | gate archetype 已比较强，主要缺显式 contract 与 rationalizations |
| `ahe-completion-gate` | 与 regression gate 同类，结构上接近目标态 |
| `ahe-finalize` | finalizer archetype 已较完整，适合跟 gate 一起收敛 |
| `ahe-code-review` | 相比上游 reviewer trio，更接近目标态 reviewer 写法 |
| `ahe-test-review` | 已有较清楚的定位与适用时机，缺的是进一步标准化 |
| `ahe-traceability-review` | 同样更接近目标态 reviewer skeleton |
| `ahe-hotfix` | branch / re-entry archetype 已比较明确 |
| `ahe-increment` | 与 `ahe-hotfix` 类似，优先级可后置 |

## 执行顺序

这里区分两种顺序：

- `按 gap 大小排序`：看哪里偏差最大
- `按依赖执行排序`：看实际应该先改什么

真正执行时，应优先服从依赖顺序，而不是只看 gap 排名。

## 按依赖执行的推荐顺序

### Step 1. `P0-2` router collateral 对齐

先处理：

- `skills/ahe-workflow-router/SKILL.md`
- `skills/ahe-workflow-router/references/profile-selection-guide.md`
- `skills/ahe-workflow-router/references/routing-evidence-guide.md`
- `skills/ahe-workflow-router/references/routing-evidence-examples.md`
- `skills/ahe-workflow-router/references/review-dispatch-protocol.md`
- `skills/ahe-workflow-router/references/reviewer-return-contract.md`

原因：

- 当前它们之间已有显式冲突
- 不先对齐，会把旧字段、旧心智继续传播到后续 skill sweep

### Step 2. `P0-3` 对齐 `task-progress` schema

先改：

- `templates/task-progress-template.md`

原因：

- core skill 改造前，先稳定 canonical field
- 避免后面在 `Output Contract` 里再次出现漂移

### Step 3. `P0-4` core skills 第一波

建议顺序：

1. `ahe-specify`
2. `ahe-design`
3. `ahe-tasks`

原因：

- 这 3 个 producer archetype 最适合先打样
- 它们决定后续 chain contract 的上游输入形态

### Step 4. `P0-4` core skills 第二波

建议顺序：

1. `ahe-regression-gate`
2. `ahe-completion-gate`
3. `ahe-finalize`
4. `ahe-test-driven-dev`

原因：

- gate/finalize 的 output vocabulary 应先稳定
- `ahe-test-driven-dev` 体量最大，放在最后更容易复用前面已经稳定下来的 contract

如果更想严格遵循现有计划文件的列举顺序，也可以保持：

1. `ahe-test-driven-dev`
2. `ahe-regression-gate`
3. `ahe-completion-gate`
4. `ahe-finalize`

但从改造效率看，先 gate / finalize、后 TDD 更合适。

### Step 5. `P0-5` reviewer / branch 第一波

建议顺序：

1. `ahe-spec-review`
2. `ahe-design-review`
3. `ahe-tasks-review`

原因：

- 这 3 个是 reviewer archetype 中偏差最明显的一组
- 适合先统一成新的 reviewer skeleton

### Step 6. `P0-5` reviewer / branch 第二波

建议顺序：

1. `ahe-test-review`
2. `ahe-code-review`
3. `ahe-traceability-review`
4. `ahe-bug-patterns`

原因：

- 前 3 个已经有较清楚的定位与适用时机
- `ahe-bug-patterns` 适合在 reviewer 结构稳定后再对齐

### Step 7. `P0-5` reviewer / branch 第三波

建议顺序：

1. `ahe-hotfix`
2. `ahe-increment`

原因：

- branch / re-entry archetype 已相对稳定
- 适合放在 reviewer 第二波之后统一补 contract

### Step 8. `P0-6` router 第二轮瘦身

最后再处理：

- `skills/ahe-workflow-router/SKILL.md`
- `skills/ahe-workflow-router/references/*.md`

原因：

- 此时 family vocabulary、output contract、reviewer / gate 边界都已经稳定
- 更容易知道哪些说明真正应留在 router 主文件，哪些应继续下沉到 `references/` 或 `using-ahe-workflow`

## 批次建议

可直接转成后续执行批次：

| 批次 | 范围 | 目的 |
| --- | --- | --- |
| Batch A | router collateral | 关闭文档层冲突 |
| Batch B | `task-progress` 模板 | 冻结 canonical schema |
| Batch C | `ahe-specify` `ahe-design` `ahe-tasks` | 形成 producer archetype |
| Batch D | `ahe-regression-gate` `ahe-completion-gate` `ahe-finalize` `ahe-test-driven-dev` | 形成 gate / finalizer / implementation archetype |
| Batch E | `ahe-spec-review` `ahe-design-review` `ahe-tasks-review` | reviewer 第一波统一 |
| Batch F | `ahe-test-review` `ahe-code-review` `ahe-traceability-review` `ahe-bug-patterns` | reviewer 第二波统一 |
| Batch G | `ahe-hotfix` `ahe-increment` | branch / re-entry 对齐 |
| Batch H | router second slimming | 回收解释层、完成 kernel 收口 |

## 当前最值得进入的下一编辑入口

如果要继续直接改文件，最优入口不是 gap 最大的 `ahe-workflow-router` 主文件本体，而是：

1. `skills/ahe-workflow-router/references/profile-selection-guide.md`
2. `skills/ahe-workflow-router/references/routing-evidence-examples.md`
3. `skills/ahe-workflow-router/SKILL.md`

原因：

- 这一步属于 `P0-2`
- 它能先消除最明显的 collateral 冲突
- 做完之后再改模板与 core skills，返工最少

## 一句话结论

从目标态 anatomy 看，当前 AHE 最需要的不是“继续增加规则”，而是按依赖顺序把已有强能力结构化：先修 router collateral，再冻结 progress schema，然后分批把 producer、gate、reviewer 和 branch archetype 对齐到统一 skeleton。
