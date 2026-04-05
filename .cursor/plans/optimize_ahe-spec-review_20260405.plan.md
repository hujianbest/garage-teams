# 优化 `ahe-spec-review` 方案

## 目标

把 `skills/ahe-spec-review/SKILL.md` 从“能检查规格是否大致完整”的 skill，提升为“能稳定 gate 住高质量需求规格，并为真人确认提供高质量评审依据”的 skill。

本次优化不改变 AHE 主链契约：

- 仍然只评审规格，不在 review 阶段顺手做设计
- 仍然通过 `通过 | 需修改 | 阻塞` 三态给出结论
- 仍然在 `通过` 后进入规格真人确认，而不是直接进入 `ahe-design`
- 仍然在 `需修改` / `阻塞` 时回到 `ahe-specify`

## 当前问题

当前 `ahe-spec-review` 已具备正确 gate 和基础检查项，但仍偏“通用规格检查器”，主要短板是：

- 没有把 `ahe-specify` 当前已经要求的高质量规格契约反向映射成 review 清单
- 对需求编号、追溯、一致性、验收标准配对关系的检查不够具体
- 对 NFR 可测性和模糊表述的检查还不够机械化
- 缺少对关键用户旅程 / 顺序假设 / 失败路径的 spec 层审视
- 与通用 review 模板 verdict 字段的映射没有明确说明

## 优化方向

### 1. 对齐 `ahe-specify` 交付契约

显式检查：

- 关键功能需求是否带验收标准
- NFR 是否可判断
- 约束 / 接口 / 假设 / 例外是否清楚
- 阻塞性开放问题是否已清空

为什么这么改：

- review gate 的首要职责就是验证 upstream skill 的产物契约是否被真正满足

主要参考：

- `skills/ahe-specify/SKILL.md`
- `references/longtaskforagent-main/skills/long-task-requirements/SKILL.md`

### 2. 增加追溯与一致性检查

显式检查：

- 需求编号或稳定需求条目是否清楚
- 是否存在重复、冲突、孤立的验收标准
- 规格是否足以成为 `ahe-design` 的稳定输入

为什么这么改：

- 高质量规格 review 不只是看“写没写”，还要看后续设计是否能可靠接住

主要参考：

- `skills/ahe-design/SKILL.md`
- `skills/ahe-specify/SKILL.md`

### 3. 强化问题 / 用户 / 成功标准视角

在不变成产品规划 skill 的前提下，补强检查：

- 这个规格是否清楚写明服务谁、解决什么问题
- 是否清楚说明什么算成功
- 是否存在写得完整但方向仍偏的情况

为什么这么改：

- 有些规格不是写作质量差，而是问题定义本身没立稳

主要参考：

- `references/everything-claude-code-main/skills/product-lens/SKILL.md`

### 4. 强化 NFR 和模糊词审计

显式检查：

- 是否存在“快速 / 稳定 / 安全 / 友好”这类不可判定表述
- NFR 是否写成可判断、可验收的条件

为什么这么改：

- 模糊 NFR 是规格评审里最高频的隐患之一

主要参考：

- `references/longtaskforagent-main/skills/long-task-requirements/SKILL.md`
- `skills/ahe-specify/SKILL.md`

### 5. 增加关键场景 / 失败路径检查

对于交互或流程型需求，补查：

- 主路径是否清楚
- 关键失败路径是否被规格承接
- 是否存在顺序 / 状态假设没有显式写出

为什么这么改：

- 这些问题如果在规格阶段漏掉，设计阶段会被迫补规格

主要参考：

- `references/everything-claude-code-main/skills/click-path-audit/SKILL.md`
- `skills/ahe-specify/SKILL.md`

### 6. 明确 review 模板 verdict 映射

补充说明：

- `通过` -> `pass`
- `需修改` -> `revise`
- `阻塞` -> `blocked`

为什么这么改：

- 当前 template 与 AHE verdict 词不同，但语义兼容

主要参考：

- `templates/review-record-template.md`
- `skills/ahe-spec-review/SKILL.md`

## 明确不做的事

- 不把 `ahe-spec-review` 变成 `ahe-specify`
- 不在 review 阶段开始设计系统
- 不发明与 `ahe-workflow-starter` 冲突的新 verdict 或新路由节点

## 计划中的实际改动

会对 `skills/ahe-spec-review/SKILL.md` 做一轮聚焦重构，预计包括：

- 收紧 `description`
- 增加高质量规格评审基线
- 对齐 `ahe-specify` 的交付契约
- 强化追溯 / 一致性 / NFR / 关键场景检查
- 增加更明确的 severity 和修订导向
- 明确模板 verdict 映射

## 预期效果

优化后的 `ahe-spec-review` 应该具备这些特征：

- 不只是判断规格“像不像完整”，而是判断它是否真的 ready for human approval
- 更容易发现设计阶段会爆炸的问题，如模糊 NFR、重复 / 冲突需求、未闭合开放问题
- 更稳定地为 `ahe-design` 提供高质量上游输入
