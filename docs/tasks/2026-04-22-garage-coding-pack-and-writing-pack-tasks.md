# F008: Garage Coding Pack 与 Writing Pack 任务计划

- 状态: 草稿
- 主题: 把已批准 D008 设计拆解为可单任务推进、可冷读、可追溯的工作单元
- 日期: 2026-04-22
- Revision: r1
- 关联规格: `docs/features/F008-garage-coding-pack-and-writing-pack.md`（已批准 r2）
- 关联设计: `docs/designs/2026-04-22-garage-coding-pack-and-writing-pack-design.md`（已批准 r2）
- 关联批准: `docs/approvals/F008-spec-approval.md`、`docs/approvals/F008-design-approval.md`
- 关联评审: `docs/reviews/spec-review-F008-coding-pack-and-writing-pack.md`、`docs/reviews/design-review-F008-coding-pack-and-writing-pack.md`

## 1. 概述

D008 已稳定（8 项 ADR + 5 类提交分组拆为 9 个 sub-commit + 9 条 INV 不变量 + 4 个新增测试文件 + 7 条失败模式）。本任务计划按 D008 § 10.1 给定的 9 sub-commit 边界一一对应 9 个 task，每个 task 含 Acceptance / Files / Verify / 测试设计种子 / 完成条件 + 触发的 INV + 依赖关系。

执行原则：

- **CON-801 严守**：任何 task 不得修改 `src/garage_os/`，每个 commit 后 `git diff main..HEAD -- src/garage_os/` 必须为空（INV-5 守门）
- **零回归保护**：任何 task 不得让 `uv run pytest tests/ -q` 已有用例退绿（NFR-802）
- **字节级 1:1 搬迁**（CON-803）：所有 cp -r 类 task 完成后，源端 `.agents/skills/...` 与目的端 `packs/...` 同名文件 SHA-256 必须相等（INV-4）
- **drift 收敛硬门槛**（spec § 4.2 红线 3 + INV-3）：T1c 落 sentinel 测试后，`docs/principles/skill-anatomy.md` 与 `packs/coding/principles/skill-anatomy.md` 必须字节相等
- **路径契约**：D008 ADR-D8-1 锁定 `packs/coding/skills/{docs,templates}/` + `packs/coding/principles/`；ADR-D8-2 锁定 `.agents/skills/` 删除 + dogfood 入 `.gitignore`；任何偏离需回 `hf-design`

## 2. 里程碑

| 里程碑 | 包含任务 | 退出标准 | 对应 spec/design 锚点 |
|---|---|---|---|
| **M1 packs/coding/ 落盘** | T1a + T1b + T1c | 22 skill 子目录 + 11 family asset + drift 反向同步 + sentinel 测试全部落地；INV-2 + INV-3 + INV-4 + INV-9 通过 | spec FR-801 / FR-804；design ADR-D8-1 / ADR-D8-3 / § 10.1 T1a-T1c |
| **M2 packs/writing/ 落盘** | T2 | 4 write-blog skill + LICENSE + pack.json + README 落地；INV-4 + INV-9 通过 | spec FR-802；design § 10.1 T2 |
| **M3 packs/garage/ 扩容** | T3 | find-skills + writing-skills 落地；pack.json skills[] 扩到 3 + version 0.1.0→0.2.0 | spec FR-803；design ADR-D8-5 / ADR-D8-6 / § 10.1 T3 |
| **M4 .agents/skills/ 处置 + dogfood + 集成测试** | T4a + T4b + T4c | `.agents/skills/` 删除 + `.gitignore` 排除 dogfood 产物 + AGENTS.md onboarding 段 + 3 个新增集成/layout 测试落地；INV-1 + INV-6 + INV-7 + INV-8 通过 | spec FR-805；design ADR-D8-2 / ADR-D8-7 / § 10.1 T4a-T4c |
| **M5 文档 + walkthrough** | T5 | packs/README.md + user-guide + RELEASE_NOTES F008 占位段；end-to-end smoke 在 PR walkthrough 中提供证据 | spec FR-806 / FR-807；design ADR-D8-7 / ADR-D8-8 / § 10.1 T5 |

## 3. 文件 / 工件影响图

### 3.1 新增（不存在 → 存在）

| 工件 | 来自任务 | 类型 |
|---|---|---|
| `packs/coding/pack.json` | T1b | 配置（schema_version=1, version 0.1.0, skills[22], agents[]） |
| `packs/coding/README.md` | T1b | 文档 |
| `packs/coding/skills/<id>/SKILL.md` × 22（21 hf-* + using-hf-workflow，含各自 evals/ references/ 子目录）| T1a | skill 源 |
| `packs/coding/skills/docs/<file>.md` × 4（hf-command-entrypoints / hf-workflow-entrypoints / hf-workflow-shared-conventions / hf-worktree-isolation）| T1b | family-level shared docs |
| `packs/coding/skills/templates/<file>.md` × 5（finalize-closeout-pack / review-record / task-board / task-progress / verification-record）| T1b | family-level templates |
| `packs/coding/principles/<file>.md` × 2（skill-anatomy / hf-sdd-tdd-skill-design）| T1b | family-level principles |
| `tests/adapter/installer/test_skill_anatomy_drift.py` | T1c | sentinel test |
| `packs/writing/pack.json` | T2 | 配置（schema_version=1, version 0.1.0, skills[4], agents[]） |
| `packs/writing/README.md` | T2 | 文档 |
| `packs/writing/LICENSE` | T2 | 上游 license（来自 `.agents/skills/write-blog/LICENSE`） |
| `packs/writing/skills/<id>/SKILL.md` × 4（blog-writing / humanizer-zh / hv-analysis / khazix-writer，含各自 prompts/ examples/ 子目录）| T2 | skill 源 |
| `packs/garage/skills/find-skills/SKILL.md` | T3 | meta-skill |
| `packs/garage/skills/writing-skills/` 整子目录（含 SKILL.md + examples/ + render-graphs.js + 3 reference .md）| T3 | meta-skill |
| `tests/adapter/installer/test_full_packs_install.py` | T4c | 全装集成测试 |
| `tests/adapter/installer/test_packs_garage_extended.py` | T4c | packs/garage 扩容测试 |
| `tests/adapter/installer/test_dogfood_layout.py` | T4c | layout 测试 |
| `RELEASE_NOTES.md` § "F008" 段 | T5 | 占位段（finalize 阶段填实测数据） |

### 3.2 修改（既存 → 改动）

| 工件 | 来自任务 | 修改范围 |
|---|---|---|
| `docs/principles/skill-anatomy.md` | T1c | **反向同步**：被 `packs/coding/principles/skill-anatomy.md`（HF 术语，时间戳 2026-04-18）覆盖；与 `.agents/skills/harness-flow/docs/principles/skill-anatomy.md` 字节相等 |
| `packs/garage/pack.json` | T3 | `skills[]` 从 `["garage-hello"]` 扩到字典序 `["find-skills", "garage-hello", "writing-skills"]`；`version` `0.1.0` → `0.2.0` |
| `packs/garage/README.md` | T3 | 同步刷新（含 3 skill 清单 + getting-started 三件套说明） |
| `.gitignore` | T4a | 新增两行：`.cursor/skills/` + `.claude/skills/` |
| `AGENTS.md` | T4b | 局部刷新：(a) `## Packs & Host Installer` 段 5 分钟冷读指针表中 "F008 候选" → "已落地"；(b) 新增 "本仓库自身 IDE 加载入口" 段说明首次 clone 贡献者跑 `garage init --hosts cursor,claude` |
| `packs/README.md` | T5 | "当前 packs" 表新增 `coding` + `writing` 两行；扩容 `garage` 行（1→3 skill / 0.1.0 → 0.2.0） |
| `docs/guides/garage-os-user-guide.md` | T5 | "Pack & Host Installer" 段补一句 "目前 garage init 默认装 N skill（约 29，由三 pack.json.skills[] 之和派生）" |

### 3.3 删除（存在 → 不存在）

| 工件 | 来自任务 |
|---|---|
| `.agents/skills/` 整目录（含 harness-flow / write-blog / find-skills / writing-skills 全部子树）| T4a |

### 3.4 不修改（声明性兜底，CON-801 + INV-5 守门）

`src/garage_os/` 全树（types / storage / runtime / knowledge / adapter / tools / platform 全部不动）；F001-F007 既有 ≥586 测试基线 0 改写。

## 4. 需求与设计追溯

| spec ID | design 锚点 | 任务 | 验证用例 |
|---|---|---|---|
| FR-801 packs/coding/ 22 skill | ADR-D8-1 + § 10.1 T1a/T1b | T1a + T1b | `test_full_packs_install::test_coding_pack_22_skills` + 抽样 SHA-256 比对 |
| FR-802 packs/writing/ 4 skill | § 10.1 T2 | T2 | `test_full_packs_install::test_writing_pack_4_skills` + LICENSE 存在断言 |
| FR-803 packs/garage/ 3 skill + version bump | ADR-D8-5 + ADR-D8-6 + § 10.1 T3 | T3 | `test_packs_garage_extended.py` 全部用例 |
| FR-804 family-level 资产可解析（packs 源端 + 下游文档级提示）| ADR-D8-1 + ADR-D8-4 + § 10.1 T1b | T1b | `test_full_packs_install::test_family_asset_uniqueness` (INV-2) |
| FR-805 .agents/skills/ 处置 + git status 干净 | ADR-D8-2 + § 10.1 T4a/T4b | T4a + T4b | `test_dogfood_layout.py` 全部用例 |
| FR-806 端到端 smoke + walkthrough | ADR-D8-8 + § 10.3 + § 13.3 | T4c + T5 | `test_full_packs_install::test_three_hosts_install` + manual smoke walkthrough |
| FR-807 文档同步 | ADR-D8-7 + § 10.1 T5 | T5 | 人工 review（review 阶段） |
| NFR-801 宿主无关性 | § 12 + ADR-D8-1 | T1a / T1b / T2 | F007 既有 NFR-701 grep 测试自动覆盖（INV-9） |
| NFR-802 测试基线零回归 | § 12 + § 13.1 | 全 PR | `uv run pytest tests/ -q` 整体 ≥586 |
| NFR-803 ≤ 5s | § 12 | T4c + walkthrough | `test_full_packs_install` `pytest --durations` + smoke `time` |
| NFR-804 git diff 可审计 | § 10.1 | 全 PR | 9 sub-commit 自然成立 |
| CON-801 不动 D7 管道 | § 12 + INV-5 | 全 PR | `git diff main..HEAD -- src/garage_os/` 输出空 |
| CON-802 复用 pack.json schema | § 12 | T1b + T2 + T3 | pack.json 6 字段 schema 检查（discover_packs 自动） |
| CON-803 字节级 1:1 | § 12 + INV-4 | T1a + T2 + T3 | SHA-256 对比 |
| CON-804 .agents/skills/ 处置收敛 | ADR-D8-2 + INV-6 | T4a | `git status --porcelain` + `ls .agents/skills/` 报错 |
| spec § 4.2 红线 1 (family asset 单点) | ADR-D8-1 + INV-2 | T1b | `test_full_packs_install::test_family_asset_uniqueness` |
| spec § 4.2 红线 2 (.agents/skills 处置 + git status) | ADR-D8-2 + INV-6 | T4a | `test_dogfood_layout::test_agents_skills_removed` |
| spec § 4.2 红线 3 (drift 收敛) | ADR-D8-3 + INV-3 | T1c | `test_skill_anatomy_drift.py` |
| spec § 4.2 红线 4 (AGENTS.md 冷读链) | ADR-D8-3 + ADR-D8-7 | T4b | `test_dogfood_layout::test_agents_md_skill_anatomy_path` |
| spec § 4.2 红线 5 (IDE 加载链) | ADR-D8-2 + INV-7 | walkthrough | dogfood `find .cursor/skills` ≥ 5 行 + 截图证据 |
| spec § 4.2 红线 6 (D7 管道不动) | CON-801 + INV-5 | 全 PR | git diff |

## 5. 任务拆解

### T1a. packs/coding/ 22 skill cp -r 字节级搬迁

- **目标**: 把 `.agents/skills/harness-flow/skills/{hf-*,using-hf-workflow}/` 共 22 个 skill 子目录（含各自 evals/ references/ 等子文件）按 `cp -r` 字节级搬到 `packs/coding/skills/<id>/`
- **Acceptance**:
  - `ls packs/coding/skills/ | grep -E '^(hf-|using-hf-workflow)'` 输出恰好 22 行（21 hf-* + 1 using-hf-workflow）
  - 任一 hf-* skill 的 SKILL.md 在源端 `.agents/skills/harness-flow/skills/<id>/SKILL.md` 与目的端 `packs/coding/skills/<id>/SKILL.md` 的 SHA-256 字节级相等
  - 所有源端子文件（references/*.md / evals/*.json / 等）均已 1:1 落到目的端
  - INV-9: `grep -rE '\.claude/|\.cursor/|\.opencode/|claude-code' packs/coding/skills/` 命中数 = 0
- **依赖**: 无（M1 起点）
- **Ready When**: design 已批准（已满足）；当前分支为 `cursor/f008-coding-pack-and-writing-pack-bf33`
- **初始队列状态**: ready
- **Selection Priority**: 1（M1 起点；其它 task 均依赖 packs/coding/ 落地）
- **Files / 触碰工件**: `packs/coding/skills/<id>/` × 22（新增；T1a 完成时 packs/coding/skills/ 下**只有 22 个 hf-* + using-hf-workflow 子目录**，不含 docs/ templates/，后者由 T1b 加）
- **测试设计种子**:
  - 主行为：从 `.agents/skills/harness-flow/skills/hf-specify/SKILL.md` cp 到 `packs/coding/skills/hf-specify/SKILL.md` → SHA-256 相等（无需 fail-first，cp -r 即满足）
  - 关键边界：`hf-specify/references/spec-template.md` 等子文件也被复制（递归）
  - fail-first 适用点：在 T4c `test_full_packs_install.py` 中，跑前先期望 packs/coding/skills/hf-specify/SKILL.md 存在；若 T1a 漏拷某 skill，T4c 会 RED
- **Verify**（tasks-review-F008 r1 minor #5 修正自相矛盾）:
  - `ls packs/coding/skills/ | wc -l` == 22（T1a 完成时点严格相等；T1b 完成后会变 24，含 docs/ + templates/）
  - `find packs/coding/skills/hf-specify -type f -exec sha256sum {} \;` 与对应源端 sha256sum 一一相等（抽样）
  - `grep -rE '\.claude/|\.cursor/|\.opencode/|claude-code' packs/coding/skills/` 命中 = 0
- **预期证据**: PR commit `f008(coding/skills): packs/coding/ 22 skill cp -r` 的 git diff stat 含 ≈ 22 个 SKILL.md + N 个子文件 add；CI 跑 NFR-701 既有 grep 测试通过
- **完成条件**: 22 skill 目录全部物理存在 + SHA-256 抽样验证通过 + INV-9 grep 通过 + commit 落地

### T1b. packs/coding/ 11 family asset + pack.json + README

- **目标**: (a) 把 `.agents/skills/harness-flow/skills/{docs,templates}/` 共 9 个 family asset 搬到 `packs/coding/skills/{docs,templates}/`；(b) 把 `.agents/skills/harness-flow/docs/principles/{skill-anatomy,hf-sdd-tdd-skill-design}.md` 共 2 个 principles 搬到 `packs/coding/principles/`；(c) 写 `packs/coding/pack.json`（schema_version=1, pack_id="coding", version="0.1.0", description, skills[22], agents[]）；(d) 写 `packs/coding/README.md`
- **Acceptance**:
  - `find packs/coding -name 'hf-workflow-shared-conventions.md' -type f | wc -l` == 1（INV-2 family-asset 单点）
  - `find packs/coding -name 'task-progress-template.md' -type f | wc -l` == 1
  - `find packs/coding -name 'skill-anatomy.md' -type f | wc -l` == 1（在 packs/coding/ 内单点；根级 `docs/principles/skill-anatomy.md` 是 packs/ 之外，不计入 INV-2）
  - 任一 family asset 与上游 SHA-256 相等（CON-803 / INV-4）
  - `packs/coding/pack.json` 字段 schema_version=1, pack_id="coding", version="0.1.0", skills[] 长度 = 22, agents[] = []
  - `discover_packs` (F007 D7 管道) 跑 `packs/` 不抛 InvalidPackError / PackManifestMismatchError（pack.json skills[] 与磁盘子目录一致）
- **依赖**: T1a（packs/coding/skills/<22 hf-*>/ 已存在，否则 pack.json skills[] 与磁盘 mismatch）
- **Ready When**: T1a 完成
- **初始队列状态**: pending（依赖 T1a）
- **Selection Priority**: 2
- **Files / 触碰工件**:
  - 新增 `packs/coding/skills/docs/<file>.md` × 4
  - 新增 `packs/coding/skills/templates/<file>.md` × 5
  - 新增 `packs/coding/principles/<file>.md` × 2
  - 新增 `packs/coding/pack.json`
  - 新增 `packs/coding/README.md`
- **测试设计种子**:
  - 主行为：discover_packs(packs/) 返回的 Pack 列表含 pack_id="coding"，skills[] 长度 == 22
  - 关键边界：family asset 在 packs/coding/skills/{docs,templates}/ 下不被 discover_packs 误识别为 skill（实际 docs/ 与 templates/ 不含 SKILL.md 子目录，不被 _scan_disk_skills 拾取）
  - fail-first 适用点：在 T4c `test_full_packs_install::test_family_asset_uniqueness` 中先 assert 11 个 family asset 文件名 each `find packs -name <name> | wc -l == 1`
- **Verify**:
  - `cat packs/coding/pack.json | jq '.skills | length'` == 22
  - `python -c "from garage_os.adapter.installer.pack_discovery import discover_packs; from pathlib import Path; print([p.pack_id for p in discover_packs(Path('packs'))])"` 输出含 "coding"
  - `find packs/coding/skills/docs -type f | wc -l` == 4
  - `find packs/coding/skills/templates -type f | wc -l` == 5
  - `find packs/coding/principles -type f | wc -l` == 2
  - INV-2: 11 个 family asset 各 `find packs -name <file> -type f | wc -l` ≤ 1
- **预期证据**: PR commit `f008(coding/family-asset): 11 个 family-level 资产 + pack.json + README` 的 git diff stat 含 ≈ 11 个 .md add + 2 个新文件 (pack.json / README.md)
- **完成条件**: 11 个 family asset 物理存在 + pack.json 通过 discover_packs 校验 + INV-2 通过 + commit 落地

### T1c. drift 反向同步 + sentinel 测试

- **目标**: (a) 把 `packs/coding/principles/skill-anatomy.md`（与 family 副本字节相等，HF 术语 + 时间戳 2026-04-18）反向同步到根级 `docs/principles/skill-anatomy.md`（覆盖）；(b) 新增 `tests/adapter/installer/test_skill_anatomy_drift.py` sentinel 测试
- **Acceptance**:
  - `diff /workspace/docs/principles/skill-anatomy.md /workspace/packs/coding/principles/skill-anatomy.md` 输出空（INV-3 / 红线 3）
  - `tests/adapter/installer/test_skill_anatomy_drift.py` 含至少 1 个用例 `test_root_and_packs_principles_byte_equal` assertSHA-256 相等；该测试在当前分支 `uv run pytest tests/adapter/installer/test_skill_anatomy_drift.py -v` 通过
  - 现有 30 个 installer 测试 + N 个其它测试 0 退绿
- **依赖**: T1b（packs/coding/principles/skill-anatomy.md 已存在）
- **Ready When**: T1b 完成
- **初始队列状态**: pending（依赖 T1b）
- **Selection Priority**: 3
- **Files / 触碰工件**:
  - 修改 `docs/principles/skill-anatomy.md`（反向同步覆盖）
  - 新增 `tests/adapter/installer/test_skill_anatomy_drift.py`
- **Sub-acceptance（fail-first 顺序硬门槛，tasks-review-F008 r1 important #3 显式回应）**:
  - **Step 1 (RED 期)**: 先添加 `tests/adapter/installer/test_skill_anatomy_drift.py` 但**暂不**反向同步根级文件；本地跑 `uv run pytest tests/adapter/installer/test_skill_anatomy_drift.py -v` 必须 RED（两份字节不等）。在 PR walkthrough 中提供该 RED 截图或终端输出（可以是临时 stash 状态）作为证据
  - **Step 2 (GREEN 期)**: 执行反向同步 `cp packs/coding/principles/skill-anatomy.md docs/principles/skill-anatomy.md`，再跑同一测试必须 GREEN
  - **Step 3 (commit)**: GREEN 状态下落 commit；commit 包含 (a) sentinel test 文件 (b) 已被反向同步的 docs/principles/skill-anatomy.md
- **测试设计种子**（这是本 task 的核心交付）:
  - 主行为：`test_root_and_packs_principles_byte_equal` — 读两份 skill-anatomy.md，assert hashlib.sha256(content_a) == hashlib.sha256(content_b)
  - 关键边界：测试在 fixture **不依赖 .garage/ 或临时目录**，直接读仓库内固定路径（这是 sentinel 测试的特性，标记在测试 docstring 内）
  - fail-first 适用点：见上面 Sub-acceptance Step 1-3 三步显式拆出
- **Files / 触碰工件**（补充 sentinel test 不依赖 .garage/）:
  - 修改 `docs/principles/skill-anatomy.md`（反向同步覆盖）
  - 新增 `tests/adapter/installer/test_skill_anatomy_drift.py`（**sentinel: 不使用 tmp_path / .garage/ fixture，直接读 `Path(__file__).resolve().parents[3] / 'docs/principles/skill-anatomy.md'` 与 `... / 'packs/coding/principles/skill-anatomy.md'`**）
- **Verify**:
  - `diff /workspace/docs/principles/skill-anatomy.md /workspace/packs/coding/principles/skill-anatomy.md` exit code 0
  - `uv run pytest tests/adapter/installer/test_skill_anatomy_drift.py -v` 1 passed
  - `uv run pytest tests/ -q` ≥ 587 passed (586 baseline + 1 sentinel)
- **预期证据**: PR commit `f008(coding/drift-sync): 反向同步根级 skill-anatomy.md + sentinel test` 的 git diff 含 docs/principles/skill-anatomy.md 修改 + 1 个新测试文件；PR walkthrough 含 fail-first Step 1 RED → Step 2 GREEN 的证据（终端输出或 stash 截图）
- **完成条件**: Sub-acceptance Step 1-3 全过 + drift 收敛 + sentinel 测试 GREEN + commit 落地

### T2. packs/writing/ 4 skill + LICENSE + pack.json + README + 宿主中性化替换

- **目标**: 把 `.agents/skills/write-blog/{blog-writing,humanizer-zh,hv-analysis,khazix-writer}/` 共 4 个 skill cp -r 到 `packs/writing/skills/`；保留上游 LICENSE；写 pack.json + README；按 CON-803 例外 #2 对 hv-analysis/SKILL.md 做宿主中性化替换。
- **上游 layout 实测基线**（tasks-review-F008 r1 important #2 修正）:
  - `blog-writing/`：仅 `SKILL.md`
  - `humanizer-zh/`：`SKILL.md` + `LICENSE` + `README.md`
  - `hv-analysis/`：`SKILL.md` + `references/` + `scripts/`
  - `khazix-writer/`：`SKILL.md` + `references/`
  - **family-level**：`.agents/skills/write-blog/prompts/横纵分析法.md` 与 `.agents/skills/write-blog/README.md` — 决策：本 cycle 把 `prompts/横纵分析法.md` 作为 family-level shared 资产搬到 `packs/writing/prompts/横纵分析法.md`（与 packs/coding/ 的 family-level 资产同精神，但放在 pack 顶层而非 skills/ 子目录，因为 write-blog family 没有 hf-* 那种 "skills/docs/" 引用约定）；上游 `write-blog/README.md` 内容已被 packs/writing/README.md 替代，不再单独搬迁
- **Acceptance**:
  - `ls packs/writing/skills/ | wc -l` == 4，含 blog-writing / humanizer-zh / hv-analysis / khazix-writer
  - 任一 write-blog skill 的 SKILL.md（**除 hv-analysis 因宿主中性化替换外**）在源端与目的端 SHA-256 字节级相等（CON-803 / INV-4）；hv-analysis SKILL.md 允许 ≤ 3 行 diff（CON-803 例外 #2 量化守门）
  - `packs/writing/LICENSE` 存在且与上游 `.agents/skills/write-blog/LICENSE` SHA-256 相等
  - `packs/writing/prompts/横纵分析法.md` 存在且与上游 `.agents/skills/write-blog/prompts/横纵分析法.md` SHA-256 相等
  - `packs/writing/pack.json` schema_version=1, pack_id="writing", version="0.1.0", skills[] 长度 = 4, agents[] = []
  - `discover_packs` 跑 `packs/` 不抛错（包含 writing pack）
  - **INV-9 (宿主中性化)**: `grep -rE '\.claude/|\.cursor/|\.opencode/|claude-code' packs/writing/` 命中 = 0；这要求对 `hv-analysis/SKILL.md` line 55 `检查路径 '/mnt/.claude/skills/web-access/SKILL.md' 是否存在` 做最小替换（如改为 `检查路径 '<host-skills-dir>/web-access/SKILL.md' 是否存在` 或 `通过宿主原生机制检查 web-access skill 是否可用`），git diff ≤ 3 行
  - 既有 `tests/adapter/installer/test_neutrality.py` 在 T2 完成后跑必须 100% 通过（NFR-802 + NFR-801）
- **依赖**: 无（与 T1 系列并行可在依赖图层面无依赖；§ 8 调度仍按 P 升序串行）
- **Ready When**: 当前分支已就位
- **初始队列状态**: ready
- **Selection Priority**: 4（按 P 升序，T1c 之后）
- **Files / 触碰工件**:
  - 新增 `packs/writing/skills/blog-writing/` (`SKILL.md` 一个)
  - 新增 `packs/writing/skills/humanizer-zh/` (`SKILL.md` + `LICENSE` + `README.md`)
  - 新增 `packs/writing/skills/hv-analysis/` (`SKILL.md` + `references/` + `scripts/`，**SKILL.md 经宿主中性化替换**)
  - 新增 `packs/writing/skills/khazix-writer/` (`SKILL.md` + `references/`)
  - 新增 `packs/writing/prompts/横纵分析法.md`（family-level 资产）
  - 新增 `packs/writing/LICENSE`
  - 新增 `packs/writing/pack.json`
  - 新增 `packs/writing/README.md`
- **测试设计种子**:
  - 主行为：discover_packs(packs/) 返回含 pack_id="writing", skills[] 长度 == 4
  - 关键边界：(a) hv-analysis SKILL.md 替换后通过 test_neutrality.py grep；(b) family-level prompts/ 在 pack 顶层而非 skills/ 子目录；(c) 上游 README + 其它 .md 内容物按实测 layout 1:1 搬，不引入 prompts/ 或 examples/ 子目录
  - fail-first 适用点：T4c 集成测试 assert writing pack 存在 + INV-9
- **Verify**:
  - `cat packs/writing/pack.json | jq -e '.skills | length == 4'`
  - `test -f packs/writing/LICENSE`
  - `test -f packs/writing/prompts/横纵分析法.md`
  - `find packs/writing/skills -name 'SKILL.md' | wc -l` == 4
  - `grep -rE '\.claude/|\.cursor/|\.opencode/|claude-code' packs/writing/ | wc -l` == 0
  - `git diff packs/writing/skills/hv-analysis/SKILL.md | grep '^[+-]' | grep -v '^[+-]\+\+\+\|^[+-]---' | wc -l` ≤ 3*2=6（diff 单行算 +/- 各一行）
  - `uv run pytest tests/adapter/installer/test_neutrality.py -v` 100% 通过
- **预期证据**: PR commit `f008(writing): packs/writing/ 4 skill + LICENSE + family-level prompts/ + 宿主中性化替换`
- **完成条件**: 4 skill 物理存在 + LICENSE + family-level prompts/ 在 + pack.json 通过 discover_packs + INV-9 通过 + test_neutrality 通过 + commit 落地

### T3. packs/garage/ 扩容（+find-skills +writing-skills, 0.1.0→0.2.0 + 宿主中性化替换）

- **目标**: 把 `.agents/skills/find-skills/` 与 `.agents/skills/writing-skills/`（含 examples/ render-graphs.js 等子文件）搬到 `packs/garage/skills/`；改写 `packs/garage/pack.json.skills[]` 从 `["garage-hello"]` 扩到字典序 `["find-skills", "garage-hello", "writing-skills"]`；version `0.1.0` → `0.2.0`；同步刷新 README；按 CON-803 例外 #2 对 writing-skills/SKILL.md 做宿主中性化替换。
- **Acceptance**:
  - `ls packs/garage/skills/ | wc -l` == 3，含 garage-hello / find-skills / writing-skills
  - `cat packs/garage/pack.json | jq '.skills'` == `["find-skills", "garage-hello", "writing-skills"]`
  - `cat packs/garage/pack.json | jq '.version'` == `"0.2.0"`
  - `cat packs/garage/pack.json | jq '.agents'` == `["garage-sample-agent"]`（保留，ADR-D8-5）
  - find-skills/SKILL.md 与 .agents/skills/find-skills/SKILL.md 字节相等（INV-4）
  - **writing-skills/SKILL.md 经宿主中性化替换**（CON-803 例外 #2）：上游 line 12 含 `~/.claude/skills` + `~/.agents/skills/`（描述 personal skills 目录约定），改为 `<host-skills-dir>` + `<agent-personal-skills-dir>` 或等价宿主无关表达；git diff ≤ 3 行
  - writing-skills 的 examples/ + render-graphs.js + 3 reference .md（除 SKILL.md）全部 1:1 搬迁（INV-4 / CON-803）
  - discover_packs 不抛错
  - **INV-9**: `grep -rE '\.claude/|\.cursor/|\.opencode/|claude-code' packs/garage/` 命中 = 0
  - 既有 `tests/adapter/installer/test_neutrality.py` 在 T3 完成后跑必须 100% 通过
- **依赖**: 无（与 T1/T2 并行可，但建议串行）
- **Ready When**: 当前分支已就位
- **初始队列状态**: ready
- **Selection Priority**: 5
- **Files / 触碰工件**:
  - 新增 `packs/garage/skills/find-skills/SKILL.md`
  - 新增 `packs/garage/skills/writing-skills/`（整子目录）
  - 修改 `packs/garage/pack.json`（skills[] 1→3, version 0.1.0→0.2.0）
  - 修改 `packs/garage/README.md`（同步刷新清单）
- **测试设计种子**:
  - 主行为：discover_packs 返回 garage pack 含 skills[] 长度 == 3
  - 关键边界：(a) writing-skills 的 render-graphs.js 也被搬迁（不可执行性是 deferred 不影响 cycle）；(b) writing-skills SKILL.md 替换后通过 test_neutrality.py grep
  - fail-first 适用点：T4c `test_packs_garage_extended.py` assert + INV-9 + test_neutrality
- **Verify**:
  - `cat packs/garage/pack.json | jq -e '.skills | length == 3'`
  - `cat packs/garage/pack.json | jq -e '.version == "0.2.0"'`
  - `test -f packs/garage/skills/writing-skills/render-graphs.js`
  - `grep -rE '\.claude/|\.cursor/|\.opencode/|claude-code' packs/garage/ | wc -l` == 0
  - `git diff packs/garage/skills/writing-skills/SKILL.md | grep '^[+-]' | grep -v '^[+-]\+\+\+\|^[+-]---' | wc -l` ≤ 6
  - `uv run pytest tests/adapter/installer/test_neutrality.py -v` 100% 通过
- **预期证据**: PR commit `f008(garage): +find-skills +writing-skills, 0.1.0→0.2.0 + 宿主中性化替换`
- **完成条件**: 3 skill 物理存在 + pack.json 字段更新 + INV-9 + test_neutrality 通过 + commit 落地

### T4a. .agents/skills/ 删除 + .gitignore 排除 dogfood 产物

- **目标**: 改 `.gitignore` → `rm -rf .agents/skills/` → 若本地有 dogfood 残留则先 rm；提交 commit
- **执行顺序硬门槛**（tasks-review-F008 r1 缺失项之三）:
  1. **先**改 `.gitignore`（追加 `.cursor/skills/` + `.claude/skills/` 两行）
  2. **再**删 `.agents/skills/` 整子目录
  3. **再**检查本地是否有 dogfood 残留：`if [ -d .cursor/skills ]; then rm -rf .cursor/skills; fi; if [ -d .claude/skills ]; then rm -rf .claude/skills; fi`（这一步只删 dogfood 产物，确保 INV-6 git status 干净）
  4. **最后**跑 `git status --porcelain` 必须输出空才能 commit
- **Acceptance**:
  - `ls .agents/skills/` 报错 "No such file or directory"
  - `git status --porcelain` 输出空（INV-6 / 红线 2）
  - `grep -E '^\.cursor/skills/$' .gitignore && grep -E '^\.claude/skills/$' .gitignore` 都成功（INV-8）
  - 本地若曾跑过 `garage init --hosts cursor,claude` 产生 `.cursor/skills/` 等目录，T4a commit 前必须确保它们不在 git 追踪范围内（已被 .gitignore 排除即可，无需删）
- **依赖**: T1a + T1b + T1c + T2 + T3 全部完成（packs/ 已就位才能删 .agents/skills/）
- **Ready When**: M1 + M2 + M3 全部退出
- **初始队列状态**: pending
- **Selection Priority**: 6（M4 起点，T4a 必须先于 T4b T4c）
- **Files / 触碰工件**:
  - 删除 `.agents/skills/` 整目录（含 28 source SKILL.md + 11 family asset 全部子树，git diff 行数将极大）
  - 修改 `.gitignore`（追加 2 行）
- **测试设计种子**:
  - 主行为：rm 后 `.agents/skills/` 不存在；`.gitignore` 含两行排除
  - 关键边界：rm 不能误删 `.agents/skills/` 之外的文件（如 `.agents/` 本身保留为空目录或被 git 自动清理）
  - fail-first 适用点：T4c `test_dogfood_layout::test_agents_skills_removed`
- **Verify**:
  - `test ! -d .agents/skills/`
  - `git status --porcelain` 输出空（关键 invariant；commit 后跑）
  - `grep -E '^\.cursor/skills/$' .gitignore`
  - `grep -E '^\.claude/skills/$' .gitignore`
- **预期证据**: PR commit `f008(layout/remove-agents): 删 .agents/skills/，dogfood 产物入 .gitignore`，git diff 显示 删除 ~28 个 SKILL.md + 11 family asset + 各自子文件，及 .gitignore +2 行
- **完成条件**: .agents/skills/ 删除 + .gitignore 排除 + INV-6 + INV-8 通过 + commit 落地

### T4b. AGENTS.md 局部刷新（Packs 段 + IDE 加载入口段）

- **目标**: (a) `## Packs & Host Installer` 段 5 分钟冷读指针表新增 `coding` `writing` `garage` 三行说明（pack-id + 状态 + skill 计数）；(b) 新增 "本仓库自身 IDE 加载入口" 段，说明首次 clone 贡献者必须先跑 `garage init --hosts cursor,claude` 激活 dogfood 产物（ADR-D8-2 候选 C 配套）；(c) 必要时在 § "Packs & Host Installer (F007)" 标题处把 `(F007)` 改为 `(F007/F008)` 以反映多 cycle 沉淀
- **Acceptance**（tasks-review-F008 r1 minor #6 显式修正过弱验收）:
  - **(结构性检查)** AGENTS.md `## Packs & Host Installer` 段后续表格新增包含 `packs/coding/` `packs/writing/` 两行（行内含 pack-id + 状态 "✅ 已落盘（F008）" + 对应 skill 计数 22/4 或近似），扩容 `packs/garage/` 行（1→3 / 0.1.0→0.2.0）
  - **(onboarding)** AGENTS.md grep `garage init --hosts cursor,claude` 命中 ≥ 1（onboarding 命令样板存在）
  - **(冷读链不破)** `grep 'docs/principles/skill-anatomy.md' AGENTS.md` 仍命中（红线 4）
  - **(防误改)** 现有 AGENTS.md § "Skill 写作原则" 段未被破坏（grep `## Skill 写作原则` 仍命中且段首段尾文字未变）
  - **(F007 段不被破坏)** AGENTS.md § "Packs & Host Installer" 内 F007 已落入口指针表（含 `packs/README.md` / `docs/guides/garage-os-user-guide.md` / F007 spec link）仍存在
- **依赖**: T4a（dogfood 产物排除已落 .gitignore；AGENTS.md 段说明的前置）
- **Ready When**: T4a 完成
- **初始队列状态**: pending
- **Selection Priority**: 7
- **Files / 触碰工件**: `AGENTS.md`（局部刷新）
- **测试设计种子**:
  - 主行为：AGENTS.md grep 检查上述三个 invariant
  - 关键边界：不破坏 § "Skill 写作原则" 段对 docs/principles/skill-anatomy.md 的引用
  - fail-first 适用点：T4c `test_dogfood_layout::test_agents_md_skill_anatomy_path` 与 `test_agents_md_dogfood_onboarding`
- **Verify**:
  - `grep -E 'Packs & Host Installer' AGENTS.md` 命中
  - `grep -E 'packs/coding/' AGENTS.md` 命中（结构性，coding pack 已加表）
  - `grep -E 'packs/writing/' AGENTS.md` 命中
  - `grep -E 'garage init --hosts' AGENTS.md` 命中
  - `grep -E 'docs/principles/skill-anatomy.md' AGENTS.md` 命中（红线 4 守门）
  - `grep -E '## Skill 写作原则' AGENTS.md` 命中（防误改）
- **预期证据**: PR commit `f008(layout/agents-md): AGENTS.md Packs 段刷新 + 首次 clone 贡献者 onboarding`，git diff 显示 AGENTS.md 局部修改
- **完成条件**: AGENTS.md 6 个 grep invariant 通过 + commit 落地

### T4c. 集成测试三件套（test_full_packs_install / test_packs_garage_extended / test_dogfood_layout）

- **目标**: 新增 3 个测试文件，覆盖 INV-1 + INV-2 + INV-7 + INV-8 与 spec FR-803 / FR-805 / FR-806 验收
- **Acceptance**:
  - `tests/adapter/installer/test_full_packs_install.py` 至少含：
    - `test_three_packs_total_29_skills`：assert sum(pack.json.skills[] 长度) for pack in [garage,coding,writing] == 29 (INV-1)
    - `test_family_asset_uniqueness`：每个 family asset 文件名 `find packs -name <name> | wc -l == 1` (INV-2)
    - `test_install_packs_three_hosts`：fixture 跑 install_packs(hosts=["claude","cursor","opencode"])，assert manifest.installed_packs == sorted(["coding","garage","writing"])，files[] 长度 == 29*3 + 1 (1 个 agent 装到 claude)
    - `test_skill_byte_level_sample`：随机抽 hf-specify SKILL.md，assert 装到 .claude/skills/hf-specify/SKILL.md 后去除 Garage marker block 的内容与 packs/coding/skills/hf-specify/SKILL.md 字节级相等（INV-4）
  - `tests/adapter/installer/test_packs_garage_extended.py` 至少含：
    - `test_garage_pack_has_3_skills`：discover_packs → garage pack skills[] 集合等价 {"garage-hello","find-skills","writing-skills"}
    - `test_garage_pack_version_bumped`：pack.json version == "0.2.0"
    - `test_writing_skills_subdir_complete`：assert writing-skills 子目录含 examples/ + render-graphs.js
  - `tests/adapter/installer/test_dogfood_layout.py` 至少含：
    - `test_agents_skills_removed`：assert not Path(".agents/skills").exists()
    - `test_gitignore_excludes_dogfood`：read .gitignore 文本，assert 含 `.cursor/skills/` 与 `.claude/skills/`
    - `test_agents_md_skill_anatomy_path`：grep AGENTS.md 含 `docs/principles/skill-anatomy.md`（红线 4）
    - `test_agents_md_dogfood_onboarding`：grep AGENTS.md 含 `garage init --hosts cursor,claude` 形式样板
  - 新增 3 个测试文件全部通过；现有 30 个 installer 测试 + N 其它测试 0 退绿（NFR-802）
  - `uv run pytest tests/ -q` 整体计数 ≥ 586 + 3 文件新增用例数（约 ≥ 596）
- **依赖**: T4a + T4b（dogfood layout 已就位才能跑 test_dogfood_layout）
- **Ready When**: T4a + T4b 完成
- **初始队列状态**: pending
- **Selection Priority**: 8
- **Files / 触碰工件**:
  - 新增 `tests/adapter/installer/test_full_packs_install.py`
  - 新增 `tests/adapter/installer/test_packs_garage_extended.py`
  - 新增 `tests/adapter/installer/test_dogfood_layout.py`
- **测试设计种子**（任务自身就是测试，种子已在 Acceptance 内）:
  - 主行为：3 个测试文件按上述 acceptance 落地
  - 关键边界：fixture 用 tmp_path 创建临时 .garage/ + 临时 packs/（参考 F007 既有 test_pipeline.py fixture 模式）；不污染真实 .garage/
  - fail-first 适用点：先写测试 → 在 packs/ 还未装齐时跑应 RED（INV-1 失败）→ T1+T2+T3 完成后 + T4c 落 fixture 跑应 GREEN
- **Verify**:
  - `uv run pytest tests/adapter/installer/test_full_packs_install.py -v` 至少 4 passed
  - `uv run pytest tests/adapter/installer/test_packs_garage_extended.py -v` 至少 3 passed
  - `uv run pytest tests/adapter/installer/test_dogfood_layout.py -v` 至少 4 passed
  - `uv run pytest tests/ -q` 整体 ≥ 596 passed
- **预期证据**: PR commit `f008(layout/tests): 全装集成测试 + dogfood layout 测试 + packs/garage 扩容测试`
- **完成条件**: 3 测试文件 GREEN + 整体测试基线 ≥ 596 + commit 落地

### T5. 文档同步（packs/README.md + user-guide + RELEASE_NOTES F008 占位段）

- **目标**: 同步刷新 `packs/README.md` "当前 packs" 表（+coding +writing +扩容 garage），`docs/guides/garage-os-user-guide.md` "Pack & Host Installer" 段补 N skill 描述，`RELEASE_NOTES.md` 新增 F008 段（占位结构，finalize 阶段填实测数据）
- **占位字段清单**（tasks-review-F008 r1 minor #7 显式回应；finalize 阶段对接清晰）:
  - `manual_smoke_wall_clock` = TBD（finalize 阶段填实测 `time garage init --hosts all` 输出）
  - `pytest_total_count` = TBD（finalize 阶段填实测 `uv run pytest tests/ -q` 总数）
  - `installed_packs_from_manifest` = TBD（finalize 阶段填实测 `host-installer.json` 内容）
  - `commit_count_per_group` = TBD（finalize 阶段填 9 sub-commit 实际 commit hash）
  - `release_notes_quality_chain` = TBD（finalize 阶段填完整 review/gate 链路 verdict 表）
- **Acceptance**:
  - `grep -E '\| (coding|writing) \|' packs/README.md` 两行都命中且 "状态" 列为 "✅ 已落盘（F008）"
  - `grep -E '0\.2\.0|3 个 skill' packs/README.md` 至少一条命中（garage 扩容描述）
  - `grep -E 'N skill|约 29' docs/guides/garage-os-user-guide.md` 命中
  - `grep -E '## F008' RELEASE_NOTES.md` 命中且段落结构与 F007 段对齐（用户可见变化 / 数据与契约影响 / 验证证据 / 已知限制 4 段）
  - **(占位字段守门)** `grep -cE 'TBD' RELEASE_NOTES.md` 在 F008 段内命中 ≥ 5（对应上面 5 个占位字段；finalize 后该 grep 应 = 0）
- **依赖**: T1a + T1b + T1c + T2 + T3 + T4a + T4b + T4c 全部完成
- **Ready When**: 所有前序 task 完成
- **初始队列状态**: pending
- **Selection Priority**: 9（cycle 收尾）
- **Files / 触碰工件**:
  - 修改 `packs/README.md`
  - 修改 `docs/guides/garage-os-user-guide.md`
  - 修改 `RELEASE_NOTES.md`（新增 F008 段，含上面 5 个占位字段 — 实测数据由 finalize 填）
- **测试设计种子**:
  - 主行为：3 处文档 grep 检查
  - 关键边界：F007 段不被破坏（grep `## F007` 仍命中）；packs/README.md 顶层契约段不被破坏
  - fail-first 适用点：N/A（文档级 task；review 阶段人工 review）
- **Verify**:
  - 上述 grep 全部命中
  - `head -30 packs/README.md`、`head -50 RELEASE_NOTES.md` 人工 review
- **预期证据**: PR commit `f008(docs): packs/README + user-guide + RELEASE_NOTES F008 占位段`
- **完成条件**: 3 文档全部更新 + commit 落地

## 6. 依赖与关键路径

```
T1a ─→ T1b ─→ T1c ─┐
                   │
T2 ────────────────┼─→ T4a ─→ T4b ─→ T4c ─→ T5
                   │
T3 ────────────────┘
```

**依赖图层面**: T2 / T3 与 T1c 互不依赖（T2 / T3 只依赖分支已就位）。

**调度层面**（tasks-review-F008 r1 minor #4 修正与 § 8 一致）: § 8 选择规则按 Selection Priority 升序串行调度（router 不并发），实际执行顺序 T1a → T1b → T1c → T2 → T3 → T4a → T4b → T4c → T5。"并行" 仅指依赖图层面无前置约束，不指 router 真的并发。

**关键路径**: 9 跳（按 P 升序串行；critical path = 全路径）；这是为了 NFR-804 git diff 可审计，每步独立 commit / review。

**关键约束**:
- T4a 必须在 T1c + T2 + T3 全部完成之后（packs/ 已就位才能删 .agents/skills/）
- T4c 必须在 T4a + T4b 之后（test_dogfood_layout 依赖 dogfood 状态已建立）
- T5 必须在所有 T1-T4 之后（文档反映最终状态）

## 7. 完成定义与验证策略

cycle 完成定义（与 spec § 2.2 验收 #1-#9 对齐）：

1. T1a + T1b + T1c + T2 + T3 + T4a + T4b + T4c + T5 全部 commit 落地
2. INV-1..9 全部通过（详见 design § 11.1）
3. spec § 4.2 6 条 "Design Reviewer 可拒红线" 全部通过（详见 design § 2.3）
4. `uv run pytest tests/ -q` ≥ 596 passed（586 baseline + 4 个新文件 sentinel/集成测试 + 若干）
5. `git diff main..HEAD -- src/garage_os/` 输出空
6. **(零依赖变更守门)** `git diff main..HEAD -- pyproject.toml uv.lock` 输出空（NFR-803 / spec § 8 "本 cycle 零依赖变更"）
7. End-to-end smoke 在 PR walkthrough 提供证据（dogfood `garage init --hosts cursor,claude` + `find .cursor/skills | head` + 截图）

验证顺序（hf-test-driven-dev 阶段执行）：
- 每个 task commit 后跑该 task 的 Verify 命令 + INV 守门
- 全 PR 跑 `uv run pytest tests/ -q` + `mypy src/` + `ruff check src/ tests/`
- T2 / T3 完成后立即跑 `uv run pytest tests/adapter/installer/test_neutrality.py -v` 守门 NFR-801（防止上游瑕疵未替换干净）
- **NFR-803 ≤ 5s 验收**（tasks-review-F008 r1 minor #8 显式回应）双轨：
  - 自动化口径：T4c `test_full_packs_install` 用 `pytest --durations=10` 抓 install_packs() 调用 wall-clock（不含 fixture setup）
  - Manual smoke 口径：在 PR walkthrough 提供 `time garage init --hosts all` 实测 wall-clock（与 design § 10.3 manual smoke 完全一致）
  - 两个口径都需 ≤ 5s
- T5 完成后跑 manual smoke walkthrough（dogfood 验证）

## 8. 当前活跃任务选择规则

按依赖图 DFS：

1. 若无 in_progress task → 选 `Selection Priority` 最低的 `ready` task
2. T1a 是绝对起点（Selection Priority=1，无依赖）
3. T1a 完成 → T1b ready
4. T1b 完成 → T1c ready；同时 T2 / T3 也 ready（与 T1c 并行可，但建议串行）
5. T1c + T2 + T3 全部完成 → T4a ready
6. T4a 完成 → T4b ready
7. T4b 完成 → T4c ready（test_dogfood_layout 依赖 .gitignore + AGENTS.md 已落地）
8. T4c 完成 → T5 ready

router 在每个 task 完成后按上述规则重选下一 task；若候选不唯一，按 `Selection Priority` 升序选最小者。

## 9. 任务队列投影视图

```
[T1a] coding/skills      ready    P=1
[T1b] coding/family-asset pending  P=2  ← T1a
[T1c] coding/drift-sync   pending  P=3  ← T1b
[T2]  writing             ready    P=4
[T3]  garage              ready    P=5
[T4a] layout/remove-agents pending P=6  ← T1c+T2+T3
[T4b] layout/agents-md     pending P=7  ← T4a
[T4c] layout/tests         pending P=8  ← T4b
[T5]  docs                 pending P=9  ← T4c
```

Task Board 实时状态：见 `task-progress.md` 同步字段（`Current Active Task` 字段）。

## 10. 风险与顺序说明

| 风险 | 缓解 | 锚点 |
|---|---|---|
| T1a 复制时 macOS .DS_Store 被一并搬入 packs/ | T1a commit 前跑 `find packs -name .DS_Store -delete`；建议在 .gitignore 全局排除 .DS_Store（如尚未） | design § 14 F1 |
| T1c sentinel 测试在反向同步前先写会 RED | 这是 fail-first 期望行为；先写测试（RED）→ 跑同步 → 跑测试（GREEN）；测试本身不阻塞 commit | design § 14 F2 |
| T4a `git status` 不干净（dogfood 产物已存在但未入 .gitignore） | T4a 必须先改 .gitignore 再 rm -rf；或在 PR walkthrough 之前已跑过 dogfood 的话先 rm -rf .cursor/skills .claude/skills 再 commit | design § 14 F3 |
| T1a 时 .agents/skills/harness-flow/skills/ 实际 hf-* 数 ≠ 21 | spec ASM-801 已声明 cycle 期间不被修改；T1a 前跑 `ls .agents/skills/harness-flow/skills/ \| grep -c '^hf-'` 确认 == 21 | design § 14 F4 |
| T2 漏拷 LICENSE | T2 acceptance 含 `test -f packs/writing/LICENSE`；T4c integration test 也守门 | design § 14 F5 |
| smoke 时 garage CLI 不在 PATH | walkthrough 用 `uv run python -m garage_os` 或先 `uv pip install -e .` | design § 14 F6 |
| family asset 在装到下游宿主时不被复制（D7 管道边界）| spec FR-804 已显式分两层口径承认；RELEASE_NOTES F008 "已知限制" 显式说明；D9 候选记录管道扩展 | design § 14 F7 + ADR-D8-4 |
| T5 RELEASE_NOTES 在实施期间是占位段，finalize 阶段填实测 | T5 acceptance 写明占位段结构；finalize 阶段（hf-finalize）补实测数据 | design § 18 #2 |
