# T113: Execution Authority Implementation

- Task ID: `T113`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 落 provider authority placement、execution runtime 与 trace mainline 的实现切片。
- 关联设计文档:
  - `docs/features/F161-provider-authority-placement.md`
  - `docs/features/F162-tool-execution-capability-surface.md`
  - `docs/features/F163-execution-trace.md`
  - `docs/features/F164-evidence-linked-execution-outcomes.md`

## 1. 交付目标

- provider authority below core
- execution runtime
- shared execution trace

## 2. 最小交付物

- provider authority placement baseline
- tool capability surface baseline
- execution runtime mainline
- normalized execution trace

## 3. 依赖

- `F161`
- `F162`
- `F163`
- `F164`

## 4. 验收

- provider truth 不会被 host 或 packs 抢走
- tool capability surface 有清楚 owner 和实现边界
- execution / trace / evidence-linked outcomes 形成一条完整实现主线
