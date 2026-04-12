# D103: Host Bridge Integration Design

- Design ID: `D103`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 展开 `HostBridgeEntry` 作为 capability injection 层的集成设计。
- 关联文档:
  - `docs/design/D10-agent-team-workspace-designs.md`
  - `docs/features/F103-host-bridge-capability-injection.md`
  - `docs/features/F161-provider-authority-placement.md`

## 1. 设计目标

- 让现有工具可以注入 Garage 能力
- 保证 host 只扩展工作方式，不抢系统真相
- 维持 shared runtime、shared authority、shared governance

## 2. 设计问题

这份文档要解决的是：

- 已有工具如何接入 `Garage Team`
- 宿主层到底能注入什么
- 什么必须留在共享 runtime 真相内

## 3. 宿主可注入的内容

- 局部上下文
- 本地 UX affordances
- capability hints
- 与宿主工作流相关的触发入口

## 4. 宿主不能拥有的内容

- provider / model authority
- pack truth
- session lifecycle truth
- growth / continuity truth
- workspace-first fact ownership

## 5. 典型注入模式

这份设计默认承接三类宿主：

- `Claude`
- `OpenCode`
- `Cursor`

它们都应通过 shared host bridge seam 工作，而不是各自复制一套 runtime。

## 6. 失败与回退

宿主设计必须显式考虑：

- host hint 与 authority 冲突
- host 请求越过允许边界
- host 本地上下文无法映射到共享 runtime

这些都应回到共享错误语义，而不是在宿主内私自吞掉。

## 7. 非目标

- 不在本设计中定义某一宿主的全部 UX 细节
- 不把 HostBridge 设计成新的主产品入口
- 不让宿主注入演化成宿主真相

## 8. 设计完成标准

- HostBridge 作为 capability injection 的边界清楚
- `Claude/OpenCode/Cursor` 级别的接入模式清楚
- 下游 task 不需要再猜“宿主能做什么、不能做什么”
