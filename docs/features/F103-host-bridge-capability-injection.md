# F103: Host Bridge Capability Injection

- Feature ID: `F103`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 定义 `HostBridgeEntry` 作为能力注入层的稳定产品语义。

## 1. 这份文档回答什么

已有工具如何接入 Garage，而不抢走 Garage 的系统真相。

## 2. 稳定语义

- HostBridge 是 capability injection，不是 product authority
- host 可以提供 hint 与 local context
- host 不能成为 provider truth、pack truth 或 growth truth 的拥有者
