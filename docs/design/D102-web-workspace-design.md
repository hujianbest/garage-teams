# D102: Web Workspace Design

- Design ID: `D102`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 展开 `WebEntry` 作为 local-first 工作环境入口的产品与交互设计。
- 关联文档:
  - `docs/design/D10-agent-team-workspace-designs.md`
  - `docs/features/F102-independent-workspace-entries.md`
  - `docs/features/F103-host-bridge-capability-injection.md`

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

## 4. 与共享 runtime 的关系

- Web 通过共享 `SessionApi` 进入工作主线
- Web 复用共享 execution / evidence / governance 语义
- Web 不拥有自己的 session truth、provider truth 或 growth truth

## 5. 状态与恢复

Web 设计应明确：

- 刷新页面后如何回到当前 session
- 多个 panel 看到的状态如何共享同一 truth
- local-first 场景下如何恢复最小工作上下文

## 6. 非目标

- 不在本设计中定义完整设计系统
- 不在本设计中把 Web 升级成 remote SaaS
- 不在本设计中引入第二套 web-only orchestration

## 7. 设计完成标准

- Web 作为独立工作环境入口的最小产品面清楚
- Web 和 CLI 的共享 truth 与差异层被明确区分
- 下游 task 不需要再猜 Web 的 MVP 范围
