# Spec Review — F005 Garage Knowledge Authoring CLI (Round 2)

- 评审范围: `docs/features/F005-garage-knowledge-authoring-cli.md`（草稿，348 行）
- Review skill: `hf-spec-review`（round 2，delta-only depth）
- 评审者: cursor cloud agent (auto mode, reviewer subagent，由 `hf-specify` 父会话派发)
- 日期: 2026-04-19
- Workflow Profile / Mode / Isolation: `standard` / `auto` / `in-place`
- Branch: `cursor/f005-knowledge-add-cli-177b`
- 上游证据基线（沿用 r1）: `task-progress.md` / `RELEASE_NOTES.md` / `AGENTS.md` / `docs/soul/*` / `src/garage_os/cli.py` / `src/garage_os/knowledge/{knowledge_store,experience_index}.py` / `src/garage_os/types/__init__.py`
- 上一轮记录: `/workspace/docs/reviews/spec-review-F005-knowledge-authoring-cli.md`（结论 = `需修改`，5 项 LLM-FIXABLE finding）

## 1. Precheck

| 检查项 | 结果 |
|--------|------|
| 存在稳定可定位 spec draft | ✓ F005 草稿仍在原路径，结构完整 |
| route / stage / profile 已明确 | ✓ Stage=`hf-specify` 回流，Pending=`hf-spec-review`（r2），无 route/stage 冲突 |
| 上游证据一致 | ✓ 源码事实（`ExperienceIndex.INDEX_PATH = "knowledge/.metadata/index.json"`、`ExperienceIndex.delete()` 已存在、`KnowledgeStore.update()` 仍 `version+=1`）与 spec 引用一致 |
| 结构契约 | ✓ 沿用 F003/F004 骨架不变 |

Precheck 通过；进入 r2 delta-only rubric。

## 2. R1 Findings 闭合验证

| # | R1 Finding | 关闭证据 | 状态 |
|---|------------|----------|------|
| 1 | `[important][LLM-FIXABLE][Q4]` FR-501 验收 #4 与 FR-508 对 ID 哈希输入定义直接矛盾 | FR-501 验收第 4 条（行 159）现写 "Given 用户**未**传 `--id`，Then CLI 走 **FR-508** 定义的 ID 生成算法（本 FR 不重复算法定义；冲突处理由 FR-508 决定）"。删除了原来的 "保证可复算" 措辞与算法重写，改为单点引用 FR-508；FR-508 (行 232-243) 维持时间敏感算法。两处不再相互矛盾，单一权威定义在 FR-508。 | ✓ 已关闭 |
| 2 | `[important][LLM-FIXABLE][Q1]` FR-507 验收 #4 索引路径与 `ExperienceIndex.INDEX_PATH` 实际路径不一致 | FR-507 已拆为 FR-507a/FR-507b；FR-507b 需求陈述（行 226）和验收 #2（行 229）现写 `.garage/knowledge/.metadata/index.json`，与 `src/garage_os/knowledge/experience_index.py:23` `INDEX_PATH = "knowledge/.metadata/index.json"` 一致。原来错写的 `.garage/experience/records/.metadata/index.json` 在 spec 中已不复存在（grep 验证）。 | ✓ 已关闭 |
| 3 | `[minor][LLM-FIXABLE][A3]` NFR-502 验收 #2 把 `grep -r "import " src/garage_os/cli.py` 写进规格层 | NFR-502 验收（行 283-285）现写 "`pyproject.toml` 在本 cycle 不新增 runtime dependency" + "F005 引入的所有新源码模块（CLI 子命令处理器及其直接被调用的 helper）的 `import` 闭包仅包含 Python stdlib + `garage_os.*` 内部模块；评审时按依赖面校验（不绑定具体文件路径）"。已抽象为依赖面约束，不再绑死具体实现路径。 | ✓ 已关闭 |
| 4 | `[minor][LLM-FIXABLE][A2/G1]` FR-507 打包 `experience show + delete` | FR-507 已拆为 **FR-507a `experience show`**（行 213-220）和 **FR-507b `experience delete`**（行 222-230），各自独立优先级、来源、需求陈述、验收，traceability gate 阶段可逐项追溯。 | ✓ 已关闭 |
| 5 | `[minor][LLM-FIXABLE][A3]` § 4.1 与 FR-501 重复 ID 生成规则 | § 4.1 表格（行 118）现写 "未传 `--id` 时由 CLI 生成稳定可读 ID。具体算法、可复算性边界与冲突处理见 **FR-508**（权威定义）"；FR-501 验收 #4（行 159）也仅引用 FR-508。三处（§ 4.1 / FR-501 / FR-508）已收敛为单点权威定义 + 两处引用，Q7 散落问题消除。 | ✓ 已关闭 |

## 3. Delta-only Rubric Pass

针对修订涉及的 § 4.1 / FR-501 / FR-507a / FR-507b / FR-508 / NFR-502 五处区域做局部回看；其余未触及部分沿用 r1 结论。

### 3.1 Group Q（受影响维度）

| ID | 检查 | r2 结论 | 备注 |
|----|------|--------|------|
| Q1 Correct | ✓ | FR-507b 索引路径与源码 `INDEX_PATH` 一致；FR-501 不再独立写算法 |
| Q2 Unambiguous | ✓ | FR-508 仍给精确算法定义，复算性边界在子条目里说明清楚 |
| Q4 Consistent | ✓ | FR-501 / FR-508 不再互斥；新增的 FR-507a/507b 之间无冲突（一个读、一个删） |
| Q6 Verifiable | ✓ | FR-507a/507b 各自验收为命令级断言（exit code、stdout/stderr、文件存在性、索引摘除）；NFR-502 改为依赖闭包级判断仍可在 review 时核对 |
| Q7 Modifiable | ✓ | ID 规则单点权威化，Q7 闭合 |

### 3.2 Group A / C / G（受影响维度）

| ID | r2 结论 | 备注 |
|----|--------|------|
| A2 复合需求 | ✓ | FR-507 拆分后不再 CRUD-pack |
| A3 设计泄漏 | ✓ | NFR-502 抽象到依赖面；FR-508 算法属"ID 形态契约"保留单点定义可接受（对应 r1 的"权威定义在 FR-508 可保留"判断） |
| C1 Requirement contract | ✓ | FR-507a/507b 字段齐全（Statement/Acceptance/Priority/Source） |
| C5 Deferral handling | ✓ | § 5 deferred backlog 未变动 |
| G1 Oversized FR | ✓ | FR-507 拆分消除了 GS2 CRUD-packing 边界信号 |
| G3 Repairable scope | ✓ | r1 全部 5 项 finding 在单轮内被收敛，无回归性新问题 |

### 3.3 新引入风险扫描（fresh light pass）

- ASM-504 与 OQ-502 措辞中"中央索引"现统一指向 `.garage/knowledge/.metadata/index.json`，与 FR-507b 一致，无残留旧路径。grep 验证：spec 全文不再出现 `experience/records/.metadata/index.json`。
- FR-510 列出的 `garage knowledge --help` 子命令仍含 `add / edit / show / delete / search / list` 6 项；`garage experience --help` 含 `add / show / delete` 3 项——FR-507 拆分为 507a/507b 不改变 CLI 子命令数，FR-510 验收无需联动调整。
- FR-509 的 `cli:knowledge-add` / `cli:knowledge-edit` 来源标记没有被本轮编辑波及，与 CON-504 仍一致。
- ASM-504 关于 "若 `ExperienceIndex` 没有 `delete()` ... fallback" 的措辞，r1 已说明实际 fallback 不会触发；FR-507b 把正向路径写死调 `ExperienceIndex.delete()`，可在 design 阶段直接消化 ASM-504 的 fallback 分支，不需进一步规格修订。
- NFR-504 验收仍含 `grep "Knowledge entry " src/garage_os/cli.py`，这与 NFR-502（已修）属性质不同——NFR-504 检查的是"stable stdout marker 必须由顶层常量产出"（F004 § 11.5 已确立模式），不是依赖面约束。r1 未列入 finding，r2 delta-only 不扩张范围；保持沿用。

## 4. 发现项（r2）

> 无 critical / important finding；R1 的 5 项 LLM-FIXABLE finding 全部已在本轮关闭，未引入新冲突或新缺口。

## 5. 缺失或薄弱项

- 沿用 r1 结论：无关键缺失。ASM-504 fallback 分支不会触发，可由 design 阶段直接确认正向路径，不需要写入 spec 修订。

## 6. 结论

**通过**

判断依据：
- R1 的 2 项 important LLM-FIXABLE finding（Q4 算法矛盾、Q1 索引路径错误）均已收敛，且与源码事实一致
- R1 的 3 项 minor LLM-FIXABLE finding（A3 实现文件 grep、A2/G1 FR-507 拆分、A3 ID 规则散落）均已收敛
- delta-only 二轮扫描未发现新引入的内部矛盾、范围漂移或事实性错误
- 范围 / 范围外 / 假设 / 开放问题闭合度仍足以支撑 `hf-design` 作为稳定输入
- 无 USER-INPUT 类阻塞 finding；无 critical / route / stage / 证据冲突
- 满足 rubric "范围清晰、核心需求可验收、无阻塞 USER-INPUT、足以成为设计稳定输入"

## 7. 下一步

- **`规格真人确认`**：父会话向真人展示 1-2 句 plain-language 通过结论，等待人类批准；批准后再交给 `hf-design` 作为稳定输入。
- 不需要 reroute via router；不需要再开 review 轮次。

## 8. 交接说明

- `规格真人确认`（auto mode）：reviewer subagent 不代替父会话写入批准结论，由父会话在 approval step 完成后同步 `task-progress.md` Current Stage 与 Next Action Or Recommended Skill，并把规格状态从 `草稿` 推到批准态。
- 无 USER-INPUT finding，父会话不需要发起最小定向问题。
- 父会话在向真人摘要时只说 "r1 列出的 5 项 finding 全部已修复，r2 通过；进入规格真人确认"，不需要把 rubric 表格原样贴给用户。

## 9. 结构化返回

```json
{
  "conclusion": "通过",
  "next_action_or_recommended_skill": "规格真人确认",
  "record_path": "/workspace/docs/reviews/spec-review-F005-knowledge-authoring-cli-r2.md",
  "key_findings": [],
  "needs_human_confirmation": true,
  "reroute_via_router": false,
  "finding_breakdown": [],
  "round1_findings_closure": [
    {
      "round1_id": "[important][LLM-FIXABLE][Q4]",
      "summary": "FR-501 vs FR-508 ID 哈希输入定义直接矛盾",
      "status": "closed",
      "evidence": "FR-501 验收 #4 (行 159) 改为引用 FR-508，删除算法重写与 '保证可复算' 措辞；FR-508 维持时间敏感算法为单一权威定义"
    },
    {
      "round1_id": "[important][LLM-FIXABLE][Q1]",
      "summary": "FR-507 验收 #4 索引路径与 ExperienceIndex.INDEX_PATH 不一致",
      "status": "closed",
      "evidence": "FR-507 已拆为 FR-507a/FR-507b；FR-507b 验收 #2 (行 229) 路径改为 .garage/knowledge/.metadata/index.json，与 experience_index.py:23 INDEX_PATH 一致"
    },
    {
      "round1_id": "[minor][LLM-FIXABLE][A3]",
      "summary": "NFR-502 验收 #2 把 grep src/garage_os/cli.py 写进规格层",
      "status": "closed",
      "evidence": "NFR-502 验收 (行 283-285) 改为 'pyproject.toml 不新增 runtime dependency' + '依赖闭包仅含 stdlib + garage_os.*，按依赖面校验，不绑定具体文件路径'"
    },
    {
      "round1_id": "[minor][LLM-FIXABLE][A2/G1]",
      "summary": "FR-507 打包 experience show + delete",
      "status": "closed",
      "evidence": "FR-507 已拆为 FR-507a (experience show, 行 213-220) 与 FR-507b (experience delete, 行 222-230)，独立优先级、独立验收"
    },
    {
      "round1_id": "[minor][LLM-FIXABLE][A3]",
      "summary": "§ 4.1 与 FR-501 重复 ID 生成规则",
      "status": "closed",
      "evidence": "§ 4.1 表格 (行 118) 与 FR-501 验收 #4 (行 159) 均改为引用 FR-508 单点权威定义"
    }
  ]
}
```
