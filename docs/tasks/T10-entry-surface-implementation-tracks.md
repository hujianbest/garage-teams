# T10: Entry Surface Implementation Tracks

- Task ID: `T10`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 拆解 `Garage` 作为独立工作环境与能力注入层时，三类入口的实现任务。
- 关联设计文档:
  - `docs/features/F10-agent-teams-product-surface.md`
  - `docs/features/F11-runtime-topology-and-entry-bootstrap.md`
  - `docs/design/D10-agent-team-workspace-designs.md`

## 1. 这份文档回答什么

CLI / Web / HostBridge 应该按什么顺序、以什么切片被实现。

## 2. 推荐顺序

1. `T101` CLI
2. `T103` HostBridge
3. `T102` Web

原因：

- CLI 最薄，最适合先验证 shared entry chain
- HostBridge 在 CLI 之后更容易收敛成 capability injection，而不是各宿主各长 runtime
- Web 最后做，可以建立在 shared truth 已经稳定的前提上

## 3. family 交付目标

- 三类入口都共享同一条 `Bootstrap -> SessionApi -> Session` 主链
- CLI / Web 是独立工作环境入口
- HostBridge 是能力注入层
- 三者都不复制私有 runtime truth

## 4. 并行与依赖

- `T101` 是本 family 的基线
- `T103` 依赖 `T101`
- `T102` 最好在 `T101` 和 `T103` 的共享入口语义稳定后推进

## 5. 验收

- 用户可以从三类入口进入同一 `Garage Team`
- 三类入口对 session/workspace/profile 的解释一致
- 宿主注入不越权，Web 不复制第二套 runtime

## 6. 非目标

- 不一次性完成所有入口 UX 打磨
- 不提前做 remote SaaS 控制面
- 不把任何单一入口升格成系统真相 owner

## 7. 下游 specs

- `T101`：CLI entry implementation
- `T102`：Web entry implementation
- `T103`：HostBridge implementation
