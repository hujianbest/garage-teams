# Garage Hosts

- 状态: phase 1 scaffold
- 日期: 2026-04-11
- 定位: `garage/hosts/` 是 host adapter stubs 的预留目录，后续承接 `CLI`、`IDE`、chat 等宿主的接入壳，但 phase 1 的 `01` 只先冻结目录边界，不展开具体宿主实现。

## 边界

这里放：

- host adapter stubs
- host capability shims
- 宿主差异的轻量接入层

这里不放：

- 平台中立 core 逻辑
- pack-specific 角色与节点逻辑
- 设计文档与分析资料

## phase 1 说明

当前只预留宿主 seam，不在 `01` 中提前决定第一个完整 host profile 的实现方案。
