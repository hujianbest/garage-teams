# D102: Web Workspace Design

- Design ID: `D102`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 展开 `WebEntry` 作为 local-first 工作环境入口的产品与交互设计。
- 关联文档:
  - `docs/design/D10-agent-team-workspace-designs.md`
  - `docs/features/F102-independent-workspace-entries.md`
  - `docs/features/F103-host-bridge-capability-injection.md`
  - `docs/features/F131-workspace-first-facts.md`

## 1. 设计目标

- 让 Web 成为独立工作环境入口
- 暴露 session、workspace facts、review 与 observability 的最小界面
- 不把 Web 设计成第二套 runtime

## 2. 用户进入时看到什么

Web 入口首先应该把 `Garage Team` 工作环境可视化，而不是只把 CLI 文本换成网页。

用户最少应能看到：

- 当前 team / workspace / session
- 当前工作主线和关键状态
- 主要 workspace facts
- review / approval / observability 的最小入口

## 3. 最小页面能力

最小 Web 工作环境至少应包含：

- session create / resume / attach 入口
- workspace facts 浏览面
- session progress 查看面
- evidence / trace / review / approval 的最小查看面

## 4. Web 页面结构与数据绑定

| 页面/面板 | 主要数据源 | 操作 | 返回 |
| --- | --- | --- | --- |
| Session Launcher | `CreateSession` / `ResumeSession` | 创建、恢复、附着 | `session_id`, `session_snapshot` |
| Workspace Facts Panel | `AttachWorkspace` + facts projection | 浏览 facts、切换 scope | `facts_projection`, `last_synced_at` |
| Session Progress Panel | `GetSessionStatus` | 查看状态、待处理 gate | `status`, `pending_gates`, `next_actions` |
| Evidence/Trace Panel | `SubmitStep` 结果聚合 | 查看证据链和 trace | `trace_ref`, `evidence_ref` |

## 5. 与共享 runtime 的关系

- Web 通过共享 `SessionApi` 进入工作主线
- Web 复用共享 execution / evidence / governance 语义
- Web 不拥有自己的 session truth、provider truth 或 growth truth

## 6. 状态同步与恢复

Web 设计应明确：

- 刷新页面后如何回到当前 session
- 多个 panel 看到的状态如何共享同一 truth
- local-first 场景下如何恢复最小工作上下文

状态恢复规则：

- 首屏加载先读本地 `last_session_hint`，再调用 `ResumeSession` 校验。
- 多 panel 使用同一 `session_id` 作为单一状态锚点，不允许各自缓存真相。
- `facts_unavailable` 时保留最后成功快照并显示 stale 标记，不伪造最新状态。

## 7. 失败语义与回退

- `session_missing`: 引导进入创建/附着流程。
- `governance_gate_failed`: 在 Session Progress 中展示 gate 名称与建议动作。
- `runtime_rejected`: 保留用户输入草稿，允许修正后重提。
- `facts_unavailable`: 显示降级告警，允许手动重试同步。

## 8. 测试策略与验收锚点

- 跨 panel 一致性测试: 同一时刻多个 panel 的 `session_status` 一致。
- 刷新恢复测试: 刷新后可恢复到同一 session 并保持 pending gates。
- 错误回退测试: `runtime_rejected` 与 `facts_unavailable` 下页面可恢复。
- 可观测性测试: step 结果可在 Evidence/Trace panel 检索。

验收锚点：

- `WEB-A1`: Web 是独立入口，不依赖 CLI 前置流程。
- `WEB-A2`: 状态恢复不产生第二套 session truth。
- `WEB-A3`: governance/evidence/trace 在 Web 可读且可追溯。

## 9. 非目标

- 不在本设计中定义完整设计系统
- 不在本设计中把 Web 升级成 remote SaaS
- 不在本设计中引入第二套 web-only orchestration

## 10. 设计完成标准

- Web 作为独立工作环境入口的最小产品面清楚
- Web 和 CLI 的共享 truth 与差异层被明确区分
- 下游 task 不需要再猜 Web 的 MVP 范围
