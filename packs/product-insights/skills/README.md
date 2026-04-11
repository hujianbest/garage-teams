# AHE Product Skills

`packs/product-insights/skills/` 是当前仓库里 `Product Insights Pack` 的来源技能面，承接 AHE 上游产品洞察 workflow 的 skill、共享文档、模板与配套 agents。

它在 phase 1 的定位是：

- `Garage` 的 product insights 来源资产
- `Product Insights Pack` 的参考 workflow 面
- 上游 research、opportunity、concept、probe 与 bridge 相关约定的维护入口

## 目录约定

- `packs/product-insights/skills/README.md`：本目录总览
- `packs/product-insights/skills/docs/`：共享约定、方法来源和 handoff 规则
- `packs/product-insights/skills/templates/`：洞察、机会、概念、验证与 bridge 模板
- `packs/product-insights/skills/<skill-name>/SKILL.md`：单个 skill 的入口文件

## 先看哪里

- 还不知道该从哪个节点起步时，先读 `packs/product-insights/skills/using-ahe-product-workflow/SKILL.md`
- 需要共享规则时，读 `packs/product-insights/skills/docs/`
- 需要模板时，读 `packs/product-insights/skills/templates/`
- 需要理解 pack 边界时，配合 `packs/product-insights/README.md` 和 `docs/design/D110-garage-product-insights-pack-design.md` 阅读

## 当前 workflow family

当前主要成员包括：

- `ahe-outcome-framing`
- `ahe-insight-mining`
- `ahe-opportunity-mapping`
- `ahe-concept-shaping`
- `ahe-assumption-probes`
- `ahe-spec-bridge`

## 配套 agents

当前 product insights 相关 agents 位于 `packs/product-insights/agents/`，例如：

- `product-web-researcher.md`
- `github-pattern-scout.md`
- `product-thesis-advocate.md`
- `product-contrarian.md`
- `product-debate-referee.md`
- `wedge-synthesizer.md`
- `probe-designer.md`

## 什么时候用

在这些场景优先用这一组 skills：

- 用户只有一个模糊 idea，还说不清目标用户、desired outcome 和替代方案
- 想先做 web / GitHub / 社区 research，而不是直接写 feature
- 已经有一些证据，但还没决定先打哪个机会
- 需要提出多个 concept direction，并让多个 agent 讨论 / PK
- 需要把上游洞察压成可交给 coding workflow 的 bridge 输入

不要在这些场景使用：

- 已经有稳定需求规格，当前只是继续设计、拆任务或实现
- 当前只是解决局部技术问题
- 当前只需要 coding family 的节点级工作

## 使用建议

1. 先从 `using-ahe-product-workflow` 判断当前节点。
2. 用上游 skill 产出洞察、机会、概念和验证计划。
3. 进入 `ahe-spec-bridge`，把结果压缩成可交给 `packs/coding/skills/` 消费的输入。
4. 再进入 coding family 走精确实现链路。

## 维护约定

1. 产品洞察 workflow 继续使用 `ahe-*` 命名族，但路径引用必须使用当前真实路径。
2. 每个 skill 入口统一放在 `packs/product-insights/skills/<skill-name>/SKILL.md`。
3. 共享协议与模板优先维护在 `docs/` 与 `templates/` 中，而不是分散写在每个 skill 里。
4. pack-specific 配套 agents 统一维护在 `packs/product-insights/agents/`。
