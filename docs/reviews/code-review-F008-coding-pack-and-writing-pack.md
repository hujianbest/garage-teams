# Code Review — F008 Garage Coding Pack 与 Writing Pack

- 状态: r1 通过
- 日期: 2026-04-23
- Reviewer: hf-code-review subagent (独立 reviewer)
- Cycle: F008
- 关联规格: `docs/features/F008-garage-coding-pack-and-writing-pack.md`（已批准 r2）
- 关联设计: `docs/designs/2026-04-22-garage-coding-pack-and-writing-pack-design.md`（已批准 r2，含 9 项 ADR）
- 关联任务计划: `docs/tasks/2026-04-22-garage-coding-pack-and-writing-pack-tasks.md`（已批准 r4，9 个 task）
- 关联前置评审: spec-review r2 通过 / design-review r2 通过 / tasks-review r4 通过 / test-review r1 通过（4 minor LLM-FIXABLE 不阻塞）
- 评审 skill: `packs/coding/skills/hf-code-review/`（rubric: CR1-CR6 + CA1-CA5）

## Precheck

- 稳定实现交接块 ✓ — `task-progress.md` `Current Stage=hf-test-review`（已通过流转中）；9/9 task commit 落地
- 可定位代码变更 ✓ — `git log main..HEAD --oneline` 共 14 个 commit，9 个为 T1a/T1b/T1c/T2/T3/T4a/T4b/T4c/T5（参见 hash 对照下文）+ 4 个 review/approval/test-review pre-commit + 1 个 task-progress 同步收尾 commit
- route/stage/profile 一致 ✓ — `Workflow Profile=full`、`Execution Mode=auto`、stage 已稳定推进到 review 链路
- 上游 evidence 一致 ✓ — hf-test-review verdict=通过 + 4 minor LLM-FIXABLE 全部不阻塞

precheck PASS，进入正式 6 维评审。

## 9 sub-commit 与 task plan 对照（NFR-804 git diff 可审计验证）

| commit hash | task | 主题 |
|---|---|---|
| `4f92b05` | T1a | `f008(coding/skills): packs/coding/ 22 skill cp -r 字节级搬迁` |
| `1a86212` | T1b | `f008(coding/family-asset): 11 个 family-level 资产 + pack.json + README` |
| `fa3d3fc` | T1c | `f008(coding/drift-sync): 反向同步根级 skill-anatomy.md + sentinel test`（含 carry-forward `tests/test_cli.py:3042` 修复，commit message 已声明） |
| `f0f2c05` | T2 | `f008(writing): packs/writing/ 4 skill + LICENSE + family-level prompts/ + 宿主中性化替换` |
| `b81664a` | T3 | `f008(garage): +find-skills +writing-skills, 0.1.0->0.2.0 + 宿主中性化替换` |
| `5a95b45` | T4a | `f008(layout/remove-agents): 删 .agents/skills/, dogfood 产物入 .gitignore` |
| `907bbfb` | T4b | `f008(layout/agents-md): AGENTS.md Packs 段刷新 + 首次 clone 贡献者 onboarding` |
| `57a1efd` | T4c | `f008(layout/tests): 4 集成测试 + EXEMPTION_LIST 扩展` |
| `6aa7587` | T5 | `f008(docs): packs/README + user-guide + RELEASE_NOTES F008 占位段` |

✓ 9 个 sub-commit 与 task plan § 5 拆解一对一映射；commit message 第一行均含 `f008(<scope>)` 前缀，可独立 review。

## 关键不变量实测

| INV / 红线 | 验证命令 | 实测 |
|---|---|---|
| INV-5 / 红线 6 (D7 管道不动) | `git diff main..HEAD -- src/garage_os/ \| wc -l` | **0**（CON-801 严守 ✓） |
| 零依赖变更 | `git diff main..HEAD -- pyproject.toml uv.lock \| wc -l` | **0** ✓ |
| INV-3 / 红线 3 (drift 收敛) | `diff /workspace/docs/principles/skill-anatomy.md /workspace/packs/coding/principles/skill-anatomy.md` | exit 0（字节相等 ✓） |
| 红线 4 (AGENTS.md 冷读链) | `grep 'docs/principles/skill-anatomy.md' AGENTS.md && test -f docs/principles/skill-anatomy.md` | both pass ✓ |
| 红线 2 / INV-6 (.agents/skills/ 删除 + git status) | `ls .agents/skills/`（应失败）+ `git status --porcelain` | dir 不存在 ✓；status 仅有 untracked dogfood 产物 + 本 review 文件（合规） |
| INV-8 (.gitignore 排除 dogfood) | `grep -E '^\.cursor/skills/$' .gitignore`、`grep -E '^\.claude/skills/$' .gitignore` | 均命中 ✓ |
| INV-9 layer (a) 强约束 (NFR-801) | `find packs/ \( -name 'SKILL.md' -o -path '*/agents/*.md' \) -exec grep -lE '\.claude/\|\.cursor/\|\.opencode/\|claude-code' {} \;` | 0 命中 ✓ |
| INV-9 layer (b) meta 豁免 (ADR-D8-9) | `pytest tests/adapter/installer/test_neutrality_exemption_list.py` | 3 passed ✓ |
| INV-2 family asset 单点 (红线 1) | `find packs -name <11 family asset 文件名> -type f \| wc -l` 抽样：hf-workflow-shared-conventions=1 / task-progress-template=1 / skill-anatomy=1 / hf-sdd-tdd-skill-design=1 / 横纵分析法=1 | 全部 ≤ 1 ✓ |
| review-record-template 多副本 | 7 个文件 SHA-256 各异（per-skill 特化版） | by design — `packs/coding/README.md` 已注明"每个 review skill 在自己 references/ 下还有特化版"；不计入 INV-2 family-asset 单点（11 项 enumerate 范围） ✓ |
| 安装期管道全测试 | `pytest tests/adapter/installer/ -q` | 120 passed ✓（含 5 个 F008 新测试文件 + 既有 test_neutrality.py 自动 parametrize 拾取 28 个新 SKILL.md） |

## 三个 pack.json 三向一致性核验

| Pack | pack.json.skills[] 长度 | 磁盘 SKILL.md 子目录数 | README 声明 | version | 三向一致 |
|---|---|---|---|---|---|
| `packs/coding/` | 22（21 hf-* + using-hf-workflow，字典序） | 22（按 `ls packs/coding/skills/` 减 `docs/`+`templates/` = 24-2=22） | "22（21 hf-* + 1 using-hf-workflow）" | `0.1.0`（首版，ADR-D8-6） | ✓ |
| `packs/writing/` | 4（blog-writing, humanizer-zh, hv-analysis, khazix-writer，字典序） | 4 | "4 个写作 skill" | `0.1.0`（首版，ADR-D8-6） | ✓ |
| `packs/garage/` | 3（find-skills, garage-hello, writing-skills，字典序） | 3 | "3" | `0.2.0`（F007 0.1.0 → F008 0.2.0，ADR-D8-6） | ✓ |
| `packs/garage/`.agents[] | `["garage-sample-agent"]` | 1 | "1"（ADR-D8-5 保留） | — | ✓ |

总 N = 22 + 4 + 3 = **29 skills**；总 M = **1 agent** — 与 spec 验收 #1、design § 8.1、AGENTS.md "当前 packs" 表全部一致。

## CON-803 例外 #2 量化守门（宿主中性化最小替换）

| 文件 | 上游来源 | 替换前 | 替换后 | git diff 行数 | ≤ 3 行 |
|---|---|---|---|---|---|
| `packs/writing/skills/hv-analysis/SKILL.md:55` | `.agents/skills/write-blog/hv-analysis/SKILL.md` | `检查路径 '/mnt/.claude/skills/web-access/SKILL.md' 是否存在` | `通过宿主原生机制检查该 skill 是否可用` | 1 行（diff -/+ 各 1） | ✓ |
| `packs/garage/skills/writing-skills/SKILL.md:12` | `.agents/skills/writing-skills/SKILL.md` | `(\`~/.claude/skills\` for Claude Code, \`~/.agents/skills/\` for Codex)` | `(refer to your host's documentation for the canonical skills directory path)` | 1 行 | ✓ |

✓ 两处替换均符合 CON-803 例外 #2 + spec NFR-801 验收 #4 量化上限；语义可读性保留；后续 grep 黑名单 0 命中。

## ADR-D8-9 EXEMPTION_LIST 三层同步实测

| 层 | 文件 | 豁免条目数 | 内容一致性 |
|---|---|---|---|
| spec | `docs/features/F008-...md` § CON-803 详细说明 | **7**（4 skill 内 meta + 3 pack-level README） | ✓ |
| design | `docs/designs/2026-04-22-...md` ADR-D8-9 表 | **7** | ✓ |
| 测试常量 | `tests/adapter/installer/test_neutrality_exemption_list.py` `EXEMPTION_LIST: frozenset[str]` | **7** | ✓ |

✓ 三层完全同步；`test_meta_files_in_exemption_list` 跑通 → 当前 packs/ 内所有非 SKILL.md 命中行的所属文件都 ∈ EXEMPTION_LIST，没有 unauthorized hits；新增同类豁免必须三层 amend 才能解锁。

## drift 反向同步方向核验（ADR-D8-3）

| 检查项 | 实测 | 期望 |
|---|---|---|
| `head -3 packs/coding/principles/skill-anatomy.md` | "定位: 项目级原则文档..." | （HF 副本权威） ✓ |
| `grep -c 'HF' packs/coding/principles/skill-anatomy.md` | **10** | HF 术语 ≥ 1 ✓ |
| `grep -c 'AHE' packs/coding/principles/skill-anatomy.md` | **0** | AHE 术语 = 0（已废弃） ✓ |
| `diff docs/principles/skill-anatomy.md packs/coding/principles/skill-anatomy.md` | exit 0 | 二者字节相等 ✓ |

✓ T1c 反向同步方向正确：取 family 副本（HF 术语，2026-04-18 时间戳，design ADR-D8-3 选定权威源）覆盖根级（AHE 术语已废弃）。AGENTS.md `## Skill 写作原则` 段引用路径 `docs/principles/skill-anatomy.md` 仍指向真实文件 → 红线 4 不破。

## 多维评分

按 `references/review-checklist.md` 6 维 0-10 评分：

| 维度 | 得分 | 评语 |
|---|---|---|
| **CR1 正确性** | 9/10 | 三 pack.json schema 全部正确（schema_version=1 / pack_id=目录名 / version 字符串 / skills[] 字典序 / agents[]）；skills[] 与磁盘 SKILL.md 子目录三向一致；version bump `packs/garage/` 0.1.0→0.2.0 合理（内容物从 1→3 skill，ADR-D8-6）；F007 carry-forward `tests/test_cli.py:3042` 改写正确（`==` → `in`，与 test_subprocess_smoke_three_hosts:3144 同精神）。9 个 sub-commit 内每个 cp -r 字节级 1:1 都通过 `test_skill_byte_level_sample_INV4` 抽样守门 + 自动化测试 120 passed |
| **CR2 设计一致性** | 9/10 | 9 项 ADR 全部严格实施：ADR-D8-1 family asset 落 `packs/coding/skills/{docs,templates}/` + `packs/coding/principles/`（去重 ✓）；ADR-D8-2 候选 C `.agents/skills/` 删除 + dogfood `.gitignore` 排除 ✓；ADR-D8-3 反向同步方向选 family 副本（HF 术语，时间戳更新）覆盖根级 ✓；ADR-D8-4 文档级提示边界在 README 显式说明 ✓；ADR-D8-5 garage-sample-agent 保留 ✓；ADR-D8-6 version bump 0.2.0 ✓；ADR-D8-7 AGENTS.md 局部刷新（`(F007)` → `(F007/F008)` + 当前 packs 表 + IDE 加载入口段）✓；ADR-D8-8 双轨 smoke + 自动化测试 ✓；ADR-D8-9 EXEMPTION_LIST 三层完全同步（spec + design + 测试常量都是 7 项）✓ |
| **CR3 状态 / 错误 / 安全** | 9/10 | cycle 内零代码改动（INV-5 守门 ✓），不引入新错误处理路径或状态转换；ADR-D8-9 EXEMPTION_LIST 当前 enum 完整（覆盖所有 packs/**/*.md 内非 SKILL.md/agent.md 的命中）；test_meta_files_in_exemption_list passed 证明无 unauthorized hits；未来新增 README 触发 layer (b) RED 是有意保护机制（强制三层同步），不是 bug；INV-9 layer (a) SKILL.md/agent.md 强约束 0 命中，宿主无关性 NFR-801 自动测试守门（test_neutrality.py 跑 29 次 SKILL.md parametrize 全过） |
| **CR4 可读性与可维护性** | 8/10 | 三个 pack README 文档质量良好（pack 概况表 + skill 清单 + family asset 引用关系 + 安装样板 + dogfood 提示）；AGENTS.md 局部刷新干净（保留原 § "Skill 写作原则" 段 + 新增 "本仓库自身 IDE 加载入口" 段，未误改 docs/principles/skill-anatomy.md 路径）；9 sub-commit message 对应 T1a/T1b/T1c/T2/T3/T4a/T4b/T4c/T5 一一映射，commit message 详尽含 acceptance 命令 + SHA-256 hash + 增量数。`packs/coding/README.md` 内 `### Authoring（4）` 实际有 5 项、`### Review（6）` 实际有 8 项（注释已 ack 后者但前者没注），属 cosmetic 清单标题计数小漂移（minor LLM-FIXABLE） |
| **CR5 范围守卫** | 10/10 | CON-801 严守：`git diff main..HEAD -- src/garage_os/ \| wc -l` = 0（INV-5 ✓）；零依赖变更：`git diff main..HEAD -- pyproject.toml uv.lock \| wc -l` = 0（NFR-803 ✓）；CON-803 例外 #2 量化守门通过（每处替换 1 行 diff ≤ 3 上限）；cp -r 整目录搬迁未借机改写 SKILL.md 业务逻辑（INV-4 字节级 1:1 由 test_skill_byte_level_sample_INV4 守门）；既有 30 个 installer 测试 0 改写（test review 已确认 git log main..HEAD -- tests/adapter/installer/ 全 add 动作）。CA3 undocumented behavior 无 — 9 个 commit 全部对应 task plan 内任务 |
| **CR6 下游追溯就绪度** | 9/10 | 9 sub-commit 独立可审计（NFR-804）；commit message 含完整 acceptance + 实测命令 + SHA-256 hash；INV-1..9 全部有自动化或 walkthrough 守门；spec → design → tasks → 实施 → 验证全链路追溯 anchor 清晰（task plan § 4 表已映射）；RELEASE_NOTES F008 段含 5 项 TBD 占位字段（finalize 阶段填充，design § 18 #2 已说明），结构与 F007 段对齐。test review 已识别的 4 minor LLM-FIXABLE（F5 LICENSE / carry-forward 混 commit / sentinel RED 证据弱 / NFR-803 fixture symlink）均不阻塞 traceability review |

总均分：**54/60 = 9.00/10**

无关键维度 < 6，无阻塞性 finding。

## 发现项

按 severity 排列（评 5 项 minor LLM-FIXABLE 全部不阻塞）：

### critical / important

无。

### minor

- [minor][LLM-FIXABLE][CR4] **`packs/coding/README.md` 类目计数标题与表格行数轻漂移**：`### Authoring（4）` 段表格实际 5 行（`hf-product-discovery` / `hf-specify` / `hf-design` / `hf-ui-design` / `hf-tasks`），标题数 4 但表格 5；`### Review（6）` 段表格实际 8 行，下方注释已 ack "上表实际 8 项 review skill" 但标题未同步刷新。这是 cycle 内文档新增未严格 cross-check 类目计数，不影响 22 总数（1+5+8+2+4+2=22 ✓）；建议 hf-test-driven-dev 后续轮把 "Authoring（4）" 改为 "Authoring（5）" + "Review（6）" 改为 "Review（8）"。当前不阻塞 hf-traceability-review，可作 carry-forward。
- [minor][LLM-FIXABLE][CR4] **`packs/garage/README.md` 表头行示意 `## Skills` 段下表头注 "（F007/F008 cycle 扩容）"**：表头本身正确但 README "Pack 概况" 表中 `version` 行注 "（F007 0.1.0 → F008 扩容到 3 skill）" — 拼接 `0.2.0` 与说明文字略冗长，可简化为 `0.2.0`（脚注/HTML 注释里写 cycle 来源）。当前可读性轻负担，不阻塞。
- [minor][LLM-FIXABLE][CR6/CA5] **`tests/test_cli.py:3042` carry-forward 修复混入 T1c drift-sync commit**（与 hf-test-review TT5 同源，本 review 同意其判定）：F007 hard-coded `manifest["installed_packs"] == ["garage"]` 在 packs 扩容后必然 RED，改成 `"garage" in manifest["installed_packs"]` 是合理的 forward-compatible 放宽（与 `test_subprocess_smoke_three_hosts:3144` regex-on-marker 同精神）。但混在 `fa3d3fc f008(coding/drift-sync)` commit 而非独立 commit，commit message 末尾以"顺手修"声明可追溯。NFR-804 "git diff 可审计 / 任意一组改动可独立 review" 精神在此略偏离。建议下次类似改动单独 commit `f008(test-cli/forward-compat): 解耦 F007 hard-coded installed_packs assertion`。当前不阻塞，commit message 已声明可追溯。
- [minor][LLM-FIXABLE][CR6] **RELEASE_NOTES F008 段测试增量分解描述精度**："+22 test_neutrality.py 新增 SKILL.md parametrize + +18 个新测试用例 + +7 个 packs/{garage,writing}/skills/<id>/SKILL.md 增量"（46+1=47？文字层 22+18+7=47 与 633-586=47 增量对得上，但分类口径不严谨：test_neutrality.py 自动 parametrize 拾取的是 SKILL.md 文件数 28（按 hf-test-review 实测）而非 22；`+7 个 packs/{garage,writing}/skills/<id>/SKILL.md` 不是测试用例而是被测对象计数）。属占位段文字描述精度问题，hf-finalize 阶段填实测后会重写。当前不阻塞。
- [minor][LLM-FIXABLE][CR6] **review-record-template.md 7 副本与单源 family-asset 关系无 README 显式说明**：`packs/coding/skills/templates/review-record-template.md`（family-level，作为 INV-2 enumerate 的 5 个 templates 之一）+ 6 个 review skill 各自 `references/review-record-template.md`（per-skill 特化版，SHA-256 各异）共 7 处。`packs/coding/README.md` 已用一句注释 "每个 review skill 在自己 references/ 下还有特化版" cover，但未在 family-asset 引用关系段显式说明 "family-level 模板是基线，per-skill 特化是细化覆盖"；初次审计读者可能误以为冗余副本违反 INV-2。建议在 `packs/coding/README.md` "Family-Level 引用与下游可达性" 段加一行说明。当前不阻塞，因 README 已 ack 二者并存。

## 代码风险与薄弱项

- **F5 LICENSE 守门链条断一环**（hf-test-review TT3 minor 同源，本 review 同意）：`packs/writing/LICENSE` 物理存在（T2 commit `f0f2c05` 已落），但无 pytest 用例显式断言；下次有人误删 LICENSE 不会被任何测试拦截。当前不阻塞 hf-traceability-review，建议作下个 cycle carry-forward 在 `test_full_packs_install.py` 加 `test_writing_license_preserved`。
- **NFR-801 文件级豁免清单 7 项的工程含义需在 traceability 阶段二次确认**：当前 EXEMPTION_LIST 含 `packs/{coding,garage,writing}/README.md` + `packs/README.md` 4 个 pack-level README（为 README 含 `garage init --hosts claude` / `ls .claude/skills/` 安装样板而豁免）。这是合理的 design 选择（README 是 meta 文档），但任何后续在 packs/ 内新增 README 触发 layer (b) RED 必须先 amend ADR-D8-9 + spec NFR-801 + 测试常量；这一约束在当前 commit message 与 RELEASE_NOTES 已说明，但建议 hf-traceability-review 检查"未来 packs/<new-pack>/README.md 触发 RED → 强制 amend 三层"的作动机制是否在 design ADR-D8-9 + spec NFR-801 详细说明都明确。
- **dogfood 产物 `.cursor/skills/` `.claude/skills/` 在 IDE 首次加载之前是空状态**（design ADR-D8-2 候选 C 已知 trade-off）：本仓库首次 clone 贡献者必须先跑 `garage init --hosts cursor,claude` 才能在 IDE 内加载 hf-* skill。AGENTS.md `## Packs & Host Installer (F007/F008) > 本仓库自身 IDE 加载入口` 段已说明，CONTRIBUTING.md 暂未引入。当前可接受。
- **drift sentinel test 的 PR walkthrough RED 阶段证据仅 commit message 文字层**（hf-test-review TT1 minor 同源，本 review 同意）：T1c sentinel test 的 fail-first RED 阶段证据 sha256 对比记录在 `fa3d3fc` commit message 内（`root sha256=283b6dae... vs packs sha256=9e523cbb...`），可重放（git revert 即可重现 RED）但缺独立 PR walkthrough artifact。建议下次类似 sentinel test 引入用两步 commit 方案（仅 sentinel commit → 反向同步 commit）给 reviewer 提供 git-history 层 RED→GREEN 证据。

## 缺失或薄弱项

- **F5 LICENSE 自动化保护链**（minor，已列入 finding）— 物理存在但无 pytest 守门
- **`packs/coding/README.md` 类目计数标题精度**（minor，已列入 finding）— Authoring/Review 标题数与表格行数轻漂移
- **carry-forward `tests/test_cli.py:3042` 与 T1c drift-sync 混 commit**（minor，已列入 finding）— 偏离 NFR-804 单独可审计精神，commit message 声明缓解
- **review-record-template.md 7 副本由设计意图但 README 未显式分层说明**（minor，已列入 finding）— 现有注释 cover 但欠完整
- **RELEASE_NOTES F008 段 5 项 TBD 占位 + 测试增量分解描述精度**（minor，已列入 finding）— hf-finalize 阶段重写

均无阻塞性，足以让 hf-traceability-review 做可信判断。

## 下一步

- **next_action_or_recommended_skill**: `hf-traceability-review`
- **needs_human_confirmation**: `false`（按 reviewer-return-contract.md：`hf-code-review` 在 `通过` 时默认 `false`，由父会话直接派发下一节点）
- **reroute_via_router**: `false`

父会话应直接派发独立 reviewer subagent 执行 `hf-traceability-review`，评审 spec → design → tasks → 实施 → 验证全链路追溯。本 review 已确认代码质量足够支持 traceability review 做可信判断。

## 记录位置

- review 记录: `/workspace/docs/reviews/code-review-F008-coding-pack-and-writing-pack.md`（本文件）

## 交接说明

### 给父会话

- 代码质量 r1 通过，无需回修
- 5 条 minor finding 全部 LLM-FIXABLE 但**不阻塞** hf-traceability-review；建议作为 carry-forward 在 hf-finalize 阶段或下次 cycle 处理
- 直接派发 hf-traceability-review，prompt 中可附本评审 5 条 minor finding 作为 reviewer 上下文（本 review 与 hf-test-review 共 9 条 minor，可在 hf-completion-gate 集中收敛决定哪些进 finalize / 哪些 carry-forward）

### 给 hf-traceability-review reviewer

追溯评审重点应放在：

1. **spec → design → tasks → 实施 → 测试 五元组锚点完整性**：每个 FR/NFR/CON/INV 的链路是否端到端可追溯（task plan § 4 表已映射，可逐条核验 evidence 锚点是否真实存在）
2. **ADR-D8-9 EXEMPTION_LIST 三层同步链的 traceability anchor**：spec NFR-801 详细说明（line 415-425） + design ADR-D8-9（line 343-353） + tests/adapter/installer/test_neutrality_exemption_list.py 的 EXEMPTION_LIST 常量（21-49 行）是否可双向追溯（找 spec 条目能定位到 design ADR + 测试用例，反之亦然）
3. **9 个 INV 责任 commit 与实施 commit 的 traceability anchor**：design § 11.1 表把每个 INV 标注了责任 commit（如 INV-3 → T1c），实施完成后这些 anchor 是否都在 PR 中可定位
4. **CON-803 例外 #2 实施期间扩展的 wording-only 修订是否反向回到 spec/design**：T2/T3 实施时的两处宿主中性化替换，是否在 design ADR-D8-9 表内 enum + 在 spec CON-803 例外 #2 详细说明列入 "（实施期间已发现，涵盖 r1 critical 命中）" 段（实测：spec line 410-413 已 enumerate 这两处）
5. **manual smoke walkthrough artifact 与 INV-7 IDE 加载链的追溯**：5 个 artifact 是否完整覆盖 INV-7 验证（hf-test-review precheck 已确认归档完整）

### 给后续 reviewer 链

- hf-regression-gate: NFR-802 测试基线 ≥ 633 ✓、INV-5 src/garage_os/ 零修改 ✓、INV-6 git status 干净（注：当前 workspace 有 `.claude/` 与 `.garage/config/host-installer.json` untracked，是 dogfood smoke 产物，已被 .gitignore 排除是正确状态；regression-gate 应在 clean checkout 上验证）
- hf-completion-gate: 9 条累计 minor finding（hf-test-review 4 + hf-code-review 5）是否需要在 cycle 内补，还是作为下个 cycle carry-forward；建议 F5 LICENSE 守门 + `packs/coding/README.md` 类目计数刷新作 cycle 内补，其余作 carry-forward
- hf-finalize: RELEASE_NOTES F008 段 5 个 TBD 占位字段需用 manual smoke 实测数据填充（design § 18 #2 已说明）；测试增量分解描述精度同步刷新

---

## 结构化返回

```json
{
  "conclusion": "通过",
  "next_action_or_recommended_skill": "hf-traceability-review",
  "record_path": "docs/reviews/code-review-F008-coding-pack-and-writing-pack.md",
  "key_findings": [
    "[minor][LLM-FIXABLE][CR4] packs/coding/README.md 类目计数标题与表格行数轻漂移（Authoring 标题 4 实际 5；Review 标题 6 实际 8 已 ack 但标题未刷新）",
    "[minor][LLM-FIXABLE][CR4] packs/garage/README.md version 行说明文字略冗长，可简化",
    "[minor][LLM-FIXABLE][CR6/CA5] tests/test_cli.py:3042 F007 hard-coded assertion carry-forward 修复混入 T1c drift-sync commit（与 hf-test-review TT5 同源），偏离 NFR-804 单独可审计精神",
    "[minor][LLM-FIXABLE][CR6] RELEASE_NOTES F008 段测试增量分解口径不严谨（22+18+7=47 数对得上但分类描述混测试 vs 被测对象），属占位段，hf-finalize 阶段重写",
    "[minor][LLM-FIXABLE][CR6] review-record-template.md 7 副本（1 family-level + 6 per-skill 特化）由设计意图但 packs/coding/README.md 未显式分层说明，初次审计可能误判 INV-2 违反"
  ],
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "finding_breakdown": [
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "CR4",
      "summary": "packs/coding/README.md 类目计数标题与表格行数轻漂移（Authoring/Review 标题数与表格行数对不上）"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "CR4",
      "summary": "packs/garage/README.md version 行说明文字略冗长可简化"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "CR6",
      "summary": "tests/test_cli.py:3042 carry-forward 修复混入 T1c commit，偏离 NFR-804 单独可审计精神"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "CR6",
      "summary": "RELEASE_NOTES F008 段测试增量分解描述口径不严谨，hf-finalize 阶段重写"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "CR6",
      "summary": "review-record-template.md 7 副本设计意图未在 packs/coding/README.md 显式分层说明"
    }
  ]
}
```
