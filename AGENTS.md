# Garage — Agent 指引

## 仓库定位

这个仓库的根目录现在按 `Garage` 的逻辑根目录使用。

当前阶段，仓库同时承接：

- `Garage` 的设计文档链
- `Garage` phase 1 的开发任务链
- `Garage` phase 1 的 pack surface 与 file-backed runtime surfaces

当前仓库中的历史 AHE 来源资产，已经主要收口到下面这些真实路径：

- `packs/coding/skills/`
- `packs/product-insights/skills/`
- `.agents/skills/`

它们在 phase 1 中的定位仍然是来源资产、参考 workflow、模板与 skill 工具链，而不是完整的 `Garage Core`。

## 工作方式

1. **先看当前入口**：默认从 `README.md`、`AGENTS.md`、`docs/README.md`、`docs/GARAGE.md`、`docs/tasks/README.md` 或用户明确指定的文件开始，而不是假设存在历史入口。
2. **以实际目录为准**：只引用当前仓库中真实存在的路径。`docs/architecture/`、`docs/design/`、`docs/features/` 负责设计主线，`docs/tasks/` 负责开发拆解，`docs/wiki/` 负责参考知识与 supporting material，`packs/` 负责当前 pack surface，root-level `artifacts/`、`evidence/`、`sessions/`、`archives/`、`.garage/` 负责 file-backed surfaces。
3. **从对应入口继续深入**：查看 `Garage` 设计时从 `docs/README.md` 和 `docs/GARAGE.md` 开始；查看 phase 1 任务时从 `docs/tasks/` 开始；查看当前 pack surface 时从 `packs/` 开始；查看来源技能和工具链时从 `packs/coding/skills/`、`packs/product-insights/skills/`、`.agents/skills/` 的真实入口继续。
4. **控制改动范围**：只修改当前任务涉及的目录与文档，不为了“统一整理”去批量改写无关分析资料，也不要在 phase 1 早期做大规模目录迁移。
5. **保持边界稳定**：platform-neutral 语义优先留在 `docs/architecture/` 与 `docs/features/`；pack-specific 语义留在 `packs/`；来源技能与工具链继续留在 `packs/*/skills/` 与 `.agents/skills/`。
6. **主线相关改动先做一致性检查**：当任务涉及 `docs/`、`packs/`、`.garage/`、`artifacts/`、`evidence/`、`sessions/`、`archives/` 或 `.agents/skills/` 的编辑时，默认先读取并使用 `.agents/skills/vision-obey/SKILL.md`，先检查变更是否违背 `Garage` 的愿景、架构边界、runtime surfaces、governance 与 growth 主线；如果提案只有在回写 `docs/architecture/`、`docs/features/` 或 `docs/design/` 后才成立，应先明确这一点，再继续实施。纯措辞级、且不改变系统语义的编辑可跳过。 

## 路径速查

| 路径 | 用途 |
| --- | --- |
| `README.md` | `Garage` 根目录总览与使用入口 |
| `AGENTS.md` | 仓库级 agent 工作约定 |
| `docs/` | `Garage` 主文档树 |
| `docs/GARAGE.md` | `Garage` 品牌定位、愿景与主线阅读入口 |
| `docs/architecture/` | 平台中立架构与核心边界 |
| `docs/design/` | 子系统与 pack-specific 详细设计 |
| `docs/features/` | phase 1 contracts、bridge、artifact、runtime 等能力切面 |
| `docs/tasks/` | `Garage` phase 1 开发任务链 |
| `docs/wiki/` | 外部分析、采用方式、路径映射与 supporting references |
| `packs/` | `Garage` phase 1 的当前 pack surface |
| `artifacts/` | 当前主工件面 |
| `evidence/` | 当前证据面 |
| `sessions/` | 当前会话协调面 |
| `archives/` | 统一历史归档面 |
| `.garage/` | 索引、sidecars 与机器辅助面 |
| `packs/coding/skills/` | coding workflow 来源资产入口 |
| `packs/product-insights/skills/` | 产品洞察 workflow 来源资产入口 |
| `.agents/skills/` | 通用 agent skills 与 skill 工具链 |

## Cursor / 技能说明

本仓库当前仍以 Markdown 资产和少量 Python 辅助脚本为主，没有业务应用构建链路。

### 运行时依赖

- `Python 3.12+`
- `PyYAML`（按需安装）

### 当前本地 skills

旧的本地 skill 脚本目录已移除。

当前仓库内仍保留这些本地 skills 入口：

| 路径 | 用途 |
| --- | --- |
| `.agents/skills/find-skills/SKILL.md` | 查找或发现可用 skill |
| `.agents/skills/writing-docs/SKILL.md` | 维护 `docs/` 下的 Garage 系统文档 |
| `.agents/skills/writing-skills/SKILL.md` | 创建、编辑和验证 skill 文档 |
| `.agents/skills/vision-obey/SKILL.md` | 对照 `docs/` 主线做一致性检查 |
| `.agents/skills/architecture-designer/SKILL.md` | 辅助架构设计工作 |

### 注意事项

- `references/` 类型目录若存在，默认视为参考资料，不强行安装或运行其依赖。
- 本仓库当前没有内置的统一 skill 脚本工具链。
- 本仓库当前没有统一 lint、CI 或自动化测试套件；核心验证方式仍是路径检查和现有 Python 测试。
