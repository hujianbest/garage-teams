# T00: Garage Implementation Tracks

- Task ID: `T00`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: `docs/tasks/` 负责把新的产品定义、architecture 主线、feature families 和 design 主线拆成 implementation tracks。它回答“先做什么、后做什么、怎样交付”，但不反向拥有系统真相。
- 关联文档:
  - `docs/VISION.md`
  - `docs/GARAGE.md`
  - `docs/README.md`
  - `docs/ROADMAP.md`

## 1. 这组文档回答什么

`docs/tasks/` 负责回答：

- 应该先做什么，后做什么
- 哪些任务可以并行，哪些必须串行
- 每个 delivery slice 要交付什么
- 当前开发任务如何跟新的 architecture / features / design 主线对齐

## 2. 任务树规则

- task docs 跟随 `architecture / features / design`
- 当设计真相和任务切片冲突时，以设计真相为准
- tasks 解释交付顺序，不解释系统本体

## 3. 编号规则

新的 `docs/tasks/` 保留 `T` 前缀，并采用两层结构：

- `T10-T19`：顶层 task families
- `T101-T199`：对应 family 下的具体 delivery specs

## 4. 当前 Task Families

| Family | 作用 | 主要输入 |
| --- | --- | --- |
| `T10` | Entry surfaces implementation | `F10`、`F11`、`D10` |
| `T11` | Runtime core and topology implementation | `F11`、`F12` |
| `T12` | Governance and workspace truth implementation | `F13`、`D12` |
| `T13` | Continuity and growth implementation | `F14`、`D12` |
| `T14` | Pack platform and collaboration implementation | `F15`、`D11` |
| `T15` | Product hardening and delivery implementation | `F16`、`D10`、`D12` |

## 5. 阅读顺序

建议这样读：

1. `docs/VISION.md`
2. `docs/GARAGE.md`
3. `docs/architecture/`
4. `docs/features/`
5. `docs/design/`
6. `docs/tasks/README.md`

## 6. 一句话总结

新的 `docs/tasks/` 不再继承旧 `T010-T230` 任务树，而是按新的 architecture / features / design 主线重切成两层 implementation tracks。
