# F007: Garage Packs 与宿主安装器 — 让 `garage init` 把内置 skills/agents 安装到目标 AI 工具

- 状态: 已批准（auto-mode approval；见 `docs/approvals/F007-spec-approval.md`）
- 主题: 在 `packs/` 沉淀 Garage 自带的 `skills/` 与 `agents/` 集合；让 `garage init` 在用户项目里按用户选择的宿主（Claude Code / OpenCode / Cursor 等）把它们安装/同步到对应的工具目录。
- 日期: 2026-04-19
- 关联:
  - F001（Garage Agent 操作系统）— `CON-002` 已声明 "Skills 存放在 `packs/coding/skills/` 和 `packs/product-insights/skills/`"，但今天 `packs/` 目录空缺，HF 系列 skills 仍在 `.agents/skills/` 之下
  - F002（Garage Live）— `garage init` 当前仅创建 `.garage/` 目录树，未做宿主集成
  - `docs/soul/manifesto.md`、`docs/soul/design-principles.md` § 1 宿主无关原则、§ 3 渐进复杂度原则
  - `docs/principles/skill-anatomy.md`（pack 内 skill 的目录 anatomy）
  - 调研参考: OpenSpec `openspec init --tools <list>` 的 host 集成模型（`docs/supported-tools.md`）— 每个宿主有显式 `skills path pattern` + `command/agent path pattern`，由 init 时一次性物化到项目根

## 1. 背景与问题陈述

今天 Garage 仓库里有两类、两个位置的 skills：

| 类型 | 当前位置 | 服务对象 |
|------|---------|---------|
| HF workflow skills（含 `architecture-designer` / `using-hf-workflow` / `hf-*` / `ui-ux-pro-max` / `vision-obey` / `write-blog/*` / `writing-docs` / `writing-skills` 等约 30 个） | `.agents/skills/<skill-name>/SKILL.md` | 当前仓库自身的 AHE 工作流 |
| 计划中的 Garage-bundled packs | `packs/`（**今天空缺**） | 任何挂载 Garage 的下游用户项目 |

`F001 CON-002` 已经把 `packs/coding/skills/` 与 `packs/product-insights/skills/` 写成了项目结构约束，但 `packs/` 目录从未被建出来；`packs/coding/skills/docs/` 这种 family-level 共享路径在 `docs/principles/skill-anatomy.md` 里被多次引用，而仓库里查无此目录。这是个**未兑现的约束**——既不在 spec/design 上闭合，也没有任何 CLI 入口把它生效。

更具体的真实摩擦：

1. **Garage 不能"跟人走"**：`docs/soul/manifesto.md` 的核心承诺是"挂载 Garage 目录后，几秒后 Agent 就变成你的 Agent"。今天用户在自己的项目里执行 `garage init`，得到的只有空的 `.garage/` 目录树——**没有任何 skill 被安装到该项目的 Claude Code / Cursor / OpenCode 能识别的位置**，也就拿不到 HF workflow / 写博客 / UI 设计这些 Garage 已经写好的能力。承诺与实现之间存在缺口。
2. **HF skills 与 Garage-bundled packs 边界不清**：当前 `.agents/skills/` 同时承担两件事——(a) 本仓库自己用的 AHE 节点，(b) 事实上是"Garage 自带、未来要分发给下游用户"的能力。这导致："我能不能改这条 skill"在 Garage 仓库内部没有清晰答案，下游用户项目要不要拷一份也没规则可循。用户在本 cycle 明确："当前这些 packs 下没有内容，后续会把 HF 系列 skills 放到 packs 中"——这条迁移路径需要先有 packs 目录契约和 init-时安装管道，再做内容搬迁。
3. **宿主多样性已经发生**：今天 Garage 仓库 `host_type` 默认硬编码为 `claude-code`（见 `src/garage_os/cli.py` 顶层 `DEFAULT_PLATFORM_CONFIG.host_type` 与 `DEFAULT_HOST_ADAPTER_CONFIG.host_type` 字面赋值 `"claude-code"`），但用户期望覆盖 Claude Code、OpenCode、Cursor 至少三类宿主。这些工具的 skill / agent 目录约定各不相同：
   - Claude Code: `.claude/skills/<name>/SKILL.md`、`.claude/agents/<name>.md`、`.claude/commands/<name>.md`
   - OpenCode: `.opencode/skills/<name>/SKILL.md`、`.opencode/command/<name>.md`、`.opencode/agent/<name>.md`
   - Cursor: `.cursor/rules/*.mdc` 或 `.cursor/skills/<name>/SKILL.md`（取决于 Cursor 版本）+ `.cursor/commands/*.md`
   今天 Garage 没有任何机制把 packs 内容物化到这些位置；用户被迫手工拷文件。
4. **OpenSpec 已经验证过相同形态可行**：`openspec init --tools claude,cursor,opencode` 在 ~25 个宿主上一次性安装 skills + commands；它的关键设计是"每个宿主的 skills/commands path pattern 显式声明，init/update 时按用户选择的子集物化"。Garage 的差别在于：(a) Garage 已有 `.garage/` 运行时数据目录；(b) Garage 的 skills 是"能力基座"，不是单一 workflow 的实现；(c) Garage 主张 host adapter 是真实的语义层（见 `src/garage_os/adapter/`），不仅是路径映射表。OpenSpec 模型可以借鉴**显式 host 列表 + 路径模式 + 安装/扩展两态**这三件事，但要在 Garage 既有 host adapter 抽象上落地。
5. **"宿主无关原则"的隐性违反风险**：如果不显式建立 packs → host 安装的"中立中间层"，下游会出现两类反模式——(a) 直接在 Garage 仓库塞满 `.claude/`、`.cursor/` 等宿主目录（核心约定泄漏到宿主层），(b) skill 内容里写死宿主特定术语（违反 `docs/soul/design-principles.md` § 1 反模式 1）。F007 必须把"中立 packs 内容物 vs 宿主特定物化目标"这条边界用 spec 钉死。

## 2. 目标与成功标准

### 2.1 核心目标

把 Garage 仓库**内置 skills/agents 的源**与**安装到下游项目内宿主目录的动作**显式拆成两层：

```
源：           packs/<pack-id>/skills/<skill-name>/SKILL.md     ← Garage 自带，宿主无关
               packs/<pack-id>/agents/<agent-name>.md           ← Garage 自带，宿主无关

动作：         garage init  ──interactive/--hosts──►  Project root
               ├── .claude/skills/<skill-name>/SKILL.md       (Claude Code)
               ├── .opencode/skills/<skill-name>/SKILL.md     (OpenCode)
               ├── .cursor/...（按 Cursor 当前可用 surface）   (Cursor)
               └── .garage/config/host-installer.json           ← 安装清单（idempotency 凭证）
```

本 cycle 收敛：
- `packs/` 目录契约（结构、front matter、自描述）
- `garage init` 增加宿主选择 / 安装管道（交互 + 非交互双路径）
- 至少三个 first-class host adapter：Claude Code / OpenCode / Cursor
- 安装清单（`.garage/config/host-installer.json`）以支持幂等再运行与 extend mode

**显式不在本 cycle 内**（见 § 5）：
- 把现有 `.agents/skills/` 下 30 个 HF skills 实际搬到 `packs/` —— 用户已说"后续会把 HF 系列 skills 放到 packs 中"，本 cycle 只把容器和管道做出来，让搬迁可以零风险发生。
- `garage uninstall` / `garage update`（host 端 skill 更新拉新）—— 见 § 5 deferred。
- "全局安装到 `~/.claude/skills/`"（OpenSpec issue #752 的全局模式）—— 见 § 5 deferred。

### 2.2 成功标准

1. **零配置可演示**：在一个全新 clone 的 Garage 仓库里，`packs/` 哪怕只有 1-2 条占位 skill（比如 `packs/garage/skills/garage-hello/SKILL.md`），`garage init --hosts claude,cursor,opencode` 一行命令就能在当前目录下创建 `.claude/skills/garage-hello/SKILL.md`、`.cursor/...`、`.opencode/skills/garage-hello/SKILL.md` 三处可被对应宿主识别的文件，退出码 0。
2. **交互 + 非交互双通道**：不带 `--hosts` 时进入交互式选择（多选 checkbox 或 y/n 序列），允许用户挑选要安装的宿主子集；带 `--hosts <comma-list>` 或 `--hosts all` / `--hosts none` 时完全跳过交互（CI/Agent 友好）。
3. **幂等 / Extend Mode**：再次运行 `garage init`（无论同/不同 hosts 子集）必须不破坏已有用户编辑过的工件，且新增宿主只追加新目录、不重写已存在 host 的安装产物。判定路径：依据 `.garage/config/host-installer.json` 与每个被安装文件首末的 Garage 安装标记块（HTML 注释或 front matter `installed_by: garage` 字段）。
4. **宿主无关源 vs 宿主特定目标分层**：`packs/` 源文件中**禁止**出现 Claude Code / OpenCode / Cursor 任一宿主特定的术语、API 或路径；宿主转换发生在 host adapter 层（`src/garage_os/adapter/`），由各 adapter 定义自己的 `target_paths(skill_id, agent_id)` 与可选的 `render(content) -> content`。验收：grep `packs/` 不命中 `.claude/`、`.cursor/`、`.opencode/`、`claude-code` 等宿主关键字。
5. **自描述安装清单**：`.garage/config/host-installer.json` 至少记录 `{ "schema_version": 1, "installed_hosts": [...], "installed_packs": [...], "files": [{"src": "...", "dst": "...", "host": "...", "content_hash": "..."}], "installed_at": "..." }`，让任何后续 Agent 仅凭该文件就能回答 "本仓库装过哪些 host、哪些 pack、哪些文件来自 Garage" 这三个问题。
6. **不破坏 F001-F006 既有契约 / 测试**：`KnowledgeStore` / `ExperienceIndex` / `SessionManager` / `HostAdapterProtocol` / `garage init` 既有 .garage 目录创建行为、`garage status/run/knowledge/memory/recommend/experience` 既有命令面零回归；`uv run pytest tests/ -q` 在 F006 基线 ≥496 测试上仅新增、不退绿。
7. **CLI 文档可冷读**：在 `docs/guides/garage-os-user-guide.md` 增 "Pack & Host Installer" 段，使任何用户从 `garage init --help` 出发即可完成 pack 安装；`packs/` 顶层放 `README.md` 说明目录契约。

### 2.3 非目标

- 不在本 cycle 设计/实现一种新的 skill 调用机制（运行时仍由宿主负责加载 SKILL.md，Garage 不接管 skill 执行）。
- 不在本 cycle 引入新的 skill schema / front matter 字段——`packs/` 内 skill 必须遵循 `docs/principles/skill-anatomy.md` 已定义的 anatomy。
- 不在本 cycle 做 host adapter 的"语义动作"扩展（invoke_skill / read_file / write_file / get_repository_state 行为契约保持 F001 不变，安装器是新增的、与运行时执行解耦的能力）。
- 不在本 cycle 引入对 Cursor / OpenCode 任意一方的 deep integration（如：依赖该宿主的 plugin API、登录态、配置同步）；只做**文件级安装**。
- 不在本 cycle 为 packs 引入跨仓库依赖管理（package manager / lockfile 升级语义）；安装器只是把仓库里已经存在的 packs 内容拷到目标位置。

## 3. 用户角色与关键场景

### 3.1 主要用户角色

- **Solo Creator (人类用户)**：在自己的项目根目录执行 `garage init`，期望被问"你用哪个 AI 工具？"，选完后下次打开 Claude Code / Cursor / OpenCode 就能直接看见 Garage 自带的 HF / 写博客 / UI 设计 skill。
- **CI / Agent 调用方**：自动化场景里跑 `garage init --hosts claude --yes`，期望非交互、可重复、退出码语义稳定。
- **Pack 作者**：未来要往 `packs/` 里加新 skill / agent 的人。期望"我加一个 SKILL.md，它就能被自动安装到所有支持的宿主"，不需要每个 host adapter 都去改代码。
- **Garage 仓库维护者 / 审计读者**：在 `git diff` 看 `.garage/config/host-installer.json` + 各 host 目录变化，期望能直接判断这次安装影响了哪些宿主、覆盖了哪些文件。

### 3.2 关键场景

1. **首次安装（交互）**：用户在 `~/projects/my-app` 目录执行：
   ```bash
   garage init
   ```
   → CLI 创建 `.garage/` 目录后，提示 `Detected hosts you can install Garage packs into:` 并列出 `[ ] claude  [ ] opencode  [ ] cursor`，用户用空格选中 claude+cursor 后回车 → CLI 把 `packs/garage/skills/*/SKILL.md` 复制到 `.claude/skills/` 与 `.cursor/skills/`（或 Cursor 当前等价 surface），写入 `.garage/config/host-installer.json`，stdout: `Installed 12 skills, 3 agents into hosts: claude, cursor`，退出码 0。
2. **首次安装（非交互 / CI）**：
   ```bash
   garage init --hosts claude,opencode
   ```
   → 完全跳过交互，行为同上但只装两个宿主。
3. **再次运行（幂等）**：用户已经运行过 1 次，今天又运行 `garage init --hosts claude,opencode`：CLI 读取 `.garage/config/host-installer.json` → 对每个 file，比较 `content_hash` 与目标位置实际内容；若用户没改过则覆盖更新，若用户已编辑则保留并 stderr 警告 `Skipped <path> (locally modified, pass --force to overwrite)`，退出码 0。
4. **新增宿主**：用户已经装了 claude，今天首次想加 cursor：`garage init --hosts cursor` → 只在 `.cursor/` 下追加，不重写 `.claude/` 下任何文件；`installed_hosts` 字段从 `["claude"]` 变成 `["claude", "cursor"]`。
5. **空 packs 边界**：用户的 Garage 仓库 `packs/` 目录为空（这是 cycle 启动时的真实状态）→ `garage init --hosts claude` 仍应成功完成 .garage/ 创建并写入空 `installed_packs: []`、`files: []`，stdout: `No packs found under packs/, host directories not created.`，退出码 0。这保证 F002 既有 `garage init` 行为（仅创建 `.garage/`）在 packs 缺失时**完全不变**。
6. **未知宿主**：`garage init --hosts notarealtool` → stderr `Unknown host: notarealtool. Supported hosts: claude, opencode, cursor`，退出码 1，**`.garage/` 目录创建仍然成功**（因为这是 F002 既有不可破坏的承诺）。
7. **协助审计**：用户六个月后回来，想知道 `.claude/skills/hf-specify/SKILL.md` 是不是 Garage 装的——只需 `cat .garage/config/host-installer.json | jq '.files[] | select(.dst == ".claude/skills/hf-specify/SKILL.md")'`，能拿到 `src` / `host` / `installed_at` / `content_hash` 四个字段。

## 4. 当前轮范围与关键边界

### 4.1 包含

| 能力 | 描述 |
|------|------|
| `packs/` 目录契约 | 顶层 `packs/<pack-id>/` 下有 `skills/<skill-name>/SKILL.md` 与可选 `agents/<agent-name>.md` 两个子目录；每个 pack 必须有 `pack.json`（`schema_version` / `pack_id` / `description` / `version`） |
| `packs/README.md` | 顶层 README，说明 packs 目录契约、如何写 pack、pack 与 host 的关系 |
| `garage init --hosts <list>` | 新增 `--hosts` 参数：`all` / `none` / 逗号分隔宿主 ID |
| `garage init --yes` | 跳过所有交互（与 `--hosts` 并存时即"非交互非空清单"；不带 `--hosts` 但带 `--yes` 时等价于 `--hosts none`） |
| `garage init --force` | 覆盖目标位置已被本地修改的文件（默认跳过并警告） |
| 交互式宿主选择 | 不带 `--hosts` 也不带 `--yes` 时进入；至少支持空格多选 + 回车确认；TTY 不存在时退化为 `--hosts none` 并 stderr 提示 |
| 三个 first-class host adapter | `claude` / `opencode` / `cursor`，每个 adapter 实现 (a) `target_skill_path(skill_id) -> Path`、(b) `target_agent_path(agent_id) -> Path`（`None` 表示该宿主不支持 agent surface）、(c) 可选 `render(content) -> content`（默认透传） |
| `.garage/config/host-installer.json` | 安装清单 schema 见 § 6 NFR 与 § 9 约束；含 `schema_version` / `installed_hosts` / `installed_packs` / `files[]` |
| 内容指纹 | 每个 `files[]` entry 含 `content_hash` (SHA-256 of installed bytes)，用于幂等比较 |
| 标记块（Should，参 FR-708） | 每个被安装的 SKILL.md / agent.md 在文件首末加 Garage 安装标记（HTML 注释 + 不破坏 SKILL.md front matter parsing），让宿主依然能正常解析；本 cycle 不强求，缺失时改用 manifest 的 `content_hash` 做 "Garage-owned" 判定 |
| 退出码语义 | 0 = 成功（包括"无 packs，无宿主目录写入"）；1 = 输入错误（未知 hosts）；2 = 文件冲突且未带 `--force` |
| 文档 | `packs/README.md` + `docs/guides/garage-os-user-guide.md` 增 "Pack & Host Installer" 段 |

### 4.2 关键边界

- 安装是**单向的**：从 `packs/` → 宿主目录。本 cycle 不做反向（用户改了 `.claude/skills/...` 之后回流到 `packs/`）。
- 安装是**仓库本地的**：始终安装到执行 `garage init` 时的 cwd 项目根（同 F002 当前行为）。本 cycle 不引入 `--global` / 用户家目录安装（OpenSpec issue #752 模式留给 deferred）。
- "宿主"是**已知有限集合**：本 cycle 仅 `claude` / `opencode` / `cursor` 三个；新增宿主必须扩 host adapter 注册表 + spec 增补，不允许通过用户配置注入。
- 安装内容**只看 `packs/` 当前 git 状态**：本 cycle 不下载远程 pack、不解析 lockfile、不跟踪版本依赖。
- Cursor host adapter **以最小可工作的 surface 落地**：先支持 `.cursor/skills/<name>/SKILL.md`（Cursor 已支持的目录），如经研究该路径在用户的 Cursor 版本不可用，allowed 退化为 `.cursor/rules/<name>.mdc`（仍是 Garage 内部决策，不再追加新宿主）。具体落地见 design 阶段。

### 4.3 与 F001 / F002 / F003 / F004 / F005 / F006 的边界

| 既有契约 | F007 影响 |
|---------|----------|
| `garage init` 创建 `.garage/` 目录树（F002） | **保留**，仅在其后追加 host 安装步骤 |
| `DEFAULT_PLATFORM_CONFIG.host_type = "claude-code"`（F001/F002） | **保留**，但与本 cycle "可装到多宿主"是不同维度——`host_type` 描述运行时 invoke_skill 走哪个 adapter；本 cycle 安装清单是物化记录，互不冲突 |
| `HostAdapterProtocol`（F001 adapter 模块） | **不修改**核心 `invoke_skill / read_file / write_file / get_repository_state` 四操作；可在同模块下新增 `HostInstallerProtocol`（独立接口） |
| `KnowledgeStore` / `ExperienceIndex` / Memory 整条管道（F003-F006） | **零回归**，本 cycle 不读写知识/经验存储 |

## 5. 范围外内容（显式 deferred backlog）

下列项目真实存在且会发生，但**显式不在 F007**；按"延后到下一个 cycle"处理：

| 项 | 为什么本 cycle 不做 | 期望落点 |
|----|--------------------|----------|
| 把 `.agents/skills/` 下 30 个 HF skills 真正搬迁到 `packs/coding/skills/` | 搬迁动作是数据迁移，需要先有容器和管道；混在 F007 会让本 cycle review 范围爆炸 | F008 候选 |
| `garage uninstall --hosts <list>` | 安装的逆向操作；F007 先把"装"和"幂等再装"做对 | F008 候选 |
| `garage update --hosts <list>` | 当 packs 内容变化后，重新拉取并对比已安装文件 | F008 候选（与 uninstall 合并 cycle） |
| 全局安装到 `~/.claude/skills/`、`~/.config/opencode/...` | OpenSpec issue #752 模式；对 solo creator 跨多个客户仓库有价值，但与 Garage workspace-first 的"数据归你"信念有 trade-off，应单独 spec 化 | 单独候选，待用户需求再启动 |
| Pack 远程分发 / Marketplace / lockfile 版本管理 | 跨仓库依赖治理，超出 Stage 2 范围 | Stage 3+ 候选 |
| 反向同步：用户在宿主目录修改 → 回流到 `packs/` | 形态会破坏"`packs/` 是源"的单向不变量；需要单独设计冲突解决 | 单独候选 |
| 新增宿主（GitHub Copilot / Codex / Gemini CLI / Windsurf 等） | 每加一个宿主都是 host adapter + 路径模式 + 文档 + 测试；先把 3 个 first-class 验证好 | F008+ 增量候选 |
| 安装时的 LLM 辅助选择（"我看你这个项目用了 React + Tailwind，建议给你装 ui-ux-pro-max skill"） | 与本 cycle 的零依赖原则冲突 | 单独探索性候选 |

## 6. 功能需求

### FR-701 `packs/` 目录契约

- **优先级**: Must
- **来源**: 用户请求 "在 garage 项目的 packs 目录下，skills 和 agents 目录" + F001 `CON-002` 的未兑现约束 + `docs/principles/skill-anatomy.md` 既有 anatomy
- **需求陈述**: 系统必须把 Garage 自带的可分发能力以下列结构沉淀在仓库 `packs/` 目录下——`packs/<pack-id>/skills/<skill-name>/SKILL.md` 与可选 `packs/<pack-id>/agents/<agent-name>.md`，且每个 pack 根含 `pack.json` 元描述。
- **验收标准**:
  - Given 仓库根目录已建立 `packs/garage/skills/garage-hello/SKILL.md` 与 `packs/garage/pack.json`，When 任意 Agent 仅读取 `packs/garage/pack.json` + `packs/README.md`，Then Agent 必须能回答出 (a) 这个 pack 叫什么、(b) 它包含哪些 skill 名、(c) 它的 schema_version 是多少 三个问题。
  - Given `packs/garage/skills/garage-hello/SKILL.md` 内容遵循 `docs/principles/skill-anatomy.md`（含 `name` / `description` front matter），When 安装到任一支持宿主的 skill 目录，Then 该宿主必须能按其原生 skill 加载机制把它识别为 1 个有效 skill。
  - Given 仓库 `packs/` 目录不存在，When 任何用户/Agent 读取，Then `packs/README.md` 必须显式说明 "本目录用于沉淀 Garage-bundled skills/agents；空目录不影响 garage 命令运行"。

### FR-702 `garage init` 增加 `--hosts` 选项

- **优先级**: Must
- **来源**: 用户请求 "询问用户要适配哪些工具，比如 claudecode/opencode/cursor 等" + OpenSpec `--tools` 模型借鉴
- **需求陈述**: 当用户执行 `garage init` 时，系统必须接受可选 `--hosts <list>` 参数，其中 `<list>` 取值为 `all` / `none` / 逗号分隔已知 host id 集合。
- **验收标准**:
  - Given 用户执行 `garage init --hosts claude`，When 命令运行结束，Then 退出码为 0，且 `.garage/config/host-installer.json` 中 `installed_hosts` 字段恰好为 `["claude"]`。
  - Given 用户执行 `garage init --hosts all`，When 命令运行结束，Then `installed_hosts` 字段必须包含本 cycle 支持的全部 first-class 宿主（claude、opencode、cursor）。
  - Given 用户执行 `garage init --hosts none`，When 命令运行结束，Then `installed_hosts` 必须为 `[]` 且**不创建**任何宿主目录，但 `.garage/` 目录树创建必须仍然成功（向后兼容 F002）。
  - Given 用户传入 `garage init --hosts unknownhost`，When 命令运行，Then stderr 必须打印 `Unknown host: unknownhost. Supported hosts: claude, opencode, cursor` 形式的诊断，退出码为 1，且 `.garage/` 目录创建必须仍然成功。

### FR-703 `garage init` 交互式宿主选择

- **优先级**: Must
- **来源**: 用户请求 "在安装的过程中，询问用户要适配哪些工具"
- **需求陈述**: 当用户执行 `garage init` 既不带 `--hosts` 也不带 `--yes` 且 stdin 是 TTY 时，系统必须进入交互式宿主选择，允许用户在已知宿主集合中挑选任意子集后再执行安装。
- **验收标准**:
  - Given 用户在 TTY 下执行 `garage init`（无 `--hosts` / `--yes`），When 提示出现，Then 提示必须列出所有 first-class 宿主，并允许"全部不选 = 空集"作为合法答案。
  - Given 用户在 TTY 下执行 `garage init` 后选中 `claude`、`cursor` 两项，When 提交，Then 安装行为必须等价于 `garage init --hosts claude,cursor`。
  - Given 用户执行 `garage init` 但 stdin 非 TTY（CI 场景）且未传 `--hosts`、未传 `--yes`，Then 系统必须退化为 `--hosts none` 行为并在 stderr 打印一行 `non-interactive shell detected; install no hosts (pass --hosts <list> to override)` 形式提示，退出码 0。

### FR-704 安装管道：`packs/` → 目标宿主目录

- **优先级**: Must
- **来源**: § 2.1 核心目标分层图、§ 3.2 关键场景 1 / 2 / 4 / 5
- **需求陈述**: 当 `garage init` 解析出 `installed_hosts` 非空且 `packs/` 下存在至少 1 个 pack 时，系统必须把每个 pack 的 `skills/<name>/SKILL.md` 与每个 `agents/<name>.md` 按对应 host adapter 给出的目标路径物化到执行目录下；多次运行的宿主集合可以纯追加（不影响其它宿主既有安装产物）。
- **验收标准**:
  - Given 一份位于 `packs/<pack-id>/skills/<skill-id>/SKILL.md` 的 skill 与某 first-class 宿主，When 命令运行结束，Then 该宿主对应 skill 子目录下必须存在该 skill 文件，且其原始 SKILL.md 主体（去除 Garage 安装标记块后）字节级等于源文件。
  - Given 一份位于 `packs/<pack-id>/agents/<agent-id>.md` 的 agent，When 选定宿主的 host adapter 声明该宿主支持 agent surface，Then 该宿主对应 agent 目录下必须存在该 agent 文件；若 host adapter 声明该宿主不支持 agent surface，Then 该宿主目录下必须**不**为该 agent 写文件。
  - Given `packs/` 目录为空，When `--hosts <任一>`，Then 命令仍应退出码 0、`installed_hosts` 非空、`installed_packs: []`、`files: []`，stdout 含 `No packs found under packs/` 形式提示。
  - Given 同名 skill 同时存在于多个 pack，Then 系统必须以确定性失败（退出码 2 + stderr 列出冲突 source/dest）而不是静默覆盖。
  - Given 用户从只装某宿主升级为追加另一宿主，When 仅以新增宿主为参数再次运行 `garage init`，Then 既有宿主下 Garage-owned 文件零变更，新增宿主下文件按本 FR 物化，`installed_hosts` 累加为两个宿主的稳定排序结果。

### FR-705 安装清单：`.garage/config/host-installer.json`

- **优先级**: Must
- **来源**: § 2.2 成功标准 5、§ 4.1 关键边界 / 自描述原则、`docs/soul/design-principles.md` § 4 自描述
- **需求陈述**: 系统必须在每次成功安装结束时，向 `.garage/config/host-installer.json` 写入完整安装清单，schema 至少包含 `{schema_version, installed_hosts, installed_packs, files[], installed_at}`；其中每个 `files[]` entry 至少含 `{src, dst, host, content_hash}`。
- **验收标准**:
  - Given `garage init --hosts claude,cursor` 完成，When 任意 Agent 读取 `.garage/config/host-installer.json`，Then Agent 必须能在不读取源 packs 的前提下回答 (a) 装了哪些宿主、(b) 装了哪些文件、(c) 每个文件来自哪个 src 三个问题。
  - Given 该文件被读取并解析，When 校验，Then `schema_version == 1`、`installed_at` 为 ISO-8601 时间戳、`content_hash` 必须是 SHA-256 hex 形式。
  - Given 用户连续 2 次以相同 `--hosts` 运行 `garage init` 且其间未编辑 packs/目标目录，Then 第 2 次写入的 `files[]` 集合必须与第 1 次按 `(src, dst)` 等价（content_hash 不变）。

### FR-706a 幂等再运行（未修改文件）

- **优先级**: Must
- **来源**: § 3.2 关键场景 3、OpenSpec init 的 Extend Mode 模式
- **需求陈述**: 当 `garage init` 在已存在 `.garage/config/host-installer.json` 的仓库再次运行时，系统必须不破坏既有 `.garage/` 内容；对此前由本工具安装且本地内容 SHA-256 与 manifest 中 `content_hash` 一致（即用户未修改）的目标文件，必须按当前 packs 源版本直接覆盖更新（哪怕字节相同也接受 no-op 写入语义，但应满足 NFR-702 的"无变化时不刷 mtime"约束）。
- **验收标准**:
  - Given 上次安装产生了一份 Garage-owned skill 文件，且其本地 SHA-256 等于 manifest 记录的 `content_hash`，When 再次运行 `garage init --hosts <same-list>`，Then 该文件被认定为"未修改"并按当前 packs 源覆盖更新，stdout 不出现警告。
  - Given 同上但 packs 源未变，When 检查目标文件 `mtime`，Then `mtime` 不被刷新（与 NFR-702 一致）。
  - Given 上次安装产生了一份 Garage-owned skill 文件且 packs 源版本已改变，When 再次运行，Then 目标文件被覆盖为新源内容，且 manifest 中该 entry 的 `content_hash` 同步更新。

### FR-706b 已被本地修改文件的保护与 `--force`

- **优先级**: Must
- **来源**: § 3.2 关键场景 3、`docs/soul/user-pact.md` "数据归你"
- **需求陈述**: 当 `garage init` 再次运行时，对此前由本工具安装但本地内容 SHA-256 已与 manifest 中 `content_hash` 不一致（即用户已编辑）的目标文件，系统必须默认跳过覆盖并向 stderr 打印一行 `Skipped <path> (locally modified, pass --force to overwrite)` 形式提示；仅当用户显式传入 `--force` 时才允许覆盖，并向 stderr 打印 `Overwrote locally modified file <path>` 形式提示。
- **验收标准**:
  - Given 用户修改了某 Garage-owned 目标文件，When 再次运行 `garage init --hosts <same-list>`（无 `--force`），Then 文件**不被覆盖**，stderr 出现上述 `Skipped ... locally modified` 形式 marker，退出码 0。
  - Given 同上场景，When 改加 `--force`，Then 文件被覆盖，stderr 出现 `Overwrote locally modified file ...` 形式 marker，退出码 0。
  - Given 上次安装由 Garage 完成、用户随后用同名手写文件覆盖了目标位置（无 manifest 重写），Then 该文件按 "已被本地修改" 路径处理（与 FR-708 标记块缺失时的回退一致）。

### FR-707 Host Adapter 注册表与扩展点

- **优先级**: Must
- **来源**: § 4.1 三个 first-class host adapter、`docs/soul/design-principles.md` § 1 宿主无关原则
- **需求陈述**: 系统必须维护一个显式 host adapter 注册表，至少包含 `claude` / `opencode` / `cursor` 三项；每个 adapter 必须暴露 (a) "给定 skill id 计算该宿主下的 skill 目标路径" 与 (b) "给定 agent id 计算该宿主下的 agent 目标路径，或声明该宿主不支持 agent surface" 这两类查询能力；可选支持 "在写入前对内容做无副作用的透传渲染" 用于将来按宿主追加/裁剪元数据。注册表驱动 `--hosts all` 的展开与未知宿主的拒绝行为。具体函数签名 / 类与对象划分留给 design。
- **验收标准**:
  - Given 注册表当前包含 `[claude, opencode, cursor]`，When 执行 `garage init --hosts all`，Then `installed_hosts` 必须正好为这 3 项的稳定排序结果。
  - Given 任意一个 adapter 声明该宿主不支持 agent surface，Then 安装管道必须跳过该 agent 在该宿主下的物化，不报错、不在 `files[]` 写入对应记录。
  - Given 任意 adapter 给出的 skill 目标路径，Then 该路径必须是相对于项目根（cwd）的相对路径，且其前缀对应该宿主原生约定的 skill 子目录（具体字面值由 design 决定）；`packs/` 内任何源文件与本 spec 正文均**不得**出现该字面值或其它宿主特定路径硬编码（与 NFR-701 一致）。

### FR-708 安装标记块

- **优先级**: Should
- **来源**: § 2.2 成功标准 3 + § 4.1"不破坏已有用户编辑过的工件"
- **需求陈述**: 当系统把一个 SKILL.md / agent.md 文件物化到宿主目录时，应当在文件首部和/或尾部追加 Garage 安装标记块（HTML 注释形式或宿主可接受的元数据形式），让后续运行可以识别"该文件来自 Garage 安装、可安全更新"。标记块必须不破坏宿主原生的 skill / agent 解析。
- **验收标准**:
  - Given 一个由 Garage 安装的 `.claude/skills/foo/SKILL.md`，When Claude Code 加载该 skill，Then 标记块的存在不应导致 SKILL.md front matter (`name` / `description`) 解析失败。
  - Given 用户手写一个 `.claude/skills/foo/SKILL.md`（没有标记块），When 用户运行 `garage init --hosts claude`，且 packs 内**也**有同名 skill，Then 系统必须按 FR-706b 的 "已被本地修改" 路径处理（默认跳过 + 警告）。

### FR-709 退出码与 stderr/stdout 文案稳定常量

- **优先级**: Should
- **来源**: § 4.1 退出码语义；与 F005 § 9.5 / NFR-504 既有"稳定 stdout marker"约定保持同构
- **需求陈述**: 系统在 init 安装路径上必须使用稳定的 stdout / stderr 文案常量（与 F005 同样在 `cli.py` 顶部声明），让下游 Agent / 测试可基于 grep 匹配，不依赖完整 prose。
- **验收标准**:
  - Given 任意一次成功安装，When 解析 stdout，Then 至少出现 1 条 `Installed N skills, M agents into hosts: <comma-list>` 形式的稳定 marker。
  - Given 任意一次"未知宿主"失败，When 解析 stderr，Then 必须出现 `Unknown host: <name>` 形式 marker。
  - Given 任意一次"locally modified skip"，When 解析 stderr，Then 必须出现 `Skipped <path> (locally modified` 前缀 marker。

### FR-710 文档与可发现性

- **优先级**: Must
- **来源**: § 2.2 成功标准 7、`docs/soul/design-principles.md` § 5 约定可发现
- **需求陈述**: 系统必须随本 cycle 提供至少两份可冷读文档：(a) `packs/README.md` 说明 `packs/` 目录契约；(b) `docs/guides/garage-os-user-guide.md` 增 "Pack & Host Installer" 段，覆盖交互/非交互/extend 三种用法。
- **验收标准**:
  - Given 任意新 Agent / 新用户从仓库根目录开始读，When 顺序读 `AGENTS.md` → `packs/README.md` → `docs/guides/garage-os-user-guide.md` "Pack & Host Installer" 段，Then 必须能在 5 分钟内回答出 (a) `packs/` 与 `.agents/skills/` 的关系、(b) 如何用 1 行命令在自己项目里装上 garage skills、(c) 装完后的文件落到哪儿 三个问题。

## 7. 非功能需求

### NFR-701 宿主无关性 (源)

- **优先级**: Must
- **来源**: `docs/soul/design-principles.md` § 1 宿主无关原则、§ 1.3 反模式 1
- **需求陈述**: `packs/` 下的任意 skill / agent 内容文件**不得**出现宿主特定术语、API 引用或硬编码路径（黑名单：`.claude/` / `.cursor/` / `.opencode/` / `claude-code` / `Claude Code 的 X` 等表述）。宿主语义必须仅出现在 host adapter 实现与本 spec 内。
- **验收标准**:
  - Given 一份新加入 `packs/` 的 SKILL.md，When 用 grep 扫描黑名单关键字，Then 0 命中即视为通过；任何命中视为 spec 违反。
  - Given host adapter 注册表新增宿主，When 仅修改 adapter 与注册表（无需修改任何 `packs/` 内容），Then 所有既有 packs 必须继续可被装到新宿主（除非该宿主 `target_skill_path` 显式不支持）。

### NFR-702 安装幂等性 / 性能

- **优先级**: Should
- **来源**: § 3.2 关键场景 3、Stage 2 飞轮要"用得越多它越强"
- **需求陈述**: 在 packs 总量 ≤ 100 个 skill + 30 个 agent、3 个 host 全装的合成基准下，单次 `garage init` 重复运行（无任何文件变化）的总耗时不应超过 2 秒（user-perceived），且不得对未发生变化的目标文件触发实际写入。
- **验收标准**:
  - Given 上述基准，When 第二次连续运行 `garage init --hosts all`，Then 实测耗时（不含 fork python 解释器启动）≤ 2 秒。
  - Given 同上，When 检查目标文件 `mtime`，Then 未变化的目标文件 `mtime` 不被刷新（即真正实现"无写入"）。

### NFR-703 跨平台路径稳定性

- **优先级**: Should
- **来源**: § 4.1 安装是 "仓库本地的"，但用户机器可能是 macOS / Linux / Windows
- **需求陈述**: 安装管道生成的目标路径必须使用 `pathlib.Path` 抽象，不允许在 spec 或代码中出现写死分隔符的绝对/相对路径常量；`.garage/config/host-installer.json` 中的 `src` / `dst` 字段必须用 POSIX-style 正斜杠 `/`，让 Linux/macOS/Windows 的 git diff 一致。
- **验收标准**:
  - Given 同一 packs 内容在 Linux 与 macOS 上各自 init，When 比较两份 `host-installer.json`（除 `installed_at` 外），Then `files[]` 字段按 `(src, dst, content_hash)` 必须 byte-equal。

### NFR-704 与既有 F001-F006 测试基线零回归

- **优先级**: Must
- **来源**: § 2.2 成功标准 6
- **需求陈述**: 本 cycle 引入的所有变更必须在 `uv run pytest tests/ -q` 下保持既有测试 100% 通过；新增测试覆盖至少 (a) FR-702/703/704/705/706a/706b 的核心 acceptance、(b) NFR-701 grep 检查、(c) host adapter 注册表的扩展点 round-trip。
- **验收标准**:
  - Given F006 基线 ≥496 passed，When F007 实现完成，Then `uv run pytest tests/ -q` 整体计数 ≥ 旧基线 + 新增；旧用例 0 退绿。
  - Given F007 新增了 host installer 模块，When `uv run pytest tests/host_installer/ -q`（或等价目录），Then 至少 10 个新增用例覆盖以上验收。

## 8. 外部接口与依赖

- **依赖**: 仅依赖项目既有 `pyproject.toml` 中已有依赖（`pyyaml`、`filelock`、`atomicwrites`）。本 cycle **禁止新增** TUI 依赖（`questionary` / `inquirerpy` / `rich.prompt` 等）；交互式 prompt 用 stdlib 实现（`input()` + 简单循环）。如 design 阶段确认必须引入额外依赖，须回到 spec 增补一条 `IFR-7xx` 显式记录原因。
- **外部接口（与宿主交互）**: 仅文件系统级——按 host adapter 给出的相对路径写文件、可选追加安装标记块。不调用任何宿主 API、不改任何宿主配置文件、不要求宿主进程运行。
- **AGENTS.md 路径映射**: 本 cycle 不修改 `AGENTS.md`（除非 design / 实施阶段发现必要）；packs 与 host installer 的约定通过 `packs/README.md` + 用户指南承载。

## 9. 约束与兼容性要求

### CON-701 复用 F001 host adapter 模块位置

- **优先级**: Must
- **来源**: F001 既有 `src/garage_os/adapter/` 已是 host 抽象的 home
- **需求陈述**: 本 cycle 的 host adapter 注册表与三个 first-class adapter 实现必须放在 `src/garage_os/adapter/` 下（与既有 `claude_code_adapter.py` 同级或同包），不另起新的顶层包。
- **详细说明**: 这保留 "host 相关代码集中一处"的可发现性；如 design 阶段决定新增 `host_installer/` 子包，仍应位于 `src/garage_os/adapter/` 之下。

### CON-702 不破坏 F002 既有 `garage init` 行为

- **优先级**: Must
- **来源**: F002 已发布行为是 "`garage init` 只创建 `.garage/`"，下游可能已经在用
- **需求陈述**: 调用方式 `garage init`（无任何新参数、无 packs 内容、无既有 `host-installer.json`）的可观察输出必须与 F002 当前行为完全一致——只有 `.garage/` 创建 + 既有 stdout `Initialized Garage OS in <path>`。
- **详细说明**: 新增 `--hosts` 是可选；缺省时不执行宿主选择；交互式提示仅在 TTY + 未带任何相关参数时出现，FR-703 已对 non-TTY 退化作出约束。

### CON-703 schema_version 受 VersionManager 管控

- **优先级**: Should
- **来源**: F001 § "文件即契约" + 既有 `src/garage_os/platform/` `VersionManager`
- **需求陈述**: `.garage/config/host-installer.json` 的 `schema_version` 必须接入 `VersionManager`（与 platform.json / host-adapter.json 同等待遇），任何 schema 变更必须有迁移路径。

### CON-704 工件路径优先 AGENTS.md

- **优先级**: Must
- **来源**: `docs/soul/design-principles.md` § 5 + 项目 AGENTS.md 现状
- **需求陈述**: 文档中提到"安装到 .claude/skills/<name>/SKILL.md"等路径时，必须显式说明 "该路径由对应 host adapter 决定，其值是宿主原生约定"，不得让用户产生 "Garage 自创了一个路径" 的误解。

## 10. 假设

### ASM-701 三个 first-class 宿主的 skill / agent surface 在本 cycle 时段稳定

- **优先级**: Should
- **来源**: 调研得到 OpenSpec `docs/supported-tools.md` 与各宿主公开文档
- **需求陈述**: 假设 Claude Code、OpenCode、Cursor 三家在本 cycle 实施期间各自 `.claude/skills/` / `.opencode/skills/` / `.cursor/skills/`（或等价 surface）目录约定不发生 breaking change。
- **失效风险**: 若某家在 implementation 时段静默改名/弃用，会导致对应 host adapter 安装出去的文件不被识别。
- **缓解措施**: design 阶段为每个 adapter 显式记录其 path pattern 来源（链接到该工具公开文档或 OpenSpec `supported-tools.md`），并在 implementation 后跑一次三家宿主的 smoke 验证（人工或脚本）。

### ASM-702 用户能区分 "Garage 仓库自身"与 "下游用户项目"

- **优先级**: Could
- **来源**: 用户请求场景 "在一个项目的目录下执行 garage init"
- **需求陈述**: 假设用户理解 packs 来自 Garage 仓库（`packs/<pack-id>/...`），而 `garage init` 是在另一个项目目录里运行的——即两套目录可以是同一个 git 仓库（dogfooding）也可以是不同仓库；本 cycle 不强制后者。
- **失效风险**: 若用户在 Garage 仓库自身执行 `garage init --hosts claude`，会看到自己的 `.claude/skills/` 出现 packs 内容；这是预期行为，但可能引起混淆。
- **缓解措施**: `packs/README.md` 显式给出 "Garage 仓库内 dogfood 安装" 与 "下游项目使用 Garage 安装" 两段清晰示例。

### ASM-703 用户优先用 git 而非 OS 备份保护被本地修改的文件

- **优先级**: Should
- **来源**: F005-F006 一贯假设
- **需求陈述**: 假设用户在让 `garage init --force` 覆盖已修改文件前，已经 `git status` 检查过差异。
- **失效风险**: 用户误用 `--force` 会丢失本地修改。
- **缓解措施**: `--force` 触发覆盖时，stderr 必须打印 `Overwrote locally modified file <path>`，让 `git status` 之后能立刻看到差异。

## 11. 开放问题

### 阻塞性（必须在 hf-spec-review 通过前关闭）

当前**无阻塞性开放问题**。若 spec reviewer 发现以下任一项摇摆，应反馈以阻塞 finding 形式提出：
- 三个 first-class 宿主集合是否就是 `claude / opencode / cursor`，或还应在本 cycle 包含 `codex` / `gemini` / `windsurf`
- 是否在本 cycle 引入 `--global` 安装路径（OpenSpec issue #752 模式）

### 非阻塞性（可在 design 阶段细化）

1. Cursor 当前 stable 版本对 `.cursor/skills/<name>/SKILL.md` 与 `.cursor/rules/*.mdc` 两套 surface 的支持优先级——需要 design 阶段做一次轻量调研选定，本 spec 接受 "由 host adapter 决定"。
2. 安装标记块的具体形式（HTML 注释 vs `installed_by: garage` front matter 字段）——本 spec 只约束"不破坏宿主原生解析"，具体形式由 design 阶段决定。
3. 交互式 prompt 是用 stdlib `input()` 多行 yes/no 还是简单数字编号选择菜单——本 spec 接受任一方案，前提是不引入新依赖。
4. 是否在 `packs/<pack-id>/` 下区分 `coding` / `product-insights` 等子 pack（F001 CON-002 既有约束），或先在本 cycle 收敛为单一 `packs/garage/`——design 阶段决定，spec 不强制。

## 12. 术语与定义

| 术语 | 定义 |
|------|------|
| **Pack** | 一组以共同主题打包的 Garage skills + agents，目录形态 `packs/<pack-id>/skills/...`、`packs/<pack-id>/agents/...`，含 `pack.json` 元描述 |
| **Host** | 一个能加载 SKILL.md 的 AI 工具，本 cycle first-class 集合为 `claude`（Claude Code）、`opencode`（OpenCode）、`cursor`（Cursor） |
| **Host Adapter** | 把 Garage 中立 pack 内容映射到具体宿主目录约定的代码组件，至少给出 `target_skill_path` / `target_agent_path` |
| **Host Installer** | 把 packs 物化到目标宿主目录的执行管道，本 cycle 集成进 `garage init` |
| **Install Manifest** | `.garage/config/host-installer.json` 上记录的安装清单，作为幂等再运行的凭证 |
| **Extend Mode** | 当 manifest 已存在时再次运行 `garage init`，行为收敛为"对未修改文件刷新、对已修改文件跳过、对新增 host 追加" |
| **First-class Host** | 本 cycle 显式覆盖、有 acceptance 测试保护的宿主集合（claude / opencode / cursor） |

