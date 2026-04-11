# Product Insight Shared Conventions

## Purpose

本文定义 `ahe-product-skills/` 的共享约定，目标是在保持创造性的同时，确保输出能稳定进入后续 `ahe-coding-skills`。

## Family Role

本家族负责回答这些问题：

- 这个产品机会到底值不值得做？
- 它为什么会比“又一个同类产品”更有吸引力？
- 哪个用户、哪个场景、哪个 wedge 最值得先打？
- 在写规格和做实现之前，哪些假设必须先被暴露和验证？

本家族不负责：

- 直接写实现设计
- 直接拆任务
- 直接写代码
- 把“一个好点子”伪装成“已批准需求”

## Shared Artifact Types

默认产物分成 5 类：

1. `insight-pack`
   聚合用户信号、替代品、竞品模式、GitHub / 社区观察、显著 tensions 和 no-go 信号。
2. `opportunity-map`
   把目标 outcome、JTBD、机会分支和优先机会整理成结构化视图。
3. `concept-brief`
   对选定机会提出多个概念方向，并收敛出差异化 wedge。
4. `probe-plan`
   把关键未知项转成低成本验证实验。
5. `spec-bridge`
   把以上内容压缩成 `ahe-coding-skills/ahe-specify` 可消费的 pre-spec 输入。

## Evidence Labels

为避免把想象误写成事实，默认使用以下标签：

- `Observed`：有明确来源的事实，例如用户话语、数据、代码、网页或 GitHub 项目。
- `Inferred`：基于多个事实形成的解释。
- `Invented`：刻意发散出的新概念、新 wedge 或新 framing。
- `Untested`：尚未验证、但会影响成败的关键假设。

如果一个结论无法落到 `Observed` 或 `Inferred`，不要把它写成“用户一定会要”。

## Creativity Rules

所有 product insight 节点都应遵守：

1. 先生成至少 3 个 framing 或 concept，再做第一次收敛。
2. 至少对 1 个“看起来最合理”的方向做反向挑战。
3. 优先寻找用户已有的工作流、替代品和 workaround，而不是先想功能列表。
4. 每次收敛都要回答：
   - 为什么这个方向值得做？
   - 为什么现在值得做？
   - 为什么这个方向不只是同类产品换皮？
5. 若没有明确差异化，不要急着进入 `ahe-coding-skills`。

## Multi-Agent Debate Rules

在洞察和创新阶段，默认不要只依赖单个 agent 的第一次答案。

以下节点默认启用多 agent 讨论 / PK：

- `ahe-insight-mining`
- `ahe-opportunity-mapping`
- `ahe-concept-shaping`

默认 debate 至少包含：

- `Scout`：带回证据
- `Advocate`：建立最强正方论证
- `Contrarian`：指出 commodity 和伪需求风险
- `Referee`：比较双方并给出 verdict

所有 debate 都应满足：

1. 先并行，再收敛。
2. 先有候选项，再 PK。
3. 先有证据，再论胜负。
4. 允许保留多个 surviving options，但必须给出排序。
5. 最终只允许单 writer 写主文档。

共享协议见：

- `ahe-product-skills/docs/product-debate-protocol.md`

## Default Output Paths

默认落盘到：

- `docs/insights/YYYY-MM-DD-<topic>-insight-pack.md`
- `docs/insights/YYYY-MM-DD-<topic>-opportunity-map.md`
- `docs/insights/YYYY-MM-DD-<topic>-concept-brief.md`
- `docs/insights/YYYY-MM-DD-<topic>-probe-plan.md`
- `docs/insights/YYYY-MM-DD-<topic>-spec-bridge.md`

## Handoff Into `ahe-coding-skills`

进入 `ahe-coding-skills` 之前，至少应具备：

- 一个明确的目标用户或用户段
- 一个明确的 desired outcome
- 一个明确的优先机会，而不是一组散点痛点
- 一个候选概念或 wedge
- 一组被标出的关键假设
- 一份 `spec-bridge`

默认 handoff 目标是：

- `ahe-coding-skills/ahe-specify/SKILL.md`

因为 coding family 需要的是：

- 可规格化的问题定义
- 可以被验收的目标和边界
- 明确的范围外内容
- 已显式列出的关键未知项

它不应替 product family 去发明这些内容。

## Recommended Source Pattern

默认优先结合：

- 用户当前描述与现有项目材料
- Web 上的官方资料、产品页面、社区讨论和评论信号
- GitHub 上的相邻仓库、开源产品、agent / skill 项目
- 必要时的只读 repo 上下文

## Anti-Patterns

- 还没搞清用户 progress，就开始写一堆 feature。
- 把竞品功能列表直接抄成路线图。
- 用“摄影社区”“AI 工作台”这类大类目替代具体价值命题。
- 只写亮点，不写 no-go 信号和危险假设。
- 上游没有 spec-bridge，就把模糊 idea 直接扔进 `ahe-coding-skills`。
