# Garage Runtime Home And Workspace Topology

- 状态: 草稿
- 日期: 2026-04-11
- 定位: 定义 `Garage` 作为独立可运行程序时的 `source root / runtime home / workspace` 拓扑，明确当前仓库中的 repo-local surfaces 与未来可安装运行形态之间的关系。
- 当前阶段: phase 1
- 关联文档:
  - `docs/garage/README.md`
  - `docs/garage/garage-runtime-bootstrap-and-entrypoints.md`
  - `docs/garage/garage-phase1-artifact-and-evidence-surface.md`
  - `docs/garage/garage-continuity-memory-skill-architecture.md`
  - `garage/README.md`

## 1. 文档目标与范围

这篇文档只回答一个问题：

**如果 `Garage` 后续要成为独立可运行程序，而不是永远绑定在当前仓库根目录里，那么它的 `source root`、`runtime home` 和 `workspace` 拓扑应该如何先冻结。**

本文覆盖：

- 运行时拓扑中的三个稳定层次
- 当前 repo-local surfaces 应如何被解释
- 独立安装运行时与当前仓库 dogfooding 形态之间的关系

本文不覆盖：

- 具体安装脚本
- 具体系统路径
- 具体 secrets 管理方式
- 多设备同步细节

## 2. 为什么需要这份文档

当前 phase 1 文档明确规定了：

- `artifacts/`
- `evidence/`
- `sessions/`
- `archives/`
- `.garage/`

这 5 个 surface 以当前仓库根目录为主事实面。

这个判断对 phase 1 很重要，但如果目标是独立程序，还必须进一步回答：

- 程序本体放哪里
- 运行时 home 放哪里
- workspace 放哪里
- 当前仓库根目录到底是“程序目录”还是“工作区目录”

如果这层不说清楚，后续会出现两类混乱：

- 把 repo root 当成未来唯一运行形态
- 把 runtime home、workspace state、source code 混成同一层

## 3. 建议冻结的三层拓扑

`Garage` 作为独立程序时，建议至少区分 3 个稳定层次：

| 层次 | 作用 | 典型内容 |
| --- | --- | --- |
| `Garage Source Root` | 程序源码与设计资产所在位置 | `docs/`、`garage/`、来源资产目录 |
| `Garage Runtime Home` | 用户级 runtime home 与 profile 所在位置 | profiles、runtime config、cache、adapter metadata |
| `Garage Workspace` | 某个创作或开发 workspace 的主事实面 | `artifacts/`、`evidence/`、`sessions/`、`archives/`、`.garage/` |

关键判断是：

- source root 不等于 runtime home
- runtime home 不等于 workspace
- workspace 才是 phase 1 file-backed surface 的主要承载面

## 4. `Garage Source Root`

`Garage Source Root` 回答的是：

- 程序代码在哪里
- 设计文档在哪里
- 参考资产在哪里

在当前仓库里，它主要包括：

- `docs/`
- `garage/`
- `ahe-coding-skills/`
- `ahe-product-skills/`
- `ahe-refer-skills/`

这一层的职责是：

- 承载源码
- 承载设计
- 承载来源资产

它不应默认承担所有运行时状态。

## 5. `Garage Runtime Home`

`Garage Runtime Home` 回答的是：

- 当前用户或当前安装实例的 runtime 设置放在哪里
- 不同 profile、adapter 元数据、局部 cache 如何被管理

这一层建议承接：

- runtime profiles
- provider / adapter 配置引用
- 运行时缓存与局部索引
- 与安装实例绑定的元数据

它不应默认承接：

- 某个具体 workspace 的主工件
- 某个 workspace 的主要 evidence
- 某个 workspace 的显式会话主线

## 6. `Garage Workspace`

`Garage Workspace` 回答的是：

- 当前正在推进哪个创作或开发上下文
- 当前 artifacts、evidence、sessions 与 archives 落在哪里

phase 1 建议继续坚持：

- `artifacts/`
- `evidence/`
- `sessions/`
- `archives/`
- `.garage/`

属于 workspace 级 surfaces，而不是 runtime home 级 surfaces。

这意味着：

- `Garage` 可以作为独立程序运行
- 但它推进的主事实面仍然优先留在 workspace 本地

## 7. 当前仓库在 phase 1 中如何解释

当前仓库不应被理解为未来唯一部署形态，而应被理解为：

- `Garage` 的 source root
- 同时也是当前默认 dogfooding workspace

也就是说，当前仓库处于一种：

- source-coupled workspace mode

在这个模式下：

- `garage/` 承接程序实现骨架
- 仓库根目录同时承接当前 workspace surfaces
- 设计链和任务链也都暂时放在同一仓库里

这是一种对 phase 1 友好的开发与 dogfooding 形态，但不是未来唯一运行形态。

## 8. 独立安装运行时的目标形态

当 `Garage` 走向独立程序时，更理想的形态应是：

- 程序代码可以独立安装或打包
- `Garage Runtime Home` 可以独立于具体 workspace 存在
- 用户可以把 `Garage` 绑定到任意 workspace root
- 每个 workspace 继续拥有自己的 file-backed surfaces

这意味着未来可以同时支持：

1. 当前 repo 内 dogfooding mode
2. 独立安装程序 + 外部 workspace mode

## 9. 拓扑绑定规则

建议 phase 1 先冻结下面这些绑定规则：

- 一个 `Session` 只能属于一个 workspace。
- 一个 workspace 可以被多个 session 先后使用，但不能把多个 workspace 混成一个 session。
- `Garage Runtime Home` 可以跨 workspace 存在，但不能吞并 workspace surfaces。
- root-level surfaces 的当前语义仍以 workspace 为中心，而不是以安装实例为中心。

## 10. 与 continuity 的关系

独立程序化之后，最容易混乱的是 continuity 资产的归属。

因此这里先冻结一个保守判断：

- `artifact / evidence / session` 默认仍是 workspace-first
- `memory / skill` 的全局化或跨 workspace 共享，必须显式设计，不能因为有了 runtime home 就自动漂移过去

也就是说：

- runtime home 的出现，不等于所有连续性资产都变成全局资产

## 11. 与 bootstrap 的关系

runtime bootstrap 建议按下面顺序解析拓扑：

1. 先解析 `RuntimeProfile`
2. 再解析 `Garage Runtime Home`
3. 再绑定目标 `Garage Workspace`
4. 最后挂载 workspace surfaces 并恢复 session

这条顺序的意义是：

- 先知道程序以谁的身份和配置启动
- 再知道它当前服务哪个 workspace

## 12. phase 1 收敛范围

phase 1 只需要先冻结这些判断：

- 当前仓库是 source root
- 当前仓库也可以作为默认 dogfooding workspace
- workspace surfaces 仍然是主事实面
- runtime home 必须在概念上与 workspace 分层

phase 1 不要求：

- 立刻把源码仓与运行 workspace 彻底拆开
- 设计完整 installer
- 设计跨设备同步
- 设计多 workspace 并发守护进程

## 13. phase 1 非目标

- 不把 repo-local dogfooding 形态误写成未来唯一部署方式
- 不把 runtime home 直接做成 database-first 控制面
- 不让 workspace surfaces 悄悄迁进安装目录
- 不让 `memory / skill` 因为“方便”而失去明确边界

## 14. 遵循的设计原则

- Source root / runtime home / workspace 分层：程序源码、运行时 home、工作区主事实面必须拆开。
- Workspace-first facts：`artifacts / evidence / sessions / archives / .garage` 默认仍属于 workspace。
- Dogfooding mode is valid, not final：当前仓库中的 source-coupled 形态是有效开发模式，但不是未来唯一部署形态。
- Runtime home does not swallow workspace：runtime home 负责安装实例与 profile，不吞并主工件与主证据面。
- Explicit continuity scope：`memory / skill` 是否跨 workspace 必须显式设计，不能隐式漂移。
- phase 1 克制：先把拓扑边界讲稳，再决定 installer、daemon、多 workspace runtime 等更重形态。
