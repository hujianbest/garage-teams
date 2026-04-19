# Spec Review — F006 Garage Recall & Knowledge Graph

- 评审范围: `docs/features/F006-garage-recall-and-knowledge-graph.md`（草稿，338 行）
- Review skill: `hf-spec-review`
- 评审者: cursor cloud agent (auto mode, reviewer subagent，由 `hf-specify` 父会话派发)
- 日期: 2026-04-19
- Workflow Profile / Mode / Isolation: `standard` / `auto` / `in-place`
- Branch: `cursor/f006-recommend-and-link-177b`
- 上游证据基线: `task-progress.md`、`RELEASE_NOTES.md`（F003/F004/F005 entries）、`AGENTS.md`、`docs/soul/manifesto.md`、`docs/soul/growth-strategy.md`、`src/garage_os/cli.py`、`src/garage_os/memory/recommendation_service.py`、`src/garage_os/knowledge/knowledge_store.py`、`src/garage_os/knowledge/experience_index.py`、`src/garage_os/types/__init__.py`、F005 spec/design/closeout

## 1. Precheck

| 检查项 | 结果 |
|--------|------|
| 存在稳定可定位 spec draft | ✓ `docs/features/F006-garage-recall-and-knowledge-graph.md` 已落盘，结构完整 |
| route / stage / profile 已明确 | ✓ Stage=`hf-specify`，Pending=`hf-spec-review`，Profile=`standard`，Mode=`auto`，Isolation=`in-place` |
| 上游证据一致 | ✓ F003/F004/F005 闭环；`RecommendationService` / `KnowledgeStore` / `ExperienceIndex` 等模块皆在 main 上 |
| 结构契约 | ✓ 沿用 F003/F004/F005 骨架（背景 → 目标/SC/非目标 → 角色/场景 → 范围 → deferred → FR → NFR → 接口 → 约束 → 假设 → 开放问题 → 术语） |

Precheck 通过；进入正式 rubric。

## 2. 证据校验（重点逐条核对 spec 的代码引用）

| 校验项 | spec 主张 | 源码事实 | 一致？ |
|--------|----------|----------|------|
| `RecommendationService.recommend(context)` 接受 `skill_name=""`、仅靠 tags / domain 也能产生命中 | ASM-604、FR-601、§ 1 | `recommendation_service.py:64-95` 中 `skill_name = (context.get("skill_name") or "").lower()`；line 77/80/84/87 均以 `if skill_name and ...` / `if domain and ...` 守卫；line 91-94 `for tag in tags: if tag in entry_tags: score += 0.6, reasons.append(f"tag:{tag}")` 仅基于 tags 即可加分。仅有 tags 时 score>0 路径成立。 | ✓ |
| `RecommendationService.recommend()` 同时召回 knowledge + experience | § 2.2 SC-1（"CLI 返回 top-N 个相关 entry（knowledge + experience）"）；FR-601 #3-4；FR-602；§ 8（"复用 ... + `ExperienceIndex.list_records()`"）；OQ-601（"本 cycle 默认混合召回"） | `recommendation_service.py:48-56` 构造函数接收 `experience_index` 但 `recommend()` 全函数体（line 62-135）**只**遍历 `self._knowledge_store.list_entries()`（line 69），**从未**触碰 `self._experience_index`。Line 51 的 `experience_index` 在 `recommend()` 中是 dead reference。 | ✗ **不一致** |
| `KnowledgeStore.update()` 始终 `version+=1` | FR-603 验收 #2、CON-603、OQ-602 | `knowledge_store.py:194` `entry.version += 1` 在 `update()` 入口无条件执行 | ✓ |
| `KnowledgeStore.update()` round-trip 保留 `related_decisions` | FR-603 验收 #1 | `_entry_to_front_matter()`（line 410-411）显式写 `related_decisions`/`related_tasks`；`_front_matter_to_entry()`（line 465-466）以 `fm.get("related_decisions", [])` / `fm.get("related_tasks", [])` 兜底默认空 list；`_DATACLASS_FRONT_MATTER_KEYS`（line 366-381）含两字段。append→update→retrieve 链路保留。 | ✓ |
| `_front_matter_to_entry` 对缺失 `related_decisions`/`related_tasks` 默认 `[]` | ASM-603 | `knowledge_store.py:465-466` `fm.get("related_decisions", [])` / `fm.get("related_tasks", [])` 兜底为空 list | ✓（但 spec 引用行号 "knowledge_store.py:475-476" 与实际 line 465-466 偏差 10 行，见 F-2） |
| `KnowledgeEntry.related_decisions: List[str]` / `related_tasks: List[str]` 字段存在 | FR-603/FR-605 全部依赖 | `types/__init__.py:108-109` 两字段均为 `field(default_factory=list)` 的 `List[str]` | ✓ |
| FR-604/FR-605 在 3 个 type 目录跨目录查 ID 实现路径合理 | FR-604/FR-605 | `knowledge_store.py:228-237` `list_entries(knowledge_type=None)` 返回全部条目；`KnowledgeStore.TYPE_DIRECTORIES`（line 30-34）含 3 个 type 目录映射；CLI 可在 list_entries 上做 `entry.id == X` 过滤并按 `entry.type` 区分。实现路径平凡。 | ✓ |
| `ExperienceIndex.list_records()` 存在 | § 8 | `experience_index.py:160-181` `list_records()` 实现存在 | ✓ |
| F005 cli: 命名空间约定可延伸 | FR-606、CON-604 | `cli.py:61-63` 已有 `CLI_SOURCE_KNOWLEDGE_ADD/EDIT/EXPERIENCE_ADD`，新增 `CLI_SOURCE_KNOWLEDGE_LINK = "cli:knowledge-link"` 与既有命名空间相容 | ✓ |
| `recommendation_enabled` flag 不影响 `garage recommend` | § 8 | `cli.py:282` `recommendation_enabled` flag 仅守卫 `garage run` 内 RecommendationService 的实例化；`garage recommend` 是新顶级命令，不会受该 flag 影响（spec 主张成立，前提是新命令不读 flag） | ✓ |

## 3. Rubric 评审

### 3.1 Group Q

| ID | 检查 | 结论 | 锚点 / 备注 |
|----|------|-----|-----------|
| Q1 Correct | ⚠️ | 行号引用错位（spec 行 310 引 `knowledge_store.py:475-476`，实际为 line 465-466）— 见 F-2 |
| Q2 Unambiguous | ✓ | 无未量化模糊词；NFR-603 给 `<1.5s` 阈值 |
| Q3 Complete | ⚠️ | 边界 case 大体覆盖（empty .garage、missing entry、ambiguous type、link target 不存在、重复 link 幂等）；但 mixed knowledge+experience 召回的实现路径 / scoring 模型缺 — 见 F-1 |
| Q4 Consistent | ✗ | SC-1/FR-601/FR-602/§ 8 与 CON-602/CON-605 + 现有 `recommend()` 源码事实直接矛盾 — 见 F-1 |
| Q5 Ranked | ✓ | 7 个 FR 显式 Must/Should；6 个 NFR 同 |
| Q6 Verifiable | ✓ | 每条 FR/NFR 含 Given/When/Then；FR-601 验收 6 条具体到 stdout 子串、exit code、context 字段 |
| Q7 Modifiable | ✓ | 单点权威定义清晰；常量在 § 4.1 / NFR-604 收敛在 cli.py 顶层 |
| Q8 Traceable | ✓ | 每条需求带 Source（§/SC/F005 ADR-503/F004 § 11.5 等） |

### 3.2 Group A

| ID | 检查 | 结论 | 备注 |
|----|------|-----|------|
| A1 模糊词 | ✓ | "≤100 条 entry < 1.5s" 显式量化 |
| A2 复合需求 | ✓ | FR-601~607 各只承担一个能力（recommend / 兜底 / link 写入 / link 多匹配 / graph / 来源标记 / help） |
| A3 设计泄漏 | ⚠️ | NFR-604 / NFR-602 / FR-606 写到了模块常量名 `CLI_SOURCE_KNOWLEDGE_LINK = "cli:knowledge-link"`、`grep "Linked '" src/garage_os/cli.py`。F005 spec review r2 已对同模式判定为"可保留 stable stdout marker，不属 NFR-502 的依赖面违规"；F006 沿用 F005 模式可接受，但 NFR-602 验收的 "F005 cycle 末态 `git diff main..HEAD -- pyproject.toml` 为空" 是 F005 历史快照，应改为 F006 自身 cycle 度量 — 见 F-3 |
| A4 无主体的被动表达 | ✓ | "When 用户调用..., the system shall ..." 模式贯穿 |
| A5 占位/待定值 | ✓ | 无 TBD / 待确认 |
| A6 缺少负路径 | ✓ | FR-601 验收覆盖 0 entry / 不命中 / no .garage；FR-603 覆盖 missing from / 重复 link；FR-604 覆盖 ambiguous；FR-605 覆盖 missing id / ambiguous |

### 3.3 Group C

| ID | 检查 | 结论 | 备注 |
|----|------|-----|------|
| C1 Requirement contract | ✓ | FR-601~607、NFR-601~605 均有 ID/Statement/Acceptance/Priority/Source |
| C2 Scope closure | ⚠️ | § 4.1 / § 4.2 列出包含/不包含；但 mixed knowledge+experience 召回属"包含但实现路径未指明"，scope 边界半开 — 见 F-1 |
| C3 Open-question closure | ✓ | OQ-601~607 全部标"非阻塞"且当前判断写明；OQ-604 性能问题留 design 层独立立项可接受 |
| C4 Template alignment | ✓ | F003/F004/F005 同骨架；EARS+BDD 沿用 |
| C5 Deferral handling | ✓ | § 5 deferred backlog 列了 unlink / 多跳 / experience link / 跨类型 link / 图导出 / `--format json` / `--include experience-only` / embedding / 自动建议链接，每条带延后理由 |
| C6 Goal and success criteria | ⚠️ | SC-1 主张"knowledge + experience"，但与源码事实冲突（见 F-1）— SC-1 的"experience"半句若不可达，会让 success criteria 变得不可判断 |
| C7 Assumption visibility | ✓ | ASM-601~605 均显式写出，含失效影响；ASM-604 还做了源码引用（虽然行号偏差，但语义对） |

### 3.4 Group G

| ID | 检查 | 结论 | 备注 |
|----|------|-----|------|
| G1 Oversized FR | ✓ | 7 个 FR 单粒度可控；FR-604 单独承担 ambiguous-type 一个边界，避免 FR-603 扩张 |
| G2 Mixed release boundary | ✓ | § 5 deferred 与 § 4 当前轮明确分隔；未来 unlink / 多跳 / 跨类型不混入 FR |
| G3 Repairable scope | ✓ | F-1 / F-2 / F-3 / F-4 等 finding 均可定向回修，1-2 轮可收敛，无需推倒重来 |

## 4. 发现项

- **[important][USER-INPUT][Q4/C2/C6]** **F-1**：mixed knowledge+experience 召回与源码事实直接冲突。
  - SC-1（行 44）："CLI 返回 top-N 个相关 entry（**knowledge + experience**）"
  - FR-601 #3（行 164）："实例化 `RecommendationService(KnowledgeStore, ExperienceIndex)`"
  - FR-602（行 181）：错误文案 `"No matching knowledge or experience for query: '<query>'"`
  - § 8（行 292）："复用既有 ... + `ExperienceIndex.list_records()`"
  - OQ-601（行 318）："本 cycle 默认混合召回"
  - 源码事实：`recommendation_service.py:62-135` 中 `recommend()` 函数体只遍历 `self._knowledge_store.list_entries()`（line 69），**从未**触碰 `self._experience_index`。Line 51 的 `experience_index` 在 `recommend()` 中是 dead reference。
  - CON-605（行 303）："不改变 F003 `RecommendationService` 已有 ranking 算法或 score 权重"。
  - 矛盾：spec 明确要 experience 也被召回（SC-1 + OQ-601），但 (a) 现有 `recommend()` 不召回 experience，且 (b) CON-605 禁止改 `recommend()`。FR-601 step 4 仅 `service.recommend(context)` 一次调用，不存在第二次对 ExperienceIndex 的扫描；spec § 8 提到 `ExperienceIndex.list_records()` 也未在任何 FR 中具体编排进 CLI 流程。
  - 解决路径有三：
    1. **缩小 wedge**：从 SC-1 / FR-602 文案 / § 8 / OQ-601 中移除 "experience"，本 cycle 仅做 knowledge 召回，把 experience 召回归入 deferred backlog。
    2. **新增 FR**（仍在 CON-605 内）：在 FR-601 中显式追加 step "5. 扫描 `ExperienceIndex.list_records()` 应用等价的启发式 scoring（含 task_type / domain / problem_domain / key_patterns 的 token 命中规则）并与 knowledge results 合并按 score 降序"。但该 step 要为 ExperienceRecord 引入一套**新的** scoring 业务规则（experience 字段集与 knowledge 不同：无 `tags` / `topic`，有 `task_type` / `domain` / `problem_domain` / `key_patterns` / `lessons_learned`），属新增业务事实。
    3. **放宽 CON-605**：允许扩展 `recommend()` 接收 experience 维度并在内部融合，但需说明对 `garage run` 路径行为零影响如何兜底。
  - 选择哪一条 = wedge / scope / 新业务规则的判断，reviewer 不可代替用户裁决。
  - 修复归属：USER-INPUT（路径 1 是缩小 scope，需用户同意；路径 2 引入新 scoring 业务事实；路径 3 放宽既有 constraint）。

- **[minor][LLM-FIXABLE][A3]** **F-3**：NFR-602 验收（行 267）写"F005 cycle 末态 `git diff main..HEAD -- pyproject.toml` 为空"——把 F006 cycle 的 acceptance 绑定在 F005 历史快照上。应改为"F006 cycle 内 `pyproject.toml` 不新增 runtime dependency"或等价的本 cycle 度量。

- **[minor][LLM-FIXABLE][Q1]** **F-2**：ASM-603（行 310）注释引用 `knowledge_store.py:475-476` 作为兜底默认 `[]` 的位置，实际为 `knowledge_store.py:465-466`（行号偏差 10 行）。语义对、影响小，仅需更新行号。

- **[minor][LLM-FIXABLE][C2]** **F-4**：FR-602（行 177-185）与 FR-601 验收 #6（行 174）在"零结果"语义上有重叠。建议在 FR-602 一句话指明边界（"FR-602 覆盖**有 entry 但 query 不命中**的情形；零 entry 情形由 FR-601 #6 覆盖"），避免两条 FR 在同一行为上互相 reference。

- **[minor][LLM-FIXABLE][Q3]** **F-5**：FR-607（行 247）只要求 `garage knowledge --help` stdout **含** `link` / `graph`，未声明 F005 已有的 `add` / `edit` / `show` / `delete` / `search` / `list` 必须**继续保持出现**。NFR-601 零回归保护可隐式覆盖（F005 测试集会捕获），但 FR-607 平行写一句"F005 已有 7 个子命令仍存在"会更显式。

## 5. 缺失或薄弱项

- mixed knowledge+experience 召回的实现路径（F-1）若选路径 2，则缺一套 ExperienceRecord scoring 启发式定义；当前 spec 既无该定义、也无显式指向 design 阶段去补。需先在 spec 层裁决路径。
- 其他维度无关键缺失。FR-601~607 / NFR-601~605 在 F-1 解决后即可作为 design 输入。

## 6. 结论

**需修改**

判断依据：
- 1 项 important USER-INPUT finding（F-1：mixed recall 与源码事实直接矛盾，需用户在缩小 scope / 新增 experience scoring 规则 / 放宽 CON-605 三条路径中裁决）
- 4 项 minor LLM-FIXABLE finding（F-2 行号、F-3 NFR-602 跨 cycle 度量、F-4 FR-601/FR-602 边界澄清、F-5 FR-607 显式列出 F005 子命令）
- 范围 / 范围外 / 假设 / 开放问题闭合度大体到位；修订路径明确、收敛风险低
- 无 critical finding；无 route / stage / 证据冲突
- 满足 rubric "有用但不完整，findings 可 1-2 轮定向修订" → `需修改`

## 7. 下一步

- **`hf-specify`**：父会话回流到 `hf-specify`，向用户呈现 F-1 的 USER-INPUT 选择题（缩小 scope / 新增 experience scoring / 放宽 CON-605），用户裁决后由 `hf-specify` 直接消化 F-2~F-5 四项 LLM-FIXABLE，重新提交 r2 评审。
- 不需要 reroute via router。

## 8. 交接说明

- `hf-specify`：用于消化全部 5 项 finding；F-1 需要先收 USER-INPUT，F-2~F-5 LLM 直接修。修订完成后由 `hf-spec-review` r2 复审。
- 父会话向真人摘要时只说：**"实现路径与代码事实在一处冲突需要您裁决（experience 召回是否纳入本轮），其他都是局部 wording 问题"**；不要把 rubric 表格 / JSON 原样贴给用户。
- 父会话不代替用户在 USER-INPUT 上决定，也不顺手开始 design。

## 9. 结构化返回

```json
{
  "conclusion": "需修改",
  "next_action_or_recommended_skill": "hf-specify",
  "record_path": "/workspace/docs/reviews/spec-review-F006-recall-and-knowledge-graph.md",
  "key_findings": [
    "[important][USER-INPUT][Q4/C2/C6] F-1 SC-1 / FR-601 / FR-602 / § 8 / OQ-601 主张 mixed knowledge+experience 召回，但 recommendation_service.py:62-135 中 recommend() 仅遍历 KnowledgeStore.list_entries()，从未触碰 self._experience_index；CON-605 又禁止改 recommend() 算法。需在缩小 scope / 新增 experience scoring 规则 / 放宽 CON-605 三条路径中裁决。",
    "[minor][LLM-FIXABLE][A3] F-3 NFR-602 验收把 F006 cycle 的度量绑定到 'F005 cycle 末态 git diff main..HEAD'，应改为 F006 自身 cycle 度量。",
    "[minor][LLM-FIXABLE][Q1] F-2 ASM-603 引用 knowledge_store.py:475-476，实际行号为 465-466。",
    "[minor][LLM-FIXABLE][C2] F-4 FR-602 与 FR-601 验收 #6 在零结果语义上重叠，需澄清边界。",
    "[minor][LLM-FIXABLE][Q3] F-5 FR-607 未显式声明 F005 已有 6 个 knowledge 子命令在 help 中继续保留。"
  ],
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "finding_breakdown": [
    {
      "id": "F-1",
      "severity": "important",
      "classification": "USER-INPUT",
      "rule_id": "Q4",
      "summary": "mixed knowledge+experience 召回承诺与 recommend() 源码事实及 CON-605 直接矛盾，需用户在 3 条解决路径中裁决"
    },
    {
      "id": "F-2",
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "Q1",
      "summary": "ASM-603 引用 knowledge_store.py:475-476，实际是 465-466"
    },
    {
      "id": "F-3",
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "A3",
      "summary": "NFR-602 验收绑定 F005 cycle 末态 git diff，应改为 F006 cycle 自身度量"
    },
    {
      "id": "F-4",
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "C2",
      "summary": "FR-602 与 FR-601 验收 #6 在零结果语义上重叠，应澄清边界"
    },
    {
      "id": "F-5",
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "Q3",
      "summary": "FR-607 未显式声明 F005 已有 6 个 knowledge 子命令在 --help 中继续保留"
    }
  ]
}
```
