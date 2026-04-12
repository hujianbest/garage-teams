# D11: Reference Pack Designs

- Design ID: `D11`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 收口当前 reference packs 的设计主线，说明它们怎样作为 `Garage Team` 的能力面展开。
- 关联文档:
  - `docs/GARAGE.md`
  - `docs/features/F15-pack-platform-and-collaboration.md`
  - `docs/features/F14-continuity-and-growth.md`

## 1. 这份文档回答什么

当前 reference packs 怎样作为产品能力面与团队协作面存在。

## 2. 设计目标

- 让 reference packs 作为 `Garage Team` 的能力面被清楚定义
- 说明它们如何复用 shared runtime、governance、continuity 和 bridge 主线
- 让下游实现和任务切片不再需要猜 pack 设计的最小范围

## 3. 共同设计原则

- 每个 pack 都代表一类团队能力，而不是一组孤立脚本
- 每个 pack 都必须显式说明 roles、outputs、review points 和 evidence hooks
- 每个 pack 都必须能接入 cross-pack collaboration，而不是被封闭成私有岛

## 4. 当前 reference pack 角色

- `Product Insights`
  - 负责研究、洞察、问题结构化和向下游 pack 输出可消费结果
- `Coding`
  - 负责实现、验证、修订与交付代码相关结果

## 5. 下游 specs

- `D111`：Product Insights pack design
- `D112`：Coding pack design
- `D113`：Cross-pack workflow design
