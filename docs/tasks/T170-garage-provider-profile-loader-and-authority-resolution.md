# T170: Garage Provider Profile Loader And Authority Resolution

- Task ID: `T170`
- 状态: 已完成
- 日期: 2026-04-11
- 定位: 把 `runtime home` 中 `profiles / config / adapters` 的静态语义落成真实 loader 与 authority resolution 链，使 `CLIEntry`、`HostBridgeEntry`、`WebEntry` 共享同一条 provider / model 配置主线。
- 当前阶段: 完整架构主线下的第二组独立入口 implementation tracks
- 关联设计文档:
  - `docs/features/F210-runtime-home-and-workspace-topology.md`
  - `docs/features/F220-runtime-bootstrap-and-entrypoints.md`
  - `docs/features/F230-runtime-provider-and-tool-execution.md`
  - `docs/architecture/A120-garage-core-subsystems-architecture.md`
  - `docs/features/F050-governance-model.md`

## 1. 任务目标

在三类入口 family 都已被切成实现任务后，这一篇单独解决：

- provider / model 配置到底由谁决定
- 这些配置怎样从 `runtime home` 被解析出来
- 宿主 hint、入口偏好与 runtime authority 怎样被分层

它要证明的是：

- `RuntimeProfile` 是 provider / model authority 的主入口
- `runtime home` 下的 `profiles / config / adapters` 可以被真实加载与解析
- CLI、host bridge、web 不再各自长一套 provider 配置解析逻辑

## 2. 输入设计文档

这一篇主要承接：

- `RuntimeProfile` 作为 provider / model authority
- `runtime home` 的最小目录语义与解析顺序
- host 只能提交 hint，不能改写 authority
- execution layer 对 `ProviderAdapter` 与 `ToolRegistry` 的统一调用边界
- `SessionApi` / `Session` / `Governance` 对 execution 的前置约束

## 3. 本文范围

- `runtime home` 内 profile / config / adapters 的 loader
- provider / model / adapter authority resolution 顺序
- host hint、entry override 与 runtime default 的合并规则
- provider adapter 选择前的归一化配置对象
- authority 冲突、缺失与不兼容时的错误面

## 4. 非目标

- 不实现 provider marketplace
- 不一次性设计完整 secrets vault
- 不让宿主直接持有 vendor-specific 主配置
- 不在这里扩展 remote control plane 或多租户配置系统

## 5. 交付物

- 一条稳定的 `RuntimeProfile -> runtime home -> execution layer` 配置解析链
- 一组 `profiles / config / adapters` 的最小 loader 骨架
- 一套 host hint 与 runtime authority 的冲突处理规则
- 一组统一的 provider / model / adapter 归一化对象
- 给后续 `runtime ops / packaging / secrets` 切片复用的 authority 前提

## 6. 实施任务拆解

### 6.1 冻结 authority resolution 顺序

- 明确先选 `RuntimeProfile`，再解析 `runtime home` 内 provider / model / adapter 引用。
- 明确 host 与 entry 只能提交非权威 hint，而不是直接改写主配置。
- 明确 packs 继续只声明 capabilities，而不是声明 vendor / model。

### 6.2 落 `runtime home` loader

- 为 `profiles/`、`config/`、`adapters/` 准备最小 loader 骨架。
- 明确缺文件、缺字段、引用失配或目录不完整时如何报错。
- 保持 `cache/` 只承载派生物与可重建状态，不混入 authority 真相。

### 6.3 归一化 provider / model / adapter 选择结果

- 生成 execution layer 可直接消费的归一化配置对象。
- 让 `ProviderAdapter` 在统一 authority 下工作，而不是自己再决定主配置。
- 避免 CLI / host bridge / web 对同一 profile 得到不同解析结果。

### 6.4 接入三类入口 family

- 让 `CLIEntry`、`HostBridgeEntry`、`WebEntry` 都通过同一 loader 读取 authority。
- 明确 entry override 与 host hint 的允许范围。
- 保证入口差异只影响交互，不影响 provider authority 主线。

### 6.5 做最小验证闭环

- 验证同一 `RuntimeProfile` 在三类入口下得到相同 authority 结果。
- 验证 host hint 与 authority 冲突时会被显式拒绝或降级处理。
- 验证 execution layer 消费的是统一归一化配置对象，而不是入口私货。

## 7. 依赖与并行建议

- 依赖 `11`、`12`、`13`、`14`、`15`、`16`
- 应作为第二组独立入口切片的收束任务
- 完成后再继续切 `runtime ops / packaging / secrets` 会更稳定

## 8. 验收与验证

完成这篇任务后，应能验证：

- provider / model authority 已收敛到 `RuntimeProfile` 与 `runtime home`
- 三类入口共享同一套 loader 与 authority resolution 结果
- host hint 不会反向重写 provider 主配置
- execution layer 前已经存在统一的配置归一化对象

## 9. 完成后进入哪一篇

- `docs/tasks/T180-garage-secrets-and-credential-resolution.md`
- `docs/tasks/T181-garage-runtime-home-config-doctor.md`
- `docs/tasks/T200-garage-runtime-ops-and-diagnostics.md`
