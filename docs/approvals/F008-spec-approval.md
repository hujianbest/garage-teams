# Approval Record - F008 Spec

- Artifact: `docs/features/F008-garage-coding-pack-and-writing-pack.md`
- Approval Type: `specApproval`
- Approver: cursor cloud agent (auto-mode policy approver)
- Date: 2026-04-22
- Workflow Profile / Execution Mode: `full` / `auto`
- Workspace Isolation: `in-place`（工作分支 `cursor/f008-coding-pack-and-writing-pack-bf33`）

## Evidence

- Round 1 review: `docs/reviews/spec-review-F008-coding-pack-and-writing-pack.md`（R1 段） — `需修改`
  - 0 critical / 4 important / 3 minor（全部 LLM-FIXABLE，USER-INPUT = 0）
  - F-1 [important][Q1/Q3] § 1 表 + § 2.1 + § 4.1 + FR-801 + ASM-801 数字与仓库实际不符（hf-* 22→21、source 26→28、`packs/coding/skills[]` 24→22）
  - F-2 [important][Q1/A5] § 1 #6 事实错误：`docs/principles/skill-anatomy.md` 实际存在且与 `.agents/skills/harness-flow/docs/principles/skill-anatomy.md` 已 drift
  - F-3 [important][C6/A3] § 2.2 / FR-806 / § 3.2 把 stdout marker 字面值 "29" 锁死，与 design 决策弹性冲突
  - F-4 [important][C2/A3] FR-804 / FR-805 把核心 layout 决策放权给 design 但缺最低判定边界
  - F-5 [minor][Q5/C2] root-level vs family principles 关系未明示（与 F-2 同根）
  - F-6 [minor][C7] ASM-801 commit #21 锚点缺可回读 hash + "26" 数字与 F-1 同
  - F-7 [minor][G3] FR-801/802/803 拆分粒度可接受（仅 informational，无需修改）
- Round 1 follow-up commit: `8dc0cfe` "f008(spec): r1 spec-review 通过定向回修 (4 important + 3 minor 全部 LLM-FIXABLE)"
  - F-1 闭合：spec body 数字全部对齐到 21 hf-* / 28 source SKILL.md / 22 `packs/coding/skills[]` / 29 total；FR-801 验收新增 `ls .../grep -c '^hf-'` 实测 Given；ASM-801 验收新增 `find .../wc -l` 实测 Given
  - F-2 闭合：§ 1 #6 改写为 "实际存在 + 已 drift"（含 70 字节差与 AHE→HF rename 来源解释）；§ 4.1 新增 "drift 收敛" 行；FR-804 验收新增 #4-#5（去重不变量 + drift 收敛不变量）；§ 11 非阻塞 #3 显式枚举三种收敛策略（删根级 / 软链 / 反向同步）
  - F-3 闭合：§ 2.2 #1 / FR-806 验收 #1-#3 / § 3.2 场景 1-2 全部改为 `Installed N skills, M agents` 派生表达；N == sum(pack.json.skills[]); M == sum(pack.json.agents[]); 字面值 "29" 仅作 "预期约 29" 注释保留
  - F-4 闭合：§ 4.2 末段新增 "Design Reviewer 可拒红线" 6 条（family-asset 去重 / git status 干净 / drift 收敛 / AGENTS.md 冷读链 / IDE 加载链 / F007 管道不动）；FR-805 验收新增 #4 "git status 干净不变量 + lint 守门必须实施"；§ 11 非阻塞 1/2/3 全部锚定到 § 4.2 红线
  - F-5 闭合：与 F-2 统一处理（§ 4.1 新增行 + § 11 非阻塞 #3 显式收敛策略）
  - F-6 闭合：ASM-801 数字改 28；新增可回读 commit hash `093ffed`（PR #21）+ `b249ed0` + `c40679e`；新增 `git log --oneline --since="1 month ago" -- .agents/skills/` 复核命令
  - F-7 闭合：r1 已声明可接受合并粒度，无需修改；与 NFR-804 commit 分组要求保持一致
- Round 2 review: `docs/reviews/spec-review-F008-coding-pack-and-writing-pack.md`（R2 段） — `通过`
  - 0 critical / 0 important / 0 minor
  - r1 全部 7 条 finding 闭合（7 closed / 0 open / 0 regressed）
  - 1 条 informational 残留：标题 L1 + 关联段 L10 仍写 "26 skills"（叙事性，不属 acceptance），已在 approval 前由父会话单独清理
  - `needs_human_confirmation=true` 但 reviewer 已说明 `auto` mode 下父会话可写 approval record；不存在 USER-INPUT 类阻塞
  - `reroute_via_router=false`
- 标题与 § 关联段 informational 残留清理: 在本 approval 之前、r2 后由父会话直接修文（spec 标题 "26 skills" → "~29 skills（数由 manifest 派生）"；§ 关联段 growth-strategy 引用 "1 推到 26" → "1 推到约 29"）；属于 r2 reviewer 已识别的非阻塞清理项，未引入新 finding。
- Auto-mode policy basis: `AGENTS.md` 未限制 coding cycle 内 spec 子节点 auto resolve；本 cycle 由 router 路由为 `auto`，approval step 在 record 落盘后即可解锁下游 `hf-design`。

## Decision

**Approved**. Spec 状态由 `草稿` → `已批准（auto-mode approval）`。下一步 = `hf-design`，输入为：

- 本 F008 spec（已批准）
- F001 `CON-002` 中既已声明的 `packs/coding/skills/` 目录契约（本 cycle 兑现）
- F007 已落 packs/<pack-id>/ 目录契约 + `garage init --hosts ...` 安装管道 + conflict 检测 + extend mode + manifest（本 cycle 严禁修改）
- F007 已落 host adapter 注册表（claude / opencode / cursor，本 cycle 严禁修改）
- F007 已落 `pack.json` schema_version=1 + 6 字段（本 cycle 严禁扩展）

design 阶段需在 § 11 非阻塞 1-8 共 8 项中给出 ADR：family-level 资产物理位置 / `.agents/skills/` 处置方案 / `docs/principles/skill-anatomy.md` drift 收敛策略 / `garage-sample-agent` 处置 / `pack.json.version` bump / `AGENTS.md` 同步范围 / smoke 路径 / 是否加自动化集成测试。每项 ADR 必须能通过 § 4.2 "Design Reviewer 可拒红线" 6 条检查。

## Hash & 锚点

- Spec 初稿提交: `628bd62` "f008(spec): 起草 Garage Coding Pack 与 Writing Pack 规格"
- r2 修订提交: `8dc0cfe` "f008(spec): r1 spec-review 通过定向回修 (4 important + 3 minor 全部 LLM-FIXABLE)"
- approval 提交（含 informational 标题清理 + 状态 → 已批准）: 本 commit

## 后续 (informational, 不阻塞 approval)

- § 1 #6 提到的 `docs/principles/skill-anatomy.md` 双副本 drift 处置由 design ADR 给出后实施。
- § 11 非阻塞性开放问题 8 条由 design 阶段消化（已在 spec 内显式锚定到 § 4.2 红线）。
- `RELEASE_NOTES.md` 新增 F008 段 + `packs/README.md` "当前 packs" 表更新由 finalize 阶段完成（FR-807 验收）。
