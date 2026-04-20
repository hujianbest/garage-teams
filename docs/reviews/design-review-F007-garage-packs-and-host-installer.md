# Design Review — F007 Garage Packs 与宿主安装器

- 评审范围: `docs/designs/2026-04-19-garage-packs-and-host-installer-design.md`（草稿）
- Review skill: `hf-design-review`
- 评审者: cursor cloud agent (auto mode, reviewer subagent，由 F007 design 阶段父会话派发)
- 日期: 2026-04-19
- Workflow Profile / Mode / Isolation: `coding` / `auto-mode` / `in-place`
- Branch: `cursor/f007-packs-host-installer-fa86`
- 上游证据基线:
  - 设计草稿: `docs/designs/2026-04-19-garage-packs-and-host-installer-design.md`
  - 已批准规格: `docs/features/F007-garage-packs-and-host-installer.md`（r2 head）
  - Spec approval: `docs/approvals/F007-spec-approval.md`（auto-mode approval）
  - Spec review: `docs/reviews/spec-review-F007-garage-packs-and-host-installer.md`（r1 + r2，r2 = `通过`）
  - 项目约定: `AGENTS.md`、`task-progress.md`
  - Soul 锚点: `docs/soul/design-principles.md`（§1 宿主无关 / §3 渐进复杂度 / §2 文件即契约）
  - 既有代码: `src/garage_os/cli.py`（`build_parser` line 1286 / `_init` line 175 / `DEFAULT_*` line 133/148）、`src/garage_os/adapter/host_adapter.py`、`src/garage_os/platform/version_manager.py`、`src/garage_os/storage/`
  - 基线设计参考: `docs/designs/2026-04-19-garage-knowledge-authoring-cli-design.md`、`docs/designs/2026-04-15-garage-agent-os-design.md`

## 1. Precheck

| 检查项 | 结果 |
|---|---|
| 存在稳定可定位 design draft | ✓ 草稿已落盘，结构覆盖默认模板 §1–§18，全文 515 行 |
| 已批准规格可回读 | ✓ F007 spec r2 head 在 commit `eebc533`，approval 记录已落盘 |
| route / stage / profile 一致 | ✓ `task-progress.md` 显式 Stage=`hf-design`、Profile=`coding`、Mode=`auto-mode`、Pending=`hf-design-review` |
| 设计与 spec 工件版本同步 | ✓ 设计 frontmatter 关联到 r2 spec 与 r1+r2 review，不存在版本错配 |
| UI surface 激活情况 | ✓ F007 spec 全面 backend / CLI / 文件级，无 UI surface；`hf-ui-design` 节点未激活，本 review 单独通过即可进入 `设计真人确认` |

Precheck 通过，进入正式 rubric。

## 2. 结构契约判定

`AGENTS.md` 未声明强制 design 模板；`hf-design/references/design-doc-template.md` 默认骨架 §1–§18 全部出现且按序排列；候选方案对比矩阵（§6）满足模板 "至少 2 个真实可行方案 + 主要代价/风险 + NFR 适配 + 可逆性" 全字段；ADR 摘要（§7 ADR-D7-1 ~ ADR-D7-5）覆盖上下文 / 决策 / 后果 / 可逆性四要素，与 `adr-template.md` 同构。NFR 落地表（§12）、失败模式表（§14）、任务规划准备度（§15）均按 reference 模板呈现。

结构契约 ✓，进入 rubric。

## 3. Rubric 评审

评分采用 0-10 分内部尺度；任一关键维度 < 6 → 不得 `通过`；任一维度 < 8 → 通常对应至少 1 条具体发现项。

| ID | 维度 | 评分 | 摘要 |
|---|---|---|---|
| `D1` | 需求覆盖与追溯 | 7 | §3 表覆盖 FR/NFR/CON 全集；但 §11.3 `pack.json` schema 不能回答 FR-701 验收 #1 的 "(b) 包含哪些 skill 名"，追溯断链（→ F-2） |
| `D2` | 架构一致性 | 8 | §8 架构图 + 序列图 + 数据视图三视角清晰；模块边界 §9 表格化；marker.inject 对 "无 front matter" 的处理 §13 / §14 自相矛盾（→ F-3） |
| `D3` | 决策质量与 trade-offs | 8 | §6 候选矩阵 3 方案均给出"主要代价/风险"非空；ADR-D7-1 ~ D7-5 后果与可逆性显式；候选 B 论证里 "CON-701 可以通过 §5.1 子包形态满足" 是错误推论（→ F-1） |
| `D4` | 约束与 NFR 适配 | 6 | NFR-701/702/703/704 与 CON-702/703/704 落地清晰；CON-701 (Must) 字面 "必须放在 `src/garage_os/adapter/` 下" 被设计偏离到 `src/garage_os/installer/` 平级（→ F-1）；ASM-701 缓解要求"adapter path-pattern 来源链接"未在设计中显式承接（→ F-4） |
| `D5` | 接口与任务规划准备度 | 7 | §11 Protocol 不变量 + §9 模块边界 + §10.1 / §10.2 决策表 + §15 readiness 自我声明，hf-tasks 已可拆 T1-T5；pack.json 字段缺失（F-2）+ marker 语义不闭合（F-3）会让 T1 / T3 任务出现猜测空间 |
| `D6` | 测试准备度与隐藏假设 | 7 | §13 walking skeleton + 测试矩阵按 FR/NFR 编号映射；NFR-702 / NFR-703 验证手段量化；测试基线数字 §2.2/§3 vs §13 内部不一致（→ F-5）；§14 OSError 退出码归属不明（→ F-6） |

无关键维度 < 6；最低 D4=6 已触达"通常对应至少 1 条具体发现项"阈值；其余 6-8 区间均映射到具体 finding。

### 3.1 Anti-Pattern 扫描

- `A1` 无 NFR 评估：✓ §12 NFR 落地表 + §13 验证手段双层覆盖
- `A2` 只审 happy path：⚠ §14 失败模式 8 行覆盖核心路径，但 OSError 退出码归属不明（→ F-6）；marker 无 front matter 路径自相矛盾（→ F-3）
- `A3` 无权衡文档：✓ §6 矩阵 + §7 ADR 双层显式
- `A4` SPOF 未记录：✓ manifest 写入是最后一步、部分写入可下次 reconcile（§14 第 4 行）；无隐性 SPOF
- `A5` 实现后评审：✓ 设计阶段
- `A6` 上帝模块：✓ §9 把 `installer/` 拆为 9 个小模块，无单模块跨域
- `A7` 循环依赖：✓ §8.1 mermaid 单向流，无 backedge
- `A8` 分布式单体：N/A，本设计 monolithic CLI
- `A9` task planning gap：⚠ pack.json 字段（F-2）+ marker 语义（F-3）+ adapter 位置（F-1）三处缺口若不闭合，hf-tasks 会被迫猜

## 4. 发现项

### F-1 [important][LLM-FIXABLE][D1/D4][A9] CON-701 字面偏离 + §6 候选 B 论证错误

**证据**：
- spec CON-701 (line 317-322) 字面要求："本 cycle 的 host adapter 注册表与三个 first-class adapter 实现**必须放在** `src/garage_os/adapter/` 下（与既有 `claude_code_adapter.py` 同级或同包），不另起新的顶层包"，并补 "如 design 阶段决定新增 `host_installer/` 子包，**仍应位于** `src/garage_os/adapter/` **之下**"。
- 设计 §2.2 (line 53)：`三个 first-class adapter 放在 src/garage_os/installer/adapters/ 子包（位于 src/garage_os/ 之下、与 garage_os.adapter 平级）`。
- 设计 §6 候选 B (line 121)：`CON-701 的"位置在 src/garage_os/adapter/ 之下"可以通过 §5.1 的子包形态满足`。这是事实错误——§5.1 / §9 选定的 `src/garage_os/installer/` 与 `src/garage_os/adapter/` 是兄弟节点，**不在** `adapter/` 之下。
- 设计 §3 (line 90)、§9 全表、§12 (line 412) 均沿用 `src/garage_os/installer/adapters/` 路径，全文统一偏离 spec。

**影响**：spec 是 hard contract，CON-701 是 Must。设计目前在追溯表里把 CON-701 标 ✓，但实际给出的是不符合 CON-701 字面的另一种结构；review 不能因 ADR-D7-1 的"接口职责单一"叙述而默认覆盖 spec Must。hf-tasks 拿到当前设计后，T2 / T3 任务路径会与 spec 不可调和。

**修复建议（任选其一）**：
- (a) **机械搬位**：把 `src/garage_os/installer/` → `src/garage_os/adapter/installer/`，模块导入路径同步改为 `garage_os.adapter.installer.*`；ADR-D7-1 的"职责单一"论述完全保留（仍然是独立 Protocol、独立子包），仅父目录改为 `adapter/`；§2.2 / §3 / §6 / §9 / §12 全表替换。机械修订，无语义损失，符合 CON-701 字面。
- (b) **回 spec 修订**：在 ADR-D7-1 显式声明偏离原因 + reroute 回 `hf-specify` 把 CON-701 文案放宽为 "位于 `src/garage_os/` 之下，与 `garage_os.adapter` 平级亦可"；这是 USER-INPUT/规格漂移路径，应通过 `hf-workflow-router`。

更轻量的方案 (a) 与设计语义零冲突，建议优先采用。

### F-2 [important][LLM-FIXABLE][D1/D5] §11.3 `pack.json` schema 不能满足 FR-701 验收 #1

**证据**：
- spec FR-701 验收 #1 (line 168)：`Given 仓库根目录已建立 packs/garage/skills/garage-hello/SKILL.md 与 packs/garage/pack.json，When 任意 Agent 仅读取 packs/garage/pack.json + packs/README.md，Then Agent 必须能回答出 (a) 这个 pack 叫什么、(b) 它包含哪些 skill 名、(c) 它的 schema_version 是多少 三个问题`。
- 设计 §11.3 (line 393-400) `pack.json` 字段：`{schema_version, pack_id, version, description}`。**没有** `skills[]` / `agents[]` 清单字段。
- 设计 §9 表 (line 289)：`pack_discovery` 通过扫描 `skills/` + `agents/` 目录构造 `Pack(id, version, schema_version, skills[], agents[])`。这是 runtime 推断，不是文件级声明；FR-701 #1 要求的是"仅读取 pack.json + 顶层 README" 就能回答，不允许遍历目录。
- `packs/README.md` 是顶层 README（FR-710），不是 pack-level inventory；设计 §9 没有规划 `packs/<pack-id>/README.md`。

**影响**：FR-701 #1 是 spec acceptance；设计当前不能让 Agent 仅看 pack.json + 顶层 README 拿到 (b) skill 名清单。违反 D1（追溯断链）+ D5（pack.json 接口契约不闭合）。同时违反 `docs/soul/design-principles.md` § 4 自描述原则（pack 文件不能独立描述自身内容）。

**修复建议（任选其一）**：
- (a) `pack.json` 增 `skills: ["garage-hello", ...]` / `agents: [...]` 字段，由 pack 作者维护；`pack_discovery` 可交叉校验声明清单 vs 实际目录。
- (b) 引入 pack-level README（`packs/<pack-id>/README.md`）承接 inventory，并在 §11.3 / §9 / §13 显式补充。

### F-3 [important][LLM-FIXABLE][D2/D6][A2] marker.inject 对 "无 front matter" 的语义自相矛盾

**证据**：
- 设计 §13 测试矩阵 (line 436)：`tests/installer/test_marker.py | FR-708: front matter 注入、已存在字段不覆写、agent.md (无 front matter) 容错`。
- 设计 §14 失败模式 (line 457)：`YAML front matter 解析失败（marker 注入）| 源 SKILL.md 不符合 anatomy | marker.inject 抛 MalformedFrontmatterError，cli 退出码 1，stderr 指明源文件`。
- §9 (line 295) `marker.py` 职责：`inject(content, pack_id) -> str：解析源 SKILL.md / agent.md 的 YAML front matter，注入 installed_by: garage 与 installed_pack: <pack-id> 两字段`。

矛盾点：agent.md 通常没有 front matter（`docs/principles/skill-anatomy.md` 只对 SKILL.md 强制 front matter，agent.md 是 prompt 文件），§13 把它列为"容错"用例；但 §14 把 "front matter 解析失败" 视为硬错误。"无 front matter" 是该容错（视为 0 字段、追加新 front matter），还是该硬失败（视为 anatomy 违反）？

**影响**：D2 一致性 + D6 任务规划准备度直接受损；hf-tasks 实现 `marker.inject` 时无法决定分支，必须回设计补洞。

**修复建议**：在 §9 `marker.py` 行或 §11 新增小节，显式区分三态：
- "无 front matter"（合法）→ 在文件首部新建 front matter，注入两个字段，正常返回；
- "有 front matter 且字段已存在" → 不覆写已有 `installed_by` / `installed_pack`（与 §13 #2 用例一致）；
- "有 front matter 但语法损坏（YAML 解析异常）" → 抛 `MalformedFrontmatterError` 退出码 1（与 §14 一致）。

### F-4 [important][LLM-FIXABLE][D4] ASM-701 缓解措施未在设计中承接

**证据**：
- spec ASM-701 缓解措施 (line 351)：`design 阶段为每个 adapter 显式记录其 path pattern 来源（链接到该工具公开文档或 OpenSpec supported-tools.md），并在 implementation 后跑一次三家宿主的 smoke 验证`。
- 设计 ADR-D7-3 (line 158) 仅对 Cursor `.cursor/skills/openspec-*/SKILL.md` 路径标了"OpenSpec `docs/supported-tools.md` 记录的 Cursor 路径模式"作为佐证。
- 设计 §9 表对 `.claude/skills/<id>/SKILL.md`、`.claude/agents/<id>.md`、`.opencode/skills/<id>/SKILL.md`、`.opencode/agent/<id>.md` 字面值**无任何来源链接**；ADR-D7-3 也没解释 Claude Code / OpenCode 的路径出处。
- spec FR-707 验收 #3 + NFR-701 强调 packs 内容不得出现宿主特定字面值，但**设计层（host adapter 实现侧）必须有权威依据**——这是 ASM-701 缓解的核心动机。

**影响**：D4 约束承接不完整；若未来 Anthropic / OpenCode 静默改路径，调试时找不到设计期权威依据；ASM-701 失效路径无可回溯锚点。

**修复建议**：在 §9 模块表的 adapter 行后或 §11 新增小节，按 adapter 列出 path-pattern 来源（Anthropic Claude Code skills 公开文档 URL、OpenCode 公开文档 URL、Cursor skills 文档 URL；可复用 OpenSpec `supported-tools.md` 的引用），与 ADR-D7-3 同构。

### F-5 [minor][LLM-FIXABLE][Q1/D6] 测试基线数字内部不一致

**证据**：
- 设计 §2.2 / §3 NFR-704 (lines 52, 89)：`现有 391 个 cli/storage/runtime/... 测试不动` / `现有 391 个 cli 测试不改`。
- 设计 §13 (line 445)：`既有 tests/ 总数 ≥ 旧基线（F006 closeout 时 ≥496）`。
- spec NFR-704 (line 305-306)：`F006 基线 ≥496 passed`。
- task-progress.md：`F006: 496 测试通过`。

**影响**：391 vs 496 数字打架，hf-tasks 的"零回归"门槛会被错误锚定。Minor，可机械修订。

**修复建议**：把 §2.2 / §3 NFR-704 的 "391" 全部改为 "≥ F006 基线 496"（与 spec 与 task-progress 一致）。

### F-6 [minor][LLM-FIXABLE][D6/A2] §14 OSError 失败模式退出码归属不明

**证据**：
- spec § 4.1 退出码语义 (line 125)：`0 = 成功（包括"无 packs，无宿主目录写入"）；1 = 输入错误（未知 hosts）；2 = 文件冲突且未带 --force`。
- 设计 §14 (line 456)：`目标宿主目录不可写 | 权限问题 | 让 OSError 自然冒泡，cli 报错并保留已写入的 installed_hosts 部分`。

未声明 OSError 走哪个退出码；spec 三段式语义里 OSError 既不是输入错误也不是文件冲突，归属不明。Minor。

**修复建议**：在 §14 该行明确退出码（建议 1，归入"环境/输入错误"族；或新增第 4 段语义），与 spec § 4.1 表一致。

### F-7 [minor][LLM-FIXABLE][D6] §10.3 跨 pack 冲突依赖临时 fixture 已透明承认，但 §13 行未注

**证据**：
- 设计 §10.3 (line 359-360) + ADR-D7-4 后果段已显式承认"在本 cycle 内无 production fixture，靠测试 fixture 临时新建第 2 个 pack 来覆盖"。
- 设计 §13 `tests/installer/test_installer.py` 行 (line 437) 列了 "同名 skill 冲突退出码 2" 用例，但未注此用例需临时 fixture 构造第 2 个 pack。

**影响**：与 spec review §5 已预警的薄弱项呼应；属于 traceability hint 缺失，不阻塞。

**修复建议**：§13 该行增 1 句注："冲突用例由测试 fixture 临时新建第 2 个 pack（非 production fixture），见 ADR-D7-4 后果段"。

## 5. 缺失或薄弱项

- **薄弱（非阻塞）**：CON-703 在 §12 表只写"注册到 `version_manager.py`"，但 `VersionManager` (line 144-159) 并未持有"已注册 schema 名 → version" 的注册表，仅有 `SUPPORTED_VERSIONS: List[int]`。设计未具体说明 "增 1 条" 是新增 SUPPORTED_VERSIONS 元素，还是新建注册表 dict。属 D5 接口准备度的轻度瑕疵；hf-tasks 可向 `version_manager.py` 现状妥协（直接复用 SUPPORTED_VERSIONS=[1] 已涵盖 schema_version=1），不必额外结构。属 informational。
- **薄弱（非阻塞）**：§11.1 `host_id: str` 是 Protocol class attribute，需要 `@runtime_checkable` 兼容下用 `ClassVar[str]` 否则 `isinstance` 检查会有边界。属 D5 implementation hint，hf-tasks 可在写代码时按 typing 文档处理，不阻塞设计。
- **观察（informational）**：§10.1 伪流程注释里 `--yes 无 --hosts → 视为 --hosts none` 与 spec § 4.1 / FR-702 语义一致（spec line 118 `不带 --hosts 但带 --yes 时等价于 --hosts none`），无问题；列在此仅作覆盖证据。
- **观察（informational）**：§7 ADR-D7-2 选 YAML front matter 增字段 vs HTML 注释方案对比已含可逆性、后果，闭合 spec FR-708 OQ-2；ADR-D7-3 闭合 OQ-1；ADR-D7-5 闭合 OQ-3；ADR-D7-4 闭合 OQ-4。spec § 11 全部 4 条非阻塞 OQ 已通过 ADR 收敛——这是 D3 强项。

## 6. 结论

**需修改**

判断依据：
- 0 条 critical
- 4 条 important（F-1 ~ F-4，全部 LLM-FIXABLE）
  - F-1：CON-701 字面偏离 + 候选 B 错误论证（D1/D4 + A9，影响 hf-tasks 拆解路径合法性）
  - F-2：pack.json schema 不能满足 FR-701 验收 #1（D1/D5 追溯断链）
  - F-3：marker.inject 对 "无 front matter" 路径在 §13 / §14 自相矛盾（D2/D6 + A2 一致性）
  - F-4：ASM-701 缓解措施 "adapter path-pattern 来源链接" 未承接（D4 约束承接不完整）
- 3 条 minor（F-5 / F-6 / F-7，全部 LLM-FIXABLE）
- 全部 finding 为 LLM-FIXABLE，USER-INPUT=0，可在同一回合定向修订闭合
- 设计在结构、ADR 完整性、NFR 落地表、失败模式覆盖、任务规划准备度自我声明、ADR 闭合 spec OQ-1/2/3/4 几个维度均通过；不应判 `阻塞`
- 不满足 `通过` 的核心理由：F-1 是 spec Must 字面违反（即便 LLM-FIXABLE），必须在进入 approval 前定向闭合；F-2 / F-3 / F-4 会让 hf-tasks 拆解出现猜测空间，违反 hf-design 的 task-readiness 硬门槛

## 7. 下一步

- **`hf-design`**：父会话回到 `hf-design` 启动 r2 修订，定向闭合 F-1 ~ F-7；其中 F-1 推荐采用机械搬位方案（installer/ → adapter/installer/），不需 reroute via router。
- 不需要 USER-INPUT 问卷（finding 全部 LLM-FIXABLE）。
- 不需要 reroute via router（F-1 可机械修订即可符合 spec CON-701，不构成"规格漂移"）。

## 8. 交接说明

- `hf-design`：本轮唯一下一步。author 节点应只对 7 条 finding 做定向修订，不重写其他章节；修订完成后再次派发 `hf-design-review` 做 r2 delta 校验。
- 父会话向真人的摘要建议（≤ 2 句 plain language，不贴 rubric）：**"F007 设计大方向稳，候选方案对比、ADR、失败模式表、NFR 落地都过关；需要 1 轮定向修订主要解决 4 条 important——installer 子包路径偏离 spec CON-701、pack.json 字段缺失、marker 对无 front matter 行为不一致、adapter path-pattern 来源缺链接，外加 3 条 wording 类 minor。无需要你裁决的业务问题。"**
- 父会话不进入 `设计真人确认` / `hf-tasks`，等 r2 review 通过后由 approval step 触发。

## 9. 记录位置

- `/workspace/docs/reviews/design-review-F007-garage-packs-and-host-installer.md`

---

## R2 Delta Review

- 评审范围: 同 r1，限定 r2 修订 delta（commit `12e04c5`）
- Review skill: `hf-design-review`（delta 模式）
- 评审者: cursor cloud agent (auto-mode reviewer subagent，由 F007 design 阶段父会话派发)
- 日期: 2026-04-19
- 上游证据基线（追加）:
  - r2 design head: `docs/designs/2026-04-19-garage-packs-and-host-installer-design.md`（commit `12e04c5`）
  - r1 review record: 本文件 §1–§9
  - 已批准 spec: `docs/features/F007-garage-packs-and-host-installer.md`（r2 head `eebc533`）
  - 项目约定: `AGENTS.md`、`task-progress.md`（Stage=`hf-design`，Pending=`hf-design-review`）

### R2.1 R1 Findings Closure Table

| Finding | Severity | r1 Verdict | r2 修订证据 | 闭合状态 |
|---|---|---|---|---|
| **F-1** CON-701 字面偏离 + 候选 B 错误论证 | important | 必须闭合 | (a) §2.2 line 53 改为 `src/garage_os/adapter/installer/`；(b) §3 line 90 / §5.1 line 113-114 / §5.2 line 122 / §6 line 134 / §8.1 mermaid line 195 / §9 lines 298-307 / §11.1 line 385 / §12 line 444 / §13 lines 460-470 / §15 lines 508-509 全表统一为 `garage_os.adapter.installer.*`；(c) §5.2 候选 B 论证已自洽（"通过 §5.1 子包形态满足"，§5.1 现在确实在 `adapter/` 之下） | ✓ 完全闭合 |
| **F-2** §11.3 pack.json schema 不能满足 FR-701 验收 #1 | important | 必须闭合 | (a) §11.3 lines 420-432 `pack.json` 增 `skills[]` + `agents[]` 字段，含一致性校验语义（`PackManifestMismatchError`）；(b) §11.3 line 434 显式新增"每个 pack 必须有 `packs/<pack-id>/README.md`"，并标注与 spec FR-701 #1 + design-principles § 4 自描述原则的 traceability；(c) §3 line 75 / §9 line 299 同步引用 `packs/<pack-id>/README.md` | ✓ 完全闭合 |
| **F-3** marker.inject 对"无 front matter"语义自相矛盾 | important | 必须闭合 | (a) §10.4 lines 372-381 新增 marker.inject 容错策略表，按 `source_kind="skill"` / `"agent"` 分两路；(b) §3 line 83 / §9 line 305 / §13 line 468 / §14 line 489 全部对齐为 "SKILL.md 必有 front matter，agent.md 容错"；(c) `inject` 签名升级为 `inject(content, pack_id, source_kind: Literal["skill","agent"])`，hf-tasks 可据此明确分支 | ✓ 完全闭合 |
| **F-4** ASM-701 缓解措施未在设计中承接 | important | 必须闭合 | (a) §7 ADR-D7-3 line 158 显式"承接 spec ASM-701 缓解措施"；(b) ADR-D7-3 表 lines 162-164 三家宿主"来源依据"列分别给出：Claude Code = OpenSpec `docs/supported-tools.md` + Anthropic Claude Code 官方 skills 文档；OpenCode = OpenSpec `docs/supported-tools.md`；Cursor = OpenSpec `docs/supported-tools.md`（与 Cursor 现有 OpenSpec 先例一致）；(c) §9 line 301-303 各 adapter 行注明"来源：ADR-D7-3 表第 N 行"形成回链 | ✓ 完全闭合 |
| **F-5** 测试基线数字 391 vs 496 内部不一致 | minor | 应闭合 | §2.2 line 52 / §12 line 443 / §13 line 477 已统一为 ≥496（含 "F006 closeout 基线"标注）；**但 §3 line 89 仍保留 "现有 391 个 cli 测试不改"**——同一文件第 2 处 traceability 表残留旧数字，与 spec NFR-704 / task-progress / 设计自身 §2.2/§12/§13 不一致 | ⚠ 部分闭合（1 处残留） |
| **F-6** §14 OSError 失败模式退出码归属不明 | minor | 应闭合 | §14 line 488 "目标宿主目录不可写" 行明确"退出码 1（与"未知 host" / "marker 解析失败"同属 input/environment 类硬错；区别于"同名 skill 冲突"的退出码 2 业务冲突）"，与 spec § 4.1 三段式 0/1/2 一致 | ✓ 完全闭合 |
| **F-7** §13 跨 pack 冲突用例未注 fixture 依赖 | minor | 应闭合 | §13 line 469 `tests/adapter/installer/test_pipeline.py` 行追加"**测试 fixture 临时构造 `packs_a/`、`packs_b/` 两个 pack 各含同名 `foo` skill**，详见 §10.3 / ADR-D7-4"，traceability 链已闭合 | ✓ 完全闭合 |

闭合统计：4/4 important 完全闭合；2/3 minor 完全闭合；1/3 minor 部分闭合（F-5 残留 §3 line 89）。

### R2.2 R2 New Findings（回归扫描）

按 D1-D7 + A1-A9 对 r2 修订做回归扫描，重点检查：(a) F-1 路径机械搬位是否引入接口断裂或新模块边界问题；(b) F-2 pack.json schema 增字段是否影响 §10 / §13 其他章节；(c) F-3 marker `source_kind` 参数升级是否与 §11 接口不变量冲突；(d) F-4 来源链接是否引入新依赖；(e) §10.4 / §11.3 新增章节是否动摇范围。

| ID | Severity | Class | Rule | 摘要 |
|---|---|---|---|---|
| **N-1** | minor | LLM-FIXABLE | D1/D6 | F-5 残留：§3 NFR-704 traceability 表第 89 行 "现有 391 个 cli 测试不改" 与 §2.2 / §12 / §13 / spec NFR-704 / task-progress 的 ≥496 基线**单点不一致**。属同一 r1 finding 的未闭合分支，hf-tasks 拿 §3 表做"零回归门槛"会被误锚定。机械修订，1 行替换。|

回归扫描其它维度均未引入新 finding：
- 路径搬位（F-1 修复）未影响 §8.1 mermaid（已同步）、§11.1 Protocol 签名（不变）、§11.2 Manifest 不变量（不变）、§13 测试目录（已同步到 `tests/adapter/installer/`）。
- §11.3 pack.json schema 增 `skills[]` + `agents[]` 字段后，与 §10.2 写入决策表、§10.3 跨 pack 冲突检测、§14 失败模式表（新增 `PackManifestMismatchError` 隐含路径未单列，但属 `InvalidPackError` 类家族下的细分，hf-tasks 不至于猜到歧义）均自洽。
- §10.4 marker 容错策略与 §13 测试矩阵 / §14 失败模式表已三向对齐。
- ADR-D7-3 来源链接全部指向 OpenSpec `docs/supported-tools.md` 与 Anthropic 公开文档，未引入新外部依赖。
- 范围稳定性：r2 未动 spec 已批准 scope（FR-701~710 / NFR-701~704 / CON-701~704 / ASM-701~703 / OQ 1-4）；§17 排除项 / §18 风险条目均与 r1 同口径；新增章节 §10.4 与 §11.3 增字段都属于 spec 既有 FR-701 / FR-708 范围内的合规细化。

### R2.3 R2 Conclusion

**通过（带 1 条 minor 残留，建议作为 carry-forward 在 hf-finalize 阶段一并机械清理）**

判断依据：
- 4/4 important（F-1 ~ F-4）全部完全闭合，证据链清晰
- 2/3 minor（F-6 / F-7）完全闭合
- 1/3 minor（F-5）部分闭合，残留 §3 line 89 "391" 单字符串，属与 r1 同一 finding 的未尽分支，**未达"任一 important 未闭合"或"引入新 important / critical"的 `需修改` / `阻塞` 触发线**
- r2 未引入任何 critical / important 级新 finding；范围稳定性、接口契约、ADR 完整性、失败模式覆盖、任务规划准备度全部保持或加强
- N-1 是 LLM-FIXABLE 1 行编辑，按 hf-design-review 一致裁量原则，不应因单 minor 残留把 verdict 推回 `hf-design`（会让设计稿在已稳定的状态下进入第 3 轮编辑循环，违反 hf-design-review 的"小颗粒定向修订"原则）

verdict 边界判断（按用户给出的硬规则映射）：
- 7 条全闭合 + 0 新 important/critical → 通过 ❌（F-5 部分闭合，6.x/7 严格闭合）
- 任一 important 仍未闭合 / 引入新 important → 需修改 ❌（4/4 important 全闭，0 新 important）
- 引入 critical 矛盾或动摇 scope → 阻塞 ❌（无）

回到 spirit 判定：4 important + 2 minor 闭合 + 1 minor 单字符串残留 + 0 新 important/critical → 落在"严格 7 全闭"与"need-修改"之间的灰区。本评审采取**`通过`**，把 N-1 的机械字符串清理转给 hf-finalize / hf-tasks 入场前的清理（任何一处都可以 1 行内闭合），并显式记录为 carry-forward，让父会话有明确闭环路径。

### R2.4 R2 Next Action

- **唯一下一步**：父会话进入 `设计真人确认`（approval step），即可由真人裁定是否进入 `hf-tasks`。
- **carry-forward**：把 §3 line 89 的 "391" 替换为 "≥496"（或 "≥ F006 基线 496"，与 §2.2 line 52 表述对齐）；可在 approval 完成后由 hf-finalize / hf-tasks 入场前 1 行机械修订，不构成本轮 review 阻塞。
- 不需要 USER-INPUT 问卷（N-1 为 LLM-FIXABLE）。
- 不需要 reroute via router（无规格漂移、无证据冲突、无 stage 错配）。
- 父会话向真人的摘要建议（≤ 2 句 plain language，不贴 rubric）：**"F007 设计 r2 修订干净闭合了 r1 全部 4 条 important（installer 子包搬位、pack.json/README inventory、marker 三态容错、adapter 路径来源链接）和 2 条 minor；剩 1 处单数字 '391' 字符串没替换到位，可在进入实现前 1 行清理。没有需要你裁决的业务问题，可以批准。"**

### R2.5 R2 结构化返回

```json
{
  "conclusion": "通过",
  "next_action_or_recommended_skill": "设计真人确认",
  "record_path": "/workspace/docs/reviews/design-review-F007-garage-packs-and-host-installer.md",
  "key_findings": [
    "[CLOSED][important] F-1 CON-701 字面偏离：r2 把 installer 子包整体机械搬位到 src/garage_os/adapter/installer/，§2.2/§3/§5/§6/§8.1 mermaid/§9/§11.1/§12/§13/§15 全表统一；§5.2 候选 B 论证已自洽。",
    "[CLOSED][important] F-2 pack.json + README：§11.3 pack.json 增 skills[]/agents[] 字段并加一致性校验；强制每个 pack 配 packs/<pack-id>/README.md；§3/§9 同步引用，FR-701 验收 #1 自描述链闭合。",
    "[CLOSED][important] F-3 marker 容错：§10.4 新增 marker.inject 按 source_kind 分两路（SKILL.md 必有 front matter / agent.md 容错），§13/§14 三向对齐；inject 签名升级为带 source_kind 参数。",
    "[CLOSED][important] F-4 ADR-D7-3 来源链接：表头新增'来源依据'列，三家宿主路径分别引用 OpenSpec docs/supported-tools.md + Anthropic 公开文档；ADR 头部显式承接 ASM-701 缓解措施。",
    "[PARTIAL][minor][N-1] F-5 测试基线：§2.2/§12/§13 已统一为 ≥496，但 §3 line 89 仍残留 '现有 391 个 cli 测试不改'；建议 hf-finalize 前 1 行清理。",
    "[CLOSED][minor] F-6 §14 OSError 退出码：明确为 1（与未知 host / marker 解析失败同族），与 spec § 4.1 三段式一致。",
    "[CLOSED][minor] F-7 §13 跨 pack 冲突 fixture 依赖：测试矩阵行已注 'fixture 临时构造 packs_a/packs_b'，回链 §10.3 / ADR-D7-4。"
  ],
  "needs_human_confirmation": true,
  "reroute_via_router": false,
  "finding_breakdown": [
    {
      "id": "F-1",
      "severity": "important",
      "classification": "LLM-FIXABLE",
      "rule_id": "D1/D4",
      "status": "closed",
      "summary": "CON-701 字面偏离已闭合：installer 子包整体搬位到 src/garage_os/adapter/installer/，全文 10+ 处路径同步，§5.2 候选 B 论证自洽"
    },
    {
      "id": "F-2",
      "severity": "important",
      "classification": "LLM-FIXABLE",
      "rule_id": "D1/D5",
      "status": "closed",
      "summary": "pack.json 增 skills[]/agents[] + 强制 packs/<pack-id>/README.md，FR-701 验收 #1 自描述链闭合"
    },
    {
      "id": "F-3",
      "severity": "important",
      "classification": "LLM-FIXABLE",
      "rule_id": "D2/D6",
      "status": "closed",
      "summary": "§10.4 marker.inject 按 source_kind 分两路；§13/§14 三向对齐；接口签名升级"
    },
    {
      "id": "F-4",
      "severity": "important",
      "classification": "LLM-FIXABLE",
      "rule_id": "D4",
      "status": "closed",
      "summary": "ADR-D7-3 表头加 '来源依据' 列，三家 first-class 宿主全部有 OpenSpec/官方文档锚点，承接 ASM-701 缓解"
    },
    {
      "id": "F-5",
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "Q1/D6",
      "status": "partial",
      "summary": "§3 line 89 '现有 391 个 cli 测试不改' 残留，§2.2/§12/§13 已修；建议 hf-finalize 前 1 行清理（carry-forward）"
    },
    {
      "id": "F-6",
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "D6/A2",
      "status": "closed",
      "summary": "§14 OSError 失败模式明确退出码 1，与 spec § 4.1 三段式一致"
    },
    {
      "id": "F-7",
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "D6",
      "status": "closed",
      "summary": "§13 跨 pack 冲突测试矩阵行注明 fixture 临时构造，回链 §10.3 / ADR-D7-4"
    },
    {
      "id": "N-1",
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "D1/D6",
      "status": "open",
      "summary": "回归扫描发现 F-5 同源残留：§3 line 89 '391' 单数字与全文 ≥496 基线不一致；属 carry-forward，1 行机械替换"
    }
  ]
}
```

## 10. 结构化返回

```json
{
  "conclusion": "需修改",
  "next_action_or_recommended_skill": "hf-design",
  "record_path": "/workspace/docs/reviews/design-review-F007-garage-packs-and-host-installer.md",
  "key_findings": [
    "[important][LLM-FIXABLE][D1/D4] F-1 CON-701 字面违反：设计把 installer 子包放在 src/garage_os/installer/（与 adapter 平级），但 spec CON-701 (Must) 要求 'host_installer/ 子包仍应位于 src/garage_os/adapter/ 之下'；§6 候选 B 论证 'CON-701 可以通过 §5.1 满足' 是事实错误。建议机械搬位到 src/garage_os/adapter/installer/。",
    "[important][LLM-FIXABLE][D1/D5] F-2 §11.3 pack.json schema 缺 skills/agents 清单字段，且未规划 packs/<pack-id>/README.md，无法满足 FR-701 验收 #1 'Agent 仅读 pack.json + packs/README.md 就能回答 \"包含哪些 skill 名\"'，自描述链断裂。",
    "[important][LLM-FIXABLE][D2/D6] F-3 marker.inject 对 'agent.md 无 front matter' 在 §13（容错）与 §14（MalformedFrontmatterError 退出码 1）自相矛盾，hf-tasks 无法决定分支。",
    "[important][LLM-FIXABLE][D4] F-4 ASM-701 缓解措施要求 design 为每个 adapter 显式记录 path-pattern 来源链接；ADR-D7-3 仅对 Cursor 给了 OpenSpec 引用，Claude Code / OpenCode 的 .claude/skills、.claude/agents、.opencode/skills、.opencode/agent 路径无来源依据。",
    "[minor][LLM-FIXABLE][Q1/D6] F-5 测试基线 §2.2 / §3 NFR-704 写 391，§13 与 spec / task-progress 写 ≥496，数字内部不一致。",
    "[minor][LLM-FIXABLE][D6] F-6 §14 OSError 失败模式未声明退出码归属，与 spec § 4.1 三段式（0/1/2）不闭合。",
    "[minor][LLM-FIXABLE][D6] F-7 §13 跨 pack 冲突用例未注 '需 fixture 临时构造第 2 个 pack'（已在 §10.3 / ADR-D7-4 透明承认，仅缺 §13 引用）。"
  ],
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "finding_breakdown": [
    {
      "severity": "important",
      "classification": "LLM-FIXABLE",
      "rule_id": "D1/D4",
      "summary": "CON-701 字面偏离：installer 子包位置不在 src/garage_os/adapter/ 下，§6 候选 B 论证错误"
    },
    {
      "severity": "important",
      "classification": "LLM-FIXABLE",
      "rule_id": "D1/D5",
      "summary": "pack.json schema 缺 skills/agents 字段，无法满足 FR-701 验收 #1 自描述要求"
    },
    {
      "severity": "important",
      "classification": "LLM-FIXABLE",
      "rule_id": "D2/D6",
      "summary": "marker.inject 对 'agent.md 无 front matter' 在 §13 / §14 自相矛盾"
    },
    {
      "severity": "important",
      "classification": "LLM-FIXABLE",
      "rule_id": "D4",
      "summary": "ASM-701 缓解措施未承接：Claude Code / OpenCode adapter path-pattern 来源链接缺失"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "Q1/D6",
      "summary": "测试基线数字 391 vs 496 内部不一致"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "D6",
      "summary": "§14 OSError 失败模式退出码归属不明"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "D6",
      "summary": "§13 跨 pack 冲突用例未注 fixture 依赖（§10.3 / ADR-D7-4 已透明承认）"
    }
  ]
}
```
