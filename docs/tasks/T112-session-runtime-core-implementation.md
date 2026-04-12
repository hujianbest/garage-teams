# T112: Session Runtime Core Implementation

- Task ID: `T112`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 落 neutral runtime records、SessionApi、session lifecycle 与 registry core 的实现切片。
- 关联设计文档:
  - `docs/features/F121-neutral-runtime-records.md`
  - `docs/features/F122-session-lifecycle.md`
  - `docs/features/F123-handoff-and-review-boundaries.md`
  - `docs/features/F124-registry-backed-capability-discovery.md`
  - `docs/features/F113-session-api-and-shared-entry-binding.md`

## 1. 交付目标

- neutral runtime records
- session lifecycle
- SessionApi / registry core

## 2. 最小交付物

- neutral records model
- session lifecycle and state transitions
- SessionApi core path
- registry-backed capability discovery baseline

## 3. 依赖

- `F121`
- `F122`
- `F123`
- `F124`

## 4. 验收

- runtime core 能以中立对象支撑 team work
- session lifecycle 与 handoff/review 边界清楚
- SessionApi 和 registry 不再需要下游实现自行补脑
