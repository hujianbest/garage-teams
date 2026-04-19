# Design Review — F005 Garage Knowledge Authoring CLI

- 评审对象: `docs/designs/2026-04-19-garage-knowledge-authoring-cli-design.md`（D005, 草稿）
- 关联规格: `docs/features/F005-garage-knowledge-authoring-cli.md`（已批准, see `docs/approvals/F005-spec-approval.md`）
- 评审日期: 2026-04-19
- Reviewer: hf-design-review subagent
- Workflow Profile / Mode: `standard` / `auto`
- Workspace Isolation: `in-place`
- Branch: `cursor/f005-knowledge-add-cli-177b`
- UI Surface 激活: ❌（CLI-only feature；本评审不依赖 hf-ui-review peer）

## 结论

**通过**

D005 草稿可以进入 `设计真人确认` step；不存在阻塞 `hf-tasks` 干净拆解的设计空洞。所有 10 条 FR / 5 条 NFR / 5 条 CON 都在 §3 追溯表里有明确承接落点；3 个 ADR 形态完整（背景 / 决策 / 候选 / 后果 / 可逆性）；3 张数据流时序图覆盖了 add / edit（关键 v1.1 不变量延伸路径）/ experience delete（关键索引级联路径）；T1-T6 任务粒度建议清晰。仅有 4 条 `minor` finding（全部 LLM-FIXABLE，可在起草侧顺手处理或推迟到 tasks/实现阶段处理）。

## 多维评分摘要（内部）

| 维度 | 分数 | 备注 |
|------|------|------|
| `D1` 需求覆盖与追溯 | 9/10 | §3 追溯表 22 行覆盖全部 FR/NFR/CON；FR-507a / FR-507b 都有独立行；FR-509 在 ADR-503 单独展开 |
| `D2` 架构一致性 | 9/10 | Thin CLI Handler Pattern 与 `_init` / `_status` / `_run` / `_memory_review` 风格一致；不引入新模块 |
| `D3` 决策质量与 trade-offs | 8/10 | §5 三候选对比 + §6/7/8 三 ADR；ADR-503 对 "publisher 路径 artifacts 留空" 的描述与代码不严格吻合（见 finding F2） |
| `D4` 约束与 NFR 适配 | 8/10 | §11 NFR Mapping 5 行覆盖；NFR-503 < 1.0s 给出可执行验证方式 |
| `D5` 接口与任务规划准备度 | 8/10 | §9 三个参数表 + §13.2 30 条测试 + §14 T1-T6 任务建议；§10.2 mermaid 中 `update()` 返回值与实际签名不一致（finding F3） |
| `D6` 测试准备度与隐藏假设 | 8/10 | §13 测试金字塔 + §15 4 条 OD；NFR-503 smoke test 显式 |

## 发现项

### F1: [minor][LLM-FIXABLE][D2/CON-501] CON-501 的"现有 experience 父命令"措辞与代码现状不一致；设计已正确处理但应在追溯表中显式标注

- **证据**：
  - 规格 CON-501（`docs/features/F005-garage-knowledge-authoring-cli.md:316`）原文："新增子命令必须挂在**现有** `knowledge` / `experience` 父命令下，不引入新顶级命令"。
  - 实际 `cli.py` 当前只存在 `init` / `status` / `run` / `knowledge` / `memory` 5 个一级 subparser（`src/garage_os/cli.py:585-666`），没有 `experience` 父命令。
  - 设计 §3 表中 CON-501 行注："`experience` 父 subparser 是新引入但仍是二级，不破坏 CON-501"；§9.1 子命令树也明确把 `experience` 标为 NEW parent。
- **影响**：实际不阻塞——规格 §4.1 自身就把 `garage experience add/show/delete` 列为本 cycle 引入的子命令，CON-501 措辞中的"现有 experience"是规格本身的笔误，设计的解读是一致的；但设计追溯行可以更显式说明这是"在 garage 顶级下新增 1 个二级 parent + 在其下挂 3 个三级子命令"，避免后续 reviewer 误以为违反 CON-501。
- **建议**：把 §3 追溯表 CON-501 行的备注从"`experience` 父 subparser 是新引入但仍是二级，不破坏 CON-501"扩成"`experience` 父 subparser 是本 cycle 新增的二级 parent（与 `knowledge` / `memory` 平级），未在 garage 之上引入新顶级 entrypoint；规格 CON-501 的'现有 experience'措辞为遗留笔误，已在 spec round 1 review 之外被 §4.1 实质覆盖"。

### F2: [minor][LLM-FIXABLE][D3/A3] ADR-503 对 publisher 路径 `artifacts` 行为的描述与现有代码不严格吻合

- **证据**：
  - ADR-503（设计 §8）原文："CLI experience add 写 record.artifacts = ["cli:experience-add"]，与 publisher 路径**留空或写其他来源**不冲突"。
  - 实际 publisher 代码（`src/garage_os/memory/publisher.py:287`）：`artifacts=list(payload.get("source_artifacts", []))` —— 当 candidate payload 含 `source_artifacts` 时，publisher 会把这些字符串（通常是文件路径）写入 `ExperienceRecord.artifacts`，**不**总是留空。
  - 真正的"区分性"（手工 vs 自动）成立的依据是 **`cli:` 前缀**，而不是"留空 vs 非空"。
- **影响**：disambiguation 性质本身仍然成立（grep `cli:experience-add` 不会命中 publisher 写入的文件路径），下游 task plan / 实现不会被误导；但 ADR-503"留空"措辞会让后续 reviewer 在追溯 publisher 实际行为时产生短暂混淆。
- **建议**：把 ADR-503 后果段中"+ grep 'cli:experience-add' .garage/experience/records/ 可一键过滤"扩成"+ grep `cli:experience-add` `.garage/experience/records/` 可与 publisher 路径写入的 source-artifact 字符串（通常是文件路径，见 `publisher.py:287`）严格区分"，并把决策段中"publisher 路径留空或写其他来源不冲突"改为"publisher 路径写入的 `artifacts[0]` 是文件路径或外部 source 字符串，不会带 `cli:` 前缀"。

### F3: [minor][LLM-FIXABLE][D5] §10.2 数据流 mermaid 中 `KnowledgeStore.update()` 返回值与实际签名不符

- **证据**：
  - 设计 §10.2 mermaid 第 5 行："KS-->>H: checksum, new_version"。
  - 实际签名（`src/garage_os/knowledge/knowledge_store.py:181-204`）：`def update(self, entry: KnowledgeEntry) -> str:` —— 只返回 checksum 字符串。
  - 实际 `update()` 通过 `entry.version += 1`（line 194）就地修改 entry 的 version 字段；handler 必须从 `entry.version` 读取新版本，而不是从 `update()` 返回值。
- **影响**：mermaid 展示错把 `new_version` 算作返回值。task plan 或实现阶段如果照搬"checksum, new_version"作为 update 接口契约，会出现类型错误；但只要实现者读源码就能立刻发现，不会真的塞错代码。仍属于 LLM-FIXABLE。
- **建议**：把 §10.2 mermaid 第 5 行改为 `KS-->>H: checksum (entry.version mutated in-place)`，并在 §2.3 现有系统约束 `KnowledgeStore.update(entry)` 行后追加一句"调用方需通过 `entry.version` 读取递增后的版本，`update()` 本身只返回 checksum"。

### F4: [minor][LLM-FIXABLE][D6] `knowledge edit` 对 `KnowledgeEntry.date` 的处理未显式说明

- **证据**：
  - `KnowledgeEntry` dataclass（`src/garage_os/types/__init__.py:97-115`）中 `date: datetime` 是创建时间字段；没有独立的 `updated_at` 字段。
  - 设计 §9.3 edit 参数表与 §10.2 数据流均未提及"edit 时如何处理 `date`"——按 §10.2"overlay explicit fields"语义，未传 `--date` 就保持不变（这正是预期行为），但因为参数表里也没有 `--date`，就会有"是否完全不可改 date？"的歧义。
  - 规格 FR-503 对 date 也未提及。
- **影响**：实现者按"未传字段保持不变 + 没有 `--date` 参数"会推出"date 永不被 CLI edit 修改"的正确实现，task 拆解不会被误导；但显式写一行可以避免下游 reviewer 翻 dataclass 验证。
- **建议**：在 §10.2 数据流后追加一段或在 §13.2 测试列表追加一条："`knowledge edit` 不修改 `KnowledgeEntry.date`（dataclass 中 `date` = 创建时间；CLI 不暴露 `--date` 参数；version 通过 `update()` 自增）"，并补 1 条单元测试断言 edit 后 entry.date 与原值一致。

## 薄弱或缺失的设计点

- §10.x 数据流图覆盖了 add / edit / experience delete，但 knowledge `show` / `delete` / experience `add` / `show` 的数据流未画——这 4 条都是薄包装现有 store/index 方法，不画也可，**不属于阻塞**；如果起草者顺手在 §10.4-§10.7 各加 3-5 行简短 mermaid，会让 task plan 的输入更对称。属于 nice-to-have。
- §13.2 第 7 条 "knowledge add collision (monkeypatch `datetime.now`)"——建议在测试 hint 里指明 monkeypatch 的目标是 `cli._generate_entry_id` 内部调用的 `datetime.now`（而不是全局），便于 task plan 拆 helper 时考虑可注入 timestamp 的依赖注入参数（与设计 §2.1 FR-508 行已写的"timestamp 通过依赖注入便于测试"呼应）。属于 nice-to-have。
- ADR-501 / ADR-502 / ADR-503 都未列 `参与者 / 评审者`——按本仓库 `standard` profile 不强求 inline ADR 列出 committee，但若起草者愿意加 1 行（如"评审者: hf-design-review subagent；起草者: hf-design"）会增强追溯。属于 nice-to-have。

## 下一步

- 结论 = **通过** → 进入 `设计真人确认`。`auto` mode 下父会话可直接写 approval record（见 spec approval 同样模式：`docs/approvals/F005-spec-approval.md`）。
- 4 条 minor finding 均 `LLM-FIXABLE`，建议起草者在 approval record 落盘前顺手在设计文中消化 F1 / F2 / F3（措辞修正），F4 可推迟到 hf-tasks 阶段补 1 条测试 hint。即使全部不修改，也不阻塞 `hf-tasks` 推进——4 条都属于"不影响任务拆解、不影响实现正确性"的措辞 / 文档完备度问题。

## 记录位置

- `docs/reviews/design-review-F005-knowledge-authoring-cli.md`（本文件）

## 交接说明

- `设计真人确认`：`auto` 下由父会话写 approval record；本 reviewer 不代填。
- 不调用 `hf-design`（无 `需修改` 或 `阻塞` 项）。
- 不调用 `hf-workflow-router`（无需求漂移、无证据冲突、无 stage 不清）。
