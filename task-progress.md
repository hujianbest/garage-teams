# Task Progress

## Goal

- Goal: F006 Garage Recall & Knowledge Graph — 让用户主动召回知识、把孤立 entry 连成图，铺好 Stage 3 模式检测的衬底
- Owner: hujianbest
- Status: 🟢 Active — drafting feature spec
- Last Updated: 2026-04-19

## Previous Milestones

- F001 Phase 1: ✅ 完成（T1-T22，416 测试通过）
- F002 Garage Live: ✅ 完成（CLI + 真实 Claude Code 集成，436 测试通过）
- F003 Garage Memory: ✅ 完成（T1-T9，384 测试通过）
- F004 Garage Memory v1.1: ✅ 完成（T1-T5，414 测试通过）
- F005 Garage Knowledge Authoring CLI: ✅ 完成（T1-T6，451 测试通过）

## Current Workflow State

- Current Stage: `hf-test-driven-dev`
- Workflow Profile: `standard`
- Execution Mode: `auto`
- Workspace Isolation: `in-place`
- Current Active Task: T1 — `_resolve_knowledge_entry_unique` + `_recommend_experience` helpers
- Pending Reviews And Gates: test-review、code-review、traceability-review、regression-gate、completion-gate
- Next Action Or Recommended Skill: `hf-test-driven-dev`
- Relevant Files:
  - `docs/features/F006-garage-recall-and-knowledge-graph.md`（待创建）
  - F003 `src/garage_os/memory/recommendation_service.py`（基础设施）
  - F005 `src/garage_os/cli.py`（CLI handler 模式）
  - `KnowledgeEntry.related_decisions / related_tasks` (schema 早已存在，无变更)
- Constraints:
  - Stage 2 仍保持 workspace-first
  - 复用 F003 `RecommendationService` 与 F005 CLI handler 模式
  - 不引入新 third-party 依赖
  - 不改 `KnowledgeStore` / `ExperienceIndex` 公开 API（与 F005 一致）

## Wedge

F003 已经做了 RecommendationService，但只在 `garage run <skill>` 时被动触发；用户没有主动召回入口（`manifesto.md` 承诺"记得你上个月的架构决策"在产品层未兑现）。F005 让用户能添加知识，但 entry 仍是孤立点——`KnowledgeEntry.related_decisions` schema 字段从 F001 起就存在，从未被任何路径写入或读取。

F006 收敛的最小 wedge = **"主动召回 + 知识图最小可用形态"**：
- `garage recommend <query>` — 主动 pull recommendations
- `garage knowledge link --from <id> --to <id>` — 维护图边
- `garage knowledge graph --id <id>` — 1 跳邻居视图

## Next Step

按 EARS + BDD + MoSCoW + 六分类法起草 `docs/features/F006-garage-recall-and-knowledge-graph.md`，然后派发 `hf-spec-review`。
