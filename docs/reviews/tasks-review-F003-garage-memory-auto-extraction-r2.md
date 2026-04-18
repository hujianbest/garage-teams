# 任务计划评审记录（第二轮）：F003 Garage Memory 自动知识提取与经验推荐

- 评审对象: `docs/tasks/2026-04-18-garage-memory-auto-extraction-tasks.md`
- 关联规格: `docs/features/F003-garage-memory-auto-extraction.md`
- 关联设计: `docs/designs/2026-04-18-garage-memory-auto-extraction-design.md`
- 关联批准记录:
  - `docs/approvals/F003-spec-approval.md`
  - `docs/approvals/F003-design-approval.md`
- 上一轮评审: `docs/reviews/tasks-review-F003-garage-memory-auto-extraction.md`
- 评审日期: 2026-04-18
- 评审角色: 独立 reviewer subagent

## Precheck

- 已存在稳定、可定位的任务计划草稿，且 `task-progress.md` 仍明确当前处于 `hf-tasks`，待执行 `hf-tasks-review`。
- 已批准 spec / design 的 approval evidence 均可回读，`Current Stage`、`Pending Reviews And Gates`、`Next Action Or Recommended Skill` 三者一致。
- `Current Active Task` 当前仍指向 “F003 任务计划草稿”，与本次复审对象一致；不存在需要先经 `hf-workflow-router` 重编排的 route / stage / profile 冲突。
- 结论：precheck 通过，可进入正式 rubric 复审。

## 结论

需修改

相较上一轮，本次回修已经完成了明确的定向修正：

1. 上一轮关于“自动提取 / 推荐可关闭”的重要 finding 已被显式承接：新增 T4 作为统一 memory feature flag / 配置开关任务，补齐了配置落点、runtime 读取点、关闭时降级行为以及 on/off 验证路径。
2. 上一轮关于“CLI-first 主动推荐展示路径缺 owner task”的重要 finding 已被显式承接：T8 现在明确把 `src/garage_os/cli.py`、`tests/test_cli.py` 纳入 `garage run <skill>` 执行前推荐摘要的 canonical CLI 路径。
3. 上一轮关于 `edit_accept` 测试设计种子的 minor finding 已被显式承接：T5 已补上“编辑后接受 -> 发布内容与 confirmation record 一致”的 fail-first 种子。

因此，上一轮 2 个 important finding 和 1 个 minor finding 均已完成定向回修，本轮不再重复提出。

本轮仍不给出“通过”，原因不是旧问题未修，而是任务计划在回修后引入了一个新的依赖一致性缺口：T6 / T7 的任务明细区块、依赖图、顺序说明、queue projection 之间出现了相互冲突的前置条件定义。这个问题会直接影响后续 `hf-test-driven-dev` 与 router 对“何时可选下一个任务”的一致判断，因此仍应先做一次小范围回修，再进入 `任务真人确认`。

## 维度评分

| 维度 | 评分 | 评语 |
|------|------|------|
| `TR1` 可执行性 | 8/10 | 9 个任务仍保持单任务可验证闭环，新增 T4 也成功把开关契约从“无 owner”变成了可执行任务。 |
| `TR2` 任务合同完整性 | 8/10 | 关键任务现在普遍具备 `Acceptance / Files / Verify / 完成条件`；只剩少量文案级一致性问题。 |
| `TR3` 验证与测试设计种子 | 8/10 | 上一轮缺失的 `edit_accept` 核心路径已补齐，主要主链都有可进入 fail-first 的 test seed。 |
| `TR4` 依赖与顺序正确性 | 6/10 | T6 / T7 的依赖与 ready 条件在任务正文和队列投影视图中互相冲突，影响顺序定义的单一真相。 |
| `TR5` 追溯覆盖 | 8/10 | 上一轮缺失的开关契约与 CLI-first 主动推荐路径均已补回，关键 FR / 设计锚点基本闭合。 |
| `TR6` Router 重选就绪度 | 7/10 | 当前 `T1` 仍唯一，但 T6 / T7 的双重依赖定义会让后续重选时出现“正文一套、queue 一套”的歧义。 |

## 发现项

- [important][LLM-FIXABLE][TR4] 本轮回修后，T6 / T7 的前置条件定义出现内部冲突：任务正文里 T6 写的是 `依赖: T4`、`Ready When: T4=done`，T7 也写的是 `依赖: T4`、`Ready When: T4=done`；但依赖图、queue projection 与顺序说明又把 T6 / T7 写成依赖 T5。由于 T6 是“冲突探测与发布策略”，T7 是“CLI-first 候选确认入口”，二者都明显建立在 review / publish 主链之上，这种双重定义会让实现者与 router 对“何时可开工”得出不同答案，需统一成单一真相。
- [minor][LLM-FIXABLE][TR2] 任务计划头部与里程碑统计仍是旧计数：概述写“拆成 8 个任务”，里程碑任务数统计也仍是 `2 + 4 + 2`，但正文实际已是 T1-T9 共 9 个任务。该问题不阻塞执行，但会降低计划的可读性与评审信心，建议顺手回修。

## 缺失或薄弱项

- 上一轮要求补回的 3 个定向问题均已解决，本轮无需再就开关契约、CLI-first 推荐展示路径、`edit_accept` 测试种子重复回修。
- 当前缺口集中在“依赖定义一致性”与“文案统计同步”，不需要重做任务拆解，也不需要重画整体依赖图。
- `Current Active Task = T1` 目前仍唯一成立；本轮不是 workflow blocker，无需 reroute。

## 下一步

- `需修改`：`hf-tasks`

## 记录位置

- `docs/reviews/tasks-review-F003-garage-memory-auto-extraction-r2.md`

## 交接说明

- 回修时请优先统一 T6 / T7 在“任务正文 / 依赖图 / queue projection / 顺序说明”中的依赖与 `Ready When` 定义，只保留一个可回读的单一真相。
- 建议以 queue projection 与顺序说明为基线回写任务正文，避免后续 router 依据不同区块读出不同 ready 条件。
- 同步更新“总任务数 / 里程碑任务数”这类文案统计即可；本轮不要求新增任务，也不要求重做验收拆分。
- 本轮不是 workflow blocker；修订任务计划后，可再次派发 `hf-tasks-review` 复审。
