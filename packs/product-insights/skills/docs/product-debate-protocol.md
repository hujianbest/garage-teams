# Product Debate Protocol

## Purpose

本文定义 `ahe-product-skills/` 在洞察和创新阶段的默认多 agent 讨论 / PK 机制。

目标不是为了“让 agent 聊天更热闹”，而是为了避免单个 agent：

- 太快收敛到第一个看起来合理的方向
- 只会补强自己的直觉，而不会主动挑战
- 把“有道理”误判成“有吸引力”

## Where Debate Is Required

以下节点默认启用多 agent 讨论 / PK：

- `ahe-insight-mining`
- `ahe-opportunity-mapping`
- `ahe-concept-shaping`

以下节点默认只在必要时启用 debate：

- `ahe-assumption-probes`

## Debate Roles

标准 PK 至少包含 3 个角色：

1. `Scout`
   负责带回证据，不抢着做最终判断。
2. `Advocate`
   负责替候选 insight / opportunity / concept 建立最强正方论证。
3. `Contrarian`
   负责指出平庸化风险、伪需求、脆弱前提和 table stakes 幻觉。

若需要正式收敛，再加第 4 个角色：

4. `Referee`
   负责比较双方论证质量、证据强度和 surviving options，输出 verdict。

## Required Agents

默认可复用：

- `agents/product-web-researcher.md`
- `agents/github-pattern-scout.md`
- `agents/product-thesis-advocate.md`
- `agents/product-contrarian.md`
- `agents/product-debate-referee.md`
- `agents/wedge-synthesizer.md`

## Round Structure

### Round 1: Gather

由 `Scout` 角色并行收集证据：

- 用户与社区信号
- 替代品与竞品信号
- GitHub / 开源模式

### Round 2: Propose

由 `Advocate` 根据证据提出：

- 最值得放大的 insight
- 最值得下注的 opportunity
- 最有 pull 的 concept

### Round 3: Attack

由 `Contrarian` 挑战：

- 哪些方向只是 commodity clone
- 哪些价值被高估
- 哪些前提未经验证

### Round 4: PK

由 `Referee` 对候选项做比较，至少回答：

- 哪个方向 survive
- 哪个方向暂缓
- 哪个方向应直接淘汰
- 哪些问题要留到 probe 再验证

## PK Rules

所有 debate 都应遵守：

1. 先有候选项，再 PK，不要对空气争论。
2. 先有证据，再开打，不要只拼措辞。
3. 允许保留多个 surviving options，但必须排出优先级。
4. 若结论仍高度分裂，不要硬拍板，转成 `Untested` 问题。
5. 最终只允许单 writer 写主文档。

## Output Contract

在主文档中，至少保留一段简短 `Debate Verdict`，说明：

- 参与 PK 的候选项
- 最强支持理由
- 最强反对理由
- 最终保留方向
- 被淘汰方向及原因

## Anti-Patterns

- 让多个 agent 同时改主文档。
- 没有候选项就让 agent 空打。
- 只有反方，没有正方。
- 有分歧时直接取平均，而不是回到证据。
- 把“agent 观点数量多”当成“结论更正确”。
