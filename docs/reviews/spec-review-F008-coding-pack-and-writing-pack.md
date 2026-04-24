# Spec Review — F008 Garage Coding Pack 与 Writing Pack

- 评审目标: `docs/features/F008-garage-coding-pack-and-writing-pack.md`（草稿，2026-04-22）
- Reviewer: 独立 reviewer subagent（按 `hf-spec-review` skill 执行）
- 评审时间: 2026-04-22
- 上游证据基线: `task-progress.md`（Stage=`hf-specify` / Profile=`full` / Mode=`auto`）、`docs/features/F007-garage-packs-and-host-installer.md`（已批准）、`packs/README.md`、`packs/garage/pack.json`、`.agents/skills/` 现状清点

## 结论

需修改

verdict 理由：F008 spec 范围清晰、动机充分、与 F007 边界清楚、deferred backlog 显式、ASM/CON 完整，方向上完全可作为 design 的稳定输入。但发现 **3 条事实性数字错配（`hf-*` 数 / 总 SKILL.md 数 / 现状摩擦 #6）** 与 **1 条把 stdout marker 数字过早写死的可验证性风险**，以及 **2 条 LLM-FIXABLE 的 wording / classification 问题**。这些 finding 都能在 1 轮定向回修内闭合，不破坏核心范围、不需要新业务输入，因此判 `需修改` 而非 `阻塞`。

## 发现项

### Critical

无 critical 级 finding。

### Important

- [important][LLM-FIXABLE][Q1/Q3] **§ 1 表 + § 2.1 + § 4.1 + FR-801 + § 1 标题数字与仓库实际不符**：
  - F008 spec 标题与 § 1 # 1 称 `.agents/skills/` 下"26 个已写好 skills"；§ 1 表又写 "22 个 hf-* + 1 个 using-hf-workflow = 23"；§ 2.1 与 § 4.1 与 FR-801 验收都暗示 `packs/coding/` 含 "23 hf-* + using-hf-workflow = 24 skill"。
  - 实测仓库现状（`ls -d .agents/skills/harness-flow/skills/hf-*/` = 21；`find .agents/skills/ -name SKILL.md -type f | wc -l` = 28）：实际是 **21 个 hf-* + 1 个 using-hf-workflow + 4 个 write-blog + 1 个 find-skills + 1 个 writing-skills = 28 个 source SKILL.md**，加 F007 已落 `garage-hello` 后总 29 与 spec § 2.2 验收 #1 的 "29 skills" 数字一致，但中间分项几乎全错（hf-* 22→21、coding skills[] 24→22）。
  - 修复指引：把 § 1 表、§ 2.1 ASCII 树注释（"23 hf-*"）、§ 4.1 包含表（`skills[24]`）、FR-801 需求陈述与验收标准（"24 个 hf-* + using-hf-workflow"、`skills[]` 长度 = 24 → 22）、ASM-801（"26 个 SKILL.md" → "28 个 SKILL.md"）按现状改一次；29 这个总数侧（NFR / smoke / FR-806）保持。
  - 锚点：F008 spec L2、L33-45（§ 1 表）、L60-76（§ 2.1）、L182-184（§ 4.1）、L242-246（FR-801）、L390-396（ASM-801）；现状证据 `ls -d .agents/skills/harness-flow/skills/hf-*/`。

- [important][LLM-FIXABLE][Q1/A5] **§ 1 现状摩擦 #6 事实错误**：
  - spec 称 `AGENTS.md § "Skill 写作原则" 引用的 docs/principles/skill-anatomy.md 在仓库根不存在`。
  - 实测：`docs/principles/skill-anatomy.md` 真实存在（16707 字节，2026-04-22 mtime），且与 `.agents/skills/harness-flow/docs/principles/skill-anatomy.md`（16637 字节）**已存在内容 drift**——这是事实状态，且引出一个 spec 未识别的处置问题（drift 的两份哪份是真源、F008 收敛后只能留一份）。
  - 修复指引：把 #6 改写为"实际存在且已与 `.agents/skills/harness-flow/docs/principles/skill-anatomy.md` 内容 drift（70 字节差异）"，并在 § 4 / FR-804 / FR-807 中显式加一条："F008 落地时必须确定 `docs/principles/skill-anatomy.md` 与 `.agents/skills/harness-flow/docs/principles/skill-anatomy.md` 中哪一份是规范源（design 决定），另一份必须删除或反向同步，**不允许 cycle 后仍存在 drift 的双副本**"。
  - 锚点：F008 spec L54（# 6）；FR-804 验收 #3（L276）、FR-807 验收 #2（L311）。

- [important][LLM-FIXABLE][C6/A3] **§ 2.2 验收 #1 + FR-806 验收 #1 把 stdout marker 数字写死为 "29"**：
  - `Installed 29 skills, 0 agents` 是字面 acceptance condition。但 spec 同时把 (a) 是否纳入 `garage-hello` (b) 是否保留 `garage-sample-agent` (c) `.agents/skills/` 处置方案 (d) `find-skills`/`writing-skills` 是否归 `packs/garage/` 还是 `packs/meta/` 全部放权给 design（§ 11 阻塞性问题第 1 项 "spec 默认假设归 garage/"、§ 4.2 边界 "保留还是删除由 design 决定"）。
  - 风险：design 阶段任一决策变化（如：`garage-sample-agent` 删除，agents 数变 -1；`find-skills` 移到 `packs/meta/`，packs/garage/ skills[] 仍 3 但分布变；某 hf-* 搬迁失败必须延后）都会让 spec 验收硬码的 "29" 失效，逼回 spec。
  - 这条问题之所以是 LLM-FIXABLE（不是 USER-INPUT）：解决方案是把验收陈述从字面值松绑到 invariant：例如 "stdout marker 含 `Installed N skills, M agents` 形式且 N == sum of (3 个 pack.json 的 skills[] 长度) == files_per_host"，让数字派生于 pack.json 而不是硬码。这种 wording 调整不需要新业务输入。
  - 修复指引：§ 2.2 验收 #1、§ 3.2 场景 1/2、FR-806 验收 #1 / #2 / #3 中的 "29" 全部改为派生表达；保留 "目前预期值 = 29" 作为参考注释。
  - 锚点：F008 spec L103（§ 2.2 #1）、L139-151（§ 3.2 场景 1/2）、L294-298（FR-806）。

- [important][LLM-FIXABLE][C2/A3] **§ 4 + FR-804/FR-805 把两个核心 layout 决策完全放权给 design，但又用 § 2.2 / FR-804/805 验收硬约束 "design 选定后必须满足 X"，缺少给 design reviewer 的可判定边界**：
  - § 11 非阻塞 #1（family-level 资产 A/B/C 候选）、§ 11 非阻塞 #2（`.agents/skills/` 处置 A/B/C 候选）放权给 design 是合理的。但 spec 没明确写出 design reviewer 用什么 acceptance 判一个 ADR 是不是"对的"——只给了"装完后引用不 404"（FR-804 验收 #1）和"IDE 加载链不破"（FR-805 验收 #2，且验证方式由 design 自定）。
  - 风险：到了 design / design-review 阶段，reviewer 没有 spec 层 anchor 决定 "复制到每个 hf-* skill 的 references/" 这种臃肿但可行的方案是否合规，反而会掉头回 spec。
  - 修复指引：在 § 4 或 FR-804 / FR-805 加一条 "判 design 收敛是否合规的最低标准"：例如 (a) 对 family-level 资产：去重一次、不允许同一文件出现两份磁盘副本；(b) 对 `.agents/skills/` 处置：选定后 `git status` 干净、不允许遗留 dead 文件、不允许 mtime drift；(c) 显式枚举 design reviewer 可拒的反模式（如 "把 11 个 family asset 复制到每个 hf-* skill 下，导致 22 × 11 = 242 份冗余" 应被否决，或被允许但需注明）。这些是 LLM 可写的判定边界，不是新业务事实。
  - 锚点：F008 spec L191-196（§ 4.2）、L272-276（FR-804）、L283-286（FR-805）、L432-434（§ 11 非阻塞 1/2）。

### Minor

- [minor][LLM-FIXABLE][Q5/C2] **`packs/coding/` family-level 资产 11 项里包括两份 principles，但 spec 没明示这两份 principles 与 `docs/principles/skill-anatomy.md` 仓库根副本的关系**：
  - spec § 4.1 把 `principles/ (2 个 family principles：skill-anatomy / hf-sdd-tdd-skill-design)` 放进 `packs/coding/`，但根级 `docs/principles/skill-anatomy.md` 不在 `packs/coding/` 下、也不在 `.agents/` 下，是被 `AGENTS.md § "Skill 写作原则"` 直接引用的"项目级"principle 入口。F008 spec 没说 cycle 完成后是 (a) 删除根级、统一指向 `packs/coding/principles/`；(b) 保留根级、`packs/coding/principles/` 是 family 内私有副本；(c) 使根级成为软链。
  - 与上面 important #2 的 drift finding 同根，但严重度低一档因为可在 design 阶段一次性收敛；提到这里是为了 design reviewer 不漏掉。
  - 锚点：F008 spec L183（§ 4.1 family-level 资产行）、L308（FR-807 验收 #2 暗示 `AGENTS.md § "Skill 写作原则"` 引用路径同步）。

- [minor][LLM-FIXABLE][C7] **ASM-801 文本与现状描述不符（"26 个 SKILL.md"），且 "git history 显示 .agents/skills 在最近 1 个月内只有 blog 内容相关 commit (#21)" 的事实没有被 spec 给出可回读锚点**：
  - 这是 assumption visibility 问题：reviewer / design reader 无法验证 #21 commit 是哪一个；建议改为引用 `git log --oneline .agents/skills/ | head -5` 输出节选或具体 commit hash。
  - 数字 "26" 同 important #1，一并改。
  - 锚点：F008 spec L390-396（ASM-801）。

- [minor][LLM-FIXABLE][G3] **FR-801 / FR-802 / FR-803 三条 FR 是按 pack 维度切的，每条 FR 内部仍打包 (a) `pack.json` 落盘 (b) `README.md` 落盘 (c) skill 子目录字节级搬迁 (d) 子目录附属内容搬迁四个动作**：
  - 严格按 GS3 / GS4 看是有"场景爆炸"嫌疑，但因为搬迁是机械动作 + 三个 pack 的内部结构同构，再拆会带来更多噪声。属于可接受的合并粒度。reviewer 不要求拆分，仅记录该 finding 让 design / tasks 阶段心里有数：tasks 拆分时应按 pack 拆 commit（与 NFR-804 已有约定一致），不要按 skill 维度爆破。
  - 锚点：F008 spec L240-266（FR-801/802/803）、L348-350（NFR-804）。

## 缺失或薄弱项

1. **`docs/principles/skill-anatomy.md` 与 `.agents/skills/harness-flow/docs/principles/skill-anatomy.md` 的双副本 drift 处理策略**（见 Important #2）。spec 未识别这是一个独立于 `.agents/skills/` 处置的问题。
2. **stdout marker 与 acceptance 数字硬码** 与 cycle 中可能的 design 决策弹性（agents 是否保留 `garage-sample-agent`）耦合（见 Important #3）。
3. **design reviewer 的判定边界**：对放权给 design 的两个 ABC 决策，spec 未提供"什么样的 design 收敛会被 design-review 直接 block"的最低 acceptance（见 Important #4）。
4. **FR-805 验收 #2 的"IDE 加载链不破"验证方式由 design 自定**：宽松度合理（spec 不指定具体 IDE log / cursor MCP / find 输出形式），但应至少要求 "在 PR walkthrough 提交可重放证据"，否则 cycle 收尾时审计困难。spec 现状表述（"manual 截图 / find 输出 / IDE 日志 / cursor MCP 调用"）已经枚举得不错，可不强求修改，记录在此供 design 注意。

## 下一步

`hf-specify`（按本 review 的 4 条 important + 3 条 minor 做 1 轮定向回修；预计回修后即可 `通过`）

回修建议聚焦：
- 把 `21 hf-* / 28 source SKILL.md / 22 packs/coding/skills[]` 这三个数字一次性改对（important #1）
- 把 § 1 # 6 的 "不存在" 改为 "存在且已 drift"，并显式把 drift 处置写入 § 4 / FR-804 / FR-807（important #2）
- 把 stdout marker 的 acceptance 从字面值 "29" 改为派生表达（important #3）
- 给 design reviewer 加判定边界（important #4）

回修期间不需向真人提任何 USER-INPUT 问题——所有 finding 均 LLM-FIXABLE。

## 记录位置

`docs/reviews/spec-review-F008-coding-pack-and-writing-pack.md`

## 交接说明

- `规格真人确认`：本轮 verdict = `需修改`，不进入。
- `hf-specify`：父会话应把本 review 记录路径与 4 条 important + 3 条 minor 全部回传给负责 spec 修订的会话；预计 1 轮定向回修 + 1 轮 review 即可冻结进入 design。
- `hf-workflow-router`：route / stage / 证据无冲突，不需要 reroute（`reroute_via_router=false`）。
- 不修改 `task-progress.md`、不修改 F008 spec 文档、不 git commit / push（由父会话执行）。

---

## 复审 r2

- 复审时间: 2026-04-22
- 复审目标: 验证父会话在 commit `8dc0cfe` 中针对 r1 的 4 important + 3 minor finding 是否全部闭合
- Reviewer: 同 r1 独立 reviewer subagent
- 复审范围: **仅** r1 finding 闭合状态 + 是否引入新风险；不重新执行 Q/A/C/G 全量 rubric

### 结论

通过

verdict 理由：r1 列出的 4 important + 3 minor 全部 LLM-FIXABLE finding 已全部闭合到 acceptance shape 层；spec body 的事实数字、stdout marker 解耦、design reviewer 红线、drift 收敛不变量全部落到位。回修过程未引入新设计泄漏、未引入新模糊词、未破坏 deferred backlog 范围；所剩仅 1 条**叙事性数字残留**新风险（标题与 § 关联段中 "26 skills" 字样未与 spec body 的 28/29 同步），不属于 acceptance / 验收标准、不影响 design 启动判断，故判 `通过`，下一步 `规格真人确认`。

### 7 条 r1 finding 闭合状态

| # | r1 finding | 闭合状态 | 证据锚点（F008 spec 行号）|
|---|---|---|---|
| 1 | [important][LLM-FIXABLE][Q1/Q3] 数字错配 (hf-* 22→21、总 SKILL.md 26→28、coding skills[] 24→22) | **已闭合** | L33-46（§ 1 表已改 21 hf-* + 1 using-hf-workflow，合计 28 source SKILL.md，并加 `find` 实测命令锚点）；L61, L69, L184（§ 2.1 + § 4.1 表已改 22 项）；L259-264（FR-801 已改 21+1=22，且加 `ls .agents/skills/harness-flow/skills/ \| grep -c '^hf-' == 21` 实测基线作为 acceptance Given）；L290（FR-804 改 "22 个 packs/coding/skills/* SKILL.md"）；L411-415（ASM-801 改 28 + 加 `find -maxdepth 4` 实测命令锚点）|
| 2 | [important][LLM-FIXABLE][Q1/A5] § 1 #6 事实错误 + drift 治理缺失 | **已闭合** | L55（§ 1 #6 已改写为"实际存在 16707 字节 + 与 16637 字节 family 副本 drift + 给出 AHE→HF rename 解释 + 显式声明 cycle 后不允许双副本并存"）；L91, L189（§ 2.1 + § 4.1 新增 drift 收敛行）；L296（FR-804 验收 #5 新增 `diff` 输出为空的 drift 收敛不变量）；L456（§ 11 非阻塞 #3 新增三选一收敛策略）|
| 3 | [important][LLM-FIXABLE][C6/A3] stdout marker 数字硬码 "29" | **已闭合** | L85（§ 2.1 ASCII 树后已加"验收侧不锁死字面 29，由 manifest 派生"）；L105（§ 2.2 #1 已改 `Installed N skills, M agents`，N/M 派生于 pack.json）；L107（§ 2.2 #3 同步派生表达）；L130（§ 3.1 用户角色"约 29"措辞松绑）；L141, L150-152, L176（§ 3.2 场景 1/2/7 全部改派生 N）；L315-317（FR-806 验收 #1/#2/#3 全部派生）；L327（FR-807 文档段同步派生）|
| 4 | [important][LLM-FIXABLE][C2/A3] design reviewer 缺判定边界 | **已闭合** | L206-217（§ 4.2 末新增 "Design Reviewer 可拒红线" 段含 6 条具体可拒条款，覆盖去重不变量 / git status 干净 / drift 收敛 / AGENTS.md 链 / 本仓库 IDE / F007 管道动到）；L295（FR-804 验收 #4 加去重不变量与 § 4.2 红线呼应）；L307（FR-805 验收 #4 加 git status 干净不变量 + lint 守门必须三选一具体实施位置）；L454-456（§ 11 非阻塞 #1/#2/#3 全部加 "前提是 § 4.2 红线 X 同时满足" 字眼，把 design 决策与 spec 红线锚定）|
| 5 | [minor][LLM-FIXABLE][Q5/C2] root vs family 双 principles 入口关系未明示 | **已闭合**（与 important #2 同根，统一在 § 4.1 drift 收敛行 + § 11 非阻塞 #3 三个候选策略 + FR-804 验收 #5 中处理）| L189, L296, L456 |
| 6 | [minor][LLM-FIXABLE][C7] ASM-801 数字 + commit 锚点缺失 | **已闭合** | L411-417（ASM-801 数字改 28 + 来源段加 commit hash 锚点 `093ffed Merge #21` / `b249ed0` / `c40679e` + 实测命令）|
| 7 | [minor][LLM-FIXABLE][G3] FR-801/802/803 合并粒度 | **已闭合**（r1 显式说"属可接受合并粒度，不要求拆分"）| 无修改要求；现状沿用 NFR-804 commit 分组（L368-371）已满足 |

### 新风险（不构成新 finding，但需父会话知晓）

- **[新风险/叙事性残留][Q1/L1+L10]** 标题 `让 garage init 真正交付"挂上目录就有 26 skills"` 与 § 关联段 `本 cycle 把可分发 skills 从 1 推到 26` 仍残留旧数字 "26"。这些是 spec 元信息（标题 / 关联引用）而非 acceptance / 验收标准，不影响 design / design-review / tasks 任一阶段的判断，但与 spec body 的 28 source / 22 packs/coding skills[] / 29 total 已不一致。建议父会话在 `规格真人确认` 这一节点顺手清理这两处叙事性 wording（从 "26" 改为 "29"，与 § 1 末句 `本 cycle 落地后总 packs SKILL.md 数 = 29` 对齐），但不强制阻塞 verdict。
- **[新风险/无]** 未发现新设计泄漏、未发现新模糊词、未发现 USER-INPUT 缺失、未发现 deferred backlog 范围溢出。

### 下一步

`规格真人确认`（interactive 模式下父会话向真人确认 spec；auto 模式下父会话写 approval record 后进入 `hf-design`）

接下来 `hf-design` 阶段必须收敛的 design 决策（spec 已显式放权 + 给出 § 4.2 可拒红线作为判定边界）：
1. family-level 11 个资产物理位置（A/B/C 候选）+ 去重方案
2. `.agents/skills/` 处置方案（A/B/C 候选）+ 若选 B 必须给出 lint 三选一具体位置
3. `docs/principles/skill-anatomy.md` drift 收敛策略（三选一）
4. `packs/garage/garage-sample-agent` 处置 + `pack.json.version` bump 策略

### 复审记录位置

`docs/reviews/spec-review-F008-coding-pack-and-writing-pack.md`（与 r1 同文件，本段为 `## 复审 r2` 追加段）

### 交接说明

- `规格真人确认`：本轮 r2 verdict = `通过`，父会话应执行 approval step（interactive 等待真人 / auto 写 approval record）；执行后由父会话同步 `task-progress.md` Current Stage 与规格状态字段（`草稿` → `已批准`）。
- `hf-specify`：r2 已通过，无需回修；建议父会话在 approval step 顺手把标题 / § 关联段 "26 skills" 残留更新为 "29 skills"，作为零成本叙事一致性修复。
- `hf-workflow-router`：route / stage / 证据无冲突，不需要 reroute。
- 不修改 F008 spec 文档（只读复审）、不修改 `task-progress.md`、不 git commit / push（由父会话执行）。
