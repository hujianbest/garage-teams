# Garage — Agent 指引

## 仓库定位

这个仓库的根目录现在按 `Garage` 的逻辑根目录使用。

当前阶段，仓库同时承接：

- `Garage` 的设计文档链
- `Garage` phase 1 的开发任务链
- `Garage` phase 1 的实现骨架与 file-backed runtime surfaces

仓库里仍保留大量 `ahe-*` 资产，但它们在 phase 1 的定位是：

- `Garage` 的来源资产
- `Product Insights Pack` 与 `Coding Pack` 的转译来源
- 参考 workflow、模板与规则资产

它们不是当前 `Garage` runtime 的根目录本体。

## 工作方式

1. **先看当前入口**：默认从 `README.md`、`AGENTS.md`、`docs/garage/README.md`、`docs/tasks/README.md` 或用户明确指定的文件开始，而不是假设存在历史入口。
2. **以实际目录为准**：只引用当前仓库中真实存在的路径。`docs/garage/` 负责设计，`docs/tasks/` 负责开发拆解，`garage/` 负责实现骨架，root-level `artifacts/`、`evidence/`、`sessions/`、`archives/`、`.garage/` 负责 file-backed surfaces。
3. **从对应入口继续深入**：查看 `Garage` 设计时从 `docs/garage/` 开始；查看 phase 1 任务时从 `docs/tasks/` 开始；查看实现骨架时从 `garage/` 开始；查看现有来源资产时从 `ahe-coding-skills/`、`ahe-product-skills/`、`ahe-refer-skills/` 的真实入口继续。
4. **控制改动范围**：只修改当前任务涉及的目录与文档，不为了“统一整理”去批量改写无关分析资料，也不要在 phase 1 早期做大规模目录迁移。
5. **保持边界稳定**：platform-neutral 语义留在 `garage/core/` 与 `garage/contracts/`；pack-specific 语义留在 `garage/packs/`；来源资产继续留在 `ahe-*` 目录。

## 路径速查

| 路径 | 用途 |
| --- | --- |
| `README.md` | `Garage` 根目录总览与使用入口 |
| `AGENTS.md` | 仓库级 agent 工作约定 |
| `docs/` | 分析、设计说明、任务拆解与研究记录 |
| `docs/garage/` | `Garage` 设计文档链 |
| `docs/tasks/` | `Garage` phase 1 开发任务链 |
| `garage/` | `Garage` phase 1 的实现骨架根目录 |
| `artifacts/` | 当前主工件面 |
| `evidence/` | 当前证据面 |
| `sessions/` | 当前会话协调面 |
| `archives/` | 统一历史归档面 |
| `.garage/` | 索引、sidecars 与机器辅助面 |
| `ahe-coding-skills/` | coding workflow 来源资产 |
| `ahe-product-skills/` | 产品洞察 workflow 来源资产 |
| `ahe-refer-skills/` | refer / skill authoring 相关来源资产 |
| `templates/` | 通用 Markdown 模板 |
| `agents/` | 角色化 agent 说明与可复用合同 |
| `rules/` | 常驻规则占位目录 |
| `hooks/` | hooks 说明或辅助脚本占位目录 |
| `ahe-refer-skills/skill-creator/` | skill 校验、打包、评测辅助脚本 |

## Cursor / 脚本说明

本仓库当前仍以 Markdown 资产和少量 Python 辅助脚本为主，没有业务应用构建链路。

### 运行时依赖

- `Python 3.12+`
- `PyYAML`（按需安装）

### 常用脚本

以下脚本都应在 `ahe-refer-skills/skill-creator/` 下执行：

| 命令 | 用途 |
| --- | --- |
| `python -m scripts.quick_validate <skill-dir>` | 校验 `SKILL.md` frontmatter |
| `python -m scripts.package_skill <skill-dir> [output-dir]` | 打包 skill |
| `python -m scripts.aggregate_benchmark <benchmark-dir>` | 汇总 benchmark |
| `python -m scripts.generate_report <json-input> [-o output.html]` | 生成 HTML 报告 |
| `python -m scripts.run_eval ...` | 触发评测，依赖 `claude` CLI |
| `python -m scripts.run_loop ...` | 评测改进循环，依赖 `claude` CLI |

### 注意事项

- `references/` 类型目录若存在，默认视为参考资料，不强行安装或运行其依赖。
- 本仓库当前没有统一 lint、CI 或自动化测试套件；核心验证方式仍是路径检查和上述 skill 脚本。
