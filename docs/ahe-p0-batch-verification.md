# AHE P0 Batch Verification

## Scope

本轮验证覆盖以下 P0 批次及其后续收口：

- P0-4 producer archetype
- P0-4 gate / finalizer / implementation archetype
- P0-5 upstream reviewer skeleton
- P0-5 downstream reviewer / bug-patterns
- P0-5 branch / re-entry contract
- P0-6 router-era kernel / entry split（历史上曾记为对 pre-split **legacy 合并 router** 的第二轮瘦身；现状以 `ahe-workflow-router` + `using-ahe-workflow` 为准）
- reviewer handoff canonical field rollout
- progress schema canonical naming rollout

## Checks Run

### 1. Repo text consistency scans

对 `skills/` 与 `docs/ahe*.md` 做了多轮文本扫描，重点检查：

- 旧 reviewer handoff 字段 `next_action`
- 旧 progress schema 名称，如 `Current Task`、`Next Action`、`phase`
- `任务真人确认`、`needs_human_confirmation`、`reroute_via_router`
- `Next Action Or Recommended Skill` 与 `Current Stage` 的使用一致性

结果：

- live AHE skills 与 AHE docs 已收口到 canonical handoff / progress schema
- 旧字段仅在历史工件兼容说明中保留；当前 canonical 写法统一为 `reroute_via_router`

### 2. Independent review passes

对 runtime router / reviewer contract 收口结果与整个 P0 面向契约的一致性做了独立 review，并修复了 review 中发现的关键问题：

- `ahe-tasks` 不再在 `ahe-tasks-review` 通过后直接跳进 `ahe-test-driven-dev`，而是先进入 `任务真人确认`
- `ahe-specify` / `ahe-design` / `ahe-tasks` 的 reviewer `阻塞` 结果不再一律回本 skill；当 reviewer 显式要求重编排时，改为回到 `ahe-workflow-router`
- `ahe-workflow-router` 主文件、`execution-semantics.md` 与 `profile-node-and-transition-map.md` 已对齐 human confirmation、pause point 与 reroute-to-router 语义
- `ahe-finalize` 对 `Next Action Or Recommended Skill` 的说明已对齐 router-era canonical vocabulary，不再把合法值错误收窄到仅 `ahe-*`

### 3. Diagnostics

对本轮修改过的 skills / docs 以及 `skills/`、`docs/` 目录执行了 IDE diagnostics 读取。

结果：

- `ReadLints` 未发现新增 diagnostics

### 4. `quick_validate` status

按 `skill-creator` 的建议尝试补跑 `.cursor/skills/skill-creator/scripts.quick_validate` 前，先检查了 Python 运行环境。

结果：

- `python` 命令不可用
- `py` launcher 不存在
- `python3` 也不可用

因此本轮 **无法** 在当前环境中执行 `quick_validate`。这不是 skill 内容失败，而是运行环境缺少 Python 入口。

## Verification Verdict

在文档级与契约级检查范围内，P0 当前状态可视为：

- canonical handoff contract: pass
- canonical progress schema: pass
- router routing / human confirmation / reroute semantics: pass
- diagnostics: pass
- `quick_validate`: blocked by environment

## Follow-up

后续仍应在具备 Python 入口的环境中补跑：

- `python -m scripts.quick_validate <skill-dir>` for all `skills/ahe-*`
- 更完整的 `skill-creator` family-level validation / testing
