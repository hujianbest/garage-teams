# Garage Implementation Root

- 状态: phase 1 scaffold
- 日期: 2026-04-11
- 定位: `garage/` 是 `Garage` 在 phase 1 的实现根目录，承接 core、shared contracts、reference packs 和 host adapter stubs 的代码骨架，不承接设计长文，也不直接等同现有 `ahe-*` 资产。
- 关联文档:
  - `docs/garage/README.md`
  - `docs/tasks/README.md`
  - `docs/tasks/garage-phase1-01-foundation-and-repository-layout.md`

## 1. 目录职责

| 路径 | 作用 |
| --- | --- |
| `garage/core/` | `Garage Core` 的稳定实现面，后续承接 `session`、`registry`、`governance`、artifact routing 与 evidence coordination |
| `garage/contracts/` | phase 1 共享 contracts、schema 校验、加载与 registry 对接 |
| `garage/packs/` | reference packs 的实现根目录，pack-specific 角色、节点、artifact 与 evidence 留在各自 pack 下 |
| `garage/hosts/` | host adapter stubs 与宿主侧接入壳；phase 1 只预留 seam，不展开完整 host 实现 |

## 2. workspace 级 file-backed surfaces

下面这些目录是 phase 1 的 workspace 级主事实面，因此保留在仓库根目录，而不是塞进 `garage/` 内：

- `artifacts/`
- `evidence/`
- `sessions/`
- `archives/`
- `.garage/`

这样可以让 `Garage` 的实现根目录与文件化运行面明确分离：

- `garage/` 放实现骨架
- 根目录 surfaces 放当前工件、证据、会话与归档

## 3. 与现有 AHE 资产的关系

phase 1 中，下面这些目录仍然是重要来源资产：

- `ahe-coding-skills/`
- `ahe-product-skills/`

但它们当前不等同于 `Garage` runtime 本体。

它们在现阶段的角色是：

- 提供现有 workflow 资产、模板与约定
- 作为 `garage/packs/coding/` 与 `garage/packs/product-insights/` 的转译来源
- 作为 phase 1 pack 设计是否成立的参考面对照

phase 1 不在这个阶段做大规模重命名或整体搬迁。

## 4. phase 1 非目标

当前骨架阶段不做这些事：

- 不实现 `writing`、`video` 等新 packs
- 不实现 database-first 控制面
- 不实现完整多 host profile
- 不把现有 AHE 资产直接改造成 `Garage` runtime

## 5. 使用方式

如果你是第一次进入 `Garage` 的实现骨架，建议顺序是：

1. 先读 `docs/garage/README.md`
2. 再读 `docs/tasks/README.md`
3. 再从这里进入 `garage/core/`、`garage/contracts/`、`garage/packs/` 或 `garage/hosts/`
