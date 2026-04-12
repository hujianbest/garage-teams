# T103: Host Bridge Implementation

- Task ID: `T103`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 落 `HostBridgeEntry` 作为 capability injection 层的实现切片。
- 关联设计文档:
  - `docs/features/F103-host-bridge-capability-injection.md`
  - `docs/design/D103-host-bridge-integration-design.md`

## 1. 交付目标

- shared host bridge seam
- concrete host adapter injection paths
- host hints stay below runtime truth

## 2. 最小交付物

- shared host bridge seam
- 至少一条具体宿主适配路径
- host hint / context injection 边界
- host failure / rejection 回退语义

## 3. 依赖

- `F103`
- `F161`
- `D103`

## 4. 验收

- HostBridge 只注入能力，不拥有系统真相
- 具体宿主路径可以建立在 shared bridge seam 上
- provider authority / pack truth / growth truth 不会被 host 抢走
