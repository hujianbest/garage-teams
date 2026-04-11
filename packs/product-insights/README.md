# Garage Product Insights Pack

- 状态: phase 1 scaffold
- 日期: 2026-04-11
- 定位: `packs/product-insights/` 是 `Product Insights Pack` 的当前目录入口，后续承接 framing、research、opportunity、concept、probe 与 bridge 相关实现壳。

## 当前角色

phase 1 中，这里是 `Product Insights Pack` 的目标实现面。

当前它与现有资产的关系是：

- `packs/product-insights/skills/` 仍是当前来源资产与参考面
- 这里才是后续 `Garage` runtime 中的 pack 落点

## 边界

这里放：

- pack manifest
- pack-local roles / nodes
- 上游 artifact 与 evidence mappings
- bridge-ready 输出钩子

这里不放：

- 平台中立 core 逻辑
- `packs/product-insights/skills/` 的整体直接搬运副本
