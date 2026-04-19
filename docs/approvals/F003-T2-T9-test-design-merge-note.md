# F003 T2-T9 测试设计批准合并说明

- 适用范围: F003 任务计划 §5 中除 T1 之外的全部任务（T2-T9）
- Workflow Profile: `full`
- Execution Mode: `auto`
- Date: 2026-04-18

## 背景

F003 在 `auto` 模式下推进。`hf-tasks-review` r3 通过后，父会话以 `tasks-approval` 把整个任务计划（含每个任务的"测试设计种子"段落）一次性批准。后续 `hf-test-driven-dev` 在 auto 模式下进入实现，仅 T1 单独产出了一份独立的 `F003-T1-test-design-approval.md`；T2-T9 的测试设计是随 `tasks-approval` 合并批准并直接进入实现的。

## 治理路径

- T2-T9 的"测试设计"内容来源于 `docs/tasks/2026-04-18-garage-memory-auto-extraction-tasks.md` §5 中各任务的「测试设计种子」段落，已在 `docs/approvals/F003-tasks-approval.md` 范围内被显式批准。
- 实现期间的 fail-first 测试与"测试设计种子"对齐情况，在 `docs/verification/F003-test-review-r1-handoff.md` 与 `docs/verification/F003-code-review-r1-handoff.md` 的"与任务计划测试种子的差异"段中逐项记录。
- `hf-test-review` 三轮（r1 / r2 / r3）已对 T2-T9 的实际测试质量做出 verdict：
  - r1 = 需修改（覆盖关闭分支、supersede/abandon、truncation、FR-302b 校验缺口）
  - r1 follow-up + r2 = 通过
  - code-review r1 follow-up + r3 = 通过
- `hf-traceability-review` 已在 link matrix 中为每个 FR/任务建立到测试与验证证据的稳定锚点，并把"仅 T1 有 testDesignApproval"明确标注为 minor LLM-FIXABLE，建议在 `hf-finalize` 阶段以 merge note 形式回写——本文件即该 merge note。

## 结论

- T2-T9 的测试设计在 `auto` 模式下随 `docs/approvals/F003-tasks-approval.md` 合并批准，无需补独立的 per-task `test-design-approval.md`。
- 后续如再次出现 `hf-tasks-review` 退回或 `hf-test-review` 提出"测试设计应当与任务批准解耦"的硬要求，由 `hf-workflow-router` 重新拉起 per-task test-design approval。

## Related Artifacts

- `docs/approvals/F003-tasks-approval.md`
- `docs/approvals/F003-T1-test-design-approval.md`
- `docs/tasks/2026-04-18-garage-memory-auto-extraction-tasks.md`
- `docs/reviews/test-review-F003-garage-memory-auto-extraction.md`（r1）
- `docs/reviews/test-review-F003-garage-memory-auto-extraction-r2.md`
- `docs/reviews/test-review-F003-garage-memory-auto-extraction-r3.md`
- `docs/reviews/code-review-F003-garage-memory-auto-extraction.md`（r1）
- `docs/reviews/code-review-F003-garage-memory-auto-extraction-r2.md`
- `docs/reviews/traceability-review-F003-garage-memory-auto-extraction.md`
- `docs/verification/F003-T1-implementation-handoff.md`
- `docs/verification/F003-test-review-r1-handoff.md`
- `docs/verification/F003-code-review-r1-handoff.md`
