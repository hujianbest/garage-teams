# Garage Coding Pack

- 状态: phase 1 scaffold
- 日期: 2026-04-11
- 定位: `garage/packs/coding/` 是 `Coding Pack` 的实现根目录，后续承接 intake、specify、design、tasking、implement、review、verify 与 closeout 相关实现壳。

## 当前角色

phase 1 中，这里是 `Coding Pack` 的目标实现面。

当前它与现有资产的关系是：

- `ahe-coding-skills/` 仍是来源资产与参考面
- 这里才是后续 `Garage` runtime 中的 pack 落点

## 边界

这里放：

- pack manifest
- pack-local roles / nodes
- 下游 artifact 与 evidence mappings
- bridge intake 与 closeout 相关钩子

这里不放：

- 平台中立 core 逻辑
- `ahe-coding-skills/` 的整体直接搬运副本
