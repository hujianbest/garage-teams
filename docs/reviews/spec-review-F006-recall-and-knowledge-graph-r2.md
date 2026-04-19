# Spec Review — F006 Garage Recall & Knowledge Graph (Round 2)

- 评审范围: `docs/features/F006-garage-recall-and-knowledge-graph.md`（草稿 r2，359 行）
- Review skill: `hf-spec-review`
- 评审者: cursor cloud agent (auto mode, reviewer subagent，由 `hf-specify` 父会话派发)
- 日期: 2026-04-19
- Workflow Profile / Mode / Isolation: `standard` / `auto` / `in-place`
- Branch: `cursor/f005-knowledge-add-cli-177b`
- 评审范围：仅对 round 1（`docs/reviews/spec-review-F006-recall-and-knowledge-graph.md`）5 条 finding 的关闭做 delta 校验 + 本轮新增章节（FR-602 / FR-603 / FR-608）的 Q/A/C/G 抽查；未触动的章节继承 round 1 评分。
- 上游证据基线: round 1 record；现在的 spec；`src/garage_os/cli.py`、`src/garage_os/memory/recommendation_service.py`、`src/garage_os/knowledge/knowledge_store.py`、`src/garage_os/knowledge/experience_index.py`、`src/garage_os/types/__init__.py`

## 1. Precheck

| 检查项 | 结果 |
|--------|------|
| 存在稳定可定位 spec draft | ✓ 文件已落盘，结构完整 |
| route / stage / profile 已明确 | ✓ Stage=`hf-specify` r2，Pending=`hf-spec-review` r2 |
| 上游证据一致 | ✓ 源码事实未变，round 1 锚点仍可复算 |

Precheck 通过。

## 2. Round 1 Findings 闭合校验

| ID | round 1 摘要 | r2 闭合证据 | 关闭？ |
|----|------|------|------|
| **F-1** [important][USER-INPUT][Q4/C2/C6] mixed knowledge+experience 召回与 `recommend()` 源码事实 + CON-605 直接矛盾 | 用户裁决路径 2（CLI-internal experience scorer，不动 `RecommendationService`）。spec 改动：(a) FR-601 step 3 显式说明 "`RecommendationService.recommend` 当前实现仅遍历 `KnowledgeStore`... 本 FR 不修改该实现，与 CON-605 兼容"（行 164）；(b) **新增 FR-602**（行 176-196）"experience 半边召回必须由 `cli.py` 内新增**纯本地** helper `_recommend_experience(records, context)` 完成"，给出 6 条 scoring 启发式（domain/problem_domain → +0.8；task_type/tech_stack/key_patterns → +0.6；lessons_learned 文本 → +0.4），accept criteria 含 "**不**修改 `recommendation_service.py` 任何代码（CON-605）" 与 "**不**改变 `RecommendationContextBuilder.build()` 既有签名（CON-602）"；(c) §8 "外部接口与依赖" 隐含的"复用 `ExperienceIndex.list_records()`"被 FR-602 step 1 显式落实；(d) OQ-601 仍标注 "本 cycle 默认混合召回"，与 SC-1 一致。源码侧校验：`experience_index.py:160-181` `list_records()` 存在；`ExperienceRecord` 字段（`task_type` / `domain` / `problem_domain` / `tech_stack` / `key_patterns` / `lessons_learned`）在 `types/__init__.py:118-141` 全部可读。FR-602 不需要任何 `RecommendationService` / `KnowledgeStore` / `ExperienceIndex` 公开 API 变更。CON-602/603/605 仍互不冲突。 | ✓ |
| **F-2** [minor][LLM-FIXABLE][Q1] ASM-603 引用 `knowledge_store.py:475-476`，实际是 465-466 | spec 行 331 现写 "见 `knowledge_store.py` `_front_matter_to_entry` 中 `related_decisions=fm.get("related_decisions", [])` 与 `related_tasks=fm.get("related_tasks", [])` 两行" — 改为定位**符号** + 字面字符串而非具体行号，对未来重构稳健。`knowledge_store.py:465-466` 仍含此两行，定位方式 valid。 | ✓ |
| **F-3** [minor][LLM-FIXABLE][A3] NFR-602 验收绑定 F005 cycle 末态 git diff | NFR-602 现写 "`pyproject.toml` 在本 F006 cycle 不新增 runtime dependency；本 cycle 完成时 `git diff main..HEAD -- pyproject.toml`（HEAD = F006 终态 commit）为空 diff"（行 288） — HEAD 显式注解为"F006 终态 commit"，度量回归到本 cycle。 | ✓ |
| **F-4** [minor][LLM-FIXABLE][C2] FR-602 与 FR-601 验收 #6 在零结果语义上重叠 | (a) round 1 的 FR-602 文本（"零召回兜底"）已被升格为**新独立 FR-603**（行 198-206），统一处理 knowledge+experience 合并后的零结果出口；(b) FR-603 显式声明 "本 FR 是 FR-601/602 的零结果共同归并出口... 不重复在 FR-601/602 的 happy path 验收里同时声明"；(c) FR-601 验收 #6（行 174）现仅覆盖 `ERR_NO_GARAGE`（未 init），不再与 FR-603 零结果文案重叠；(d) FR-602 验收第 3 条 "experience 全部 score=0... 与 FR-603 联动给零结果文案"（行 194）显式 cross-link 而非自说自话。两条 FR 边界清晰。 | ✓ |
| **F-5** [minor][LLM-FIXABLE][Q3] FR-607 未声明 F005 已有 6 个 knowledge 子命令在 help 中继续保留 | 原 FR-607 重新编号为 **FR-608**（行 262-272）。需求陈述第 2 条显式写 "`garage knowledge --help` stdout 含 `link` 与 `graph`（F006 新增），且**继续**含 `search` / `list` / `add` / `edit` / `show` / `delete` 这 6 个 F005 既有子命令（保护 NFR-601 零回归）"；验收明示 "`knowledge --help` 断言显式覆盖 6 个 F005 既有名 + 2 个 F006 新增名共 8 个"。F005 子命令清单与源码 `cli.py` 一致（add/edit/show/delete/search/list）。 | ✓ |

5/5 round 1 finding 已关闭。

## 3. 本轮 Delta 章节抽查（仅对 r2 新增/重写部分）

### 3.1 FR-602（新增）

| 维度 | 结论 | 备注 |
|------|------|------|
| Q1 Correct | ✓ | 锚点 `recommendation_service.py:69` 准确（实际行号 69，遍历 `self._knowledge_store.list_entries()`）；`ExperienceRecord` 字段引用在 `types/__init__.py:118-141` 可核验 |
| Q2 Unambiguous | ✓ | 6 条 scoring 规则给具体数值（+0.8 / +0.6 / +0.4），无模糊词 |
| Q3 Complete | ✓ | 覆盖 happy path（含 mixed sort）+ score=0 全空 + 不可改既有模块两条边界 |
| Q4 Consistent | ✓ | 不与 CON-602/603/605 冲突；step 4 与 FR-601 step 4 cross-link 一致；entry shape 含 `entry_type: "experience"` 与 FR-601 stdout 块（"[EXPERIENCE]"）对齐 |
| Q5 Ranked | ✓ | Must |
| Q6 Verifiable | ✓ | 3 条 BDD 验收 + 2 条 hard constraint |
| Q7 Modifiable | ✓ | scoring 数值集中在 FR-602 一处 |
| Q8 Traceable | ✓ | Source: § 1 摩擦 1 / § 2.1 / CON-605 |
| A2 复合需求 | ✓ | 单一职责（仅 experience scorer） |
| A3 设计泄漏 | ✓ | 提到 `_recommend_experience` helper 名是必要的"延伸 F005 cli: 命名空间约定"前置词；不是泄漏 |
| C1 Contract | ✓ | ID/Statement/Acceptance/Priority/Source 齐 |
| GS1 Oversized | ✓ | scoring 规则 6 条仍是单 FR 可控范围；未来若加 weighting 调整会增量 |

### 3.2 FR-603（新增）

| 维度 | 结论 | 备注 |
|------|------|------|
| Q3/C2 边界闭合 | ✓ | 明示 "FR-601/602 零结果共同归并出口，不重复在 happy path 验收里声明"，把 F-4 重叠彻底切断 |
| Q6 Verifiable | ✓ | 2 条 Given/When/Then；显式列 `\n` 与"仅一行 + 换行"，无歧义 |
| A6 负路径 | ✓ | 覆盖"全空" + "有 entry 但 query 不命中" 两种零结果触因 |

### 3.3 FR-608（重写自 FR-607）

| 维度 | 结论 | 备注 |
|------|------|------|
| Q3 Complete | ✓ | F005 6 个既有子命令显式列出；3 个新子命令的 `--help` 参数清单显式列出 |
| C1 Contract | ✓ | 验收量化为 "8 个名" 与 "5 条断言对应 5 个 test func" |

### 3.4 跨条目编号一致性

- 原 FR-607 → FR-608 重新编号，spec 内部所有引用（§ 2.2 SC 列表行 49、scenarios、CON-606）未出现 "FR-607" 残留；GitHub 检索 spec 文档 `FR-607` 仅匹配新文本上下文（如 "F005 FR-510"、"FR-608" 自身）。
- 原文档目录 ToC（§6 章节）未单列 ToC 条目，无需同步。
- ✓ 无 ID 漂移导致的悬挂引用。

### 3.5 触动文本对其他章节的回流影响

- §2.2 SC-1（"knowledge + experience"）仍成立，因 r2 新增了实际承接 experience 半边的 FR-602。
- §8 "外部接口与依赖" 内 `ExperienceIndex.list_records()` 复用承诺被 FR-602 step 1 兑现。
- CON-605 仍完整；FR-602 是**绕过**而非**修改** `RecommendationService`。
- §11 OQ-601 与 FR-602 不冲突（"默认混合"在 r2 实际可达）。
- ✓ 无回流问题。

## 4. 发现项

无（5 项 round 1 finding 全部关闭，r2 新增章节抽查全 ✓）。

## 5. 缺失或薄弱项

- **薄弱（非阻塞）**：FR-602 step 2 的 6 条 scoring 规则与 `RecommendationService.recommend` 的 knowledge scoring 规则在数值上不完全等价（experience 无 `skill_name` 命中通道、无 fallback `skill_name_only`），混合排序时可能出现"experience 永远排在 knowledge 后" 或反之的小偏差。这属于 **design 层 ranking calibration**，spec 已在 OQ 类语义里被 OQ-604 / 默认混合召回收敛；不阻塞批准。建议 design 阶段做一次 5-10 条混合数据的 sanity check。

## 6. 结论

**通过**

判断依据：
- round 1 五项 finding 全部关闭，关键 USER-INPUT 已由用户裁决并在 FR-602 中以代码一致的方式落地（不动 `RecommendationService`，CLI 层独立 scorer）
- r2 新增章节通过 Q/A/C/G 抽查
- 范围 / scope 边界 / 约束 / 假设 / 开放问题在 r2 后整体闭合
- 无 critical / important finding；仅 1 条非阻塞薄弱项（ranking calibration），属 design 层正常工作
- 满足 rubric "范围清晰、核心需求可验收、无阻塞 USER-INPUT、足以成为设计稳定输入" → `通过`

## 7. 下一步

- **`规格真人确认`**：父会话向真人摘要 r2 关闭情况并请求 approval；通过后进入 `hf-design`。
- 不需要 reroute via router。

## 8. 交接说明

- `规格真人确认`：仅当本结论为 `通过`；interactive 模式下父会话等待真人对 r2 spec 做最终签字；auto 模式下父会话写 approval record。
- 父会话向真人的摘要建议：**"r2 已闭合 round 1 全部 5 项 finding；其中关键的 mixed recall 矛盾通过新增 FR-602（CLI 层独立 experience scorer，不动 RecommendationService）解决，与 CON-605 完全兼容；可进入真人确认。"** 不要把 rubric / JSON 原样贴给用户。
- 父会话不顺手开始 `hf-design`，approval step 后再转。

## 9. 结构化返回

```json
{
  "conclusion": "通过",
  "next_action_or_recommended_skill": "规格真人确认",
  "record_path": "/workspace/docs/reviews/spec-review-F006-recall-and-knowledge-graph-r2.md",
  "key_findings": [
    "F-1 已闭合：新增 FR-602 在 cli.py 层用纯本地 _recommend_experience() 扫描 ExperienceIndex.list_records()，与 CON-605/CON-602 完全兼容，源码事实一致。",
    "F-2 已闭合：ASM-603 改为按符号定位 _front_matter_to_entry 中两行字面字符串，避开行号漂移。",
    "F-3 已闭合：NFR-602 度量改回 F006 cycle 自身（HEAD = F006 终态 commit）。",
    "F-4 已闭合：零结果归口 FR-603 独立承担，FR-601 验收 #6 收窄为 ERR_NO_GARAGE，FR-602 验收 cross-link FR-603。",
    "F-5 已闭合：FR-608 显式列出 F005 既有 6 个 knowledge 子命令必须继续在 --help 出现，验收量化为 8 个名。"
  ],
  "needs_human_confirmation": true,
  "reroute_via_router": false,
  "finding_breakdown": []
}
```
