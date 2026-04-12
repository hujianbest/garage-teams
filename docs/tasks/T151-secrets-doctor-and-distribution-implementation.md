# T151: Secrets, Doctor, And Distribution Implementation

- Task ID: `T151`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 落 secrets / credential resolution、doctor 与 distribution 主线的实现切片。
- 关联设计文档:
  - `docs/features/F161-provider-authority-placement.md`
  - `docs/design/D103-host-bridge-integration-design.md`

## 1. 交付目标

- authority-backed secrets
- runtime doctor
- distribution/install path

## 2. 最小交付物

- secrets / credential resolution
- runtime doctor
- distribution / install layout baseline

## 3. 验收

- provider authority 不会因 secrets/distribution 再次漂移
- runtime home 可被诊断、安装、升级
- 下游 ops / observability / web depth 有稳定交付前提
