# docs

`docs/` 只保留分组目录与索引页，长文默认按主题归档，不再继续堆放在根目录。

## 分类说明

| 目录 | 说明 |
| --- | --- |
| `analysis/` | 外部 harness / workflow 仓库的源码分析与对比 |
| `architecture/` | AHE 的系统级运行模型与架构设计 |
| `designs/` | AHE skill / workflow 的目标态设计说明 |
| `garage/` | `Garage` 的品牌定位、项目愿景与可扩展分层架构文档 |
| `tasks/` | `Garage` phase 1 的开发任务拆解与执行顺序文档 |
| `guides/` | AHE 对外接入、映射与使用指南 |
| `mind/` | 主题化总结、设计心法与高层认知提炼 |
| `plans/` | 尚在推进中的优化方案、路线图与规划稿 |
| `references/` | 参考资产索引与研究辅助文档 |

## 当前内容

### `analysis/`

- `analysis/clowder-ai-harness-engineering-analysis.md`
- `analysis/everything-claude-code-main-harness-engineering-analysis.md`
- `analysis/get-shit-done-main-harness-engineering-analysis.md`
- `analysis/gstack-main-harness-engineering-analysis.md`
- `analysis/hermes-agent-harness-engineering-analysis.md`
- `analysis/longtaskforagent-main-harness-engineering-analysis.md`
- `analysis/OpenSpec-main-harness-engineering-analysis.md`
- `analysis/superpowers-main-harness-engineering-analysis.md`

### `architecture/`

- `architecture/ahe-platform-first-multi-agent-architecture.md`
- `architecture/ahe-workflow-skill-anatomy.md`

### `designs/`

- 当前暂无收录文档

### `garage/`

- 建议先从 `garage/README.md` 开始，再按其中的阅读顺序继续。
- `garage/README.md`
- `garage/garage-extensible-architecture.md`
- `garage/garage-core-subsystems-architecture.md`
- `garage/garage-phase1-core-runtime-records.md`
- `garage/garage-phase1-session-lifecycle-and-handoffs.md`
- `garage/garage-phase1-governance-model.md`
- `garage/garage-phase1-artifact-and-evidence-surface.md`
- `garage/garage-shared-contracts.md`
- `garage/garage-phase1-shared-contract-schemas.md`
- `garage/garage-continuity-memory-skill-architecture.md`
- `garage/garage-phase1-continuity-mapping-and-promotion.md`
- `garage/garage-phase1-reference-packs.md`
- `garage/garage-product-insights-pack-design.md`
- `garage/garage-coding-pack-design.md`
- `garage/garage-phase1-cross-pack-bridge.md`

### `tasks/`

- 建议先从 `tasks/README.md` 开始，再按其中的开发顺序继续。
- `tasks/README.md`
- `tasks/garage-phase1-01-foundation-and-repository-layout.md`
- `tasks/garage-phase1-02-core-runtime-records.md`
- `tasks/garage-phase1-03-shared-contracts-and-registry.md`
- `tasks/garage-phase1-04-session-lifecycle-and-governance.md`
- `tasks/garage-phase1-05-artifact-routing-and-evidence-surface.md`
- `tasks/garage-phase1-06-continuity-and-promotion.md`
- `tasks/garage-phase1-07-reference-pack-shells.md`
- `tasks/garage-phase1-08-product-insights-pack.md`
- `tasks/garage-phase1-09-coding-pack.md`
- `tasks/garage-phase1-10-cross-pack-bridge-and-phase1-walkthrough.md`

### `guides/`

- `guides/ahe-path-mapping-guide.md`
- `guides/ahe-workflow-externalization-guide.md`

### `mind/`

- `mind/clowder-ai-core-design-ideas.md`
- `mind/hermes-agent-core-design-ideas.md`

### `plans/`

- `plans/ahe-agent-platform-roadmap-and-adr-backlog.md`
- `plans/ahe-review-subagent-optimization-plan.md`

### `references/`

- `references/skills_refer.md`

## 维护约定

- 新文档先选分类目录，再命名文件；避免重新把长文直接放回 `docs/` 根目录。
- 若文档同时涉及多个主题，以“主要用途”决定目录，其他关系通过 `README.md` 或文内 `Related Docs` 互链。
- 只有当现有分类已经明显不足以承载新增文档时，才新增新的一级目录。
