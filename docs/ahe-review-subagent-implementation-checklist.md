# AHE Review Subagent 化实施清单

## 目的

这份清单是 `docs/ahe-review-subagent-optimization-plan.md` 的下一步落地文档。

它不直接修改任何 `ahe-*` skill，而是把后续真正动手时需要改哪些 skill、每个 skill 要改什么、哪些先做、哪些后做，整理成一份可执行的实施清单。

目标不是重新设计整个 AHE workflow，而是把以下能力稳定落地：

1. review 动作统一由独立 reviewer subagent 执行
2. reviewer subagent 根据交付件类型调用对应 review skill
3. 父会话只负责产出、派发 review、消费结论和推进主链
4. spec / design 类真人确认仍留在父会话，不下放给 reviewer

## 本轮实施边界

### 必须实现

- 文档型 review 链的 subagent 化
- review skill 的按交付件类型路由
- reviewer subagent 与父会话之间的最小输入 / 输出协议
- 父会话与 reviewer 的职责分离

### 暂不强求

- 一次性把所有 gate 节点都改成 subagent 化
- 引入复杂的 review dashboard、review telemetry 或多 reviewer 并行裁决
- 新增一个替代现有 `ahe-*review` 的总 review skill

## 目标状态

建议把 review 动作未来统一收敛到下面这个执行模型：

```text
产出 skill
  -> 保存交付件
  -> 构造 review request
  -> 启动 reviewer subagent
      -> 读取对应 ahe-*review skill
      -> 读取最小必要工件
      -> 执行评审
      -> 写 review 记录
      -> 回传结构化摘要
  -> 父会话消费摘要
      -> 若通过且需真人确认：进入真人确认
      -> 若通过且无需真人确认：进入下一节点
      -> 若需修改 / 阻塞：回到相应上游 skill
```

其中最关键的一点是：

- **评审判断在 reviewer subagent 中发生**
- **workflow 推进在父会话中发生**

## 共享协议清单

后续真正修改 skill 前，建议先以共享约定的方式固定以下协议。

### 1. review 路由协议

先固定一张最小可用映射表：

| 交付件类型 | 触发节点 | reviewer subagent 使用的 skill |
| --- | --- | --- |
| spec 文档 | `ahe-specify` 产出后 | `ahe-spec-review` |
| design 文档 | `ahe-design` 产出后 | `ahe-design-review` |
| tasks 文档 | `ahe-tasks` 产出后 | `ahe-tasks-review` |
| test 资产 | `ahe-test-driven-dev` 后的质量链 | `ahe-test-review` |
| code 实现 | `ahe-test-review` 通过后 | `ahe-code-review` |
| traceability 证据链 | `ahe-code-review` 通过后 | `ahe-traceability-review` |

第一阶段先覆盖前五类即可，`traceability` 可一起做，也可以放入第二批。

### 2. reviewer 输入协议

建议 future caller skills 统一构造如下输入：

```json
{
  "review_type": "spec|design|tasks|test|code|traceability",
  "review_skill": "ahe-xxx-review",
  "topic": "本次交付主题",
  "artifact_paths": ["被检视交付件路径"],
  "supporting_context_paths": ["最小必要辅助上下文路径"],
  "expected_record_path": "docs/reviews/... 或映射路径",
  "current_profile": "full|standard|lightweight",
  "return_contract": "fixed"
}
```

### 3. reviewer 输出协议

建议所有 reviewer subagent 至少回传：

```json
{
  "conclusion": "通过|需修改|阻塞",
  "next_action": "推荐下一步 skill 或动作",
  "record_path": "实际写入的记录路径",
  "key_findings": [
    "关键发现 1",
    "关键发现 2"
  ],
  "needs_human_confirmation": false,
  "reroute_via_starter": false
}
```

补充约定：

- `needs_human_confirmation=true` 主要用于 `ahe-spec-review`、`ahe-design-review`
- `reroute_via_starter=true` 用于 reviewer 发现当前不是简单回修，而是需要重新编排的情况

### 4. 职责边界协议

必须固定以下边界：

| 角色 | 负责什么 | 不负责什么 |
| --- | --- | --- |
| 父会话 | 产出、派发 review、真人确认、状态推进 | 不直接执行评审判断 |
| reviewer subagent | 执行评审、写记录、回传摘要 | 不推进主链、不代替真人确认 |
| review skill | 定义评审标准和记录要求 | 不决定整个 workflow 下一阶段 |

## 实施顺序

建议按四批推进，而不是一次性改全链路。

### Batch 1：先改 review 调度入口

优先修改：

- `skills/ahe-workflow-starter/SKILL.md`
- `skills/ahe-specify/SKILL.md`
- `skills/ahe-design/SKILL.md`
- `skills/ahe-tasks/SKILL.md`

原因：

- 这几处最直接决定“review 是内联执行还是独立 subagent 执行”
- 它们控制了最清晰的文档主链
- 改完后马上能验证 `spec -> review -> human confirm -> next stage` 这条核心路径

### Batch 2：再改 review skill 自身契约

优先修改：

- `skills/ahe-spec-review/SKILL.md`
- `skills/ahe-design-review/SKILL.md`
- `skills/ahe-tasks-review/SKILL.md`
- `skills/ahe-test-review/SKILL.md`
- `skills/ahe-code-review/SKILL.md`
- `skills/ahe-traceability-review/SKILL.md`

原因：

- caller skill 知道要派 subagent 以后，review skill 也要明确“自己运行在 reviewer 上下文中”
- 否则 review skill 仍会隐式假设自己在父会话里运行

### Batch 3：再接实现链与支线

优先修改：

- `skills/ahe-test-driven-dev/SKILL.md`
- `skills/ahe-hotfix/SKILL.md`
- `skills/ahe-increment/SKILL.md`

原因：

- 它们负责把实现结果送进后续 review / gate 链
- 需要知道哪些 review 动作已经不是“当前会话直接做”，而是“交给 reviewer subagent”

### Batch 4：最后考虑 gate 类动作是否同样 subagent 化

视实际收益决定是否继续改：

- `skills/ahe-regression-gate/SKILL.md`
- `skills/ahe-completion-gate/SKILL.md`

建议先观察前 3 批落地后的收益，再决定 gate 是否也统一改成独立 verifier subagent。

原因：

- gate 和 review 很像，但不完全一样
- 当前用户的明确要求聚焦于 review 动作，gate 可以后置

## Skill 级实施清单

下面按 skill 列出建议修改点。

### 1. `skills/ahe-workflow-starter/SKILL.md`

这是最关键的入口改造点。

#### 必改项

- 在“路由顺序”或“后续编排规则”中明确：当下一节点是 review 节点时，执行方式不是“父会话内联进入 review skill”，而是“启动 reviewer subagent，并在 subagent 中调用对应 review skill”
- 增加一段“review dispatch 规则”，说明如何根据节点名映射到 review skill
- 增加一段“review 结果回收规则”，说明如何消费 `conclusion`、`next_action`、`needs_human_confirmation`、`reroute_via_starter`
- 在“暂停点”说明中保留 spec/design 的真人确认逻辑，但改成“reviewer 返回通过后，由父会话触发真人确认”

#### 建议新增的小节

- `## Review Dispatch Protocol`
- `## Reviewer Return Contract`
- `## Human Confirmation Ownership`

#### 不该改的部分

- workflow profile 选择逻辑
- 合法状态集合
- 主链迁移表的大结构

#### 完成标准

- starter 可以明确区分“进入执行 skill”和“派发 review subagent”
- starter 不会再把 review skill 当成普通下游 skill 直接内联执行

### 2. `skills/ahe-specify/SKILL.md`

这是文档型 review subagent 化的第一条主链。

#### 必改项

- 在交付阶段把“直接交给 `ahe-spec-review`”改成“构造 spec review request 并启动 reviewer subagent”
- 明确父会话在 review 返回后只做两件事：
  - `通过` -> 向真人展示 review 结论并请求批准
  - `需修改/阻塞` -> 根据 reviewer 返回的问题清单继续修订
- 更新 handoff 文案，避免误导成“下一步当前会话直接执行 `ahe-spec-review`”

#### 建议新增的小节

- `## 交给 Reviewer Subagent`
- `## Review 返回后的父会话职责`

#### 不该改的部分

- 规格澄清协议主体
- 规格骨架
- 规格自检逻辑

#### 完成标准

- `ahe-specify` 自己不再执行 spec review 判断
- 它只负责产出 spec、派发 review、处理 review 回流和真人确认

### 3. `skills/ahe-design/SKILL.md`

与 `ahe-specify` 类似，但下游是 design review。

#### 必改项

- 把“准备好之后，交给 `ahe-design-review`”改成“启动 reviewer subagent 执行 `ahe-design-review`”
- 保留“design-review 通过后仍需真人确认”的规则，但明确真人确认归父会话所有
- 在回修路径里，使用 reviewer 返回的结构化发现项，而不是泛化地“回到设计修订”

#### 建议新增的小节

- `## Design Review Dispatch`
- `## Human Approval After Review`

#### 不该改的部分

- 设计驱动因素提取
- 候选方案比较 / 决策记录
- 设计骨架与视图要求

#### 完成标准

- design review 执行边界与 human approval 边界清晰分离

### 4. `skills/ahe-tasks/SKILL.md`

这是第三条文档型主链。

#### 必改项

- 把“任务计划准备好后，交给 `ahe-tasks-review`”改成“派发 reviewer subagent 执行 `ahe-tasks-review`”
- 明确 `ahe-tasks` 在 review 返回后如何处理：
  - `通过` -> 进入 `ahe-test-driven-dev`
  - `需修改/阻塞` -> 回到任务修订
- 在 handoff 文案里，区分“推荐 review 节点”与“实际执行方式是 subagent”

#### 建议新增的小节

- `## Tasks Review Dispatch`
- `## Tasks Review Return Handling`

#### 不该改的部分

- 任务拆解方法
- 里程碑与 active task 规则

#### 完成标准

- `ahe-tasks` 不再把 `ahe-tasks-review` 当父会话内联步骤

### 5. `skills/ahe-spec-review/SKILL.md`

这是第一批 review skill 中最需要补“subagent 运行语义”的一个。

#### 必改项

- 在角色定位里明确：本 skill 预期运行在独立 reviewer subagent 中
- 增加一条规则：本 skill 负责写 review 记录和回传结构化摘要，但不负责发起真人批准确认
- 在输出格式后补充“父会话回传摘要格式”说明

#### 建议新增的小节

- `## Reviewer Subagent 运行约定`
- `## 回传给父会话的摘要`

#### 不该改的部分

- spec review 的判断标准
- `通过 / 需修改 / 阻塞` 的定义
- 记录落盘要求

#### 完成标准

- 这个 skill 从文义上不再隐含“自己会继续带着用户推进下一阶段”

### 6. `skills/ahe-design-review/SKILL.md`

和 spec review 同理。

#### 必改项

- 明确该 skill 运行于 reviewer subagent
- 明确它不负责真人确认
- 增加结构化回传摘要要求

#### 不该改的部分

- 设计评审检查清单
- 设计通过后的真人确认规则本身

#### 完成标准

- review 与批准在职责上彻底分离

### 7. `skills/ahe-tasks-review/SKILL.md`

这是最容易落地的 review skill。

#### 必改项

- 明确 reviewer subagent 语义
- 增加结构化回传摘要格式
- 明确 reviewer 只返回结论和下一步，不直接重排整个 workflow

#### 不该改的部分

- 任务粒度 / 顺序 / 可验证性标准

#### 完成标准

- 任务评审结果可被父会话机械消费

### 8. `skills/ahe-test-driven-dev/SKILL.md`

这个 skill 本身不是 review skill，但它是后续 review 链的上游生产者。

#### 必改项

- 在“实现交接块”或 handoff 章节中，明确后续 `ahe-test-review` / `ahe-code-review` 等质量判断由独立 reviewer subagent 执行
- 若当前是回流修订，再进入下游 review 时，也应按“重派 reviewer subagent”处理，而不是默认当前会话接着 review

#### 建议新增的小节

- `## 下游 Review Dispatch 约定`

#### 不该改的部分

- 活跃任务锁定
- 测试设计确认
- TDD 红绿重构主体

#### 完成标准

- 实现交接块可以直接喂给后续 reviewer subagent

### 9. `skills/ahe-test-review/SKILL.md`

这是实现链中的第一层 reviewer。

#### 必改项

- 明确运行于 reviewer subagent
- 增加“输入中应包含 fail-first 证据、测试范围、实现范围”的显式要求
- 增加结构化回传摘要格式

#### 不该改的部分

- fail-first、行为价值、覆盖形态等检查标准

#### 完成标准

- 测试评审可被 `ahe-workflow-starter` 或父会话机械消费，并决定是否进入 `ahe-code-review`

### 10. `skills/ahe-code-review/SKILL.md`

这是实现链中的第二层 reviewer。

#### 必改项

- 明确运行于 reviewer subagent
- 增加“最小输入要求”说明：实现范围、相关测试、相关规格/设计/任务锚点
- 增加结构化回传摘要格式

#### 不该改的部分

- 正确性 / 设计一致性 / 可维护性 / 错误处理等检查标准

#### 完成标准

- code review 可以作为独立 reviewer，被父会话稳定重用

### 11. `skills/ahe-traceability-review/SKILL.md`

这个 skill 很适合一起纳入 reviewer subagent 模式。

#### 必改项

- 明确它是 evidence-chain reviewer，而不是父会话中的普通顺序步骤
- 明确当发现“需要重新编排”的问题时，如何用 `reroute_via_starter=true` 回传
- 增加结构化回传摘要格式

#### 不该改的部分

- 链路矩阵
- 追溯缺口 / 漂移风险检查维度

#### 完成标准

- traceability review 的阻塞结论能区分“回实现修订”与“回 starter 重编排”

### 12. `skills/ahe-hotfix/SKILL.md`

它本身不做 review，但必须知道后续 review 已经变成 subagent 化。

#### 必改项

- 明确交接给 `ahe-test-driven-dev` 后，后续 review / gate 将由父会话按 workflow 恢复，不在 hotfix 内联完成
- 若 hotfix 输出中涉及 review 预期，也改成“由 downstream reviewer subagent 消费”

#### 不该改的部分

- hotfix / increment 判别
- 复现、root cause、最小修复边界

#### 完成标准

- hotfix 不再暗示 review 会在当前会话继续顺手完成

### 13. `skills/ahe-increment/SKILL.md`

与 hotfix 类似，主要是 handoff 契约层面的适配。

#### 必改项

- 在状态回流部分补充：若下一阶段是 review 节点，执行方式为 reviewer subagent
- 若 increment 导致旧 review 结论失效，明确要求重新派发对应 reviewer，而不是口头承认“需要重审”

#### 不该改的部分

- 变更包与影响矩阵
- 失效项标记逻辑

#### 完成标准

- increment 结束后，后续 review 重跑方式是明确的，不依赖隐含理解

### 14. `skills/ahe-regression-gate/SKILL.md`

这个节点建议放到第二阶段再决定是否 subagent 化。

#### 第一阶段建议

- 暂不强制改为 subagent
- 先只补一句兼容性说明：若后续全链路统一 verifier subagent 化，本 skill 可平移到 verifier 执行

#### 为什么暂缓

- 用户当前要求更聚焦于 review 动作
- gate 的输入输出协议与 review 相近，但仍有额外验证运行语义

### 15. `skills/ahe-completion-gate/SKILL.md`

与 `ahe-regression-gate` 相同。

#### 第一阶段建议

- 暂不强制 subagent 化
- 先观察 review subagent 化后的链路是否已经足够清晰

## 文档落地建议

如果后续要真的开始改 skill，建议先补两类共享文档，而不是一上来直接 scattered edits。

### 建议新增的共享文档

- `skills/references/review-dispatch-protocol.md`
- `skills/references/reviewer-return-contract.md`

如果不想放进 `skills/`，也可以先放到 `docs/`，但长期看更适合作为 workflow 家族共享参考资料。

### 这两份文档至少应包含

- review 路由矩阵
- reviewer 输入协议
- reviewer 输出协议
- 父会话 / reviewer / review skill 的职责边界
- spec/design 真人确认归属说明

## 最小验收标准

当第一阶段真正改完时，至少应能满足以下验收标准：

1. `ahe-specify` 产出规格后，不在父会话内联执行 spec review，而是派发 reviewer subagent。
2. `ahe-design` 产出设计后，不在父会话内联执行 design review，而是派发 reviewer subagent。
3. `ahe-tasks` 产出任务计划后，不在父会话内联执行 tasks review，而是派发 reviewer subagent。
4. `ahe-spec-review` 和 `ahe-design-review` 通过后，真人确认仍由父会话执行。
5. reviewer subagent 至少能统一返回 `conclusion`、`next_action`、`record_path`、`key_findings`。
6. `ahe-workflow-starter` 能识别“review 节点 = 派发 reviewer”而不是“直接进入 review skill”。

## 推荐的实施顺序

如果只做最小闭环，建议按下面顺序开工：

1. 先改 `ahe-workflow-starter`
2. 再改 `ahe-specify` + `ahe-spec-review`
3. 再改 `ahe-design` + `ahe-design-review`
4. 再改 `ahe-tasks` + `ahe-tasks-review`
5. 再补 `ahe-test-driven-dev`、`ahe-test-review`、`ahe-code-review`
6. 最后再考虑 `ahe-traceability-review`、`ahe-regression-gate`、`ahe-completion-gate`

这个顺序的原因很简单：

- 先把入口和三条文档主链打通，最快获得稳定收益
- 再把实现链纳入
- gate 类动作最后评估是否值得继续统一

## 建议结论

下一步最值得做的，不是立刻散点改多个 skill，而是按以下顺序推进：

1. 以本清单为蓝本，先补共享的 review dispatch / return contract 参考文档。
2. 先完成 `starter + specify/design/tasks + 对应 review skill` 的第一阶段改造。
3. 第一阶段跑通后，再把 `test-review`、`code-review`、`traceability-review` 接入同一 reviewer subagent 模式。

这样可以在不重写 AHE 主链的前提下，把 review 独立性、路由一致性和后续可维护性一起拿到。
