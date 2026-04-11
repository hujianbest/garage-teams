# W030: Hermes Agent Harness Engineering Analysis

- Wiki ID: `W030`
- 状态: 参考
- 日期: 2026-04-11
- 定位: 记录外部项目、方法与设计资料的分析结果，提炼对 `Garage` 的结构启发；默认作为参考资料，不作为当前主线真相源。
- 关联文档:
  - `docs/README.md`
  - `docs/GARAGE.md`
  - `docs/ROADMAP.md`

这份报告的目标不是复述 `hermes-agent` 的安装命令、平台列表或 marketing 文案，而是回答一个更重要的问题：

**如果我们想构建一个长期在线、跨入口、可积累经验、可扩展但又不失控的 agent runtime，Hermes Agent 的源码到底体现了哪些架构边界、工程取舍和设计思想。**

说明：本文中出现的路径均指被分析项目 `hermes-agent` 内部路径；在当前仓库里，它对应 `references/hermes-agent/`，不代表当前 `ahe` 仓库的目录结构。

---

## 一、结论先行

如果把 `hermes-agent` 压缩成一句话，它本质上不是“一个支持很多模型和很多聊天平台的 AI 助手”，而是一个偏个人使用场景的 **long-lived agent runtime / personal agent OS**：

- 用 `run_agent.py` 中的 `AIAgent` 作为统一核心循环，把 CLI、消息网关、ACP、批处理和训练相关入口收束到同一套执行语义
- 用 `agent/prompt_builder.py`、`agent/memory_manager.py`、`hermes_state.py` 把 prompt、记忆、会话搜索和技能沉淀做成长期状态，而不是单轮对话临时技巧
- 用 `tools/registry.py`、`model_tools.py`、`toolsets.py` 把“工具能力面”统一成一个可注册、可组合、可按平台裁剪的运行时层
- 用 `gateway/run.py`、`gateway/session.py` 把 Telegram、Discord、Slack、Email 等消息入口视为同一个 agent 的不同表面，而不是不同产品
- 用 `tools/approval.py`、`agent/prompt_builder.py`、`run_agent.py`、`pyproject.toml` 把安全、部署韧性、依赖可控性、安装路径约束直接写进实现

从 harness engineering 的角度看，Hermes 最值得借鉴的不是“功能很多”，而是它持续在做同一件事：**把 agent 从一次性聊天对象，提升为一个具有长期状态、统一控制面、跨入口连续性的运行时实体。**

同时，它也暴露出几类很真实的代价：

- 核心文件非常大，`run_agent.py`、`cli.py`、`gateway/run.py`、`hermes_cli/main.py` 都带有明显 monolith 特征
- 为了兼容多入口和异步工具，`model_tools.py` 里出现了比较复杂的 sync/async bridging 逻辑
- 工具系统依赖 import-time registration，扩展灵活，但也引入顺序、冲突和调试复杂度
- 跨平台策略是务实但不完全对称的，明确要求 Unix-like 环境，Windows 走 WSL2，`[all]` extra 也会主动绕开有问题的依赖

这说明 Hermes 的设计哲学不是“理论上最优雅”，而是 **围绕可运行、可连续、可积累、可扩展且可维护到一定程度的现实主义工程选择。**

---

## 二、分析范围

本报告基于对 `hermes-agent` 源码和少量开发文档的定向阅读，重点关注以下资产：

- 项目定位与打包入口：`README.md`、`pyproject.toml`
- 统一运行核心：`run_agent.py`
- CLI 入口与命令分发：`hermes_cli/main.py`、`cli.py`
- Prompt 与长期状态：`agent/prompt_builder.py`、`agent/memory_manager.py`、`agent/memory_provider.py`
- 工具系统：`model_tools.py`、`toolsets.py`、`tools/registry.py`
- 多 Agent / 子代理约束：`tools/delegate_tool.py`
- 安全护栏：`tools/approval.py`
- 会话持久化与检索：`hermes_state.py`、`gateway/session.py`
- 网关与多平台入口：`gateway/run.py`
- 扩展机制：`hermes_cli/plugins.py`
- 开发者总览校对：`website/docs/developer-guide/architecture.md`

分析重点不是穷举全部平台适配器或所有工具实现，而是提炼对 agent runtime 设计最有迁移价值的结构原则和取舍。

---

## 三、Hermes 到底是什么

从 `README.md` 和 `pyproject.toml` 看，Hermes 的产品定义非常鲜明：它不是一个“把模型接进终端”的薄壳，也不是一个“多平台聊天机器人集合”，而是一个强调 **self-improving**、**cross-session**、**runs anywhere** 的长期 agent。

这个定位在代码里不是口号，而是会落到结构上的：

1. 它强调 **长期连续性**  
   `README.md` 把 memory、session search、skills、closed learning loop 放在核心卖点里；`agent/prompt_builder.py` 则进一步把这些能力拆成不同的指导块，明确告诉模型什么信息该进入 memory、什么应该留在 transcript、什么应该沉淀为 skill。

2. 它强调 **多表面接入，但单一行为核心**  
   `pyproject.toml` 暴露出 `hermes`、`hermes-agent`、`hermes-acp` 三个脚本入口，但这些入口并不是三套不同 agent，而是汇入共享运行时。`website/docs/developer-guide/architecture.md` 也直接把 `AIAgent (run_agent.py)` 画在系统中心。

3. 它强调 **不绑死在本地机器**  
   `README.md` 明确把 CLI、gateway、serverless terminal backends、messaging continuity 放在一起讲；`toolsets.py`、`gateway/run.py`、`tools/environments/` 则体现出它在运行面上就是按“远程可运行 agent”来设计的。

4. 它强调 **agent 的能力积累，而不是单次回答质量最大化**  
   Hermes 的很多实现都不是为了把某一轮 answer 做到极致，而是为了让一个 agent 在多轮、多会话、多入口里保持身份、记忆、技能和操作连续性。这是它和很多“coding assistant + tool calling”项目最大的分野。

换句话说，Hermes 的产品原型更像：

- 上层是一个长期存在的 agent 身份
- 中层是 memory / session / skill / toolset / security / prompt contract
- 下层是 CLI、gateway、ACP、batch、tool backends、provider adapters

它卖的不是某个模型，而是一套 **agent continuity runtime**。

---

## 四、源码架构拆解：Hermes 的 7 个关键子系统

### 1. 一个核心循环，多种入口共用

Hermes 最核心的架构判断，是把平台差异压到边缘，把 agent 行为收束到 `run_agent.py` 的 `AIAgent`。

从入口看：

- `pyproject.toml` 暴露 `hermes = "hermes_cli.main:main"`
- `pyproject.toml` 暴露 `hermes-agent = "run_agent:main"`
- `pyproject.toml` 暴露 `hermes-acp = "acp_adapter.entry:main"`

从实际控制流看：

- `hermes_cli/main.py` 在最前面先处理 `--profile`，确保 `HERMES_HOME` 在其他模块 import 前就被确定
- `hermes_cli/main.py` 的 `cmd_chat()` 在做完 provider 检查、skills sync、session 续接等准备后，再桥接到 `cli.py`
- `gateway/run.py` 中的 `GatewayRunner` 负责多平台消息收发，但真正执行任务时依然调用 `AIAgent`

这意味着 Hermes 的真实分层不是“CLI 层”和“bot 层”分别实现业务逻辑，而是：

- 入口层负责接入与上下文恢复
- 核心层负责 conversation loop、tool use、memory、retries、fallback、persistence
- 平台层只负责把外部世界翻译成统一事件

这种设计的最大价值是 **一致性**：

- CLI 和 Telegram 并不是两个产品
- ACP 和 gateway 并不是两套不同 agent
- 工具调用、记忆注入、会话存储、安全约束都能复用同一套语义

对 harness engineering 来说，这个判断非常关键：**如果想让 agent 能跨入口持续工作，必须有一个比“交互界面”更高一级的 runtime 核心。**

### 2. Prompt 不是文案，而是运行时契约

Hermes 的另一个强设计信号是：它把 prompt 视为 runtime contract，而不是可随便拼接的文案。

`agent/prompt_builder.py` 体现了几个非常明确的判断：

- system prompt 由多个稳定部件装配：identity、memory guidance、session search guidance、skills guidance、tool-use enforcement、context files
- context file（如 `AGENTS.md`、`.cursorrules`、`SOUL.md`）在注入前会先经过 prompt injection 扫描
- 不同模型族会注入不同的执行纪律指导，例如 OpenAI 系模型会额外得到更强的 tool persistence / verification guidance

更重要的是，`run_agent.py` 在 `run_conversation()` 里不是每轮无脑重建 system prompt，而是显式缓存 `_cached_system_prompt`。在继续会话场景下，它甚至会优先从 session store 里恢复旧 prompt，而不是根据最新磁盘状态重算，原因是要保持 prompt prefix 稳定，从而命中 Anthropic prompt cache。

这个实现背后的思想很重要：

- prompt 会影响行为稳定性
- prompt 会影响缓存命中和成本
- prompt 漂移会制造“同一会话里 agent 身份突变”

也就是说，在 Hermes 里，prompt 不只是“告诉模型怎么做事”，而是系统一致性的一部分。

这对 AHE 类工作流尤其有启发：**workflow 里的指令、约束、状态注入，最好被视为可组合、可扫描、可缓存、可持久化的运行时契约，而不是随手堆进系统提示词的自由文本。**

### 3. 把长期知识拆成三层：Memory、Session、Skill

Hermes 最成熟的设计思想之一，是它没有把所有“长期性”都塞进同一个记忆系统，而是显式拆成三层：

1. **Memory**：稳定、可长期复用的事实  
   `agent/prompt_builder.py` 的 `MEMORY_GUIDANCE` 明确要求只保存 durable facts，例如偏好、环境约束、稳定约定，不要把任务进度和会话日志塞进去。

2. **Session Search**：跨会话召回的情节性记录  
   `hermes_state.py` 使用 SQLite + FTS5 存储 `sessions` 和 `messages`，并通过 `messages_fts` 做全文检索。这里存的是“发生过什么”，而不是“以后永远有效的事实”。

3. **Skill**：可复用工作流与程序性知识  
   `SKILLS_GUIDANCE` 明确要求在复杂任务或 tricky fix 之后把方法沉淀成 skill；如果 skill 过时，则直接 patch，而不是等用户提醒。

这套拆法在源码里非常一致：

- `agent/memory_provider.py` 规定 built-in memory 永远存在，external provider 只能外挂一个
- `agent/memory_manager.py` 明确限制同时只能启用一个外部 memory provider，避免 tool schema 膨胀和多后端冲突
- `hermes_state.py` 则负责 transcript persistence、FTS 搜索、session lineage

这不是实现细节，而是一种很成熟的知识分层：

- 稳定事实放 memory
- 历史证据放 session transcript
- 可复用方法放 skills

很多 agent 系统的问题恰恰是把这三者混在一起，最终导致：

- memory 垃圾化
- transcript 不可检索
- workflow 经验无法复用

Hermes 在这点上的工程意识非常强。

### 4. 工具系统是统一控制面，而不是零散函数集合

Hermes 的工具能力面不是 scattered utilities，而是一个统一的 runtime subsystem。

这里最关键的三个文件是：

- `tools/registry.py`
- `model_tools.py`
- `toolsets.py`

它们共同体现出几个关键判断。

第一，**工具注册统一到单一 registry**。  
`tools/registry.py` 说明每个工具文件在 import 时调用 `registry.register()`，注册 schema、handler、toolset、availability check。`model_tools.py` 不再自己维护一份平行结构，而是把 registry 作为唯一真相源。

第二，**tool discovery 是 import-driven 的**。  
`model_tools.py` 通过 `_discover_tools()` 批量 import `tools/*.py`，让各个工具在 import 时自注册。优点是扩展简单、工具与 schema 共址；缺点是有 side effect、顺序和 collision 风险。`tools/registry.py` 甚至直接对同名覆盖发 warning，说明作者也清楚这种模式的代价。

第三，**toolset 是产品能力面，不是代码组织顺手附带的标签**。  
`toolsets.py` 里有一个 `_HERMES_CORE_TOOLS`，注释写得很直白：**“Edit this once to update all platforms simultaneously.”**  
也就是说，CLI、Telegram、Discord、Slack、Email 等入口默认共享同一套核心工具语义；平台差异不是再复制一套功能，而是复用一套核心工具清单。

这说明 Hermes 把工具系统看成统一 agent surface，而不是“每个平台随便挑几个工具装上去”。这背后的设计哲学是：

- 工具能力应该是 agent 身份的一部分
- 平台不应轻易改变 agent 的能力边界
- 平台差异应更多体现在授权、回调、UI 和适配，而不是另起炉灶

### 5. 网关不是通知层，而是 agent 的第二生存空间

很多项目把 Telegram / Slack / Discord 集成做成“消息转发器”。Hermes 不是。

`gateway/run.py` 和 `gateway/session.py` 可以看出，gateway 在 Hermes 里是一个真正的一等运行模式：

- `GatewayRunner` 统一管理 adapters、session store、delivery router、running agents、pending approvals、voice mode、hooks、background tasks
- `adapter.set_message_handler(self._handle_message)` 说明所有平台消息最终都汇到同一个处理路径
- `SessionStore` 使用 SQLite 作为主存储，并保留 JSONL fallback，处理 session key、reset policy、历史 transcript、活跃进程保护
- `GatewayRunner` 还会 **按 session 缓存 `AIAgent`**，为了保留 frozen system prompt 和 tool schema，从而命中 prompt cache，避免每条消息都重建 agent 带来的成本和漂移

这一点非常能体现 Hermes 的产品判断：

- 消息平台不是“弱化版入口”
- CLI 不是唯一真入口
- agent 应该真正“活在”这些平台里，而不是被动接收转发消息

这也是为什么 `toolsets.py` 会让不同消息平台共享核心工具面，为什么 `gateway/run.py` 要处理 per-session model override、interrupt、approval、voice、hook、cron 等复杂细节。它在做的不是 bot integration，而是 **把同一个 runtime 延展到多表面交互环境里。**

### 6. 扩展性是开放的，但开放边界被设计得很克制

Hermes 并不是封闭系统。相反，它给了很多扩展点：

- `hermes_cli/plugins.py` 支持用户目录插件、项目目录插件、pip entry points
- 插件必须有 `plugin.yaml` 和 `register(ctx)`，可以注册工具、hooks、CLI commands
- `model_tools.py` 还会额外发现 MCP tools 和 plugin tools
- memory provider 也被抽象成专门的插件型能力

但更值得注意的是它的“克制”：

- `MemoryManager` 不允许同时启用多个外部 memory provider
- `tools/delegate_tool.py` 显式屏蔽子代理访问 `delegate_task`、`clarify`、`memory`、`send_message`、`execute_code`
- `delegate_tool.py` 还限制 `MAX_CONCURRENT_CHILDREN = 3`、`MAX_DEPTH = 2`

这些约束说明 Hermes 的设计哲学不是“能力开放得越多越好”，而是：

- 核心 runtime 必须保持可理解
- 扩展点必须有清晰 contract
- 子代理不是无限递归的 agent society，而是受限的并行工作器
- 共享 memory、跨平台 side effects、用户交互等高风险能力不能随便下放

对 harness engineering 来说，这点很重要。很多多 agent 系统的问题不是“不够开放”，而是开放得太快，结果：

- 权限边界模糊
- 状态写入互相污染
- 行为无法预测
- 调试成本陡增

Hermes 提供了一条更稳妥的路线：**先把 seam 设计清楚，再开放 extension。**

### 7. 安全与运维不是补丁，而是产品体验的一部分

Hermes 的另一个成熟之处，是它把安全和 operability 放到了产品核心，而不是文档附录。

`tools/approval.py` 是很典型的例子：

- 它把危险命令检测、approval state、gateway blocking approval、smart approval、permanent allowlist 聚合成单一真相源
- 因为 gateway 并发执行 agent turn，所以使用 `contextvars` 保存 session-local approval state，避免全局状态竞争
- 对 gateway 场景，它不是把 “approval_required” 暴露给 agent 自己处理，而是阻塞线程等待用户 `/approve` 或 `/deny`
- 超时默认 fail closed，返回明确的 `BLOCKED`

这说明 Hermes 的安全思想不是“遇到危险命令时提醒一下”，而是：

- approval 是运行时协议的一部分
- CLI 和 gateway 应有一致的安全语义
- 并发环境下的会话隔离要落实到实现细节

运维韧性也同样被写进代码：

- `run_agent.py` 的 `_SafeWriter` 明确为 systemd / Docker / daemon / ThreadPool 场景兜底，避免 broken pipe 或 closed stdio 直接把 agent 打崩
- `hermes_state.py` 采用 SQLite WAL，并对写竞争做 jitter retry，而不是单纯依赖 SQLite 默认 busy handler
- `pyproject.toml` 把依赖分成多个 optional extras，并在注释里写清楚为什么 `matrix` 要从 `[all]` 中排除，以避免一次安装拖垮整个 extra
- `README.md` 和文档明确声明 Native Windows 不支持，要求 WSL2，这是一种非常务实的环境边界声明

这些点看起来零碎，但合起来体现出一个很清楚的价值观：**真实运行环境里的脏问题，应该由 runtime 主动吸收，而不是推给最终用户自己解决。**

---

## 五、从源码里看到的 6 条设计思想

如果把上面的实现再抽象一层，Hermes 的设计思想大概可以压缩成下面 6 条。

### 1. 把 agent 设计成长期存在的主体，而不是一次性回答器

Hermes 的 memory、session search、skills、session lineage、gateway continuity 都围绕一个假设：用户面对的不是“这一轮模型调用”，而是一个持续存在、会积累经验、会跨入口延续上下文的 agent。

这个假设一旦成立，系统设计就会完全不同：

- 你需要状态分层
- 你需要会话恢复
- 你需要长期身份
- 你需要可持续工具面
- 你需要安全与操作连续性

### 2. 把平台差异压到边缘，把一致性留在核心

Hermes 最重要的结构判断，是让 CLI、gateway、ACP、batch 共享 `AIAgent`，把平台差异关在 adapter、command router、delivery、callback 这些边界模块里。

这种做法保证：

- 行为一致
- 能力一致
- 状态语义一致
- 安全策略一致

同时也减少了“每加一个入口就复制一份 agent 逻辑”的系统腐化。

### 3. 把长期知识分解成不同存储与不同行为路径

Hermes 明确区分：

- durable facts
- transcript recall
- procedural workflows

这使得 memory 不会变成“另一份 session log”，也使 skills 不会变成“把 prompt 备份到文件里”。这是它在长期 agent 设计上最成熟的一点。

### 4. 把 prompt、toolset、session store 都当成 runtime contract

在 Hermes 里：

- prompt 需要稳定、可扫描、可缓存
- toolset 需要统一、可组合、可按平台治理
- session store 需要支持 lineage、search、恢复和成本可控

这意味着很多在别的项目里被当作“实现细节”的东西，在 Hermes 里其实是运行时契约。

### 5. 扩展性要有 seam，但 seam 不能无边界

插件、MCP、memory provider、delegate subagents 都是 seam；而 one-external-memory、blocked tools、depth limit、approval queue 这些是 seam 的边界。

Hermes 不是没有开放性，而是明确反对“无限制开放”。这是一种典型的 runtime-first 心态。

### 6. 真实世界的脏问题，要由系统吸收

缓存漂移、并发 approval、broken stdout、SQLite 写争用、依赖碎裂、WSL2 边界，这些都不是“理论架构图”会出现的内容，但它们恰恰决定系统是否真的能长期运行。

Hermes 在很多地方都表现出一种很强的 operability pragmatism：**先活下来，再谈优雅。**

---

## 六、对 AHE / Harness Engineering 的具体启发

结合当前 `ahe` 仓库关注的 harness engineering 方向，Hermes 至少给出 8 个很有迁移价值的启发。

### 1. 不要把“长期记忆”做成一个桶

应该像 Hermes 一样，把：

- 用户/环境稳定事实
- 可检索历史证据
- 可复用操作方法

拆成不同的存储层和不同的注入策略。否则长期系统很快会被噪音淹没。

### 2. 需要一个高于 UI / CLI 的统一 agent core

如果未来 AHE 也希望有多入口形态，例如：

- 命令入口
- IDE / ACP 类入口
- 消息入口
- 批处理 / 评测入口

那么必须尽早形成统一 runtime contract，而不是让不同入口各自长出一套 agent 逻辑。

### 3. Prompt assembly 应该工程化

Hermes 的做法表明，prompt assembly 不该是散落在多个脚本里的字符串拼接，而应当：

- 有明确模块边界
- 支持稳定组合
- 能做安全扫描
- 能与 session persistence / caching 联动

这对任何 workflow-heavy 的 agent 系统都很关键。

### 4. Tool registry 和 toolset governance 值得单独设计

Hermes 的工具系统虽然有 import-side-effect 的代价，但它至少把：

- schema
- handler
- availability
- toolset membership

统一放到了一个清晰模型里。AHE 如果未来要向“平台化 agent runtime”靠近，这一层不应继续隐含在 prompt 或零散脚本中。

### 5. 多 Agent 不是越自由越好

`delegate_tool.py` 说明一个很重要的现实：多 agent 体系真正难的不是“能不能并发”，而是：

- 哪些能力可以下放
- 子代理能否写共享状态
- 能否继续递归派生
- 谁承担副作用
- 谁负责最终一致性

这类边界如果不先定清楚，多 agent 只会制造更多不可预测行为。

### 6. 会话系统需要支持 lineage 和搜索，而不只是 history replay

Hermes 的 `parent_session_id`、FTS5、context snippet、source filter 说明，会话存储不应只是“把历史 append 到 JSONL”。

对于长期 workflow 系统，更合理的目标是：

- 可搜索
- 可切分
- 可 lineage 追踪
- 可跨入口过滤

### 7. 安全与 approval 流程应该被当成 runtime 协议

Hermes 的 approval 设计提醒我们，安全不是单纯的 blacklist 或文案提醒，而应该是：

- 会话级状态
- 并发安全
- 人机交互协议的一部分
- 能跨入口保持一致语义

### 8. 产品能力面可以很大，但安装面必须可控

`pyproject.toml` 的 extras 划分很值得借鉴。即使能力很广，也不意味着要把所有依赖硬塞进默认安装。对 agent runtime 来说，**可安装、可升级、可定位问题** 本身就是平台能力。

---

## 七、Hermes 的局限与代价

Hermes 很强，但它的取舍也很鲜明。以下几类代价在源码里是清楚可见的。

### 1. 核心文件体积过大

`run_agent.py`、`cli.py`、`gateway/run.py`、`hermes_cli/main.py` 都是超大文件。这样做的好处是关键逻辑相对集中，坏处是：

- 新贡献者进入成本高
- 局部改动容易影响全局
- 代码 review 和测试定位都更难

### 2. sync/async bridging 带来隐性复杂度

`model_tools.py` 为了解决 cached async clients 与多线程环境的问题，维护了 main-thread persistent loop、worker-thread loop、async-context thread fallback 等路径。这很务实，但也意味着运行时心智负担明显上升。

### 3. import-time registration 扩展灵活，但调试不轻松

registry-first + import discovery 的模式，在功能增长时通常会面临：

- import 顺序敏感
- 工具覆盖冲突
- 可观测性下降
- optional dependency 缺失时的部分加载问题

Hermes 已经通过 warning 和 check_fn 做了一些治理，但根本代价依然存在。

### 4. 产品姿态清晰，也意味着边界清晰

Hermes 明确选择 Unix-like runtime，Windows 走 WSL2；明确拆分 extras；明确限制某些能力组合。这让系统更可控，但也意味着它不是“哪里都原生顺滑”的普适消费级产品。

### 5. prompt-level enforcement 很强，可能带来过度约束

Hermes 在 `prompt_builder.py` 中对某些模型注入很强的 tool-use enforcement 和 execution discipline。这对减少“空承诺”非常有效，但也可能在部分任务上让 agent 呈现出更重的执行偏置，牺牲一些对话弹性。

这些不是简单的缺点，而是 Hermes 作为 runtime-first agent 系统的自然代价。

---

## 八、最终判断

Hermes Agent 最值得研究的地方，不是它“支持 40 多个工具、十几个平台、很多 provider”，而是它如何把这些能力组织成一个 **持续存在的 agent runtime**。

如果把它的设计哲学压缩成一句话，我会这样描述：

**Hermes 试图把 agent 从一次性调用的大模型外壳，推进成一个具有长期身份、统一执行核心、分层记忆体系、受控扩展面和真实运维韧性的个人运行时系统。**

对 AHE / harness engineering 来说，它最有价值的不是某个具体实现技巧，而是以下几条原则：

- 先定义 runtime 边界，再扩展入口
- 先分清 memory / session / skill，再谈长期智能
- 先把 prompt / toolset / session store 工程化，再谈 workflow 稳定性
- 先给扩展点划边界，再谈多 agent
- 先处理真实运行问题，再谈架构优雅

如果说 Clowder 更像团队级多 Agent 协作平台，那么 Hermes 更像 **单体但长期在线的个人 Agent OS**。两者都不是“聊天 UI”，但它们分别站在协作平台层和个人 runtime 层，代表了两种非常值得分开吸收的 harness engineering 路线。
