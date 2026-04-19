# Tasks Review — F004 Garage Memory v1.1（发布身份解耦与确认语义收敛）

- 评审范围: `docs/tasks/2026-04-19-garage-memory-v1-1-tasks.md`（草稿）
- Review skill: `hf-tasks-review`
- 评审者: cursor cloud agent (auto mode, reviewer subagent，由 `hf-tasks` 父会话派发)
- 日期: 2026-04-19
- Workflow Profile / Mode: `full` / `auto`
- Workspace Isolation: `in-place`
- 上游证据基线:
  - 已批准规格: `docs/features/F004-garage-memory-v1-1-publication-identity-and-confirmation-semantics.md`
  - 已批准设计: `docs/designs/2026-04-19-garage-memory-v1-1-design.md`（r1）
  - Spec 审批: `docs/approvals/F004-spec-approval.md`（auto-mode）
  - Design 审批: `docs/approvals/F004-design-approval.md`（auto-mode r1，4/4 finding 闭合）
  - Spec 评审: `docs/reviews/spec-review-F004-memory-v1-1.md`（通过）
  - Design 评审: `docs/reviews/design-review-F004-memory-v1-1.md`（需修改 → r1 1:1 闭合）
  - 历史参照: `docs/tasks/2026-04-18-garage-memory-auto-extraction-tasks.md`、`docs/approvals/F003-T2-T9-test-design-merge-note.md`
  - `task-progress.md`（Stage=`hf-tasks`，Pending=`hf-tasks-review`，profile/mode 一致）
  - `AGENTS.md`（关键命令：`uv run pytest tests/ -q`、`uv run pytest tests/memory/ -q` 等）

## 1. Precheck

| 检查项 | 结果 |
|--------|------|
| 存在稳定可定位 task plan draft | ✓ `docs/tasks/2026-04-19-...md` 草稿完整、326 行、§1~§10 章节齐备 |
| 上游 spec 已批准 + evidence 可回读 | ✓ F004 spec approval（auto-mode）+ spec-review record 通过 |
| 上游 design 已批准 + evidence 可回读 | ✓ F004 design approval r1（auto-mode）+ design-review r1 finding 4/4 闭合 |
| route / stage / profile / mode 一致 | ✓ task-progress：Stage=`hf-tasks`、Pending=`hf-tasks-review`、Profile=`full`、Mode=`auto` |
| F004 不含 UI surface | ✓ 设计 §9 模块表与规格 §4.1 均无前端 / 页面 / 组件 |
| 上游证据无冲突 | ✓ design-review r1 全部 finding 已在 design r1 闭合；spec-review 3 项 minor 在 spec approval 前已收敛 |

Precheck 通过，进入正式 rubric。

## 2. 多维 rubric 评分

| 维度 | 评分 | 关键观察 |
|------|------|----------|
| TR1 可执行性 | 9/10 | 5 个任务全部冷启动可执行；最大单任务 T2 虽包装 3 个子动作（store-or-update / supersede carry-over / self-conflict 短路），但均落在 `publisher.publish_candidate` 同一函数路径上，互相耦合（短路是 store-or-update 决策的前置剔除；carry-over 是 update 路径子动作），不构成 TA1 |
| TR2 任务合同完整性 | 10/10 | 每个任务显式 `Acceptance`、`Files`、`Verify`、`完成条件`、`测试设计种子`、`Ready When`、`Selection Priority`、`初始队列状态` |
| TR3 验证与测试设计种子 | 9/10 | T1=5 测试 / T2=7 / T3=6 / T4=6 / T5=3；每任务至少 1 条 fail-first；T2 含 §10.1.1 self-conflict 关键边界 + §11.2.1 supersede 不变量 + NFR-402 wall-clock；T4 含 schema 不变量；docs lint 用 token 检查 |
| TR4 依赖与顺序 | 9/10 | T1→T2→T3 (P1)、T4 (P2 解耦) 但实施顺序排 T3 后、T5 (P3) 依赖全部；无循环；T3 显式说明依赖 T2 是因为需 §10.1.1 短路才能让 fixture "命中相似条目" 指向真冲突而非自冲突，逻辑成立 |
| TR5 追溯覆盖 | 8/10 | §4 追溯矩阵覆盖 FR-401/402/403a-c/404/405、NFR-401/402、IFR-401/402、CON-401~404、design §10.1.1 / §11.2.1 / §11.4；存在 1 处轻微缺口：CON-403（schema 兼容）只挂到 T4+T5，但实际也涉及 T3 的 confirmation 字段语义化（不删字段 + 字段值复用） |
| TR6 Router 重选就绪度 | 8/10 | §6 队列投影 + §6.1 显式描述每个完成节点的唯一 next-ready 选择；§6.2 含"多 ready 同优先级 hard stop"；唯一缺口：§6 表中 T4 Status=`pending`，但 T4 `Ready When=F004 spec/design approval 已完成`（已满足）—— Status 与 Ready When 不一致，§6.1 又说"T1 完成后 T4 此时也 ready（无依赖、Priority P2）"，未来 router 在启动时是否把 T4 视作 ready 取决于看 Status 还是 Ready When；不影响最终选择（T1 是 P1 唯一）但表语义不对齐 |

所有维度 ≥ 8/10，全部高于 6/10 通过门槛。

## 3. 正式 checklist 审查

### 3.1 TR1 可执行性

- T1：单一职责（generator + 入口校验前置），单文件 + 单测试文件，5 个测试名 ✓
- T2：3 个子动作均锚定同一函数路径上的连续逻辑，且 `store-or-update` 决策与 `self-conflict 短路` 在判定 `similar_entries` 是否要求 strategy 之前必须协同（拆开会导致中间态不能通过测试），打包合理；7 个测试名 ✓
- T3：CLI 双路径文案 + confirmation 字段 + 6 个测试名 ✓
- T4：分 phase try/except + `_persist_extraction_error` + 6 个测试名（含 success path / disabled path / schema invariant）✓
- T5：文档段 + docs lint + 全 suite 回归，3 个测试名 ✓

无"实现某模块"式抽象任务。✓ TA1 不命中。

### 3.2 TR2 任务合同完整性

- 每任务都有 `Acceptance`、`Files / 触碰工件`、`Verify`、`完成条件`、`测试设计种子` ✓
- Verify 命令全部使用 AGENTS.md 中声明的真实命令：`uv run pytest tests/memory/ -q`、`uv run pytest tests/ -q`、`uv run mypy src/`、`uv run ruff check src/ tests/` ✓
- 每任务的 `Acceptance` 都可冷读出"完成时什么必须为真" ✓

✓ TA2 / TA3 不命中。

### 3.3 TR3 验证与测试设计种子

- T1 fail-first：`test_publication_identity_generator_is_deterministic` ✓
- T2 fail-first：`test_repeated_accept_uses_update_increments_version`；关键边界：`test_repeated_accept_short_circuits_self_conflict`、`test_repeated_publish_preserves_supersedes_chain_from_v1`、`test_repeated_publish_preserves_related_decisions_from_v1` ✓
- T3 fail-first：`test_memory_review_abandon_writes_resolution_abandon_with_null_strategy`；关键边界：`test_memory_review_two_abandon_markers_do_not_overlap` ✓
- T4 fail-first：`test_archive_session_persists_extraction_error_orchestrator_init`；schema 不变量：`test_memory_extraction_error_json_has_full_schema` ✓
- T5：3 个 docs lint 用 token 检查（"abandon" + "publication attempt" + "conflict" / "PublicationIdentityGenerator" + "version" + "update" / "memory-extraction-error.json" + "phase" + 三个枚举值）✓

✓ TA4 不命中。每个任务都不是空泛"补测试"。

### 3.4 TR4 依赖与顺序正确性

依赖图（线性 + 1 旁路）：

```
T1 (P1, ready)
  └─ T2 (P1, depends T1)
        └─ T3 (P1, depends T2 — 因 §10.1.1 短路使 T3 测试中的"命中相似条目"语义可锚定)
T4 (P2, 与 T1/T2/T3 解耦；实施顺序排 T3 后)
T5 (P3, depends T1+T2+T3+T4)
```

- 无循环 ✓
- T3 → T2 的反向依赖（"命中相似条目"在 T2 self-conflict 短路实现后才能稳定指代真冲突）经过显式论证，合理 ✓
- T4 与 T1~T3 解耦让 router 在 T1 完成后存在"P1 vs P2"的优先级竞争，作者用 P1 > P2 显式打破 ✓

### 3.5 TR5 追溯覆盖

§4 追溯矩阵：

- FR-401 → T1+T2 ✓
- FR-401+FR-405 supersede 链 carry-over → T2 ✓
- FR-401 self-conflict 短路 → T2 ✓
- FR-402 → T1 ✓
- FR-403a → T3 ✓
- FR-403b → T3 ✓
- FR-403c → T5 ✓
- FR-404 → T4 ✓
- FR-405 兼容性 → T2+T3+T4+T5 显式 verify 全 suite ✓
- NFR-401 决定性 → T1 ✓
- NFR-402 不退化 → T2 wall-clock ✓
- IFR-401/402 复用 update → T2 ✓
- CON-401~404 → T4+T5（`CON-403` 也涉及 T3 confirmation 字段语义化，矩阵未显式登记，见 finding F1）
- 设计 §10.1.1 self-conflict 短路 → T2 ✓
- 设计 §11.2.1 PRESERVED_FRONT_MATTER_KEYS → T2 ✓
- 设计 §11.4 memory-extraction-error.json schema → T4 ✓
- ASM-403 不补 publisher 专项 benchmark → §9 不在范围内显式声明 ✓

无 orphan task。✓ TA6 不命中。

### 3.6 TR6 Router 重选就绪度

- §6 表给出 Status / Depends On / Ready When / Selection Priority 4 列 ✓
- §6.1 描述每个 router 重选触发点的唯一 next-ready：
  - 启动 → T1（P1 唯一 ready）
  - T1 完成 → T2 vs T4，P1>P2 → T2
  - T2 完成 → T3 vs T4，P1>P2 → T3
  - T3 完成 → T4 唯一
  - T4 完成 → T5 唯一
  - T5 完成 → `hf-finalize`
- §6.2 显式 hard stop on tie ✓
- 缺口（finding F2）：§6 表中 T4 Status=`pending`，与其 `Ready When=F004 spec/design approval 已完成`（启动时已满足）不一致；§6.1 又说"T1 完成后 T4 此时也 ready（无依赖、Priority P2）"——三处表述应统一

✓ TA7 不命中（最终唯一规则成立）；只是描述层面的一致性可优化。

## 4. 发现项

### F1 [minor][LLM-FIXABLE][TR5] §4 追溯矩阵中 CON-403 仅挂 T4+T5，未显式登记 T3 confirmation 字段语义化

`CON-403`（schema 演进可兼容）规格层定义"`confirmation_ref` 与 `KnowledgeEntry.front_matter` 在 v1.1 后旧版数据仍可读；新增字段只追加、不删除已有字段"。T3 在 confirmation 持久产物上把 `resolution=accept + conflict_strategy=abandon` 与 `resolution=abandon + conflict_strategy=null` 两条路径字段语义化（复用现有字段而非加新字段），正是 CON-403 的直接落点。当前矩阵把 CON-401~404 整体行打包到 T4+T5，建议在矩阵中追加一行或拆分让 CON-403 同时挂 T3。

修订建议：在 §4 追溯矩阵将 `CON-401~404` 行拆为 4 条单行映射，CON-401→T4、CON-402→所有任务、CON-403→T3+T4、CON-404→T4+T5。

### F2 [minor][LLM-FIXABLE][TR6] T4 队列状态 Status=`pending` 与 `Ready When=F004 spec/design approval 已完成` 矛盾

§6 表：

```
T4 | pending | - | F004 spec/design approval 已完成 | P2
```

T4 `Depends On = -`，且 `Ready When` 在启动时即满足（spec/design 已批准），按其它 task 的对应关系（T1 同样 `Depends On = -` 且 Ready When 同条件 → Status=`ready`），T4 启动时也应是 `ready`。但表中标 `pending`。§6.1 又写"启动时：T1 是唯一 P1 ready，选 T1"——若 T4 启动时也 ready，则更准确的描述应为"T1 与 T4 启动时同时 ready，但 P1 > P2 → 选 T1"。

修订建议：把 T4 Status 改为 `ready`，并把 §6.1 启动段改为"T1 与 T4 启动时同时 ready，按 Selection Priority P1 > P2，选 T1"。语义不变，但表格与描述对齐，router 实施时不再需要额外判断。

### F3 [minor][LLM-FIXABLE][TR5] T2 性能验收"F003 baseline" 数值锚点未具名

T2 Acceptance 第 7 条与测试种子 #7：`pytest tests/memory/ -q` 总时长不超过 F003 baseline 的 110%。但 baseline 具体秒数未在 task plan 或 design / spec 中固化，T2 实施者必须先复跑 F003 现状再得到一个 baseline。设计 §12 末尾 ASM-403 决议"wall-clock suite 已能反映回归"已经隐含此意，但 T2 验收应显式说明 baseline 取得方式（如"实施前先 git checkout F003 完结点跑 3 次取均值，写入 task implementation handoff"）。

修订建议：在 T2 Acceptance 第 7 条尾部追加"baseline 取得方式：实施前 git checkout F003 完结 commit 跑 3 次取均值"或在 §10 Open Questions #2 中补一句指向。

### 整体评估

- 0 critical
- 0 important
- 3 minor LLM-FIXABLE
- 0 USER-INPUT

3 条 minor 全部为可在 author self-check 中 1:1 收敛的小修，不影响任务计划的可执行性、依赖正确性与测试设计种子充分性。

## 5. 缺失或薄弱项

- 无关键缺失。3 条 finding 都是表语义层面的微调或追溯矩阵的细化，不涉及任务边界 / 范围 / 测试策略 / 依赖结构。
- 风险表 §8 已主动列出 6 项关键风险（含 supersede 链丢失 / self-conflict false-positive / 145+384 回归 / 性能退化 / 命名漂移 / docs lint 漂移），且每项都映射到具体测试或 design contract 锁住，韧性策略充分。
- §10 Open Questions 含 2 项非阻塞，已显式标注解决方向。

## 6. 结论

**通过**

理由：

1. Precheck 6 项全部满足
2. 6 维 rubric 全部 ≥ 8/10，无任一维度跌破 6/10 门槛
3. 3 条 minor LLM-FIXABLE finding 不阻塞下游进入 `hf-test-driven-dev`，可由 author 在 task plan approval step 前顺手 self-check 闭合（参考 spec / design approval 的 self-check 模式）
4. 任务粒度合理，每任务 fail-first 测试 + 关键边界覆盖到位
5. 队列投影规则唯一可决（finding F2 的不一致只是表述层面，最终选择无歧义）
6. 与 design-review r1 闭合后的 §10.1.1 / §11.2.1 contract 1:1 对齐
7. 测试设计 approval 治理路径（§7）沿用 F003 已确立的 testDesignApproval 模式

## 7. 下一步

- `任务真人确认`（auto mode 下父会话写 task plan approval record）
- `needs_human_confirmation = true`（按 hf-tasks-review SKILL §4：通过时强制设 true）
- `reroute_via_router = false`
- 建议 author 在 approval 落盘前顺手 1:1 收敛 F1 / F2 / F3 三条 minor，避免拖入 hf-test-driven-dev cycle 内

## 8. 记录位置

- 本 review record：`docs/reviews/tasks-review-F004-memory-v1-1.md`

## 9. 交接说明

- 父会话（`hf-tasks`）收到本 reviewer 返回后：
  - 结论 = `通过` → 触发"任务真人确认" approval step（auto-mode 下由 author 写 approval record 到 `docs/approvals/F004-tasks-approval.md`）
  - 不需要复派 reviewer subagent
  - 不需要回流 `hf-workflow-router`
  - 进入 `hf-test-driven-dev` 前，建议把 F1/F2/F3 顺手收敛进 task plan r1（修订幅度极小，无需重新评审）

## 10. 结构化返回 JSON

```json
{
  "conclusion": "通过",
  "next_action_or_recommended_skill": "任务真人确认",
  "record_path": "docs/reviews/tasks-review-F004-memory-v1-1.md",
  "key_findings": [
    "[minor][LLM-FIXABLE][TR5] §4 追溯矩阵中 CON-403 未显式挂到 T3 confirmation 字段语义化（实际涉及 T3+T4）",
    "[minor][LLM-FIXABLE][TR6] T4 Status=pending 与 Ready When=spec/design approval 已完成 在表语义上不一致，§6.1 描述同样可优化",
    "[minor][LLM-FIXABLE][TR5] T2 性能验收的 F003 baseline 数值锚点未显式说明取得方式"
  ],
  "needs_human_confirmation": true,
  "reroute_via_router": false,
  "finding_breakdown": [
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TR5",
      "summary": "§4 追溯矩阵 CON-403 应同时挂到 T3（confirmation 字段语义化）"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TR6",
      "summary": "T4 Status 标注与 Ready When 不一致；§6.1 启动选择描述可同步对齐"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TR5",
      "summary": "T2 性能验收应显式说明 F003 baseline 取得方式"
    }
  ]
}
```
