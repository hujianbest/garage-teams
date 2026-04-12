# A115: Product Surfaces And Host Capability Injection

- Architecture ID: `A115`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 在 `docs/VISION.md` 与 `docs/GARAGE.md` 已明确 `Garage` 首先是独立工作环境、宿主集成是能力注入层之后，继续冻结产品入口 surfaces 与 host capability injection 的边界。
- 当前阶段: 完整架构主线，实施将按切片推进
- 关联文档:
  - `docs/VISION.md`
  - `docs/GARAGE.md`
  - `docs/architecture/A105-garage-team-workspace-and-first-class-objects.md`
  - `docs/architecture/A110-garage-extensible-architecture.md`
  - `docs/architecture/A120-garage-core-subsystems-architecture.md`
  - `docs/features/F220-runtime-bootstrap-and-entrypoints.md`
  - `docs/features/F230-runtime-provider-and-tool-execution.md`

## 1. 文档目标与范围

这篇文档只回答一个问题：

**如果 `Garage` 首先是一个可直接进入的工作环境，同时又要把自己的能力注入到现有宿主里，那么 CLI / Web / HostBridge 这三类产品 surfaces 应该如何分工，哪些东西属于独立入口，哪些东西只属于能力注入层。**

本文覆盖：

- `CLIEntry`、`WebEntry`、`HostBridgeEntry` 的产品关系
- 独立工作环境与宿主能力注入层的边界
- 哪些语义可以因入口不同而变化，哪些绝不能变化
- 入口 surfaces 与统一 runtime 的关系

本文不覆盖：

- 具体 CLI 命令集或前端组件树
- 具体宿主 adapter 实现细节
- 具体 HTTP、SSE、WebSocket 等协议选择
- 具体任务拆解与交付顺序

## 2. 为什么这篇文档必须存在

在旧的 runtime-first 叙事里，产品入口常常会被写成：

- “都只是不同入口”
- “先有 runtime，再说产品”

但在新的产品定义下，这还不够。

我们还必须回答：

- `Garage` 是不是首先要作为独立产品成立
- 宿主集成是不是和独立入口同等地位
- 宿主是否可以反向拥有 `Garage` 的核心真相

如果这层不冻结，系统很容易重新漂回：

- 每个宿主各长一套私有 runtime
- CLI / Web 只是测试壳，真正产品又退回到宿主插件
- host provider hints 逐渐偷走 authority

## 3. 三类产品 surfaces

当前主线下，`Garage` 采用三类一等入口 family：

| surface | 产品角色 | 默认形态 | 不拥有什么 |
| --- | --- | --- | --- |
| `CLIEntry` | 独立工作环境入口 | 本地命令行 / shell | 私有 runtime 真相 |
| `WebEntry` | 独立工作环境入口 | local-first control plane + UI | 第二套 web-only runtime |
| `HostBridgeEntry` | 能力注入入口 | `Claude` / `OpenCode` / `Cursor` 等宿主桥 | 宿主私有 runtime 真相 |

这里最关键的判断是：

- `CLIEntry` 和 `WebEntry` 是独立工作环境
- `HostBridgeEntry` 是能力注入层
- 三者都可以是一等入口 family，但产品优先级不同

## 4. 独立工作环境与能力注入层的关系

`Garage` 的产品优先级应当固定为：

1. 先作为独立工作环境成立
2. 再把 agents、skills 和长期能力注入现有工具

这意味着：

- 宿主集成不是 `Garage` 的唯一存在方式
- 宿主能力注入不应反向定义 `Garage` 的产品本体
- `CLI` / `Web` 的存在不是为了 debug runtime，而是为了提供 Garage 自己的工作环境

## 5. 哪些东西可以不同，哪些绝不能不同

### 5.1 可以因入口不同而变化的东西

- UX
- presentation
- local interaction style
- host-specific hints
- capability visibility

### 5.2 绝不能因入口不同而变化的东西

- `Session` 语义
- `WorkspaceBinding`
- `RuntimeProfile` authority
- `Governance` verdict 语义
- `ExecutionLayer` 的中立事件语义
- workspace-first facts

换句话说：

- 产品表面可以不同
- runtime 真相不能分叉

## 6. Host capability injection 到底是什么

`HostBridgeEntry` 的本质不是“再做一个入口壳”，而是：

- 把 `Garage` 的 agents、skills、长期 memory 和工作方式接进用户已经在使用的宿主环境

它负责的是：

- 把宿主动作映射到共享 `SessionApi`
- 把宿主上下文压到 adapter 边缘
- 把宿主限制表达成 capability hint，而不是 authority

它不负责的是：

- 定义新的 runtime 真相
- 重写 `Garage Team` 的产品主对象
- 把 provider / model authority 提升到宿主层

## 7. 与统一 runtime 的关系

从架构上看，三类 surfaces 的统一规则应是：

- 都先进入统一 `Bootstrap`
- 都通过统一 `SessionApi` 进入会话边界
- 都共享同一套 `RuntimeProfile` authority、workspace facts、governance 与 execution 语义

也就是说：

`Product Surfaces -> Bootstrap -> SessionApi -> Garage Team Runtime`

而不是：

`CLI Runtime`

`Web Runtime`

`Host Runtime`

三套并行长大。

## 8. 边界上的 5 条红线

1. `CLIEntry` 和 `WebEntry` 不能退化成只是 runtime 调试壳，它们是 Garage 自己的独立工作环境。
2. `HostBridgeEntry` 不能反向成为 `Garage` 的产品主身份。
3. 宿主集成不能把 provider / model authority 提升到 host 层。
4. 任何 entry surface 都不能复制一套私有 session / execution 语义。
5. “为了宿主方便”不能成为破坏共享 runtime 真相的理由。

## 9. 这篇文档与其他文档的关系

这篇文档负责：

- 冻结产品入口 surfaces 与能力注入层的关系
- 解释独立工作环境优先、宿主注入层次之
- 说明不同入口可以差异化的范围与绝不能变化的共享真相

后续由不同文档继续展开：

- `A120`：继续定义 `Garage Team runtime` 的子系统图
- `A140`：继续在系统级叙事里把三类 surfaces 串进端到端主链
- `F220`：继续定义 bootstrap 与 entrypoints 的 feature-level 语义
- `F230`：继续定义 execution 与 provider / tool 的共享边界

## 10. 一句话总结

在新的产品主线下，`Garage` 的入口不是“几个平行的壳”，而是“两个独立工作环境 + 一个能力注入层”；它们都共享同一个 runtime，但只有 CLI 和 Web 负责承载 `Garage` 作为产品本体的独立存在。
