---
name: ahe-bug-patterns
description: 基于团队历史错误案例和常见缺陷模式，对当前改动做专项排查。适用于 full / standard profile 中实现完成后的首个质量节点、热修复后需要做复发模式检查、或改动涉及边界、状态、时序、幂等、资源释放、配置读取等高风险区域的场景。本 skill 产出结构化 defect-pattern findings 与下游 handoff，不替代 `ahe-test-review`、`ahe-code-review` 或 `ahe-regression-gate`。
---

# AHE 缺陷模式排查

基于已知错误模式，对当前改动做专项风险排查。

在完整 AHE workflow 中，它通常作为 full / standard 实现后的首个质量能力。

## 角色定位

这个 skill 用于把团队已经吃过的亏，转成当前任务可以执行的检查动作。

它不是通用代码评审的替代品，而是对高频错误类型的定向补强。

## 与 AHE 主链的关系

- 在 full / standard profile 中，通常位于 `ahe-test-driven-dev` 之后、`ahe-test-review` 之前
- 在 lightweight profile 中，`ahe-workflow-starter` 默认跳过本节点；若用户显式要求或团队规则要求手动运行，应把它视为 out-of-band 补充分析，而不是改写 workflow canonical state 的正式节点
- 本 skill 重点产出 pattern-driven findings，不替代后续 `ahe-test-review`、`ahe-code-review` 或 `ahe-regression-gate`
- 若发现问题需要回到实现修订，应把下一步明确写回 `ahe-test-driven-dev`

## 高质量排查基线

高质量的 `ahe-bug-patterns` 结果，至少应满足：

- 先消费上游实现交接块，而不是脱离改动上下文做空泛检查
- 不只说“这里有风险”，还要说清模式、机制、证据锚点、严重级别和扩散面
- 对重要发现给出回归假设和建议证伪方式，但不越权去跑完整 regression gate
- 输出能直接被 `ahe-test-review`、`ahe-code-review` 或 `ahe-regression-gate` 继续消费

## 适用时机

优先用于以下场景：

- 需要对当前改动做一轮高风险专项排查
- 当前任务刚完成最小实现，准备进入正式评审链
- 当前改动涉及边界、状态、时序、幂等、资源释放、配置读取等高风险区域
- 当前任务属于热修复或缺陷复发区域
- 团队已有类似错误案例，且本次改动命中相同风险类别

## 输入

阅读以下最少必要信息：

- 当前改动涉及的实现与测试变更
- `ahe-test-driven-dev` 的实现交接块或等价记录
- 与当前改动相关的需求、设计或任务背景（如有）
- 团队已知错误案例、事故复盘或缺陷模式清单（如有）

如果当前上下文无法提供完整规格或任务文档，至少应提供当前改动范围、目标行为、本次排查关注点，以及上游实现已经证明了什么。

## Pre-flight

开始排查前，至少固定：

- 当前任务 ID
- 触碰工件 / 关键 diff 面
- 上游实现交接块中的 RED / GREEN 证据摘要
- 当前 profile

如果缺少团队历史 pattern catalog，不要因此放弃排查；应明确记录“当前仅使用通用 defect families”。

## 记录要求

排查完成后，必须将本次结论写入：

- `docs/reviews/bug-patterns-<task>.md`

如 `AGENTS.md` 为当前项目声明了等价路径，按其中映射路径保存。

若项目尚未形成固定 review 记录格式，默认使用：

- `templates/review-record-template.md`

如果当前任务正在使用 `task-progress.md` 驱动 workflow，且当前 profile 是 full / standard，应同步更新：

- `task-progress.md` 中的缺陷模式排查状态
- 当前任务是否需要回到实现修订，还是可以进入 `ahe-test-review`
- 当前阻塞原因或待处理风险（如有）

若项目尚未形成固定进度记录格式，默认使用：

- `templates/task-progress-template.md`

## 参考资料

如果团队还没有成型的缺陷模式库，可先使用以下模板初始化：

- 当前 skill 目录下的 `references/bug-pattern-catalog-template.md`

## 与下游节点的边界

- `ahe-test-review` 负责一般测试质量与 fail-first 裁决；本 skill 只提出 pattern-linked 的测试补强建议
- `ahe-code-review` 负责更广泛的实现质量判断；本 skill 不做泛泛代码风格检查
- `ahe-regression-gate` 负责更广义的验证执行与 gate 结论；本 skill 只提出回归假设和建议证伪方式

## 结构化排查方法

### 1. 先消费上游实现证据

先回答：

- 当前任务改了哪些工件
- 上游已经证明了哪些行为
- 当前尚未被证明的高风险区域有哪些

### 2. 用结构化 taxonomy 记录命中模式

每个命中模式至少写清：

- Pattern ID / 名称
- 机制
- 证据锚点
- 严重级别
- 重复性：重复缺陷 | 近似缺陷 | 新风险
- 置信度：demonstrated | probable | weak-signal

### 3. 必查模式族

#### 历史重复缺陷

- 当前改动是否命中团队历史高频错误模式？
- 是否只是修掉症状，而没有处理同类缺陷机制？

#### 通用编码风险

- 是否存在边界值、空值、默认值处理缺口？
- 是否存在状态切换、时序依赖、重入、幂等等风险？
- 是否存在资源释放、异常恢复、配置误用等问题？

#### AI-assisted blind spots

- 是否存在主路径修了、旁支路径没修的双路径不一致？
- 是否存在跨层传播不完整，导致一层修了、另一层状态仍旧过期？
- 是否存在“实现看起来完成了，但保护性分支或错误路径没被同步更新”的情况？

#### 防护是否足够

- 这些风险是否被测试覆盖？
- 是否有必要补充保护性判断、断言、降级逻辑或约束说明？

#### 扩散面与回归假设

- 当前缺陷模式是否可能在相邻模块中重复出现？
- 若要证伪这个担忧，最适合补哪类测试、检查哪类路径、或运行哪类验证？

## 检查清单

- 不要跳过上面的结构化记录要求
- 不要把 checklist 当成最终输出；它只是发现模式的辅助视角

## 输出格式

请严格使用以下结构：

```markdown
## 结论

通过 | 需修改 | 阻塞

## 上游已消费证据

- Task ID
- 实现交接块 / 等价证据
- 触碰工件

## 命中的缺陷模式（结构化）

- Pattern ID / 名称
- 机制
- 证据锚点
- 严重级别
- 重复性
- 置信度

## 缺失的防护

- 条目

## 回归假设与扩散面

- 假设
- 建议证伪方式

## 下一步

`ahe-test-review` | `ahe-test-driven-dev`

## 记录位置

- `docs/reviews/bug-patterns-<task>.md` 或映射路径
```

## 判定规则

只有当当前改动涉及的主要缺陷模式已经被识别，且风险有相应测试、保护措施或合理说明时，才返回 `通过`。

如果命中了已知高风险模式，但缺少必要防护、测试或修正，则返回 `需修改`。

如果当前排查连最基本的改动面、上游实现证据或关键风险类别都无法判定，则返回 `阻塞`。

full / standard 中，本 skill 返回 `通过` 后进入 `ahe-test-review`，返回 `需修改` / `阻塞` 时回到 `ahe-test-driven-dev`。

lightweight 手动调用时，应把本次结果视为补充性分析：可以记录发现，但不要改写 workflow canonical `Next Action Or Recommended Skill`。

## 反模式

- 把这个 skill 变成泛泛而谈的代码评审
- 只列风险，不说明是否已被覆盖
- 明知命中历史缺陷模式，却不补测试或防护
- 只检查单点，不考虑同类问题是否扩散
- 不读取上游实现交接块，就直接“按经验”排查
- 把回归建议当成已经完成的 regression gate

## 完成条件

排查结论必须写入仓库中的评审记录路径。可以在对话中摘要结论，但对话不能替代记录工件。

只有在排查记录已经落盘，且给出明确结论、命中模式、缺失防护和唯一下一步之后，这个 skill 才算完成。
