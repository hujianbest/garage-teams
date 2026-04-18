# 设计评审记录：F003 Garage Memory 自动知识提取与经验推荐（第二轮）

- 评审对象: `docs/designs/2026-04-18-garage-memory-auto-extraction-design.md`
- 关联规格: `docs/features/F003-garage-memory-auto-extraction.md`
- 关联批准记录: `docs/approvals/F003-spec-approval.md`
- 关联上一轮评审: `docs/reviews/design-review-F003-garage-memory-auto-extraction.md`
- 评审日期: 2026-04-18
- 评审角色: 独立 reviewer subagent

## Precheck

- 已存在稳定可定位的设计草稿，且 `task-progress.md` 明确当前仍处于 `hf-design`、待执行 `hf-design-review`。
- 已批准规格可回读，`docs/approvals/F003-spec-approval.md` 与规格状态一致。
- route / stage / profile / approval evidence 无冲突，本次第二轮 design review 合法进入正式评审。

## 结论

通过

作者已对上一轮 3 个 `important` finding 做出定向回修，且修订点都落到了可支撑后续 `hf-tasks` 的稳定 contract 上，而不是停留在补充性 prose：

1. 上一轮关于“自动提取输入证据契约未闭合”的问题，现已通过 `9.1A 输入证据最小契约` 明确三层证据来源、最小输入结构、`no_evidence / evaluated_no_candidate / evaluated_with_candidates` 判定与缺失记录策略，任务规划不再需要替设计补定义。
2. 上一轮关于“发布后 traceability / confirmation 契约未落到正式数据”的问题，现已通过 `11.4` 把 `KnowledgeEntry` 与 `ExperienceRecord` 的发布态可回读字段显式写出，并明确 `experience_summary` 第一版落到扩展后的 `ExperienceRecord`，从而闭合发布态追溯链。
3. 上一轮关于“主动推荐输入与 canonical surface 未收口”的问题，现已通过 `9.8 canonical surface` 与 `10.4 推荐触发输入构造与降级` 收敛到 CLI-first、host-compatible 的统一入口，并定义 richer context 的构造优先级与缺失降级规则。

基于当前设计文本，F003 已满足进入 `设计真人确认` 的条件：关键决策可追溯到已批准规格，新增模块边界清楚，约束与 NFR 已真正进入设计，接口与关键交互已稳定到足以支撑任务规划。本轮未发现阻塞 approval step 的设计空洞。

## 维度评分

| 维度 | 评分 | 评语 |
|------|------|------|
| `D1` 需求覆盖与追溯 | 9/10 | FR-301~FR-307、NFR-301/302/304 与关键模块、流程、契约之间的映射清楚，未见无法回指规格的关键新增能力。 |
| `D2` 架构一致性 | 9/10 | `memory` 编排层与现有 `KnowledgeStore` / `ExperienceIndex` / `SessionManager` / `SkillExecutor` 的边界清晰，逻辑图与时序图一致。 |
| `D3` 决策质量与 trade-offs | 9/10 | A/B/C 三个方案的取舍、ADR、后果与可逆性都可冷读，不依赖 reviewer 脑补。 |
| `D4` 约束与 NFR 适配 | 8/10 | workspace-first、用户确认门禁、失败降级、兼容现有链路与推荐性能门槛都已进入设计，而非只在概述中被提到。 |
| `D5` 接口与任务规划准备度 | 8/10 | 候选批次、候选草稿、confirmation、提取输入、推荐输入与 canonical surface 已闭合，`hf-tasks` 不再需要重新发明关键接口。 |
| `D6` 测试准备度与隐藏假设 | 8/10 | 最薄验证路径、建议测试层次、失败模式与高风险假设都已显式化，足以支撑后续定向测试设计。 |

## 发现项

- [minor][LLM-FIXABLE][D4] 若作者希望进一步强化“文件即契约”的一致性，可在后续设计润色中把 `CandidateBatch` 与 `ConfirmationRecord` 示例也补上显式 `schema_version` 字段，和 `CandidateDraft` 保持完全同构的版本语义表达；该问题不阻塞当前设计进入 approval step。

## 薄弱或缺失的设计点

- `experience_summary` 第一版落为扩展后的 `ExperienceRecord` 是合理收敛，但实现阶段仍应保持推荐与回溯只消费正式发布态，避免未来把候选态与正式态再次混淆。
- CLI-first canonical surface 已收口；若后续补充宿主对话面的 UX 细节，应继续坚持复用同一套 schema 与 service，不要引入第二套私有 contract。

## 下一步

- `通过`：`设计真人确认`

## 记录位置

- `docs/reviews/design-review-F003-garage-memory-auto-extraction-r2.md`

## 交接说明

- 本轮评审确认：上一轮 3 个 `important` finding 已完成定向回修。
- 当前剩余问题仅为不阻塞 approval step 的 minor 文档完善项，不需要回退到 `hf-design`。
- 由于当前 workflow 为 `interactive`，下一步应进入 `设计真人确认`，由父会话继续主链推进。
