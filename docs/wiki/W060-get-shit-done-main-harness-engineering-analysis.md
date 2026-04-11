# W060: Get Shit Done Harness Engineering Analysis

- Wiki ID: `W060`
- 状态: 参考
- 日期: 2026-04-11
- 定位: 记录外部项目、方法与设计资料的分析结果，提炼对 `Garage` 的结构启发；默认作为参考资料，不作为当前主线真相源。
- 关联文档:
  - `docs/README.md`
  - `docs/GARAGE.md`
  - `docs/ROADMAP.md`

这份报告的目标，不是复述 `get-shit-done` 提供了哪些命令，而是回答一个更关键的问题：

> 如果你想为团队搭一套可长期演进的 harness engineering，这个框架到底提供了哪些值得借鉴的工程机制？

说明：下面列出的路径均指被分析项目 `get-shit-done-main` 内部的路径，不代表当前 `ahe` 仓库的目录结构；我通读的重点对象包括：

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/AGENTS.md`
- `bin/install.js`
- `get-shit-done/bin/gsd-tools.cjs`
- `get-shit-done/workflows/*.md`
- `hooks/*.js`
- `tests/*.test.cjs`
- `sdk/src/*.ts`

结论先行：`get-shit-done`（后文简称 GSD）本质上不是“一个命令包”或“一个提示词仓库”，而是一套围绕 **上下文工程、阶段化工作流、多 agent 编排、文件态状态管理、验证闭环、多 runtime 适配** 构建出来的 Agent 交付系统。

如果把它放到团队级 harness engineering 语境下看，它最值得学习的不是口号式的“spec-driven development”，而是它如何把 Agent 开发拆成可治理的工程对象：

- 命令是资产
- workflow 是资产
- agent 定义是资产
- `.planning/` 状态工件是资产
- hooks 是资产
- installer/runtime adapter 是资产
- 测试与安全扫描也是资产

这套思路，非常适合作为团队搭建 harness engineering 的参考母体。

---

## 一、先给一个总体判断：GSD 属于哪一种 Harness 路线

如果只看 README，GSD 看起来像一套“让 Claude Code 更可靠”的 meta-prompting 系统；但从源码和架构文档看，它实际上走的是一条更完整的路线：

### 1. 它不是单 Agent 神 prompt，而是阶段化操作系统

README 里把核心流程明确成：

- `new-project`
- `discuss-phase`
- `plan-phase`
- `execute-phase`
- `verify-work`
- `ship`
- `complete-milestone`

这说明 GSD 的基本单位不是“一次对话”，而是 **项目 / 里程碑 / phase / plan** 这套层级化交付单元。

这点对团队非常重要。因为真正可持续的 harness engineering，从来不是让 Agent 在一个上下文里“尽量多做事”，而是：

1. 把工作拆成阶段
2. 为每个阶段定义上下文入口
3. 为每个阶段定义产物
4. 为每个阶段定义验证方式
5. 让后续阶段消费前一阶段的工件

GSD 已经把这件事产品化了。

### 2. 它的“可靠性”主要来自 fresh context + file-based state

GSD 反复强调 context rot，也就是上下文越积越长后质量退化。它的核心对策不是“更会提示模型”，而是两件事：

- **每个 agent 使用 fresh context window**
- **把跨阶段记忆写回 `.planning/` 文件系统**

也就是说，它不是让主对话持续记住一切，而是把记忆外置到文件，再让不同 workflow 和 agent 按需加载。

这对团队落地时有很强指导意义：

- 不要把“长期记忆”押注在会话上下文里
- 要把记忆做成 inspectable artifacts
- 这些 artifacts 最好既给人看，也给 agent 读

### 3. 它是一套“编排系统”，而不是单点工具

从 `docs/ARCHITECTURE.md` 和 `sdk/src/phase-runner.ts` 看，GSD 的主线一直是：

- 薄 orchestrator
- 专职 subagent
- 文件态状态
- 事件流
- 每阶段明确职责

这意味着如果你想给团队搭 harness engineering，GSD 最值得借鉴的是 **编排思想**，不是其中任何一个孤立命令。

---

## 二、从源码拆开看：GSD 的系统由哪几层构成

如果站在架构视角，我会把 GSD 划成六层。

### 1. Command Layer：面向用户的入口层

这一层主要在：

- `commands/gsd/*.md`

用户通过 `/gsd:new-project`、`/gsd:plan-phase`、`/gsd:execute-phase` 之类的命令进入系统。命令文件本质上是 prompt 入口，负责：

- 定义用途
- 提供参数提示
- 挂接具体 workflow

这里的启发是：**团队的 harness 不应该只暴露“一个万能命令”**。更合理的是按交付节点提供有限、明确、语义稳定的入口。

### 2. Workflow Layer：核心编排层

这一层在：

- `get-shit-done/workflows/*.md`

真正的系统逻辑放在 workflow 里，而不是放在 command 入口里。比如：

- `new-project.md` 负责初始化项目、深问、研究、需求、roadmap
- `execute-phase.md` 负责计划发现、wave 分组、并行执行、分支策略、校验
- `verify-work.md` 负责把 summary 中的交付结果转成可执行 UAT

这意味着 GSD 的设计很清晰：

- command 负责“用户怎么进来”
- workflow 负责“系统怎么运转”

对团队来说，这是一条很值得照搬的分层原则。

### 3. Agent Layer：专职角色层

这一层主要在：

- `agents/*.md`
- `docs/AGENTS.md`

GSD 不是一个统一的 worker，而是一组功能明确的 agent：

- researcher
- planner
- roadmapper
- executor
- plan-checker
- verifier
- debugger
- codebase-mapper
- ui-checker / ui-auditor / nyquist-auditor 等

这背后的意义很大：**不同阶段的 agent，有不同的工具权限、输入上下文、输出工件和模型档位**。

团队落地时，不应该上来就做“一个全能工程师 agent”，而应先定义几个稳定角色：

- 需求澄清/研究
- 计划生成
- 执行实现
- 验证验收
- 调试修复

### 4. CLI / State Layer：文件态真相源

这一层在：

- `get-shit-done/bin/gsd-tools.cjs`
- `get-shit-done/bin/lib/*.cjs`

这是 GSD 的一个关键点：workflow 不是直接手写一堆 shell 逻辑，而是通过 `gsd-tools.cjs` 访问结构化能力。

从入口可以看出它内置了很多 domain module：

- `state.cjs`
- `phase.cjs`
- `roadmap.cjs`
- `config.cjs`
- `verify.cjs`
- `template.cjs`
- `frontmatter.cjs`
- `milestone.cjs`
- `security.cjs`
- `uat.cjs`
- `workstream.cjs`

这说明 GSD 不仅有“工作流提示词”，还有一个真实的状态操作 API 层。

这对团队落地特别重要，因为一旦没有这层能力，workflow 就会退化成“在 Markdown 上瞎写 shell 脚本”。

### 5. Hook Layer：运行时增强层

这一层在：

- `hooks/gsd-statusline.js`
- `hooks/gsd-context-monitor.js`
- `hooks/gsd-check-update.js`
- `hooks/gsd-prompt-guard.js`
- `hooks/gsd-workflow-guard.js`

这些 hooks 不是可有可无的小配件，而是把运行时治理接进系统的关键。

比如：

- 上下文预警
- 更新检查
- 写入 `.planning/` 时的 prompt injection 提示
- 非 workflow 上下文编辑代码时的提醒

这说明 GSD 把“Agent 行为约束”往运行时前移了，而不是只依赖静态文档约束。

### 6. Runtime Adapter / Installer Layer：多宿主分发层

这一层主要在：

- `bin/install.js`

安装器体量非常大，不只是复制文件。它要处理：

- 运行时选择
- 全局/本地安装
- 命令、workflow、agent、hooks 的部署
- Claude/OpenCode/Gemini/Codex/Copilot/Cursor/Windsurf/Antigravity 的格式转换
- 路径替换
- settings 集成
- 本地修改备份与回放
- manifest 记录
- uninstall

这意味着 GSD 已经把“多宿主适配”设计成系统内建能力，而不是事后补丁。

---

## 三、GSD 最值得团队复用的 10 个 Harness 机制

下面这部分是整份报告最重要的内容。因为你后续不是要“理解一个项目”，而是要从里面拿出方法论去搭自己的团队系统。

### 机制 1：把工作流拆成稳定阶段，而不是让一个 Agent 从头跑到尾

GSD 用 phase 驱动整个系统：

- discuss
- research
- plan
- execute
- verify
- ship

并且每一步都对应明确工件。

这种方式最适合团队场景，因为它天然支持：

- 阶段复查
- 阶段回滚
- 阶段重跑
- 阶段审计
- 多人协作接力

如果你后续为团队搭 harness，我建议第一版就强约束“阶段化”，至少具备：

- intake / clarify
- plan
- execute
- verify
- release

### 机制 2：把状态写进 `.planning/`，让文件系统成为第一真相源

GSD 的 `.planning/` 不是附属目录，而是系统核心。

典型工件包括：

- `PROJECT.md`
- `REQUIREMENTS.md`
- `ROADMAP.md`
- `STATE.md`
- `config.json`
- `research/`
- `codebase/`
- `phases/*`
- `quick/`
- `todos/`
- `threads/`
- `seeds/`
- `debug/`

这带来的收益很实际：

- 上下文压缩或切换后还能恢复
- 人和 agent 都能读
- 可以被 git 跟踪
- 可以做审计
- 可以做自动恢复与增量推进

如果没有这一层，你们团队后续会非常依赖“某个会话还没丢”“某个 agent 还记得”。这在工程上很脆弱。

### 机制 3：orchestrator 只负责编排，重活都交给专职 agent

在 `docs/ARCHITECTURE.md` 和多个 workflow 中都能看出，GSD 对 orchestrator 有强约束：

- 负责初始化上下文
- 负责拉起 agent
- 负责收集结果
- 负责推进状态
- 不自己做重研究、不自己写大量实现、不自己承担全部思考

这个思想对团队非常关键。

因为很多团队在做 harness 时，容易把 orchestrator 写成“超级代理”，最终问题会变成：

- prompt 巨长
- 职责混乱
- 上下文污染严重
- 失败时不好归因

而薄 orchestrator + 专职 agent 的模式，更容易做到：

- 换模型
- 换角色
- 局部替换
- 单点评估
- 权限最小化

### 机制 4：执行阶段不是简单串行，而是基于依赖图的 wave 并行

`execute-phase.md` 和 `sdk/src/phase-runner.ts` 都强调 wave 执行模型。

这不是一个小优化，而是 GSD 走向“工程系统”的标志。因为它已经开始解决真实交付中的几个难题：

- 哪些 plan 可并行
- 哪些 plan 必须等待依赖
- 并行执行如何避免 git / hook / state 互相踩踏

在 SDK 的 `PhaseRunner` 中，也能直接看到它对 plan 按 wave 分组，再并发执行，wave 之间串行推进。

这对团队落地很有借鉴意义：

- 计划必须带依赖信息
- 并行不能只靠“感觉可以一起跑”
- 编排器要有显式的波次概念

如果你们团队后续会用多 agent 并发交付，这套 wave 模型非常值得尽早引入。

### 机制 5：执行结果必须被结构化验证，而不是“改完就算完成”

GSD 的 verify 并不是可选装饰，而是主流程一部分。

它至少有三层验证思路：

1. **plan-check**：执行前校验计划是否靠谱
2. **verifier**：执行后校验是否达到 phase 目标
3. **verify-work / UAT**：让用户按一个个测试点去确认实际体验

更重要的是，`sdk/src/phase-runner.ts` 里的 verify 逻辑不是一次性检查，而是支持：

- passed
- human_needed
- gaps_found

如果发现 gaps，还可以再触发 plan → execute → re-verify 闭环。

这说明 GSD 的心智模型不是“生成一次成功”，而是“通过结构化验证把错误闭环掉”。

这正是团队级 harness engineering 最该优先建设的能力。

### 机制 6：用户验收被做成文件化的对话式 UAT

`verify-work.md` 很值得细看，因为它没有把 UAT 当成一句“请你自己测一下”。

它做的是：

- 从 `SUMMARY.md` 中提取可观察交付物
- 生成 `UAT.md`
- 按测试点逐个向用户提问
- 把用户反馈回写文件
- 让 UAT 可以在会话切换后继续
- 把发现的 gap 再喂回后续规划

这比大多数 Agent 工作流成熟很多。

团队落地时，这一层尤其重要，因为很多失败并不出在代码没写，而出在：

- 体验不对
- 需求理解偏了
- 用户可见行为不符合预期

如果你们不把 UAT 工程化，后续很容易变成“代码看起来对，但业务方总觉得不对”。

### 机制 7：多 runtime 支持不是复制 prompt，而是安装时转换

`bin/install.js` 是 GSD 里最能体现工程成熟度的部分之一。

它的核心思路不是维护多套源文件，而是：

- 以 Claude 风格格式为主源
- 安装时转换到不同 runtime

配套测试也能看到它认真处理了各种转换细节，比如：

- OpenCode 不支持 `model: inherit`
- Gemini 需要不同工具名映射
- 某些 frontmatter 字段要剔除
- 文本里对 `CLAUDE.md` 的引用要替换成宿主对应的指令文件

对团队而言，这个机制价值极大。

因为很多团队后面都会遇到：

- 一部分人用 Cursor
- 一部分人用 Claude Code
- 自动化任务又跑在 SDK 或其他 runtime 上

如果没有 runtime adapter 层，prompt 资产会很快裂成多份。

### 机制 8：安全不是一条文档，而是多层防御

GSD 在安全上做的事情比常见 Agent 项目要多。

从 README、`security.cjs` 相关测试、`gsd-prompt-guard.js`、`prompt-injection-scan.test.cjs` 看，它至少做了：

- 路径穿越防护
- prompt injection 检测
- prompt sanitization
- shell 参数校验
- JSON 安全解析
- 写入 `.planning/` 时的注入风险提醒
- 对 agent/workflow/command/hook 源文件做全仓扫描

尤其值得关注的是：它把“规划文档会成为未来 system prompt 的一部分”这件事，当作一等安全问题来处理。

这对团队极其重要。因为一旦你们把需求文本、用户描述、工单内容、外部文档纳入 planning artifacts，就已经进入间接 prompt injection 风险区间了。

### 机制 9：hooks 被用来增强运行时感知，而不是只做美化

`gsd-context-monitor.js` 很能体现 GSD 的设计味道。

它不是单纯做一个状态栏，而是：

- 通过 statusline bridge 读上下文使用率
- 在阈值下主动给 agent 注入 additionalContext
- 区分普通上下文和 GSD 激活状态
- 用 advisory 而不是硬阻断

类似地，`gsd-prompt-guard.js` 也不是简单静态扫描，而是在写 planning 文件前就发出风险提示。

这说明团队落地 harness 时，hooks 不应只被看作 UI embellishment，而要被看作：

- 运行时护栏
- 风险提示器
- 行为调节器
- 系统粘合层

### 机制 10：它已经开始从“命令系统”走向“程序化 SDK”

很多 Agent 框架只停留在命令层，但 GSD 还做了 `sdk/`。

这表示它不满足于“人在终端里手动用”，而是开始尝试让外部系统程序化调用它的 phase lifecycle。

从 `sdk/src/index.ts` 可以看到：

- 可以执行单个 plan
- 可以执行整 phase
- 可以执行整个 milestone
- 有事件流
- 有 prompt factory
- 有 context engine
- 有 phase runner

这对团队很有启发。

因为当 harness 逐渐成熟后，你们通常会想把它接到：

- CI
- 平台服务
- 自动调度
- 交付面板
- 内部运营系统

如果一开始只做“命令提示词集合”，后面演化到 SDK 会非常痛苦。GSD 至少已经验证了一条可行方向。

---

## 四、这套系统最值得学习的，不是命令本身，而是它的数据流设计

GSD 的很多强项，来自它把文件工件串成了一条稳定数据流。

### 1. 新项目流

大致可以概括成：

1. 用户描述目标
2. 深问补上下文
3. 并行 research
4. 生成 requirements
5. 生成 roadmap
6. 初始化状态

这一步完成后，系统不再依赖“用户最初那段自然语言”，而是依赖结构化工件。

### 2. 单 phase 交付流

标准路径是：

1. `discuss-phase` 生成 `CONTEXT.md`
2. `plan-phase` 生成 `RESEARCH.md` 和 `PLAN.md`
3. `execute-phase` 生成 `SUMMARY.md`
4. `verify-work` 生成 `UAT.md`
5. `ship` 把验证后的结果推向 PR 或发布阶段

这里有个非常关键的思想：

> 每一步都把“自由文本交流”沉淀成下游可消费的结构化文档。

这就是 harness engineering 的核心价值之一：**把会话知识变成系统知识**。

### 3. 调试与恢复流

GSD 还有一些容易被忽略、但团队很需要的恢复型能力：

- `pause-work`
- `resume-work`
- `forensics`
- `health --repair`
- `debug`
- `session-report`

这说明它不是只考虑 happy path，而是考虑了真实使用过程中的：

- 中断
- 状态漂移
- 失败归因
- 工件损坏
- 会话恢复

这对团队系统非常关键，因为真正的生产场景里，中断和失败远比“首次顺畅跑完”常见。

---

## 五、如果你要为团队搭 Harness Engineering，哪些部分最应该直接借鉴

下面按优先级来给。

### A 类：强烈建议直接借鉴

#### 1. 文件态项目记忆层

至少包含：

- 项目目标
- 需求边界
- 路线图
- 当前状态
- 分阶段工件目录

原因很简单：这是整套系统可恢复、可接力、可审计的基础。

#### 2. 薄 orchestrator + 专职 agent

原因：

- 更容易控上下文
- 更容易分配模型
- 更容易做权限最小化
- 更容易测试和替换

#### 3. phase / plan 两级结构

原因：

- phase 保证业务交付粒度
- plan 保证 Agent 单次上下文可执行粒度
- 这两层之间天然适合做验证与并行

#### 4. verify / UAT 闭环

原因：

- 能真正把“代码完成”变成“交付完成”
- 能把用户反馈结构化回流到系统

#### 5. runtime adapter 思维

即使你们第一版只支持一个宿主，也要把“未来可能支持多宿主”预留成架构层能力，而不是把所有宿主细节硬编码在 prompt 里。

#### 6. 安全扫描和 prompt injection 防护

这是团队系统必须补的基础设施，不要等出事再补。

### B 类：建议裁剪后借鉴

#### 1. 完整的命令矩阵

GSD 命令非常多，但团队起步不必全抄。

我建议第一批只保留：

- 初始化
- 规划
- 执行
- 验证
- 调试
- 发布

其他如 workstreams、milestone summary、user profiling 可以后加。

#### 2. workstreams / workspaces

这些能力说明 GSD 已经在处理并行大任务和隔离工作目录问题，方向是对的。

但如果团队当前还没到多并行工作流阶段，第一版可以先不引入。

#### 3. UI 相关的一整套能力

像：

- `ui-phase`
- `ui-review`
- `ui-auditor`

对偏前端团队很有价值；对后端或平台团队，优先级可以延后。

#### 4. 用户画像与个性化输出

`profile-user` 这类功能说明 GSD 开始把使用者偏好也纳入系统。

这对长期提升体验很有用，但不属于团队起步阶段最关键的核心骨架。

### C 类：更适合当理念参考，而不是直接照搬

#### 1. 产品化命名与话术风格

GSD 的品牌表达很强，这适合它作为开源产品传播。

但团队内建 harness 更重要的是：

- 清晰
- 稳定
- 易训练
- 易审计

没必要照抄它的风格人格。

#### 2. 面向多公开 runtime 的完整安装器复杂度

GSD 的安装器是开源分发产品所需，不一定是所有团队都需要的。

内部团队版可以先做：

- 单 runtime
- 固定目录布局
- 简化版 manifest
- 简化版 settings 集成

等体系稳定后再扩。

---

## 六、GSD 暴露出的隐含前提与潜在风险

如果你要参考它搭团队系统，不能只看优点，也要看它赖以成立的前提。

### 1. 它默认团队接受“Markdown 工件本身就是产品代码”

GSD 的很多能力都建立在一个文化前提上：

- planning artifacts 需要认真维护
- workflow 文档是工程资产
- agent 定义是工程资产
- hooks 与模板也要进审查和测试

如果团队只愿意维护业务代码，不愿意维护这些“控制面资产”，那就很难复制 GSD 的优势。

### 2. 它对纪律要求很高

GSD 的效果很大程度上来自：

- 按 phase 推进
- 不乱跳流程
- 按要求生成工件
- 接受验证与 UAT

如果团队成员习惯于“先让 Agent 自由写、后面再看”，那套纪律很容易被绕开。

### 3. 它的复杂度已经是系统级，而非 prompt 级

你从这些目录就能感受到复杂度：

- `commands/`
- `workflows/`
- `agents/`
- `hooks/`
- `bin/`
- `tests/`
- `sdk/`

这说明它适合当中长期演进的参考系统，但不适合“第一天就全量复制”。

### 4. 多 runtime 适配会把维护难度抬高很多

你们后续如果也要支持多个宿主，会面对：

- frontmatter 差异
- tool name 差异
- hook event 差异
- 指令文件名差异
- agent 调用方式差异

GSD 已经通过安装器和测试体系承接了这部分复杂度。团队落地时，一定要先问清楚：多宿主到底是不是第一阶段必须需求。

### 5. 文档与实现之间需要持续对齐，不然复杂系统会很快漂移

像 GSD 这种系统，一旦：

- workflow 更新了
- SDK 更新了
- hook 行为变了
- runtime converter 更新了

如果没有测试和一致性检查，就很容易出现“说明文档还是旧的、行为已经变了”的问题。

这也是它为什么有大量测试文件的原因。

---

## 七、从测试体系看，GSD 为什么更像一个工程系统

我认为很多团队最该学 GSD 的，不是命令设计，而是它对测试的态度。

### 1. 它在测试“框架行为”，不是只测函数

例如可以看到几类测试：

- `execute-phase-wave.test.cjs`
- `runtime-converters.test.cjs`
- `security.test.cjs`
- `prompt-injection-scan.test.cjs`
- `hook-validation.test.cjs`

这些测试验证的对象包括：

- workflow 是否声明了用户可见契约
- 不同 runtime 转换是否正确
- 安全模块是否真的拦住路径穿越和注入
- 代码库中会进入 agent 上下文的文本是否含可疑内容
- hook 配置是否满足宿主 schema

这说明它在测试“Agent 基础设施本身”，而不是仅测试业务逻辑。

### 2. 它已经把 prompt / workflow / hook 当成可测试对象

这是很多团队会忽略的点。

如果你后续搭团队 harness，一定要接受这个现实：

- prompt 不是不可测资产
- workflow 不是不可测资产
- hook 不是只靠人工点点看

否则系统复杂度一上来，回归风险会迅速失控。

### 3. 它把安全扫描纳入常规测试，而不是单独人工检查

`prompt-injection-scan.test.cjs` 的意义非常大，因为它把：

- agents
- commands
- workflows
- hooks
- lib 源码

都纳入扫描范围。

对团队来说，这个模式非常值得直接借鉴：

- 凡是最终会进入 agent context 的文件，都应该被纳入扫描边界
- 安全规则最好以测试形式固化，而不是靠经验提醒

---

## 八、GSD 对团队搭 Harness Engineering 的真正启发是什么

如果一定要把前面的分析收束成几条高价值原则，我会给下面八条。

### 原则 1：把“会话知识”外置成“系统工件”

这是 Harness 的地基。

### 原则 2：把“自由对话”收敛成“阶段工作流”

这是可管理性的来源。

### 原则 3：把“一个 Agent 干所有事”拆成“多角色编排”

这是可扩展性的来源。

### 原则 4：把“看起来做完了”替换成“被验证为做完了”

这是可信度的来源。

### 原则 5：把“宿主差异”下沉到适配层，而不是污染业务提示词

这是多平台可维护性的来源。

### 原则 6：把“安全问题”视为规划工件链路的一部分

这是 Agent 系统时代的新必修课。

### 原则 7：把“并行执行”设计成受控波次，而不是随手多开几个 agent

这是规模化执行的来源。

### 原则 8：把 Harness 本身纳入测试与发布纪律

这是长期演进的来源。

---

## 九、如果让我替团队做裁剪，我会怎么基于 GSD 搭第一版

下面是我认为最务实的一版落地方案。

### 第一阶段：先搭最小可用骨架

目标不是功能齐全，而是把基本工程形态立住。

建议第一版就有：

1. 一个团队统一的 harness 仓库
2. 一个固定的项目状态目录，例如 `.planning/` 或 `.agent/`
3. 4 个核心 workflow：
   - intake / clarify
   - plan
   - execute
   - verify
4. 3-5 个核心 agent：
   - researcher
   - planner
   - executor
   - verifier
   - debugger（可选）
5. 一个 `tools` CLI 层，负责 state/config/phase/verify 的读写

这个阶段不用急着做：

- 多 runtime
- workstreams
- 用户画像
- UI 审计
- 全量 SDK

### 第二阶段：把验证闭环和安全补齐

建议补：

- 计划检查
- 验证文件生成
- 对话式 UAT
- prompt injection 扫描
- path/shell/json 安全校验
- hooks 护栏

这个阶段完成后，你们的系统才算从“能跑”进入“更可信”。

### 第三阶段：把并行和隔离能力补齐

当团队开始希望提升吞吐时，再引入：

- wave 并行
- worktree/隔离目录
- 原子提交策略
- 并发状态写入保护
- 批量验证

### 第四阶段：再考虑多宿主与 SDK 化

当流程稳定后，再做：

- runtime adapter
- 安装器
- programmatic SDK
- CI 集成
- 面板化事件流

这个顺序会比直接照搬 GSD 全套更可控。

---

## 十、如果你要用这份分析来指导团队建设，我建议你们优先回答这 10 个问题

1. 你们最需要工程化的 3-5 个 Agent 工作流是什么？
2. 你们是否接受把 planning artifacts 当成正式工程资产？
3. 你们的长期状态是放在文件系统、数据库还是别的媒介？
4. 你们是否需要多 agent 并行？如果需要，依赖关系如何表达？
5. 你们的验证体系里，哪些必须自动化，哪些必须人工确认？
6. 你们是否会支持多个宿主/runtime？
7. 你们准备如何处理 prompt injection 和间接注入风险？
8. 你们是否需要 hooks 作为运行时护栏？
9. 你们希望 harness 最终只服务终端用户，还是还要程序化接入平台？
10. 你们能投入多少纪律来维护这套“控制面资产”？

如果这 10 个问题没有答清楚，直接“照着 GSD 做”大概率只会得到一个看起来很强、实际很重的系统。

---

## 十一、对这套框架的总评价

如果站在“指导团队搭建 harness engineering”的角度，我会这样评价 GSD。

### 它最强的地方

- 它把 Agent workflow 真正做成了一套工程系统，而不是一堆零散 prompt
- 它非常清楚地把状态、计划、执行、验证、恢复、发布串成了闭环
- 它已经认真处理多 runtime、hooks、安全和 SDK 这些“第二层难题”
- 它展示了 Agent 系统如何从个人效率工具演进成团队交付基础设施

### 它最值得警惕的地方

- 系统复杂度已经不低
- 需要团队认可大量 Markdown/配置/脚本资产的工程价值
- 对纪律要求高
- 多 runtime 与多能力叠加后维护成本明显上升

### 对你后续搭团队 Harness Engineering 的最大启示

`get-shit-done` 最值得学习的，不是“怎么让 Agent 一次输出更聪明”，而是：

> **怎么把 Agent 的工作过程拆成可编排、可恢复、可验证、可审计、可演进的工程系统。**

这才是它对团队真正有价值的部分。

---

## 十二、给你的直接行动建议

如果你接下来真要为团队搭 harness engineering，我建议按这个顺序推进：

### 第一批马上做

- 定义统一状态目录与核心工件
- 定义 4 个核心 workflow
- 定义 3-5 个核心 agent
- 做一个最小 `tools` CLI 层
- 给 plan / verify / UAT 建基础模板

### 第二批尽快补

- 计划检查
- gap 回流
- hooks 护栏
- 安全扫描
- 基础测试套件

### 第三批按需要扩

- wave 并行
- 隔离执行环境
- 多 runtime 适配
- SDK 化
- 运营/观测面板

如果你们按这个顺序做，就能吸收 GSD 最值钱的结构性能力，而不会一上来就把自己拖进过重系统。

---

## 最终一句话总结

GSD 不该被理解成“一个很会写代码的 Agent prompt 包”，而应该被理解成：

> 一套把 Agent 交付流程做成工程基础设施的参考实现。

对团队来说，最值得借鉴的不是它所有功能，而是它背后的工程结构：

- 阶段化
- 文件态状态
- 多角色编排
- 验证闭环
- 运行时护栏
- 多宿主适配
- 安全与测试内建

如果你后续按这个结构去搭自己的 harness engineering，你会更容易做出一套真正能在团队里持续运行的系统，而不是一堆短期好用、长期失控的 prompt。
