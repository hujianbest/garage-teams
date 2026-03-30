# OpenSpec-main 源码分析报告：面向团队搭建 Harness Engineering 框架的参考

这份报告的目标不是介绍 `references/OpenSpec-main/` 的命令清单，而是回答一个更关键的问题：

**如果团队后续要把 Agent 使用方式工程化，OpenSpec 的源码里有哪些结构、机制和边界，值得被吸收进一套团队级 harness engineering 框架。**

---

## 一、结论先行

如果把 `OpenSpec-main` 压缩成一句话，它本质上不是“又一个 spec 文档模板仓库”，而是一套围绕 **artifact-driven workflow** 组织 Agent 工作的框架：

- 用 `openspec/specs/` 和 `openspec/changes/` 建立长期规范与单次变更的分层
- 用 `schemas/spec-driven/schema.yaml` 把 proposal、specs、design、tasks、apply 定义成可计算的工作流
- 用 `src/core/artifact-graph/` 把工作流转成依赖图、完成状态和指令生成能力
- 用 `src/core/init.ts`、`src/core/update.ts`、`src/core/command-generation/registry.ts` 把同一套 workflow 分发到多种 AI 工具
- 用 `openspec/config.yaml`、自定义 schema 和模板，把团队规则注入到每个 artifact 的生成过程

对团队做 harness engineering 来说，OpenSpec 最值得借鉴的不是“spec 写法”，而是下面这 5 层分治结构：

1. **工件层**：把需求、设计、任务拆成独立且可归档的 artifacts
2. **工作流层**：把 artifacts 的依赖关系写成 schema，而不是写死在 prompt 里
3. **引擎层**：用 graph、status、instruction generator 统一驱动人和 Agent
4. **适配层**：同一套逻辑，按不同工具生成对应 skills / slash commands
5. **治理层**：用配置、模板、schema fork 和 archive 机制支持团队演进

这五层正好对应团队搭建 harness engineering 时最容易混在一起、也最应该拆开的五类能力。

---

## 二、分析范围

本报告基于对 `references/OpenSpec-main/` 的源码级阅读，重点关注以下资产：

- 入口与定位：`README.md`、`bin/openspec.js`、`src/cli/index.ts`
- 核心工作流：`docs/concepts.md`、`docs/workflows.md`
- 工作流定义：`schemas/spec-driven/schema.yaml`
- 图与指令引擎：`src/core/artifact-graph/graph.ts`、`src/core/artifact-graph/instruction-loader.ts`、`src/commands/workflow/instructions.ts`
- 分发与适配：`src/core/init.ts`、`src/core/update.ts`、`src/core/profiles.ts`、`src/core/command-generation/registry.ts`
- 团队定制：`docs/customization.md`、`src/core/config.ts`

分析重点不是穷举所有实现，而是提炼出对团队建设 harness engineering 最有迁移价值的设计原则。

---

## 三、OpenSpec 到底是什么

从 `README.md` 和 `docs/concepts.md` 可以看出，OpenSpec 解决的不是“怎么写更详细的 prompt”，而是三件更底层的事：

1. 让需求、设计、任务和实现之间有稳定的工件边界
2. 让 Agent 围绕这些工件工作，而不是围绕一段临时聊天上下文工作
3. 让同一套工作方式可以被安装到多种 AI coding tool 中

它的核心哲学也非常明确：

- `fluid not rigid`
- `iterative not waterfall`
- `easy not complex`
- `brownfield-first`

这意味着它不是传统 PM 流程工具的 CLI 版，而是一个偏 Agent-native 的 **workflow harness**。它承认真实开发会反复修改 proposal、design、tasks，但又通过 schema 和 artifact graph 保持结构化。

---

## 四、源码架构拆解：OpenSpec 的 6 个关键子系统

### 1. CLI 编排层：统一入口，命令路由清晰

`bin/openspec.js` 很薄，只负责把进程交给编译后的 CLI。真正的命令编排集中在 `src/cli/index.ts`。

这一层做了几件很重要的事：

- 用 `commander` 注册 `init`、`update`、`validate`、`archive`、`status`、`instructions`、`schemas` 等命令
- 在 `preAction` / `postAction` 中统一处理 telemetry 和全局行为
- 把命令路由到 `src/core/` 或 `src/commands/` 中的模块，而不是把业务逻辑塞进 CLI 文件

这对团队 harness 的启发是：**入口应尽量薄，工作流能力要模块化。** CLI、IDE command、Web hook 都应只是入口，真正的 workflow engine 要独立存在。

### 2. 工件模型层：把“当前事实”和“待实施变化”分开

OpenSpec 的目录模型是整个框架最值得学习的部分之一：

- `openspec/specs/` 表示当前系统行为的 source of truth
- `openspec/changes/<change-name>/` 表示一个待完成变更的完整上下文
- `openspec/changes/archive/` 保留已完成变更的完整历史

在 `docs/concepts.md` 里，这个模型被解释得很清楚：`specs/` 是当前事实，`changes/` 是提案与变更工作区，归档时 delta 会合并回主 specs。

这个分层对团队 harness engineering 很关键，因为它天然解决了 4 个问题：

- **并行性**：多个 change 可以并行推进
- **审查性**：proposal / design / tasks / delta specs 聚合在一个 change 目录中
- **可追溯性**：归档后能同时看到“改了什么”和“为什么这么改”
- **稳定协作边界**：Agent 不再只依赖聊天历史，而是依赖可读写工件

### 3. Schema 层：把流程定义成数据

`schemas/spec-driven/schema.yaml` 是 OpenSpec 的核心设计点。这里并没有把流程硬编码成“必须先 proposal 再 specs 再 design”，而是把 artifact 定义为带依赖关系的声明式数据：

- `proposal` 无依赖
- `specs` 依赖 `proposal`
- `design` 依赖 `proposal`
- `tasks` 依赖 `specs` 和 `design`
- `apply` 依赖 `tasks`，并跟踪 `tasks.md`

更重要的是，这个 schema 还包含：

- artifact 的输出路径
- artifact 的模板文件
- artifact 的生成说明
- apply 阶段的跟踪文件与执行说明

这带来的好处非常大：

- 新增一个流程步骤，本质上是改 schema，而不是重写整套系统提示
- 不同团队可以 fork schema，生成不同 workflow
- 运行时可以对 artifact 完整性、依赖关系、模板存在性做验证

对 harness engineering 来说，这相当于把“团队工作流”从隐性经验升级成 **可执行流程元数据**。

### 4. Artifact Graph 与指令引擎：把 schema 变成可操作系统

OpenSpec 不是停在 YAML 定义层，而是继续在 `src/core/artifact-graph/` 里把 schema 变成运行时能力。

### `ArtifactGraph`

`src/core/artifact-graph/graph.ts` 提供了：

- build order 计算
- ready artifact 计算
- blocked artifact 计算
- workflow complete 判定

这里的关键不是算法本身，而是它把“当前 change 到底能做什么”抽象成统一状态机。

### `instruction-loader`

`src/core/artifact-graph/instruction-loader.ts` 会把：

- schema instruction
- 模板内容
- project context
- artifact-specific rules
- 已完成依赖与未完成依赖

合成结构化的 artifact instructions。

### `instructions` / `apply`

`src/commands/workflow/instructions.ts` 又把这些内部对象输出成面向 Agent 的文本接口：

- 创建某个 artifact 时该读哪些依赖文件
- 输出写到哪里
- 使用哪个模板
- 当前是否被依赖阻塞
- `apply` 阶段还有多少任务未完成

这一步非常值得团队借鉴，因为它说明一个成熟 harness 不只是“存规则”，还要提供 **instruction API**。Agent 最好不是直接读整个仓库自己猜，而是由 harness 明确给出当下可执行指令。

### 5. 分发与适配层：同一 workflow，面向多种宿主

`src/core/init.ts` 和 `src/core/update.ts` 是另一组很有工程价值的源码。它们做的事情并不是初始化一个业务项目，而是：

- 探测项目里有哪些 AI 工具目录
- 根据 profile 决定启用哪些 workflow
- 根据 delivery 决定生成 skills、commands 或两者
- 用共享模板 + 各工具 `skillsDir` 生成 skills
- 用 `CommandAdapterRegistry` 为不同工具生成 commands

`src/core/config.ts` 和 `src/core/command-generation/registry.ts` 进一步表明，这个框架从一开始就是按“共享核心 + 多宿主 adapter”设计的。支持的工具非常多，但核心 workflow 并没有被复制多份。

对团队落地尤其重要的启发是：

- 核心能力要放在共享层
- 宿主差异要收敛到 adapter
- 不要把 Cursor、Claude、Codex 的差异直接写进每个 skill 的正文里

如果未来你们团队需要兼容多种 Agent 宿主，这一层应该从第一天就设计出来。

### 6. 配置与定制层：把团队规则注入到 artifact 生成过程

`docs/customization.md`、`src/utils/change-metadata.ts` 和 `src/core/global-config.ts` 展示了 OpenSpec 的另一条很成熟的思路：**不要把所有控制面都塞进同一份项目配置，而是分层治理。**

OpenSpec 实际上至少有三层配置面：

- **项目级配置**：`openspec/config.yaml`，用于默认 schema、context、artifact rules
- **变更级元数据**：`openspec/changes/<change>/.openspec.yaml`，允许单个 change 覆盖 schema 选择
- **用户级全局配置**：平台配置目录下的 `openspec/config.json`，例如 Windows 的 `%APPDATA%/openspec/config.json` 或类 Unix 环境下的 `~/.config/openspec/config.json`，用于 profile、delivery、workflows 等本地安装行为

这种分层很值得团队借鉴，因为它把：

- 团队共享规范
- 单次变更特例
- 个人工具安装偏好

拆到了不同层次，避免一个配置文件同时承担流程治理和个人环境管理。

其中，团队在 `openspec/config.yaml` 中主要配置：

- 默认 schema
- 通用 context
- 不同 artifact 的规则

当生成某个 artifact 时，这些 context 和 rules 会被按顺序注入到 instructions 中。

这意味着：

- 核心 workflow 能保持通用
- 项目/团队可以在不改内核的情况下定制输出质量
- 同一套 harness 可以被不同业务线复用

对于团队级 harness engineering，这是一种非常健康的治理方式。

### 7. 迁移与兼容层：源码复杂度里有一部分不是目标架构，而是过渡成本

这是阅读 OpenSpec 源码时很容易忽略、但对复用判断非常重要的一点。

从 `docs/opsx.md`、`src/core/init.ts` 和 `src/core/update.ts` 可以看出，当前仓库并不只是一个“纯净的新架构实现”，还承担了从 legacy workflow 迁移到 OPSX workflow 的兼容职责，包括：

- legacy artifact 检测与清理
- profile system 迁移
- 旧命令与新命令并存
- update 时的兼容升级与漂移修复

这意味着团队在借鉴 OpenSpec 时，要把两类内容区分开：

- **值得复用的目标态设计**：artifact model、schema、graph、instruction engine、adapter
- **不必照搬的过渡态代码**：legacy cleanup、migration、兼容分支、双轨命令支持

换句话说，OpenSpec 仓库里的复杂度并不全是你们未来框架必须拥有的复杂度，其中一部分只是公共开源项目为了兼容历史资产付出的成本。

---

## 五、OpenSpec 最值得借鉴的 7 个设计模式

### 模式 1：把工作流定义成 schema，而不是长 prompt

OpenSpec 的最大优点是把 proposal、spec、design、tasks、apply 的关系定义成数据。这样流程就能被验证、被查询、被扩展，也更容易做自动化。

### 模式 2：用 artifact 作为人机协作的稳定边界

proposal 讲为什么，spec 讲做什么，design 讲怎么做，tasks 讲实施步骤。这样人审阅的是工件，Agent 执行的也是工件，聊天上下文只承担临时沟通，不承担长期记忆。

### 模式 3：让 graph 成为 workflow runtime

很多框架只有模板，没有状态引擎。OpenSpec 的 graph 能回答 ready、blocked、complete 这类问题，使 workflow 不再只是文档约定，而是运行时可判断的系统。

### 模式 4：给 Agent 暴露显式 instruction interface

`openspec instructions` 和 `apply instructions` 说明，harness 应该有能力把“下一步该做什么”解释给 Agent，而不是让 Agent 自己拼装所有上下文。

### 模式 5：核心共享，适配分发

流程逻辑、schema、模板和规则应该共享；不同宿主的命令格式、文件布局、安装方式应该下沉到 adapter。

### 模式 6：用 profile 管理复杂度

`src/core/profiles.ts` 里 `core` 只暴露少量默认 workflow，而完整能力可以按需开启。这种分层很适合团队推广，先给普通成员低复杂度入口，再逐步开放高级能力。

### 模式 7：把 archive 设计成治理能力，而不是简单归档

OpenSpec 的 archive 不是把文件挪走，而是把 delta 合并回主 specs，同时保留变更上下文。对于团队来说，这是一种非常实用的“规范演进记录机制”。

不过这里要分清两层：

- **CLI `openspec archive`**：默认会做 change / delta specs 校验，并在需要时阻塞归档
- **工作流命令 `/opsx:archive`**：更偏 agent-driven 收尾流程，会检查状态、提示 sync、对未完成任务给 warning，但整体比 CLI 更柔性

这说明 OpenSpec 的 archive 体系其实是“硬校验 CLI + 柔性工作流命令”并存，而不是单一风格。

---

## 六、哪些适合直接借鉴，哪些不要原样照搬

### 建议直接借鉴

1. **Artifact 分层模型**
   - `specs` / `changes` / `archive` 这套结构非常适合团队做长期规范沉淀

2. **Schema 驱动工作流**
   - 比写死在 prompt 中的阶段规则更易维护、更适合自动化

3. **Instruction Generator**
   - 这是让 Agent 真正“按框架工作”的关键中间层

4. **多宿主 adapter 设计**
   - 如果团队未来不止一种 Agent 宿主，这层必须尽早存在

5. **分层配置方式**
   - 项目级、变更级、用户级配置分层，比把所有控制项堆进单一 repo 配置更健康

### 不建议原样照搬

1. **完全照搬它的“fluid not rigid”哲学**
   - OpenSpec 故意把依赖做成 enabler 而不是强 gate，这很灵活，但对高合规、高安全、强审批场景可能不够

2. **把不同入口的 archive 行为混成一种门禁风格**
   - OpenSpec 的 `/opsx:verify` 是 advisory 的，不阻塞 `/opsx:archive`；CLI `openspec archive` 默认则会对 change 和 delta specs 做更硬的校验。团队借鉴时应区分“面向 Agent 的柔性流转”和“面向治理的硬校验入口”

3. **一开始就支持大量工具**
   - OpenSpec 支持的宿主很多，但团队自建框架起步阶段最好先稳住 1 到 2 个主要宿主

4. **把 spec 机制应用到所有类型工作**
   - Spec-driven workflow 对中大型、跨模块、需要审查的变化很有效，但对极小任务可能过重，团队需要定义使用边界

5. **把迁移兼容代码当成目标架构的一部分**
   - OpenSpec 当前仓库有不少复杂度来自 legacy 兼容与迁移，这部分通常不是团队自建框架起步阶段必须复制的内容

---

## 七、对团队搭建 Harness Engineering 的直接启发

如果后续你们团队要搭一套自己的 harness engineering 框架，我建议优先抽取 OpenSpec 里的以下骨架。

### 1. 建立团队级 artifact model

最少应该有：

- `spec` 或等价规范
- `design`
- `tasks`
- `review` / `verification`
- `archive`

不一定照搬 OpenSpec 命名，但一定要有“长期规范”和“单次变更工作区”的区分。

### 2. 用 schema 管流程，不用口头约定管流程

把每个 artifact 的：

- 输入依赖
- 输出位置
- 生成模板
- 生成规则
- 完成判定

都写成机器可读配置。这样后面才能做状态计算、校验、指令生成和宿主适配。

### 3. 设计一个独立的 instruction engine

团队框架不能只会“生成文档”，还要能回答：

- 这个 change 现在缺什么
- 下一步能做什么
- 哪些依赖必须先读
- 输出路径是什么
- 哪些团队规则适用

这正是 OpenSpec 最有工程价值的部分。

### 4. 把 review / compliance / verification 变成显式 artifacts

OpenSpec 在 `docs/customization.md` 里已经展示了给 schema 增加 `review` artifact 的方法。对团队实践来说，这一步非常重要，因为很多真正的 harness engineering 差异，不在 proposal/spec/design/tasks，而在：

- 安全评审
- 合规检查
- 测试验证
- 发布审批

这些应被建模成正式工件和正式依赖，而不是附注。

### 5. 把多宿主支持设计成后置 adapter

团队先做好：

- 核心 workflow schema
- instruction engine
- artifact storage

然后再为 Cursor、Claude、Codex 等环境生成各自的指令入口和文件布局。不要一开始就让平台差异污染核心模型。

---

## 八、一个更适合团队的落地版本

如果以 OpenSpec 为参考，我更建议你们落地成一个“更强治理版”的 harness，而不是原样复刻。

### 推荐的最小可行结构

1. `framework/specs/`
   - 团队公共规范与标准能力定义

2. `framework/changes/<change-id>/`
   - 单次变更工作区，包含 proposal、design、tasks、verification 等 artifacts

3. `framework/schemas/`
   - 团队 workflow 定义

4. `framework/templates/`
   - 各 artifact 的统一模板

5. `framework/engine/`
   - graph、status、instruction generation、validation

6. `framework/adapters/`
   - 不同 Agent 宿主的安装与分发逻辑

### 相比 OpenSpec 建议额外补强的能力

- 强制 review gate
- 强制 verification gate
- 和 CI / issue / PR 审批系统的联动
- 对不同工作类型使用不同 schema
- 对高风险场景增加人工确认与审计记录

也就是说，**OpenSpec 很适合做你们框架的内核灵感，但团队版需要比它更强调治理与质量门。**

---

## 九、最终建议

站在“为团队搭建 harness engineering 框架”的角度，我对 `OpenSpec-main` 的最终判断是：

### 它最值得学习的，不是 spec 文档格式，而是 workflow engine 思维

OpenSpec 真正做成的事情是：

- 把变更过程拆成稳定工件
- 把工件关系定义成 schema
- 把 schema 变成 graph 和 instructions
- 把 instructions 分发给多种 Agent 工具
- 把团队定制约束注入整个生成与执行过程

### 你们最该复用的三条原则

1. **先建 artifact model，再建提示词**
2. **先建 instruction engine，再建多宿主适配**
3. **先把 review / verification 建成正式 gate，再扩大自动化规模**

### 如果只做一件事

那我建议你们优先借鉴 OpenSpec 的这一条主线：

**schema -> artifact graph -> instruction generation -> tool adapters**

因为这条链路决定了一套 harness engineering 框架能否从“文档规范”升级为“真正可运行、可治理、可扩展的团队系统”。

---

## 附录：一句话总结 OpenSpec

`OpenSpec-main` 不是在教团队“如何写 spec”，而是在示范：**如何把 Agent 的规划、执行与归档过程，做成一套由 artifact、schema 和 adapter 驱动的工程框架。**
