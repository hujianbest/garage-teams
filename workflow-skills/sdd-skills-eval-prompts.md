# SDD Skills 演练 Prompt 集

这份文档用于验证当前 SDD skills 体系是否能在真实场景下正确触发、正确路由、并沿着预期流程推进。

重点不是测“能不能回答”，而是测：

- 是否先命中 `sdd-workflow-starter`
- 是否被正确路由到当前阶段 skill
- 是否会跳过应有门禁
- handoff 到下一 skill 时是否清晰

## 使用方式

每个测试场景都按下面方式执行：

1. 准备文档中要求的最小前置工件
2. 把“用户 prompt”原样输入给 Agent
3. 观察实际触发的 skill 与输出
4. 对照“期望行为”和“失败信号”判断是否通过

建议优先做 5 个场景，不要一次混跑。

## 评估维度

每个场景至少看这 5 项：

1. `starter` 是否优先触发
2. 当前阶段是否路由正确
3. 是否错误跳过 review / gate
4. 输出中是否明确指出当前阶段证据与下一 skill
5. 是否没有越权开始实现、设计或任务拆分

---

## 场景 1：全新需求进入规格阶段

### 前置工件

项目根目录下不存在：

- `workflow-state.json`
- `change-request.json`
- `hotfix-request.json`
- 已批准规格文档
- 已批准设计文档
- 已批准任务计划

### 用户 Prompt

```text
我们准备做一个内部发布审批系统。第一期只支持员工提交发布申请、直属主管审批、审批通过后通知申请人。先帮我开始推进这件事，后面会按你说的流程走。
```

### 期望命中

- 首先命中：`sdd-workflow-starter`
- 然后路由到：`sdd-work-specify`

### 期望行为

- 不直接进入设计或编码
- 明确说明当前没有 approved spec
- 开始围绕范围、角色、约束、验收标准做需求澄清

### 失败信号

- 直接输出系统架构方案
- 直接开始写数据库表或接口
- 不说明当前为什么进入 `work-specify`

---

## 场景 2：规格已通过，应该进入设计

### 前置工件

存在已批准规格，例如：

- `docs/specs/2026-03-26-release-approval-srs.md`

且文档里有：

- `Status: Approved`

不存在：

- 已批准设计文档
- `change-request.json`
- `hotfix-request.json`

### 用户 Prompt

```text
继续这个发布审批系统。需求规格已经确认过了，下一步该怎么走就怎么走。
```

### 期望命中

- 首先命中：`sdd-workflow-starter`
- 然后路由到：`sdd-work-design`

### 期望行为

- 读取 approved spec 作为设计输入
- 不回去重新做 requirements
- 不跳过设计直接做任务拆分
- 进入“提出 2-3 个实现方案并给推荐”的设计流程

### 失败信号

- 继续追问大量需求问题但不解释为什么
- 直接拆 milestones / tasks
- 直接进入实现

---

## 场景 3：设计和任务计划都已通过，应该进入实现

### 前置工件

存在并已批准：

- `docs/specs/2026-03-26-release-approval-srs.md`
- `docs/designs/2026-03-27-release-approval-design.md`
- `docs/tasks/2026-03-27-release-approval-tasks.md`

可选：

- `workflow-state.json` 中 `phase` 标记为 `implement`

不存在：

- `change-request.json`
- `hotfix-request.json`

### 用户 Prompt

```text
继续这个项目。按照已经确认好的任务计划，先做当前该做的那一项，不要自己扩 scope。
```

### 期望命中

- 首先命中：`sdd-workflow-starter`
- 然后路由到：`sdd-work-implement`

### 期望行为

- 明确说当前进入实现阶段
- 强调一次只处理一个 active task
- 先读取 task plan / progress / spec / design 中与当前任务有关的部分
- 实现后按顺序进入：
  `sdd-test-review -> sdd-code-review -> sdd-regression-gate -> sdd-completion-gate`

### 失败信号

- 同时做多个任务
- 没有 TDD 倾向，直接上实现
- 实现后直接宣称 done
- 跳过 review / regression / completion gate

---

## 场景 4：需求变更进入 increment 支线

### 前置工件

存在并已批准：

- requirement spec
- design doc
- task plan

且项目根目录新增：

- `change-request.json`

建议内容类似：

```json
{
  "reason": "增加需求",
  "change_type": "new-requirement",
  "summary": "审批通过后，需要自动抄送项目经理"
}
```

### 用户 Prompt

```text
需求有变化。审批通过以后，除了通知申请人，还要自动抄送项目经理。你按正确流程处理，不要直接偷偷改代码。
```

### 期望命中

- 首先命中：`sdd-workflow-starter`
- 然后路由到：`sdd-work-increment`

### 期望行为

- 先读 change request 和现有 spec / design / task plan
- 做 impact analysis
- 明确哪些工件需要更新
- 把下一步路由回 `sdd-spec-review`、`sdd-design-review` 或 `sdd-tasks-review`

### 失败信号

- 直接进 `sdd-work-implement`
- 只改任务计划，不回写 spec
- 默认认为旧批准仍然有效

---

## 场景 5：紧急缺陷进入 hotfix 支线

### 前置工件

主链工件已存在，项目根目录新增：

- `hotfix-request.json`

建议内容类似：

```json
{
  "severity": "critical",
  "summary": "审批通过后没有发送通知",
  "expected_behavior": "审批通过立即通知申请人",
  "actual_behavior": "审批通过成功，但没有通知消息",
  "impact": "影响发布流转"
}
```

### 用户 Prompt

```text
线上有个紧急问题：审批通过以后没发通知，这个今天必须修。你按热修复流程来，但不要省略验证。
```

### 期望命中

- 首先命中：`sdd-workflow-starter`
- 然后路由到：`sdd-work-hotfix`

### 期望行为

- 先复现问题
- 先写 failing reproduction 或至少明确复现步骤
- 做最小修复
- 之后仍然进入 review / regression / completion gates

### 失败信号

- 不复现就开始改
- 用“很急”为理由跳过回归
- 修完后不经过 completion gate

---

## 建议再补的近似误触发场景

如果你想继续提高这套 skills 的稳定性，建议后面再加两个“近似误触发”测试：

### 近似误触发 A：用户只问概念，不该进入完整主链

```text
你解释一下什么是规范驱动开发，别开始给我做项目。
```

观察点：

- 不应该强行进入 `work-specify`
- 更不应该开始生成交付件

### 近似误触发 B：用户明确要求只做 review

```text
我已经写好设计文档了，你只帮我做设计审查，不要改内容。
```

观察点：

- 应该尽量直接进入 `sdd-design-review`
- 不应重复走 `work-design`

---

## 推荐记录表

建议你每跑一个场景，记录成下面这样：

```markdown
## Eval: 场景名称

- Prompt:
- 前置工件:
- 实际首个命中 skill:
- 实际下游 skill:
- 是否跳步:
- 是否解释了路由依据:
- 是否 handoff 清晰:
- 结论: PASS | PARTIAL | FAIL
- 备注:
```

## 通过标准

这套 prompt 演练的最低通过标准是：

- 5 个主场景里，至少 4 个能先命中 `sdd-workflow-starter`
- 5 个主场景里，至少 4 个能正确路由到目标 skill
- 不出现“直接跳到实现”这种严重越权
- 主链场景中，`work-implement` 之后能明确说出 review/gate 顺序

如果你后面想继续，我建议下一步直接把这份文档再扩成：

- 一份 `evals.json`
- 一份人工评测表
- 或者一组“带前置文件样例的演练包”
