# superpowers-main 源码分析报告：面向团队搭建 Harness Engineering 的落地参考

这份报告的目标不是简单介绍 `references/superpowers-main/` 有哪些技能，而是回答一个更实际的问题：

**如果你的团队要把 Agent 使用方式工程化，如何从 `superpowers-main` 里提炼出一套可复用、可迁移、可验证、可演进的 harness engineering 骨架。**

---

## 一、结论先行

如果把 `superpowers-main` 简化成一句话，它本质上不是一个“提示词仓库”，而是一套围绕 coding agent 的 **workflow harness**：

- 用 `skills/` 定义主工作流与关键工程纪律
- 用 `hooks/` 在会话启动时把 workflow bootstrap 注入上下文
- 用平台适配层把同一套技能分发到 Claude Code、Cursor、Codex、OpenCode、Gemini
- 用 `tests/` 验证“技能系统本身”是否真的会被触发、遵循并在真实会话中工作
- 用 `docs/specs` 与 `docs/plans` 把框架自己的演进也纳入工程化管理

对团队建设 harness engineering 来说，它最值得借鉴的不是“技能数量”，而是它把 Agent 工程拆成了 5 个清晰层次：

1. **引导层**：统一 bootstrap，让 agent 先学会“如何使用技能”
2. **流程层**：用技能串起从设计、计划、实现、评审到收尾的开发闭环
3. **适配层**：针对不同宿主做薄适配，而不是复制整套资产
4. **验证层**：对技能触发、工具调用顺序、端到端行为做专项测试
5. **演进层**：用 specs、plans 和元技能持续改进框架本身

如果你的团队后续要搭 harness，最应该复用的是这五层分治结构，而不是照搬它全部目录和全部技能。

---

## 二、分析范围与方法

本报告基于对 `references/superpowers-main/` 的源码级阅读，重点关注以下资产：

- 根入口：`README.md`、`package.json`
- 平台适配：`.cursor-plugin/`、`.claude-plugin/`、`.opencode/`、`.codex/`、`gemini-extension.json`
- 引导与 hooks：`hooks/session-start`
- 主技能：`skills/*/SKILL.md`
- 验证体系：`tests/skill-triggering/`、`tests/explicit-skill-requests/`、`tests/claude-code/`、`tests/opencode/`、`tests/brainstorm-server/`
- 设计与计划资产：`docs/plans/`、`docs/superpowers/specs/`、`docs/superpowers/plans/`

分析重点不是穷举所有文件，而是抽取对团队工程化最重要的设计模式、约束方式和实施启发。

---

## 三、这套框架到底是什么

从根 README 可以看出，`superpowers-main` 把自己定义成一套 **完整的软件开发工作流**，并且强调它不是“建议型技巧”，而是会在合适时机自动激活的流程系统。

它的目标很明确：

- 在写代码前，先做问题澄清与设计
- 设计确认后，再形成实现计划
- 实现阶段强调 TDD、review 和验证
- 更复杂的计划执行通过 subagent 进行任务级隔离
- 最后通过分支收尾流程来关闭一次开发循环

也就是说，这个仓库试图解决的不是“模型怎么更聪明”，而是：

1. 如何让 agent **按工程流程工作**
2. 如何让这套流程 **跨宿主分发**
3. 如何让这套流程 **被测试和验证**

这正是团队搭 harness engineering 时最需要的三件事。

---

## 四、源码架构拆解：superpowers 的 8 个关键子系统

### 1. `using-superpowers`：先教 agent“怎么用技能”

这套框架最关键的设计，不是某个具体实现技能，而是 `skills/using-superpowers/SKILL.md`。

它承担的是元引导职责：

- 要求在任何响应或行动前先检查技能是否适用
- 明确技能与用户指令、系统默认指令之间的优先级
- 规定多技能同时适用时的优先顺序
- 强制 agent 先学会“先找流程、再行动”

这意味着 `superpowers-main` 的核心不是“技能内容本身”，而是先建立一个 **技能驱动的执行纪律**。

对团队的启发很大：

- 团队 harness 不能只有很多 skill，还要有一个 **bootstrap skill / bootstrap contract**
- bootstrap 的职责不是解决业务问题，而是统一 agent 的工作方法
- 如果没有这一层，后续 skill、command、hook 的一致性都会变差

### 2. `hooks/session-start`：把 workflow bootstrap 自动注入会话

`hooks/session-start` 是整个仓库最工程化的文件之一。

它做了三件重要的事：

1. 读取 `using-superpowers` 的完整内容
2. 把内容序列化成会话上下文
3. 根据当前宿主输出不同的 hook 字段，分别兼容 Cursor 与 Claude Code

这说明作者并不依赖“用户自己记得先加载技能”，而是把最关键的引导逻辑推到 **会话启动阶段自动完成**。

团队落地时，这个模式非常值得直接借鉴：

- 对 agent 行为影响最大的“总则”，应在 session start 注入
- 不同宿主的 hook 字段、注入方式可能不同，必须显式适配
- 真正关键的 bootstrap，不应依赖人工口头约定

### 3. `skills/`：用技能描述一条完整开发主流程

`superpowers-main` 的技能库并不是杂乱知识集合，而是围绕一个主开发闭环来组织。

根 README 里的主流程是：

1. `brainstorming`
2. `using-git-worktrees`
3. `writing-plans`
4. `subagent-driven-development` 或 `executing-plans`
5. `test-driven-development`
6. `requesting-code-review`
7. `finishing-a-development-branch`

再加上按需介入的：

- `systematic-debugging`
- `verification-before-completion`
- `receiving-code-review`
- `dispatching-parallel-agents`

这个设计值得注意的点是：它不是把每个 skill 都设计成平权的工具箱，而是明确形成 **主路径 + 辅路径**。

对团队来说，这一点很重要：

- skill 体系最好围绕几个稳定主流程组织
- 调试、并行执行、验收这些应作为分支流程存在
- 一套 harness 最先应该定义的是“默认开发路径”，而不是尽可能多的技能目录

### 4. `subagent-driven-development`：把计划执行变成受控流水线

`subagent-driven-development` 是这个框架里最有代表性的执行型技能。

它不是简单地说“用子代理去做任务”，而是把子代理工作流拆成严格步骤：

- 读取 plan，一次性抽取任务全文
- 为每个任务派发新的 implementer subagent
- implementer 完成后先自审
- 然后进入 spec review
- spec review 通过后，再进入 code quality review
- 评审不通过必须回到 implementer 修复并重新 review
- 全部任务完成后再做最终代码审查和分支收尾

这套机制的本质是：把“多 agent 协作”从经验做法升级成 **带质量门的流水线**。

对团队最值得借鉴的点：

- 子代理不该只被当作“并发执行器”，更应该是“任务隔离器”
- 实现、spec 校验、质量 review 最好是不同角色
- review 顺序应显式规定，而不是随缘发生
- 对计划执行，controller 应给子代理完整任务文本，而不是让它自己再去读一堆文件

### 5. 跨宿主适配层：一套技能，多种分发方式

这个仓库非常适合用来理解“同一套 harness 如何跨宿主存在”。

它的做法不是给每个平台重写一套技能，而是：

- Claude Code / Cursor：走插件与 hook 机制
- Codex：通过 clone + symlink / junction 暴露 skills 目录
- OpenCode：通过运行时插件注册 skills 路径，并用 system transform 注入 bootstrap
- Gemini：通过扩展元数据与文档接入

这一点说明它真正采取的是：

- **共享核心层**：`skills/`、部分 docs、bootstrap 逻辑
- **平台适配层**：插件 manifest、hook 输出、工具映射、安装说明

这正是团队搭建 harness engineering 时最该学习的跨平台策略：

- 不要把宿主差异藏在隐式约定里
- 把可共享的资产尽量稳定下来
- 把差异显式放到 adapter / install / docs 层

### 6. 少量运行时代码：只为平台适配和可视化补充，不让代码吞掉框架主体

从 `package.json` 和目录结构看，仓库并不是一个大型应用，它的“运行时代码”非常克制，主要集中在：

- `.opencode/plugins/superpowers.js`
- `hooks/session-start`
- `hooks/run-hook.cmd`
- `skills/brainstorming/scripts/*`
- `tests/*`

这里体现了一个成熟的判断：

- 绝大多数流程知识用 Markdown skill 保持可读性
- 只有当需要宿主集成、会话注入、本地服务、文件监听等能力时，才落成脚本

这对团队很重要，因为很多团队会走向两个极端：

- 要么一切都写在 prompt 里，导致不可测试
- 要么过早写大量平台代码，导致维护成本过高

`superpowers-main` 提供了一个更平衡的做法：**知识优先文档化，能力边界才代码化。**

### 7. `tests/`：测试的不只是功能，而是“技能系统本身”

这个仓库很值得学习的一点，是它把测试重心放在“技能框架本身是否按预期工作”。

不同测试目录职责很清晰：

- `tests/skill-triggering/`：测试自然语言请求是否触发正确 skill
- `tests/explicit-skill-requests/`：测试用户明确点名 skill 时是否真的先调用 Skill 工具
- `tests/claude-code/`：测试 Claude Code CLI 下技能说明、顺序与集成行为
- `tests/opencode/`：测试 OpenCode 插件加载、工具映射与优先级
- `tests/brainstorm-server/`：测试 brainstorming 依赖的本地服务行为

这意味着它不是在测试“业务功能”，而是在测试：

- skill 是否会被正确发现
- agent 是否真的遵循 skill
- 多 subagent 工作流是否真的按设计顺序运行
- 跨平台插件是否真的能装载 skills

这对 harness engineering 尤其关键，因为 harness 本身就是平台资产，必须有自己的回归验证。

### 8. `docs/specs` 与 `docs/plans`：框架自己也按工程流程迭代

仓库里不仅有技能，还有大量设计与计划文档：

- `docs/plans/`：偏平台级或跨能力设计记录
- `docs/superpowers/specs/`：某项能力的设计规格
- `docs/superpowers/plans/`：对规格的实施计划拆解

这说明作者并没有把 Superpowers 当成“只靠直觉改 prompt 的仓库”，而是把它本身也作为一个需要 spec、plan、实施、验证的工程项目来管理。

对团队的直接启发是：

- 团队要做 harness engineering，最好也把 harness 本身纳入规范开发流
- 复杂能力先写 spec，再写可执行 plan
- 这样 agent 和人类都能围绕同一份工件协作

---

## 五、superpowers 最值得借鉴的 7 个设计模式

### 模式 1：先用 bootstrap 建立“工作纪律”

不要让 agent 直接进入业务实现，而是先注入一个元规则，告诉它：

- 什么时候必须先检查 skill
- 什么时候必须先规划
- 用户指令和技能冲突时谁优先

这可以避免团队使用 agent 时最常见的“先动手、后补流程”问题。

### 模式 2：围绕主流程组织技能，而不是堆积知识片段

`superpowers-main` 不是“很多技巧目录”，而是一条从 brainstorming 到 branch finishing 的完整链路。

这说明团队在设计 skills 时，应优先建设主路径：

- 澄清 / 设计
- 规划
- 实现
- review
- 验证
- 收尾

有了这条主路径，再谈分支型技能。

### 模式 3：多 agent 协作要有顺序化质量门

`subagent-driven-development` 最有价值的不是“用了 subagent”，而是给出：

- implementer
- spec reviewer
- code quality reviewer

这样的分工与顺序。

这对团队非常有用，因为多 agent 协作真正危险的地方，不是不会并发，而是**没有一致的质量门**。

### 模式 4：跨宿主共享核心，差异放适配层

如果团队未来要兼容多个宿主，最值得借鉴的是：

- 共享 `skills/` 和核心说明
- 为不同宿主写插件/安装/工具映射 adapter
- 用 docs 说明各自限制和使用方式

真正应复用的是知识资产，不是具体平台接口。

### 模式 5：把 harness 自己当成可测试系统

`tests/` 的存在说明，团队不应该只测业务代码，也要测：

- skill 会不会触发
- hook 会不会加载
- workflow 会不会按顺序执行
- adapter 会不会丢失 bootstrap

否则 harness 会越来越像“不可控的组织经验集合”，而不是工程系统。

### 模式 6：规格与计划分离，便于 agent 和人协作

spec 负责说明设计与边界，plan 负责把变更拆成任务。

这对团队尤其适合，因为：

- 人类更容易评审 spec
- agent 更容易执行 plan
- 二者结合，形成稳定交接面

### 模式 7：运行时代码只做必要增强

只在以下场景引入代码：

- 平台插件集成
- hook 注入
- 本地交互式辅助服务
- 测试与验证

其余流程逻辑尽量保持在 Markdown 层。这种做法更利于治理、迁移和审查。

---

## 六、哪些值得借鉴，哪些不要直接照搬

### 建议直接借鉴的部分

1. **bootstrap + session-start hook 的总入口设计**
2. **围绕主开发流程组织 skills**
3. **多 subagent 执行中的顺序化 review gate**
4. **跨宿主的核心共享 + 适配分层**
5. **对 skill system 本身做专项测试**
6. **spec / plan 驱动框架自身演进**

### 不建议直接照搬的部分

1. **全部技能数量**
   - 这套仓库已经有较完整的公开框架形态，团队起步不需要一次性复制全部 skill

2. **过强硬的技能纪律措辞**
   - `using-superpowers` 的规则非常强，适合公共框架塑形，不一定适合所有团队文化

3. **对 Claude Code 生态的强依赖测试方式**
   - 某些测试需要真实 `claude` CLI 和 headless session transcript，不一定适合每个团队当前环境

4. **全部平台同时起步支持**
   - 起步阶段应先选主宿主做稳，再扩展到其它平台

5. **带本地服务的 brainstorming 可视化能力**
   - 这是增强项，不是团队搭 harness 的最小必需品

一句话：**先学它的结构，不要先学它的规模。**

---

## 七、如果你的团队照着搭，最小可行版本应该是什么

基于 `superpowers-main` 的结构，我建议团队最先搭一个最小闭环，而不是完整复刻。

### 1. 一个统一 bootstrap

至少要有一个总入口，告诉 agent：

- 如何发现和使用团队技能
- 哪些工作必须先走计划或验证
- 用户指令、团队规则、默认行为之间的优先级

### 2. 一条主流程

最小建议是：

1. 澄清 / 设计
2. 计划拆解
3. 实现
4. review
5. verify
6. branch / release 收尾

### 3. 三到五个核心 skills

建议优先建设：

- `brainstorming` 或等价设计技能
- `writing-plans`
- `test-driven-development` 或团队认可的实现约束技能
- `requesting-code-review`
- `verification-before-completion`

### 4. 一个 session-start 注入机制

不论宿主是什么，都建议有办法在会话开始时自动注入团队 bootstrap，而不是依赖人工“记得先读某文档”。

### 5. 一套 harness 自测

至少先覆盖：

- skill 是否能被发现
- bootstrap 是否被加载
- 关键 skill 是否在典型 prompt 下被触发
- review / verify 这类关键流程有没有被跳过

这就是团队 harness 的最小可信版本。

---

## 八、结合你们后续团队搭建的实施建议

如果目标是“指导团队后续搭建 harness engineering”，从 `superpowers-main` 里我认为最值得优先落地的是下面这 6 件事。

### 建议 1：先设计一份团队级 bootstrap 文档

内容至少包括：

- agent 工作流总原则
- 技能使用纪律
- 用户/项目规则/默认行为的优先级
- 常见任务该走哪些流程

### 建议 2：围绕主开发链先建设最小 skill 集

不要先追求很多 skill，而是先把：

- 设计
- 规划
- 实现纪律
- review
- verify

这五类能力串起来。

### 建议 3：把跨宿主差异显式化

如果未来团队可能同时用 Cursor、Claude Code、Codex 或其它宿主，建议从一开始就拆出：

- 核心 skills 层
- adapter / install 层
- 工具映射文档层

不要把平台差异写进一大段不可维护的系统提示词。

### 建议 4：把 harness 自己纳入 specs / plans 管理

团队在建设 harness 时，也应该像建设普通软件一样：

- 先做设计
- 再做计划
- 再实施
- 再验证

不要把 harness 建设变成“边想边加文档”的长期失控过程。

### 建议 5：尽早做 skill-system 测试，而不只是文档检查

仅仅验证 Markdown frontmatter 正确是不够的。更高价值的是验证：

- 某类 prompt 是否会触发对应 skill
- agent 是否在行动前真的先加载了 skill
- 关键工作流有没有按顺序执行

这是 `superpowers-main` 特别值得借鉴的地方。

### 建议 6：把复杂多 agent 协作做成显式流水线

如果团队未来想上 subagent，不要只说“可以派子代理做任务”，而是要规定：

- 谁负责实现
- 谁负责规格校验
- 谁负责质量校验
- 哪一关不过不能流到下一关

这样多 agent 协作才可控。

---

## 九、推荐的团队落地路线

下面是一条比“直接照搬 Superpowers”更现实的演进路径。

### 阶段 0：统一工作纪律

先产出：

- bootstrap 文档
- 最小 skill 使用规则
- 团队默认开发流程

成功标志：

- 团队对 agent 什么时候该 plan、什么时候该 review、什么时候该 verify 有共同理解

### 阶段 1：形成最小 skill 闭环

先搭出：

- brainstorming / design
- writing-plans
- review
- verify

成功标志：

- 大多数常见开发请求已经能走统一主路径

### 阶段 2：补 session-start 与宿主适配

补齐：

- 会话自动注入
- 平台安装说明
- 工具映射文档

成功标志：

- 同一套核心技能可以在主宿主中稳定工作

### 阶段 3：补 harness 测试

补齐：

- 触发测试
- 顺序测试
- 端到端 workflow 测试

成功标志：

- 升级 bootstrap、skills、adapter 时不再完全靠人工试错

### 阶段 4：再考虑 subagent 流水线和可视化增强

此时再引入：

- subagent-driven execution
- 更强的 review gate
- 更复杂的 brainstorm UI / local service

成功标志：

- 团队已经能稳定驾驭 harness，而不是被复杂度反噬

---

## 十、最终建议

站在“指导团队搭 harness engineering”的视角，我对 `superpowers-main` 的最终判断是：

### 它最值得学习的，不是技能内容，而是把 Agent 使用方式工程化

这套框架真正做成的事情是：

- 把“先检查流程再行动”变成 bootstrap
- 把“开发闭环”变成一组可触发 skills
- 把“跨宿主支持”变成薄适配层
- 把“框架本身是否有效”变成测试对象
- 把“框架自身演进”变成 specs + plans 驱动

### 你的团队最该复用的三条原则

1. **先建 bootstrap，再扩 skill 数量**
2. **先建主流程，再建复杂分支能力**
3. **先把 harness 测起来，再把 harness 做大**

### 如果只做一件事

那我建议你们先按 `superpowers-main` 的思路搭出这样一个最小闭环：

- 一个团队 bootstrap
- 一条设计到验证的主流程
- 四到五个核心 skills
- 一个 session-start 注入机制
- 一组 skill trigger / workflow tests

只要这个闭环稳定跑起来，你们的 harness engineering 就已经从“个人提示词技巧”进入“团队工程系统”的阶段了。

---

## 附录：一句话总结这套框架

`superpowers-main` 不是在教团队“怎么写更长的提示词”，而是在示范：**如何把 Agent 的工作方式产品化成一套可引导、可分发、可验证、可演进的工程框架。**
