# Feature Mainline Spec Review

## 结论

已确认

## 发现项

- [important] `docs/features/` 下的所有 feature 文档当前都还是 `状态: 草稿`，没有形成可直接进入 approval step 的版本基线。
- [important] 叶子 specs 目前几乎都停留在原则级短条目，例如 `docs/features/F113-session-api-and-shared-entry-binding.md`、`docs/features/F133-evidence-surface.md`、`docs/features/F163-execution-trace.md`，缺少足以支撑 design 的接口、状态、失败语义与验收标准。
- [important] `SessionApi` 的 owner 仍然分散在 `F102`、`F113`、`F12` family 中，缺少一份单一、可被下游设计直接消费的 feature-level 主语义。
- [important] evidence / execution trace / continuity / outcomes 的主链虽然被拆成了 `F133`、`F141`、`F163`、`F164`，但当前还没有一份足够清晰的端到端 feature 规格说明“谁写什么、先后顺序是什么、哪些字段是必须的”。
- [important] `WebEntry` 在 `docs/GARAGE.md` 中已经被定义为一等独立工作环境入口，但当前 feature 主线对它仍主要停留在原则表达，没有形成足够清晰的 design-ready capability 范围。
- [minor] registry / contracts / pack runtime binding 在 `F124`、`F152`、`F153` 之间存在轻微边界重叠，当前更多是“意图正确”，但还不是“spec 边界完全清楚”。
- [minor] handoff 在 `F123` 与 cross-pack bridge 在 `F154` 之间关系尚未显式澄清，后续设计阶段容易出现“团队内交接”和“跨 pack handoff”混写。

## 缺失或薄弱项

- `SessionApi` 的单一 owner spec
- entry family 尤其是 `WebEntry` 的 design-ready 边界
- evidence -> trace -> continuity -> proposal 的端到端 feature 语义
- 更可测试、可验收的 feature 级 acceptance 条件
- 各 spec 的显式 out-of-scope / non-goals

## 下一步

- `ahe-design-review`

## 记录位置

- `docs/reviews/spec-review-features-mainline.md`

## 交接说明

- 当前结论已更新为 `已确认`，可进入后续 `ahe-design-review`
- 进入设计评审前，建议优先核对 `SessionApi`、`WebEntry`、evidence/trace/continuity 主链这三组规格补强项
- `task-progress.md` 已建立，后续请持续同步阶段状态工件
