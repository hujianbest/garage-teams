# `agent-skills-main` 与 `ahe-*` workflow skills 对比报告

## 结论摘要

- `agent-skills-main` 仍然更像一个“可分发、可移植、可快速上手”的通用工程 skill 产品包。它的核心优势依旧是统一 anatomy、元 skill 路由、命令/agent/hook 配套，以及天然兼容“单 skill 独立调用 + 多 skill 串联调用”。主要依据仍是 `references/agent-skills-main/README.md`、`references/agent-skills-main/docs/skill-anatomy.md`、`references/agent-skills-main/skills/using-agent-skills/SKILL.md`。
- `ahe-*` 当前已经不再只是“只能串联调用的 workflow 节点集合”。本轮修改之后，它更准确的定位是“以 **`ahe-workflow-router`** 为 runtime kernel、以 **`using-ahe-workflow`** 为家族公开入口的软件交付 workflow family”（pre-split 时期曾由单一 **legacy 合并入口/router** 兼任两者），并开始具备“条件式独立调用 + 强约束串联调用”的双模式能力。关键依据在 `skills/ahe-workflow-router/SKILL.md`、`skills/using-ahe-workflow/SKILL.md`、`skills/ahe-specify/SKILL.md`、`skills/ahe-design/SKILL.md`、`skills/ahe-tasks/SKILL.md`、`skills/ahe-test-review/SKILL.md`、`skills/ahe-bug-patterns/SKILL.md`。
- AHE 当前最突出的新变化有三点：一是 `ahe-workflow-router` 的连续执行、迁移表和恢复编排协议更完整；二是 review 节点已经明确走 reviewer subagent 协议；三是家族开始朝“独立调用 + 串联调用”双模式收敛，但 live skills 尚未完全统一成同一套 section-level contract。
- 因此，AHE 现在最需要借鉴 `agent-skills-main` 的，不再是“有没有双模式”本身，而是“如何把已经开始出现的双模式能力，收敛成统一 anatomy、统一入口心智、统一 collateral 文档”。

## 对比范围

- `references/agent-skills-main` 全量 skill 目录与代表性入口/命令/agent/hook 文档
- `skills/ahe-*/SKILL.md` 全量 17 个 workflow skills
- `skills/README.md`
- `skills/design_rules.md`
- `templates/task-progress-template.md`
- `skills/ahe-workflow-router/references/profile-selection-guide.md`
- `skills/ahe-workflow-router/references/routing-evidence-guide.md`
- `skills/ahe-workflow-router/references/routing-evidence-examples.md`
- `skills/ahe-workflow-router/references/review-dispatch-protocol.md`
- `skills/ahe-workflow-router/references/reviewer-return-contract.md`

## 本轮刷新后的关键判断

### AHE 相比上一版评估，已经发生的变化

- `ahe-workflow-router` 不仅负责 runtime 路由，还明确承担连续执行、review/gate 后恢复编排、显式 handoff 解释和结果驱动迁移；家族公开入口由 `using-ahe-workflow` 承担。参见 `skills/ahe-workflow-router/SKILL.md`。
- review 节点现在有更清晰的 subagent 执行协议，尤其是 `skills/ahe-workflow-router/references/review-dispatch-protocol.md` 和 `skills/ahe-workflow-router/references/reviewer-return-contract.md`，说明 AHE 已经把 reviewer 从“当前会话直接继续评审”推进到“受控 reviewer return contract”。
- 多个上游节点已经统一加入“如果当前请求尚未经过 router 的阶段判断，应先回到 `ahe-workflow-router` 完成路由”的硬性门禁，例如 `skills/ahe-specify/SKILL.md`、`skills/ahe-design/SKILL.md`、`skills/ahe-tasks/SKILL.md`、`skills/ahe-spec-review/SKILL.md`、`skills/ahe-design-review/SKILL.md`、`skills/ahe-tasks-review/SKILL.md`。
- 同时，质量评审类节点又开始明确手动调用/补充性调用语义，这意味着 AHE 现在已经具备“节点可独立调用，但必须受前置条件约束”的雏形，而不是纯 chain-only。

### AHE 当前仍未完成的收敛

- live skills 还没有统一写成显式的 `standalone contract` / `chain contract` 结构，这一点和 `agent-skills-main` 的清晰 anatomy 仍有差距。
- 共享模板层已经开始向 canonical schema 收敛，但 live skills 还没有整体完成 adopt，真正的 contract rollout 仍在后续批次里。
- router collateral 的最高优先级冲突已经开始被关闭，但 `ahe-workflow-router/SKILL.md` 主文件仍然偏重，离理想的 kernel 形态还有距离（解释层应继续向 `using-ahe-workflow` 与 docs 转移）。
- reviewer subagent 协议已经有了更清楚的 canonical handoff 表达，但 downstream reviewer skills 自身还没有全部同步到同一套目标态 skeleton。

## 系统定位对比

| 维度 | `agent-skills-main` | `ahe-*` 当前状态 | 判断 |
| --- | --- | --- | --- |
| 主要目标 | 通用工程 skill 产品包 | 软件交付 workflow family | 两者目标依然不同，不能只按“功能多少”评价 |
| 复用单元 | 单 skill 可独立触发，也可被命令串联 | 单节点 skill 可被独立点名，但常需满足前置条件；阶段不清时由 `ahe-workflow-router` 验证并恢复编排 | `agent-skills` 仍更像工具箱，AHE 更像流程机 |
| 路由方式 | `using-agent-skills` 元 skill + `.claude/commands/*.md` + SessionStart hook | `using-ahe-workflow`（入口）+ `ahe-workflow-router` + legal node set + migration tables + recovery protocol | AHE 路由更强约束、更状态机化 |
| 双模式能力 | 天然支持独立调用与薄命令串联 | 已开始支持“条件式 direct invoke + 强约束 chain invoke”，但尚未统一成固定 contract | AHE 正在追近，但还未完全达成 |
| 生命周期模型 | DEFINE / PLAN / BUILD / VERIFY / REVIEW / SHIP | full / standard / lightweight 主链 + increment / hotfix 支线 | `agent-skills` 易懂，AHE 更贴近真实软件交付 |
| 证据模型 | Verification checklist + review persona + command wrapper | review record + verification record + task-progress + explicit handoff + reviewer return contract | AHE 的证据链仍更完整、更可审计 |
| reviewer 执行方式 | 人格/skill/command 协同，但更多是产品化薄封装 | review 节点显式采用 reviewer subagent 协议；gates 仍保留主会话 authority | AHE 在“受控 review 节点化”上更强 |
| 人工介入 | 偏建议式与验证式，人类可随时介入 | spec/design 审批、测试设计确认等处仍有明确 pause point | AHE 仍更适合高控制场景 |
| 辅助资产 | `docs/skill-anatomy.md`、`agents/`、`.claude/commands/`、`hooks/`、`references/` | `templates/` + skill `references/` + `AGENTS.md` + router / workflow collateral docs | `agent-skills` 配套层更产品化，AHE 配套层更 workflow-specific |
| 可移植性 | 高，默认就是可分发 skill pack | 中等；比上一版更可拆用，但仍依赖目录、记录路径与状态工件 | AHE 仍需一层 repo-agnostic 抽象 |
| 维护成本 | 中等，靠统一 anatomy 降低漂移 | 仍偏高；router 主文件仍偏重，且家族规则尚未完全从 live skills 中抽离 | AHE 仍更容易出现一致性漂移 |

## `agent-skills-main` 的优势

- 有稳定的家族级元 skill。`references/agent-skills-main/skills/using-agent-skills/SKILL.md` 集中定义 discovery flowchart、全局操作行为和多 skill 序列。
- 有统一、明确、外部可复用的 anatomy。`references/agent-skills-main/docs/skill-anatomy.md` 对 frontmatter、章节、supporting files、cross-skill references 都有清晰规则。
- 对“双模式调用”的支持更自然。单个 `SKILL.md` 本身就是原子复用单元，而 `.claude/commands/build.md` 这类 wrapper 又天然提供串联入口。
- 配套资产更完整。`references/agent-skills-main/.claude/commands/*.md`、`references/agent-skills-main/agents/*.md`、`references/agent-skills-main/hooks/session-start.sh` 一起降低了“先用哪个 skill”的心智负担。
- 更像产品包而不是仓库内部协议。对外接入与选择性加载的边界，在 `README.md`、`docs/getting-started.md`、`docs/cursor-setup.md` 中相对清楚。

## `agent-skills-main` 的劣势与不应被高估的地方

- “会自动激活”不能被过度高估。它在 Claude Code plugin + hook 场景下更强，但在 Cursor 等其它宿主里，很多能力仍依赖手动加载或选择性粘贴。
- `references/agent-skills-main/AGENTS.md` 与实际仓库结构并不完全一致，不能把它当成唯一真实的 packaging ground truth。
- 它的 chaining 仍以 narrative 和 command wrapper 为主，而不是像 AHE 一样有状态机、合法节点集合和迁移表。
- 它在长期、多轮、带审批和带回流的交付链路上，约束力度仍明显弱于 AHE。

## `ahe-*` 当前的优势

- `ahe-workflow-router` 仍是非常强的 workflow kernel。它已经明确 profile、合法节点集合、恢复编排、连续执行、pause point 和迁移来源。参见 `skills/ahe-workflow-router/SKILL.md`。
- reviewer subagent 协议已经开始成体系落地。`skills/ahe-workflow-router/references/review-dispatch-protocol.md` 和 `skills/ahe-workflow-router/references/reviewer-return-contract.md` 是本轮最重要的结构增强之一。
- AHE 不再只是“只能串联调用”。上游节点通过“先回 router 路由”的硬性门禁明确了 direct invoke 的 fallback；部分质量节点又允许手动补充性调用。这说明 AHE 已开始形成双模式能力。
- 实现节点依然清晰。`skills/ahe-test-driven-dev/SKILL.md` 作为唯一实现入口，仍然把实现、fresh evidence 和 handoff 统一在一个节点上。
- gate authority 依然强。`skills/ahe-regression-gate/SKILL.md` 与 `skills/ahe-completion-gate/SKILL.md` 明确指出它们当前不走 reviewer subagent 协议，保留 gate judgement 的主会话 authority，这对 AHE 是合理的设计。
- 分支模型和收尾模型仍然很强。`skills/ahe-hotfix/SKILL.md`、`skills/ahe-increment/SKILL.md` 与 `skills/ahe-finalize/SKILL.md` 让 workflow family 的边界比一般 skill pack 更完整。

## `ahe-*` 当前的劣势

- 双模式能力已经出现，但还没有被统一表达。当前很多 skill 还没有显式的 `standalone contract` / `chain contract` 段落，家族 contract 仍需要进一步落地。
- 模板层的 canonical schema 已开始收敛，但 live skills 与 reviewer / gate 输出还没有全部围绕这套 schema 统一。
- router 仍然偏重。虽然 collateral docs 增加了，但 `skills/ahe-workflow-router/SKILL.md` 本体仍然承载了大量规则与解释。
- router collateral 的关键冲突已经开始修补，但 family 级解释层与 live skills 之间仍有进一步对齐空间。
- 家族级公共规则仍大量分散在 live skills 中重复出现，维护成本还没真正降下来。

## 谁更强，取决于目标

- 如果目标是“做一个可分发、低摩擦、跨宿主接入的通用 skill pack”，`agent-skills-main` 仍然更强。
- 如果目标是“在长期软件交付里严格控制阶段、证据、回流、审批和完成定义”，AHE 仍然更强。
- 如果目标是“把 AHE 打造成更成熟的个人 harness engineering 工作台”，现在最优路线已经不是“先证明双模式可不可做”，而是“把已经出现的双模式能力收敛成统一 contract”。

## 刷新后的借鉴重点

### `P0`

- 不再是“从零提出家族 anatomy”，而是“用已经出现的 anatomy / dual-mode 思路统一 live skills 的 contract”。
- 最高优先级结构问题从“是否支持 direct invoke”转为：
  - `templates/task-progress-template.md` 与 canonical schema 对齐
  - 把 `standalone contract` / `chain contract` 明确落到核心主链节点
  - 修正 router collateral 与 router 主文件之间的冲突
  - 继续把解释层下沉到 `references/`、`using-ahe-workflow` 与 `docs/`

### `P1`

- 重点从“是否抽元 skill”转为“如何为 direct invoke 与 chain invoke 提供更低摩擦、但不削弱 kernel 的入口说明”。
- `using-ahe-skills`、entrypoints docs、command conventions 依然值得做，但它们现在是“收敛入口心智”的工作，而不是“填补能力空白”。

### `P2`

- 对外化仍应延后，但现在已经可以提前把“单节点采用”和“整链采用”视为不同接入模式来规划。

## 不建议 AHE 直接照搬的方面

- 不建议把 AHE 的 direct invoke 目标理解成“任意节点都能像普通工具一样脱链运行”。AHE 的价值仍然来自 route-first、evidence-first 和 gate-first。
- 不建议为了更像 `agent-skills-main` 而弱化 `ahe-workflow-router` 的 authority。
- 不建议在当前 router collateral 还未对齐之前，过早增加更多 wrapper、hook 或 plugin 层。

## 一句话判断

- `agent-skills-main` 仍然胜在“像产品的 skill pack”。
- AHE 仍然胜在“像 workflow kernel”。
- 本轮更新后的关键变化是：AHE 已经开始具备“条件式独立调用 + 强约束串联调用”的双模式能力；下一步最关键的，不是再证明这个方向，而是把它统一成可维护的家族 contract。
