# clowder-ai 源码分析报告：多 Agent 协作平台对 Harness Engineering 的启发

这份报告的目标不是复述外部项目 `clowder-ai` 的命令清单，而是回答一个更关键的问题：

**如果团队后续要把多 Agent 协作、身份常驻、流程治理和跨模型分工工程化，Clowder AI 的源码里有哪些结构、机制与边界，值得被吸收进一套团队级 harness engineering 框架。**

说明：本文中出现的路径均指被分析项目 `clowder-ai` 内部路径；在当前仓库里，它对应 `references/clowder-ai/`，不代表当前 `ahe` 仓库的目录结构。

---

## 一、结论先行

如果把 `clowder-ai` 压缩成一句话，它本质上不是“一个支持很多模型的聊天 UI”，而是一个位于 **模型** 和 **Agent CLI** 之上的 **协作平台层**：

- 用 `README.md`、`docs/VISION.md`、`docs/features/F059-open-source-plan.md` 明确把产品定位为“让 agent 成为团队，而不是工具调用器”
- 用 `packages/api/` 把身份、路由、记忆、审计、线程、协作协议和多平台网关收束为统一运行时
- 用 `packages/shared/` 和 `packages/mcp-server/` 维持跨端契约与工具能力分发
- 用 `docs/SOP.md`、`docs/ROADMAP.md`、`docs/features/`、`docs/decisions/` 把“怎么开发、怎么验收、怎么同步开源、怎么保持证据链”写成结构化制度，而不是藏在 prompt 里
- 用 `scripts/start-entry.mjs` 及一组本地脚本，把多进程、多端口、Redis、前后端、sidecar 和运行模式组织成可重复启动的本地协作环境

对 harness engineering 来说，Clowder 最值得借鉴的不是它“做了很多功能”，而是它把以下 6 类能力拆成了相对清晰的层：

1. **产品叙事层**：先定义“人和 Agent 的关系”，再定义工具
2. **平台职责层**：把身份、路由、记忆、纪律从模型能力里剥离出来
3. **CLI 适配层**：把 Claude/Codex/Gemini/opencode 看成不同供应商适配器，而不是不同工作流
4. **共享契约层**：把类型、schema、registry、工具协议抽到共享包
5. **治理工件层**：用 vision、SOP、feature spec、ADR、roadmap 管理演化
6. **运行与隔离层**：把 runtime、alpha、worktree、本地端口和数据存储约束成明确环境语义

同时，它也暴露出几个必须正视的代价：

- 系统边界很宽，产品形态、接入面和运行面都很复杂
- 对外部 CLI 输出行为与会话语义有较强依赖，适配层脆弱性高
- 运行方式偏本地多进程和脚本编排，新团队接入门槛不低
- 公开 CI / public gate 的覆盖面明显小于完整系统能力，存在“核心价值很多，公开验证面偏窄”的风险

---

## 二、分析范围

本报告基于对 `clowder-ai` 源码与高层文档的定向阅读，重点关注以下资产：

- 项目入口与定位：`README.md`、`AGENTS.md`、`package.json`
- 愿景与方法论：`docs/VISION.md`、`docs/SOP.md`
- 演进与成熟度：`docs/ROADMAP.md`、`docs/features/F059-open-source-plan.md`
- 技术架构：`docs/architecture/cli-integration.md`
- Monorepo 结构：`pnpm-workspace.yaml`
- 前端：`packages/web/package.json`、`packages/web/next.config.js`
- 后端：`packages/api/package.json`、`packages/api/src/index.ts`
- 共享层：`packages/shared/package.json`
- MCP：`packages/mcp-server/package.json`、`packages/mcp-server/src/index.ts`
- 工程验证：`.github/workflows/ci.yml`
- 运行入口：`scripts/start-entry.mjs`

分析重点不是穷举全部实现，而是提炼对团队建设 Agent 协作底座最有迁移价值的设计原则和工程取舍。

---

## 三、Clowder 到底是什么

从 `README.md`、`docs/VISION.md` 和 `docs/features/F059-open-source-plan.md` 可以看出，Clowder 解决的并不是“如何把一个大模型接进 Web 应用”，而是三件更底层的事：

1. 让多模型协作从“人肉切换窗口和复制上下文”升级成“平台级团队分工”
2. 让 Agent 的身份、记忆、协作纪律和审计能力跨会话持续存在
3. 让人与 Agent 的关系从“单次调用工具”转成“长期共创团队”

它的产品叙事非常完整，而且和工程设计是一致的：

- `README.md` 提出 **Hard Rails. Soft Power. Shared Mission.**
- `docs/VISION.md` 解释“缺的不是更强的 AI 工具，而是一支能把想法做成产品的团队”
- `docs/features/F059-open-source-plan.md` 把三层能力边界直接写成公开产品哲学：模型负责推理，Agent CLI 负责工具执行，平台负责身份、协作、纪律、审计和记忆

这意味着 Clowder 不是典型的“AI SDK 包装层”，而是更接近一个 **Agent Team OS / Collaboration Runtime**：

- 上层是 CVO（Chief Vision Officer）和团队协作体验
- 中层是 Hub、Mission Hub、Signals、Voice、A2A 路由等产品能力
- 下层是 AgentRouter、CLI 子进程调度、MCP、消息存储、线程、回调和多平台网关

另一个值得注意的事实是：`README.md` 已经用 `Clowder AI` 做公开品牌，但根 `package.json`、workspace package name 和大量内部命名仍保留 `cat-cafe`。这说明该项目并不是从零设计的开源产品，而是从内部生产工作台抽离出来的公开版本。这个“抽离态”既是它成熟度的来源，也是后续治理负担的来源。

---

## 四、源码架构拆解：Clowder 的 6 个关键子系统

### 1. 平台分层：先定义边界，再定义功能

`README.md` 和 `docs/features/F059-open-source-plan.md` 都反复强调三层边界：

- **模型层**：负责理解、推理、生成
- **Agent CLI 层**：负责工具使用、文件操作、命令执行
- **平台层**：负责身份、协作路由、流程纪律、审计追溯和记忆沉淀

这套分层非常关键，因为它把很多团队常犯的混淆拆开了：

- 不再把“模型是否聪明”当成“团队是否可靠”
- 不再把“CLI 是否能调工具”当成“多 Agent 协作是否成立”
- 不再把“prompt 写得更长”当成“系统有治理能力”

对 harness engineering 来说，这种边界定义比具体实现更重要，因为它明确告诉我们：**协作系统的真相源应该放在平台，而不是放在单个模型上下文里。**

### 2. Monorepo 分包：前端、后端、共享契约、MCP 四层分离

`pnpm-workspace.yaml` 只挂了 `packages/*`，说明这是一个相对标准的 pnpm monorepo。核心包的职责也很清晰：

- `packages/web`：Next.js 14 + React 18 前端，承载聊天、Hub、Mission Hub、Signals、游戏、终端等体验壳
- `packages/api`：Fastify 后端，是整个平台运行时和控制面的核心
- `packages/shared`：跨端共享类型、schema、registry、utils
- `packages/mcp-server`：独立的 stdio MCP 服务器，供平台或外部 Agent 接入工具能力

这种拆法的价值在于：

- 前后端边界清楚，不把业务逻辑揉进 UI 工程
- 共享契约可单独构建、复用和版本化
- MCP 能力不会硬绑在某个前端或 API 进程里
- 多 Agent 相关概念可以跨包复用，而不是四处复制字符串协议

对 AHE 这类仓库来说，`packages/shared` 这层尤其值得借鉴。很多团队把 workflow 术语、状态枚举、路由元数据散落在 prompt、脚本和后端逻辑里；Clowder 至少在结构上已经把它们收束成可编译、可导出的共享层。

### 3. API 运行时：真正的控制平面

`packages/api/src/index.ts` 非常长，但恰恰因为它长，才暴露了 Clowder 的真实形态：这不是一个单纯 API 服务，而是整个平台的 **runtime control plane**。

从入口文件能直接看出它装配了大量核心能力：

- Cat 配置和账户绑定
- Invocation queue / registry / tracker
- Agent registry 与多 provider service
- Authorization、memory、message、task、thread、workflow SOP store
- Push、TTS、terminal、preview、signal、leaderboard、project、workspace 等多个域
- 大量 route 注册，包括 `skills`、`signals`、`queue`、`sessionChain`、`workflowSop`、`workspaceGit`、`terminal`、`projects` 等

这说明 Clowder 的后端不是传统意义上的“给前端提供 CRUD 接口”，而是在承担：

- Agent 生命周期管理
- 多线程协作状态管理
- 记忆与证据存储
- 多渠道消息与事件桥接
- 运行态观测与辅助能力分发

这类设计的好处是平台能力集中，坏处是 API 层天然容易膨胀成大控制器。对 harness engineering 而言，Clowder 给出的启发是：**如果要做团队级 Agent 平台，后端很可能不是普通业务 API，而是“协调系统”本身。**

### 4. CLI 适配层：把供应商差异收敛在统一调度框架里

`docs/architecture/cli-integration.md` 是 Clowder 最有工程含金量的文档之一。它没有停留在“支持 Claude/Codex/Gemini”这种营销说法，而是明确给出了一套统一对接模型 CLI 的机制：

- `AgentRouter` 负责 mention 解析与目标 Agent 选择
- 各自的 `*AgentService` 负责供应商级适配
- `spawnCli()` 负责子进程生命周期管理
- `parseNDJSON()` 负责统一流式解析
- 上层再把厂商原始事件转换成统一消息类型

这里最值得吸收的不是 NDJSON 本身，而是两条原则：

1. **CLI 子进程优先于 SDK 直连**
2. **供应商差异尽量收敛在 adapter，而不是扩散进全系统**

文档里记录的经验也很真实，例如：

- 选择 CLI 是因为用户已有订阅、CLI 已包含工具能力、子进程隔离更安全、升级解耦
- `stderr` 活跃也要视为“进程仍在工作”，否则会误判超时
- 不同 CLI 的 session 恢复方式和事件流格式完全不同，必须先统一再上抛

这套设计对 AHE 非常有借鉴价值。AHE 当前更多是 workflow 资产仓，而不是 Agent 运行时；但如果后续要做多宿主或多模型适配，Clowder 证明了 **共享 workflow 逻辑 + 宿主 adapter** 这条路线是成立的。

### 5. MCP 与共享契约：把工具平面抽成独立能力

`packages/mcp-server/src/index.ts` 说明 Clowder 没把 MCP 当成 Claude 专属能力，而是把它做成独立 Node 进程上的 stdio server。入口逻辑很薄：

- 创建 `McpServer`
- 注册完整工具集
- 通过 `StdioServerTransport` 对外服务

再结合 `packages/shared/package.json` 导出的 `types`、`schemas`、`utils`、`registry` 可以看出，Clowder 在结构上区分了：

- **共享协议**：类型、schema、registry
- **共享工具面**：MCP server
- **运行时接入**：API 或 Agent CLI 再按需探测、注入、调用

这种设计的价值是显著的：

- 让 MCP 变成平台能力，而不是某个模型的专属附属品
- 让共享契约可以在不同包间稳定复用
- 让工具能力具备相对独立的演进空间

对于任何希望把“技能 / 工具 / 工作流”解耦的 harness 来说，这是一个非常值得参考的拆层方式。

### 6. 运行脚本与环境纪律：本地多进程协作栈

根 `package.json` 和 `scripts/start-entry.mjs` 显示，Clowder 的运行模式是明显的 **local-first、多进程、脚本编排**：

- `pnpm start`、`pnpm start:direct`、`pnpm dev:direct` 通过统一入口分发到 Windows PowerShell 或 Unix shell
- 默认依赖 Node 20+、pnpm、Git，Redis 可选但在主路径里被视为一等能力
- `docs/SOP.md` 进一步把 runtime、alpha、worktree 区分成不同环境语义，并对端口、重启和验收做了硬约束

`packages/web/next.config.js` 也能看到典型的本地一体化运行方式：

- 前端通过 rewrite 把 `/api`、`/socket.io`、`/uploads` 转发到 API 基址
- 同时内置 PWA 缓存策略
- 默认 API 端口和前端端口之间存在固定约定

这类运行方式的优点是：

- 本地体验完整，适合高频 dogfooding
- 能快速验证真实协作链路，而不是只跑最小 demo
- 容易承载 Hub、Signal、Voice、Game、Connector 这类复合能力

缺点也很明显：

- 本地环境复杂度高
- 脚本、端口、sidecar、缓存和数据路径都需要高度一致
- 新贡献者接入成本会明显高于纯前端或纯 SDK 仓库

---

## 五、Clowder 最强的地方：不是“功能多”，而是“治理真的写进系统里了”

很多 Agent 项目都有路线图、README 和一堆 feature page，但 Clowder 的特殊之处在于：这些文档不是装饰品，而是在共同定义系统边界。

### 1. Vision 不是营销文案，而是角色定义

`docs/VISION.md` 直接把“人是作者，猫是共创放大器”“领养团队，不是配置工具”“没有 Boss Agent，但执行有纪律”写成系统前提。  
这会反过来影响：

- UI 里为什么强调每只猫的身份
- 为什么要有 shared memory、skills、review、gate
- 为什么产品从一开始就不是单 Agent 控制台

### 2. SOP 不是开发建议，而是运行纪律

`docs/SOP.md` 把以下内容写成显式流程：

- Design Gate
- worktree
- quality-gate
- review 循环
- merge-gate
- 愿景守护

它甚至进一步规定：

- runtime 单实例保护
- alpha 验收通道
- 何时允许跳过 PR review
- 开源仓 hotfix lane
- full sync gate 和 release provenance

也就是说，Clowder 不只是“做出一个多 Agent 平台”，而是在给“如何运营这个平台、如何保证它不自我腐化”建立制度化约束。

### 3. Feature Doc / Roadmap / ADR 构成了演化真相源

`docs/ROADMAP.md` 保留活跃 feature，`docs/features/` 用 F 编号维护规格，`docs/decisions/` 沉淀关键决策。  
这种结构对 harness engineering 的价值非常高，因为它把以下三类信息拆开了：

- **现在要做什么**：roadmap
- **具体要做到什么**：feature spec
- **为什么这样设计**：decision / ADR

这比“所有信息都在 issue 和 PR 里”要可读得多，也更适合让 Agent 读取后参与持续协作。

---

## 六、对 AHE / 团队级 Harness Engineering 的可迁移价值

如果从 AHE 的视角去看，Clowder 最值得吸收的不是产品外观，而是以下几点工程思想。

### 1. 把“平台层”单独命名出来

AHE 现在更偏 workflow 与 skill 资产仓。Clowder 的启发是：一旦要支持多 Agent、多宿主、多模型、多渠道，就必须显式承认“平台层”存在，并为它定义职责边界。  
否则身份、协作、状态、审计和记忆会散落在各类 prompt、脚本和文档里，难以维护。

### 2. 用 adapter 吃掉宿主差异，不要复制 workflow

Clowder 的 `AgentRouter -> AgentService -> spawnCli/parseNDJSON` 路线证明，Claude/Codex/Gemini 这类差异更适合作为 **适配问题**，而不是 **工作流分叉问题**。  
对 AHE 来说，这意味着如果未来要兼容多种 agent host，应该优先收敛共享 contract，再做 host-specific adapter。

### 3. 让治理文档真正参与运行时

Clowder 的 `VISION`、`SOP`、`ROADMAP`、`Fxxx` 不是纯资料，它们在决定：

- 角色定义
- 环境纪律
- review / gate 节奏
- 开源同步规则
- 完成标准

AHE 也在做 workflow 工件和 router；Clowder 提醒我们，**只做节点定义还不够，还要把“环境语义”“发布语义”“审计语义”写成 Agent 可读、团队可执行的工件。**

### 4. 共享契约必须独立成层

`packages/shared` 的存在本身就是一个信号：一旦多个包、多个宿主、多个运行时要共享概念，术语、状态、schema 和 registry 最好不要四散定义。  
AHE 若未来产生脚本、服务、UI 或 CLI 层，应该尽早考虑这类共享层，否则工作流术语很快会飘。

### 5. 运行隔离是 Agent 平台的底线能力

`docs/SOP.md` 里的 runtime / alpha / worktree 分层非常值得注意。  
很多团队在做 Agent 平台时只谈 prompt 和工具，不谈“哪套环境允许 restart、哪套环境只做验收、哪套环境跑 feature worktree”。Clowder 说明：**环境纪律本身就是平台能力的一部分。**

---

## 七、优势总结：为什么这个项目有参考价值

### 1. 产品叙事和工程实现高度一致

很多项目会在 README 里讲愿景，但源码里看不见。Clowder 的优势是：

- README 讲多 Agent 团队
- 文档讲 CVO、SOP、共享记忆
- 代码里确实有 thread、queue、memory、review、signals、terminal、connector、MCP、voice 等系统级实现

这说明它不是“概念先行，工程没跟上”，而是已经有较强的 dogfooding 痕迹。

### 2. CLI 集成层的工程经验很成熟

`docs/architecture/cli-integration.md` 展示的不是纸上方案，而是踩坑后的工程收敛，包括：

- 为什么不用 SDK
- 如何做会话恢复
- 如何做 NDJSON 解析
- 如何判断子进程是否仍然活着
- 如何把不同供应商事件变成统一消息模型

这部分对任何要做多 Agent 平台的人都非常有价值。

### 3. 文档资产已经接近“治理系统”

`docs/README.md`、`docs/VISION.md`、`docs/SOP.md`、`docs/ROADMAP.md`、`docs/features/` 和 `docs/decisions/` 共同形成了一个高密度知识面。  
它不只是方便人阅读，也天然适合被 Agent 读取、路由和验证。

### 4. 工程面并不“玩具化”

从 `.github/workflows/ci.yml`、`pnpm check`、`dependency-cruiser`、目录大小检查、PWA、WebSocket、Redis、SQLite、MCP、多平台 SDK 这些细节来看，Clowder 已经超出“演示性 AI 项目”的范畴，更接近长期演化中的产品底座。

---

## 八、风险与局限：哪些地方不能照抄

### 1. 系统面太宽，复杂度管理压力大

Clowder 同时覆盖：

- 多 Agent 协作
- 多模型 CLI
- 线程与记忆
- Mission Hub / Signals / Voice / Game
- 多平台聊天网关
- MCP 与外部工具

这种广度很容易让 API runtime 变成巨型控制平面。它适合已经接受“平台型复杂度”的团队，不适合还在验证单一核心场景的团队直接照搬。

### 2. 对外部 CLI 契约的依赖是天然脆点

既然走 CLI 子进程路线，平台就要持续吸收这些波动：

- 输出格式变化
- session 行为变化
- stdout / stderr 语义差异
- resume 机制差异
- 不同厂商的权限与工具约束差异

这条路线的上限很高，但维护成本也会长期存在。

### 3. 运行与部署偏本地脚本化，复制成本不低

从 `package.json`、`scripts/start-entry.mjs` 和相关脚本看，Clowder 更像一套本地协作工作台，而不是天然云原生的 SaaS 部署单元。  
这很适合强 dogfooding，但对外部团队而言意味着：

- 环境一致性要求高
- 脚本兼容性要长期维护
- 端口、Redis、sidecar、缓存目录等问题都会变成一线运维问题

### 4. 公开验证面小于系统真实能力面

`.github/workflows/ci.yml` 的 `Test (Public)` 只跑 `@cat-cafe/api` 的 `test:public`。  
而 `packages/api/package.json` 中的 `test:public` 又通过一长串排除规则过滤了不少测试。这个做法可以理解为“为开源公共环境裁剪可运行测试集”，但它也意味着：

- CI 绿并不代表整个平台关键能力都被覆盖
- 部分跨域或依赖运行态的回归，可能落在 public gate 之外

如果 AHE 将来借鉴它的做法，最好把“公开 gate”和“完整 gate”明确区分，并持续记录两者差距。

### 5. 当前快照仍有“抽离态”痕迹

当前快照里至少有两个明显信号：

- 品牌名是 `Clowder AI`，但 package 与大量内部命名仍是 `cat-cafe`
- 根 `package.json` 定义了 `pnpm gate -> bash ./scripts/pre-merge-check.sh`，但在当前快照中 `scripts/pre-merge-check.sh` 不存在

这不影响其核心思路的参考价值，但说明该仓库仍处于“从内部系统向公开产品持续同步”的过程中。对于读者而言，应该把它当成 **成熟思路 + 仍在清理中的公开产物**，而不是把每个脚本入口都视为最终稳定接口。

---

## 九、总结：Clowder 给我们的真正启发

Clowder AI 最值得研究的地方，不是它把多少模型接进了一个页面，而是它证明了一件事：

**多 Agent 协作要想真正稳定，必须把“身份、路由、记忆、纪律、证据和环境隔离”从零散经验提升为平台能力。**

它给团队级 harness engineering 的核心启发可以归纳为四句话：

1. **先定义平台边界，再定义技能和流程。**
2. **先收敛共享契约，再适配不同宿主。**
3. **先把治理写成工件，再让 Agent 读取这些工件。**
4. **先把运行环境分层，再谈自动化协作的可靠性。**

如果未来 AHE 要从“workflow 资产仓”进一步走向“团队级 Agent 协作底座”，Clowder 是一个非常值得持续跟踪的参考样本。它的上限不是“更像一个聊天工具”，而是“更像一个真正的 Agent 团队运行时”。
