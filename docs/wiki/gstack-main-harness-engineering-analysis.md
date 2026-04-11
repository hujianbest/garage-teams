# gstack-main 框架源码分析报告：面向团队搭建 Harness Engineering 的可落地参考

这份报告不是从“它有哪些炫酷命令”出发，而是从**团队要如何把 Agent 能力工程化**出发，去拆解外部项目 `gstack-main` 这套框架真正重要的部分。

说明：本文中出现的路径均指被分析项目 `gstack-main` 内部的路径，不代表当前 `ahe` 仓库的目录结构。

如果把 `gstack` 简化成一句话，它本质上不是一个单点工具，而是一套把 Agent 开发流程**角色化、技能化、工具化、验证化**的工程骨架。它把很多原本散落在人脑中的开发习惯，落成了：

- 一组可安装、可调用的 `SKILL.md` 技能
- 一套由模板生成的技能文档流水线
- 一组真正可执行的 CLI 工具与浏览器自动化能力
- 一套分层测试、E2E、LLM eval、diff 选测与结果归档机制
- 一套围绕上下文、偏好、安全、记忆与团队治理的运行约定

对准备为团队搭建 harness engineering 的人来说，`gstack` 最值得学习的，并不是某一个 prompt，而是它如何把“让 Agent 可靠工作”拆成多个工程层面，然后分别加约束、加验证、加反馈闭环。

---

## 一、先给一个结论：gstack 代表的是哪一种 Harness 思路

`gstack` 不是“一个超级 Agent 自动帮你做完所有事”的路线，它更像一套**AI 工程工作流操作系统**。它的核心信念是：

1. **不同阶段应该由不同技能承担不同角色**，而不是一个大 prompt 包打天下。
2. **技能文档不能手写散养**，而要有模板、生成器和一致性校验。
3. **Agent 不是只会说，还要会做**，所以必须接浏览器、CLI、测试、评测和发布流程。
4. **昂贵测试不能全量乱跑**，需要 diff 感知、分层分级、结果归档。
5. **安全、范围边界、提问格式、团队偏好、上下文记忆** 这些“软约束”，都要尽量产品化、脚本化、标准化。

也就是说，`gstack` 把 harness engineering 看成五层能力的叠加：

- **Workflow Layer**：角色化技能和阶段化流程
- **Prompt Infra Layer**：模板、生成器、前置注入、跨宿主适配
- **Tool Layer**：浏览器、设计工具、配置工具、工作树工具
- **Quality Layer**：单测、E2E、LLM judge、diff 选测、CI
- **Governance Layer**：安全边界、贡献规则、文档治理、遥测与偏好

这个分层视角，非常适合作为团队落地 harness engineering 的总蓝图。

---

## 二、从源码看，gstack 的整体架构是什么

从 `README.md`、`AGENTS.md`、`CLAUDE.md` 和实际目录结构看，`gstack` 由三类核心资产组成。

### 1. 技能层：把开发流程拆成多个“专家角色”

`README.md` 把整套流程明确写成：

**Think → Plan → Build → Review → Test → Ship → Reflect**

对应到仓库中的技能目录，就是：

- `office-hours/`：需求重构与问题定义
- `plan-ceo-review/`、`plan-eng-review/`、`plan-design-review/`：计划阶段多角色评审
- `review/`：代码审查
- `investigate/`：问题调查与根因分析
- `qa/`、`qa-only/`：浏览器驱动的 QA
- `ship/`、`land-and-deploy/`：发布与部署
- `document-release/`：文档与代码发布后一致性修复
- `retro/`：复盘
- `cso/`：安全审计
- `codex/`：第二模型意见
- `careful/`、`freeze/`、`guard/`、`unfreeze/`：安全与编辑边界控制

这里最关键的不是 skill 数量多，而是它**强行把不同开发阶段拆开**。这意味着团队在设计自己的 harness 时，不应该一开始就追求“全能 Agent”，而应该先回答两个问题：

- 你的团队最常见的工作阶段是什么？
- 哪些阶段值得单独做成 skill，而不是揉进一个通用 prompt？

`gstack` 给出的答案是：需求澄清、计划评审、实现审查、QA、发布、文档、复盘都值得独立。

### 2. 运行时层：不仅有 prompt，还有真正能跑的工具

`gstack` 并不是只有 Markdown。

它有两个很关键的运行时子系统：

- `browse/`：基于 Playwright 的浏览器 CLI
- `design/`：设计相关 CLI，包括生成、对比、记忆提取等

其中 `browse/src/commands.ts` 直接把浏览器能力做成命令注册表，分成三类：

- 读操作：`text`、`html`、`links`、`forms`、`console`、`network` 等
- 写操作：`goto`、`click`、`fill`、`scroll`、`upload` 等
- 元命令：`snapshot`、`screenshot`、`handoff`、`resume`、`connect`、`watch` 等

这件事非常重要。因为它说明 `gstack` 的 skill 不是“凭空想象浏览器该怎么点”，而是有一个**稳定、可描述、可校验的工具面**。而且 `commands.ts` 还是单一事实源，它同时被：

- 运行时分发使用
- 文档生成器读取
- 校验脚本读取
- 测试使用

这就是标准的 harness thinking：**让工具定义成为多个系统共享的真相源**，而不是在 prompt 文档里重复描述一遍。

### 3. 工程基础设施层：生成、校验、测试、CI 都内置

`gstack` 的 `scripts/`、`test/`、`.github/workflows/` 不是附属品，而是它成为“工程化框架”的核心原因。

几个关键目录如下：

- `scripts/gen-skill-docs.ts`：从 `.tmpl` 生成 `SKILL.md`
- `scripts/resolvers/`：各类占位符解析器
- `scripts/skill-check.ts`：技能健康检查
- `test/`：静态校验、E2E、LLM eval、路由测试、hook 测试
- `lib/worktree.ts`：基于 git worktree 的隔离运行与 patch harvest
- `.github/workflows/`：gate/periodic eval 的 CI 落地

所以如果你要为团队搭 harness engineering，千万不要只学它的 skill 写法，更要学它的**生成 + 校验 + 测试 + CI** 四件套。

---

## 三、gstack 最值得复用的 8 个 Harness 机制

下面这部分是整份报告最关键的内容。因为团队落地时，真正有价值的是“哪些机制值得直接借鉴”。

### 机制 1：技能文档不是手写资产，而是“模板生成物”

`gstack` 明确规定：`SKILL.md` 是生成物，源头是 `SKILL.md.tmpl`。

在 `scripts/gen-skill-docs.ts` 里，整个生成流程很清楚：

1. 读取 `.tmpl`
2. 找到 `{{PLACEHOLDERS}}`
3. 由 resolver 从源码或规则中解析内容
4. 输出到对应 `SKILL.md`
5. 支持 dry-run 校验是否 stale
6. 统计 token budget

这带来几个团队级收益：

- 技能文档不容易和实现漂移
- 可以把重复片段抽成 resolver
- 可以针对不同宿主生成不同版本
- 可以在 CI 中检查生成物是否过期

对团队来说，这意味着你不应该直接把 skill 当成静态 prompt 文档管理，而应当把它当成**可构建产物**。

建议你后续落地时至少做三件事：

- 所有关键 skill 改成 `.tmpl + generated md`
- 把共享前置规则提取成 resolver
- 在 CI 里加“生成物 freshness 检查”

### 机制 2：Preamble 注入是整套系统的真正“运行时胶水”

如果只看 skill，很容易以为 `gstack` 只是长 prompt 的集合。但 `scripts/resolvers/preamble.ts` 说明，真正把整套系统粘起来的，是统一前置注入。

这个 preamble 负责做很多事情：

- 更新检查
- session 跟踪
- 当前分支输出
- repo mode 检测
- 用户偏好读取
- telemetry 状态读取
- analytics 本地落盘
- 提问格式规范
- completeness 原则
- contributor mode
- completion status protocol

也就是说，`gstack` 并不是让每个 skill 各自决定怎么问用户、怎么记录、怎么遵守规则，而是通过 preamble 把这些“元规则”统一注入到 skill 里。

这是团队落地时最应该优先复用的思想。

如果没有统一 preamble，会发生这些问题：

- 不同 skill 的提问风格和决策标准不一致
- 运行偏好无法共享
- 技能升级和治理规则分散
- 团队很难审计 Agent 的行为边界

因此，在你自己的 harness engineering 里，建议把 preamble 视为一级资产，内容至少包括：

- 当前 repo / branch / task 感知
- 团队统一的提问格式
- 风险分级和升级规则
- 用户偏好与团队策略读取
- telemetry / local analytics
- 完成状态协议

### 机制 3：跨宿主输出不是“兼容一下”，而是生成链路的一部分

`gen-skill-docs.ts` 不只支持 Claude，还支持 Codex 风格输出。

它做了几件关键事情：

- 根据 `--host` 选择输出路径
- 对 Codex 版本 frontmatter 做裁剪，只保留 `name + description`
- 从 hooks 提取安全说明，转成 inline prose
- 自动写 `openai.yaml`
- 检查 Codex description 长度是否超限
- 处理 symlink loop

这说明 `gstack` 对“多宿主兼容”的态度不是复制一份文档，而是把兼容层做进构建过程。

对团队而言，这特别有价值。因为很多团队后面会遇到：

- 本地开发用一个 Agent
- CI / 审计 / 评测用另一个 Agent
- 某些成员用 Cursor，另一些成员用 Codex / Claude Code

如果你不从一开始就设计**宿主适配层**，后面很容易把技能资产裂变成多个版本，维护成本迅速失控。

### 机制 4：工具描述也必须有单一事实源

`browse/src/commands.ts` 是一个典型的单一事实源设计。

它不只定义命令，还定义：

- 分类
- 描述
- 用法
- 与测试和文档的关联

这意味着浏览器命令的文档不是“另写一份说明书”，而是从同一个 registry 里反推。

这对团队非常有指导意义：

- 任何 Agent 工具，如果会被 prompt、文档、测试、UI、CLI 多处引用，都应该有 central registry
- 不要在 skill 文档中硬编码命令列表
- 不要让测试和文档各自维护不同的工具定义

如果你之后会为团队接入 MCP、内部脚本或服务，也建议按这个思路管理：

- 命令/工具定义
- 参数 schema
- 文档描述
- 测试映射
- 权限分类

最好来自同一个源头。

### 机制 5：昂贵评测必须做 diff 感知和分层分级

`test/helpers/touchfiles.ts` 可以说是 `gstack` 在“成本可控的可靠性工程”上最值得抄的部分之一。

它做了三件非常重要的事：

1. 每个 E2E / LLM judge 测试都声明依赖文件集合
2. 根据 `git diff` 自动判断本次应跑哪些测试
3. 把测试分成 `gate` 和 `periodic` 两级

这背后的思想很成熟：

- 不要因为有评测就全量跑，成本太高
- 也不要因为成本高就不跑，风险太大
- 应该通过“变更影响范围”来控制测试预算

这对团队搭 harness engineering 的现实意义非常大。因为只要进入 Agent 驱动阶段，测试成本通常会显著上升：

- 浏览器 E2E 很贵
- LLM judge 有 API 成本
- 跨 Agent E2E 更贵
- 多宿主验证更贵

如果没有 diff-based 选测机制，团队很快就会在“全跑太贵”和“不跑不放心”之间来回摇摆。

我的建议是，你们后面至少要复制这套三段式：

- **Tier 1**：免费静态校验和本地单测
- **Tier 2**：gate 级关键 E2E
- **Tier 3**：periodic 级质量评测 / 非确定性 eval

然后再加上 touchfile 风格的依赖声明。

### 机制 6：E2E 不是 mock skill，而是跑真实 Agent

`gstack` 的 E2E 测试不是简单断言字符串，而是通过 `claude -p` 之类的真实子进程跑技能行为。

这意味着它在验证的是：

- prompt 是否真的能驱动模型按预期执行
- skill 文档是否有歧义
- 工具调用链是否真的通
- 真实上下文中会不会出现路径、状态、行为偏差

这是一种非常“harness-native”的测试思路。因为对 skill 系统来说，真正的 bug 往往不在函数逻辑，而在：

- prompt 漏步骤
- 上下文顺序错误
- 工具描述不一致
- 模型行为偏移

这些问题，用普通 unit test 很难覆盖。

对团队来说，这意味着你们要接受一个现实：**skill 系统的正确性，必须部分依赖真实 agent-in-the-loop 测试**。

### 机制 7：worktree 隔离是多 Agent / 多模型验证的关键基础设施

`lib/worktree.ts` 很值得关注。

它做的不是简单开临时目录，而是：

- 创建 git worktree
- 拷贝必要的 gitignored 运行物
- 执行隔离测试
- harvest 测试过程产生的 patch
- 对 patch 去重归档
- 自动清理

这非常适合以下场景：

- 让不同模型对同一问题独立作答
- 让 QA / review / codex 等技能在隔离环境里运行
- 避免 agent 改坏主工作树
- 对多次尝试的输出做结果比对

如果你的团队后续会走向：

- 并行 agent
- best-of-n
- 多模型 second opinion
- 自动 patch harvest

那 worktree manager 这类基础设施非常值得尽早建设。

### 机制 8：设计系统也被纳入记忆与约束闭环

`design/src/memory.ts` 展示了 `gstack` 比较少见、但很值得借鉴的一点：它不只关心代码，也关心设计约束如何沉淀。

它会从批准的 mockup 中提取：

- 颜色
- 字体
- 间距
- 布局
- 整体 mood

再写入 `DESIGN.md`，后续作为约束被读取。

这背后的思想，其实和需求文档、计划文档、测试文档是一样的：

> 把跨会话、跨阶段、跨角色需要共享的信息，从临时上下文里拿出来，变成持久化工件。

这对团队的启发是：

- harness engineering 不应该只覆盖“代码 agent”
- 还应该覆盖设计约束、产品原则、术语规范、发布规则等长期记忆

---

## 四、gstack 的质量体系为什么值得团队重点学习

很多团队搭 Agent 流程，最容易忽略的是：**skill 能运行，不等于系统可靠**。

`gstack` 的质量体系之所以有参考价值，在于它同时覆盖了四种不同性质的问题。

### 1. 静态正确性

通过 `bun test` 跑：

- skill validation
- 文档生成质量检查
- browse 集成测试

这类测试便宜、快，适合每次提交都跑。

### 2. 行为正确性

通过 skill E2E 测试去验证真实 agent 是否按技能预期执行。

这解决的是“prompt 看起来合理，但 agent 真跑时不照做”的问题。

### 3. 质量回归

通过 LLM-as-judge 评估技能输出的质量，而不是只看流程是否执行成功。

这在设计、审查、路由类技能里尤其关键。因为很多时候不是“会不会执行”，而是“执行结果够不够好”。

### 4. 成本与频率控制

通过 touchfiles + gate/periodic，保证质量体系不会把开发流程拖垮。

对团队来说，这是一个很重要的提醒：

> Agent workflow 的测试体系，不能照搬传统应用测试体系。你必须同时平衡正确性、质量、成本和运行频率。

---

## 五、如果你要为团队搭 Harness Engineering，哪些地方可以直接照搬

下面按“可直接复用程度”来给建议。

### A 类：强烈建议直接照搬的机制

这些机制在大多数团队里都有普适价值。

#### 1. `.tmpl -> SKILL.md` 生成链路

原因：

- 易维护
- 易审计
- 易做多宿主适配
- 易做 CI freshness check

#### 2. 统一 preamble

原因：

- 统一行为边界
- 统一提问格式
- 统一 completion status
- 统一偏好、遥测、repo mode

#### 3. 工具 registry 单一事实源

尤其适用于：

- 浏览器命令
- MCP 工具
- 团队内部自动化命令

#### 4. diff-based eval selection

这是控制成本的关键，没有它很难长久运行。

#### 5. gate / periodic 双层质量体系

它让“每次必跑什么”和“定期抽检什么”有了结构化边界。

### B 类：建议按团队情况裁剪后复用的机制

#### 1. 多角色技能体系

`gstack` 的 skill 很多，但团队不必全抄。

更现实的做法是先做 5 类核心角色：

- 需求/计划
- 实现
- 审查
- QA
- 发布

其他如设计顾问、复盘、安全官，可以后续逐步加。

#### 2. `browse` 这类重运行时工具

如果你们的主要场景是 Web 产品、需要真实 UI 测试，那值得优先建设。

如果主要是后端、数据、平台工具，则可以先把浏览器能力延后。

#### 3. `design memory`

如果团队很重视 UI consistency，这一层非常有价值。

如果当前重点是纯后端流程，可以先不做。

#### 4. 多模型 second opinion

像 `/codex` 这种多模型交叉评审机制很强，但引入成本包括：

- 工具链更复杂
- CI 更复杂
- 成本更高
- 结果治理更复杂

适合在核心流程稳定后再引入。

### C 类：更适合作为理念参考，而不是直接复制的部分

#### 1. `gstack` 的话术与产品风格

`preamble.ts` 里有很强的风格约束和 Garry Tan 风格注入。这是它产品身份的一部分，不适合直接照抄。

你们可以学的是“统一 voice directive”，不是具体语气。

#### 2. telemetry 与 community mode

`gstack` 做了本地 analytics 和可选远端 telemetry，这对开源项目很合理。

但团队内部场景要先考虑：

- 数据合规
- 隐私要求
- 内部使用接受度

#### 3. YC / founder 风格的价值观注入

这个属于产品人格，不属于通用 harness 工程机制。

---

## 六、gstack 暴露出的前提条件与潜在风险

搭团队级 harness engineering，不能只看优点，也要看这套方案成立所依赖的前提。

### 1. 它依赖团队接受“长 Markdown skill 是工程资产”

很多团队愿意维护代码，不愿意维护 prompt 资产。

但 `gstack` 的前提是：

- skill 是正式资产
- 要写模板
- 要生成
- 要审查
- 要测试

如果团队文化还没接受这一点，照搬全套会比较痛苦。

### 2. 它对工具链有要求

运行它需要：

- Bun
- Playwright / Chromium
- 某些情况下还需要外部模型 API
- 某些 eval 依赖特定 Agent CLI

这说明团队落地 harness engineering 时，除了技能设计，还要考虑环境标准化。

### 3. 它的复杂度是“系统级”的，不是 prompt 级的

`gstack` 真正强的地方，也正是它重的地方：

- 技能多
- 构建链路多
- 测试层次多
- 运行时工具多
- 治理规则多

所以如果团队目前还处在“先试试 Agent 能不能帮上忙”的阶段，直接全盘引入是过重的。

### 4. 多宿主兼容会拉高维护成本

一旦要同时支持 Claude / Codex / 其他 SKILL.md 宿主，你们就必须维护：

- frontmatter 差异
- hooks 差异
- 安全约束差异
- 文档路径差异
- 测试宿主差异

这个成本要从第一天就预估进去。

### 5. E2E 失败归因会变得比传统测试更难

`CLAUDE.md` 专门写了 E2E eval failure blame protocol，这本身就说明：

- prompt 改动
- helper 改动
- 生成文档改动
- timing 变化

都可能导致真实 Agent 行为变化。

这会让“谁引发了失败”比传统代码测试更难判断。团队如果没有明确归因协议，后面很容易陷入扯皮。

---

## 七、对你后续搭团队 Harness Engineering 的建议路线图

如果你的目标是“参考 gstack，为团队搭一套可持续演进的 harness engineering”，我建议不要一步到位，而是按下面顺序推进。

### 阶段 1：先搭最小骨架，不追求功能齐全

目标：把“技能资产工程化”的底座搭起来。

建议先做这 5 件事：

1. 建一个团队技能仓库或技能目录
2. 统一 `SKILL.md.tmpl -> SKILL.md` 生成方式
3. 做一个共享 `preamble`
4. 选 3-5 个核心 skill 先落地
5. 给 skill 资产加最基础的静态校验

这个阶段不要急着做浏览器、遥测、多模型。

优先把“技能是资产，不是 prompt 草稿”这件事立住。

### 阶段 2：把工具层接上去

目标：让 Agent 不只是说，而是能稳定执行。

按业务场景选：

- Web 团队：优先浏览器能力
- 后端团队：优先 shell / test / deploy 工具封装
- 数据团队：优先 notebook / SQL / 评估工具封装

关键原则是：

- 工具定义要集中注册
- prompt 不要自己发明工具语义
- 文档、实现、测试都引用同一个工具定义

### 阶段 3：把质量闭环建起来

目标：让技能系统从“可用”变成“可依赖”。

建议顺序：

1. 静态 skill 校验
2. 几个关键 skill 的真实 E2E
3. diff-based 选测
4. gate / periodic 分层
5. eval 结果归档与对比

没有这一步，团队对 Agent 的信任很难稳住。

### 阶段 4：把治理和团队协作接进去

目标：让系统适合多人团队长期使用。

建议加入：

- repo mode / ownership 模式
- 统一 AskUserQuestion 格式
- 完成状态协议
- 失败归因协议
- 文档发布与收尾流程
- 审计日志 / local analytics

到这一步，才算真正进入 harness engineering，而不只是“做了一些技能”。

### 阶段 5：再考虑高级能力

包括：

- 多模型 second opinion
- 设计记忆
- 并行 agent / worktree harvest
- telemetry 仪表盘
- 全局 retro / 跨项目分析

这些都很有价值，但应该建立在前四阶段已经稳定的基础上。

---

## 八、如果让我替团队做取舍，我会怎么裁剪 gstack

如果要把 `gstack` 的方法论收敛成一套更适合大多数团队起步的方案，我会这样裁剪。

### 第一批一定做

- `tmpl + generator`
- shared preamble
- skill registry / skill check
- 计划 skill
- 实现/审查 skill
- QA 或验证 skill
- ship / release skill
- diff-based test selection

### 第二批再做

- 浏览器 CLI
- 多宿主输出
- 设计类 skill
- 文档 release skill
- worktree 隔离运行

### 最后再做

- 多模型交叉评审
- telemetry 社区化
- 全局 retro
- 设计记忆自动提取

换句话说，`gstack` 最该学的是它的**工程结构**，而不是它当前展现出来的完整技能规模。

---

## 九、对这套框架的总评价

如果站在“指导团队搭建 harness engineering”的角度，我会这样评价 `gstack`：

### 它最强的地方

- 把 skill 从 prompt 文档提升成了可构建、可测试、可治理的工程资产
- 把浏览器、设计、CLI、工作流、测试和文档治理整合进了同一个系统
- 非常重视“昂贵评测如何控成本”这个现实问题
- 对多宿主适配、范围边界、安全约束和团队治理有明确方案
- 展示了 Agent workflow 如何从个人玩法走向团队工程化

### 它最值得警惕的地方

- 整体复杂度高，不适合团队上来就全量照搬
- 很多能力依赖较强的工具链和使用纪律
- 多模型、多宿主、真实 E2E 会显著提高维护成本
- 风格和产品人格成分较重，需要和通用机制剥离开来看

### 最重要的启示

`gstack` 最值得学习的，不是“让 Agent 更像一个厉害的人”，而是：

> **让 Agent 系统更像一个可维护、可验证、可治理的工程系统。**

这才是 harness engineering 的核心。

---

## 十、给你的最终建议

如果你后续真要为团队搭 harness engineering，不要问“要不要做成 gstack 这样”，而应该问：

1. 我们团队最关键的 3-5 个工作流阶段是什么？
2. 哪些阶段最需要 skill 化，而不是继续靠自由对话？
3. 哪些规则必须通过 preamble 统一注入？
4. 哪些工具应该有单一事实源？
5. 哪些 eval 是必须 gate 的，哪些可以 periodic？
6. 我们准备接受多大程度的运行时和维护复杂度？

如果这六个问题答清楚，再去参考 `gstack` 的具体实现，你就不会把它当成一个“命令大礼包”，而会把它当成一套**AI 工程基础设施设计样本**。

这才是它对团队最有价值的地方。
