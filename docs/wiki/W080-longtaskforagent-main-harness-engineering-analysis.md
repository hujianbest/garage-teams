# W080: Longtaskforagent Harness Engineering Analysis

- Wiki ID: `W080`
- 状态: 参考
- 日期: 2026-04-11
- 定位: 记录外部项目、方法与设计资料的分析结果，提炼对 `Garage` 的结构启发；默认作为参考资料，不作为当前主线真相源。
- 关联文档:
  - `docs/README.md`
  - `docs/GARAGE.md`
  - `docs/ROADMAP.md`

这份报告不是为了介绍外部项目 `longtaskforagent-main` 有多少 skill，而是为了回答一个更实用的问题：

> 如果你的团队要把 Agent 从“单轮能写点代码”，提升到“能跨会话、可治理、可验证、可持续交付”，`longtaskforagent-main` 这套框架到底提供了哪些值得借鉴的工程机制？

说明：下面列出的路径均指被分析项目 `longtaskforagent-main` 内部的路径，不代表当前 `ahe` 仓库的目录结构。

这份分析聚焦它的实际源码与入口文件，尤其关注：

- `README.md`
- `CLAUDE.md`
- `hooks/hooks.json`
- `hooks/session-start`
- `skills/using-long-task/SKILL.md`
- `skills/using-long-task/references/architecture.md`
- `skills/long-task-init/scripts/init_project.py`
- `scripts/auto_loop.py`
- `.opencode/plugins/long-task.js`
- `.claude-plugin/plugin.json`

---

## 一、结论先行

如果把 `longtaskforagent-main` 压缩成一句话，它本质上不是一个“长 prompt”或“skill 合集”，而是一套把复杂软件任务拆成 **阶段化工作流 + 文件态状态机 + 质量门禁链 + 多会话恢复机制** 的 Agent harness。

它最有价值的地方，不是“让 Agent 更聪明”，而是通过明确的结构，把以下几件常见但容易失控的事情收束为可重复的工程动作：

1. **长任务如何跨会话延续**
2. **当前应该进入哪个阶段**
3. **阶段之间依赖什么工件**
4. **什么时候允许实现，什么时候必须回到上游**
5. **什么时候才算真的完成**
6. **如何让同一套流程在 Claude Code / OpenCode 这类宿主里复用**

从团队搭建 harness engineering 的角度看，`longtaskforagent-main` 最值得借鉴的是这五层结构：

1. **路由层**：会话启动即注入路由器 skill，先判断阶段，再决定行动
2. **工件层**：SRS / UCD / Design / ATS / feature-list / progress / release notes 承接长期状态
3. **执行层**：Init、Worker、Hotfix、Increment、System Test 这些技能分担不同职责
4. **门禁层**：TDD、覆盖率、变异测试、ATS 覆盖检查、系统测试 readiness 形成强约束
5. **自动化层**：hook 注入、脚手架脚本、验证脚本、auto loop 承担可机械化部分

如果你的团队后续要搭自己的 harness，最应该学的是这个“分层与边界”，而不是把它的全部技能与文档一比一搬过去。

---

## 二、这个框架到底解决了什么问题

`longtaskforagent-main` 的核心问题意识非常明确：**复杂任务无法安全地依赖单个上下文窗口完成**。

典型失败模式包括：

- 会话一旦 `/clear`，模型丢失项目状态
- 模型在需求不清楚时直接写代码
- 模型跳过测试或只写表面测试
- UI / API / NFR 验证在项目后期才临时补
- 需求增量或缺陷修复没有被纳入受控流程

它给出的答案不是“继续堆提示词”，而是：

### 1. 用阶段化流程替代自由漫游

主线被拆成：

- Requirements
- UCD
- Design
- ATS
- Init
- Worker
- System Testing
- Finalize

并补充两条支线：

- Hotfix
- Increment

### 2. 用磁盘工件替代对话记忆

这套系统不假设模型记得上一轮做了什么，而是假设：

- 状态必须落文件
- 文件既给人看，也给 Agent 读
- 后续阶段只能消费已存在、可审计的工件

### 3. 用强门禁替代“建议遵守”

框架中很多约束并不是“推荐”，而是明确写成：

- 没有批准 SRS 不许设计
- 没有设计不许 ATS / Init / 编码
- 没有质量证据不许把 feature 标成 passing
- 所有 active feature passing 之前不能进入 ST

这正是 harness engineering 与普通 prompt engineering 的分水岭。

---

## 三、整体架构：它是如何运转起来的

从源码看，`longtaskforagent-main` 可以拆成六个核心子系统。

## 1. Bootstrap 路由系统：每次会话先注入规则，再决定阶段

这是整套系统最关键的入口。

### 入口文件

- `hooks/hooks.json`
- `hooks/session-start`
- `skills/using-long-task/SKILL.md`

### 工作方式

Claude Code 侧的 `SessionStart` hook 会在 `startup|resume|clear|compact` 这些事件上执行 `hooks/session-start`。这个脚本会做三件大事：

1. 读取 `skills/using-long-task/SKILL.md`
2. 检测当前项目处于哪个阶段
3. 把 skill 正文和阶段提示一起注入到 session context

也就是说，这套框架不是“用户自己记得该用哪个 skill”，而是通过 hook 强行把路由器放进每个会话的最前面。

### 为什么这点非常重要

团队里的 Agent 系统一旦没有统一入口，就很容易出现：

- 有人从需求开始走流程
- 有人直接跳到实现
- 有人遇到 bug 直接手修
- 有人把增量需求直接改 `feature-list.json`

`longtaskforagent` 的做法是：**所有工作先路由，再执行**。
这比“约定大家自觉使用某个 skill”更可靠，因为它已经进入了运行时。

### 一个值得注意的细节

路由规则在 `skills/using-long-task/SKILL.md` 里最完整，包括：

- `bugfix-request.json`
- `increment-request.json`
- `feature-list.json`
- `docs/plans/*-ats.md`
- `docs/plans/*-design.md`
- `docs/plans/*-ucd.md`
- `docs/plans/*-srs.md`

而 `hooks/session-start` 里的 `status_hint` 检测逻辑是更轻量的提示版。它覆盖了增量、feature-list、ATS、design、UCD、SRS，但没有把 `bugfix-request.json` 纳入状态提示文案。

这说明它的实际设计是：

- **hook 负责快速提示与注入**
- **完整阶段裁决以路由 skill 本身为准**

对团队落地的启发是：
**“运行时提示”和“真正的状态机规则”可以分层，但一定要明确谁才是最终真相源。**

---

## 2. 技能系统：不是一个万能 Agent，而是一组阶段技能

框架通过 `Skill` 工具按需加载技能，而不是把所有规则都塞进一个超长 system prompt。

### 技能分层

#### Phase skills

- `using-long-task`
- `long-task-requirements`
- `long-task-ucd`
- `long-task-design`
- `long-task-ats`
- `long-task-init`
- `long-task-work`
- `long-task-st`
- `long-task-hotfix`
- `long-task-increment`

#### Discipline skills

- `long-task-feature-design`
- `long-task-tdd`
- `long-task-quality`
- `long-task-feature-st`

#### Meta skills

- `long-task-finalize`
- `long-task-retrospective`

### 这套设计代表什么

它代表一种非常成熟的 harness 思路：

- **路由职责** 和 **执行职责** 分离
- **阶段技能** 和 **纪律技能** 分离
- **交付技能** 和 **收尾/自进化技能** 分离

这比“一个 agent 同时负责需求、设计、编码、测试、发布”的方案稳定得多，因为：

1. 每个 skill 只关心一个上下文范围
2. 技能可以独立演化
3. 失败时更容易定位问题出在什么阶段
4. 后续要裁剪流程时可以按 skill 维度拆装

对团队来说，这非常值得直接借鉴。第一版不一定要有这么多 skill，但至少要把：

- 路由
- 上游工件生成
- 实现
- 验证
- 变更/热修

这些角色拆开。

---

## 3. 工件系统：把项目状态外置成 inspectable artifacts

这是 `longtaskforagent-main` 最“harness engineering”的部分。

它依赖的不是一个数据库，也不是隐藏状态，而是一套可读、可改、可追踪的文件工件。

### 核心工件

#### 上游规划工件

- `docs/plans/*-srs.md`
- `docs/plans/*-ucd.md`
- `docs/plans/*-design.md`
- `docs/plans/*-ats.md`

#### 中间状态工件

- `feature-list.json`
- `task-progress.md`
- `long-task-guide.md`
- `CLAUDE.md`
- `AGENTS.md`
- `RELEASE_NOTES.md`

#### 下游验证与交付工件

- `docs/features/*.md`
- `docs/test-cases/feature-*.md`
- `docs/plans/*-st-plan.md`
- `docs/plans/*-st-report.md`
- `examples/`

#### 信号文件

- `increment-request.json`
- `bugfix-request.json`

### 为什么这套文件结构重要

很多团队做 Agent 工作流时，只会关注 prompt 和工具，却忽略“状态到底放在哪里”。

`longtaskforagent` 的答案非常清楚：

- **结构化状态** 放 JSON
- **叙事与审批上下文** 放 Markdown
- **短期触发信号** 放独立 signal file
- **交付与使用说明** 放 examples / release notes

特别值得注意的是 `feature-list.json`。

它不是简单待办列表，而是整个系统的共享状态中心，包含：

- project 元信息
- tech stack
- quality gates
- constraints / assumptions
- required configs
- waves
- features 列表
- 每个 feature 的状态、追溯关系、依赖、UI 标记、ST case 信息

这让它既是：

- Worker 的任务来源
- ST readiness 的判断依据
- ATS coverage 的检查对象
- 增量和热修流程的回写目标

对团队落地而言，一个非常直接的结论是：

> **不要把长期状态只放在 issue、聊天记录或临时 TODO 里。至少要有一个 Agent 可读写、又适合人类审计的项目状态文件。**

---

## 4. Init 脚手架：把通用控制面先确定下来

`skills/long-task-init/scripts/init_project.py` 是这套框架里最容易被低估，但其实非常关键的文件。

它负责生成一组**确定性的基础骨架**，包括：

- `feature-list.json`
- `task-progress.md`
- `RELEASE_NOTES.md`
- `CLAUDE.md`
- `AGENTS.md`
- `examples/README.md`
- `scripts/` 辅助脚本
- `docs/plans/`
- `docs/test-cases/`
- `docs/templates/`

同时它明确区分出两类资产：

### 脚本生成的资产

适合确定性脚手架生成：

- 文件结构
- 基础模板
- 工具脚本复制
- 初始 schema

### LLM 生成的资产

必须按项目上下文定制：

- `long-task-guide.md`
- `init.sh` / `init.ps1`
- feature 内容
- constraints / assumptions / required_configs 的具体值

### 这背后的设计思想

这说明作者已经清楚地区分：

- 什么适合“程序生成”
- 什么适合“模型生成”

这是团队搭 harness 时必须掌握的一条边界。

如果不做这层区分，常见问题会是：

- 明明是固定结构，却每次都让模型重新写，导致漂移
- 明明高度依赖项目上下文，却想用通用模板硬套，结果失真

对团队来说，脚手架层至少应该把以下事情固定下来：

1. 状态文件格式
2. 目录结构
3. 验证脚本入口
4. 约束文档落点
5. 初始化最小工件集合

这样后面的模型输出才有稳定“容器”可落。

---

## 5. 质量门禁链：这是它区别于普通 long-task prompt 的核心

`longtaskforagent-main` 最强的地方，不是阶段多，而是它把验证做成了一个完整链条。

### Worker 内的强制顺序

从文档与架构说明看，Worker 不是“选一个 feature 然后写代码”，而是：

1. Orient
2. Bootstrap
3. Config Gate
4. DevTools Gate
5. Feature Detailed Design
6. TDD Red
7. TDD Green
8. Coverage Gate
9. TDD Refactor
10. Mutation Gate
11. Feature ST
12. Inline Compliance Check
13. Persist

这里特别要强调：第 5 步不是泛泛的“计划一下”，而是由 `long-task-feature-design` 这个 discipline skill 先产出 feature 级详细设计工件，通常落到 `docs/features/*.md`。后续的 TDD、Feature ST、Inline Compliance Check 都会消费这个工件，所以它不是可有可无的附属步骤，而是 Worker 内部把“系统级设计”桥接到“单 feature 实现”的关键控制点。

### 它解决了什么问题

这条链条解决的是传统 Agent 编码里最常见的四类失控：

#### 1. 没有真实失败测试就开始实现

通过 `long-task-tdd` 强制 Red → Green → Refactor。

#### 2. 测试看起来很多，但其实没测到关键逻辑

通过 Coverage Gate + Mutation Gate 双门禁提升测试有效性。

#### 3. UI 功能只跑单测，不做真实界面验证

通过 `ui: true` 标记和 Chrome DevTools MCP 测试把 UI 变成显式要求。

#### 4. 标记 passing 靠主观判断

通过“fresh verification evidence”原则禁止“应该可以”“大概没问题”。

### 这对团队为什么关键

如果你的团队要做 harness engineering，必须接受一个现实：

> Agent 的最大风险不是“不会生成代码”，而是“会生成看起来像完成、但证据不足的结果”。

因此，团队版 harness 至少要把以下三种门禁变成明确动作：

1. **实现前门禁**：需求、设计、配置是否齐备
2. **实现中门禁**：测试先行、覆盖率、关键断言质量
3. **实现后门禁**：系统级验证、交付文档、完成定义

`longtaskforagent` 在这三层上都给出了很强的参考样板。

---

## 6. ATS：把验收测试策略前移，而不是等写完再补 QA

这是该框架相对很多同类方案最突出的一个特征。

它不是等代码写完之后才思考怎么验收，而是在 Design 之后单独引入一个 ATS 阶段：

- 将 FR/NFR/IFR 映射到验收场景
- 标注测试类别：FUNC / BNDRY / SEC / UI / PERF
- 提前规划跨功能集成场景
- 用独立 reviewer subagent 审核 ATS

### 为什么 ATS 很重要

这一步把“测试”从实现末端拉到了规划中段，带来几个直接收益：

1. 需求一开始就有测试视角，不容易遗漏边界与 NFR
2. Init 可以根据 `srs_trace` 和 ATS 类别给 feature 打 `ui` 等标记
3. feature-level ST 和 system-level ST 都有可追溯的上游依据
4. ST 不再是“手工想几个场景试一下”，而是被测试策略约束

### 团队落地时是否必须照搬 ATS？

不一定。

但它至少提醒团队要正视一个问题：

> 如果测试策略没有在实现前成型，那么后面的 QA、回归和验收很容易变成补洞式行为。

对大多数团队，一个裁剪版 ATS 也很有价值，哪怕只先覆盖：

- 关键 FR
- 关键 NFR
- 高风险场景
- UI / SEC / PERF 分类

---

## 四、运行时与宿主适配：核心框架和宿主 glue 要分开看

这个仓库并不只是 Claude Code skill 包，它还显式提供了多宿主适配。

### Claude Code 侧

- `.claude-plugin/plugin.json`
- `hooks/hooks.json`
- `hooks/session-start`

Claude 侧的强项是：

- 原生 SessionStart hook
- 通过 hook 注入完整 bootstrap 内容
- 可在会话启动时做状态提示和脚本复制

### OpenCode 侧

- `.opencode/plugins/long-task.js`

OpenCode 插件做了几件事：

- 将 `using-long-task` 内容注入 system prompt transform
- 在目标项目里复制 `init_project.py`
- 自动补充 chrome devtools MCP 配置
- 通过 signal file 处理 AskUserQuestion / 交互暂停

不过这里要明确区分**宿主提示层**与**真实路由层**。OpenCode 插件里的 `detectPhase()` 只是 hint 级实现，它并没有完整覆盖 Claude 侧和 `using-long-task` 路由 skill 中的全部判定条件，例如没有单独检测 `bugfix-request.json`，也没有把 `*-ats.md` 作为独立阶段节点；它甚至会把 `*-design.md` 直接提示成 Initializer。真正的 canonical truth 仍然是注入到上下文中的 `using-long-task` skill，而不是各宿主本地的 phase hint。

### 这里最值得团队学习的是什么

不是“支持多个宿主”这件事本身，而是它们的分层方式：

#### 核心层

- skills
- scripts
- artifacts schema
- workflow 规则

#### 适配层

- hook 机制
- prompt 注入方式
- AskUserQuestion 捕捉方式
- MCP 配置写入方式
- 技能发现路径

### 为什么这点重要

很多团队做内部 harness 时，会把宿主细节写死进技能或文档里。
一旦迁移宿主，就会发现：

- tool 名不一样
- hook 能力不一样
- 会话启动注入点不一样
- 技能加载方式不一样

`longtaskforagent-main` 提供的启发是：

> **要把“工作流逻辑”与“宿主接入方式”分开建模。**

不过它也暴露出一个现实问题：
不同宿主实现不可能完全 1:1 对齐。

例如 OpenCode 插件里的阶段检测顺序和 Claude hook 的实现细节并不完全一致，而且这种差异不只是代码风格不同，而是会导致阶段提示能力存在缺口。
这提醒团队一件事：

> **多宿主支持是架构问题，不是简单复制一份 prompt。**

### 另一个很容易被忽略的点：bootstrap 并非纯只读

这套框架的接入层不是只负责“注入一段 prompt”。它在会话开始时还可能做运行时写操作：

- Claude hook 会尝试渲染 `.long-task-bindings/`
- Claude hook 会复制 `scripts/init_project.py`，并写入 `scripts/.long-task-plugin-root`
- OpenCode 插件会复制 `init_project.py`
- OpenCode 插件还会 upsert 用户全局 `~/.config/opencode/opencode.json` 里的 chrome devtools MCP 配置

这意味着它不是一个完全无副作用的 skill 包，而是一个会主动塑造项目控制面的运行时系统。团队如果要借鉴这套方案，必须明确：

1. 哪些副作用允许发生在项目目录
2. 哪些副作用允许发生在用户全局配置
3. 这些副作用如何审计、回滚和与现有开发环境共存

---

## 五、auto_loop：它把“多会话连续推进”显式程序化了

`scripts/auto_loop.py` 是另一个非常具有 harness 特征的组件。

它的作用不是生成业务代码，而是把“多轮会话反复推进直到所有 feature passing”这件事，做成一个外部控制循环。

### 它提供了什么能力

- 每轮 fresh context
- 自动迭代直到所有 active feature passing
- AskUserQuestion 检测并暂停
- 错误模式检测（context / token / rate limit / overloaded）
- graceful interrupt 与 force kill
- session log 自动写入
- 运行成本累计

### 这反映了什么设计思想

它说明作者并不把 Claude 会话看作唯一执行环境，而是把会话当作**可被外部脚本调度的工作单元**。

这对团队很有启发，因为很多长任务真正需要的是：

- 能中断
- 能恢复
- 能批量推进
- 能观察每一轮状态
- 能在用户介入时暂停

如果未来你的团队也想做：

- nightly 自动推进
- 批量 feature 执行
- 受控循环式 agent work
- 自动回收 session log

那么类似 `auto_loop.py` 这样的控制器非常值得早一点建设。

### 它不是工作流本身，而是工作流调度器

这层区分也很重要：

- workflow 决定“本轮应该做什么”
- auto loop 决定“要不要继续下一轮”

团队自建时也建议保留这层分工，不要把循环控制硬塞进每个 skill 里。

---

## 六、这个框架最值得借鉴的 10 个 Harness 机制

下面这部分是最适合团队直接拿来做设计输入的。

## 1. 会话开始即注入路由器

价值：

- 防止阶段漂移
- 保证所有任务从统一入口进入
- 降低“用户说继续，Agent 就开始乱做”的概率

## 2. 文件态状态机

价值：

- 可审计
- 可恢复
- 可 diff
- 不依赖上下文记忆

## 3. JSON + Markdown 双工件策略

价值：

- JSON 适合结构化状态和脚本检查
- Markdown 适合审批、设计、叙事和人机共读

## 4. 上游工件先行

价值：

- 把 WHAT / LOOK / HOW / TEST STRATEGY 分离
- 降低编码阶段返工

## 5. Worker 与纪律技能分离

价值：

- 实现流程更清晰
- TDD / quality / feature ST 可独立演进

## 6. 验收测试策略前移

价值：

- 测试不是末端补洞
- traceability 更自然

## 7. 热修复与增量作为受控支线

价值：

- 避免团队绕过主流程
- 让 bugfix / change request 也能被追踪

## 8. 外部 auto loop 控制 fresh context

价值：

- 长任务不再依赖单个超长会话
- 便于暂停、重启、日志归档

## 9. 宿主适配层显式存在

价值：

- 让跨 Claude / OpenCode 的迁移有边界
- 降低 workflow 逻辑被宿主细节污染

## 10. 脚本化验证而不是纯口头规范

价值：

- `validate_features.py`
- `check_configs.py`
- `check_devtools.py`
- `validate_ats.py`
- `check_ats_coverage.py`
- `check_st_readiness.py`
- `check_real_tests.py`

这些脚本共同说明一个原则：

> **凡是可以机械判断的事情，就不要只写在 prompt 里。**

---

## 七、哪些地方值得借鉴，哪些地方不要直接照搬

## 强烈建议借鉴的部分

### 1. 路由器 + 阶段 skill 的分层

适合大多数团队直接采用。

### 2. 工件驱动的状态管理

至少要有一个稳定状态文件和一组上游工件落点。

### 3. 质量门禁链

尤其是测试前置和完成必须绑定验证证据。

### 4. Hotfix / Increment 的独立支线

非常适合真实团队工作流。

### 5. 外部循环控制器

只要你们有跨会话长任务需求，这层都很值。

## 需要裁剪后借鉴的部分

### 1. 完整的八阶段主线

对很多团队来说过重。第一版可以裁剪成：

- intake / requirements
- design
- implement
- verify
- release

### 2. ATS 的完整形态

对高复杂度产品很有价值；对中小项目可以先做轻量版本。

### 3. UCD 阶段

对 UI 产品重要，对纯后端或平台类项目可以先跳过。

### 4. 变异测试强门禁

价值很高，但成本也高。第一版可以先从关键模块或周期性运行开始。

## 不建议直接照搬的部分

### 1. 它的全部 skill 数量

对于起步团队会过重。

### 2. 完整的标准名词体系

如 ISO/IEEE 术语与完整模板，可以吸收思想，不必全部原样继承。

### 3. 多宿主一次性全支持

建议先把主宿主做稳，再做适配层扩展。

### 4. 所有质量门禁一次到位

应按团队成本承受能力逐步引入。

一句话总结就是：

> **先学它的结构，不要先学它的规模。**

---

## 八、从团队视角看，它的成本和限制是什么

如果要把这套方案作为团队参考，必须同时看到它的代价。

## 1. 流程强度高

这套方案本质上偏“重流程”。
对新功能、复杂项目很合适；对微小改动可能显得笨重。

## 2. 需要团队接受“文档即工程资产”

如果团队不愿意维护：

- SRS
- design
- ATS
- progress
- release notes

那很难真正发挥它的优势。

## 3. 要求较强的纪律性

因为它不是“建议”，而是很多地方明确要求：

- 先走哪一步
- 不能跳过哪一步
- 哪个工件缺失就必须回退

这需要团队文化配合。

## 4. 宿主适配存在漂移风险

一旦支持多个宿主，就必须处理：

- hook 差异
- tool 映射差异
- 技能加载差异
- 状态提示差异

这会引入维护成本。

## 5. bootstrap 具有写副作用，不是纯注入层

这套框架在 session start 或宿主初始化时会主动：

- 复制项目脚本
- 生成或刷新 `.long-task-bindings/`
- 写入 plugin-root hint
- 在 OpenCode 下修改全局 MCP 配置

这对团队是一个非常现实的限制，因为它意味着 harness 接入不仅仅是“加一份文档”，还涉及：

- worktree 可能变脏
- 用户环境可能被改写
- 会话启动逻辑本身需要版本治理

如果团队内部对“运行时是否允许自动改项目目录 / 全局配置”没有共识，这套模式需要先做裁剪。

## 6. 它对目标项目的运行时契约有明显要求

框架并不是只依赖上游文档工件，还要求目标项目暴露出足够稳定的运行时控制接口，例如：

- 服务启停命令应记录在 `env-guide.md`
- 测试周期之间要遵守 restart protocol
- 服务启动输出需要打印 port / PID / ready signal

这说明它的 harness 设计并不只是 prompt + state file，而是默认项目本身也愿意配合暴露一层“可自动化运维接口”。对已有团队项目来说，这可能意味着需要额外改造启动脚本、日志格式和环境指南。

## 7. 自动化脚本主要保护控制面，不等于端到端替代

它的 pytest 测试和校验脚本主要覆盖的是：

- schema
- 脚手架
- 配置
- readiness
- 覆盖检查

它们并不能完全替代真实项目里的完整业务级集成测试。

这提醒团队不要误以为“有了 harness 测试，就不需要业务测试”。

---

## 九、如果用它来指导团队搭建 Harness Engineering，我建议的落地路线

下面是一条比“直接复刻 longtaskforagent”更现实的路线。

## 阶段 1：先建立最小状态骨架

目标：

- 不依赖会话记忆

建议产物：

- 一个统一入口文件（如 `AGENTS.md`）
- 一个状态文件（类似 `feature-list.json`）
- 一个进度日志（类似 `task-progress.md`）
- 一个最小 release notes

成功标志：

- 任意人/任意会话都能从文件恢复当前状态

## 阶段 2：把任务拆成阶段而不是一步到位

目标：

- 让 Agent 有明确的进入顺序

建议阶段：

- requirements
- design
- implement
- verify
- release

成功标志：

- 团队能说清楚“每一阶段的输入、输出和进入条件”

## 阶段 3：补上最关键的门禁

目标：

- 防止“看起来完成”

优先门禁：

- 配置检查
- 测试前置
- 最小 coverage
- 完成必须有 fresh evidence

成功标志：

- Agent 不再仅靠主观判断宣称完成

## 阶段 4：引入支线流程

目标：

- 处理真实项目中的 bugfix 与 change request

建议：

- 单独定义 hotfix
- 单独定义 increment / change flow

成功标志：

- 团队不再通过直接改状态文件或直接修代码来绕开流程

## 阶段 5：把多会话调度程序化

目标：

- 让长任务可以自动推进和暂停恢复

建议：

- 做一个 loop controller
- 自动记录日志
- 支持用户介入暂停

成功标志：

- 长任务不再依赖人工不断重复“继续”

## 阶段 6：按需扩展宿主适配与高级验证

目标：

- 从单宿主内部工具升级为团队平台能力

可选扩展：

- 多宿主适配
- ATS
- 系统测试计划
- mutation gate
- retrospective / self-evolution

成功标志：

- harness 具备平台化演进空间，而不是只能服务单一工具

---

## 十、给团队的直接实施清单

如果你要正式据此搭团队版 harness，我建议先回答这 10 个问题：

1. 你们准备把长期状态放在哪个文件里？
2. 你们的最小阶段集合是什么？
3. 你们的“完成定义”需要哪些验证证据？
4. 哪类任务必须回到 requirements / design，而不能直接实现？
5. bugfix 和需求增量是否要走独立支线？
6. 哪些规则适合脚本检查，哪些规则只能人工判断？
7. 你们是否真的需要 ATS，还是先做轻量测试策略即可？
8. 当前主宿主是什么，是否真的需要同时支持多个宿主？
9. 是否要支持外部 loop controller 来跑长任务？
10. 团队是否愿意把这些控制面资产当正式工程资产维护？

如果这些问题没有回答清楚，直接照着 `longtaskforagent-main` 复刻，最后大概率会得到一个“看起来完整、实际难以落地”的系统。

---

## 十一、最终判断

站在“指导团队后续搭建 harness engineering”的角度，我对 `longtaskforagent-main` 的最终判断是：

### 它最强的地方

- 把长任务的跨会话问题工程化了
- 把阶段路由做成了运行时前置动作
- 把状态、规划、执行、验证串成了文件驱动的闭环
- 把质量门禁前置到了实现流内部
- 把热修和增量纳入了同一套受控工作流

### 它最值得警惕的地方

- 流程偏重
- 对文档资产依赖高
- 对团队纪律要求高
- 多宿主支持会带来一致性维护成本

### 对团队最重要的启示

`longtaskforagent-main` 最值得学习的，不是“怎么写一套更长的技能”，而是：

> **怎么把 Agent 的长期工作拆成可路由、可恢复、可验证、可追溯、可扩展的工程系统。**

如果你后续为团队搭 harness engineering，我建议优先继承它的四个核心原则：

1. **先路由，再行动**
2. **先工件，再状态推进**
3. **先证据，再宣称完成**
4. **先把控制面工程化，再追求更多智能化**

---

## 最终一句话总结

`longtaskforagent-main` 不是一个“让模型在单轮里做更多事”的提示工程项目，而是一套示范：**如何用路由、工件、门禁、脚本和外部循环，把 Agent 交付过程升级为团队可持续运行的 Harness Engineering 系统。**
