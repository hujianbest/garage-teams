# Garage

`Garage` 是一个面向 `solo creator` 的 `Creator OS`。从当前阶段开始，这个仓库的根目录就视为 `Garage` 的根目录，而不再只是一个以 `AHE` 命名的资料工作台。

当前仓库里仍保留大量 `ahe-*` 资产，但它们在 phase 1 的定位已经变成：

- `Garage` 的来源资产
- `Product Insights Pack` 与 `Coding Pack` 的转译来源
- 参考工作流、模板与规则资产

它们**不是**当前 `Garage` runtime 的根目录本体。

仓库物理目录名暂未切换，不影响这里作为 `Garage` 根目录的逻辑定位。

## 当前定位

当前仓库根目录同时承接 3 类内容：

- `Garage` 的设计文档链
- `Garage` phase 1 的开发任务链
- `Garage` phase 1 的实现骨架与 file-backed surfaces

当前阶段仍然坚持：

- `Markdown-first`
- `file-backed`
- `Contract-first`
- 先做 `Product Insights Pack` 与 `Coding Pack` 两个 reference packs

## 先看哪里

1. 初次进入仓库时，先读 `README.md` 和 `AGENTS.md`。
2. 需要理解 `Garage` 的愿景、定位与架构设计时，先读 `docs/garage/README.md`。
3. 需要理解 phase 1 的开发顺序与任务拆解时，读 `docs/tasks/README.md`。
4. 需要理解当前已经落下来的实现骨架与目录边界时，读 `garage/README.md`。
5. 如果当前关注的是上游产品洞察来源资产，先读 `ahe-product-skills/README.md`，再进入 `ahe-product-skills/using-ahe-product-workflow/SKILL.md`。
6. 如果当前关注的是 coding workflow 来源资产，先读 `ahe-coding-skills/README.md`，再读 `ahe-coding-skills/docs/ahe-workflow-entrypoints.md`。
7. 需要维护 skill、模板或 workflow 规则时，再进入对应 `ahe-*` 目录。
8. 需要做 skill 校验、打包或评测时，以 `ahe-refer-skills/skill-creator/` 为工作目录执行脚本。

## 根目录规则

- 仓库根目录就是 `Garage` 根目录。
- `garage/` 是 phase 1 的实现骨架子树，不是另一个独立项目。
- `artifacts/`、`evidence/`、`sessions/`、`archives/`、`.garage/` 是 root-level file-backed runtime surfaces。
- `docs/garage/` 负责设计，`docs/tasks/` 负责开发拆解，`garage/` 负责实现骨架。
- `ahe-coding-skills/` 与 `ahe-product-skills/` 当前仍是来源资产目录，不直接等同于 `Garage` runtime。
- phase 1 不在这一阶段做大规模目录迁移或整体重命名。

## 仓库结构

| 路径 | 作用 |
| --- | --- |
| `README.md` | `Garage` 根目录总览与使用入口 |
| `AGENTS.md` | 仓库级 agent 工作约定 |
| `docs/` | 按 `analysis/`、`architecture/`、`designs/`、`garage/`、`tasks/`、`guides/`、`plans/`、`references/` 分组的长文文档 |
| `garage/` | `Garage` phase 1 的实现骨架根目录，承接 core、contracts、packs 与 hosts |
| `artifacts/` | `Garage` phase 1 的当前主工件面 |
| `evidence/` | `Garage` phase 1 的当前证据面 |
| `sessions/` | `Garage` phase 1 的当前会话协调面 |
| `archives/` | `Garage` phase 1 的统一历史归档面 |
| `.garage/` | `Garage` phase 1 的机器辅助面、索引与 sidecars |
| `ahe-coding-skills/` | 现有 coding workflow 来源资产与相关设计规则 |
| `ahe-coding-skills/docs/` | 直接服务现有 coding workflow 资产的共享文档 |
| `ahe-coding-skills/templates/` | 直接服务现有 coding workflow 资产的模板 |
| `ahe-product-skills/` | 现有产品洞察 workflow 来源资产 |
| `ahe-product-skills/docs/` | 直接服务现有产品洞察 workflow 的共享文档 |
| `ahe-product-skills/templates/` | 直接服务现有产品洞察 workflow 的模板 |
| `ahe-refer-skills/` | 现有 refer / skill authoring 相关来源资产 |
| `templates/` | 其他可复用的 Markdown 模板 |
| `agents/` | 预留给角色化 agent 说明或提示词 |
| `rules/` | 预留给常驻规则 |
| `hooks/` | 预留给 hooks 设计与辅助脚本 |
| `ahe-refer-skills/skill-creator/` | skill 校验、打包、评测辅助脚本 |

`agents/`、`rules/`、`hooks/` 当前仍是轻量骨架目录，可按后续需要逐步填充。

## 现有来源资产：AHE Coding Skills

这一组内容在 phase 1 中主要为 `Coding Pack` 提供来源资产、约定与参考工作流。

| 类别 | Skills | 作用 |
| --- | --- | --- |
| Public Entry | `using-ahe-workflow` | 新会话入口、命令入口与 family discovery |
| Orchestrator | `ahe-workflow-router` | 当前 runtime router、恢复编排、路由与阶段判断 |
| Authoring | `ahe-specify`、`ahe-design`、`ahe-tasks` | 产出主链规格、设计和任务工件 |
| Upstream Review | `ahe-spec-review`、`ahe-design-review`、`ahe-tasks-review` | 评审上游主工件并给出结构化结论 |
| Implementation And Branches | `ahe-test-driven-dev`、`ahe-hotfix`、`ahe-increment`、`ahe-finalize` | 实现、支线分析与收尾闭环 |
| Quality And Gates | `ahe-bug-patterns`、`ahe-test-review`、`ahe-code-review`、`ahe-traceability-review`、`ahe-regression-gate`、`ahe-completion-gate` | 缺陷模式排查、质量评审、回归与完成门禁 |

完整目录说明见 `ahe-coding-skills/README.md`。

## 现有来源资产：AHE Product Skills

这一组内容在 phase 1 中主要为 `Product Insights Pack` 提供来源资产、约定与参考工作流。

| 类别 | Skills | 作用 |
| --- | --- | --- |
| Public Entry | `using-ahe-product-workflow` | 判断当前应该先从 framing、research、opportunity、concept、probe 还是 bridge 起步 |
| Framing | `ahe-outcome-framing` | 把模糊 idea 重写成更锋利的 outcome、用户、替代品和非目标 |
| Research | `ahe-insight-mining` | 从 web、GitHub、社区和本地材料里提取信号，并默认通过多 agent 讨论 / PK 收敛 `insight-pack` |
| Convergence | `ahe-opportunity-mapping`、`ahe-concept-shaping` | 选优先机会、生成多个 concept direction，并收敛 wedge |
| Validation | `ahe-assumption-probes` | 把最危险未知项转成低成本 probe 和 kill criteria |
| Bridge | `ahe-spec-bridge` | 把上游洞察和验证结果压缩成 `ahe-coding-skills` 可消费输入 |

如果你当前只知道“先别写代码，先帮我把产品想清楚”，默认来源入口仍是 `ahe-product-skills/using-ahe-product-workflow`。更细的说明见 `ahe-product-skills/README.md`。

## 关键文档

- `docs/garage/README.md`：`Garage` 的品牌定位、phase 1 设计链与阅读入口。
- `docs/tasks/README.md`：`Garage` phase 1 的开发任务拆解与执行顺序入口。
- `garage/README.md`：`Garage` phase 1 的实现骨架根目录与目录边界入口。
- `docs/README.md`：`docs/` 分组索引与维护约定入口。
- `docs/architecture/ahe-platform-first-multi-agent-architecture.md`：当前主架构文档采用的平台优先控制面与共享契约边界。
- `docs/plans/ahe-agent-platform-roadmap-and-adr-backlog.md`：长期能力路线图、阶段退出条件与需要逐步冻结的 ADR 清单。
- `ahe-coding-skills/docs/ahe-workflow-entrypoints.md`：现有 coding workflow 来源资产的入口规则。
- `ahe-coding-skills/docs/ahe-workflow-shared-conventions.md`：现有 workflow 记录表达、evidence、verdict 与 shared conventions。
- `ahe-coding-skills/docs/ahe-command-entrypoints.md`：现有 docs-only command contract。
- `docs/architecture/ahe-workflow-skill-anatomy.md`：workflow skill 的目标态 anatomy。
- `docs/guides/ahe-workflow-externalization-guide.md`：外部仓库采用 AHE workflow family 时的最小能力面。
- `docs/guides/ahe-path-mapping-guide.md`：默认逻辑工件如何映射到实际仓库路径。

## 常用模板

- `templates/AGENTS-template.md`
- `ahe-coding-skills/templates/task-progress-template.md`
- `ahe-coding-skills/templates/task-board-template.md`
- `ahe-coding-skills/templates/review-record-template.md`
- `ahe-coding-skills/templates/verification-record-template.md`

## 当前约束

- 以当前实际目录结构为准；引用路径时只使用仓库中真实存在的目录和文件。
- 当前仓库根目录已经作为 `Garage` 根目录使用，但现有 `ahe-*` 资产仍保留为来源资产。
- 这个仓库没有业务应用构建流程、数据库或统一 CI 流水线。
- 仓库中的大多数内容仍是 Markdown 资产；变更时优先保持路径清晰、引用准确、内容可复用。

## 可用验证

若修改的是仓库内或本地挂载的 Cursor skill，可在 `ahe-refer-skills/skill-creator/` 下运行这些脚本：

- `python -m scripts.quick_validate <skill-dir>`
- `python -m scripts.package_skill <skill-dir> [output-dir]`
- `python -m scripts.aggregate_benchmark <benchmark-dir>`
- `python -m scripts.generate_report <json-input> [-o output.html]`
- `python -m scripts.run_eval ...`
- `python -m scripts.run_loop ...`

运行这些脚本通常需要 `Python 3.12+`；部分评测命令额外依赖 `claude` CLI，在当前环境下通常不可用，这是预期限制。
