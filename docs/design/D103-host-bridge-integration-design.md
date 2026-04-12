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
