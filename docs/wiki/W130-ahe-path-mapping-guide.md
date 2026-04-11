# W130: AHE Path Mapping Guide

- Wiki ID: `W130`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 说明逻辑工件名如何映射到实际仓库路径，帮助不同目录结构下的 workflow family 仍能找到 spec、design、tasks、review 与 evidence。
- 关联文档:
  - `docs/README.md`
  - `docs/GARAGE.md`
  - `docs/tasks/README.md`

## Purpose

本文说明当外部仓库不采用 AHE 默认路径时，如何把逻辑工件稳定映射到实际路径。

它解决的问题不是“路径长什么样”，而是：

- runtime router 去哪里找 spec / design / tasks / reviews / verification / progress
- review / gate 完成后记录应该写回哪里
- finalize 去哪里消费 closeout 所需的 release / verification artifacts

## Core Rule

映射的是 **逻辑工件类型**，不是某个固定文件名。

所以你要回答的是：

- requirement spec 在这个仓库里由什么路径承载
- design doc 在这个仓库里由什么路径承载
- task plan 在这个仓库里由什么路径承载
- progress state 在这个仓库里由什么路径承载
- review / verification / release artifacts 在这个仓库里由什么路径承载

只要逻辑映射稳定，文件名和目录名都可以不同。

## Default Logical Surfaces

| 逻辑工件 | AHE 默认路径 | 用途 |
|---|---|---|
| requirement spec | `docs/specs/YYYY-MM-DD-<topic>-srs.md` | 说明做什么 |
| design doc | `docs/design/YYYY-MM-DD-<topic>-design.md` | 说明怎么做 |
| task plan | `docs/tasks/YYYY-MM-DD-<topic>-tasks.md` | 说明执行顺序与验证 |
| progress state | `task-progress.md` | 跨会话状态面 |
| review records | `docs/reviews/` | 各 review / analysis 记录 |
| verification records | `docs/verification/` | regression / completion 等记录 |
| release notes | `RELEASE_NOTES.md` | 用户可见变更摘要 |

## Mapping Rules

### 1. One logical surface, one authoritative mapping

同一逻辑工件类型应尽量只有一个权威入口。

例如：

- 不要同时让 `ahe-workflow-router` 猜 `docs/specs/` 和 `product/specs/`
- 不要让 completion gate 同时依赖两个不同目录里的 verification 记录

### 2. Prefer repo-local writable paths

优先映射到：

- 仓库内
- 可被 agent 读取
- 可被节点写回

若真实 source of truth 在外部系统（Jira、Notion、Confluence），建议至少导出或镜像到仓库路径，避免 workflow 在关键 gate 上失去可验证性。

### 3. Preserve logical separation

不要把不同逻辑工件长期混在同一个“万能文档”里。

例如：

- 设计与任务计划可以互相引用，但不要长期共用一个权威文件
- review 记录与 verification 记录不要混写成同一种 artifact
- progress state 不要只隐藏在 release notes 里

### 4. Keep mappings stable across sessions

一旦某个外部仓库确定了映射，就不要在不同会话中反复切换。

## Recommended Mapping Template For `AGENTS.md`

建议在外部仓库 `AGENTS.md` 中至少放入一个类似区块：

```md
## ahe-workflow

- requirement spec: docs/product/specs/
- design doc: docs/design/
- task plan: docs/execution/tasks/
- progress state: docs/status/task-progress.md
- review records: docs/reviews/
- verification records: docs/verification/
- release notes: docs/releases/RELEASE_NOTES.md
```

若项目需要更细粒度映射，可继续拆：

```md
## ahe-workflow

- spec review records: docs/reviews/spec/
- design review records: docs/reviews/design/
- task review records: docs/reviews/tasks/
- test/code/traceability reviews: docs/reviews/quality/
- regression records: docs/verification/regression/
- completion records: docs/verification/completion/
```

## Surface-Specific Guidance

### Requirement Spec

映射要求：

- 能承载范围、非目标、验收标准、关键约束
- 能被 `ahe-spec-review` 直接读取
- 能承载批准状态或可被 review record 佐证

常见可接受映射：

- `docs/specs/`
- `product/requirements/`
- `changes/<change>/spec.md`

### Design Doc

映射要求：

- 能承载方案、边界、接口、非功能决策、测试策略
- 能被 `ahe-design-review` 与 `ahe-tasks` 直接读取

常见可接受映射：

- `docs/design/`
- `docs/architecture/`
- `changes/<change>/design.md`

### Task Plan

映射要求：

- 能承载任务顺序、验证方式、依赖关系、活跃任务选择规则
- 能被 `ahe-tasks-review` 与 `ahe-test-driven-dev` 直接消费

常见可接受映射：

- `docs/tasks/`
- `execution/tasks/`
- `changes/<change>/tasks.md`

### Review Records

建议至少能区分：

- upstream reviews: spec / design / tasks
- quality reviews: test / code / traceability
- quality analysis: bug patterns

其中 `ahe-tasks-review` 记录即使在 `lightweight` profile 里也仍然需要稳定映射；可按 profile 省略的是部分质量 review，不是任务评审本身。

路径不必强制分目录，但至少要能从命名或子路径上区分类型。

推荐例子：

- `docs/reviews/spec/`
- `docs/reviews/design/`
- `docs/reviews/tasks/`
- `docs/reviews/quality/`

### Verification Records

建议至少能区分：

- regression gate records
- completion gate records

推荐例子：

- `docs/verification/regression/`
- `docs/verification/completion/`

### Progress State

progress state 是最容易被忽略，但最不该缺的映射。

最低要求：

- 能稳定写入 canonical progress schema
- 能在下一会话中被 `ahe-workflow-router` 重新读取
- 不与 release notes / review 记录混成同一种 artifact

常见可接受映射：

- `task-progress.md`
- `docs/status/task-progress.md`
- `workstreams/<name>/task-progress.md`

### Release Notes

若项目存在用户可见变更，release notes 应有清晰映射。

常见可接受映射：

- `RELEASE_NOTES.md`
- `docs/releases/RELEASE_NOTES.md`
- `docs/releases/<date>-<topic>.md`

## Monorepo Advice

对 monorepo，不建议强迫所有 package 共用一个 spec / design / task 目录。

更稳妥的做法是：

- 在 `AGENTS.md` 中声明当前作用域对应的映射
- 或为每个受支持子域声明 scoped mapping

例如：

```md
## ahe-workflow

- app:web requirement spec: apps/web/docs/specs/
- app:web design doc: apps/web/docs/design/
- app:web task plan: apps/web/docs/tasks/
- app:web progress state: apps/web/task-progress.md
```

关键不是目录结构，而是让当前会话能知道“这次工作属于哪个 scope”。

## Anti-Patterns

- 让 `ahe-workflow-router` 通过 `find` 式猜测去找工件
- 把 review / verification 记录散落在大量无命名规律的文件里
- 同一个 logical surface 在不同会话中切换不同路径
- 依赖外部系统，但仓库里没有任何可回读镜像
- 用 release notes 代替 progress state

## Minimal Mapping Checklist

- [ ] requirement spec 已有稳定映射
- [ ] design doc 已有稳定映射
- [ ] task plan 已有稳定映射
- [ ] progress state 已有稳定映射
- [ ] review records 已有稳定映射
- [ ] verification records 已有稳定映射
- [ ] release notes（如适用）已有稳定映射
- [ ] `AGENTS.md` 已声明这些映射或默认路径已被接受

## Related Docs

- `docs/wiki/W120-ahe-workflow-externalization-guide.md`
- `packs/coding/skills/docs/ahe-workflow-shared-conventions.md`
