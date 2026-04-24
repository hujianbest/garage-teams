# `packs/coding/` — HarnessFlow 工程工作流 Pack

`packs/coding/` 是 Garage 自带的 **HarnessFlow（HF）工程工作流 family pack**，把 spec → design → tasks → TDD 实现 → 多维 review → gate → finalize 的完整工程链路打包成可分发的 22 个 skill + 11 个 family-level 共享资产。

下游用户在自己项目里 `garage init --hosts <list>` 之后，就能在挂载的宿主（Claude Code / OpenCode / Cursor）里加载 hf-specify / hf-design / hf-tasks 等 skill，按 SDD + 闸 TDD 流程驱动 AI Agent 做严肃工程任务。

## Pack 概况

| 字段 | 值 |
|---|---|
| `pack_id` | `coding` |
| `version` | `0.1.0` |
| `schema_version` | `1` |
| `skills` | 22（21 hf-* + 1 using-hf-workflow） |
| `agents` | 0 |
| family-level 资产 | 11（4 docs + 5 templates + 2 principles） |

## 22 个 Skill 清单

### Public Entry（1）

| Skill | 用途 |
|---|---|
| `using-hf-workflow` | HF workflow family public entry：判断 entry vs runtime recovery，分流到 router 或 direct invoke |

### Authoring（4）

| Skill | 用途 |
|---|---|
| `hf-product-discovery` | 产品发现 / thesis / wedge / probe；尚未收敛到 formal spec 时使用 |
| `hf-specify` | 起草需求规格（EARS + BDD + MoSCoW + 六分类） |
| `hf-design` | 起草实现设计（ADR + C4 + ARC42 + 失败模式） |
| `hf-ui-design` | 起草 UI 设计（IA + wireframe + Atomic + 状态矩阵）；规格含 UI surface 时与 hf-design 并行激活 |
| `hf-tasks` | 把已批准设计拆解为可评审任务计划（WBS + INVEST + 依赖图 + DoD） |

### Review（6）

| Skill | 用途 |
|---|---|
| `hf-discovery-review` | 评审 product discovery 草稿 |
| `hf-spec-review` | 评审需求规格（Q/A/C/G 四组 rubric） |
| `hf-design-review` | 评审实现设计（ATAM + Fagan + traceability） |
| `hf-ui-review` | 评审 UI 设计（peer with hf-design-review） |
| `hf-tasks-review` | 评审任务计划（粒度 + 追溯 + 依赖正确性） |
| `hf-test-review` | 评审实现完成后的测试质量 |
| `hf-code-review` | 评审实现代码质量 |
| `hf-traceability-review` | 评审 spec → design → tasks → 实现 → 验证的追溯完整性 |

> 注：上表实际 8 项 review skill；前 4 项对应 design/spec/tasks/discovery 4 个 authoring 节点的评审，后 4 项对应 implementation 完成后的多维评审。

### Gate（2）

| Skill | 用途 |
|---|---|
| `hf-regression-gate` | 回归验证 gate（traceability review 通过后） |
| `hf-completion-gate` | 完成判定 gate（regression gate 通过后） |

### Implementation & Branch（4）

| Skill | 用途 |
|---|---|
| `hf-test-driven-dev` | 单 active task 实现入口（TDD：fail-first → minimum implementation → verify green） |
| `hf-hotfix` | 线上紧急缺陷修复支线 |
| `hf-increment` | 范围 / 验收 / 约束变更支线 |
| `hf-finalize` | Cycle closeout：状态收尾 + release notes + handoff pack |

### Routing & Meta（2）

| Skill | 用途 |
|---|---|
| `hf-workflow-router` | Runtime 编排权威：profile / mode / isolation / canonical 节点 / review dispatch / 恢复编排 |
| `hf-bug-patterns` | 把重复出现的 bug 提炼为可复用 pattern catalog |

## 11 个 Family-Level 共享资产

这些文件**不是 skill**（不含 SKILL.md），而是被多个 hf-* skill 用相对路径引用的共享资源：

### `packs/coding/skills/docs/` — 4 个 family-level shared docs

被 hf-* skill 用 `skills/docs/<file>` 形式相对引用（实测 6 处来自 hf-finalize / hf-test-driven-dev / hf-workflow-router / using-hf-workflow）：

| 文件 | 用途 |
|---|---|
| `hf-command-entrypoints.md` | `/hf-*` 命令入口约定 |
| `hf-workflow-entrypoints.md` | Public entry 与 direct invoke 边界 |
| `hf-workflow-shared-conventions.md` | HF family 共享约定 |
| `hf-worktree-isolation.md` | Worktree 隔离指南 |

### `packs/coding/skills/templates/` — 5 个 templates

被 review / gate / finalize 等 skill 引用：

| 文件 | 用途 |
|---|---|
| `finalize-closeout-pack-template.md` | Workflow closeout pack 模板 |
| `review-record-template.md` | 通用 review record 模板（每个 review skill 在自己 references/ 下还有特化版） |
| `task-board-template.md` | Task board 投影模板 |
| `task-progress-template.md` | task-progress.md canonical schema |
| `verification-record-template.md` | 验证记录模板 |

### `packs/coding/principles/` — 2 个 family-level principles

被根级 `AGENTS.md § "Skill 写作原则"` 引用：

| 文件 | 用途 |
|---|---|
| `skill-anatomy.md` | 所有 Garage skill 的目标态写法（核心 7 原则、目录 anatomy、章节骨架、演化与版本管理） |
| `hf-sdd-tdd-skill-design.md` | HF spec-driven + TDD skill 设计模式 |

> **drift 收敛不变量**（spec § 4.2 红线 3 + design ADR-D8-3）：根级 `docs/principles/skill-anatomy.md` 与本目录的 `packs/coding/principles/skill-anatomy.md` 必须字节相等；由 `tests/adapter/installer/test_skill_anatomy_drift.py` sentinel 守门。

## Family-Level 引用与下游可达性

### packs/ 源端

22 个 hf-* skill 内任意 `skills/docs/<file>` / `templates/<file>` / `references/<file>` 形式相对引用，在 `packs/coding/` 内必须 resolve 到磁盘存在的真实文件。

### 下游宿主端（D7 管道边界）

F007 安装管道当前**只复制 `<pack>/skills/<id>/SKILL.md` 单文件**，不递归 `references/` / `evals/` / `scripts/` / `assets/` 等子目录。这意味着装到下游宿主（`.claude/skills/hf-specify/`）后，hf-specify SKILL.md 内嵌的 `references/spec-template.md` 引用是**文档级提示**（指向用户本地 Garage 仓库 git checkout 的 `packs/coding/skills/hf-specify/references/spec-template.md`），不是装后宿主目录下的本地副本。

详见：

- spec § FR-804 验收（packs 源端 + 下游宿主端两层口径）
- design ADR-D8-4（文档级提示策略）
- design ADR-D8-9（NFR-801 文件级豁免清单）
- spec § 5 deferred backlog "D7 管道扩展为递归 references/" → D9 候选

## 安装样板

下游用户在自己项目执行：

```bash
cd ~/projects/my-app
garage init --hosts claude
# stdout: Installed N skills, M agents into hosts: claude   (N == sum(三 pack.json.skills[]))
ls .claude/skills/ | grep -c '^hf-'   # → 21
ls .claude/skills/using-hf-workflow   # 存在
cat .claude/skills/hf-specify/SKILL.md | head -5
# → 含 installed_by: garage, installed_pack: coding
```

## 与 Garage 仓库自身的关系

本仓库自身贡献者首次 clone 后，需要先跑一次 dogfood 才能在 IDE 内加载这 22 个 skill：

```bash
cd /path/to/garage-agent
garage init --hosts cursor,claude
# → 在仓库根 dogfood 出 .cursor/skills/ + .claude/skills/，IDE 即可加载
# 注：.cursor/skills/ 与 .claude/skills/ 在 .gitignore 内排除，不入 git 追踪
```

详见 `AGENTS.md § "本仓库自身 IDE 加载入口"` 段。
