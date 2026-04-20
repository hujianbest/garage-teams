# `packs/` — Garage 自带 Pack 集合

`packs/` 是 Garage 仓库内置的 **skills + agents 源**目录，对应 spec `F007 §11.3` 的目录契约。

## 关系

```
源（宿主无关）：     packs/<pack-id>/skills/<skill-name>/SKILL.md
                    packs/<pack-id>/agents/<agent-name>.md
                    packs/<pack-id>/pack.json
                    packs/<pack-id>/README.md

动作：              garage init --hosts claude,cursor,opencode
                    在执行 cwd 把 packs/ 内容物化到下列宿主目录
                    └── .claude/skills/...   .opencode/skills/...   .cursor/skills/...
                    └── .garage/config/host-installer.json   ← 安装清单
```

## 目录约定

每个 pack 是一个一级子目录：

```
packs/<pack-id>/
├── pack.json           # 元描述（schema_version=1）
├── README.md           # 人类可读概述
├── skills/             # 0..N 个 skill 子目录
│   └── <skill-id>/
│       └── SKILL.md    # 必须遵循 docs/principles/skill-anatomy.md
└── agents/             # 0..N 个 agent 文件
    └── <agent-id>.md
```

`pack.json` 字段：

| 字段 | 必需 | 说明 |
|---|---|---|
| `schema_version` | ✅ | 固定 `1` |
| `pack_id` | ✅ | 必须等于目录名 |
| `version` | ✅ | pack 自身版本（语义版本字符串） |
| `description` | ✅ | 人类可读说明 |
| `skills[]` | ✅ | 本 pack 包含的 skill id 清单（与 `skills/<skill-id>/SKILL.md` 一一对应；`pack_discovery` 启动时校验） |
| `agents[]` | ✅ | 本 pack 包含的 agent id 清单（与 `agents/<agent-id>.md` 一一对应；可为空数组） |

## 当前 packs

| Pack | 用途 | 状态 |
|---|---|---|
| `packs/garage/` | 占位 pack，含 1 sample skill + 1 sample agent | ✅ 已落盘（F007 cycle T1） |

未来计划（F008+）：

- `packs/coding/` — HF workflow skills 搬迁目标（30 个 hf-* / using-hf-workflow 等）
- `packs/product-insights/` — product discovery 系列 skill 搬迁目标

## 与 `.agents/skills/` 的关系

| 目录 | 角色 | 给谁用 |
|---|---|---|
| `.agents/skills/<name>/SKILL.md` | **本仓库内部**自身使用的 AHE workflow skills | 当前 Garage 仓库自身的 cursor / claude code 会话 |
| `packs/<pack-id>/skills/<name>/SKILL.md` | **可分发**的 Garage-bundled 能力 | 任何下游用户项目，通过 `garage init --hosts ...` 安装 |

短期内两者并存；F008 候选会把 `.agents/skills/` 下 30 个 HF skills 搬到 `packs/coding/skills/`，由本 cycle 提供的安装管道负责分发。

## Dogfood 与下游用法

**在 Garage 仓库自身 dogfood**：

```bash
# 在 Garage 仓库根目录执行
garage init --hosts claude
# → 会在 .claude/skills/ 下出现 packs/garage/skills/* 的副本
```

**在下游用户项目使用**：

```bash
# 用户在自己项目的根目录执行
cd ~/projects/my-app
garage init --hosts claude,cursor
# → 会在 my-app/.claude/skills/ 与 my-app/.cursor/skills/ 下出现 packs/garage/skills/* 的副本
# → 同时写入 my-app/.garage/config/host-installer.json 安装清单
```

详见 `docs/guides/garage-os-user-guide.md` 的 "Pack & Host Installer" 段。

## 不变量

- `packs/` 目录及其内容物**不得**包含任何宿主特定术语（`.claude/` / `.cursor/` / `.opencode/` / `claude-code` 等），由 NFR-701 自动测试守护。
- 同名 skill 在多个 pack 中共存会导致 `garage init` 退出码 2 + stderr 列出冲突 source/dest（FR-704 验收 #4）。
- 缺失 `packs/` 目录或 packs 为空时，`garage init` 仍正常退出 0、不创建任何宿主目录、stdout 提示 `No packs found under packs/`。
