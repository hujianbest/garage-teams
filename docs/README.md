# docs

`docs/` 只保留分组目录与索引页，长文默认按主题归档，不再继续堆放在根目录。

## 分类说明

| 目录 | 说明 |
| --- | --- |
| `analysis/` | 外部 harness / workflow 仓库的源码分析与对比 |
| `architecture/` | AHE 的系统级运行模型与架构设计 |
| `designs/` | AHE skill / workflow 的目标态设计说明 |
| `guides/` | AHE 对外接入、映射与使用指南 |
| `plans/` | 尚在推进中的优化方案、路线图与规划稿 |
| `references/` | 参考资产索引与研究辅助文档 |

## 当前内容

### `analysis/`

- `analysis/everything-claude-code-main-harness-engineering-analysis.md`
- `analysis/get-shit-done-main-harness-engineering-analysis.md`
- `analysis/gstack-main-harness-engineering-analysis.md`
- `analysis/longtaskforagent-main-harness-engineering-analysis.md`
- `analysis/OpenSpec-main-harness-engineering-analysis.md`
- `analysis/superpowers-main-harness-engineering-analysis.md`

### `architecture/`

- `architecture/ahe-platform-first-multi-agent-architecture.md`
- `architecture/ahe-workflow-skill-anatomy.md`

### `designs/`

- 当前暂无收录文档

### `guides/`

- `guides/ahe-path-mapping-guide.md`
- `guides/ahe-workflow-externalization-guide.md`

### `plans/`

- `plans/ahe-agent-platform-roadmap-and-adr-backlog.md`
- `plans/ahe-review-subagent-optimization-plan.md`

### `references/`

- `references/skills_refer.md`

## 维护约定

- 新文档先选分类目录，再命名文件；避免重新把长文直接放回 `docs/` 根目录。
- 若文档同时涉及多个主题，以“主要用途”决定目录，其他关系通过 `README.md` 或文内 `Related Docs` 互链。
- 只有当现有分类已经明显不足以承载新增文档时，才新增新的一级目录。
