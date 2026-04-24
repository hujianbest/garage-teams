# Design Review — F008 Garage Coding Pack 与 Writing Pack

- 评审目标: `docs/designs/2026-04-22-garage-coding-pack-and-writing-pack-design.md`（草稿 r1）
- Reviewer: 独立 reviewer subagent（按 `hf-design-review` skill 执行）
- 评审时间: 2026-04-23
- 上游证据基线:
  - `task-progress.md`（Stage=`hf-design` / Profile=`full` / Mode=`auto` / Workspace=`in-place`）
  - `docs/features/F008-garage-coding-pack-and-writing-pack.md`（已批准 r2）
  - `docs/approvals/F008-spec-approval.md`（auto-mode approval record）
  - `docs/reviews/spec-review-F008-coding-pack-and-writing-pack.md`（r1 需修改 → r2 通过）
  - F007 已批准设计 + 实际管道代码 `src/garage_os/adapter/installer/{pack_discovery,pipeline}.py`
  - 仓库现状：`ls .agents/skills/harness-flow/skills/`、`ls packs/garage/`、`diff docs/principles/skill-anatomy.md .agents/skills/harness-flow/docs/principles/skill-anatomy.md`

## 结论

**需修改**

verdict 理由：D008 草稿基本面扎实——8 项 ADR 全部带候选对比与可逆性评估，§ 2.3 把 spec § 4.2 全部 6 条 "Design Reviewer 可拒红线" 逐条承接，§ 11.1 9 条 INV 不变量全部可被测试或 grep 验证，§ 10.1 五类提交分组对齐 spec NFR-804，§ 14 失败模式 F1-F7 显式枚举。可作为 `hf-tasks` 拆任务的输入方向是清晰的。

但发现 **1 条 important USER-INPUT 级 spec drift 风险（ADR-D8-4 实质性下调 spec 验收口径，需真人在 design 真人确认环节明确签署）** + **3 条 important LLM-FIXABLE 级 design 内部一致性 / readiness 缺口**（§ 13 测试策略与 § 12 NFR 落地行自相矛盾、§ 17 漏列 3 项 spec § 5 deferred、§ 10.1 T1/T4 commit 粒度偏大）+ **4 条 minor LLM-FIXABLE 级 改进点**。这些 finding 不构成 design 内核坍塌，预计 1 轮定向回修可全部闭合，因此判 `需修改` 而非 `阻塞`。

ADR-D8-4 那条 USER-INPUT 是 design 阶段对已批准 spec 硬验收（FR-804 #1 / § 2.2 #2 "装完后引用不 404"）的口径下调——design 已正确识别 CON-801（不动 D7 管道）与该 spec 验收之间不可调和的张力，并把"管道扩展"放到 D9 候选——但 spec 文字未变直接靠 design ADR "重述" acceptance，仍属合规边缘，必须在真人确认环节让用户对该口径下调签字背书。这种"design 主动暴露 spec 漏洞 + 提出 deferred 解法"是允许的，但不能由 design ADR 单方面重定义 spec 已写死的 acceptance 字眼。

## 6 维评分（内部）

| 维度 | 得分 | 主要观察 |
|---|---|---|
| D1 需求覆盖与追溯 | 7/10 | § 3 追溯表覆盖 FR/NFR/CON 全集；ADR-D8-4 对 spec FR-804/§2.2#2 实质性 reinterpretation；§ 17 漏列 spec § 5 deferred 3 项 |
| D2 架构一致性 | 8/10 | § 4 模式选择 / § 8 视图清晰；§ 11 模块边界明确；§ 8.4 端到端管道图 + § 8.4 注脚显式说明 family asset 不被复制是优秀做法 |
| D3 决策质量与 trade-offs | 8/10 | 8 项 ADR 全部带 ≥2 候选对比 + Consequences/Reversibility 段；ADR-D8-3 反向同步方向的"权威源选定"缺 git log 证据 |
| D4 约束与 NFR 适配 | 8/10 | § 12 NFR/CON 落地表完整；§ 11.1 INV 不变量映射到 commit 责任；CON-801 由 INV-5 明确守门 |
| D5 接口与任务规划准备度 | 6/10 | § 10.1 五类提交分组直接对应 NFR-804；T1 单 commit 含 ≥7 类动作（22 skill + 11 family asset + drift 反向同步 + pack.json + README + sentinel test）、T4 单 commit 含 4 类动作（rm -rf + .gitignore + AGENTS.md + 集成测试），与 NFR-804 "任一组改动可被独立 review" 的 spec 意图存在张力，hf-tasks 拿到后需要进一步拆分 |
| D6 测试准备度与隐藏假设 | 6/10 | § 13 测试策略与 § 12 NFR 落地表对"新增测试文件数量"陈述自相矛盾（§13 列 2 个 / §12 列 4 个）；§ 13.3 Walking Skeleton 仅覆盖 Claude Code 一家宿主；§ 18 非阻塞 #3 已识别 dogfood 产物的新贡献者发现性问题但未进入 ADR Consequences |

任一维度未低于 6/10，但 D5/D6 两个维度刚卡 6 分，对应到 important finding。

## 发现项

### Critical

无 critical 级 finding。

### Important

1. **[important][USER-INPUT][D1]** **ADR-D8-4 实质性下调 spec FR-804 验收 #1 / § 2.2 验收 #2 的 acceptance 字面口径**：
   - spec FR-804 验收 #1 明文写："Given F008 实施完成 + 任意一次 `garage init --hosts claude` 成功，When 任意 hf-* SKILL.md 内含 `references/spec-template.md` ... 形式相对引用，**Then 该相对路径在 `.claude/skills/` 加载入口下必须能 resolve 到磁盘存在的真实文件**" — 关键约束是"在 `.claude/skills/` 加载入口下"
   - spec § 2.2 验收 #2 同样明文："**装到 `.claude/skills/` 后**必须仍能 resolve 到磁盘存在的目标文件"
   - 实测 D7 管道 `pipeline._resolve_targets()` 只对 `<pack>/skills/<id>/SKILL.md` 单文件 read→inject→write，不递归 `references/`、`docs/`、`templates/` 任一子目录
   - 实测 hf-specify 等多个 SKILL.md 内大量引用 `references/spec-template.md` / `skills/docs/hf-workflow-shared-conventions.md` / `templates/task-progress-template.md` 等家族内文件 — 在 D7 当前管道下装到 `.claude/skills/hf-specify/` 后，这些引用全部 404
   - design ADR-D8-4 选定"文档级提示" — 把 spec 硬验收口径下调到"下游用户的 Garage 仓库 git checkout 是 references 真源；下游宿主的 SKILL.md 引用是文档级提示，而非加载时硬依赖"
   - design 选择是合理的（CON-801 / 红线 6 严禁动管道 → 短期内别无他法 + D9 候选作为长期解），但**spec 已批准的 acceptance 字眼未变**，由 design ADR 单方面重述硬验收的语义属于 spec drift 风险
   - **修复路径二选一**：
     - (a) 在 design 真人确认环节让用户对"spec FR-804 验收 #1 / § 2.2 验收 #2 的 '装完后不 404' 口径下调到 'packs/ 内不 404 + 下游为文档级提示'" 显式签字背书；ADR-D8-4 文末加一段"本决策需 spec 真人在 design 真人确认时签署 acceptance 重述"
     - (b) 回 `hf-increment` 修订 spec FR-804 验收 #1 / § 2.2 验收 #2 字面口径，删除"在 `.claude/skills/` 加载入口下" 约束，改为"在 packs/ 内可解析 + 下游引用是文档级提示"，spec 重新走 r3 review；这条更干净但显著拉长 cycle
   - **锚点**：design §2.4 (L67-83)、§7 ADR-D8-4 (L227-247)；spec FR-804 验收 #1 (L292)、§2.2 验收 #2 (L106)、§3.2 场景 3 (L155)；管道事实 `src/garage_os/adapter/installer/pipeline.py:252-298`（`_resolve_targets`）+ `pack_discovery.py:62-66`（`skill_source_path`）

2. **[important][LLM-FIXABLE][D6]** **§ 12 NFR-802 落地表与 § 13.1 自动化测试表对"新增测试文件数量"自相矛盾**：
   - § 12 NFR-802 落地行（L520）声明："新增 ≥ 4 个用例（test_full_packs_install / test_skill_anatomy_drift / test_packs_garage_extended / test_dogfood_layout）"，列 **4 个测试文件**
   - § 13.1 自动化测试表（L529-533）只列 **2 个测试文件**（`test_skill_anatomy_drift.py` + `test_full_packs_install.py`）
   - § 12 列出但 § 13 缺席的两个测试文件（`test_packs_garage_extended` / `test_dogfood_layout`）在 design 中无任何"测什么 / 触哪个 INV / 触哪个 spec FR/NFR" 的描述
   - hf-tasks 阶段拿到 design 后无法判断这两个测试究竟该覆盖什么 — 直接掉头回 design 或自由发挥都不优
   - **修复指引**：§ 13.1 表补两行（test_packs_garage_extended 触发 FR-803 验收 + INV-1 / test_dogfood_layout 触发 FR-805 验收 #2 + INV-7），或反向把 § 12 NFR-802 落地行精简到 § 13 的 2 个测试 + 显式说明"hf-tasks 阶段可按需再拆"
   - **锚点**：design § 12 (L520) vs § 13.1 (L529-533)；spec NFR-802 (L350-353)

3. **[important][LLM-FIXABLE][D5]** **§ 10.1 T1 / T4 commit 粒度偏大，不利于 NFR-804 git diff 可审计性的 spec 意图**：
   - T1 (coding) 单 commit 含：(a) 22 skill 子目录 cp -r (b) 4 docs cp -r (c) 5 templates cp -r (d) 2 principles cp -r (e) drift 反向同步覆盖根级 `docs/principles/skill-anatomy.md` (f) 写 `packs/coding/pack.json` (g) 写 `packs/coding/README.md` (h) 新增 `tests/adapter/installer/test_skill_anatomy_drift.py` —— 7+ 类异质动作
   - T4 (layout) 单 commit 含：(a) `rm -rf .agents/skills/`（涉及 28 source SKILL.md + 11 family asset 删除，git diff 行数极大）(b) 改 `.gitignore`（dogfood 产物排除）(c) 改 `AGENTS.md`（局部刷新）(d) 新增 `test_full_packs_install.py` —— 4 类异质动作 + 海量删除噪声
   - spec NFR-804 的 spec 意图（L370-371 注释）："实际允许 1 个或多个 commit/group，本 NFR 不强求数量，强求**可审计性**——任意一组改动可被独立 review"
   - T1 把"内容物搬运"与"drift 收敛"+"sentinel test 新增"合并 — drift 收敛是独立逻辑切片，应可被独立 review；T4 把"删 .agents/skills/" 与"集成测试新增" + "AGENTS.md 文档"合并 — 三者实质独立
   - 这条不阻塞 design 通过 hf-design-review，但应在 design § 10.1 显式注明拆分边界（T1a/T1b/T1c 子提交 + T4a/T4b 子提交），让 hf-tasks 阶段不必从头思考切片
   - **修复指引**：design § 10.1 把 T1 拆成 T1a (22 skill) / T1b (11 family asset + pack.json + README) / T1c (drift 反向同步 + sentinel test)；T4 拆成 T4a (rm -rf .agents/skills/ + .gitignore) / T4b (AGENTS.md 文档刷新) / T4c (test_full_packs_install + test_dogfood_layout)；或在 § 15 任务规划准备度段加一行"hf-tasks 拆分时建议在 T1/T4 内再切 sub-commit"
   - **锚点**：design § 10.1 (L426-460)、§ 15 (L568-575)；spec NFR-804 (L364-371)

4. **[important][LLM-FIXABLE][D1]** **§ 17 排除项漏列 spec § 5 deferred 中 3 项**：
   - spec § 5 共列 **12 项 deferred**（uninstall / update / 全局安装 / 新增宿主 / packs/product-insights / 改写 SKILL.md / 给 packs/coding/ 加新 hf-* skill / pack.json 新字段 / find-skills 真功能 / writing-skills render-graphs.js 可执行 / 多语言 i18n / 反向同步 user→packs）
   - design § 17 复述其中 8 项 + 自加 2 项（D7 管道扩展 / 下游 references 直接打开），合计 10 项；**漏掉 spec § 5 的**：
     - (a) "给 `packs/coding/` family 加新 hf-* skill"（spec § 5 row 7）
     - (b) "多语言 / i18n 版本（write-blog 仅中文）"（spec § 5 row 11）
     - (c) "反向同步：用户在 .claude/skills/ 改了之后回流到 packs/"（spec § 5 row 12）
   - 这 3 项 spec 已显式 deferred，design § 17 不复述会让 finalize 阶段缺归口 / 验证不齐 → spec § 5 与 design § 17 的 backlog 表无法形成完整集合等价
   - **修复指引**：design § 17 补这 3 行；统一标注延后到 D9 / Stage 3 / 单独 cycle
   - **锚点**：design § 17 (L592-606)、spec § 5 (L237-251)

### Minor

5. **[minor][LLM-FIXABLE][D2]** **ADR-D8-2 候选 C "首次 clone 贡献者发现性"风险未进入 ADR Consequences 显式承接**：
   - 候选 C 选定后，新贡献者 `git clone` 后必须先跑 `garage init --hosts cursor,claude` 才能在 IDE 看到 hf-* skill；`.gitignore` 排除 `.cursor/skills/` `.claude/skills/`
   - 实测当前 `.gitignore` 仅 22 行，加入 dogfood 排除后没有任何顶层文档说明"为什么 .cursor/skills/ 在 .gitignore 但 IDE 又依赖它"
   - design § 18 非阻塞 #3 已提及"新贡献者可能困惑，AGENTS.md 段落需明确说明"，但 ADR-D8-2 Consequences 段（L184-190）没把这条作为 trade-off 显式列入风险栏
   - 也未明确"首次 clone 后激活 IDE skill 加载"的指引该落 README.md 顶部、CONTRIBUTING.md、还是 AGENTS.md 哪一处（design 只说"AGENTS.md 增一段说明"）
   - **修复指引**：ADR-D8-2 Consequences 段加一行"⚠️ 新贡献者首次 clone 后 IDE 加载链是空的，必须先跑 `garage init --hosts cursor,claude` 激活；此 onboarding 步骤需落 [README/AGENTS/CONTRIBUTING] 顶部 - 由 hf-tasks T4 commit 选定"
   - **锚点**：design § 7 ADR-D8-2 Consequences (L184-190)、§ 8.2 (L356-361)、§ 18 #3 (L617)

6. **[minor][LLM-FIXABLE][D3]** **ADR-D8-3 把 family 副本（HF 术语）作为"权威源"但缺 git log/blame 证据支撑"更新版"判定**：
   - design § 7 ADR-D8-3 称 "取 family 副本（HF 术语，**更新版**）作为权威源"
   - 实测两份 diff 显示：family 副本（HF 术语）含 `skills/docs/` 旧路径，根级（AHE 术语 + `packs/coding/skills/docs/` 现代路径）反而更"面向 F008 落地后状态"
   - 哪一份是真"更新版"取决于 git log/blame 时间戳，design ADR 内未给证据
   - reverse-sync 方向选错的代价：丢失 `packs/coding/skills/docs/` 这种更准确的路径锚点；最终 sentinel 守门字节相等是干净的，但内容选哪份是实质决策
   - **修复指引**：ADR-D8-3 Compare 表"反向同步" 行内补一句 git log 证据（如 "`git log -1 --format=%aI -- .agents/skills/harness-flow/docs/principles/skill-anatomy.md` vs `git log -1 --format=%aI -- docs/principles/skill-anatomy.md`，前者更新于 YYYY-MM-DD，故选定为权威源"）；或承认两份都"半新半旧"且声明优先采用 HF 术语版的理由（如术语一致性更重要）
   - **锚点**：design § 7 ADR-D8-3 (L194-225)、实测 diff 显示 70 字节差与术语漂移

7. **[minor][LLM-FIXABLE][D5]** **ADR-D8-1 选定的 layout (`packs/coding/skills/{docs,templates}/` + `packs/coding/principles/`) 与 spec § 4.1 候选 A 措辞 (`packs/coding/{docs,templates,principles}/`) 略有偏差，未在 ADR 内显式解释**：
   - spec § 4.1 候选 A 写 "`packs/coding/{docs,templates,principles}/`"（三者并列于 packs/coding 顶层）
   - design 选定 "`packs/coding/skills/{docs,templates}/` + `packs/coding/principles/`"（docs/templates 在 skills/ 子目录、principles 在 packs/coding 顶层）— 是 1:1 对齐现有 `harness-flow/skills/docs/` `harness-flow/skills/templates/` 的合理选择，且与现有 6 处 `skills/docs/<file>` 引用直接对齐（design ADR-D8-1 优点行已提及）
   - 但 design ADR-D8-1 没显式解释"为什么 docs/templates 落 skills/ 子目录而 principles 不落 skills/" 的非对称——两者都是 family-level shared asset，layout 不对称应有理由（猜测：principles 不被任何 hf-* skill 引用，只被 AGENTS.md 引用，所以独立顶层；但 ADR 内未写）
   - hf-tasks 阶段可能因这条非对称重新纠结
   - **修复指引**：ADR-D8-1 Decision 段后补一句"为什么 principles 不落 skills/"
   - **锚点**：spec § 4.1 (L184-185)、design § 7 ADR-D8-1 (L146-169)、§ 8.1 (L313-334)

8. **[minor][LLM-FIXABLE][D5]** **§ 13.3 最薄端到端验证路径仅覆盖 Claude Code 一家宿主**，与 FR-806 / ADR-D8-2 三家宿主全装承诺不对等：
   - FR-806 验收 #2 要求"三家宿主目录下 `*/skills/` 子目录数合计 == `N × 3`"
   - § 13.3 Walking Skeleton 只展示 `源 packs/coding/skills/hf-specify/SKILL.md → install_packs() → .claude/skills/hf-specify/SKILL.md → Claude Code skill loader → invoke`
   - cursor / opencode 两家宿主的端到端路径未在 Walking Skeleton 中展示——dogfood smoke 与 manual smoke 都跑三家，但"最薄验证路径"只展示一家弱化了证据完整性
   - **修复指引**：§ 13.3 补充至少展示 cursor 一家（含 `.cursor/skills/hf-specify/SKILL.md` 加载验证），或在路径末尾注明"同样路径适用于 cursor / opencode 仅 install 路径不同"
   - **锚点**：design § 13.3 (L543-554)、FR-806 验收 #2 (L316)

## 缺失或薄弱项

1. **ADR-D8-4 spec acceptance 口径下调缺真人签署机制**（important #1）。design 已正确识别 spec FR-804 / § 2.2 #2 与 CON-801 不可调和，但单方面 reinterpret 已批准 spec 的 acceptance 字面，需要在 design 真人确认环节明确签署该 reinterpretation。
2. **§ 12 NFR 落地与 § 13 测试策略对"新增测试数量"自相矛盾**（important #2）。两处对 4 vs 2 个测试文件的陈述不一致，hf-tasks 阶段无法判断该写多少个测试文件。
3. **§ 10.1 commit 粒度偏大**（important #3）。T1/T4 单 commit 异质动作过多，与 NFR-804 "任一组可独立 review" 意图存在张力，hf-tasks 阶段需要进一步拆分。
4. **§ 17 排除项漏 3 项 spec § 5 deferred**（important #4）。finalize 阶段无法形成完整 backlog 集合等价。
5. **首次 clone 贡献者 IDE 加载链空窗未在 ADR-D8-2 Consequences 显式承接**（minor #5）。
6. **ADR-D8-3 权威源选定缺 git log 证据**（minor #6）。
7. **ADR-D8-1 docs/templates vs principles layout 非对称未解释**（minor #7）。
8. **Walking Skeleton 仅覆盖一家宿主**（minor #8）。

## 下一步

`hf-design`（按本 review 的 1 important USER-INPUT + 3 important LLM-FIXABLE + 4 minor LLM-FIXABLE 做 1 轮定向回修）

回修优先级建议：
- **最先回修 important #1（ADR-D8-4 USER-INPUT）**：design 文档内显式声明"本 ADR 需 spec 真人在 design 真人确认时签署 acceptance 重述"；或父会话决定走 `hf-increment` 修订 spec FR-804 / § 2.2 #2 字面口径；二选一。**这条是本 review 的最重风险**，必须在进入 design 真人确认前关闭路径
- **接着回修 important #2-#4 LLM-FIXABLE**：§ 13/§ 12 测试数量对齐、§ 10.1 commit 拆分边界注明、§ 17 补齐 3 项 deferred；都是机械性 wording 调整，不需要新业务输入
- **最后回修 4 条 minor**：ADR Consequences 补充 / git log 证据 / layout 非对称解释 / Walking Skeleton 补宿主

回修期间不需要向真人提任何 USER-INPUT 问题，**仅 important #1 在回修后进入 design 真人确认时由真人签署 acceptance 重述**。

## 记录位置

`docs/reviews/design-review-F008-coding-pack-and-writing-pack.md`

## 交接说明

- `设计真人确认`：本轮 verdict = `需修改`，**不进入**
- `hf-design`：父会话应把本 review 记录路径与 1 important USER-INPUT + 3 important LLM-FIXABLE + 4 minor LLM-FIXABLE 全部回传给 design 起草会话；预计 1 轮定向回修 + 1 轮 design-review 即可冻结进入 design 真人确认
- `hf-workflow-router`：route / stage / 证据无冲突，不需要 reroute（`reroute_via_router=false`）
- `hf-tasks`：未到拆任务阶段，不进入
- `hf-increment`：仅当父会话或 design 起草会话判断 important #1 选 (b) 路径（修订 spec 字面口径而非 design 内 reinterpret）时，才走 `hf-increment` 改 spec
- 不修改 `task-progress.md`、不修改 F008 spec 文档、不修改 D008 design 文档、不 git commit / push（由父会话执行）

---

## 结构化返回（JSON 摘要）

```json
{
  "conclusion": "需修改",
  "next_action_or_recommended_skill": "hf-design",
  "record_path": "docs/reviews/design-review-F008-coding-pack-and-writing-pack.md",
  "key_findings": [
    "[important][USER-INPUT][D1] ADR-D8-4 实质性下调 spec FR-804 验收 #1 / § 2.2 验收 #2 '装完后引用不 404' 的 acceptance 字面口径，需真人在 design 真人确认环节签署 acceptance 重述或回 hf-increment 改 spec",
    "[important][LLM-FIXABLE][D6] § 12 NFR-802 落地行列 4 个新增测试文件 vs § 13.1 自动化测试表只列 2 个，hf-tasks 阶段无法判断该写多少",
    "[important][LLM-FIXABLE][D5] § 10.1 T1 单 commit 含 7+ 类异质动作 / T4 含 4 类，与 NFR-804 '任一组可独立 review' spec 意图张力",
    "[important][LLM-FIXABLE][D1] § 17 排除项漏列 spec § 5 deferred 3 项（新增 hf-* skill / i18n / 反向同步 user→packs）",
    "[minor][LLM-FIXABLE][D2] ADR-D8-2 候选 C 首次 clone 贡献者 IDE 加载链空窗未在 ADR Consequences 显式承接"
  ],
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "finding_breakdown": [
    {
      "severity": "important",
      "classification": "USER-INPUT",
      "rule_id": "D1",
      "summary": "ADR-D8-4 实质性下调 spec FR-804 验收 #1 / § 2.2 验收 #2 '装完后引用不 404' 字面口径；spec 已批准但 design ADR 单方面重述硬验收语义，需真人在 design 真人确认时签署或回 hf-increment 改 spec"
    },
    {
      "severity": "important",
      "classification": "LLM-FIXABLE",
      "rule_id": "D6",
      "summary": "§ 12 NFR-802 落地行 vs § 13.1 自动化测试表对'新增测试文件数量'自相矛盾（4 vs 2），且 § 12 列出的 test_packs_garage_extended / test_dogfood_layout 在 § 13 无任何描述"
    },
    {
      "severity": "important",
      "classification": "LLM-FIXABLE",
      "rule_id": "D5",
      "summary": "§ 10.1 T1 单 commit 含 22 skill + 11 family asset + drift 反向同步 + pack.json + README + sentinel test 7+ 类异质动作；T4 含 rm -rf + .gitignore + AGENTS.md + 集成测试 4 类，与 spec NFR-804 '任一组可独立 review' 意图张力"
    },
    {
      "severity": "important",
      "classification": "LLM-FIXABLE",
      "rule_id": "D1",
      "summary": "§ 17 排除项漏列 spec § 5 deferred 中 3 项（给 packs/coding/ 加新 hf-* skill / 多语言 i18n / 反向同步 user→packs），finalize 阶段无法形成完整 backlog 集合等价"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "D2",
      "summary": "ADR-D8-2 候选 C Consequences 段未把'首次 clone 贡献者必须先跑 garage init 才能加载 IDE skill'列为已知 trade-off + 未明确 onboarding 指引落 README/AGENTS/CONTRIBUTING 哪一处"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "D3",
      "summary": "ADR-D8-3 称 family 副本是'更新版'但缺 git log/blame 证据；reverse-sync 方向选错可能丢失根级副本的 packs/coding/skills/docs/ 现代路径锚点"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "D5",
      "summary": "ADR-D8-1 选定 packs/coding/skills/{docs,templates}/ + packs/coding/principles/ 与 spec § 4.1 候选 A (packs/coding/{docs,templates,principles}/) 偏差，docs/templates vs principles 非对称未在 ADR 内显式解释"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "D5",
      "summary": "§ 13.3 最薄端到端验证路径仅覆盖 Claude Code 一家宿主，cursor/opencode 路径未展示；FR-806 三家宿主全装承诺与最薄路径展示不对等"
    }
  ]
}
```

---

## 复审 r2

- 复审时间: 2026-04-23
- 复审目标: 验证父会话在 commit `994883e` 中针对 r1 的 1 important USER-INPUT + 3 important LLM-FIXABLE + 4 minor LLM-FIXABLE 是否全部闭合，并评估 finding #1 的 USER-INPUT 收敛路径（双向 wording 同步）是否构成新的 spec drift
- Reviewer: 同 r1 独立 reviewer subagent
- 复审范围: **仅** r1 finding 闭合状态 + 是否引入新风险；不重新执行 D1-D6 全量 rubric

### 结论

**通过**

verdict 理由：r1 列出的 8 条 finding（1 important USER-INPUT + 3 important LLM-FIXABLE + 4 minor LLM-FIXABLE）已**全部闭合**。其中最关键的 finding #1（ADR-D8-4 spec drift）通过"双向 wording 同步" + "design ADR 显式记录路径选择理由（wording-only / 不引入新业务事实）"的合规收敛——spec FR-804 / § 2.2 验收 #2 / § 3.2 场景 3 / § 5 deferred 表均已同步收紧，与 design ADR-D8-4 字面一致；不再存在"spec 写一套 / design 实施另一套"的 drift。其它 7 条 LLM-FIXABLE finding 全部按 review 修复指引落地。

回修过程未引入新设计泄漏、未触动 spec § 4.2 的 6 条 Design Reviewer 可拒红线、未破坏 deferred backlog 范围、未引入新模糊词。所剩 1 条**叙事性残留**（design § 15 任务规划准备度段未与 § 10.1 sub-commit 拆分同步刷新表述，仍写"按 5 类拆 5 个 task"）属 informational，不影响 hf-tasks 阶段拆任务判断（hf-tasks 自然会读 § 10.1 取 9 个 sub-commit），故判 `通过`，下一步 `设计真人确认`。

### 8 条 r1 finding 闭合状态

| # | r1 finding | 闭合状态 | 证据锚点（spec / design 行号）|
|---|---|---|---|
| 1 | [important][USER-INPUT][D1] ADR-D8-4 实质性下调 spec FR-804 验收 #1 / § 2.2 验收 #2 字面口径 | **已闭合** | spec § 2.2 验收 #2（L106 改为分两层口径 + 显式承认 D7 边界 + 引用 ADR-D8-4 + 指向 § 5 D9 候选）；spec § 3.2 场景 3（L155 同步分两层）；spec FR-804 验收 #1（L294-295 拆为 packs 源端 + 下游宿主端两条 acceptance）；spec § 5 deferred 新增 D7 管道扩展行（L252）；design ADR-D8-4 文末新增 "Spec acceptance 同步收紧" 段（L256-267）显式说明走 wording-only 路径而非 hf-increment 的理由（无新业务事实） |
| 2 | [important][LLM-FIXABLE][D6] § 12 NFR-802 vs § 13.1 测试数量自相矛盾 | **已闭合** | design § 13.1（L577-589）已扩到 4 个测试文件清单，每文件含"覆盖 spec FR/NFR" + "触发 INV" + "落地 commit" 三列；design § 12 NFR-802 落地行（L570）改为指向 § 13.1 表，二者一致；新增"测试执行顺序"段（L589）说明 T1c 先于 T4c 落地的依赖原因 |
| 3 | [important][LLM-FIXABLE][D5] § 10.1 T1/T4 commit 粒度偏大 | **已闭合** | design § 10.1（L455-510）已显式拆 T1→T1a/T1b/T1c + T4→T4a/T4b/T4c，合计 9 个 sub-commit；每个 sub-commit 都有清晰 commit message 模板与动作清单；§ 10.1 开头段（L457）显式声明"hf-tasks 阶段拆分粒度不能比此更粗"，把 spec NFR-804 "任一组可独立 review" 意图固化 |
| 4 | [important][LLM-FIXABLE][D1] § 17 排除项漏列 spec § 5 deferred 3 项 | **已闭合** | design § 17（L656-670）补齐 3 项："给 packs/coding/ family 加新 hf-* skill"（L663）/ "多语言 / i18n 版本"（L668）/ "反向同步：用户在 .claude/skills/ 改了之后回流到 packs/"（L669）；§ 17 段首（L654）显式标注"与 spec § 5 形成完整集合等价" |
| 5 | [minor][LLM-FIXABLE][D2] ADR-D8-2 候选 C onboarding 指引落地位置缺失 | **已闭合** | design § 7 ADR-D8-2 Consequences 段（L195）新增专门 bullet：明确 onboarding 指引落 `AGENTS.md` 顶部段落（单源） + `README.md` / `CONTRIBUTING.md` 仅 link 指向（不重复落字 + 保持单源）+ 由 hf-tasks T4 commit 承接 |
| 6 | [minor][LLM-FIXABLE][D3] ADR-D8-3 权威源选定缺 git log 证据 | **已闭合** | design § 7 ADR-D8-3 新增 "权威源选定证据" 段（L214-221）：含 git log -1 时间戳表 + commit hash + 命名术语对比 + 路径锚点对比；明确说明为何选 family 副本（时间维度晚 3 天 + 术语维度与本仓库现实一致 + 副作用：路径表达完整性 < 术语正确性 的权衡）；具体动作段（L230）补充第 5 点说明副作用 |
| 7 | [minor][LLM-FIXABLE][D5] ADR-D8-1 docs/templates vs principles layout 非对称未解释 | **已闭合** | design § 7 ADR-D8-1 Decision 段后（L160-163）新增专门段："为什么 docs/templates 落 skills/ 子目录而 principles 不落"，含实测证据（hf-* SKILL.md 内 6 处引用 `skills/docs/<file>` / `templates/<file>` vs principles 仅被根级 AGENTS.md 引用 0 处 hf-* 内引用）+ 解释为什么 layout 非对称是"更准确反映用法"而非偏差 |
| 8 | [minor][LLM-FIXABLE][D5] § 13.3 Walking Skeleton 仅覆盖 Claude Code 一家宿主 | **已闭合** | design § 13.3（L600-614）已改为三家宿主对称展示：Walking Skeleton 图 ASCII 含 claude / cursor / opencode 三条同构路径；段尾段（L614）显式说明"三条路径在管道层完全对称（同 install_packs() 入口、同 marker 注入、仅 host adapter 给的 target_skill_path 不同）"，dogfood smoke 一次性覆盖三家 |

### Finding #1 USER-INPUT 收敛路径合规性独立评估

r1 finding #1 标记为 USER-INPUT 的核心理由是："spec 已批准的 acceptance 字眼未变，由 design ADR 单方面重述硬验收的语义属于 spec drift 风险"。父会话选择 reviewer 提供的"二选一"中**路径 (a) 的等价 LLM-FIXABLE 版本**——双向 wording 同步：spec 字面与 design ADR 同步收紧到一致 wording。

本 reviewer 独立评估该收敛路径是否合规：

| 评估维度 | 结论 | 证据 |
|---|---|---|
| 是否引入新业务事实 | **否** | spec FR-804 / § 2.2 / § 3.2 仅修改 acceptance wording 把口径下调到与 D7 管道实际能力一致；spec § 5 新增 D9 候选行也只是显式记录"管道扩展"作为 deferred backlog；不涉及任何新功能 / 新约束 / 新外部依赖 / 新业务规则 |
| 是否仍存在 spec / design 字面 drift | **否** | spec FR-804 验收 #1（L293-295）已拆为 packs 源端 + 下游宿主端两条 acceptance；spec § 2.2 验收 #2（L106）已重述同样口径；design ADR-D8-4（L243-278）字面与 spec 一致 |
| 是否需要单独 hf-increment cycle | **否** | hf-increment 适用于"用户明确要求增删改需求/范围/验收/约束"。本次 wording-only 修订属于"内部 spec / design 双向 wording 同步"，且 design ADR-D8-4 文末已显式记录路径选择理由（L267：wording-only 修订，不引入新业务事实，符合 spec-review LLM-FIXABLE 分类规则）。开 hf-increment cycle 的 review surface 与 wording 调整成本比例失衡 |
| 是否破坏已批准 spec 的核心范围 | **否** | spec § 2.1 核心目标 / § 4.1 包含 / § 4.2 6 条红线 / § 5 已 deferred 集合（除新增 1 行 D9 候选） / FR-801..807 / NFR-801..804 / CON-801..804 / ASM-801..804 全部不变；只修改了 FR-804 / § 2.2 / § 3.2 中"装后宿主目录引用可达"这一原本就被 D7 管道实际能力击穿的硬验收字面口径 |
| 是否需要在 design 真人确认环节单独签署 | **否（建议）** | design ADR-D8-4 "Spec acceptance 同步收紧" 段（L256-267）已经把整个收敛路径决策显式落进 design 文档；design 真人确认环节按惯常流程让真人对整份 design 签字背书时，自然吸收对该 ADR 的批准。无需额外 USER-INPUT 询问 |

**结论**：finding #1 的 USER-INPUT 收敛路径（双向 wording 同步）**合规闭合**，不构成新的 spec drift；不需要回 hf-increment；不需要在 design 真人确认环节单独签署。reviewer 收回 r1 对 finding #1 的 USER-INPUT 标记。

### 新风险（不构成新 finding，但需父会话知晓）

- **[新风险/叙事性残留][D5]** design § 15（L628-635）任务规划准备度段未与 § 10.1 sub-commit 拆分同步刷新表述，仍写"按 5 类拆 5 个 task" + "T4 是关键合流点（rm -rf + .gitignore + AGENTS.md + 集成测试）需注意原子性"——后者与 § 10.1 已拆 T4a/T4b/T4c 不一致。这条仅是元信息表述与 § 10.1 同步性问题，不影响 hf-tasks 阶段拆任务判断（hf-tasks 自然会读 § 10.1 取 9 个 sub-commit 而非 § 15 文字描述），但建议父会话在 design 真人确认时顺手把 § 15 表述更新为"§ 10.1 拆出 9 个 sub-commit，hf-tasks 可一对一 1:1 落地或视情况再合并；T4a 是关键合流点（rm -rf + .gitignore），需注意原子性"。
- **[新风险/叙事性残留][D5]** design § 11.1 INV-1 / INV-3 / INV-4 等不变量"责任 commit"列仍写 T1 / T4，未与 § 10.1 sub-commit 拆分同步（应为 INV-3 责任 = T1c / INV-1 责任 = T4c / INV-4 责任 = T1a / T2 / T3 等）。同样不影响 hf-tasks 拆任务判断（INV 与 commit 的细粒度对齐 hf-tasks 自然会做），仅 wording 同步性问题。
- **[新风险/无设计层缺口]** 未发现新设计泄漏、未发现新模糊词、未发现新 USER-INPUT 缺失、未发现 deferred backlog 范围溢出、未发现新触发 spec § 4.2 6 条红线。

### 下一步

`设计真人确认`（interactive 模式下父会话向真人确认 design；auto 模式下父会话写 design approval record 后进入 `hf-tasks`）

设计真人确认环节的关注点（按重要度排序）：

1. **finding #1 USER-INPUT 收敛路径的最终确认**：真人对 ADR-D8-4 "Spec acceptance 同步收紧" 段（design L256-267）+ spec FR-804 / § 2.2 验收 #2 / § 3.2 场景 3 / § 5 D9 候选行 wording 同步背书。本 reviewer 已独立评估该路径合规，但真人最终拍板是否接受这种"design 阶段消化掉 spec 起草时未充分察觉的工程边界"的处理方式
2. **§ 15 / § 11.1 与 § 10.1 sub-commit 拆分同步性的叙事性清理**（informational，不阻塞）
3. **8 项 ADR 整体决策方向**：尤其 ADR-D8-2 候选 C（删除 + dogfood）+ ADR-D8-3 反向同步 + ADR-D8-4 文档级提示三项是本 cycle 最具长期影响的决策

接下来 `hf-tasks` 阶段必须按 design 收敛的 9 个 sub-commit（T1a/T1b/T1c/T2/T3/T4a/T4b/T4c/T5）拆任务，每个任务含：(a) 实施动作清单（已在 § 10.1 给出）(b) 触发 INV（已在 § 11.1 给出）(c) 关联 spec FR/NFR/CON（已在 § 3 追溯表 + § 13.1 测试表给出）(d) 完成 acceptance（按 spec § 4.2 6 条红线 + design § 10.2 验证步骤）。

### 复审记录位置

`docs/reviews/design-review-F008-coding-pack-and-writing-pack.md`（与 r1 同文件，本段为 `## 复审 r2` 追加段）

### 交接说明

- `设计真人确认`：本轮 r2 verdict = `通过`，父会话应执行 design approval step（interactive 等待真人 / auto 写 design approval record）；执行后由父会话同步 `task-progress.md` Current Stage 与 design 文档状态字段（`草稿` → `已批准`）。
- `hf-design`：r2 已通过，无需回修；建议父会话在 approval step 顺手清理 § 15 / § 11.1 与 § 10.1 sub-commit 拆分的叙事性同步残留（零成本叙事一致性修复）。
- `hf-workflow-router`：route / stage / 证据无冲突，不需要 reroute（`reroute_via_router=false`）。
- `hf-tasks`：approval 完成后才进入；不在 r2 verdict 直接触发范围。
- `hf-increment`：finding #1 USER-INPUT 收敛路径合规闭合，不需要走 hf-increment。
- 不修改 `task-progress.md`、不修改 spec / design 文档、不 git commit / push（由父会话执行）。

### 结构化返回 r2 (JSON)

```json
{
  "conclusion": "通过",
  "next_action_or_recommended_skill": "设计真人确认",
  "record_path": "docs/reviews/design-review-F008-coding-pack-and-writing-pack.md",
  "key_findings": [
    "r1 1 important USER-INPUT + 3 important LLM-FIXABLE + 4 minor LLM-FIXABLE 全部闭合（8 closed / 0 open / 0 regressed）",
    "finding #1 USER-INPUT 双向 wording 同步合规闭合：spec FR-804 / § 2.2 / § 3.2 / § 5 与 design ADR-D8-4 字面一致，无新业务事实，不需要 hf-increment",
    "新风险仅 2 条叙事性残留（§ 15 任务规划准备度段 + § 11.1 INV 责任 commit 列未与 § 10.1 sub-commit 拆分同步刷新），不阻塞 design 真人确认"
  ],
  "needs_human_confirmation": true,
  "reroute_via_router": false,
  "finding_breakdown_r1_closure": [
    {"id": 1, "severity_r1": "important", "classification_r1": "USER-INPUT", "rule_id": "D1", "closure_status": "已闭合", "evidence": "spec § 2.2#2 (L106) + § 3.2 场景 3 (L155) + FR-804 验收 #1 (L294-295) + § 5 D9 候选 (L252) 均同步收紧；design ADR-D8-4 'Spec acceptance 同步收紧' 段 (L256-267) 显式记录走 wording-only LLM-FIXABLE 路径理由；reviewer 独立评估该路径合规，收回 USER-INPUT 标记"},
    {"id": 2, "severity_r1": "important", "classification_r1": "LLM-FIXABLE", "rule_id": "D6", "closure_status": "已闭合", "evidence": "design § 13.1 测试表扩到 4 文件 + 每文件含覆盖 spec FR/NFR/INV/落地 commit 三列 + 测试执行顺序段 (L577-589)；§ 12 NFR-802 (L570) 同步指向 § 13.1"},
    {"id": 3, "severity_r1": "important", "classification_r1": "LLM-FIXABLE", "rule_id": "D5", "closure_status": "已闭合", "evidence": "design § 10.1 (L455-510) 已拆 T1→T1a/T1b/T1c + T4→T4a/T4b/T4c 共 9 sub-commit；段首 L457 显式约束 hf-tasks 拆分粒度下限"},
    {"id": 4, "severity_r1": "important", "classification_r1": "LLM-FIXABLE", "rule_id": "D1", "closure_status": "已闭合", "evidence": "design § 17 (L656-670) 补齐 3 项 spec § 5 deferred；段首 L654 标注与 spec § 5 集合等价"},
    {"id": 5, "severity_r1": "minor", "classification_r1": "LLM-FIXABLE", "rule_id": "D2", "closure_status": "已闭合", "evidence": "design ADR-D8-2 Consequences 段 L195 新增 onboarding 指引落 AGENTS.md 单源 + README/CONTRIBUTING 仅 link + hf-tasks T4 commit 承接"},
    {"id": 6, "severity_r1": "minor", "classification_r1": "LLM-FIXABLE", "rule_id": "D3", "closure_status": "已闭合", "evidence": "design ADR-D8-3 新增'权威源选定证据'段 (L214-221) git log + 术语 + 路径锚点对比 + 选 family 副本理由 + 副作用说明 (L230)"},
    {"id": 7, "severity_r1": "minor", "classification_r1": "LLM-FIXABLE", "rule_id": "D5", "closure_status": "已闭合", "evidence": "design ADR-D8-1 Decision 后段 (L160-163) 新增 docs/templates 与 principles layout 非对称解释 + 实测 6 处 vs 0 处 hf-* 内引用证据"},
    {"id": 8, "severity_r1": "minor", "classification_r1": "LLM-FIXABLE", "rule_id": "D5", "closure_status": "已闭合", "evidence": "design § 13.3 (L600-614) Walking Skeleton 改三家宿主对称展示 + 段尾说明三条路径管道层对称"}
  ],
  "new_risks": [
    {"severity": "informational", "rule_id": "D5", "summary": "design § 15 任务规划准备度段表述未与 § 10.1 sub-commit 拆分同步刷新（仍写'按 5 类拆 5 个 task' / 'T4 是关键合流点'），与 § 10.1 已拆 T4a/T4b/T4c 不一致；不影响 hf-tasks 判断，建议在 design 真人确认时顺手清理"},
    {"severity": "informational", "rule_id": "D5", "summary": "design § 11.1 INV 责任 commit 列仍写 T1/T4，未与 § 10.1 sub-commit 拆分同步（应为 INV-3=T1c, INV-1=T4c, INV-4=T1a/T2/T3 等）；同上仅叙事性残留"}
  ]
}
```
