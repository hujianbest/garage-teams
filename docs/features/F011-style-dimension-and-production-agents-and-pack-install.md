# F011: KnowledgeEntry style 维度 + 2 production agents + `garage pack install <git-url>`

- 状态: 草稿（待 hf-spec-review）
- 主题: vision-gap planning § 2.2 P1 三候选 (F011-A/B/C) 在一个 cycle 内实施: (A) 给 KnowledgeEntry 加 `style` 维度复活 Promise ② "知道你的编码风格", (B) `packs/garage/agents/` 落 2 个真正可用 agent (code-review-agent + blog-writing-agent) 启动 Stage 3 工匠, (C) `garage pack install <git-url>` 让 B5 可传承 2/5 → 3.5/5
- 日期: 2026-04-24
- 关联:
  - vision-gap planning artifact `docs/planning/2026-04-24-vision-gap-and-next-cycle-plan.md` § 2.2 (F011-A/B/C 候选定义)
  - F003 — KnowledgeEntry/KnowledgeType (本 cycle A 部分扩展)
  - F007 — Pack discovery 与 host installer (本 cycle C 部分扩展)
  - F010 — `garage sync` (本 cycle A 让 sync compiler 自动 pick up style entries)
  - manifesto Promise ② "知道你的编码风格" + Stage 3 "工匠" + 信念 B5 "可传承"
  - growth-strategy "Skills > 30 → Stage 3" (current 31, 已达触发信号)

## 1. 背景与问题陈述

vision-gap planning § 2.2 列了三个 P1 candidate, 三者都是单文件 / 小模块改动, 不彼此阻塞:

- **F011-A** Promise ② = 0/5: F003 的 4 个 KnowledgeEntry kind (decision/pattern/solution/experience_summary) 没有 style 维度. 用户偏好"functional 风格" / "中文长文遵循卡兹克节奏" 这类知识无处放
- **F011-B** Stage 3 = 5%: `packs/garage/agents/garage-sample-agent.md` 是占位; manifesto 终极形态承诺的 "代码审查 agent" / "博客写作 agent" 一个都没有. Skills > 30 触发信号已达成 (current 31)
- **F011-C** B5 = 2/5: 目前唯一 pack 分享路径是 `git clone` + 手动 `garage init`. 没有 `garage pack install <git-url>` 让用户一键拉装第三方 pack

三件事在同一个 cycle 处理是 ROI 最高: 都是单领域改动 (F011-A 在 types/ + knowledge/, F011-B 在 packs/garage/agents/, F011-C 在 cli + adapter/installer/), 互不依赖, manual smoke 可一次跑完.

## 2. 目标与成功标准

### 2.1 范围

A. **KnowledgeEntry style 维度** (FR-1101..1103):
- KnowledgeType 加 `STYLE` enum value
- KnowledgeStore TYPE_DIRECTORIES 加 `style → "knowledge/style"`
- F010 sync compiler 自动把 style 类条目 include 到 top-N (与 decision/solution/pattern 同模式, 4 per kind)
- `garage knowledge add --type style ...` 可用 (已有 CLI 自动 enum-validation 支持)

B. **2 个 production agent** (FR-1104..1105):
- `packs/garage/agents/code-review-agent.md`: 组合 hf-code-review skill + (隐式) 用户 style entries
- `packs/garage/agents/blog-writing-agent.md`: 组合 blog-writing skill + humanizer-zh skill + (可选) hv-analysis
- 两个 agent 都按 F003-F009 既有 agent.md 规范 (front matter + body), 装到 claude/opencode 的原生 agent 目录 (cursor 无 agent surface)

C. **`garage pack install <git-url>`** (FR-1106..1108):
- 新 CLI 子命令: `garage pack install <git-url>` 
- 行为: shallow git clone → discover pack metadata → 验证 schema → 装到 `packs/<pack-id>/` (workspace_root local copy)
- pack.json 加 optional `source_url` 字段记录来源
- `garage pack ls` (新): 列出已装 pack + source

### 2.2 成功标准

1. **A 端到端可演示**: `garage knowledge add --type style --topic "Functional Python preference"` → `.garage/knowledge/style/<id>.md` 创建 → `garage sync --hosts claude` 后 CLAUDE.md 含 `### Recent Style Preferences` 段
2. **B 端到端可演示**: 装到下游 host 的 `.claude/agents/code-review-agent.md` 和 `blog-writing-agent.md` 文件存在; 内容含 front matter (`name` + `description`) + body
3. **C 端到端可演示**: `garage pack install https://github.com/<test>/<repo>` (用本地 file:// URL 测试) → `packs/<pack-id>/` 物化 + pack.json `source_url` 字段写入 + `garage pack ls` 列出来
4. **F010 既有 825 测试基线 0 退绿** (CON-1101)
5. **packs/garage/ 总 skill 数 3 → 3 (不变), agents 数 1 → 3 (sample + code-review-agent + blog-writing-agent)**; INV-1 hard gate 同步 (31 → 31 skills, 1 → 3 agents); F008 既有 `test_full_packs_install.py` 同步
6. **garage pack ls 输出 marker 与 F007/F009/F010 marker family 一致** (`Installed packs (N total):`)

## 3. Success Metrics

| Metric | Outcome | Threshold | Measurement |
|---|---|---|---|
| **SM-1101** | Promise ② 复活 | KnowledgeType.STYLE 在 sync 出现, 用户能 add | manual smoke + sync CLAUDE.md 含 style 段 |
| **SM-1102** | Stage 3 启动证据 | 2 个 production agent 装到 claude + opencode | 4 个 agent 文件落盘 (2 × 2 hosts) |
| **SM-1103** | B5 可传承 | `garage pack install <local-url>` 一键拉装 | pack 物化到 packs/, pack.json 含 source_url |
| **SM-1104** | 0 regression | F010 baseline 825 → ≥ 825 | pytest |

## 4. Key Hypotheses

| HYP | Statement | Type | Confidence | Validation | Blocking? |
|---|---|---|---|---|---|
| HYP-1101 | KnowledgeType 加 enum value 不破坏 F003-F006 既有测试 | F | High | 跑 F003-F006 全套测试 + F010 sync compiler tests | Yes |
| HYP-1102 | 2 个 agent.md 满足 F007 既有 pack discovery 规范 | F | High | F007 pack discovery 测试 + 物化 verify | Yes |
| HYP-1103 | `git clone` shallow (`--depth 1`) 在 GitHub / local file:// 都工作 | F | High | manual smoke 用 local file:// 验证 (避免依赖网络) | Yes |
| HYP-1104 | `pack.json` 加 optional `source_url` 字段不破坏 schema validation | F | High | F007 pack discovery + F008 既有 test 0 退绿 | Yes |

## 5. 范围内 / 范围外

### 5.1 范围内 (Must)

A: KnowledgeType.STYLE + sync compiler include style + manual smoke
B: 2 个 production agent.md (code-review-agent + blog-writing-agent) + `packs/garage/pack.json` agents 数 + INV-1 同步
C: `garage pack install <git-url>` + `garage pack ls` + pack.json `source_url` optional 字段

### 5.2 范围外 (deferred)

- F011-D: `garage pack publish` (远端推送) — 太重, 等用户实际想分享时再开
- F011-E: 多个 pack from 同 URL (monorepo) — 假设单 pack per repo
- F011-F: pack signature / 安全审核 — 用户自管 (B5 user-pact "你做主")
- F011-G: knowledge 脱敏导出 — 与 pack install 反向, 单独 cycle
- 不在本 cycle: 多 production agent (3+); style entry 自动从用户 commit history 提取 (太魔法)

## 6. FR

### FR-1101 — KnowledgeType.STYLE enum + 目录映射
- Statement (Ubiquitous): The system SHALL 在 `KnowledgeType` enum 加 `STYLE = "style"`; KnowledgeStore TYPE_DIRECTORIES 加 `KnowledgeType.STYLE → "knowledge/style"`
- Acceptance:
  ```
  Given F011 实施
  When import KnowledgeType
  Then KnowledgeType.STYLE 存在 + .value == "style"
  And KnowledgeStore(...).list_entries(knowledge_type=KnowledgeType.STYLE) 返回 list (空时 [])
  And .garage/knowledge/style/ 目录可创建 (FileStorage 自动)
  ```

### FR-1102 — `garage knowledge add --type style` CLI 支持
- Statement: When user runs `garage knowledge add --type style --topic "..." --content "..."`, the system SHALL create a STYLE entry under `.garage/knowledge/style/`
- Acceptance: 既有 `garage knowledge add` 已 enum-validate `--type`, F011 加 STYLE 后自动支持; 测试 verify

### FR-1103 — F010 sync compiler include STYLE entries
- Statement (Event-driven): When `garage sync` runs, the system SHALL compile top-N STYLE entries into Garage marker block alongside decision/solution/pattern (4 per kind)
- Acceptance:
  ```
  Given .garage/knowledge/style/ 含 ≥ 1 entry
  When garage sync --hosts claude
  Then CLAUDE.md 含 "### Recent Style Preferences" 段
  And footer "_Synced at ..._" 含 4-section count (knowledge_kinds 含 "style")
  ```

### FR-1104 — `packs/garage/agents/code-review-agent.md`
- Statement: The system SHALL ship `packs/garage/agents/code-review-agent.md` with front matter (`name`, `description`) + body documenting how it composes hf-code-review skill + user style entries
- Acceptance: 文件存在, front matter 合规, `garage init --hosts claude` 后 `.claude/agents/code-review-agent.md` 落盘

### FR-1105 — `packs/garage/agents/blog-writing-agent.md`
- Statement: 同上, but 组合 blog-writing + humanizer-zh + (可选) hv-analysis
- Acceptance: 同 FR-1104

### FR-1106 — `garage pack install <git-url>` CLI
- Statement (Event-driven): When user runs `garage pack install <git-url>`, the system SHALL shallow-clone the repo + discover pack metadata + verify schema + install to `packs/<pack-id>/` + write `pack.json source_url`
- Acceptance:
  ```
  Given a local file:// pack URL pointing to a directory with pack.json + skills/<id>/SKILL.md
  When garage pack install file:///tmp/test-pack
  Then packs/<pack-id>/ 在 workspace 内物化
  And packs/<pack-id>/pack.json 含 source_url == "file:///tmp/test-pack"
  And stdout marker "Installed pack '<pack-id>' from <url>"
  ```

### FR-1107 — `garage pack ls`
- Statement: The system SHALL provide `garage pack ls` to list installed packs with id / version / source_url
- Acceptance:
  ```
  When garage pack ls
  Then stdout 含 "Installed packs (N total):" + per-line "<pack-id> v<version> [<source_url|local>]"
  ```

### FR-1108 — `pack.json` `source_url` optional 字段
- Statement (Ubiquitous): pack.json schema 加 optional `source_url: str` 字段; F007 既有 pack.json (无此字段) 仍 valid (backward compat)
- Acceptance: F008 既有 4 packs (garage/coding/search/writing) 测试 0 退绿; 新装 pack 含 source_url

## 7. NFR

### NFR-1101 — F010 既有 825 测试基线 0 退绿
- 沿用 F010 NFR-902/INV-F10-2 精神; 跑 `pytest tests/ -q` 守门

### NFR-1102 — `garage pack install` perf ≤ 10s for typical pack (depth=1 shallow clone)
- 与 F007/F009/F010 perf budget 量级一致, 留余量给网络

### NFR-1103 — F008 INV-1 hard gate 同步
- packs/garage/ skills 数: 3 (不变); agents 数: 1 → 3
- `tests/adapter/installer/test_full_packs_install.py` 同步: 31 skills + 1 agent → 31 skills + 3 agents (claude + opencode each get 3); manifest.files: 95 → 95+4 (3 agents × 2 hosts - 1 sample × 2 = +4 file entries) — 实际由实施时实测

## 8. CON

- **CON-1101**: F010 既有 `garage sync` / `garage session import` 行为字节级不变; F010 sync compiler 加 STYLE include 是新增 read 路径 (透明)
- **CON-1102**: KnowledgeEntry dataclass + F003-F006 内核 0 改动 (仅扩 enum + TYPE_DIRECTORIES + sync compiler kind list); 与 F010 CON-1002 同精神
- **CON-1103**: `garage pack install` 不引入新 host adapter / 不破坏 F007 既有 pack discovery (复用 `pack_discovery._load_pack`)
- **CON-1104**: 不新增 git 命令以外的网络 dep; `garage pack install` 用 subprocess 调本机 git (不引入 GitPython 等库); pyproject.toml + uv.lock git diff = 0
- **CON-1105**: cursor 无 agent surface — F011-B 的 2 agent 仅装到 claude / opencode (与 F007/F008 sample agent 同精神)

## 9. ASM

- ASM-1101: 用户机器有 git 可用 (PATH 中)
- ASM-1102: pack URL 指向的目录含合规 pack.json (CLI 友好失败 if 不合规)
- ASM-1103: STYLE 类知识价值由用户决定 (manifesto B5 "你做主"); F010 sync compiler 不替用户判断 style 内容质量

## 10. INVEST + Phase 0 自检

- [x] FR/NFR/CON/ASM 都有 ID + Priority + Source
- [x] HYP 全部含 Type/Confidence/Validation/Blocking
- [x] Success Metrics 显式
- [x] 范围内/范围外清晰
- [x] 三 candidate 互不依赖, 可独立测试
- [x] 沿用 F010 sync infrastructure (SIZE_BUDGET / per-kind top / footer)
- [x] CON-1102 守 F003-F006 0 改动精神
- [x] CON-1104 守零依赖变更
