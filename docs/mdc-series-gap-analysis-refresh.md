# MDC 系列 Skills 新一轮对比说明

## 1. 文档目的

本文重新对比三套体系：

- `superpowers`
- `longtaskforagent`
- 当前 `skills/mdc-workflow/` 下的 `mdc-*` 系列

本次评估基于 `mdc` 在方案 B 第一轮落地和第二轮质量层一致性清理之后的当前状态，而不是早期版本。

本文要回答 4 个问题：

1. 相比 `superpowers`，当前 `mdc` 继承了哪些工作流约束？
2. 相比 `longtaskforagent`，当前 `mdc` 吸收了哪些 SDD 思想？
3. 当前 `mdc` 离你期望的“强流程约束 + 轻量 SDD”还有哪些剩余差距？
4. 这些差距里，哪些是需要继续补的，哪些是有意保留的设计边界？

## 2. 结论先行

一句话结论：

**当前 `mdc` 已经从“流程蓝图”升级成了“具备轻量工件驱动闭环的可用体系”，并且已经明显接近你想要的方向；剩余差距主要不再是主链缺失，而是强度、自动化程度和多语言覆盖范围仍弱于 `superpowers` 与 `longtaskforagent`。**

如果拆开说：

- 相对 `superpowers`，`mdc` 现在已经基本继承了你最在意的那部分约束：先路由、再阶段推进、禁止跳步、TDD 前置、完成前必须验证。
- 相对 `longtaskforagent`，`mdc` 现在已经具备轻量版的工件驱动：有最小工件契约、有 `task-progress.md`、有 review / verification 落盘、有支线流程、有收尾闭环。
- 但它仍然没有达到 `longtaskforagent` 那种“强状态机 + 强脚本化 + 强中央状态文件”的机械程度，也没有达到 `superpowers` 那种“全局元纪律”强度。

因此，当前 `mdc` 的定位可以重新表述为：

**它已经不是单纯的说明型 skills 集合，而是一套偏轻量、无 subagent、以文档证据驱动的软件交付 workflow skills；只是它仍然刻意停在“中等增强版”，没有继续走向重型工程操作系统。**

## 3. 你的目标状态

结合 `coding-skills-design.md` 与你多轮要求，你真正要的不是完整复制参考体系，而是：

### 3.1 继承 `superpowers` 的纪律

- 先 skill，后动作
- 先路由，再澄清、探索、读代码、设计、实现
- 先规格，再设计，再任务，再实现
- 没有失败测试，不进入生产代码
- 没有 fresh verification evidence，不宣称完成

### 3.2 借鉴 `longtaskforagent` 的轻量 SDD

- 用工件表示阶段，而不是靠对话记忆
- 用已批准的规格 / 设计 / 任务驱动推进
- 用进度记录、评审记录、验证记录支撑跨会话恢复
- 用变更 / 热修复支线处理主链外场景

### 3.3 保留 `mdc` 的边界

- 主代理串行执行
- 不依赖 subagent 编排
- 不直接复制 ATS / feature-list / ST 全套重流程
- 保持团队内可先试用的轻量度

## 4. 三套体系的最新对比

### 4.1 总览表

| 维度 | `superpowers` | `longtaskforagent` | 当前 `mdc` |
|---|---|---|---|
| 元入口纪律 | 极强，几乎任何任务都先查 skill | 极强，长任务会话一开始先判阶段 | 在 `mdc` 域内已很强，`mdc-workflow-starter` 已成为系列级前置门 |
| 阶段路由依据 | 流程 skill + 纪律约束 | 明确工件 / 信号文件 / 状态文件 | 明确工件证据优先级 + 保守回退规则 |
| 规格 / 设计 / 任务分层 | 强，但更偏 workflow discipline | 极强，WHAT / LOOK / HOW / ATS 层次完整 | 强，已有规格 / 设计 / 任务 / 实现分层 |
| 实现约束 | TDD、验证、计划驱动 | Worker 流水线，含 TDD / Quality / ST / Persist | 有强顺序链，但不含完整 ATS / ST 体系 |
| 工件驱动程度 | 中 | 很强 | 中偏强，已具轻量闭环 |
| 跨会话恢复 | 依赖流程 skill + 计划 | 很强，文件就是状态 | 已具雏形且可用，强度仍弱于 long-task |
| 支线流程 | 有，但不是重点 | increment / hotfix 很成熟 | `mdc-increment` / `mdc-hotfix` 已接入主体系 |
| 完成门禁 | 很强 | 很强 | 很强，已明确继承 |
| 评测覆盖 | 依赖 skill 本身成熟度 | 更偏流程系统与阶段技能 | 已补主链关键 eval，但未覆盖全系列，也未形成运行闭环 |
| 自动化 / 机械化 | 中 | 很强 | 中，更多靠规则与模板，较少脚本校验 |

### 4.2 和上一轮评估相比，最大的变化

上一次对比时，`mdc` 的主要问题还是：

- 系列级入口纪律不够强
- 工件契约偏推荐，状态闭环偏弱
- 质量层 review / gate 落盘协议不统一
- `mdc-implement -> TDD` 依赖不闭合
- eval 覆盖不足

现在这几个点已经发生了明显变化：

- `mdc-workflow-starter` 已经被强化为系列级统一前置门
- `AGENTS.md` 中的 `mdc-workflow` 配置与 `routing-evidence-guide` 已明确最小工件契约与证据优先级
- `task-progress-template`、`review-record-template`、`verification-record-template` 已补齐
- 质量层已统一到 review / gate 落盘协议与 `task-progress.md` 同步语义
- `mdc-test-driven-dev` 已变成系列级 TDD 入口
- 主链关键节点已有一轮 eval 文件覆盖

所以新的评估不能再把 `mdc` 视为“只有骨架”。现在更准确的说法是：

**骨架、最小状态闭环、质量层协议和核心门禁已经形成。**

## 5. 当前 `mdc` 已经很好继承的部分

## 5.1 已明显继承 `superpowers` 的部分

### A. 先路由，后动作

`mdc-workflow-starter` 已经把“在执行任何其他动作之前先路由”写成系列级规则，且明确禁止：

- 先读实现代码
- 先做大范围探索
- 先问一轮规格问题
- 先开始设计或实现

这已经非常接近 `using-superpowers` 的核心精神。

### B. 流程类 skill 优先于实现动作

当前 `mdc` 主链已经明确：

`mdc-specify -> mdc-design -> mdc-tasks -> mdc-implement -> quality layer -> finalize`

这意味着实现不再被视为默认起点，而是流程中的后段动作。

### C. TDD 被视为硬门禁

`mdc-implement` 明确：

- 先确定当前唯一活跃任务
- 先输出测试用例设计
- 先由真人确认测试设计
- 再进入 `mdc-test-driven-dev`

这比早期版本更强，也更像 `superpowers/test-driven-development` 的严纪律版本。

### D. 完成前验证已经是体系硬门禁

`mdc-completion-gate` 现在不只是“建议检查”，而是带有：

- 验证记录默认落盘位置
- `通过 / 需修改 / 阻塞` 三态结论
- 与 `task-progress.md` 同步的下一步语义
- 明确指向 `mdc-finalize` 的收口动作

这一块已经是 `verification-before-completion` 的有效继承，而不是口号式继承。

## 5.2 已明显吸收 `longtaskforagent` 的部分

### A. 用工件和证据做阶段路由

`mdc-workflow-starter` 不再只靠用户一句“继续”，而是检查：

- `AGENTS.md` 中的 `mdc-workflow` 配置
- 规格 / 设计 / 任务工件及其批准状态
- `task-progress.md`
- review 记录
- verification 记录

并且对冲突采用保守回退。

这已经是轻量版的 phase routing，而不是对话记忆驱动。

### B. 主链与支线同时存在

当前 `mdc` 已具备：

- 主链：规格 -> 设计 -> 任务 -> 实现 -> 质量层 -> 完成
- 支线：`mdc-increment`
- 支线：`mdc-hotfix`

这和 `longtaskforagent` 的 branch thinking 是同一路数，只是更轻。

### C. 轻量持久化状态已成型

当前 `mdc` 已经有一套最小状态载体：

- `task-progress.md`
- `docs/reviews/`
- `docs/verification/`
- `RELEASE_NOTES.md`

再加上 `AGENTS.md` 中集中声明的工件映射与审批约定，已经可以支撑跨会话继续推进，而不完全依赖聊天历史。

### D. 质量层已从“建议”升级为“协议”

质量层现在不仅存在，而且已经有统一协议：

- 默认记录路径
- 默认模板
- 与 `task-progress.md` 的同步规则
- `通过 / 需修改 / 阻塞` 的状态语义
- 唯一下一步 skill

这说明 `mdc` 已经开始接近 `long-task-work` 里“流水线各步都有独立责任”的风格。

## 6. 当前 `mdc` 与目标状态的剩余差距

下面这些是新的重点差距。它们比旧版少了，但仍然真实存在。

### 6.1 差距一：入口纪律已强，但还不是 `superpowers` 级的“全局元纪律”

#### 当前状态

在 `mdc` 域内，`mdc-workflow-starter` 已经很强。

但它和 `using-superpowers` 仍有一个差别：

- `superpowers` 试图约束“任何可能相关的任务”
- 当前 `mdc` 更聚焦于“软件交付类请求”

#### 影响

如果用户在更模糊的编码上下文里发起任务，而代理没有先进入 `mdc` 域判断，理论上仍可能绕开这套体系。

#### 判断

这是 **部分差距**，但已经不是体系主缺口，而是元入口覆盖范围差异。

### 6.2 差距二：工件驱动已经成立，但中央状态载体仍弱于 `feature-list.json`

#### 当前状态

`task-progress.md` 已经承担了：

- 当前阶段
- 当前活跃任务
- 待处理 review / gate
- 下一步 skill

这已经解决了早期“完全靠会话记忆”的问题。

#### 仍然不足的地方

相比 `longtaskforagent` 的 `feature-list.json`，当前 `mdc` 仍缺：

- 全量任务状态的结构化列表
- 依赖关系的机械校验
- 任务级别的统一字段约束
- 对弃用 / 阻塞 / 已通过项的集中状态视图

#### 判断

这是 **有意保留的轻量差距**。它不是缺体系，而是尚未进入重型中央状态文件方案。

### 6.3 差距三：TDD 入口已闭合，但具体语言覆盖仍然不足

#### 当前状态

`mdc-test-driven-dev` 现在已经是系列级入口，这是一个明显进步。

但当前它的具体实现仍主要覆盖：

- C++ / GoogleTest / CMake

并明确说明其他语言尚未覆盖。

#### 影响

这意味着：

- `mdc-implement` 的制度闭环有了
- 但 `mdc` 作为通用 coding workflow skill 系列，其 TDD 执行层仍是局部可用

#### 判断

这是 **当前最大的功能性剩余差距之一**。

### 6.4 差距四：eval 覆盖已起步，但还没有形成真实验证闭环

#### 当前状态

现在已经有 eval 文件的包括：

- `mdc-workflow-starter`
- `mdc-specify`
- `mdc-design`
- `mdc-tasks`
- `mdc-implement`
- `mdc-completion-gate`

这比旧版强很多。

#### 仍然不足的地方

还缺两层：

1. 覆盖面仍未完整到全系列
2. eval 文件已经写了，但还没有形成“运行 -> 看结果 -> 继续修 skill”的闭环

#### 判断

这是 **部分实现**，而不再是“完全缺失”。

### 6.5 差距五：`longtaskforagent` 的测试策略层仍未被 `mdc` 吸收

#### 当前状态

当前 `mdc` 已有：

- TDD
- bug patterns
- test review
- code review
- traceability review
- regression gate
- completion gate

这套质量链已经够用。

#### 与 `longtaskforagent` 的差异

`longtaskforagent` 还有更重的一层：

- ATS
- feature-level ST
- system testing phase
- quality gate 脚本化阈值

当前 `mdc` 明确没有这些重层。

#### 判断

这部分既是 **剩余差距**，也是 **明确设计边界**。如果你的目标仍是轻量 SDD，就不一定要补齐。

### 6.6 差距六：协议已统一，但自动化校验仍偏少

#### 当前状态

现在 `mdc` 的很多约束已经写成了明确协议：

- 工件位置
- 批准信号
- review / verification 记录模板
- `task-progress.md` 语义
- 保守回退规则

#### 仍然不足的地方

与 `longtaskforagent` 相比，`mdc` 还缺少更多机械校验手段，例如：

- 自动检查当前阶段是否满足准入条件
- 自动检查关键记录是否缺失
- 自动检查某些任务状态或依赖冲突

#### 判断

这是 **中等差距**。它影响的是稳定性上限，而不是当前体系是否成立。

## 7. 按“已实现 / 部分实现 / 有意保留差距”重新归类

## 7.1 已实现

- `mdc` 域内的统一入口门已经成立
- 主链和支线流程已经完整
- 规格 / 设计 / 任务 / 实现分层已经成立
- review / gate 已独立成层，并已接入落盘协议
- `task-progress.md` 已成为轻量状态载体
- `mdc-completion-gate` 已有效继承完成前验证门禁
- `mdc-implement -> mdc-test-driven-dev` 的入口依赖已经闭合
- 主链关键节点已有基础 eval 覆盖

## 7.2 部分实现

- `superpowers` 级别的全局 skill-first 元纪律
- `longtaskforagent` 级别的中央任务状态文件
- 系列级 TDD 的多语言具体实现
- eval 的全系列覆盖与实际运行闭环
- 更多脚本化、机械化的自动检查

## 7.3 有意保留的差距

- 不使用 subagent 编排
- 不复制完整 ATS / feature ST / system ST 流程
- 不引入过重的信号文件和中央控制脚本
- 不把 `mdc` 直接做成另一个 `longtaskforagent`

## 8. 最新总体判断

如果把目标定义为：

**“继承 `superpowers` 的工作流约束，同时借鉴 `longtaskforagent` 的 SDD 思想，并保持无 subagent、轻量、团队可试用。”**

那么当前 `mdc` 的完成度，我会这样判断：

### 8.1 相对目标的达成度

- 工作流约束继承度：**高**
- 轻量 SDD 吸收度：**中高**
- 跨会话闭环能力：**中高**
- 机械化状态机强度：**中**
- 通用实现层完备度：**中**

### 8.2 更直白的说法

当前 `mdc` 已经不再是“还差一大截”的状态。

更准确地说：

- 你想要的方向，已经立住了
- 最核心的闭环，已经搭起来了
- 剩下的差距主要集中在“更强”“更广”“更机械”，而不是“有没有”

也就是说，当前 `mdc` 和你的目标之间，已经从“方向差距”转成了“强度差距”。

## 9. 建议如何理解这些剩余差距

我建议把剩余差距分成两类，不要混在一起。

### 9.1 应优先继续补的

- `mdc-test-driven-dev` 的非 C++ 语言覆盖
- 剩余 quality / branch skill 的 eval 覆盖与实际运行
- 少量可机械检查的协议校验

这些会直接提升体系的可用性和稳定性。

### 9.2 不必急着补的

- `feature-list.json` 级别的中央状态机
- ATS / feature ST / system ST 的完整重流程
- subagent worker 编排

这些会让 `mdc` 更像 `longtaskforagent`，但同时也会显著抬高 adoption 成本。

## 10. 最终结论

新的结论可以概括为：

**当前 `mdc` 已经基本达成“继承 `superpowers` 约束、借鉴 `longtaskforagent` 轻量 SDD”的中等增强版目标。**

它现在的主要短板不再是主流程、门禁或工件闭环，而是：

- TDD 执行层的多语言覆盖不足
- eval 还没有真正跑起来
- 缺少部分更机械的自动校验

如果你问“当前 `mdc` 离我想要的还差多少”，我的最新回答是：

**已经不是“体系没成”，而是“体系已成，但还没完全打磨到最强版本”。**
