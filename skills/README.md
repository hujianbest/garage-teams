# AHE Coding Skills

`packs/coding/skills/` 是当前仓库里 `Coding Pack` 的来源技能面，承接 AHE coding workflow family 的 skill、共享文档、模板与设计规则。

它在 phase 1 的定位是：

- `Garage` 的 coding 来源资产
- `Coding Pack` 的参考 workflow 面
- pack-local docs、templates 与设计规则的维护入口

它不是完整的 `Garage Core`，也不是未来 runtime 的全部实现。

## 目录约定

- `packs/coding/skills/README.md`：本目录总览
- `packs/coding/skills/docs/`：AHE coding workflow 的共享文档
- `packs/coding/skills/templates/`：AHE coding workflow 的共享模板
- `packs/coding/skills/design_rules.md`：skill 与 harness 资产的设计原则
- `packs/coding/skills/<skill-name>/SKILL.md`：单个 skill 的入口文件
- `packs/coding/skills/<skill-name>/references/`：该 skill 的补充说明、模板或参考资料

## 先看哪里

- 新会话入口、命令入口或 family discovery，先读 `packs/coding/skills/using-ahe-workflow/SKILL.md`
- 需要 authoritative runtime routing 或恢复编排时，读 `packs/coding/skills/ahe-workflow-router/SKILL.md`
- 需要共享规则时，读 `packs/coding/skills/docs/`
- 需要模板时，读 `packs/coding/skills/templates/`

## 当前 workflow family

当前主要成员包括：

- `ahe-specify`、`ahe-design`、`ahe-tasks`：上游主链产出
- `ahe-spec-review`、`ahe-design-review`、`ahe-tasks-review`：上游评审
- `ahe-test-driven-dev`、`ahe-hotfix`、`ahe-increment`、`ahe-finalize`：执行与支线闭环
- `ahe-bug-patterns`、`ahe-test-review`、`ahe-code-review`、`ahe-traceability-review`、`ahe-regression-gate`、`ahe-completion-gate`：质量与门禁

## 相关 supporting surfaces

- `packs/coding/skills/docs/ahe-workflow-entrypoints.md`
- `packs/coding/skills/docs/ahe-workflow-shared-conventions.md`
- `packs/coding/skills/docs/ahe-command-entrypoints.md`
- `packs/coding/skills/docs/ahe-worktree-isolation.md`
- `packs/coding/skills/templates/task-progress-template.md`
- `packs/coding/skills/templates/task-board-template.md`
- `packs/coding/skills/templates/review-record-template.md`
- `packs/coding/skills/templates/verification-record-template.md`

## 方法论基线

每个 AHE skill 都显式声明其遵循的已验证方法论。以下按角色汇总：

### 入口与路由

| Skill | 核心方法论 |
|-------|-----------|
| `using-ahe-workflow` | Front Controller Pattern, Evidence-Based Dispatch, Separation of Concerns |
| `ahe-workflow-router` | Finite State Machine Routing, Evidence-Based Decision Making, Escalation Pattern |

### 上游主链（Authoring）

| Skill | 核心方法论 |
|-------|-----------|
| `ahe-specify` | EARS (需求语句结构), BDD/Gherkin (验收标准), MoSCoW (优先级), IEEE 830 (需求分类), Socratic Elicitation (澄清模式) |
| `ahe-design` | ADR/Nygard (决策记录), C4 Model (架构视图), Risk-Driven Architecture (投入分配), YAGNI (范围控制), ARC42 (文档结构) |
| `ahe-tasks` | WBS (工作分解), INVEST Criteria (任务粒度), Dependency Graph + Critical Path (依赖与排序), Definition of Done (完成条件) |

### 上游评审

| Skill | 核心方法论 |
|-------|-----------|
| `ahe-spec-review` | Fagan Inspection (结构化评审), Checklist-Based Review, Author/Reviewer Separation |
| `ahe-design-review` | ATAM (架构权衡分析), Fagan Inspection, Traceability to Spec |
| `ahe-tasks-review` | INVEST Validation, Dependency Graph Validation, Traceability Matrix |

### 质量链评审

| Skill | 核心方法论 |
|-------|-----------|
| `ahe-bug-patterns` | Defect Pattern Catalog (Beizer/Ostrand), Checklist-Based Review, Severity-Confidence Matrix |
| `ahe-test-review` | Fail-First Validation (TDD Quality Gate), Coverage Categories (Crispin/Gregory), Bug-Pattern-Driven Testing |
| `ahe-code-review` | Fagan Code Inspection, Design Conformance Check, Defense-in-Depth Review |
| `ahe-traceability-review` | End-to-End Traceability (IEEE 830/ISO 26550), Zigzag Validation, Impact Analysis |

### 门禁

| Skill | 核心方法论 |
|-------|-----------|
| `ahe-regression-gate` | ISTQB Regression Testing, Impact-Based Testing, Fresh Evidence Principle |
| `ahe-completion-gate` | Definition of Done (Scrum), Evidence Bundle Pattern, Profile-Aware Rigor |

### 分支与收尾

| Skill | 核心方法论 |
|-------|-----------|
| `ahe-hotfix` | Root Cause Analysis (RCA/5 Whys), Minimal Safe Fix Boundary, Blameless Post-Mortem |
| `ahe-increment` | Change Impact Analysis (Boehm/Pfleeger), Re-entry Pattern (FSM), Baseline-before-Change |
| `ahe-finalize` | Project Closeout (PMBOK), Release Readiness Review, Handoff Pack Pattern |

### 实现

| Skill | 核心方法论 |
|-------|-----------|
| `ahe-test-driven-dev` | TDD (Beck), Walking Skeleton (Cockburn), Test Design Before Implementation, Fresh Evidence Principle |

## 维护约定

1. workflow skill 继续使用 `ahe-*` 命名族，但路径引用必须使用当前真实路径。
2. 每个 skill 入口统一放在 `packs/coding/skills/<skill-name>/SKILL.md`。
3. 长案例、模板说明和补充材料放到各 skill 的 `references/` 或共享 `docs/` / `templates/` 中。
4. 需要维护或验证 skill 时，优先使用当前真实存在的 skill 入口，例如 `.agents/skills/writing-skills/SKILL.md`；不要再假设旧的本地脚本工具链或统一脚本入口仍然存在。
