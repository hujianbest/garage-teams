# AHE Review 动作独立 Subagent 化优化方案

## 背景

当前 `ahe-*` workflow 中，`ahe-specify`、`ahe-design`、`ahe-tasks` 等主链 skill 会把下一步直接交给对应 review skill，但从编排语义上看，review 仍然更像“当前会话继续执行的下一步”，而不是“由独立 reviewer 在隔离上下文中完成的独立动作”。

这会带来三个问题：

1. review 容易继承产出阶段的思路污染，独立性不够。
2. 不同交付件虽然已经有不同 review skill，但缺少统一的“按交付件类型路由 review”的编排约定。
3. review 结果如何回传、何时由主会话继续处理真人确认、如何沉淀 review 工件，目前更多靠 skill 各自描述，缺少统一协议。

本方案的目标不是重写现有 review skill，也不是把 review 标准抽成一个大而全的新 skill，而是：

- 保留现有 `ahe-spec-review`、`ahe-design-review`、`ahe-tasks-review`、`ahe-test-review`、`ahe-code-review` 等 skill 的专业职责。
- 将所有 review 动作统一改为“由独立 subagent 执行”。
- 由编排层根据被检视交付件类型，路由到正确的 review skill。
- 让主会话只负责产出、触发 review、接收结论，以及在需要时处理真人确认。

## 推荐方案

推荐采用“统一 review-dispatch 编排模式 + 保留现有专业 review skill”的方案。

核心原则：

1. **review 由独立 reviewer subagent 执行**  
   主会话不直接在当前上下文里跑 review，而是构造 review request，交给独立 subagent。

2. **review skill 按交付件类型选择，不做大一统 review**  
   规格文档走 `ahe-spec-review`，设计文档走 `ahe-design-review`，任务计划走 `ahe-tasks-review`，测试资产走 `ahe-test-review`，代码实现走 `ahe-code-review`。

3. **主 skill 与 review skill 解耦**  
   主 skill 只知道“什么时候该发起哪类 review”，不再内联展开 review 判断细节。

4. **真人确认留在主会话**  
   对于 `ahe-spec-review`、`ahe-design-review` 这类“review 通过后还需要真人确认”的场景，subagent 只负责评审与落盘；真人确认仍由父会话继续处理。

## 建议的目标编排

### 1. 角色分层

建议把 review 相关职责明确拆成三层：

| 层级 | 职责 | 是否新增 |
| --- | --- | --- |
| 主 workflow skill | 产出交付件、决定何时发起 review、处理真人确认和后续路由 | 否，后续按需改造 |
| review dispatcher 约定 | 根据交付件类型选择 review skill，组装 subagent 输入与回传协议 | 是，建议先以文档/参考说明落地 |
| 专业 review skill | 执行具体评审标准并生成 review 记录 | 否，复用现有 `ahe-*review` |

这里的重点是：**新增的是编排约定，不是新增一个替代现有 review skill 的“总评审 skill”。**

### 2. review 路由矩阵

建议先采用下面这张最小可用映射表：

| 被检视交付件 | 触发阶段 | subagent 内部调用的 skill | subagent 最小输入 |
| --- | --- | --- | --- |
| 需求规格文档 | `ahe-specify` 产出草稿后 | `ahe-spec-review` | 规格文档路径、主题、必要上下文 |
| 设计文档 | `ahe-design` 产出草稿后 | `ahe-design-review` | 设计文档路径、已批准规格路径、必要上下文 |
| 任务计划 | `ahe-tasks` 产出草稿后 | `ahe-tasks-review` | 任务计划路径、相关设计/规格路径 |
| 测试资产 | `ahe-test-driven-dev` 的测试完成后 | `ahe-test-review` | 测试文件范围、实现范围、fail-first 证据 |
| 代码实现 | 测试评审通过后 | `ahe-code-review` | diff/实现范围、相关测试、相关规格/设计/任务上下文 |

后续如需扩展，可继续加入：

- 追溯性资产 → `ahe-traceability-review`
- 回归门禁证据 → `ahe-regression-gate`
- 完成态证据 → `ahe-completion-gate`

### 3. review request 协议

建议未来在 AHE 内部统一一份 reviewer subagent 输入协议，至少包含：

| 字段 | 说明 |
| --- | --- |
| `review_type` | review 类型，如 `spec`、`design`、`tasks`、`test`、`code` |
| `review_skill` | 实际调用的 AHE review skill 名称 |
| `artifact_paths` | 被检视交付件路径 |
| `supporting_context_paths` | 允许 subagent 读取的最小辅助上下文路径 |
| `expected_record_path` | review 记录预期落盘路径 |
| `topic` | 本次 review 主题/任务名 |
| `return_contract` | subagent 需要回传的结构化结果 |

建议 `return_contract` 固定为：

```json
{
  "conclusion": "通过 | 需修改 | 阻塞",
  "next_action": "下一步 skill 或动作",
  "record_path": "评审记录路径",
  "key_findings": ["关键发现 1", "关键发现 2"],
  "needs_human_confirmation": true
}
```

其中：

- `needs_human_confirmation` 对 `spec/design` 类 review 通常为 `true`
- `test/code` 类 review 通常为 `false`

## 推荐的执行时序

建议未来所有 review 都收敛到如下固定时序：

1. 主 skill 完成交付件草稿并落盘。
2. 主 skill 根据交付件类型计算 `review_type` 和 `review_skill`。
3. 主 skill 构造最小 review request。
4. 主 skill 启动独立 reviewer subagent。
5. reviewer subagent 在自己的 fresh context 中读取目标交付件与必要辅助上下文。
6. reviewer subagent 显式读取并遵循对应的 `ahe-*review` skill。
7. reviewer subagent 生成 review 结论并把记录落到 `docs/reviews/...`。
8. reviewer subagent 按约定回传结构化摘要。
9. 父会话根据摘要继续：
   - 若需真人确认，则进入真人确认流程。
   - 若需修改或阻塞，则回到相应产出 skill 继续迭代。
   - 若通过且无需真人确认，则进入下一阶段。

这个时序的关键收益是：**review 的判断发生在隔离上下文中，workflow 的推进发生在父会话中。**

## 为什么不建议直接做成一个总 review skill

不建议把所有 review 合并成一个“万能 review skill”，原因有三点：

1. 现有 `ahe-*review` 已经按交付件类型沉淀了不同检查清单和门禁规则，直接合并会稀释专业性。
2. `spec/design/tasks/test/code` 的输入边界、判定规则、输出结构虽然相似，但关注点明显不同。
3. 真正缺的不是“再写一套 review 标准”，而是“统一的 review 调度协议与独立执行边界”。

因此推荐的改造方向是：

- **保留 review skill 的垂直专业性**
- **新增 review 调度的一致性**

## 对 AHE 主链的影响建议

本轮不改 skill 内容，但从后续实施角度看，建议优先改造以下位置：

### 第一批

- `skills/ahe-specify/SKILL.md`
- `skills/ahe-design/SKILL.md`
- `skills/ahe-tasks/SKILL.md`

这三者最适合先落地，因为它们已经天然形成“产出文档 -> review -> 下一阶段”的明确链路。

### 第二批

- `skills/ahe-test-driven-dev/SKILL.md`
- `skills/ahe-hotfix/SKILL.md`
- `skills/ahe-increment/SKILL.md`

这批更多涉及测试评审、代码评审，以及修订后重新进入 review 的循环编排。

### 第三批

- `skills/ahe-workflow-starter/SKILL.md`
- 质量门禁相关 skill

这里主要负责把“review 动作用独立 subagent 执行”提升为 workflow 级别共识，而不只是个别 skill 的局部约定。

## 建议的落地顺序

### Phase 0：先补文档约定

先新增一份共享参考文档，定义：

- review 路由矩阵
- reviewer subagent 输入/输出协议
- 父会话与 reviewer 的职责边界

这样后续修改 skill 时可以统一引用，避免每个 skill 各写一套。

### Phase 1：先改文档型 review 链

优先把：

- `ahe-specify -> ahe-spec-review`
- `ahe-design -> ahe-design-review`
- `ahe-tasks -> ahe-tasks-review`

改成 subagent 方式。因为这些链路输入稳定、输出是文档、验证成本最低。

### Phase 2：再改实现型 review 链

把：

- `ahe-test-review`
- `ahe-code-review`

接入同一 dispatch 方式，并补齐测试证据、diff 范围、相关规格/设计上下文的传递协议。

### Phase 3：最后统一门禁与回传格式

让所有 review 型动作都输出统一摘要字段，便于：

- workflow-starter 识别下一步
- task-progress 或等价记录同步
- 后续做 review 轨迹统计或质量门禁自动判断

## 风险与注意事项

### 1. 不要把父会话上下文整包灌给 subagent

review 独立性的价值，来自“只给最小必要输入”。如果把整个会话上下文、所有历史推理和无关文件都给 reviewer，独立性会被抵消。

### 2. 不要让 reviewer subagent 负责真人确认

`ahe-spec-review` 和 `ahe-design-review` 都强调“review 通过不等于自动批准”。因此 reviewer 只负责评审结论，不负责代替父会话向真人发起批准确认。

### 3. 不要把 review 记录落盘责任继续留给父会话

既然 review 是 subagent 独立完成，最合理的做法是让 reviewer 自己按 skill 要求把记录写入 `docs/reviews/...`，而父会话只消费结果。

### 4. 不要把不同 review 的标准抽象得过早

可以统一协议，但不要急着统一检查清单。`spec/design/tasks/test/code` 的 review 语义差异是真实存在的，应该保留。

## 参考了哪些方案

本方案主要参考了 `docs/skills_refer.md` 中以下几类实现：

1. **`references/superpowers-main/skills/requesting-code-review/SKILL.md`**  
   参考点：明确要求把 code review 交给独立 reviewer subagent，并且只传入精心裁剪的上下文，而不是沿用主会话上下文。  
   借鉴结论：AHE 的 review 应强调“独立执行边界”和“最小必要输入”。

2. **`references/longtaskforagent-main/skills/long-task-work/SKILL.md`**  
   参考点：主 orchestrator 不直接做所有步骤，而是把特定阶段交给 sub-skill / subagent，并约束输入为路径与结构化摘要。  
   借鉴结论：AHE 可以采用“主链负责编排，专业 skill 负责执行”的模式，review 也应如此。

3. **`references/gstack-main/plan-eng-review/SKILL.md`**  
   参考点：plan 评审是独立的专业 review 阶段，强调评审结果记录、review dashboard、review chaining，以及必要时引入 outside voice。  
   借鉴结论：AHE 的 review 不只是“给几条建议”，而应是 workflow 中可回传、可衔接下一步的正式阶段。

4. **`references/gstack-main/plan-design-review/SKILL.md`**  
   参考点：按交付件类型做专业化 review，而不是把所有评审塞进一个统一流程。  
   借鉴结论：AHE 应继续保留 `spec/design/tasks/...` 分型 review，而不是合成一个通用 review skill。

5. **`references/gstack-main/review/SKILL.md`**  
   参考点：代码评审按 diff 范围执行，且可以串联条件性二次 review（例如 design review lite、adversarial review），输出结构化结论。  
   借鉴结论：AHE 后续在 `ahe-code-review` 上可以进一步演进为“主代码评审 + 条件性补充评审”的扩展模式，但第一步先完成 reviewer subagent 化。

## 建议结论

建议采纳以下方向作为后续改造基线：

1. 所有 AHE review 动作一律改为由独立 reviewer subagent 执行。
2. 保留现有 `ahe-*review` skill，不新增替代它们的大一统 review skill。
3. 新增统一的 review dispatch 协议，用“交付件类型 -> review skill”做路由。
4. review 记录由 reviewer subagent 负责落盘，父会话负责消费结论与推进下一步。
5. 文档型 review 链先改，测试/代码/门禁类 review 后改。

如果按“收益 / 改造成本”排序，最值得先做的是：

1. 先补一份共享 review-dispatch 约定文档。
2. 先把 `ahe-specify`、`ahe-design`、`ahe-tasks` 三条文档主链接上独立 reviewer subagent。
3. 再把 `ahe-test-review`、`ahe-code-review` 纳入同一协议。
