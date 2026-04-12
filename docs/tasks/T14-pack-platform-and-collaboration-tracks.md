# T14: Pack Platform And Collaboration Tracks

- Task ID: `T14`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 拆解 pack platform、shared contracts、reference packs 与 cross-pack collaboration 的实现任务。
- 关联设计文档:
  - `docs/features/F15-pack-platform-and-collaboration.md`
  - `docs/design/D11-reference-pack-designs.md`

## 1. 这份文档回答什么

pack platform、shared contracts、reference packs 与 cross-pack collaboration 应如何拆成实现任务。

## 2. 推荐顺序

1. `T141` shared contracts and registry
2. `T142` reference packs
3. `T143` cross-pack bridge

## 3. family 交付目标

- contracts / registry 主线稳定
- reference packs 作为产品能力面稳定
- cross-pack bridge 进入可追溯的实现主线

## 4. 并行与依赖

- `T141` 是 pack family 的基线
- `T142` 依赖 `T141`
- `T143` 依赖 `T141` 和 `T142`

## 5. 验收

- packs 能通过 shared contracts 和 registry 接入
- reference packs 能作为产品能力面存在
- cross-pack bridge 的 implementation 不再需要猜其对象和阶段

## 6. 非目标

- 不在这里定义 provider authority
- 不把 bridge 设计成 privileged core contract

## 7. 下游 specs

- `T141`：shared contracts and registry implementation
- `T142`：reference packs implementation
- `T143`：cross-pack bridge implementation
