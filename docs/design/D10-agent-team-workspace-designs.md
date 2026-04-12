# D10: Agent Team Workspace Designs

- Design ID: `D10`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 收口 `Garage Team` 工作环境的具体产品表面设计，说明 CLI / Web / HostBridge 三类入口怎样在产品层展开。
- 关联文档:
  - `docs/GARAGE.md`
  - `docs/architecture/10-entry-and-host-injection-layer.md`
  - `docs/features/F10-agent-teams-product-surface.md`
  - `docs/features/F11-runtime-topology-and-entry-bootstrap.md`

## 1. 这份文档回答什么

在产品层，`Garage Team` 工作环境怎样具体展开成可使用的入口设计。

## 2. 设计目标

- 让用户无论从 CLI 还是 Web 进入，都明确感知自己进入的是同一个 `Garage Team` 工作环境
- 让 `HostBridge` 成为能力注入层，而不是第二套产品真相
- 让所有入口在共享 runtime truth 的前提下保留各自的 UX 形式

## 3. 共同产品对象

所有入口都应围绕同一组产品对象组织，而不是围绕工具开关组织：

- `Garage Team`
- workspace
- session
- handoff
- review
- evidence
- long-term team assets such as memory and skill

## 4. 入口分工

### 4.1 `CLIEntry`

- 面向直接、连续、低摩擦的团队工作
- 强调 session progression、命令式推进和可恢复的工作流

### 4.2 `WebEntry`

- 面向可视化的团队工作环境
- 强调 session、workspace facts、review、observability 与多面板查看

### 4.3 `HostBridgeEntry`

- 面向能力注入
- 让已有工具借用 Garage 的 agents、skills、治理和长期能力
- 不成为新的系统真相源

## 5. 共同约束

- 三类入口都进入同一条 `Bootstrap -> SessionApi -> Session` 主链
- 三类入口共享同一组 workspace facts
- 三类入口共享同一组 governance / evidence / growth 语义
- 它们可以有不同 UX，但不能有不同 runtime truth

## 6. 非目标

- 不在这里定义具体实现代码结构
- 不把 Web 设计成 remote SaaS
- 不把 HostBridge 设计成主产品入口
- 不让 CLI 退化成内部调试壳

## 7. 下游 specs

- `D101`：CLI workspace design
- `D102`：Web workspace design
- `D103`：HostBridge integration design
