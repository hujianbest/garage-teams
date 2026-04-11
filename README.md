# Garage

`Garage` 是一个面向 `solo creator` 的 `Creator OS`。当前仓库根目录按 `Garage` 的逻辑根目录使用，既承接主线设计文档，也承接当前 reference pack surface、`src/` runtime implementation surface 和 file-backed runtime surfaces。

## 当前定位

当前阶段，这个仓库同时承接：

- `Garage` 的主线文档链
- `Garage` 的当前 implementation task 链
- `Garage` 的当前 reference pack surface、runtime package 与 workspace facts

当前仍坚持：

- `Markdown-first`
- `file-backed`
- `Contract-first`
- 先用 `Product Insights Pack` 与 `Coding Pack` 两个 reference packs 验证平台边界

## 先看哪里

1. 先读 `README.md` 和 `AGENTS.md`
2. 再读 `docs/README.md`，理解当前文档信息架构
3. 再读 `docs/VISION.md`，理解 `Garage` 为什么存在
4. 再读 `docs/GARAGE.md`，理解项目定位、愿景与主线阅读顺序
5. 再读 `docs/ROADMAP.md`，理解 `docs/features/` 的编号规则和当前 feature map
6. 需要理解当前 implementation slices 的开发顺序时，读 `docs/tasks/README.md`
7. 需要理解当前 pack surface 时，读 `packs/README.md`
8. 需要看 coding 来源资产时，读 `packs/coding/skills/README.md`
9. 需要看 product insights 来源资产时，读 `packs/product-insights/skills/README.md`
10. 需要维护通用 agent skills 或运行 skill 工具链时，进入 `.agents/skills/`

## 仓库结构

| 路径 | 作用 |
| --- | --- |
| `README.md` | 仓库级总览与入口 |
| `AGENTS.md` | 仓库级 agent 工作约定 |
| `pyproject.toml` | 当前 Python package、测试与 `src` layout 入口 |
| `src/` | `Garage` runtime 的当前实现面 |
| `docs/` | `Garage` 主文档树 |
| `packs/` | 当前 reference packs 的 pack surface |
| `artifacts/` | 当前主工件面 |
| `evidence/` | 当前证据面 |
| `sessions/` | 当前会话协调面 |
| `archives/` | 当前历史归档面 |
| `.garage/` | 机器辅助面、索引与 sidecars |
| `tests/` | runtime package 的当前最小验证面 |
| `.agents/skills/` | 通用 agent skills 与 skill 工具链 |

## Docs 信息架构

`docs/` 当前按职责分层：

| 路径 | 作用 |
| --- | --- |
| `docs/GARAGE.md` | `Garage` 的品牌定位、愿景与主线阅读入口 |
| `docs/architecture/` | 平台中立架构、核心边界与 continuity 架构 |
| `docs/design/` | 子系统与 pack-specific 详细设计 |
| `docs/features/` | contracts、governance、artifact surface、bridge、runtime 等稳定能力切面 |
| `docs/tasks/` | 当前 implementation task 链 |
| `docs/wiki/` | 外部项目分析、历史参考、采用方式与路径映射资料 |

## 当前 source surfaces

当前仓库里最接近 live runtime source 的入口是：

- `src/`
- `tests/`
- `pyproject.toml`

当前仍然承接重要来源资产与参考实现的入口是：

- `packs/coding/skills/`
- `packs/product-insights/skills/`
- `.agents/skills/`

它们在当前主线的定位是：

- `Garage` 的来源资产
- 两个 reference packs 的当前技能面
- 模板、规则与 skill 工具链的维护入口

因此当前仓库里已经有两类不同表面：

- `src/` 是 `Garage` runtime 的当前实现面。
- `packs/*/skills/` 与 `.agents/skills/` 是来源资产、参考 workflow 和 skill 工具链。

## 关键文档

- `docs/README.md`：当前文档树入口与维护约定
- `docs/VISION.md`：`Garage` 的愿景、产品哲学与 why
- `docs/GARAGE.md`：项目定位、愿景与主线设计入口
- `docs/ROADMAP.md`：`docs/features/` 的稳定 feature IDs 与路线图入口
- `docs/tasks/README.md`：当前 implementation task 链入口
- `packs/README.md`：当前 pack surface 入口
- `pyproject.toml`：当前 runtime package 与测试入口
- `docs/wiki/W140-ahe-platform-first-multi-agent-architecture.md`：平台优先的历史/背景架构文档
- `docs/design/D020-ahe-workflow-skill-anatomy.md`：AHE workflow skill 的 anatomy 基线
- `docs/wiki/W120-ahe-workflow-externalization-guide.md`：外部仓库采用 workflow family 的最小能力面
- `docs/wiki/W130-ahe-path-mapping-guide.md`：逻辑工件到实际路径的映射方式

## 当前约束

- 只引用当前仓库真实存在的路径
- 当前仓库根目录同时扮演 source root 与默认 dogfooding workspace
- 当前还没有业务应用构建流程、数据库或统一 CI 流水线
- 绝大多数资产仍是 Markdown 文档；变更时优先保持路径清晰、引用准确、内容可复用
- 当前 runtime 骨架以标准库 + `src` layout + `unittest` 为主，不把 core / contracts 塞回 `packs/` 或 `.agents/`

## 可用验证

如果需要维护仓库内或本地挂载的 Cursor skill，可在 `.agents/skills/skill-creator/` 下运行这些脚本：

- `python -m scripts.quick_validate <skill-dir>`
- `python -m scripts.package_skill <skill-dir> [output-dir]`
- `python -m scripts.aggregate_benchmark <benchmark-dir>`
- `python -m scripts.generate_report <json-input> [-o output.html]`
- `python -m scripts.run_eval ...`
- `python -m scripts.run_loop ...`

这些脚本通常需要 `Python 3.12+`；部分评测命令额外依赖 `claude` CLI，在当前环境下不可用属于预期限制。

当前 `Garage` runtime package 的最小验证也可以直接运行：

- `python -m unittest discover -s tests`
