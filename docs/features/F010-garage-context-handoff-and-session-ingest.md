# F010: Garage Context Handoff (`garage sync`) + Host Session Ingest (`garage session import`)

- 状态: 草稿（待 hf-spec-review）
- 主题: 让 F003-F006 build 的 memory 子系统**真正进入用户日常 host 对话**: (A) `garage sync` 把 top-N knowledge + recent experience 编译到三家宿主原生 context surface; (B) `garage session import --from <host>` 把日常 host 对话反向 ingest 成 Garage session 喂给 F003 自动提取链, 闭合 B4 飞轮
- 日期: 2026-04-24
- 关联:
  - `docs/soul/manifesto.md` § 终极形态（Promise ① "几秒变成你的 Agent" + Promise ③ "记得上个月的架构决策"）
  - `docs/soul/user-pact.md` § 5 "你做主"（系统提供建议, 关键决策由用户做; 自动化必须可关）
  - `docs/soul/growth-strategy.md` § Stage 2 → Stage 3（"自动 + 半自动" 提取的 Stage 2 capability 必须先有 inject 才能闭合, 才能升 Stage 3）
  - `docs/soul/design-principles.md`（B1 数据归你 + B2 宿主可换 + B4 人机共生）
  - F003 — Garage Memory 自动知识提取（`KnowledgeStore` + `ExperienceIndex` + 提取 trigger = `SessionManager.archive_session()`; 本 cycle 直接 reuse, 不改）
  - F005 — Garage Knowledge Authoring CLI（`garage knowledge add` 等; 本 cycle 加 `garage sync` 与之并列）
  - F006 — Garage Recall & Knowledge Graph（`garage recall ...` pull 路径; 本 cycle 加 push 路径作为对偶）
  - F007 — `HostInstallAdapter` Protocol + 三家 first-class adapter（claude / opencode / cursor）；本 cycle 在 Protocol 加 context surface method
  - F009 — manifest schema 2 + 双 scope（本 cycle 不改 manifest, 但 sync 产物的目标路径要支持 project / user 双 scope）
  - `docs/planning/2026-04-24-vision-gap-and-next-cycle-plan.md` § 2.1 — F010-A + F010-B 候选定义
  - 调研锚点（与 F009 § 2.3 同源, 三家官方文档 + 本 cycle 新调研）：
    - **Anthropic Claude Code**: project context = `<cwd>/CLAUDE.md`（auto-loaded）; user context = `~/.claude/CLAUDE.md`（auto-loaded）; conversation history = `~/.claude/conversations/<id>.json`（NDJSON-style, ~2026 Q1 schema）
    - **Cursor**: project context = `.cursor/rules/<id>.mdc`（front matter `alwaysApply: true` 即自动加载）; user context = `~/.cursor/rules/<id>.mdc`; conversation history 路径未在官方文档稳定暴露（research-heavy, 见 § 11 阻塞性问题 BLK-1003）
    - **OpenCode**: project context = `.opencode/AGENTS.md`（自动加载）; user context = `~/.config/opencode/AGENTS.md`（XDG default）; conversation history = `~/.local/share/opencode/sessions/<id>.json`

## 1. 背景与问题陈述

F003 (auto knowledge extraction) → F004 (publication identity) → F005 (knowledge authoring CLI) → F006 (recall + knowledge graph) 这四个 cycle 把 Garage 的"记忆体"子系统（manifesto Stage 2 capability）build 完整: `.garage/knowledge/` + `.garage/experience/` + `KnowledgeStore` + `ExperienceIndex` + `garage knowledge add` + `garage recall ...` 全套就绪.

**但用户日常打开 Cursor / Claude Code / OpenCode 开新对话时, 这些子系统完全 invisible**:

1. 宿主不会自动 read `.garage/knowledge/decisions/*.md`, 不会 read `.garage/experience/records/*.json`
2. 用户每次新对话还要手动复述上下文（"上次我们决定用方案 A"）
3. F003 的提取 trigger 是 `SessionManager.archive_session()`, 但用户日常的 Cursor / Claude Code 对话**从不变成 Garage session** — 飞轮的 input 端断了
4. `garage recall ...` 只能 pull, 用户得显式调; 没有 push 路径

vision-gap 分析（`docs/planning/2026-04-24-vision-gap-and-next-cycle-plan.md`）量化结果:

- Promise ① "几秒变成你的 Agent" = **3/5 ⚠️**（缺 context handoff）
- Promise ③ "记得上月架构决策" = **4/5 ⚠️**（缺 push 路径）
- 信念 B4 "人机共生" = **3/5 ⚠️**（飞轮 push 端 + input 端都缺）
- Stage 2 完成度 = **60%**（自动提取做完了, 但闭环不在）

F010 是把这层"沉睡资本"激活的最小动作: 让 `.garage/knowledge/` 与 `.garage/experience/` 的内容**真正出现在用户每次新对话开始时**, 同时让用户日常 host 对话**真正喂回 Garage session**.

### 真实摩擦

1. **用户在 Cursor 新对话里反复教 AI 上下文**: 用户做了 ADR-D9-7 选 candidate C 的决策, F003 已自动从 archived session 提取成 `decision` entry; 但 3 天后开新 Cursor 对话讨论同一题, AI 还是问 "你们之前是怎么决定的?" — 知识在仓库里, 但 AI 看不到
2. **`garage recall <topic>` 用户从来不主动调**: 用户已经在编辑器里, 跳出去开终端跑 `garage recall foo`, 复制结果回 IDE 粘贴 — 步骤多到没人会做; pull 路径事实上不可用, 必须升级为 push (开新对话时自动 inject)
3. **F003 自动提取流程在真实使用中只跑过 5-6 次**: 从 F003 落地到现在, 实际产生的 `archived` session 数 << 用户实际 host 对话次数; 因为只有显式 `garage run skill` 才创建 Garage session, 而用户日常工作 90% 不走这条路径
4. **三家宿主原生 context surface 已稳定**:
   - Claude Code 的 `CLAUDE.md` 自动加载是 2025 H2 落定的官方约定（持久 + 大小自管 + 项目级与用户级双层）
   - Cursor 的 `.cursor/rules/*.mdc` 配 `alwaysApply: true` 是 2026 Q1 稳定 GA 路径
   - OpenCode 的 `.opencode/AGENTS.md`（项目级）+ `~/.config/opencode/AGENTS.md`（用户级）也已 GA
   - 三家都已经 ready, 是 Garage 没有 sync 路径

### 边界澄清（不是本 cycle 的问题）

- **不是知识库本身缺**: F003-F006 already work, 不重写
- **不是宿主 API 限制**: 三家都暴露了文件级 context surface, 不需要任何 API token
- **不是 schema 设计问题**: 既有 `KnowledgeEntry` + `ExperienceRecord` 字段足够 sync 用
- **是"自动化压缩 + 路径 + 触发时机" 三个工程问题**: top-N 选择策略 + budget 算法 + sync 触发时机

## 2. 目标与成功标准

### 2.1 核心目标

把 `.garage/knowledge/` + `.garage/experience/` 的内容物以**宿主原生 context surface 文件**的形态推到三家宿主, 同时把宿主对话**反向 ingest 成 Garage session** 喂给 F003 自动提取链:

```
                F009 (现状)                                   F010 (本 cycle)
                ───────────────                               ────────────────
sync 路径:      手动 garage recall <topic>                    garage sync
(push 端)       → 用户跳出 IDE 复制粘贴                        → 自动写 .claude/CLAUDE.md / .cursor/rules/garage-context.mdc
                                                              → 用户在 IDE 内开新对话, 上下文已 inject

ingest 路径:    用户必须 garage run <skill>                   garage session import --from claude-code
(pull 端)       → 否则 host 对话不变成 Garage session          → 读 ~/.claude/conversations/*.json
                → F003 自动提取空跑                             → 转成 SessionState 喂给 F003
                                                              → 飞轮 input 端闭合
```

**A. context handoff (sync 路径) 收敛**:
- 新增 `garage sync` 子命令: 编译 top-N knowledge + recent experience 到三家宿主原生 context surface
- 三家 host adapter 加 context surface method（与 F007 `target_skill_path` 对称, F009 `target_skill_path_user` 同精神）:
  - Claude Code → `CLAUDE.md`（project: cwd; user: `~/.claude/`）
  - Cursor → `.cursor/rules/garage-context.mdc`（项目根; 用户级 `~/.cursor/rules/`）
  - OpenCode → `.opencode/AGENTS.md`（项目根; 用户级 `~/.config/opencode/`）
- 复用 F009 双 scope 模型（`--scope project|user` + per-host override）
- top-N 选择策略 + size budget 由 design ADR 决定（spec 不固化数字）
- sync 是显式触发（用户跑 `garage sync`）, 不在 cycle 内做 file-watcher / git hook 自动化（留给 F012-D）

**B. session ingest (ingest 路径) 收敛**:
- 新增 `garage session import --from <host>` 子命令: 读宿主 conversation history → 转 Garage SessionState → 触发 F003 既有 archive + 自动提取链
- 三家宿主 history reader 各加一个 plug-in 模块（与 host adapter 同模式）
- 转换是单向（host → Garage）, 不写回 host
- 用户做主（B5 user-pact）: 默认列出可 import 的对话让用户选, `--all` 显式 batch 才 batch import
- 提取出的知识仍走 F003 既有 candidate 流程（用户审批后入库）, 不绕过 trust boundary

### 2.2 成功标准

1. **F009 既有 `garage init` 行为字节级不变（CON-1001）**: 不引入 `garage init` 任何变化; F009 baseline 715 passed 全部保持
2. **`garage sync` 端到端可演示**: 干净下游项目 `cd ~/projects/my-app && garage sync --hosts claude` 后, `<cwd>/CLAUDE.md` 出现 Garage 标记段（含 top-N 知识摘要 + recent experience）, `<cwd>/.garage/config/sync-manifest.json` 写入 sync 清单（含 sync_at + content_hash + sources[]）
3. **三家宿主 sync target 端到端可演示**:
   - `garage sync --hosts claude` → `<cwd>/CLAUDE.md` 含 Garage 段
   - `garage sync --hosts cursor` → `<cwd>/.cursor/rules/garage-context.mdc` 含 Garage 段（front matter 含 `alwaysApply: true`）
   - `garage sync --hosts opencode` → `<cwd>/.opencode/AGENTS.md` 含 Garage 段
   - `--scope user` → 装到 `~/.claude/CLAUDE.md` / `~/.cursor/rules/...` / `~/.config/opencode/AGENTS.md`
4. **sync 幂等**: 第二次 `garage sync` 内容相同时, 文件 mtime 不刷新（NFR-1002 mtime stability）; 内容变化时只覆写 Garage 标记段, 用户在文件其它位置的内容字节级保留（NFR-1003 user content preservation）
5. **`garage session import` 端到端可演示**:
   - `garage session import --from claude-code` 列出最近 30 天 Claude Code 对话, 用户选 1 条 → Garage 创建 SessionState → archive_session() 自动 trigger F003 → 知识 candidate 入 `.garage/knowledge/.candidates/`
   - 用户跑 `garage knowledge approve <candidate-id>` 后, 知识进入 `.garage/knowledge/decisions/`（或对应 kind 目录）
   - 第一次 import 后立刻 `garage sync` → 新 ingest 的知识立刻出现在宿主 context surface
6. **B5 user-pact 守门**: 默认 `garage session import --from <host>` 是 interactive 模式（列出对话让用户选）; `--all` 是 explicit opt-in; 任何 import 都不绕过 F003 既有 candidate 审批流（CON-1004）
7. **F006 既有 `garage recall ...` pull 路径不变**: F010 加 push 但不删 pull; 二者并存, 不耦合
8. **测试基线零回归**: `pytest tests/ -q` ≥ F009 baseline 715, 0 退绿; 新增测试覆盖 (a) 三家 host context surface adapter (b) sync compiler 选择 + budget (c) sync 幂等 + user content preservation (d) session import 三家 history reader (e) import → archive → F003 提取链端到端
9. **manual smoke 4 tracks 全绿**:
   - Track 1: dogfood `garage sync --hosts claude` 在 Garage 仓库自身
   - Track 2: 干净 tmp 项目 `garage sync --hosts all` 三家全装
   - Track 3: `garage session import --from claude-code` interactive 选 1 条对话 → archive → F003 candidate
   - Track 4: import 后 `garage sync` 立刻看到新知识在宿主 context surface
10. **F003 既有提取链不被破坏**: import 出来的 SessionState 走 F003 同一 archive_session() trigger; F003 既有的 384 测试仍 100% 通过

### 2.3 与既有 F 的边界

- **F003 KnowledgeStore + ExperienceIndex**: 本 cycle 直接 reuse, 不改 schema; sync compiler 是新增 read 路径, ingest 是新增 write 路径
- **F006 KnowledgeIntegration**: sync compiler 复用既有 query API（`top_n_by_recency` / `top_n_by_relevance`）, 不重新实现 ranking
- **F007 HostInstallAdapter Protocol**: 加 `target_context_path` + `target_context_path_user` method; 与 F009 `target_skill_path_user` 同精神, 字段扩展同一类不引入新 Protocol（CON-1006 沿用 F009 CON-901）
- **F009 双 scope**: sync 完全复用 F009 scope 解析 + per-host override; ingest 不需要 scope（host history 路径是宿主自己定的）

## 3. Success Metrics

| Metric ID | Outcome | Threshold | Measurement | Non-goal |
|---|---|---|---|---|
| **SM-1001** | sync 后用户 IDE 新对话能看到 Garage 知识 | 在 dogfood + tmp 双轨 manual smoke 中, 至少 1 个 Garage 标记段被 host 解析为 context（含 top-N 知识 + recent experience）| 目测 IDE 内新对话; sync-manifest.json content_hash 与 host context 文件实际内容一致 | 不衡量 host 解析后 AI 答得对不对 (那是 host 自己的事) |
| **SM-1002** | session import 闭合 F003 飞轮 input 端 | 至少 1 条 host 对话被 import 成 SessionState → 触发 archive_session → F003 candidate 入库 | `.garage/knowledge/.candidates/` 出现至少 1 个新 entry; F003 提取 log 含 import 来源 anchor | 不衡量自动提取出来的知识质量 (那是 F003 既有 trust boundary) |
| **SM-1003** | 测试基线 + dogfood 不退绿 | F009 baseline 715 → F010 实施完成 ≥ 715 + 增量 | `pytest tests/ -q` + dogfood `garage init --hosts cursor,claude` stdout 字节级与 F009 baseline 一致 | 不衡量新增测试个数 |
| **SM-1004** | 文档冷读 5 分钟可达 | `AGENTS.md` → user-guide → spec/design 链路完整 | 任意 cold reader 5 分钟内能回答 "garage sync 怎么用 / garage session import 怎么用 / 哪些 host 支持" | 不衡量文档字数 |

**Non-goal Metrics** (显式不追求):
- 不追求 sync 性能极致 (NFR-1004 上限 < 5s 即可, 与 F007/F009 一致)
- 不追求 import 出来的所有知识自动入库 (CON-1004 用户审批门槛)
- 不追求第 4 家宿主插件化 (P2 候选, 等触发信号)

## 4. Key Hypotheses

| HYP ID | Statement | Type | Impact If False | Confidence | Validation Plan | Blocking? |
|---|---|---|---|---|---|---|
| **HYP-1001** | Claude Code 的 `CLAUDE.md` 在 cwd / `~/.claude/` 都会被自动 read 进 context | F (feasibility) | sync 写出去也没人 read, F010-A 价值归零 | High | manual smoke Track 1 + 阅读 Anthropic 官方文档 § "Project context" 段 | **Yes** (Blocking — manual smoke 必须验证) |
| **HYP-1002** | Cursor 的 `.cursor/rules/*.mdc` 配 `alwaysApply: true` 在新对话开始时自动注入 | F | 同上 (Cursor 视角) | High | manual smoke Track 2 + Cursor 官方文档 § "Rules" | **Yes** (Blocking) |
| **HYP-1003** | OpenCode 的 `.opencode/AGENTS.md` + `~/.config/opencode/AGENTS.md` 同 Claude Code 模式 | F | 同上 (OpenCode 视角) | Medium-High | manual smoke Track 3 + OpenCode 官方 README | **Yes** (Blocking) |
| **HYP-1004** | Claude Code conversation history 在 `~/.claude/conversations/<id>.json` 是稳定 NDJSON-like 路径 | F | session import --from claude-code 不可实现 | Medium | manual smoke + Anthropic 官方文档 + 本机实测 | **Yes** (Blocking) |
| **HYP-1005** | Cursor conversation history 路径稳定可读 | F | session import --from cursor 不可实现 | **Low** | research 阶段 + design ADR 决定是否纳入本 cycle 或 deferred | **No** (allow deferred) |
| **HYP-1006** | OpenCode conversation history 在 `~/.local/share/opencode/sessions/<id>.json` 稳定 | F | session import --from opencode 不可实现 | Medium | research 阶段 + 本机实测 | **Yes** (Blocking, 如不验证可降级 deferred) |
| **HYP-1007** | top-N + size budget 选 ≤ 16KB 段, 用户日常 IDE 对话能受益 | V (value) | sync 出来的内容用户感知不到 | Medium | manual smoke Track 4 (import → sync → IDE 新对话) | No |
| **HYP-1008** | F003 既有 archive_session() trigger 兼容 import 来源的 SessionState | F | F003 自动提取链断裂 | High | 单元测试 + manual smoke Track 3 | **Yes** (Blocking) |

> **Blocking 假设阻塞规则**: HYP-1001 / 1002 / 1003 / 1004 / 1006 / 1008 必须在 manual smoke 阶段验证, 否则 cycle 不允许进 hf-finalize. HYP-1005 (Cursor history) 允许在 design ADR 阶段降级为 deferred (如官方文档不稳定)

## 5. 范围内 / 范围外 / Deferred Backlog

### 5.1 范围内 (本 cycle 必须落)

A. **`garage sync` 子命令**:
- A1. CLI subcommand + `--hosts <list>` (复用 F009 解析) + `--scope <project|user>` (复用 F009)
- A2. Sync compiler 模块（top-N knowledge + recent experience → 编译为 markdown 段）
- A3. 三家 host context adapter method（`target_context_path` + `target_context_path_user`）
- A4. Sync manifest（`.garage/config/sync-manifest.json`, schema_version=1）
- A5. 幂等 + user content preservation（用 begin/end marker 圈定 Garage 段, 用户其它内容字节级保留）

B. **`garage session import` 子命令**:
- B1. CLI subcommand + `--from <host>` + `--all` 显式 batch
- B2. 三家 host history reader 各一个 module (但 cursor history 允许 deferred 见 HYP-1005)
- B3. SessionState 转换 (host conversation → Garage SessionState)
- B4. trigger 既有 SessionManager.archive_session() (F003 自动提取链 0 改动)
- B5. interactive 模式默认列出待 import 对话让用户选

### 5.2 范围外（本 cycle 不做）

- 不做 sync file-watcher / git hook 自动化 (F012-D 候选)
- 不做 import 出来的知识 bypass F003 candidate 审批 (CON-1004 守门)
- 不做 sync 写回 host conversation (单向, host → garage 与 garage → host 都不闭环, 都是 file-based)
- 不做 host conversation 实时 stream (一次性 read history file)
- 不做 sync 跨 scope 优先级解析 (Garage 写到指定 scope, host 自己决定加载优先级 — 与 F009 同精神)
- 不做 enterprise scope (与 F009 same)
- 不做 sync 输出格式定制 (markdown 段格式由 design ADR 固定)

### 5.3 Deferred Backlog（F011+ 候选）

- **D-1010**: Cursor conversation history 稳定路径若 design ADR 阶段确认不可读, 降级为 deferred (HYP-1005)
- **D-1011**: `garage sync watch` 文件监听自动 re-sync (F012-D 候选)
- **D-1012**: `garage session import` 支持 stream 模式 (实时跟随新对话, 而非 batch read history)
- **D-1013**: top-N 选择策略可配置 (本 cycle 默认 + 5-10 个固定参数, 不暴露 user-tunable)
- **D-1014**: sync 产物可走 git commit hook 自动 stage (B5 共享路径)
- **D-1015**: import 时按 host 自定义 conversation filter (本 cycle 默认按 mtime 倒序前 30, 不暴露 filter)

## 6. 功能需求 (FR)

### FR-1001 — `garage sync` 子命令

- 优先级: Must
- 来源: § 2.2 #2 + SM-1001
- Statement (EARS, Event-driven): When 用户执行 `garage sync [--hosts <list>] [--scope <project|user>]`, the system SHALL 编译 top-N knowledge + recent experience 到指定 host 的原生 context surface 文件, 并写 sync manifest 到 `.garage/config/sync-manifest.json`
- Acceptance (BDD):
  ```
  Given .garage/knowledge/decisions/ 含 ≥ 1 个知识条目
  When 用户在干净下游项目跑 `garage sync --hosts claude`
  Then <cwd>/CLAUDE.md 出现 Garage 标记段（begin/end marker 之间含 top-N 知识摘要）
  And <cwd>/.garage/config/sync-manifest.json 写入 sync-manifest（含 sync_at + sources[] + content_hash）
  And stdout 含 "Synced N knowledge entries + M experience records into hosts: <list>" marker
  And exit code = 0
  ```
- INVEST 自检: Independent ✓; Negotiable (top-N 数 / budget 由 design ADR 决定); Valuable (Promise ① 直接复活); Estimable ✓; Small ✓ (5 子模块); Testable ✓

### FR-1002 — `garage sync` per-host scope override (复用 F009)

- 优先级: Must
- 来源: § 2.1 + F009 FR-902 复用
- Statement (Event-driven): When 用户执行 `garage sync --hosts <host>:<scope>,...`, the system SHALL 把每个 host 装到独立 scope, 与 F009 `garage init --hosts <host>:<scope>` 解析 100% 一致
- Acceptance (BDD):
  ```
  Given fake_home + 干净 tmp 项目, .garage/knowledge/ 含 1 个条目
  When 用户跑 `garage sync --hosts claude:user,cursor:project`
  Then ~/.claude/CLAUDE.md 出现 Garage 段
  And <cwd>/.cursor/rules/garage-context.mdc 出现 Garage 段
  And <cwd>/CLAUDE.md 不被创建
  And ~/.cursor/rules/garage-context.mdc 不被创建
  ```

### FR-1003 — sync 幂等 + Garage 段 user content preservation

- 优先级: Must
- 来源: § 2.2 #4 + NFR-1002 / NFR-1003
- Statement (Ubiquitous): The system SHALL 用 begin/end marker（`<!-- garage:context-begin -->` / `<!-- garage:context-end -->`）圈定 sync 写入的 Garage 段; 第二次 sync 时只覆写 marker 之间内容; marker 之外用户手写内容字节级保留
- Acceptance:
  ```
  Given <cwd>/CLAUDE.md 已存在, 含用户在文件顶部手写的 "# My Project Notes" 段, 然后是 Garage marker 段
  When 用户再次跑 `garage sync --hosts claude` 且 Garage 段内容无变化
  Then 整个 CLAUDE.md mtime 不刷新（NFR-1002）
  And 文件顶部 "# My Project Notes" 字节级保留（NFR-1003）

  Given 同上, 但 .garage/knowledge/ 新增 1 个条目导致 Garage 段内容变化
  When 用户再次跑 `garage sync --hosts claude`
  Then marker 之间段被覆写新内容
  And 文件顶部 "# My Project Notes" 字节级保留
  And mtime 刷新
  ```

### FR-1004 — 三家 host context adapter（claude / cursor / opencode）

- 优先级: Must
- 来源: § 2.1 + 调研锚点
- Statement (Ubiquitous): The system SHALL 提供三家 first-class host adapter 的 context surface 路径解析, 每家 adapter 加 `target_context_path` (project) + `target_context_path_user` (user) 两个 method, 路径如下:
  - claude → project: `Path("CLAUDE.md")`; user: `Path.home() / ".claude" / "CLAUDE.md"`
  - cursor → project: `Path(".cursor/rules/garage-context.mdc")`; user: `Path.home() / ".cursor" / "rules" / "garage-context.mdc"`
  - opencode → project: `Path(".opencode/AGENTS.md")`; user: `Path.home() / ".config" / "opencode" / "AGENTS.md"`
- Acceptance:
  ```
  Given 三家 first-class adapter（F007 既有）
  When 实例化 + 调用 target_context_path("garage-context") / target_context_path_user("garage-context")
  Then 返回值与上表完全一致 (含分隔符与文件名)
  And HostInstallAdapter Protocol method 全部存在 (mypy 通过)
  ```

### FR-1005 — `garage session import` 子命令

- 优先级: Must
- 来源: § 2.1 + SM-1002
- Statement (Event-driven): When 用户执行 `garage session import --from <host> [--all]`, the system SHALL 读宿主 conversation history → 转 Garage SessionState → 触发既有 archive_session() → F003 自动提取链
- Acceptance (BDD):
  ```
  Given fake_home/.claude/conversations/ 含 ≥ 1 条 conversation JSON 文件
  When 用户跑 `garage session import --from claude-code`
  Then stdout 列出可 import 的对话（按 mtime 倒序前 30）
  And 用户选 1 条后, .garage/sessions/archived/ 出现新 SessionState
  And F003 自动提取链被触发, .garage/knowledge/.candidates/ 出现新 candidate
  And exit code = 0
  ```

### FR-1006 — `garage session import --all` batch 模式

- 优先级: Must (B5 user-pact 守门)
- 来源: § 2.1 + B5 + CON-1004
- Statement (Event-driven): When 用户显式传 `--all`, the system SHALL 把全部 history 一次性 import; 默认（不传 `--all`）必须 interactive 模式让用户选
- Acceptance:
  ```
  Given fake_home/.claude/conversations/ 含 5 条 conversation
  When 用户跑 `garage session import --from claude-code --all`
  Then 5 条全部 import 成 SessionState
  And 5 个 candidate 入 .garage/knowledge/.candidates/
  And stdout 含 "Imported 5 conversations from claude-code"

  Given 同上, 但用户跑 `garage session import --from claude-code` (无 --all)
  When stdin 是非 TTY (CI 场景)
  Then 提示 "non-interactive shell detected; use --all to batch import" 并 exit 0 (与 F009 prompt_hosts 退化语义一致)
  ```

### FR-1007 — sync compiler top-N 选择 + size budget

- 优先级: Must
- 来源: § 2.1 + § 5.3 D-1013
- Statement (Ubiquitous): The system SHALL 用既有 `KnowledgeStore` + `ExperienceIndex` query API 选 top-N knowledge entries + recent M experience records, 总 size ≤ B (N/M/B 数值由 design ADR 决定)
- Acceptance:
  ```
  Given .garage/knowledge/ 含 50 个条目（混 decisions / patterns / solutions）+ .garage/experience/ 含 20 条 records
  When sync 编译
  Then 输出段大小 ≤ 16KB (默认 budget)
  And 优先级: decision > solution > pattern > experience_summary (复用 F006 既有 ranking)
  And 按 mtime 倒序在同 kind 内排
  ```

### FR-1008 — sync stdout marker (与 F007/F009 marker family 一致)

- 优先级: Must
- 来源: § 2.2 #2
- Statement (Ubiquitous): The system SHALL 在 sync 成功时输出 marker `Synced N knowledge entries + M experience records into hosts: <list>` (类比 F007 `Installed N skills, M agents into hosts: <list>`), 让下游脚本 grep 命中
- Acceptance:
  ```
  Given sync 完成
  When 检查 stdout
  Then `grep -cE '^Synced [0-9]+ knowledge entries \+ [0-9]+ experience records into hosts:'` 命中 == 1
  ```

### FR-1009 — `garage status` 显示 sync 状态 (复用 F009 status 段)

- 优先级: Should
- 来源: § 2.2 #2
- Statement (Ubiquitous): The system SHALL 在 `garage status` 输出末尾追加 sync 状态段 (类似 F009 `Installed packs (project scope):` 段), 显示 sync_at + per-host context surface 路径
- Acceptance:
  ```
  Given .garage/config/sync-manifest.json 存在
  When 用户跑 `garage status`
  Then stdout 含 "Last synced: <ISO 8601 timestamp>" 行
  And 按 host 列出 context surface 路径 + 文件大小
  ```

### FR-1010 — 文档同步 (cold-read 5 分钟可达)

- 优先级: Must
- 来源: SM-1004
- Statement (Ubiquitous): The system SHALL 同步 `AGENTS.md`（"Garage Memory Sync" 段）+ `docs/guides/garage-os-user-guide.md`（"Sync & Session Import" 段）+ `RELEASE_NOTES.md`（F010 段）, 让冷读用户 5 分钟内能回答 (a) `garage sync` 怎么用 (b) `garage session import` 怎么用 (c) 三家 host 路径
- Acceptance:
  ```
  Given F010 实施完成
  When cold reader 从 AGENTS.md 顶部入口开始读
  Then 5 分钟内能找到完整 sync + ingest 用法 + 路径表
  ```

## 7. 非功能需求 (NFR)

### NFR-1001 — 沿用 F009 dogfood 不变性硬门槛

- 优先级: Must
- 质量维度 (ISO 25010): **Reliability** + **Compatibility**
- QAS 五要素:
  - Stimulus Source: F010 实施完成的 cycle commit
  - Stimulus: 在 Garage 仓库自身根目录跑 `garage init --hosts cursor,claude` (不带 sync)
  - Environment: dogfood 路径 (workspace_root = `/workspace`, packs/ symlink 不变)
  - Response: stdout `Installed 62 skills, 1 agents into hosts: claude, cursor` (字节级与 F009 baseline 一致)
  - Response Measure: SHA-256 of every SKILL.md+agent.md 落盘文件 与 F009 baseline JSON 字节级一致 (复用 F009 sentinel `test_dogfood_invariance_F009.py`)
- Acceptance:
  ```
  Given F010 实施完成
  When 跑 dogfood `garage init --hosts cursor,claude`
  Then stdout 字节级一致 + SHA-256 sentinel 通过
  ```

### NFR-1002 — sync 幂等 mtime stability

- 优先级: Must
- 质量维度: **Reliability**
- QAS:
  - Stimulus: 第二次 `garage sync --hosts <host>` 时 .garage/knowledge/ 内容无变化
  - Environment: 任意干净下游项目
  - Response: host context 文件 (CLAUDE.md / .mdc / AGENTS.md) mtime 不刷新
  - Response Measure: `(file.stat().st_mtime - first_sync_mtime) == 0`
- Acceptance: 见 FR-1003

### NFR-1003 — sync 不破坏 marker 之外用户内容

- 优先级: Must
- 质量维度: **Reliability** + **Usability** (用户对 IDE context file 的所有权)
- QAS:
  - Stimulus: 用户在 CLAUDE.md / AGENTS.md / .mdc 文件中 Garage marker 之外手写内容
  - Environment: 任意 sync 调用
  - Response: marker 之外字节级保留
  - Response Measure: SHA-256 of (file content - marker block) unchanged
- Acceptance: 见 FR-1003

### NFR-1004 — sync + import perf

- 优先级: Should
- 质量维度: **Performance Efficiency**
- QAS:
  - Stimulus: `garage sync --hosts all` 或 `garage session import --from claude-code --all`
  - Environment: 50 knowledge entries + 30 experience records + 30 host conversations
  - Response: wall_clock 完成
  - Response Measure: ≤ 5s (与 F007/F009 perf budget 一致)
- Acceptance:
  ```
  Given 上述数据规模
  When manual smoke wall_clock 测试
  Then ≤ 5s 完成
  ```

## 8. 约束 (CON)

### CON-1001 — F009 既有 `garage init` 行为字节级不变

- 优先级: Must
- 来源: § 2.2 #1 + F009 CON-901 沿用精神
- Constraint: F010 不引入 `garage init` 任何变化; 既有 715 测试基线 0 退绿; dogfood stdout 字节级一致

### CON-1002 — F003-F006 既有内核 0 改动

- 优先级: Must
- 来源: § 2.3 + 设计原则 (扩展不修改)
- Constraint: F010 sync 是 read 路径, F010 ingest 是 write 路径; 二者都通过既有 KnowledgeStore / ExperienceIndex / SessionManager / archive_session() public API, 不改 F003-F006 核心模块

### CON-1003 — host context surface 文件用 begin/end marker 圈定 Garage 段

- 优先级: Must
- 来源: NFR-1003 + B5 user-pact "你做主"
- Constraint: 三家 host 的 context 文件 (CLAUDE.md / .mdc / AGENTS.md) 都用 `<!-- garage:context-begin -->` + `<!-- garage:context-end -->` (HTML comment, 三家 markdown parser 都视为不可见) 圈定 Garage 写入段; marker 之外字节级保留 (用户手写优先)

### CON-1004 — session import 不绕过 F003 candidate 审批

- 优先级: Must
- 来源: B5 user-pact "你做主" + § 2.2 #6
- Constraint: import 出来的 SessionState 走 F003 既有 archive_session() trigger, 提取出的知识进入 `.garage/knowledge/.candidates/` (而非直接 `.garage/knowledge/decisions/` 等正式目录); 用户必须显式 `garage knowledge approve <candidate-id>` 才入正式库

### CON-1005 — manifest schema (sync-manifest.json) 独立, 不污染 host-installer.json

- 优先级: Must
- 来源: § 2.1 + 设计原则 (单一职责)
- Constraint: F010 新建 `.garage/config/sync-manifest.json` (schema_version=1), 与 F009 `host-installer.json` (schema_version=2) 完全独立; 二者文件名 / schema / 内容互不引用

### CON-1006 — HostInstallAdapter Protocol 字段扩展同一类, 不引入新 Protocol

- 优先级: Must
- 来源: F009 CON-901 沿用精神 + § 2.3
- Constraint: F010 在既有 `HostInstallAdapter` 加 `target_context_path` + `target_context_path_user` method; 不创建 `HostContextAdapter` 新 Protocol; F007 既有 `target_skill_path` / `target_agent_path` + F009 既有 `target_skill_path_user` / `target_agent_path_user` 全部签名严格不变

### CON-1007 — Cursor history reader 允许 deferred (HYP-1005)

- 优先级: Should
- 来源: HYP-1005 + § 5.3 D-1010
- Constraint: 如 design ADR 阶段确认 Cursor conversation history 路径不稳定, 允许 cursor 的 `garage session import --from cursor` 降级为 NotImplementedError + 显式 deferred 到 D-1010; claude-code + opencode 必须 in-cycle 落地

## 9. 假设 (ASM)

### ASM-1001 — Path.home() 在所有支持 OS 工作

- 沿用 F009 ASM-902, 不重述

### ASM-1002 — 三家宿主官方文档稳定 (HYP-1001/1002/1003)

- F010 假设三家 first-class adapter 的 context surface 路径在本 cycle 实施期间不变
- 失效影响: sync 写出去也没人 read; 必须重 spec
- Validation: spec 阶段 + manual smoke 双重 verify

### ASM-1003 — 用户日常 host 对话 history 是 file-based

- 假设三家宿主把 conversation history 落到本地 JSON 文件 (而非云端 API)
- 失效影响: ingest 不可实现, 需要 OAuth + API 调用 (out of cycle scope)
- Validation: 本机 ls + 阅读官方文档

### ASM-1004 — F003 既有提取规则对 import 来源 SessionState 适用

- 假设 F003 自动提取的判定逻辑对 host 对话 ingest 出来的 SessionState 也能产出有意义的 candidate
- 失效影响: import 跑通但 candidate 全空 / 全噪音
- Validation: manual smoke Track 3

## 10. INVEST + Phase 0 Anchors 自检

- [x] 问题陈述 + 目标 + 主要用户清楚
- [x] Success Metrics 章节存在 (SM-1001..1004 + Non-goal Metrics)
- [x] Key Hypotheses 章节存在 (HYP-1001..1008 + Blocking 标注)
- [x] 范围内 / 范围外 / Deferred 显式
- [x] 10 FR 全部 ID + Priority + Source + EARS Statement + BDD Acceptance
- [x] 4 NFR 全部 ID + ISO 25010 维度 + QAS 五要素 + Response Measure 阈值
- [x] 7 CON 全部 ID + Source
- [x] 4 ASM 全部 ID + 失效影响 + Validation
- [x] FR/NFR INVEST: 全部 Independent (sync 与 ingest 各自闭环 + cursor history allow deferred); Negotiable (top-N 数值由 design); Valuable (Promise ① / ③); Small (10 FR + 4 NFR + 7 CON 在 design 后可拆 6-7 sub-commit); Testable (BDD 验收)
- [x] HYP-1005 (Cursor history) 显式标注 Low confidence + allow deferred
- [x] CON-1004 user-pact "你做主" 守门显式

## 11. 阻塞性开放问题

### BLK-1001 — sync 触发时机
- 当前 cycle 范围: 仅显式 `garage sync` 触发 (一次性)
- 是否需要 file-watcher / git hook? → **不在本 cycle**, deferred 到 D-1011
- **此问题不阻塞 spec 通过** (design ADR 阶段决定 sync 触发文档)

### BLK-1002 — sync top-N 数值
- N (knowledge entries) / M (experience records) / B (size budget) 默认值
- **由 design ADR 阶段决定**, spec 不固化
- **不阻塞 spec 通过**

### BLK-1003 — Cursor conversation history 路径
- HYP-1005 Low confidence
- design ADR 阶段需 research (本机实测 + Cursor 官方文档 + 社区资料)
- 如确认不可读 → 降级 D-1010 + 修 CON-1007
- **不阻塞 spec 通过**, design ADR 阶段决定

### BLK-1004 — sync 写入 vs 用户手写冲突
- 默认行为: marker 之间覆写, marker 之外字节级保留 (CON-1003 + NFR-1003)
- 如用户手动改了 marker 之间内容怎么办? → **检测并 stderr warn, 不强行覆写; 同时 mtime 不刷新** (与 F007/F009 SKIP_LOCALLY_MODIFIED 同精神)
- **由 design ADR 阶段决定具体行为 (warn-and-skip vs warn-and-force)**, spec 给框架
- **不阻塞 spec 通过**

## 12. 评审前自检 ✅ (供 hf-spec-review)

- [x] FR/NFR/CON/ASM 都有 ID + Priority + Source + EARS/QAS/BDD
- [x] HYP 全部含 Type + Impact + Confidence + Validation; Blocking 标注完整
- [x] Success Metrics + Non-goal Metrics 显式
- [x] § 5 deferred backlog 显式 (D-1010..1015)
- [x] § 11 阻塞性开放问题分类 (BLK-1001..1004)
- [x] CON-1001..1007 守门完整 (含 F009 carry-forward + B5 user-pact)
- [x] CON-1004 + B5 user-pact "你做主" 显式
- [x] manifesto Promise ① + ③ + B4 飞轮 + Stage 2 → 3 升级路径全部 anchor
- [x] 复用 F007 / F009 既有 host adapter pattern + 双 scope, 不重新发明
- [x] F003 / F006 既有提取链 + ranking API 0 改动 (CON-1002)
- [x] 不超出 vision-gap planning § 2.1 范围 (A + B 一起, 不夹带 F011 内容)
