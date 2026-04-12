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

## 2. 用户进入时看到什么

CLI 入口首先应该让用户明确：

- 当前自己进入的是哪个 `Garage Team`
- 当前绑定的是哪个 workspace / profile / session
- 当前操作会沿着哪条 session 主链推进

## 3. 最小交互面

最小 CLI 应至少承接：

- create
- resume
- attach
- submit step
- interrupt
- status / summary

这些动作都必须通过共享 `SessionApi` 发起，而不是自己直连 runtime internals。

## 4. 状态反馈

CLI 至少应稳定展示：

- session identity
- workspace identity
- host binding summary
- session status
- 关键失败信息，例如 workspace/profile/session/entry gate 失败

## 5. 错误模型

CLI 不应自己发明错误真相，而应消费共享 entry/runtime 失败：

- workspace binding errors
- profile authority errors
- missing session
- governance gate failures
- unsupported host/entry binding

## 6. 非目标

- 不在本设计中定义完整命令大全
- 不在本设计中引入 TUI-first 重型交互
- 不让 CLI 成为 provider authority owner

## 7. 设计完成标准

- CLI 被清楚定义为独立工作环境入口
- CLI 的最小交互面与错误面足以驱动实现任务分解
- 下游 task 不需要再猜 CLI 和 SessionApi 的关系
