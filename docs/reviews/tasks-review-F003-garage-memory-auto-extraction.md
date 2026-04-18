# 任务计划评审记录：F003 Garage Memory 自动知识提取与经验推荐

- 评审对象: `docs/tasks/2026-04-18-garage-memory-auto-extraction-tasks.md`
- 关联规格: `docs/features/F003-garage-memory-auto-extraction.md`
- 关联设计: `docs/designs/2026-04-18-garage-memory-auto-extraction-design.md`
- 关联批准记录:
  - `docs/approvals/F003-spec-approval.md`
  - `docs/approvals/F003-design-approval.md`
- 评审日期: 2026-04-18
- 评审角色: 独立 reviewer subagent

## Precheck

- 已存在稳定、可定位的任务计划草稿，且 `task-progress.md` 明确当前仍处于 `hf-tasks`、待执行 `hf-tasks-review`。
- 已批准 spec / design 的 approval evidence 均可回读，`task-progress.md` 的 `Current Stage`、`Pending Reviews And Gates`、`Next Action Or Recommended Skill` 三者一致。
- `Current Active Task` 当前指向 “F003 任务计划草稿”，与本次评审对象一致；不存在需要先经 `hf-workflow-router` 重编排的 route / stage / profile 冲突。
- 备注：设计批准记录已明确通过，但设计文档头部仍写“状态: 草稿”；该不一致属于上游文案残留，不影响本次 tasks review 合法进入正式 rubric 审查。

## 结论

需修改

当前任务计划已经具备较强的工程可执行性：8 个任务都有清晰目标，绝大多数关键任务都显式写出了 `Acceptance`、`Files`、`Verify`、测试设计种子和完成条件；依赖图总体无环，当前 `Current Active Task=T1` 也足够稳定，说明作者并非在用“里程碑冒充任务”。

本轮不给出“通过”的原因，不是因为计划整体失真，而是因为仍有两处关键 coverage gap 会直接影响后续实现是否忠实落到已批准 spec / design 上：

1. “自动提取 / 推荐可关闭”的开关契约没有被任何任务显式承接。
2. CLI-first 的主动推荐展示路径没有被任务计划完整拥有，当前拆解默认了 `SkillExecutor` 改完后 CLI 就会自然拿到推荐，但仓库现实并非如此。

这些问题都属于可定向回修的 `LLM-FIXABLE` 范畴，因此结论是 `需修改`，下一步回到 `hf-tasks` 修订任务计划即可，不需要改走 router。

## 维度评分

| 维度 | 评分 | 评语 |
|------|------|------|
| `TR1` 可执行性 | 8/10 | T1-T8 基本都能冷启动推进，未见明显“实现整条系统”式空泛大任务。 |
| `TR2` 任务合同完整性 | 7/10 | 关键任务大多具备 `Acceptance / Files / Verify / 完成条件`，但与开关契约相关的实现落点没有 owner task。 |
| `TR3` 验证与测试设计种子 | 7/10 | 多数任务已有可用 test seed，但 `edit_accept` 这条核心确认路径没有被显式种子承接。 |
| `TR4` 依赖与顺序正确性 | 7/10 | 主依赖链基本合理，但主动推荐的 canonical CLI 展示路径没有被拆成清晰的依赖闭环。 |
| `TR5` 追溯覆盖 | 6/10 | 大部分 FR/设计锚点已落任务，但“可关闭开关”与“CLI-first 主动推荐展示”仍存在覆盖缺口。 |
| `TR6` Router 重选就绪度 | 8/10 | 当前 `T1` 唯一；后续多任务并发点也写明了回到 router 的规则，queue projection 可回读。 |

## 发现项

- [important][LLM-FIXABLE][TR5] 规格明确要求“自动提取被关闭时跳过而不影响 session”“用户或配置显式关闭推荐时不触发查询”，设计也把“推荐可关闭”“兼容 memory feature flag 测试”写成显式约束；但任务计划没有任何任务显式承接开关契约、配置落点与实现/验证路径。当前只有 T7/T8 在 acceptance 中提到“推荐关闭/feature 关闭”，却没有 owner task 说明要修改哪些配置工件、哪些 runtime 读取点，以及自动提取关闭由谁落地。这会让 `FR-301`、`IFR-303`、`NFR-302`、`NFR-304` 的“尊重开关”在实现阶段缺少稳定入口。
- [important][LLM-FIXABLE][TR5] 设计 `9.8` 已把 CLI 定义为主动推荐的 canonical surface，要求 `garage run <skill>` 在真正执行前展示一次推荐摘要；但任务计划里，T7 只覆盖 `RecommendationService` 与 `SkillExecutor`，未把 `src/garage_os/cli.py` / `tests/test_cli.py` 纳入主动推荐任务，T6 又只覆盖 `garage memory review <batch-id>`。结合当前仓库现实，`garage run` 直接在 CLI 中调用 adapter 并不经过 `SkillExecutor`，意味着现有任务拆解无法保证“用户实际能在 CLI 路径看到主动推荐”，对 `FR-305` / `FR-306` 与设计 `10.3` 的覆盖仍不闭合。
- [minor][LLM-FIXABLE][TR3] `edit_accept` 是 `FR-303` 的核心确认动作之一，也出现在 T4/T6 的目标中，但现有测试设计种子只显式覆盖 accept / reject / defer / batch_reject，未单独种出“编辑后接受 -> 发布内容与 confirmation record 一致”的 fail-first 路径；后续实现容易把该动作降格成口头支持。

## 缺失或薄弱项

- 大多数任务合同已经齐全，回修重点应放在“补 owner task / Files / Verify / test seed”，而不是整体重写任务分解。
- `Current Active Task` 当前可唯一落到 T1；本轮未发现需要把当前 queue projection 判为失效的证据。
- T4/T5/T6/T7 的边界总体可接受，建议仅补齐开关契约与 CLI 主动推荐展示路径的任务归属，不必重做整个依赖图。

## 下一步

- `需修改`：`hf-tasks`

## 记录位置

- `docs/reviews/tasks-review-F003-garage-memory-auto-extraction.md`

## 交接说明

- 回修时应优先补上“开关/配置契约”由哪一任务实现、触碰哪些文件、如何验证；否则 T8 的 feature-on/off 验证会变成无 owner 的终局检查。
- 回修时应把“CLI-first 主动推荐展示”作为显式任务责任收口到具体文件与测试，而不是默认 `SkillExecutor` 改动会自然覆盖 CLI。
- 本轮不是 workflow blocker；无需 reroute。修订任务计划后，可再次派发 `hf-tasks-review` 复审。
