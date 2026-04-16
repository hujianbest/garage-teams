---
name: ahe-regression-gate
description: 适用于 traceability review 通过后需回归验证、用户要求 regression check 的场景。不适用于判断任务完成（→ ahe-completion-gate）、状态收尾（→ ahe-finalize）、阶段不清（→ ahe-workflow-router）。
---

# AHE Regression Gate

防止"修好了本地但破坏了相邻模块"。在最小回归验证范围内收集 fresh evidence，判断回归面是否健康。运行在 traceability-review 之后。

不是 completion gate（判断当前任务完成），也不是 finalize（收尾）。

## Methodology

本 skill 融合以下已验证方法：

- **Regression Testing Best Practice (ISTQB)**: 定义回归范围时区分 full/standard/lightweight 三级覆盖，确保投入与风险匹配。
- **Impact-Based Testing**: 回归范围基于 traceability review 识别的影响区域，而非机械运行全部测试。
- **Fresh Evidence Principle**: 回归证据必须在当前会话内实际产生，不接受历史运行结果替代。

## When to Use

适用：traceability review 通过后需回归验证；用户要求 regression check。

不适用：判断任务完成 → `ahe-completion-gate`；状态收尾 → `ahe-finalize`；阶段不清 → `ahe-workflow-router`。

## Hard Gates

- 无当前会话 fresh evidence 不得宣称回归通过
- 上游 review/gate 记录缺失不得通过
- worktree-active 时 evidence 必须锚定同一 Worktree Path

## Workflow

### 1. 对齐上游结论

确认当前 profile 必需的 review/gate 记录齐全且结论支持继续。

Profile-aware 回归范围：
- `full`：traceability 识别的所有区域
- `standard`：直接相关模块
- `lightweight`：最小 build/test 入口

### 2. 定义回归面

明确回归覆盖：哪些模块/命令/测试套。不覆盖什么要显式写出。

### 3. 执行回归检查

运行完整回归命令。不用更弱证据替代。

### 4. 阅读结果

检查退出码、失败数量、输出是否支持"回归通过"结论、结果是否属于当前代码。

### 5. 形成 evidence bundle

记录：回归面定义、命令、退出码、结果摘要、新鲜度锚点、覆盖边界、未覆盖区域。

### 6. 门禁判断

- `通过` → `ahe-completion-gate`
- `需修改` → `ahe-test-driven-dev`
- `阻塞`(环境) → 重试 `ahe-regression-gate`
- `阻塞`(上游) → `ahe-workflow-router`

## Output Contract

记录保存到 `AGENTS.md` 声明的 verification 路径；若无项目覆写，默认使用 `docs/verification/regression-<task>.md`。结构包含：结论、上游证据、回归面、证据表、覆盖缺口、回归风险、下一步。

## 和其他 Skill 的区别

| Skill | 区别 |
|-------|------|
| `ahe-completion-gate` | 判断当前任务可否宣告完成（证据束齐不齐）；本 skill 判断回归面健康度（旁边模块坏了没） |
| `ahe-finalize` | 关闭工作周期、产出 handoff pack；本 skill 只做回归门禁 |
| `ahe-workflow-router` | 编排/路由/阶段判断；本 skill 只做回归验证 |

## Red Flags

- 不读上游 review 记录就跑回归
- "本地测试通过"等同于"回归安全"
- 依赖旧运行结果
- worktree-active 但 evidence 没锚定同一路径

## Verification

- [ ] regression record 已落盘
- [ ] 回归面定义、evidence bundle 已写清
- [ ] 基于最新证据给出唯一门禁结论
- [ ] task-progress.md 已同步
