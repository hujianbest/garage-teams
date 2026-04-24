# F009: `garage init` 双 Scope 安装（project / user）+ 交互式 Scope 选择

- 状态: 草稿
- 主题: 让 `garage init` 在装到下游宿主时支持两种 scope（project 当前项目 / user 用户家目录），并在交互式入口让用户每个宿主独立选 scope；非交互入口提供新 flag 显式声明 scope
- 日期: 2026-04-23
- 关联:
  - F001 § `CON-002` — packs/ 目录契约
  - F002 — `garage init` 既有 `.garage/` 创建行为（CON-702 必须保留）
  - F007 — `packs/<pack-id>/` 目录契约 + `garage init --hosts ...` 安装管道 + manifest schema + 三家 first-class adapter（claude / opencode / cursor）
  - F008 — packs 内容物从 1 sample 扩到 29 真实可用 skill；本 cycle 在 F008 落地的 packs 内容物上添加 scope 选择维度
  - `docs/soul/manifesto.md`、`user-pact.md`、`design-principles.md`、`growth-strategy.md`（特别 user-pact "数据归你" + design-principles workspace-first 信念）
  - F008 spec § 5 deferred backlog 第 3 行 "全局安装到 `~/.claude/skills/...`（OpenSpec issue #752 模式）：solo creator 跨多客户仓库的需求；与 Garage workspace-first 信念有 trade-off，应单独 spec 化" — 本 spec 即是该候选的正式落地
  - 调研锚点：
    - Anthropic Claude Code 官方文档：personal scope `~/.claude/skills/<id>/SKILL.md`，project scope `.claude/skills/<id>/SKILL.md`，加载优先级 enterprise > personal > project（详见 https://code.claude.com/docs/en/skills）
    - OpenCode 官方文档：global config XDG `~/.config/opencode/skills/<id>/SKILL.md` + dotfiles 风格 `~/.opencode/skills/<id>/SKILL.md` 二者皆支持（详见 PR #6174 onerepoco/opencode）
    - Cursor 官方文档：user-level `~/.cursor/skills/<id>/SKILL.md`，project-level `.cursor/skills/<id>/SKILL.md`（详见 https://cursor.sh/docs/skills）

## 1. 背景与问题陈述

F008 cycle 把 `garage init --hosts <list>` 装到的内容物从 F007 的 1 个占位 sample skill 扩到 29 个真实可用 skill（22 hf-* + 4 write-blog + find-skills + writing-skills + garage-hello），下游用户挂载 Garage 后立刻获得完整 SDD + 闸 TDD 工程工作流 + 内容创作 family。**但 F008 cycle 落地的 `garage init` 仅支持 project scope 安装**——所有 29 个 skill 全部装到执行 `garage init` 时的 cwd 项目根（`<cwd>/.claude/skills/`、`<cwd>/.cursor/skills/`、`<cwd>/.opencode/skills/`）。

F008 spec § 5 deferred backlog 已明确指出："全局安装到 `~/.claude/skills/...`（OpenSpec issue #752 模式）：solo creator 跨多客户仓库的需求；与 Garage workspace-first 信念有 trade-off，应单独 spec 化"。本 cycle 即是该候选的落地，并叠加用户现在提出的新需求："**安装时让用户选** scope"。

### 真实摩擦

1. **solo creator 跨多客户仓库的痛点**：Garage 主用户是 solo creator（参见 `docs/soul/user-pact.md`），常常在多个客户/雇主项目仓库间切换工作。当前 F008 行为要求每个项目都跑一次 `garage init`，每个项目的 `.claude/skills/` 等都堆 29 份 SKILL.md 副本，git 干净度受影响（虽然各宿主目录通常不入 git，但项目根多出 3 个 dotfile 目录）；更关键的是用户希望"我的 hf-* workflow + 我的写博客 skill 是跟着**我**走，不是跟着每个客户项目走"。
2. **三家宿主官方都已支持 user scope**（实测见调研锚点）：Claude Code / OpenCode / Cursor 三家在 2026 年 Q2 时已经全部把 personal / global / user-level scope 作为一等约定列入官方文档；Garage 作为"宿主无关能力基座"反而只支持 project scope，这是与下游真实生态的不对齐。
3. **每个宿主独立选 scope 的复合场景真实存在**：用户可能希望 hf-* workflow 装到 Cursor user scope（"跟着我走"，所有项目都能用），但同时把 packs/coding 装到当前项目的 `.claude/skills/` project scope（"团队共享"，commit 进 git）。一刀切的"全 user 或全 project"不够。
4. **当前 F008 ADR-D8-2 候选 C dogfood 路径假设 project scope**：本仓库自身贡献者首次 clone 后跑 `garage init --hosts cursor,claude` → 在仓库根创建 `.cursor/skills/` + `.claude/skills/`。这个 dogfood 路径是项目级的（验证 packs 装到本仓库），与 user scope 安装是不同决策：dogfood 应继续 project scope，但用户在自己其它项目里可能想 user scope。F009 必须显式分清这两个用法。
5. **OpenSpec issue #752 模式参考点**：spec 调研期发现 OpenSpec 已在某 issue 提出过类似需求并讨论 trade-off（见 F008 spec § 5 deferred 行的 "OpenSpec issue #752 模式" 引用），其核心争议正是"workspace-first 信念 vs 跨项目复用便利性"；F009 必须显式做这个 trade-off 评估，而不是默认抄 OpenSpec 实现。
6. **manifest 不再适合用单一项目根**：F007 落下的 `.garage/config/host-installer.json` schema 假设所有 dst 都是 `workspace_root` 相对路径。如果同一次 init 既装 user scope 又装 project scope，manifest 必须能同时记录两种 dst（绝对路径或带 scope 标识），否则幂等再装 / extend mode / `--force` 都会断裂。这是 F007 manifest schema 的延展点。

## 2. 目标与成功标准

### 2.1 核心目标

把 F007/F008 落下的 `garage init --hosts <list>` 安装管道扩展为支持双 scope，并在交互式入口让用户每个宿主独立选 scope：

```
                F007/F008 (现状)                          F009 (本 cycle)
                ───────────────                          ────────────────
非交互：        garage init --hosts claude               garage init --hosts claude
                → 装到 <cwd>/.claude/skills/             → 装到 <cwd>/.claude/skills/  (project, 默认行为不变)

                                                          garage init --hosts claude --scope user
                                                          → 装到 ~/.claude/skills/  (user scope, 新增)

                                                          garage init --hosts claude:user,cursor:project
                                                          → claude 装到 ~/.claude/skills/, cursor 装到 <cwd>/.cursor/skills/
                                                            (per-host scope override, 新增)

交互：          garage init                              garage init
                → "你用哪些宿主？" (单维度选择)           → "你用哪些宿主？每个装到哪个 scope？"
                → 全部装到 cwd                             (双维度选择, 新增)
```

本 cycle 收敛：
- `garage init` 接受新 `--scope` flag（全局默认）+ per-host override 语法（`<host>:<scope>`）
- 交互式入口为每个选定宿主独立提示 scope 选择（默认 project，按 down arrow / 输入 `u` 切 user）
- F007/F008 既有非交互行为（`--hosts <list>` 不带 `--scope`）默认 project scope，**字节级不变**（CON-901 / 沿用 F007 CON-702 精神）
- 三家 first-class adapter 各加一个 user-scope 路径解析方法（claude → `~/.claude/skills/`, opencode → `~/.config/opencode/skills/`（XDG default），cursor → `~/.cursor/skills/`）
- manifest schema 扩展（schema_version=1 → 2）：`files[].dst` 改为 absolute path（向后兼容旧 schema 通过 schema migration），新增 `files[].scope` 字段（"project" / "user"）
- 单次 `garage init` 同时装多 scope 时，manifest 完整记录每个文件归属的 scope（让幂等再装能精确比对）
- `garage status` 显示当前安装清单时按 scope 分组展示

**显式不在本 cycle**（详见 § 5）：
- 不引入 enterprise scope（Anthropic Claude Code 官方有但太重，solo creator 用不到）
- 不引入 plugin scope
- 不引入 user scope 下的 enterprise / personal / project 三层优先级语义（这是宿主自己解析时的 fallback 优先级，Garage 只负责装到指定 scope，不替宿主决定优先级）
- 不引入 `garage uninstall --scope <scope>` 或 `garage update --scope <scope>` 反向操作（与 F009 正交，留给 F010 候选）
- 不引入跨平台 user-home 推导的复杂 fallback（仅用 `Path.home()` 标准 stdlib API，Windows 在 `Path.home()` 默认行为下解析 `%USERPROFILE%`）

### 2.2 成功标准

1. **F007/F008 既有调用形态字节级不变（CON-901）**：`garage init`（无任何参数）+ `garage init --hosts claude`（无 `--scope`）+ `garage init --hosts all --yes` 三个最常见调用形态的 stdout / stderr / 退出码 / `.garage/` 目录创建 / `<cwd>/.{host}/skills/` 落盘行为与 F008 closeout 时完全一致。
2. **`--scope user` 端到端可演示**：在干净下游项目执行 `garage init --hosts claude --scope user` 后，`~/.claude/skills/` 下立即出现 packs 内容物 29 份 SKILL.md（按 manifest 计数派生），`<cwd>/.claude/skills/` **不**被创建；`<cwd>/.garage/config/host-installer.json` 仍写入安装清单，`files[].dst` 字段为 user scope 绝对路径，`files[].scope == "user"`。
3. **per-host override 端到端可演示**：`garage init --hosts claude:user,cursor:project` 后，`~/.claude/skills/` 与 `<cwd>/.cursor/skills/` 同时出现 SKILL.md，manifest 中两类 entry 的 `scope` 字段分别为 `"user"` 与 `"project"`。
4. **交互式 per-host scope 选择可演示**：TTY 下 `garage init` 进入交互式时，对每个被用户选中的宿主独立提示 "Install to project (.claude/skills/) or user (~/.claude/skills/)? [P/u]"，默认 P（project）兼容 F007/F008 行为；输入 `u` 切到 user scope；用户可在多宿主间组合。
5. **manifest schema migration 平滑**：F008 cycle 已经装过的 manifest（schema_version=1）在 F009 第一次 `garage init` 时自动迁移到 schema_version=2，旧 entry 默认补 `scope: "project"` + `dst` 转绝对路径；migration 由 `VersionManager` 接管，无需用户操作；旧 manifest 的字段含义在 F009 后仍可由任何 Agent 冷读（向后兼容文档）。
6. **幂等再装 / `--force` 行为分 scope 工作**：再次 `garage init --hosts claude --scope user` 时，对 user scope 下未修改文件按 source 覆盖（NFR-702 mtime 不刷新），对已修改文件默认跳过（与 F007 FR-706a/706b 完全等价，仅作用域不同）；project scope 与 user scope 之间的 manifest entry 互不串扰。
7. **F007 三家宿主 adapter 不破坏向后兼容**：`HostInstallAdapter` Protocol 新增可选方法 `target_skill_path_user(skill_id)` / `target_agent_path_user(agent_id)`（带 `_user` 后缀以与 F007 既有 method 区分），既有 `target_skill_path` / `target_agent_path` 仍代表 project scope 的相对路径不变；新方法返回**绝对路径**（`Path.home() / ...` 形态），与 project scope 的相对路径不同语义但同 Protocol，便于 pipeline 区分。
8. **F008 NFR-801 / ADR-D8-9 EXEMPTION_LIST 仍有效**：本 cycle 不动 packs/ 内容物，不动 EXEMPTION_LIST；只是装到的目标位置变化。三层守门（spec / design / 测试常量）继续工作。
9. **F008 dogfood 路径不被破坏**：本仓库自身的 `garage init --hosts cursor,claude` 仍默认 project scope，dogfood 产物落到 `<workspace>/.cursor/skills/` + `<workspace>/.claude/skills/`，与 F008 ADR-D8-2 候选 C 完全等价；只有用户在自己其它项目里需要时才显式切 `--scope user`。
10. **测试基线零回归**：`uv run pytest tests/ -q` 整体计数 ≥ F008 baseline 633，旧用例 0 退绿；新增测试至少覆盖 (a) 三家 adapter 的 user-scope path 解析 (b) `--scope` flag 解析 + per-host override 语法 (c) manifest schema migration 1 → 2 (d) 幂等分 scope 守门 (e) `garage status` 按 scope 分组。
11. **CON-902 严守"D7 安装管道核心算法不动"**：`pipeline.install_packs` 函数体的 phase 1-5 算法骨架（discover → resolve targets → check conflicts → decide action → apply + manifest）不被破坏；本 cycle 仅在 phase 2 resolve targets 增加 scope 维度（target.dst_abs 拼接根从 `workspace_root` 改为按 scope 分流的 `workspace_root` 或 `Path.home()`），其它 phase 算法字节级不变。

### 2.3 非目标

- 不引入 enterprise scope（Anthropic 官方有但 solo creator 用不到，加进来会让 trade-off 评估更复杂）
- 不实现 `garage uninstall --scope <scope>` / `garage update --scope <scope>`（F010 候选）
- 不引入"自动检测当前用户更适合哪个 scope"的 LLM 辅助（与 manifesto "你做主" 信念冲突）
- 不引入 `~/.garage/config/host-installer.json` 全局 manifest（每次 `garage init` 仍只写一份 manifest 到 `<cwd>/.garage/config/host-installer.json`，user scope 装的文件由该 manifest 跨 scope 完整记录）
- 不修改 packs/ 内容物（F008 已落 29 skill，本 cycle 不增不减不改）
- 不引入第四个宿主（Codex / Gemini CLI / Windsurf 等仍按 F008+ 增量候选处理）
- 不实现 `~/.claude/skills/<id>/SKILL.md` 与 `<cwd>/.claude/skills/<id>/SKILL.md` 同名 skill 的 Garage 侧优先级解析（这是宿主自己解析的事，Garage 只负责物化）
- 不实现 OpenCode `~/.opencode/skills/` (dotfiles 风格) vs `~/.config/opencode/skills/` (XDG 标准) 的双路径自动选择 — 默认走 XDG，dotfiles 风格留给 deferred / `--scope user-dotfiles` 子选项（design 阶段决定是否引入）

## 3. 用户角色与关键场景

### 3.1 用户角色

- **Solo Creator (跨多客户项目)**：在多个客户/雇主项目仓库间切换工作，希望 hf-* workflow + 写博客 skill 跟着自己走（user scope），但每个客户项目的特定 skill 仍在项目内维护（project scope）
- **Solo Creator (单项目专注)**：只在一两个项目内工作，倾向 project scope（与 F007/F008 行为一致），不需要 user scope 增量复杂度
- **CI / Cloud Agent 调用方**：希望非交互可重复，新增 `--scope user` flag 必须能在 CI script 内显式声明，不依赖交互
- **Pack 作者 / 维护者**：未来加新 skill / pack 时不需要意识到 scope（packs/ 内容物与 scope 无关）
- **Garage 仓库自身（dogfood）**：本仓库自身贡献者首次 clone 后跑 `garage init --hosts cursor,claude` 仍走 project scope（与 F008 ADR-D8-2 一致），不被 F009 影响
- **审计读者**：6 个月后查看 `host-installer.json` 想知道某个 SKILL.md 装到哪了，应能从 `files[].dst` (绝对路径) + `files[].scope` 字段直接读出来

### 3.2 关键场景

1. **F007/F008 兼容（最常见，CON-901）**：
   ```bash
   cd ~/projects/my-app
   garage init --hosts claude
   # 行为完全等价 F008: 装到 ~/projects/my-app/.claude/skills/, 29 skills + 1 agent
   ```

2. **新增：单宿主 user scope**：
   ```bash
   cd ~/projects/my-app
   garage init --hosts claude --scope user
   # 装到 ~/.claude/skills/ (29 skill), 不创建 my-app/.claude/skills/
   # ~/projects/my-app/.garage/config/host-installer.json 仍写, files[].scope == "user"
   ```

3. **新增：全宿主统一 user scope**：
   ```bash
   garage init --hosts all --scope user
   # 装到 ~/.claude/skills/ + ~/.cursor/skills/ + ~/.config/opencode/skills/
   # 87 skill (29 × 3 host), agent 装到 ~/.claude/agents/ + ~/.config/opencode/agent/ (cursor 无 agent surface)
   ```

4. **新增：per-host scope mix**：
   ```bash
   garage init --hosts claude:user,cursor:project
   # claude 装到 ~/.claude/skills/, cursor 装到 cwd/.cursor/skills/
   # manifest 含两类 entry, scope 字段分别 "user" / "project"
   ```

5. **新增：交互式 per-host 选择（TTY 用户首选）**：
   ```bash
   garage init
   # 第一轮: 选哪些宿主？[claude, cursor, opencode] (现有 F007 行为)
   # 第二轮（新增）: 对每个选中宿主独立问:
   #   "Install claude skills to: [P]roject (./.claude/skills/) or [u]ser (~/.claude/skills/)? [P/u]: " → 默认 P
   #   "Install cursor skills to: [P]roject or [u]ser? [P/u]: " → 默认 P
   # 用户输入: P, u → claude project + cursor user
   # 等价于 garage init --hosts claude:project,cursor:user
   ```

6. **幂等再装（user scope 内）**：
   ```bash
   # 第一次
   garage init --hosts claude --scope user
   # 第二次 (无变化, NFR-702 mtime 严格幂等)
   garage init --hosts claude --scope user
   # → manifest schema 不变, 文件 mtime 不刷新, stdout 仍 "Installed N skills..."
   ```

7. **混合 scope 幂等**：
   ```bash
   # 第一次: claude project + cursor user
   garage init --hosts claude:project,cursor:user
   # 第二次同样命令
   # → 两类文件分别幂等, manifest 准确比对每个文件 scope+dst 二元组的 content_hash
   ```

8. **从 F008 manifest 自动迁移到 F009 schema_version=2**：
   ```bash
   # F008 用户已经跑过 garage init --hosts claude
   # 今天升级 Garage, 跑 garage init --hosts claude --scope user
   # → manifest schema 1 → 2 自动 migration, 旧 entry 补 scope: "project" + dst 转绝对路径
   # → 新 entry (user scope) 与旧 entry (project scope) 在同一 manifest 共存
   ```

9. **`garage status` 按 scope 分组**：
   ```bash
   garage status
   # → 输出含 "Installed packs:" 段, 按 scope 分组:
   #   project: 29 skills (claude 29) at .claude/skills/
   #   user:    29 skills (cursor 29) at ~/.cursor/skills/
   ```

10. **未知 scope 错误**：
    ```bash
    garage init --hosts claude --scope unknown
    # → exit code 1, stderr: "Unknown scope: unknown. Supported scopes: project, user"
    ```

11. **per-host scope 语法错误**：
    ```bash
    garage init --hosts claude:bad
    # → exit code 1, stderr: "Unknown scope: bad in 'claude:bad'. Supported scopes: project, user"
    ```

12. **dogfood 不受影响**：
    ```bash
    cd /workspace  # Garage 仓库自身
    garage init --hosts cursor,claude
    # → 与 F008 完全等价, 装到 /workspace/.cursor/skills/ + /workspace/.claude/skills/
    # → AGENTS.md "本仓库自身 IDE 加载入口" 段无需更新
    ```

## 4. 当前轮范围与关键边界

### 4.1 包含

| 能力 | 描述 |
|------|------|
| **`--scope` flag** | `garage init --hosts <list> --scope <scope>`：`<scope>` ∈ {`project`, `user`}；缺省 `project` |
| **per-host scope override 语法** | `--hosts claude:user,cursor:project`：支持 `<host>` 与 `<host>:<scope>` 两种形式混合，per-host scope 覆盖 `--scope` 全局默认 |
| **交互式 per-host scope 选择** | TTY 下不带 `--hosts` / `--scope` 时进入两轮交互：第一轮选宿主（F007 行为不变），第二轮对每个选中宿主独立问 scope（默认 P/project，输入 `u` 切 user）|
| **三家 first-class adapter user scope path** | 在 `HostInstallAdapter` Protocol 新增 optional `target_skill_path_user` + `target_agent_path_user` method（返回 absolute Path）；三家实现：claude `~/.claude/skills/<id>/SKILL.md` + `~/.claude/agents/<id>.md`；opencode `~/.config/opencode/skills/<id>/SKILL.md` + `~/.config/opencode/agent/<id>.md`（XDG 默认）；cursor `~/.cursor/skills/<id>/SKILL.md`（无 agent surface）|
| **manifest schema 1 → 2 migration** | `.garage/config/host-installer.json` `schema_version: 2`：`files[].dst` 改为 absolute path（POSIX serialization）；新增 `files[].scope` 字段（`"project"` / `"user"`）；旧 schema 1 manifest 自动 migration 时所有 entry 补 `scope: "project"` + dst 由 relative 转 absolute（`workspace_root / dst`）；migration 由 `VersionManager` 接管 |
| **pipeline scope 拼接根分流** | `_resolve_targets` 中按 target scope 选 base path：project 用 `workspace_root`（F007 既有），user 用 `Path.home()`；其它 phase 不变（discover / conflict / decide / apply / manifest 整算法骨架不动）|
| **退出码扩展** | F007 退出码语义不变（0 / 1 / 2）；新增 unknown scope → exit 1（与 unknown host 同级）|
| **`garage status` 按 scope 分组** | 显示 manifest 时按 scope 分组（project / user），每组下按 host 子分组，类型 + 计数 + dst 前缀 |
| **stdout marker 派生** | `Installed N skills, M agents into hosts: <list>` 格式不变；新增可选附加段 `(N_user user-scope, N_project project-scope)` 仅当存在多 scope 时显示 |
| **文档** | `packs/README.md` 增 "Install scope" 段；`docs/guides/garage-os-user-guide.md` "Pack & Host Installer" 段加 `--scope` 用法 + 交互示例；`AGENTS.md` § "Packs & Host Installer (F007/F008)" 升级到 F007/F008/F009 + 新增 "Install scope" 子段 |

### 4.2 关键边界

- **F007 安装管道核心算法不变（CON-902）**：`pipeline.install_packs` 5 个 phase 算法骨架字节级不变；只 phase 2 `_resolve_targets` 内增加 scope 维度的 base path 分流（不改函数签名，但 `_Target` dataclass 增 `scope` 字段）
- **manifest schema migration 单向**：1 → 2 自动迁移，无 2 → 1 反向（与 F007 CON-703 + VersionManager 既有 schema migration 政策一致）
- **`Path.home()` stdlib 标准**：仅用 stdlib，不引入额外的 user home 推导库；Windows 在 `Path.home()` 默认行为下解析 `%USERPROFILE%`（NFR 不强约束 Windows 实测，沿用 F007 ASM 同精神）
- **OpenCode 默认走 XDG `~/.config/opencode/`**：dotfiles 风格 `~/.opencode/` 留给 deferred backlog（design 阶段决定是否加 `--scope user-dotfiles` 子选项）
- **不动 `HostInstallAdapter` Protocol 既有 method 签名**：`target_skill_path` / `target_agent_path` / `render` 行为不变；新增 `_user` 后缀 method 与既有 method 是 sibling，不破坏 F007 既有调用方
- **不动 packs/ 内容物**：本 cycle 是 CLI + adapter + pipeline + manifest 扩展，不增不减不改 packs/ 内任何 SKILL.md / family asset / pack.json / README
- **不动 F008 ADR-D8-9 EXEMPTION_LIST**：F008 的 NFR-801 文件级豁免规则继续生效，本 cycle 不动 EXEMPTION_LIST 7 项
- **dogfood 不受影响**：本仓库自身 `garage init --hosts cursor,claude`（无 `--scope`）默认 project scope，与 F008 ADR-D8-2 候选 C 完全等价
- **scope 不引入新的优先级语义**：Garage 只负责"装到 user scope" 或 "装到 project scope"，不替宿主决定加载时哪个 scope 优先（宿主自己有 enterprise/personal/project/plugin 4 级优先级，Garage 不触碰）

### 4.3 与 F001-F008 的边界

| 既有契约 | F009 影响 |
|---------|----------|
| `garage init` 缺省行为（无任何 flag）创建 `.garage/`（F002 CON-702） | **零修改**，CON-901 沿用 F002 CON-702 精神严守 |
| `garage init --hosts <list>` 接口（F007 FR-702） | **新增** `--scope` flag + per-host override 语法；既有 `--hosts <list>` 不带 `--scope` 行为字节级不变 |
| 安装管道 `src/garage_os/adapter/installer/pipeline.py`（F007 FR-704）| **最小改动**：5 phase 算法骨架不动，仅 phase 2 内增 scope 分流 |
| 安装清单 `.garage/config/host-installer.json` schema（F007 FR-705 / CON-703）| **schema 1 → 2 升级**，by VersionManager 自动迁移；旧 schema 字段含义保留可冷读 |
| Extend mode + content_hash 幂等（F007 FR-706a/706b）| **保留**，scope 加入比对 key（`(src_rel, dst_abs, host, pack_id, scope)` 五元组替换 F007 的 `(src_rel, dst_rel, host, pack_id)` 四元组）|
| Host adapter 注册表（F007 FR-707）| **不变**，仍 claude / opencode / cursor 三家；adapter 实现增 `_user` 后缀 method |
| 安装标记块（F007 FR-708）| **不变**，marker 注入与 scope 无关 |
| 退出码 / stdout/stderr marker（F007 FR-709）| **保留**；新增 unknown scope → exit 1；stdout marker 在多 scope 时附加段 |
| 同名 skill 跨 pack 冲突检测（F007 FR-704 #4）| **保留**，且扩展为同 scope 内冲突检测（不同 scope 不视作冲突）|
| F008 packs/ 内容物（22 + 3 + 4 = 29 skill + 1 agent）| **零修改** |
| F008 ADR-D8-1 family-level 资产物理位置 | **零修改** |
| F008 ADR-D8-2 dogfood 候选 C | **保留**，dogfood 默认 project scope，与 F008 行为完全等价 |
| F008 ADR-D8-3 drift 反向同步 + sentinel test | **保留** |
| F008 ADR-D8-4 文档级提示边界 | **保留**，本 cycle 仍不递归 references/ 子目录（D7 管道不动） |
| F008 ADR-D8-9 EXEMPTION_LIST | **保留** 7 项 |
| F008 INV-1..9 | **保留**，新增 INV F009 系列（详见 design 阶段） |

## 5. 范围外内容（显式 deferred backlog）

| 项 | 为什么不做 | 期望落点 |
|----|--------------------|----------|
| `garage uninstall --scope <scope>` | 与本 cycle 正交；先做安装两端再做反向 | F010 候选（与 update 同 cycle）|
| `garage update --scope <scope>` | 同上 | F010 候选 |
| Enterprise scope（Anthropic 官方有）| Solo creator 用不到；加入会让 trade-off 评估更复杂 | 单独候选，待企业用户需求 |
| Plugin scope | 同上 | 单独候选 |
| OpenCode dotfiles 风格 `~/.opencode/skills/` 子选项 | XDG 默认已覆盖 90%+ 用户；dotfiles 风格是少数偏好 | 单独 `--scope user-dotfiles` 子选项候选（design 决定是否本 cycle 加） |
| 跨 scope 同名 skill 自动 dedupe / 优先级解析 | Garage 不替宿主决定加载优先级 | 不做，宿主自己负责 |
| `~/.garage/config/host-installer.json` 全局 manifest | 与 workspace-first 信念冲突；每次 init 仍只写一份 cwd manifest | 不做（manifesto "数据归你" 锚点）|
| Cursor 老版本兼容（`.cursor/rules/<name>.mdc` fallback）| F007 已 deferred，本 cycle 不动 | 单独候选 |
| 装到任意 `--prefix <path>` 自定义路径 | 超出 user/project 二分常见场景；用户可自己 ln -s 实现 | 单独候选 |
| user scope 安装时的 `~/.garage/config/` 写入 | 与"零 user 全局 manifest"决定一致，不写 | 不做 |
| 新增宿主（Codex / Gemini CLI / Windsurf）| F007/F008 已确立 first-class adapter 注册模式；本 cycle 不动注册表 | F010+ 增量候选 |
| LLM 辅助"自动建议 scope" | 与 manifesto "你做主" 信念冲突 | 不做 |
| 反向同步：用户在 `~/.claude/skills/` 改了之后回流到 `packs/` | F007 已 deferred | 单独候选 |
| D7 管道扩展为递归 `references/` 子目录 | F008 已 deferred 为 D9 候选；与 F009 正交 | 仍是 D9 候选（与 F009 同 stage 但独立 cycle） |

## 6. 功能需求

### FR-901 `--scope` flag

- **优先级**: Must
- **来源**: 用户原始请求 "应该有两种方式，一个是当前项目，一个是用户级别"
- **需求陈述**: 当用户执行 `garage init` 时，系统必须接受可选 `--scope <scope>` flag，其中 `<scope>` ∈ {`project`, `user`}；缺省值为 `project`。该 flag 作用于本次 init 的全局默认 scope，可被 per-host override 覆盖（详见 FR-902）。
- **验收标准**:
  - Given 用户执行 `garage init --hosts claude --scope project`，When 命令运行结束，Then 退出码 0，且 SKILL.md 落到 `<cwd>/.claude/skills/`，行为与 F008 `garage init --hosts claude` 字节级一致（CON-901）
  - Given 用户执行 `garage init --hosts claude --scope user`，When 命令运行结束，Then 退出码 0，且 SKILL.md 落到 `~/.claude/skills/`，**不**创建 `<cwd>/.claude/skills/`
  - Given 用户执行 `garage init --hosts claude`（无 `--scope`），When 命令运行结束，Then 行为完全等价 `--scope project`（默认值生效，CON-901 守门）
  - Given 用户执行 `garage init --scope unknown`（含 `--hosts`），When 命令运行，Then 退出码 1，stderr 含 `Unknown scope: unknown. Supported scopes: project, user`

### FR-902 per-host scope override 语法

- **优先级**: Must
- **来源**: 用户原始请求 "安装时让用户选" 推导出"每个宿主独立选 scope"的复合场景需求
- **需求陈述**: 当用户传入 `--hosts <list>` 时，每个 host token 必须支持 `<host>` 与 `<host>:<scope>` 两种形式；带 scope 后缀的 host 使用该 scope（覆盖 `--scope` 全局默认），不带后缀的 host 使用 `--scope` 全局默认（默认 project）。
- **验收标准**:
  - Given 用户执行 `garage init --hosts claude:user,cursor:project`（无 `--scope`），When 命令运行结束，Then claude SKILL.md 装到 `~/.claude/skills/`，cursor SKILL.md 装到 `<cwd>/.cursor/skills/`；manifest 中两类 entry 的 `scope` 字段分别为 `"user"` 与 `"project"`
  - Given 用户执行 `garage init --hosts claude:user,cursor --scope project`，When 命令运行结束，Then claude 用 user scope（per-host override），cursor 用 project scope（继承 `--scope project` 全局）
  - Given 用户执行 `garage init --hosts claude:bad`，When 命令运行，Then 退出码 1，stderr 含 `Unknown scope: bad in 'claude:bad'. Supported scopes: project, user`
  - Given 用户执行 `garage init --hosts claude:user,claude:project`（同一 host 重复但不同 scope），Then 视为合法（同一 source 装到两个 dst），manifest 含两条 entry；这是显式行为不是 conflict（与 FR-907 跨 pack 冲突区分）

### FR-903 交互式 per-host scope 选择

- **优先级**: Must
- **来源**: 用户原始请求 "安装时让用户选"
- **需求陈述**: 当用户在 TTY 下执行 `garage init` 既不带 `--hosts` 也不带 `--yes` 时，系统必须进入两轮交互：第一轮选宿主（F007 FR-703 行为不变）；第二轮对每个选中宿主独立提示 scope 选择，默认 `P`（project，与 F007/F008 行为一致），用户输入 `u` 切到 user scope。
- **验收标准**:
  - Given 用户在 TTY 下执行 `garage init`，When 第一轮选完宿主（如选了 claude + cursor），Then 第二轮按选定顺序对每个宿主独立提示 `Install <host> skills to: [P]roject (./.{host}/skills/) or [u]ser (~/.{host}/skills/)? [P/u]: `
  - Given 用户在第二轮全部回车（默认），Then 等价于全部 project scope，与 F007/F008 行为一致（CON-901 在交互路径同样守门）
  - Given 用户对 claude 输入 `u`、对 cursor 回车，Then 等价于 `garage init --hosts claude:user,cursor:project`
  - Given non-TTY 场景（CI/Cloud Agent），Then 沿用 F007 FR-703 退化行为（`--hosts none` + stderr 提示），**不**进入第二轮 scope 提示

### FR-904 user scope 路径解析（三家 first-class adapter）

- **优先级**: Must
- **来源**: § 1 调研锚点（三家宿主官方文档）
- **需求陈述**: 系统必须为 claude / opencode / cursor 三家 first-class adapter 各实现 user scope 路径解析，返回 absolute Path（基于 `Path.home()` 推导）。具体路径必须遵循各家官方约定：
  - **Claude Code**: `~/.claude/skills/<skill_id>/SKILL.md` + `~/.claude/agents/<agent_id>.md`
  - **OpenCode**: `~/.config/opencode/skills/<skill_id>/SKILL.md` + `~/.config/opencode/agent/<agent_id>.md`（XDG 默认；dotfiles 风格 `~/.opencode/skills/...` 留给 deferred）
  - **Cursor**: `~/.cursor/skills/<skill_id>/SKILL.md`（无 agent surface，agent 跳过，与 F007 一致）
- **验收标准**:
  - Given `garage init --hosts claude --scope user` 完成，When 检查 `~/.claude/skills/`，Then 含 N 个 skill 子目录（N == sum(pack.json.skills[])，按 F008 落地后 N=29）
  - Given `garage init --hosts opencode --scope user` 完成，When 检查 `~/.config/opencode/skills/`，Then 含 N 个 skill 子目录；agent 装到 `~/.config/opencode/agent/`
  - Given `garage init --hosts cursor --scope user` 完成，When 检查 `~/.cursor/skills/`，Then 含 N 个 skill 子目录；`~/.cursor/agents/` **不**被创建（cursor 无 agent surface，与 F007 一致）
  - Given 任意 user scope 落盘的 SKILL.md，When 检查文件首部，Then 含 `installed_by: garage` + `installed_pack: <pack-id>` marker（与 F007 FR-708 一致，marker 与 scope 无关）

### FR-905 manifest schema migration（1 → 2）

- **优先级**: Must
- **来源**: § 2.1 核心目标 "manifest schema 扩展" + § 2.2 success criteria #5
- **需求陈述**: 系统必须把 `.garage/config/host-installer.json` 的 schema 从 F007 的 `schema_version: 1` 升级到 `schema_version: 2`，并由 `VersionManager` 接管自动 migration（沿用 F007 CON-703 + F001 platform contract 政策）。新 schema 字段：
  - `files[].dst` 改为 absolute path（POSIX serialization；不再相对 workspace_root）
  - 新增 `files[].scope` 字段（`"project"` / `"user"` 字符串）
  - 旧 schema 1 manifest 自动迁移：每条 entry 补 `scope: "project"` + `dst` 由 relative 转 absolute（`workspace_root / dst`）；schema_version 字段从 1 → 2；`installed_at` 不变
  - 新装的 user scope entry 的 `dst` 直接是 absolute path（如 `/home/<user>/.claude/skills/hf-specify/SKILL.md`）
- **验收标准**:
  - Given 用户已在 F008 cycle 跑过 `garage init --hosts claude` 并写过 manifest（schema_version=1），When 升级到 F009 后第一次跑 `garage init --hosts claude`，Then manifest 自动升级到 schema_version=2，旧 entry 全部 `scope: "project"` + dst 转 absolute
  - Given migration 后再读 manifest，Then 任意 Agent 仍能从 `files[].dst` + `files[].scope` 字段直接定位每个文件归属的 scope 与绝对位置
  - Given 用户执行 `garage init --hosts claude:project,cursor:user` 在干净 manifest，When manifest 写入完成，Then `schema_version: 2`，含两类 entry 分别 `scope: "project"` 与 `scope: "user"`，所有 dst 均为 absolute path
  - Given migration 失败（如旧 manifest JSON 损坏），Then 退出码 1，stderr 含 `Manifest migration failed: ...`，旧 manifest 不被覆盖

### FR-906 pipeline scope 分流

- **优先级**: Must
- **来源**: § 2.1 核心目标 "pipeline scope 拼接根分流" + § 2.2 success criteria #11
- **需求陈述**: `pipeline.install_packs` 函数体的 5 个 phase 算法骨架（discover → resolve → conflict → decide → apply + manifest）字节级不变；本 cycle 仅在 phase 2 `_resolve_targets` 内按 target scope 选 base path：project scope 用 `workspace_root`（F007 既有），user scope 用 `Path.home()`。`_Target` dataclass 增 `scope` 字段。其它 phase 算法（特别 phase 3 conflict / phase 4 decide / phase 5 manifest write）算法骨架不动，仅按 5 元组 key 而非 4 元组 key 比对。
- **验收标准**:
  - Given F007 既有 `pipeline.install_packs` 在 F009 实施后再读，When `git diff main..HEAD -- src/garage_os/adapter/installer/pipeline.py` 检查 phase 1 / 3 / 4 / 5 的算法逻辑，Then 仅 phase 2 `_resolve_targets` + 相关 dataclass 有改动；phase 1 (discover) / phase 3 (conflict) / phase 4 (decide) / phase 5 (apply + manifest) 的算法主体字节级保持原状（仅 type signatures 因 _Target 增 scope 字段而扩展）
  - Given 同一次 init 含混合 scope（如 `--hosts claude:project,cursor:user`），When pipeline 运行，Then phase 3 conflict detection 按"同 scope 内同 dst"判定（不同 scope 不视作冲突）；phase 4 decide_action 按"同 scope 内同 src+dst+host"比对 manifest entry
  - Given 同一 SKILL.md 同时装到同 host 不同 scope（如 `--hosts claude:user,claude:project`），Then 不视为 conflict（FR-902 验收 #4 已说明）；manifest 含两条 entry

### FR-907 跨 scope 冲突检测

- **优先级**: Should
- **来源**: F007 FR-704 #4 同名 skill 跨 pack 冲突检测精神延展
- **需求陈述**: 跨 scope 不视作 conflict（FR-906 已说明）。但同一 scope 内（如 user scope claude）若有同名 skill 来自多个 pack，仍按 F007 FR-704 #4 退出码 2 + stderr 列出冲突；该行为不被 scope 维度破坏。
- **验收标准**:
  - Given user scope 内同一 SKILL.md 同名（虚构场景），Then 退出码 2 + stderr 列出冲突 source/dest（与 F007 FR-704 #4 一致）
  - Given 同一 SKILL.md 同时装到 project + user scope，Then 不视为冲突（FR-906 验收 #3 已说明）

### FR-908 `garage status` 按 scope 分组

- **优先级**: Should
- **来源**: § 2.2 success criteria #9
- **需求陈述**: 当用户执行 `garage status` 且 manifest 存在时，系统必须按 scope 分组展示 packs 安装状态：先 project scope 段（按 host 子分组 + 类型 + 计数 + dst 前缀），再 user scope 段（同结构）；若某 scope 无内容则跳过该段。stdout 格式必须可冷读且按行可 grep。
- **验收标准**:
  - Given manifest 含 project + user 两类 entry，When 跑 `garage status`，Then stdout 含 "Installed packs (project scope):" + "Installed packs (user scope):" 两段，每段按 host 分组列出 N skills + M agents + 含 dst 前缀（如 `<cwd>/.claude/skills/`）
  - Given manifest 仅 project scope，Then 仅显示 project 段，不显示空 user 段
  - Given manifest 不存在（用户没跑过 init），Then `garage status` 输出与 F008 一致（不破坏 F008 既有 status 行为）

### FR-909 stdout marker 派生

- **优先级**: Should
- **来源**: § 2.2 success criteria + F007 FR-709 stdout marker 稳定性
- **需求陈述**: F007 既有 `Installed N skills, M agents into hosts: <list>` 格式不变；当本次 init 含混合 scope 时，stdout 必须附加一行 `(N_user user-scope skills + N_project project-scope skills)` 形式说明（具体格式由 design 决定，但必须可冷读 + 可 grep）。
- **验收标准**:
  - Given 单 scope init（如 `--hosts claude --scope user`），Then stdout 仍 `Installed N skills, M agents into hosts: claude`，不附加 scope 段（与 F007 字节级一致，CON-901）
  - Given 混合 scope init（如 `--hosts claude:user,cursor:project`），Then stdout 含 F007 marker + 一行 scope 分布说明（如 `(N_user user-scope, N_project project-scope)`）

### FR-910 文档与可发现性

- **优先级**: Must
- **来源**: F007 FR-710 + F008 FR-807 5 分钟冷读链
- **需求陈述**: 系统必须随本 cycle 提供以下用户可见文档同步：
  - `packs/README.md` 增 "Install Scope" 段，说明 project / user 二选 + per-host override 语法 + 何时选哪个
  - `docs/guides/garage-os-user-guide.md` "Pack & Host Installer" 段加 `--scope` 用法 + 交互式 per-host 选择示例 + user scope 端到端样板
  - `AGENTS.md` § "Packs & Host Installer (F007/F008)" 升级到 F007/F008/F009 + 新增 "Install Scope" 子段（说明 dogfood 仍 project，user scope 是新增可选）
  - `RELEASE_NOTES.md` 新增 F009 段（按 F008 同等详尽度）
- **验收标准**:
  - Given F009 PR 合并，When `grep -E 'Install Scope' packs/README.md`，Then 命中
  - Given 任意新 Agent / 新用户从 `AGENTS.md` 出发，When 顺序读 `AGENTS.md` → `packs/README.md` → `docs/guides/garage-os-user-guide.md`，Then 必须能在 5 分钟内回答 (a) project / user scope 区别、(b) 怎么选、(c) per-host override 怎么写 三个问题
  - Given `RELEASE_NOTES.md`，When grep `## F009`，Then 必须出现，且段落结构与 F008 段一致（用户可见变化 / 数据与契约影响 / 验证证据 / 已知限制 4 段）

## 7. 非功能需求

### NFR-901 F007/F008 既有调用形态字节级不变（CON-901 守门）

- **优先级**: Must
- **来源**: § 2.2 success criteria #1 + F002 CON-702 精神
- **需求陈述**: F007/F008 既有调用形态（包括 `garage init`、`garage init --hosts <list>`、`garage init --hosts all`、`garage init --hosts none`、`garage init --yes`、`garage init --hosts claude --force`）的 stdout / stderr / 退出码 / `.garage/` 目录创建 / `<cwd>/.{host}/skills/` 落盘行为必须与 F008 closeout 时（commit `bafbd1c` 父链）字节级一致。新增 `--scope project` 行为必须等价于不带 `--scope`（默认值生效）。
- **验收标准**:
  - Given 一份 F008 cycle 期间录制的 `garage init --hosts claude` 端到端 stdout/stderr 副本，When F009 实施后再跑同样命令，Then 字节级一致（除 stdout 中 `Initialized Garage OS in <path>` 内嵌的可变 path 部分）
  - Given F007/F008 既有 30+ installer 测试，When F009 实施后再跑，Then 100% 通过且 0 改写
  - Given `garage init --hosts claude --scope project`（显式 scope），When 与不带 `--scope` 的同样命令对比，Then stdout / stderr / manifest 写入 / 文件落盘字节级一致

### NFR-902 测试基线零回归

- **优先级**: Must
- **来源**: § 2.2 success criteria #10 + F008 NFR-802 同精神
- **需求陈述**: F009 实施完成后，`uv run pytest tests/ -q` 整体计数必须 ≥ F008 baseline 633，旧用例 0 退绿；新增测试至少覆盖：(a) 三家 adapter user scope path 解析 (b) `--scope` flag 解析 + per-host override 语法 (c) 交互式两轮 scope 选择 (d) manifest schema migration 1→2 (e) 幂等分 scope (f) `garage status` 按 scope 分组 (g) `Path.home()` fixture-isolated 测试隔离（不污染真实用户家目录）。
- **验收标准**:
  - Given F008 baseline 633 passed，When F009 实施完成，Then `uv run pytest tests/ -q` 整体计数 ≥ 633 + 新增；旧用例 0 退绿
  - Given F009 新增 user scope adapter / pipeline scope 分流，When 跑相关测试，Then 至少新增 ≥ 7 个测试模块覆盖上面 (a)-(g) 七类
  - Given user scope 测试，When fixture 隔离，Then 测试**不**污染真实 `~/.claude/skills/` 等用户家目录（用 `tmp_path` + monkeypatch `Path.home()` 隔离）

### NFR-903 跨平台路径稳定性

- **优先级**: Should
- **来源**: F007 NFR-703 同精神 + Windows `Path.home()` 默认 `%USERPROFILE%`
- **需求陈述**: user scope 路径解析必须使用 `pathlib.Path` + `Path.home()` 标准 stdlib API；不允许写死分隔符或自行推导 home。manifest 中 `dst` 字段（absolute path）必须用 POSIX-style 正斜杠 `/` 序列化（与 F007 NFR-703 一致），让 Linux/macOS/Windows 的 git diff 一致。
- **验收标准**:
  - Given 同一 packs 内容物在 Linux 与 macOS 上各自 `garage init --hosts claude --scope user`，When 比较两份 manifest（除 `installed_at` 与 home path 实际值外），Then `files[]` 字段按 `(src, dst-tail-after-home, host, scope, content_hash)` 必须 byte-equal
  - Given 任意 dst 字段，When 解析为 Path 对象，Then 可被 `Path("dst-string")` 反序列化（POSIX path 在 Windows 也合法）

### NFR-904 git diff 可审计 + commit 分组

- **优先级**: Should
- **来源**: F008 NFR-804 同精神
- **需求陈述**: F009 PR 的 git diff 必须按 "新增 adapter user scope" / "扩展 pipeline scope 分流" / "manifest schema 1→2 migration" / "扩展 CLI flag + 交互" / "新增测试" / "文档" 六类分组提交（推荐每组一个或多个 commit），让 reviewer 能逐类审计。
- **验收标准**:
  - Given F009 PR，When `git log --oneline cursor/f009-...`，Then commit 数 ≥ 6 且 commit message 主题前缀清晰对应六类分组（如 `f009(adapter):` / `f009(pipeline):` / `f009(manifest):` / `f009(cli):` / `f009(tests):` / `f009(docs):`）
  - 注：实际允许 1 个或多个 commit/group，本 NFR 不强求数量，强求**可审计性**

## 8. 外部接口与依赖

- **依赖**: 仅依赖项目既有 `pyproject.toml` 中已有依赖。本 cycle **零依赖变更**（`uv.lock` 不变）。如 design 阶段确认必须引入额外依赖，须回到 spec 增补 `IFR-9xx` 显式记录原因。
- **外部接口**: 无新增。F007 落下的 host adapter Protocol 仅扩展 optional method（`target_skill_path_user` / `target_agent_path_user`），既有 method 签名不变。
- **AGENTS.md 路径映射**: 本 cycle 涉及 `AGENTS.md § "Packs & Host Installer (F007/F008)"` 段升级为 F007/F008/F009 + 新增 "Install Scope" 子段（FR-910 验收）

## 9. 约束与兼容性要求

### CON-901 不破坏 F002/F007/F008 既有 `garage init` 行为

- **优先级**: Must
- **来源**: § 4.2 关键边界 + F002 CON-702 + § 4.3 与既有契约的边界表
- **需求陈述**: 调用方式 `garage init`（无任何新参数）+ `garage init --hosts <list>`（不带 `--scope`）+ `garage init --hosts all --yes` 等 F007/F008 既有形态的可观察输出必须与 F008 closeout 状态完全一致。新增 `--scope project` 显式 scope 必须等价于不带 `--scope`。
- **详细说明**: 这是 F002 CON-702 + F008 CON-801 同精神的延续：新增能力是可选叠加，缺省调用形态字节级不变。

### CON-902 D7 安装管道核心算法不动

- **优先级**: Must
- **来源**: § 2.2 success criteria #11 + § 4.2 关键边界
- **需求陈述**: `pipeline.install_packs` 函数体的 5 个 phase 算法骨架（discover → resolve → conflict → decide → apply + manifest）字节级保持原状；本 cycle 仅在 phase 2 `_resolve_targets` 内增加 scope 维度的 base path 分流（按 target scope 选 `workspace_root` 或 `Path.home()`），其它 phase 算法主体不变（仅 type signatures 因 `_Target` 增 `scope` 字段而扩展）。`pipeline.install_packs` 的函数签名可以扩展（增 optional 参数），但既有调用方（如 cli.py）不传新参数时行为字节级不变。
- **详细说明**: 这是把"scope 扩展"局部化在 adapter + pipeline phase 2 的硬约束，防止 review surface 失控。

### CON-903 复用 F007 `pack.json` schema + F008 ADR-D8-9 EXEMPTION_LIST

- **优先级**: Must
- **来源**: F007 FR-701 + F008 ADR-D8-9
- **需求陈述**: 三个 pack 的 `pack.json` 必须沿用 F007 落下的 6 字段 schema 不变；F008 ADR-D8-9 的 7 项 EXEMPTION_LIST 不增不减不改。本 cycle 不动 packs/ 内容物。
- **详细说明**: F009 是 CLI + adapter + pipeline + manifest 扩展，与 packs/ 内容物正交。

### CON-904 manifest schema 1 → 2 migration 单向

- **优先级**: Must
- **来源**: F007 CON-703 + F001 VersionManager schema migration 政策
- **需求陈述**: `.garage/config/host-installer.json` schema 升级单向（1 → 2，无 2 → 1 反向），由 `VersionManager` 接管自动 migration；旧 schema 字段含义在新 schema 下仍可冷读；migration 失败时退出码 1 + 旧 manifest 不被覆盖。
- **详细说明**: 与 F007 CON-703 + F001 platform contract 一致。

## 10. 假设

### ASM-901 三家宿主在 F009 实施期间仍承认上述 user scope path 不变

- **优先级**: Should
- **来源**: § 1 调研锚点（2026 Q2 三家官方文档实测）
- **需求陈述**: 假设 Claude Code / OpenCode / Cursor 在 F009 cycle 实施期间各自 user scope path 约定（`~/.claude/skills/` / `~/.config/opencode/skills/` / `~/.cursor/skills/`）不发生 breaking change。
- **失效风险**: 若某家在 implementation 时段静默改名 / 弃用，会导致对应 user scope 装出去的文件不被识别。
- **缓解措施**: design 阶段为每个 adapter 显式记录 path 来源（链接到该工具公开文档），并在 implementation 后跑一次三家宿主的 user scope smoke 验证（与 F008 dogfood 一致）

### ASM-902 用户能区分 project scope 与 user scope 的语义

- **优先级**: Should
- **来源**: § 3 用户角色
- **需求陈述**: 假设 solo creator 用户能理解 "project scope = 装到当前项目，user scope = 装到家目录跨项目复用" 的区别，且能通过 `--scope` flag 或交互式提示做出选择。
- **失效风险**: 用户误以为 user scope = 装到 `~/.garage/`（其实是 `~/.claude/skills/` 等宿主原生 user 路径）。
- **缓解措施**: 文档（FR-910）+ stdout marker（FR-909）+ 交互式提示（FR-903）三处都显式说明 dst 前缀；packs/README.md "Install Scope" 段必须有"何时选哪个"决策树

### ASM-903 `Path.home()` 在所有目标平台返回正确的用户家目录

- **优先级**: Should
- **来源**: § 4.2 关键边界 + Python stdlib pathlib
- **需求陈述**: 假设 `Path.home()` 在 Linux / macOS / Windows 默认行为下分别解析到 `$HOME` / `$HOME` / `%USERPROFILE%`，且不需要额外 fallback。
- **失效风险**: 用户 shell 环境异常（如 `$HOME` 未设置）会导致 user scope 安装到错误位置。
- **缓解措施**: pipeline 在 user scope 路径解析时若 `Path.home()` 抛 `RuntimeError`（stdlib 已记录的少数失败模式），退出码 1 + stderr 含 `Cannot determine user home directory: ...`

### ASM-904 manifest migration 在 F008 用户群体中是无感操作

- **优先级**: Should
- **来源**: F008 用户已落下的 schema 1 manifest（cycle 期间预期数量较小）
- **需求陈述**: 假设 F008 用户群体当前在自己项目的 `.garage/config/host-installer.json` 已落下 schema 1 manifest，F009 升级后第一次 `garage init` 自动迁移到 schema 2，无需用户操作；旧 entry 默认补 `scope: "project"` 是用户期望（因为 F008 行为本就是 project scope）
- **失效风险**: 极少数用户可能在 F008 manifest 之外自己 hack 过该文件，migration 可能识别失败
- **缓解措施**: migration 失败时不覆盖旧 manifest，stderr 显式打印失败原因 + 用户可手动备份 + 重新跑 init（与 F007 CON-703 + VersionManager schema migration 失败处理一致）

## 11. 开放问题

### 阻塞性（必须在 hf-spec-review 通过前关闭）

当前**无阻塞性开放问题**。若 spec reviewer 发现以下任一项摇摆，应反馈以阻塞 finding 形式提出：

- 默认 scope 是 `project`（兼容 F007/F008）还是 `user`（强推跨项目复用） — spec 默认选 project（CON-901 守门，与最小破坏性原则一致）
- per-host override 语法是 `<host>:<scope>`（spec 默认）还是 `<host>@<scope>` 或 `<scope>:<host>` — spec 默认选 `<host>:<scope>`（与 OpenSpec 调研常见模式一致）
- OpenCode 默认 user scope path 是 XDG `~/.config/opencode/`（spec 默认）还是 dotfiles 风格 `~/.opencode/` — spec 默认选 XDG（官方 PR #6174 文档同时支持但 XDG 是 OpenCode 历史默认）

### 非阻塞性（可在 design 阶段细化）

1. **manifest schema 2 字段命名**：`files[].scope` 字段值用 `"project"` / `"user"`（spec 默认）还是 `"workspace"` / `"global"`（与某些宿主官方术语一致）— design 决定
2. **`Path.home()` 抛 `RuntimeError` 的退出码**：spec 默认 1（与 unknown host 同级），design 决定是否需要专用退出码（如 3）
3. **stdout 多 scope 段的具体格式**：FR-909 留 wording，design 决定确切格式（如 `(N_user user-scope skills + N_project project-scope skills)` 或表格形式或 JSON）
4. **manifest absolute path 是否带 `~/` 前缀**：spec 默认走 `Path.home() / ...` 后展开为绝对路径（如 `/home/<user>/.claude/skills/...`），design 决定是否在 manifest serialization 时把 home 部分还原为 `~/...`（更紧凑但跨用户不可移植）
5. **交互式两轮 vs 一轮带 scope 后缀**：FR-903 默认两轮（先选宿主再每个宿主选 scope），design 决定是否合并为一轮（如 "选宿主时直接输入 `claude:user, cursor`"）
6. **`HostInstallAdapter` Protocol 新增 method 命名**：spec 默认 `target_skill_path_user` / `target_agent_path_user`（与既有 method 同名加 `_user` 后缀），design 决定是否改为 `target_skill_path(scope=...)` 单 method 带参数（更对称但破坏 F007 既有签名兼容性）
7. **`garage status` 按 scope 分组的输出格式**：FR-908 留 wording，design 决定 ASCII table / nested bullets / 其它

## 12. 术语与定义

| 术语 | 定义 |
|------|------|
| **Scope**（本 cycle 引入） | `garage init` 装到的目标位置维度：`project`（执行 cwd 项目根） / `user`（用户家目录） |
| **Project scope** | F007/F008 既有行为：装到 `<cwd>/.{host}/skills/`（如 `<cwd>/.claude/skills/`） |
| **User scope**（本 cycle 引入） | 装到用户家目录下的宿主原生约定路径（如 `~/.claude/skills/`），跨项目复用 |
| **per-host scope override**（本 cycle 引入） | `--hosts <host>:<scope>,<host>:<scope>,...` 语法，每个 host 独立指定 scope，覆盖 `--scope` 全局默认 |
| **manifest schema 2**（本 cycle 引入） | `.garage/config/host-installer.json` 在 F009 后的 schema：`schema_version: 2` + `files[].dst` absolute + `files[].scope` 字段；schema 1 自动 migration |
| **Pack**（沿用 F007） | 一组以共同主题打包的 Garage skills + agents |
| **Host**（沿用 F007） | 一个能加载 SKILL.md 的 AI 工具，本 cycle first-class 集合仍为 `claude` / `opencode` / `cursor`（不变）|
| **Host Adapter**（沿用 F007 + F009 扩展）| 把 Garage 中立 pack 内容映射到具体宿主目录约定的代码组件；本 cycle 扩展为支持 user scope path 解析（新增 `target_skill_path_user` / `target_agent_path_user` optional method）|
| **dogfood**（沿用 F008 ADR-D8-2 候选 C）| 本仓库自身贡献者首次 clone 后跑 `garage init --hosts cursor,claude` 把 packs/ 物化到本仓库的 `.cursor/skills/` + `.claude/skills/` 作为 IDE 加载入口；F009 后 dogfood 仍默认 project scope 不变 |
