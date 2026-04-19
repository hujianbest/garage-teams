# Spec Review — F007 Garage Packs 与宿主安装器

- 评审范围: `docs/features/F007-garage-packs-and-host-installer.md`（草稿，386 行）
- Review skill: `hf-spec-review`
- 评审者: cursor cloud agent (auto mode, reviewer subagent，由 `hf-specify` 父会话派发)
- 日期: 2026-04-19
- Workflow Profile / Mode / Isolation: `coding` / `auto` / `in-place`
- Branch: `main`
- 上游证据基线: `docs/features/F001-garage-agent-operating-system.md`、`docs/features/F005-garage-knowledge-authoring-cli.md`、`docs/features/F006-garage-recall-and-knowledge-graph.md`、`docs/soul/manifesto.md`、`docs/soul/design-principles.md`、`docs/soul/user-pact.md`、`docs/soul/growth-strategy.md`、`docs/principles/skill-anatomy.md`、`AGENTS.md`、`task-progress.md`、`src/garage_os/cli.py`、`src/garage_os/adapter/`、`packs/` 目录现状（不存在）

## 1. Precheck

| 检查项 | 结果 |
|--------|------|
| 存在稳定可定位 spec draft | ✓ `docs/features/F007-garage-packs-and-host-installer.md` 已落盘，结构完整 |
| route / stage / profile 已明确 | ✓ `task-progress.md` 显式 Stage=`hf-specify`、Profile=`coding`、Mode=`auto-mode`、Pending=`hf-spec-review` |
| 上游证据一致 | ✓ F001 `CON-002` 与 `packs/` 缺失现状一致；`src/garage_os/cli.py` `DEFAULT_PLATFORM_CONFIG` / `DEFAULT_HOST_ADAPTER_CONFIG` 存在；`src/garage_os/adapter/` 已是 host 抽象 home；`docs/principles/skill-anatomy.md` 与 spec § 6 FR-701 互相对齐 |

Precheck 通过，进入正式 rubric。

## 2. 结构契约判定

`AGENTS.md` 未声明强制 spec 模板；F005 / F006 已建立项目内事实模板（1 背景 → 2 目标/成功标准 → 3 角色/场景 → 4 范围 → 5 deferred → 6 FR → 7 NFR → 8 接口 → 9 约束 → 10 假设 → 11 开放问题 → 12 术语）。F007 草稿章节顺序与命名与基线高度一致；每条 FR 含 `优先级` / `来源` / `需求陈述` / `验收标准` 四字段，与 F005/F006 同构。结构契约 ✓ 不需要单独抓。

## 3. Rubric 评审

### 3.1 Group Q（Quality Attributes）

| ID | 检查 | 结论 | 备注 |
|---|---|---|---|
| Q1 Correct | 来源锚点是否真实 | ⚠ minor 漂移 | § 1.3 写 "`src/garage_os/cli.py:139` `DEFAULT_PLATFORM_CONFIG`、`:150` `DEFAULT_HOST_ADAPTER_CONFIG`"；实测行号为 133 / 148（差 5～6 行）。同 F006 round 1 F-2 同类问题。 |
| Q2 Unambiguous | 关键阈值是否量化 | ✓ | NFR-702 "≤ 2 秒"、FR-710 "5 分钟内回答出 3 个问题"、FR-705 `schema_version == 1` / SHA-256 / ISO-8601 都量化 |
| Q3 Complete | 输入/输出/错误/边界是否齐全 | ✓ | 覆盖 unknown host、空 packs、non-TTY、locally-modified、`--force`、同名 pack 冲突、agent surface = None 等多条负路径 |
| Q4 Consistent | 内部矛盾 | ⚠ important（见 finding F-1）+ minor（见 finding F-3） | FR-707 验收 #3 字面 `.claude/skills/hf-specify/SKILL.md` 与同 FR 末段 "spec 中**不**出现宿主特定路径硬编码" 自相矛盾；§ 4.1 把"标记块"放进"包含"表，但 FR-708 优先级 = Should |
| Q5 Ranked | 优先级齐全 | ✓ | 全 FR / NFR / CON / ASM 都标 Must/Should/Could |
| Q6 Verifiable | 验收可判定 | ✓ | 每条核心 FR 至少 2 条 BDD（部分 4 条），含 stdout marker / 字段断言 / 退出码 |
| Q7 Modifiable | 是否散落重复 | ✓ | scoring/退出码/manifest schema 各自集中在一处 |
| Q8 Traceable | 来源是否可冷读 | ✓ | 每条 FR / NFR / CON / ASM 均带显式 Source（用户请求 / § 内引 / soul 文档 / 调研参考） |

### 3.2 Group A（Anti-Patterns）

| ID | 检查 | 结论 | 备注 |
|---|---|---|---|
| A1 模糊词 | ✓ | "几秒后" 出现在 § 1 摩擦叙事里，不进入 FR；NFR-702 给了 ≤ 2s 上限 |
| A2 复合需求 | ⚠ minor（见 finding F-4） | FR-706 单条同时承接 hash 比对基础设施 + 未修改自动重写 + 已修改默认跳过 + `--force` 覆盖；可控但接近 GS3 |
| A3 设计泄漏 | ⚠ important（与 F-1 同条） | FR-707 statement 写进 `target_skill_path(skill_id) -> Path`、`target_agent_path(agent_id) -> Optional[Path]`、`render(content) -> content` 三个具体函数签名 + 返回类型注解；这是 design 层契约。spec 层应表达 "必须暴露 skill/agent 目标路径查询能力"，不应固化 Python 类型签名 |
| A4 无主体被动 | ✓ | 所有 FR 都以 "系统必须 ..." 起头，触发条件清晰 |
| A5 占位/TBD | ✓ | "由 design 阶段决定" 类延后均显式（FR-707 字面值 / FR-708 标记块形式 / OQ-601~604），不是 TBD |
| A6 缺少负路径 | ✓ | unknown host、locally modified skip、`--force` 覆盖、同名 pack 冲突（退出码 2）、空 packs、non-TTY 退化全覆盖 |

### 3.3 Group C（Completeness And Contract）

| ID | 检查 | 结论 | 备注 |
|---|---|---|---|
| C1 Requirement contract | ✓ | 全 10 条 FR + 4 条 NFR + 4 条 CON + 3 条 ASM 均有 ID/Statement/Acceptance/Priority/Source；EXC 收敛在 § 5 表 |
| C2 Scope closure | ✓ | § 4.1 包含表 + § 4.2 关键边界 + § 4.3 与 F001-F006 边界 + § 5 deferred 表四层闭合 |
| C3 Open-question closure | ✓ | § 11 显式声明阻塞性 = 0；候选阻塞项（first-class host 集合 / `--global` 模式）都已在 § 4.1 / § 5 内主动收敛，不应升级为阻塞（见 § 4 verdict 解释） |
| C4 Template alignment | ✓ | 与 F005/F006 同构，章节顺序、front matter 字段一致；遵循 `docs/principles/skill-anatomy.md`（pack 内 skill anatomy） |
| C5 Deferral handling | ✓ | § 5 表 7 行，每行有 Reason + 期望落点（F008 候选 / Stage 3+ 候选 / 单独探索性候选） |
| C6 Goal/Success criteria | ✓ | § 2.2 7 条 SC 全部具体可判定（"零配置可演示"含具体命令、"幂等"含 hash 比较口径、"零回归" pin 到 ≥496 测试基线） |
| C7 Assumption visibility | ✓ | § 10 三条 ASM 均带 失效风险 + 缓解措施；ASM-701 直指三宿主 surface 稳定性，缓解中给出 design 阶段补 path-pattern 来源链接 |

### 3.4 Group G（Granularity And Scope-Fit）

| ID | 检查 | 结论 | 备注 |
|---|---|---|---|
| G1 Oversized FR | ⚠ minor（见 finding F-4） | FR-706 是边界值；其余 FR 验收数量在 2-4 条间，未命中 GS3 必拆阈值 |
| G2 Mixed release boundary | ✓ | § 5 显式分流 F008 / Stage 3+；本轮 FR 不混后续 cycle |
| G3 Repairable scope | ✓ | 1 important + 3 minor 全 LLM-FIXABLE，1 轮定向回修可闭合 |

## 4. 发现项

- [important][LLM-FIXABLE][Q4][A3] **F-1** FR-707 内部矛盾且夹带 design 决策。验收 #3 写 `Path(".claude/skills/hf-specify/SKILL.md")` 字面值作为期望返回，但同 FR 末段又说"其值在 `packs/` 与本 spec 中**不**出现宿主特定路径硬编码"——两者直接打架。同时 statement 显式钉死三个 Python 函数签名（含参数名、返回类型注解），属于 design HOW。建议二选一：(a) 删除验收 #3 的字面路径，改为"返回值必须是 host adapter 自有 skills 子目录下、相对于项目根的 `Path`，具体值由 design 决定"；并把 statement 的 (a)/(b)/(c) 弱化为"必须暴露 'skill 目标路径' 与 'agent 目标路径'（后者可选）查询能力"。可在不改本轮 scope/优先级前提下定向修订（与 `granularity-and-deferral.md` Mechanical Vs Scope-Shaping Split 中"只改表达，不改范围"判定一致）。
- [minor][LLM-FIXABLE][Q1] **F-2** § 1.3 第 3 段引用 "`src/garage_os/cli.py:139` `DEFAULT_PLATFORM_CONFIG`、`:150` `DEFAULT_HOST_ADAPTER_CONFIG`"，实测行号为 133 / 148（已用 Read 校验）。建议改为按符号定位（与 F006 round 2 闭合 F-2 同样的稳健写法）："见 `src/garage_os/cli.py` 顶层 `DEFAULT_PLATFORM_CONFIG.host_type` 与 `DEFAULT_HOST_ADAPTER_CONFIG.host_type` 字面赋值 `\"claude-code\"`"。
- [minor][LLM-FIXABLE][Q4] **F-3** § 4.1 "包含" 表把"标记块"列入本 cycle 实施项，但 FR-708 优先级 = Should（而非 Must），形成 wording 不一致。建议要么把 FR-708 升为 Must（与 § 4.1 表一致），要么在 § 4.1 表的 "标记块" 行加 "(Should，参 FR-708)" 注解。需 author 选择，但任一选项都不改变本轮 scope。
- [minor][LLM-FIXABLE][G1][GS3] **F-4** FR-706 单条 FR 在 statement 内同时承接 (a) hash 比对基础设施 + (b) 未修改自动重写 + (c) 已修改默认跳过 + (d) `--force` 覆盖路径，验收 4 条且其中第 4 条 "新增 host 追加" 又跨入 FR-704 域。可考虑拆为 FR-706a（content_hash 比对 + 未修改重写）+ FR-706b（已修改默认跳过 + `--force` 覆盖）+ 把第 4 条移入 FR-704 验收。属优化建议，不强求；保留单条也能落地。

## 5. 缺失或薄弱项

- **薄弱（非阻塞）**：FR-704 验收 #4 用同名 skill 跨 pack 冲突时"退出码 2"作为 hard fail，但 § 5 deferred 已把"`packs/` 子目录是单一 `garage` 还是 `coding/product-insights` 等多 pack" 留到 design 决定（OQ-604）。若 design 选择"本 cycle 收敛单一 pack"，该验收路径在本 cycle 内无法被自然触发。建议 design 阶段澄清后回填一个最小可观察 fixture（例如临时新增第 2 个 pack 仅用于回归测试）。属 design 层正常工作，不阻塞 spec。
- **薄弱（非阻塞）**：FR-705 manifest schema 定为 `schema_version: 1` 并由 CON-703 接入 `VersionManager`，但 spec 未在 § 8 / § 9 显式声明"该 schema 与 `host-adapter.json` `schema_version` 之间是否独立演进"。属 design 层正常工作。
- **观察**：用户提示中关注的两条候选阻塞项（首类宿主集合是否包含 codex/gemini/windsurf；是否引入 `--global` 模式）均已在 § 4.1 / FR-707 / § 5 deferred 表显式收敛，**不应当**升级为阻塞 finding。reviewer 判定已足够 close。

## 6. 结论

**需修改**

判断依据：
- 0 条 critical
- 1 条 important（FR-707 内部矛盾 + API 签名设计泄漏，LLM-FIXABLE）
- 3 条 minor（行号漂移、§ 4.1 表 vs FR-708 优先级 wording、FR-706 复合可拆）
- 全部 finding 为 LLM-FIXABLE，预期 1 轮定向回修可达标
- 范围、scope 边界、deferred 处理、success criteria、assumptions、阻塞性开放问题闭合度均通过
- 满足 rubric "有用但不完整，findings 可 1-2 轮定向修订" → `需修改`

不满足 `通过` 的核心理由：FR-707 的自相矛盾 + API 签名固化属于 important 级 Q4/A3，会污染 design 阶段的判断空间（design reviewer 会被迫先解释这条矛盾），应先修订再进入 approval。

不应判 `阻塞`：核心范围、关键业务规则（packs 契约 / 安装管道 / extend mode / manifest schema / 三宿主集合）都已稳定；findings 全部可在 author 不获取新外部事实的前提下闭合。

## 7. 下一步

- **`hf-specify`**：父会话回到 `hf-specify` 启动 r2，定向修订上述 4 条 finding（重点 F-1）。
- 不需要 USER-INPUT 问卷（finding 全部 LLM-FIXABLE）。
- 不需要 reroute via router。

## 8. 交接说明

- `hf-specify`：本轮唯一下一步。author 节点应只对 4 条 finding 做定向修订，不重写其他章节；修订完成后再次派发 `hf-spec-review` 做 r2 delta 校验。
- 父会话向真人的摘要建议（≤ 2 句 plain language，不贴 rubric）：**"F007 spec 草稿大方向稳，结构、scope、deferred、success criteria 都过关；需要 1 轮定向修订主要解决 FR-707 自相矛盾 + API 签名硬编码（important）以及 3 条 wording/锚点 minor。无需要你裁决的业务问题。"**
- 父会话不开始 `hf-design`，等 r2 review 通过后由 approval step 触发。

## 9. 结构化返回

```json
{
  "conclusion": "需修改",
  "next_action_or_recommended_skill": "hf-specify",
  "record_path": "/workspace/docs/reviews/spec-review-F007-garage-packs-and-host-installer.md",
  "key_findings": [
    "[important][LLM-FIXABLE][Q4][A3] FR-707 内部矛盾：验收 #3 字面 .claude/skills/hf-specify/SKILL.md 与同 FR 末段 'spec 中不出现宿主特定路径硬编码' 直接打架；statement 还固化了 target_skill_path / target_agent_path / render 三个 Python 函数签名（含返回类型注解），属 design HOW 泄漏。",
    "[minor][LLM-FIXABLE][Q1] § 1.3 引用 cli.py:139 / :150，实际行号为 133 / 148；建议改为按符号定位（同 F006 r2 F-2 修法）。",
    "[minor][LLM-FIXABLE][Q4] § 4.1 包含表把'标记块'列入本 cycle 实施项，但 FR-708 优先级 = Should，wording 不一致。",
    "[minor][LLM-FIXABLE][G1][GS3] FR-706 复合承接 hash 比对 + 未修改重写 + 已修改跳过 + --force 覆盖 + 新增 host 追加 5 件事，可考虑拆为 706a/706b 并把'新增 host 追加'移入 FR-704。"
  ],
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "finding_breakdown": [
    {
      "severity": "important",
      "classification": "LLM-FIXABLE",
      "rule_id": "Q4/A3",
      "summary": "FR-707 自相矛盾且固化 Python 函数签名（design 泄漏）"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "Q1",
      "summary": "§ 1.3 cli.py 行号锚点漂移（139/150 → 133/148）"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "Q4",
      "summary": "§ 4.1 包含表与 FR-708 Should 优先级 wording 不一致"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "G1/GS3",
      "summary": "FR-706 单条承接 5 件事接近 oversized 边界，可拆"
    }
  ]
}
```
