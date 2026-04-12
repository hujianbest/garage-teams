# D101: CLI Workspace Design

- Design ID: `D101`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 展开 `CLIEntry` 作为独立工作环境入口的产品与交互设计。
- 关联文档:
  - `docs/design/D10-agent-team-workspace-designs.md`
  - `docs/features/F102-independent-workspace-entries.md`
  - `docs/features/F113-session-api-and-shared-entry-binding.md`

## 1. 设计目标

- 让 CLI 成为独立可用的 `Garage Team` 入口
- 暴露 create / resume / attach / step progression 的最小交互面
- 不把 CLI 设计成私有 runtime 壳层
