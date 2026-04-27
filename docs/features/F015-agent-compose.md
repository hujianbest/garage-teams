# F015: Agent Compose — `garage agent compose` 半自动产 agent.md 草稿

- **状态**: 草稿 r2 (回应 spec-review-F015-r1; 2 critical + 2 important + 4 minor + 1 nit 全部闭合; 待 r2 hf-spec-review)
- **主题**: F011 落了 3 个手写 production agent (`code-review-agent` / `blog-writing-agent` / `garage-sample-agent`); 但 `growth-strategy.md § Stage 3 第 67 行` "Skills 可组合成专用 agents" 当前是**半交付** — agent.md 仍手写, 无 compose 路径. F015 加 `garage agent compose <name> --skills <list>` CLI: 用户给一组 skill_ids + 一段意图, 系统自动从 SKILL.md 内容提取 + 用户的 KnowledgeType.STYLE entries 提取, 半自动产出 agent.md 草稿到 `packs/<target-pack>/agents/<name>.md`. 与 F013-A skill mining 同 pattern (template generator + half-automatic promote), 但是 agent 级别而非 skill 级别.
- **日期**: 2026-04-26
- **关联**:
  - vision-gap 答疑 (post-F014): § 6 P1-1 "Agent 自动组装" Stage 3 最后一项未交付
  - growth-strategy.md § Stage 3 第 67 行 "Skills 可组合成专用 agents (如 '代码审查 agent'、'博客写作 agent')" — F011 形式上交付 (3 个 agent), 但 compose 路径未做 (当前所有 agent.md 是手写)
  - F011 — 3 个 production agent 既有, 是 compose template 的 reference
  - F013-A — SkillSuggestion + Template Generator pattern 复用
  - F014 — recall workflow 提供 "用户经常一起用哪些 skill" 数据 (供 compose 默认 skill 列表建议; 但**不依赖**, F015 可独立运行)
  - F006 — `garage knowledge search` 找 STYLE entries (compose 时拉用户风格)
  - F008 — `packs/<id>/agents/<name>.md` 目录契约 (写出端)
  - manifesto B4 "人机共生" + Stage 3 工匠
  - user-pact (5) "你做主": 所有自动化都有开关; compose 必须 opt-in
  - 调研锚点 (基于 main `f5950b4` 实际代码; F015 base on F014 branch `cursor/f014-workflow-recall-bf33`):
    - F011 agent.md schema reference subset (Cr-2 r2 收窄): F015 模板参考限 **2 个** agent — `packs/garage/agents/blog-writing-agent.md` (42 行) + `packs/garage/agents/code-review-agent.md` (39 行); 都含 frontmatter `name` + `description` + sections "When to Use" / "How It Composes" / "Workflow". `packs/garage/agents/garage-sample-agent.md` (11 行) 是 F008 安装/容错样本 (FR-708 路径), **无** YAML front matter, 章节为 `## 行为` / `## Notes`; F015 显式**排除**该 agent 出 CON-1504 模板参考集.
    - F013-A SkillSuggestion + template_generator pattern: `src/garage_os/skill_mining/{types,template_generator,suggestion_store}.py`
    - F006 KnowledgeStore.list_entries: 用 `KnowledgeType.STYLE` filter 获取风格偏好
    - F004 KnowledgeEntry schema: `src/garage_os/types/__init__.py:102-121` 含 `topic / tags / content / front_matter`
    - F008 packs/ 目录契约: `packs/<pack-id>/agents/<name>.md` (与 skills/ 平级)
    - skill SKILL.md 内容: 每个 SKILL.md 起首 frontmatter `description` 是 compose 时引的 skill 简介源
    - F011 既有参考 agent.md 长度 (Mi-1 r2 修订): blog-writing 42 行 + code-review 39 行; 100-150 字 description, 4-5 sections

## 1. 背景与问题陈述

post-F014 vision-gap 显示, growth-strategy.md § Stage 3 工匠核心新增的第 2 行 (§ 56-69 行) **"Skills 可组合成专用 agents (如 '代码审查 agent'、'博客写作 agent')"** 处于半交付状态:

> 核心新增:
> - ✅ 重复模式自动识别并建议为 skill 模板 (F013-A skill mining)
> - ⚠️ **Skills 可组合成专用 agents** (F011 半交付; agent.md 手写) ← F015 目标
> - ✅ 工作流编排从手动变成半自动 (F014 workflow recall)

### 1.1 当前断点 (post-F014)

```
用户想做新 agent (例 "config-design-agent" 组合 hf-specify + hf-design + ...)
  ↓
手动 vim packs/garage/agents/<name>.md
手动写 frontmatter + 4-5 sections + 引 skill 关联
手动想 description 怎么写 (≥ 50 字, 边界显式)
  ↓
F011 production agents 3 个全是这样手写出来的 (没有 compose 路径)
```

ExperienceIndex / KnowledgeStore 已有大量 STYLE entries + skill 调用历史 + (post-F014) workflow 路径数据, 但 `garage agent compose` 不存在. 用户必须从零写 agent.md.

### 1.2 真实摩擦量化

- F011 写 3 个 agent 各花 ~30-60 min 人工 (frontmatter + How It Composes + Workflow + 边界描述)
- 用户在第 4 个 agent 时通常会复制粘贴 F011 既有, 容易忘掉某项 (例 description 的 "不适用" 段)
- skill_ids 序列重复模式 (F014 已能识别) 没有自动建议为 agent compose 起步点
- 当前 packs/garage/agents/ 仅 3 个 agent, 假如用户给 5 skill 想做新 agent, **没有任何 garage 帮助路径**

→ **F015 的核心承诺**: `garage agent compose <name> --skills s1,s2,s3 [--target-pack <id>]` 自动产 agent.md 草稿: 读各 skill 的 frontmatter description + 用户 STYLE entries → 拼装成符合 F011 既有 agent.md schema 的草稿 → 半自动 promote 到 `packs/<target>/agents/<name>.md` (用户 prompt 确认 + --yes 跳过).

### 1.3 与 user-pact "你做主" 的边界

F015 不会:
- 自动 commit 任何 agent.md 到 packs/ 之外用户路径
- 自动改 packs/<pack-id>/pack.json (`agents[]` 列表; 与 F013-A `--reject 不动 pack.json` 同精神, INV-F15-3)
- 删除既有 agent.md (即使 compose 同名也 prompt overwrite)

F015 只会:
- 读 SKILL.md frontmatter (read-only)
- 读 KnowledgeStore.list_entries(KnowledgeType.STYLE) (read-only)
- 在用户显式 `--yes` / interactive 同意时, 写 agent.md 到 packs/<target>/agents/<name>.md
- 写 `.garage/agent-compose/cache.json` (compose 结果的元数据 + 历史)

## 2. 目标与成功标准

### 2.1 范围

**A. Agent Compose Engine** (FR-1501):
- 在 `src/garage_os/agent_compose/` 顶级包内实现 `AgentComposer`
- 输入: agent_name (例 "config-design-agent") + skill_ids list (例 ["hf-specify", "hf-design", "hf-tasks"]) + 可选 description 提示 + 可选 --target-pack (默认 "garage")
- 输出: agent.md 草稿 string (in-memory, 与 F013-A template_generator pattern 同精神)
- 模板 schema 严格遵 F011 既有 agent.md 格式 (Cr-2 r2: 参考 2 个 agent — `blog-writing-agent.md` + `code-review-agent.md`; **不参考** `garage-sample-agent.md` 的简化 schema): frontmatter `name` + `description` 含适用/不适用; sections "When to Use" / "How It Composes" / "Workflow"
- description 自动拼: "适用于 <agent_name>...组合 <skills>...不适用于 <inferred 边界>" (≥ 50 字, 与 F013-A skill template 同 INV-F13-4 精神)
- "When to Use" 段从每个 skill 的 SKILL.md frontmatter description 抽前半段 (用户场景部分) 拼接
- "How It Composes" 段列出每个 skill 的角色 (基础/风格/可选 — 启发式标注, 用户可改)
- "Workflow" 段列出 skill 调用顺序 (按用户给的 skill_ids 顺序)

**B. STYLE Entries 集成** (FR-1502):
- 读 `KnowledgeStore.list_entries(knowledge_type=KnowledgeType.STYLE)` (Mi-2 r2 完整 API 签名; F011 既有)
- compose 时附 "## Style Alignment" section 列出相关 STYLE entries 的 topic + ID
- 默认 include all STYLE entries; `--no-style` flag 禁用 (用户可关)
- 阈值: 0 STYLE entry 时跳过 Style Alignment section, 用 placeholder TODO

**C. `garage agent compose <name>` CLI** (FR-1503):
- `garage agent compose <name> --skills <s1,s2,s3> [--target-pack X] [--description <text>] [--yes] [--dry-run] [--no-style]`
- 默认 `--target-pack` = "garage" (与 F011 既有 agents 同位置)
- `--description` 用户可显式提供 (覆盖自动拼装)
- `--dry-run` 显示 preview, 不写
- `--yes` 跳过 prompt
- 同名 agent 已存在 → prompt overwrite y/N (除 --yes; 与 F013-A skill promote 同精神)

**D. `garage agent ls` CLI** (FR-1504):
- `garage agent ls [--target-pack X]`
- 列 packs/<target>/agents/*.md 的 frontmatter `name` + `description` (前 80 字)
- 默认 list `packs/garage/agents/`; --target-pack 切换

**E. Audit & Sentinels** (FR-1505):
- INV-F15-1: AgentComposer 是 read-only 在 SKILL.md + KnowledgeStore (不写不删 既有 skill)
- INV-F15-3 sentinel: compose 不动 packs/<id>/pack.json `agents[]` 列表 (用户在确认 agent.md 满意后自己 update; 与 F013-A CON-1304 同精神)
- INV-F15-5 sentinel: 既有 F011 production agents (3 个) byte 不变 (compose 是 sibling, 不修改既有; Cr-1 r2 守门; BDD 8.4 的 overwrite 验收使用 `demo-overwrite-agent` 而非任一 F011 agent)
- `garage status` 加 agent-compose 段: "Agent compose: <pack> has N agents" (Im-2 r2 修订: 删除 last compose ts 提纲, 不依赖 cache.json)

### 2.2 范围内变化

- 新模块 `src/garage_os/agent_compose/`:
  - `types.py`: `AgentDraft` dataclass + `ComposeResult`
  - `template_generator.py`: agent.md 草稿生成 (与 F013-A template_generator 同 pattern)
  - `composer.py`: 主 compose 逻辑 (读 SKILL.md + STYLE entries + 拼装)
  - `pipeline.py`: 端到端 + status summary
- 新 CLI subcommand: `garage agent compose` + `garage agent ls`
- `garage status` 加 agent-compose 段
- 新 .garage 目录: `.garage/agent-compose/cache.json` (compose 历史; 不必要但便于 debug)
- platform.json schema: `agent_compose.enabled: bool` (默认 true; 与 F013-A / F014 同 pattern)

### 2.3 范围外 (Out of scope)

- 不做 agent 自动选 skills (例 "你常用这 5 个 skill, 推荐组成 agent X") — 那是 F014 recall + F013-A skill mining 进一步组合, 推 F016+
- 不做 agent.md 自动注册到 pack.json `agents[]` (CON-1503 守门; 用户用 hf-test-driven-dev 路径自己加)
- 不做 agent 运行时执行 (manifesto 显式 "Garage 是能力层, 不做 Agent 运行时")
- 不做 cross-pack agent compose (默认 garage; 用户可 --target-pack 切但不并发多 pack)
- 不修改 F011 既有 3 个 production agents (INV-F15-5)
- 不动 F003-F014 既有 API + schema

## 3. 功能需求 (FR)

### FR-1501: Agent Compose Engine (Ubiquitous)

| 字段 | 值 |
|---|---|
| **触发** | (a) `garage agent compose <name> --skills ...` CLI 调用 |
| **输入** | agent_name (str, kebab-case) + skill_ids (list[str]; 必须存在于至少一个 packs/<id>/skills/) + description override (Optional[str]) + target_pack (default "garage") + include_style (bool, default True) |
| **输出** | `ComposeResult(draft: AgentDraft, missing_skills: list[str], style_count: int)` |
| **验证** | (a) skill_ids 中所有 skill 必须存在于 packs/*/skills/<skill>/SKILL.md (找不到的进 missing_skills; Im-1 r2: library 仍生成 draft 给未来其他调用方; CLI exit 1); (b) target_pack 必须存在于 packs/<id>/; (c) agent_name 必须 kebab-case (a-z, 0-9, hyphen) |
| **draft 内容** | frontmatter (name, description ≥ 50 字 含适用/不适用) + ## When to Use + ## How It Composes + ## Workflow + ## Style Alignment (若 include_style=True 且有 STYLE entries) |
| **BDD** | Given: skill_ids=["hf-specify", "hf-design"], target_pack="garage"; When: compose; Then: AgentDraft 含 frontmatter name="<input-name>" + description 含 "组合 hf-specify, hf-design"; "How It Composes" 列 2 个 skill |
| **Edge** | skill_ids 含不存在 skill → library `ComposeResult.missing_skills` 含 + draft 含 placeholder (供未来其他调用方按需用部分 draft); target_pack 不存在 → ValueError; 0 skill_ids → ValueError. **CLI 层 (FR-1503) 严格**: missing skill > 0 → exit 1 不写盘 (Im-1 r2 双层语义) |

### FR-1502: STYLE Entries 集成 (State-driven)

| 字段 | 值 |
|---|---|
| **触发** | compose 时, 若 include_style=True 且 KnowledgeStore.list_entries(knowledge_type=KnowledgeType.STYLE) 非空 |
| **API** | `KnowledgeStore.list_entries(knowledge_type=KnowledgeType.STYLE)` (Mi-2 r2 完整签名; F011 既有, `knowledge_store.py` L229-237) |
| **draft 内容** | "## Style Alignment" section 列出每个 STYLE entry 的 `topic` + `id` (前 6 个; 多余的省略 + "see all via `garage knowledge list --type style`") |
| **--no-style flag** | 跳过该 section |
| **BDD** | Given: 3 STYLE entries (topic "prefer functional Python", "type hints required", "no class-based"); When: compose --skills hf-specify; Then: draft "## Style Alignment" 列 3 个 entry topic |
| **Edge** | 0 STYLE entry → section 用 placeholder TODO; --no-style → section 不生成 |

### FR-1503: `garage agent compose <name>` CLI (Event-driven)

| Sub-command | 行为 |
|---|---|
| `garage agent compose <name>` | 报错 "--skills required (at least one)" |
| `garage agent compose <name> --skills s1,s2,s3` | 默认 target_pack=garage; interactive prompt + preview; y → 写 |
| `garage agent compose <name> --skills s1 --target-pack X` | 切换目标 pack |
| `garage agent compose <name> --skills s1 --description "..."` | 覆盖默认 description (≥ 50 字校验) |
| `garage agent compose <name> --skills s1 --no-style` | 跳过 STYLE Alignment section |
| `garage agent compose <name> --skills s1 --dry-run` | 仅显 preview, 不写 |
| `garage agent compose <name> --skills s1 --yes` | 跳过 prompt |
| 同名 agent 已存在 | prompt overwrite y/N (除 --yes); 与 F013-A skill promote 同精神 |

| BDD | Given: target packs/garage/agents/ 有 3 个 agent; When: `garage agent compose new-agent --skills hf-specify --yes`; Then: packs/garage/agents/new-agent.md 创建 + stdout "Created agent at packs/garage/agents/new-agent.md" + 提示 "manually update packs/garage/pack.json agents[]" |
| Edge | --skills 中含不存在 skill → exit 1 + stderr 列 missing skills; agent_name 含 invalid chars → exit 1 |

### FR-1504: `garage agent ls` CLI (Event-driven)

| Sub-command | 行为 |
|---|---|
| `garage agent ls` | 默认 target packs/garage/; 列 frontmatter name + description (前 80 字) |
| `garage agent ls --target-pack X` | 切换目标 pack; 不存在 → exit 1 + stderr |

| BDD | Given: packs/garage/agents/ 含 3 个 agent (F011); When: `garage agent ls`; Then: stdout 3 行 agent name + description |
| Edge | 空 agents/ 目录 → "No agents in pack 'garage'" |

### FR-1505: `garage status` 集成 + Sentinels (State-driven)

| 触发 | 每次 `garage status` 调用 |
| 显示 | "Agent compose: <pack> has N agents" (始终显, RSK-1501 兜底; Im-2 r2 修订: 不带 last compose ts 后缀, 不依赖 cache.json) |

| BDD | Given: packs/garage/agents/ 含 3 agent; When: `garage status`; Then: stdout 末尾含 "Agent compose: garage has 3 agents" |

## 4. 不变量 (INV)

| ID | 描述 |
|---|---|
| **INV-F15-1** | AgentComposer 是 read-only 在 SKILL.md + KnowledgeStore (不写不删既有 skill / knowledge entry; 仅写 packs/<target>/agents/<name>.md + .garage/agent-compose/) |
| **INV-F15-2** | F015 不写文件到 packs/<target>/agents/ + .garage/agent-compose/ + (compose 时若 platform.json 不存在则) .garage/config/platform.json 字段级 之外 |
| **INV-F15-3** | compose 不动 packs/<target>/pack.json `agents[]` 列表 (与 F013-A CON-1304 同精神; 用户用 hf-test-driven-dev 路径自己加) |
| **INV-F15-4** | F003-F014 既有 API + schema 字节级不变 (新 AgentDraft / ComposeResult 是 sibling type) |
| **INV-F15-5** | F011 既有 3 个 production agent (`code-review-agent.md` / `blog-writing-agent.md` / `garage-sample-agent.md`) byte 不变 (compose 是新建路径, 不修改既有) |

## 5. 约束 (CON)

| ID | 描述 |
|---|---|
| **CON-1501** | F003-F014 既有 API + schema 字节级不变 |
| **CON-1502** | 零依赖变更 (`pyproject.toml + uv.lock` diff = 0); 全 stdlib (json / re / pathlib / dataclasses) |
| **CON-1503** | compose 不动 packs/<target>/pack.json (INV-F15-3); echo 提示用户手动 update + 走 hf-test-driven-dev 路径 |
| **CON-1504** | agent.md 模板严格遵 F011 既有 schema (frontmatter name + description + 4-5 sections); description ≥ 50 字 (skill-anatomy 原则 1 推广到 agent) |
| **CON-1505** | `garage agent compose / ls` 与 F006 recommend / F014 recall workflow / F013-A skill suggest 完全独立 (sibling subcommands; 不混路径) |

## 6. 假设 (HYP)

| ID | 描述 |
|---|---|
| **HYP-1501** | 用户的 .garage/knowledge/style/ 已有 STYLE entries (如本仓库 dogfood 当前为空, 但其他用户 dogfood 后会有). compose 在空 STYLE 时仍可工作, 仅 Style Alignment section 用 placeholder |
| **HYP-1502** | F011 既有 3 个 agent 的 schema (frontmatter + 4-5 sections) 是 production agent 的稳定模板. F015 compose 直接用此 schema; 未来如有 schema 演进 (例 agent.md 加 NFR section), F015 r2+ 同步更 |
| **HYP-1503** | 用户接受 "compose + 半自动" 模式 (与 F013-A skill mining 同). compose 后用户走 hf-test-driven-dev 路径 refine + 手动 update pack.json |
| **HYP-1504** | description 自动拼装质量 ≥ 用户手写 baseline 60% (足以省 50% 起步时间; 与 F013-A HYP-1302 同精神) |

## 7. 风险 (RSK)

| ID | 描述 | 缓解 |
|---|---|---|
| **RSK-1501** | 0 agent 时用户感觉 "系统没工作" | `garage status` 始终显 "Agent compose: <pack> has N agents" 即使 N=0 (与 F013-A skill mining status / F014 workflow recall status 同模式) |
| **RSK-1502** | 自动拼装的 description 质量浅 (只是 skill name 拼接) | 草稿明确标 "AI-generated draft, refine via hf-test-driven-dev" 在 frontmatter 后注释; 用户可 --description 自己写; 与 F013-A skill template 同精神 |
| **RSK-1503** | 用户 compose 同名 agent 误覆盖既有 | prompt overwrite y/N (除 --yes); --dry-run 显示 "would overwrite existing"; 与 F013-A skill promote 同精神 |
| **RSK-1504** | compose 后忘记 update pack.json `agents[]` | echo 提示 "Created agent at X. Manually update packs/<target>/pack.json agents[] to register" + AGENTS.md 文档化; 与 F013-A skill promote 同模式 |
| **RSK-1505** | F011 既有 agent.md schema 未来变 (例如加 NFR section) → F015 模板过时 | INV-F15-5 守门 (既有 byte 不变); F015 只看当前 F011 schema; schema 演进时 F015 r2+ 同步; 在 spec / design 显式标注 |

## 8. 验收 BDD (Acceptance)

### 8.1 Happy Path: 3 skill 组合 + 2 STYLE entries

```
Given:
  packs/coding/skills/{hf-specify, hf-design, hf-tasks}/SKILL.md exist
  KnowledgeStore.list_entries(STYLE) 返回 2 个 entries:
    {topic: "prefer functional Python", id: "k-001", ...}
    {topic: "type hints required", id: "k-002", ...}
  packs/garage/agents/ 不含 "config-design-agent.md"

When:
  garage agent compose config-design-agent --skills hf-specify,hf-design,hf-tasks --yes

Then:
  packs/garage/agents/config-design-agent.md 创建, 内容包括:
  - frontmatter: name=config-design-agent, description ≥ 50 字 含 "适用于" + "不适用于"
  - "## When to Use" 段含 3 个 skill 的场景描述
  - "## How It Composes" 段列 3 个 skill 角色
  - "## Workflow" 段列 3 个 skill 调用顺序
  - "## Style Alignment" 段含 2 entries (topic + id)
  stdout 含 "Created agent at packs/garage/agents/config-design-agent.md"
  stdout 含 "Manually update packs/garage/pack.json agents[] to register"
  packs/garage/pack.json bytes 不变 (CON-1503 ✓)
```

### 8.2 Empty STYLE + --no-style

```
Given:
  KnowledgeStore.list_entries(STYLE) 返回 []
When:
  garage agent compose new-agent --skills hf-specify --yes
Then:
  draft 含 "## Style Alignment" with placeholder TODO

Given (alt): 5 STYLE entries
When: garage agent compose new-agent --skills hf-specify --no-style --yes
Then: draft 不含 "## Style Alignment" section
```

### 8.3 Missing skill

```
Given: skill "nonexistent-skill" 不在 packs/*/skills/
When: garage agent compose x --skills hf-specify,nonexistent-skill --yes
Then: exit 1 + stderr 含 "Missing skills: nonexistent-skill"
And: packs/garage/agents/x.md 不创建
```

### 8.4 Overwrite prompt (Cr-1 r2: 改用 demo-overwrite-agent 而非 F011 既有 agent, 避免与 INV-F15-5 冲突)

```
Given: packs/garage/agents/demo-overwrite-agent.md 已先 compose 一次存在
  (注: 不用 code-review-agent.md / blog-writing-agent.md / garage-sample-agent.md
   因为 INV-F15-5 守 F011 既有 3 个 agent byte 不变)

When: garage agent compose demo-overwrite-agent --skills hf-specify (interactive, y)

Then: prompt "WARNING: packs/garage/agents/demo-overwrite-agent.md already exists. Overwrite? [y/N]"
  y → overwrite + stdout "Created agent at..."
  n → cancel + stdout "Cancelled"

INV-F15-5 验证: 跑完后 `git diff packs/garage/agents/code-review-agent.md packs/garage/agents/blog-writing-agent.md packs/garage/agents/garage-sample-agent.md` 应为空 (3 个 F011 agent byte 不变)
```

### 8.5 `garage agent ls` + `garage status`

```
Given: packs/garage/agents/ 含 3 agent (F011)
When: garage agent ls
Then: stdout 3 行 agent name + description (前 80 字)

When: garage status
Then: stdout 末尾含 "Agent compose: garage has 3 agents"
```

## 9. 实施分块预览 (草拟; 真正分块由 hf-tasks 决定)

| 任务 | 描述 | 复用 |
|---|---|---|
| **T1** | `agent_compose/{__init__, types.py, template_generator.py}` (AgentDraft + ComposeResult + agent.md template) + 8 测试 | F013-A skill_mining/template_generator pattern |
| **T2** | `agent_compose/composer.py` (主 compose 逻辑: 读 SKILL.md + STYLE entries + 校验 + 生成 draft) + 12 测试 | F013-A SkillMining + F011 既有 agent.md schema reference |
| **T3** | CLI `garage agent compose` + `garage agent ls` + `garage status` 集成 + `pipeline.py` (compose history cache, optional) + 10 测试 | F013-A CLI skill suggest/promote + F011 既有 agents/ 目录 |
| **T4** | AGENTS / RELEASE_NOTES + manual smoke + 4 sentinel (INV-F15-5 既有 agent byte / CON-1503 pack.json byte / CON-1502 零依赖 / CON-1505 sibling) | F013-A AGENTS section + F012 RELEASE_NOTES pattern + F013-A CON-1304 byte sentinel |

预估增量测试: ~34 (基线 main `f5950b4` snapshot + F014 +54 = 1043; F015 实施完成预计 +34 → ~1077 passed; 实施前再核 `uv run pytest` 因 F015 base 在 F014 branch 而非 main)

## 10. 与 vision 的对照

| 维度 | F015 推动后 |
|---|---|
| **Stage 3 工匠** | ~95% → **~100%** (估算; agent compose 闭环 — Mi-4 r2 注: 量化依据见 vision-gap 答疑 + growth-strategy.md § Stage 3 三项核心新增已全交付) |
| **Stage 4 生态** | 40% (维持; F015 不动生态) |
| **B4 人机共生** | 5/5 (维持; F015 是 B4 的进一步具象化) |
| **growth-strategy.md § Stage 3 第 67 行** | ⚠️ 半交付 → ✅ (vision 上 F015 唯一闭环条目) |

## 11. 测试基线

F015 base on F014 branch (PR #38 还没 merge 时) — 实际基线由 tasks 阶段实施前 `uv run pytest tests/ -q --ignore=tests/sync/test_baseline_no_regression.py` 确认.

注 (Mi-3 r2): `packs/garage/pack.json` description 文案漂移 ("agents/ 加 **2 个** production agent" 但 agents[] 数组含 3 个) 是 F011 carry-forward, 不阻塞 F015 实施; 可在 F015 finalize 阶段顺手修, 也可推到 F011 carry-forward / 任意未来 cycle.

注 (Ni-1 r2 多行 description 切分规则): 多数 `packs/*/skills/*/SKILL.md` `description` 单行; 少数如 `hv-analysis` 用多行 `description: |`. F015 模板生成时切分规则: 取 `description` 字段值的第一个非空段; 至少 50 字截断到第一个句号 (`。` / `.`) 或行尾, 取较短的.

---

> **本文档是 spec r2** (回应 spec-review-F015-r1 的 2 critical + 2 important + 4 minor + 1 nit; 全部 9 finding 已闭合, 详见 `docs/reviews/spec-review-F015-r1-2026-04-26.md`).
>
> r2 关键修订:
> - **Cr-1** (USER-INPUT 选项 a): BDD 8.4 改 agent 名为 `demo-overwrite-agent` (不用 code-review-agent), 避免与 INV-F15-5 守 F011 既有 3 个 agent byte 不变冲突
> - **Cr-2**: F011 compose 模板参考子集收窄为 **2 个** agent (`code-review-agent` + `blog-writing-agent`); `garage-sample-agent` 显式排除 (它是 F008 安装/容错样本, 故意无 frontmatter; CON-1504 不参考)
> - **Im-1**: missing skill 双层语义 — library `ComposeResult.missing_skills` 仍生成 partial draft, CLI 严格 exit 1 不写盘
> - **Im-2**: FR-1505 status 段不带 last compose ts 后缀 (避免依赖 optional cache.json)
> - **Mi-1**: 调研锚点 agent.md 行数 11-42 行 (实测)
> - **Mi-2**: API 完整签名 `KnowledgeStore.list_entries(knowledge_type=KnowledgeType.STYLE)`
> - **Mi-3**: pack.json description 文案漂移注解 (不阻塞 F015)
> - **Mi-4**: §10 Stage 3 ~95% → ~100% 加 "估算" 注 + 量化依据
> - **Ni-1**: 多行 description 切分规则补 (Mi-3 / Ni-1 合并到 §11 注)
