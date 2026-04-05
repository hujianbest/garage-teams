# AHE P1 Optional Assets Decision

## Decision Summary

本轮 **不新增** 以下资产：

- `skills/using-ahe-skills/SKILL.md`
- reviewer / gate 对应的 `agents/*.md` persona 文件

这不是否定它们的长期价值，而是当前阶段判断为 **收益不足以覆盖维护成本**。

## Why Not Add `skills/using-ahe-skills/SKILL.md` Now

当前仓库已经有以下入口资产：

- `skills/ahe-workflow-starter/SKILL.md`：runtime 路由 kernel
- `docs/ahe-workflow-entrypoints.md`：说明什么时候走 starter、什么时候允许 direct invoke
- `docs/ahe-command-entrypoints.md`：说明高频薄命令入口
- `docs/ahe-workflow-shared-conventions.md`：集中收口 shared rules

在这个基础上再新增 `using-ahe-skills` meta-skill，会带来三个问题：

1. **与 starter 职责重叠**
它很容易被误写成第二个入口 kernel。

2. **触发歧义**
模型可能在“应该用 starter”与“应该用 meta-skill”之间摇摆。

3. **维护税**
一旦 shared conventions、entrypoints、commands 或 starter 有更新，meta-skill 也必须同步。

### Revisit Trigger

只有在出现以下真实需求时，再考虑新增：

- 外部仓库用户频繁需要“家族级 onboarding”，但又不适合直接进入 starter
- 命令入口与 starter 之间还缺一层稳定的 family explainer
- 文档入口已被证明不足，用户反复在“该从哪个 ahe skill 开始”上迷路

## Why Not Add `agents/*.md` Persona Assets Now

当前质量层已经有：

- live reviewer / gate skills 自身的职责边界
- `docs/ahe-review-persona-matrix.md`：把 persona 视角写成了 docs-first matrix

在这个阶段直接再生成 `agents/*.md`，风险大于收益：

1. **事实源重复**
persona、边界、回流逻辑会在 `SKILL.md`、matrix、agents 三处同时存在。

2. **实际复用证据不足**
当前还没有证据表明 reviewer / gate persona 已经被多个宿主、多个命令、多个 wrapper 重复调用到值得单独资产化。

3. **执行模型尚未稳定**
reviewer 节点与 gate 节点的执行模型不同；若过早抽成 agent persona，容易把两类节点写得过于相似。

### Revisit Trigger

只有在出现以下真实需求时，再考虑新增：

- 同一 reviewer / gate persona 在多个命令入口、多个 wrapper 或多个宿主里被反复引用
- docs-first matrix 已不足以指导一致执行
- 需要把 persona 提供给独立 subagent 模板或未来的自动 dispatch 层复用

## Current Replacement Strategy

当前以更轻的资产组合替代 optional files：

- runtime routing：`skills/ahe-workflow-starter/SKILL.md`
- family shared rules：`docs/ahe-workflow-shared-conventions.md`
- family entry rules：`docs/ahe-workflow-entrypoints.md`
- command wrappers：`docs/ahe-command-entrypoints.md`
- reviewer / gate persona：`docs/ahe-review-persona-matrix.md`

## Practical Outcome

因此，P1 optional items 当前结论是：

- `using-ahe-skills` meta-skill：defer
- `agents/*.md` reviewer / gate personas：defer

后续若出现真实复用信号，再把本决策文档升级为实施输入。
