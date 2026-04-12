# T101: CLI Entry Implementation

- Task ID: `T101`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 落 `CLIEntry` 作为独立工作环境入口的实现切片。
- 关联设计文档:
  - `docs/features/F102-independent-workspace-entries.md`
  - `docs/design/D101-cli-workspace-design.md`

## 1. 交付目标

- 稳定 CLI 入口
- create / resume / attach / submitStep 最小主链
- 不复制私有 runtime

## 2. 最小交付物

- 可用的 CLI 入口命令面
- 明确的 session / workspace / profile summary
- 统一失败语义

## 3. 依赖

- `F102`
- `F113`
- `D101`

## 4. 验收

- CLI 可 create / resume / attach
- CLI 不需要私有 runtime 语义
- CLI 的错误与状态反馈可由下游实现直接对应
