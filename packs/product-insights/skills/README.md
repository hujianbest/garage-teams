# AHE Product Skills

`ahe-product-skills/` 用于存放 AHE 里偏产品发现、机会收敛、概念塑形和假设验证的上游 skill 资产。

它与 `ahe-coding-skills/` 的关系是：

- `ahe-product-skills/`：帮助把模糊想法收敛成更有吸引力、更有差异化、更值得实现的产品输入。
- `ahe-coding-skills/`：在需求已经相对清晰后，负责高纪律地规格化、设计、任务化和实现。

## 目录约定

- `ahe-product-skills/README.md`：本目录总览。
- `ahe-product-skills/docs/`：共享约定、方法来源和 handoff 规则。
- `ahe-product-skills/templates/`：洞察、机会、概念、验证与 bridge 模板。
- `ahe-product-skills/<skill-name>/SKILL.md`：单个 skill 的入口文件。

## Public Entry Skill

- `ahe-product-skills/using-ahe-product-workflow/`：本家族的公开入口，用于判断当前应从哪个产品洞察节点起步。

## 最短用法

如果你只知道“先别写代码，先帮我把产品方向想清楚”，默认从 `using-ahe-product-workflow` 开始。

推荐一句话提示词：

> 先不要进入 `ahe-coding-skills`，先用 `ahe-product-skills` 帮我判断这个想法值不值得做、该先打哪个机会，并告诉我下一步进入哪个节点。

## 什么时候用

在这些场景优先用 `ahe-product-skills/`：

- 用户只有一个模糊 idea，还说不清目标用户、desired outcome 和替代方案
- 项目已经做完，但“很一般”“没吸引力”“像 category clone”
- 想先做 web / GitHub / 社区 research，而不是直接想 feature
- 已经有一些证据，但还没决定先打哪个机会
- 需要提出多个 concept direction，并让多个 agent 讨论 / PK
- 方向看起来不错，但还没做低成本验证
- 需要把上游洞察压成可交给 `ahe-coding-skills` 的 pre-spec 输入

不要在这些场景使用：

- 已经有稳定需求规格，当前只是继续设计、拆任务或实现
- 当前只是解决局部技术问题
- 当前只需要 `ahe-coding-skills` 节点级工作

## 如何开始

1. 如果你还不知道该从哪个节点起步，先走 `using-ahe-product-workflow`。
2. 如果 idea 还是大词和品类名，先走 `ahe-outcome-framing`。
3. 如果需要补真实外部信号，先走 `ahe-insight-mining`。
4. 如果需要从多个痛点里选优先机会，走 `ahe-opportunity-mapping`。
5. 如果机会已选但解法仍然平庸，走 `ahe-concept-shaping`。
6. 如果方向已成形但关键未知项还没暴露，走 `ahe-assumption-probes`。
7. 如果已经有 outcome、机会、wedge 和关键假设，走 `ahe-spec-bridge` 把结果交给 `ahe-coding-skills`。

## 当前技能目录

- `ahe-outcome-framing/`：把模糊想法重写成可判断的 outcome、目标用户、替代方案和焦点问题。
- `ahe-insight-mining/`：从 web、GitHub、社区、替代品与现有上下文中提取洞察和白空间信号。
- `ahe-opportunity-mapping/`：把证据整理成 JTBD / Opportunity / wedge 视图。
- `ahe-concept-shaping/`：对候选方向做概念发散、反 commodity 挑战和差异化收敛。
- `ahe-assumption-probes/`：把危险未知项转成低成本验证探针。
- `ahe-spec-bridge/`：把上游产物整理成可交给 `ahe-coding-skills` 的 pre-spec bridge。

## 配套子 Agents

位于仓库根目录 `agents/`：

- `product-web-researcher.md`：提取用户、社区、替代品和竞品信号。
- `github-pattern-scout.md`：研究 GitHub / 开源里的常见模式、白空间和同质化风险。
- `product-thesis-advocate.md`：替候选 insight、opportunity 或 concept 建立最强正方论证。
- `product-contrarian.md`：挑战“看起来正确但其实普通”的 framing。
- `product-debate-referee.md`：比较正反双方论证并输出 PK verdict。
- `wedge-synthesizer.md`：对多个概念方向做比较并收敛 wedge。
- `probe-designer.md`：把危险假设转成便宜 probe 和 kill criteria。

## 多 Agent 讨论 / PK

在洞察和创新阶段，默认不是“一个 agent 想完就算”，而是：

1. 先由 `Scout` agents 带回证据。
2. 再由 `Advocate` 替候选方向建立最强支持论证。
3. 再由 `Contrarian` 主动找 commodity 风险和伪需求。
4. 最后由 `Referee` 输出 PK 结果，再由主 skill 单点落盘。

共享协议见：

- `ahe-product-skills/docs/product-debate-protocol.md`

## 默认产物位置

默认将中间产物写到：

- `docs/insights/YYYY-MM-DD-<topic>-insight-pack.md`
- `docs/insights/YYYY-MM-DD-<topic>-opportunity-map.md`
- `docs/insights/YYYY-MM-DD-<topic>-concept-brief.md`
- `docs/insights/YYYY-MM-DD-<topic>-probe-plan.md`
- `docs/insights/YYYY-MM-DD-<topic>-spec-bridge.md`

## 使用建议

1. 先从 `using-ahe-product-workflow/SKILL.md` 判断当前节点。
2. 用产品 skill 产出洞察、机会、概念和验证计划。
3. 进入 `ahe-spec-bridge`，把结果压缩成可交给 `ahe-coding-skills/ahe-specify` 的输入。
4. 再进入 `ahe-coding-skills/` 走精确实现链路。

## 提示词案例

下面这些提示词都可以直接触发 `ahe-product-skills/`：

### 1. 不知道该从哪里开始

```text
先不要写代码，先用 ahe-product-skills 帮我判断现在该从哪个节点开始。
这个想法还很模糊，我想先知道应该先做 framing、research、机会收敛还是验证。
```

典型进入节点：`using-ahe-product-workflow`

### 2. 先重写问题定义

```text
我想做一个给自由摄影师用的产品，但现在还停留在大类目。
先别想功能，先用 ahe-product-skills 帮我重写问题定义、目标用户、desired outcome 和替代方案。
```

典型进入节点：`ahe-outcome-framing`

### 3. 先做外部 research

```text
我想做一个摄影协作方向的产品。
先用 ahe-product-skills 看 web、GitHub、社区和替代品信号，判断这个方向是不是 commodity。
```

典型进入节点：`ahe-insight-mining`

### 4. 让多个 agent 讨论 / PK

```text
这个方向我已经有一些初步想法了。
请用 ahe-product-skills 先做多 agent 讨论 / PK：先 research，再让不同立场的 agent 辩论，最后收敛出 surviving insight 和下一步机会。
```

典型进入节点：`ahe-insight-mining` 或 `ahe-opportunity-mapping`

### 5. 先选最值得打的机会

```text
我已经有一些洞察和痛点列表了，但还没想清楚先打哪个机会。
请用 ahe-product-skills 帮我整理 JTBD / opportunity map，并明确为什么不选其他机会。
```

典型进入节点：`ahe-opportunity-mapping`

### 6. 生成多个 wedge 方向

```text
这个方向还是很像竞品。
请用 ahe-product-skills 至少给我 3 个 concept direction，并做反 commodity challenge，最后选出一个最有吸引力的 wedge。
```

典型进入节点：`ahe-concept-shaping`

### 7. 先做低成本验证

```text
先不要进规格，也先不要实现。
请用 ahe-product-skills 把这条方向里最危险的 1 到 3 个假设做成低成本 probe，并写清楚 pass / fail / kill criteria。
```

典型进入节点：`ahe-assumption-probes`

### 8. 交给 coding family 之前做 bridge

```text
现在已经有 insight、机会、concept 和 probe 结果了。
请用 ahe-product-skills 把这些内容压缩成一个 spec bridge，作为交给 ahe-coding-skills/ahe-specify 的输入。
```

典型进入节点：`ahe-spec-bridge`

## 设计原则

- 先发散，再收敛，不允许刚开始就把 feature 当答案。
- 明确区分 `证据`、`推断`、`概念` 和 `待验证假设`。
- 输出必须既保留创造性，也能形成下一步实现输入。
- 子 agent 应小而专注，避免一个 agent 同时承担“调研 + 创意 + 决策 + 写主文档”。
