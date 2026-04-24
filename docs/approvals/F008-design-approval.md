# Approval Record - F008 Design

- Artifact: `docs/designs/2026-04-22-garage-coding-pack-and-writing-pack-design.md`
- Approval Type: `designApproval`
- Approver: cursor cloud agent (auto-mode policy approver)
- Date: 2026-04-22
- Workflow Profile / Execution Mode: `full` / `auto`
- Workspace Isolation: `in-place`（工作分支 `cursor/f008-coding-pack-and-writing-pack-bf33`；PR #22）

## Evidence

- Round 1 review: `docs/reviews/design-review-F008-coding-pack-and-writing-pack.md`（R1 段）— `需修改`
  - 0 critical / 1 important USER-INPUT + 3 important LLM-FIXABLE / 4 minor LLM-FIXABLE
  - F-1 [important][USER-INPUT][D1] ADR-D8-4 实质性下调 spec FR-804 验收 #1 / § 2.2 验收 #2 "装完后引用不 404" 字面口径
  - F-2 [important][LLM-FIXABLE][D6] § 12 NFR-802 落地行 vs § 13.1 自动化测试表对"新增测试文件数量"自相矛盾（4 vs 2）
  - F-3 [important][LLM-FIXABLE][D5] § 10.1 T1/T4 单 commit 含 7+/4 类异质动作，与 NFR-804 "任一组可独立 review" 张力
  - F-4 [important][LLM-FIXABLE][D1] § 17 排除项漏列 spec § 5 deferred 中 3 项
  - F-5 [minor][LLM-FIXABLE][D2] ADR-D8-2 候选 C 首次 clone 贡献者 IDE 加载链空窗未在 ADR Consequences 显式承接
  - F-6 [minor][LLM-FIXABLE][D3] ADR-D8-3 权威源选定缺 git log 证据
  - F-7 [minor][LLM-FIXABLE][D5] ADR-D8-1 docs/templates vs principles layout 非对称未在 ADR 内显式解释
  - F-8 [minor][LLM-FIXABLE][D5] § 13.3 Walking Skeleton 仅覆盖一家宿主，与 FR-806 三家宿主全装承诺不对等
- Round 1 follow-up commit: `994883e` "f008(design): r1 design-review 通过定向回修 (1 important USER-INPUT 收敛 + 3 important + 4 minor LLM-FIXABLE)"
  - F-1 闭合：父会话评估后选择**收敛为 LLM-FIXABLE 等价路径**（reviewer 提供二选一中等价路径 (a) 的双向修复版本，避免单独开 hf-increment cycle 的开销）：
    - spec FR-804 验收 #1 改为分两层口径（packs 源端 + 下游宿主端，承认 D7 管道当前只复制 SKILL.md 单文件）
    - spec § 2.2 验收 #2 + § 3.2 场景 3 同步分层
    - spec § 5 deferred 表新增 "D7 管道扩展为递归 references/" 作为 D9 候选
    - design ADR-D8-4 文末新增 "Spec acceptance 同步收紧" 段，显式记录走 wording-only LLM-FIXABLE 路径理由（wording-only 修订，无新业务事实，符合 spec-review LLM-FIXABLE 分类）
    - r2 reviewer 独立评估该路径合规闭合，**收回 r1 USER-INPUT 标记**（5 维评估全过：无新业务事实、spec/design 字面已一致、无 drift、不破坏已批准 spec 核心范围、design 整份签字时自然吸收）
  - F-2 闭合：design § 13.1 表扩到 4 个测试文件（test_skill_anatomy_drift / test_full_packs_install / test_packs_garage_extended / test_dogfood_layout）+ 每文件含覆盖 spec FR/NFR + 触发 INV + 落地 commit 三列；§ 12 NFR-802 同步指向 § 13.1
  - F-3 闭合：design § 10.1 显式拆 T1→T1a/T1b/T1c + T4→T4a/T4b/T4c，合计 9 个 sub-commit，每个独立可 review；段首约束 hf-tasks 拆分粒度下限
  - F-4 闭合：design § 17 补齐 3 项 spec § 5 deferred（新增 hf-* skill / 多语言 i18n / 用户→packs 反向同步），与 spec § 5 形成完整集合等价
  - F-5 闭合：ADR-D8-2 Consequences 段新增首次 clone 贡献者 onboarding 指引落地位置（AGENTS.md 顶部单源 + README/CONTRIBUTING 仅 link 指向 + hf-tasks T4 commit 承接）
  - F-6 闭合：ADR-D8-3 新增 "权威源选定证据" 段（git log 时间戳对比 family 副本 2026-04-18T05:05 vs 根级 2026-04-15T20:36 + 术语 + 路径锚点对比 + 选 family 副本理由 + 副作用说明）
  - F-7 闭合：ADR-D8-1 Decision 段后新增 "为什么 docs/templates 落 skills/ 而 principles 不落" 解释（实测 6 处 hf-* 引用 vs principles 只被 AGENTS.md 引用）
  - F-8 闭合：design § 13.3 Walking Skeleton 改为三家宿主对称展示（claude / cursor / opencode 同管道、仅 target_skill_path 不同）
- Round 1 informational 残留清理（reviewer r2 在 new_risks 段提及 2 条非阻塞）：
  - § 11.1 INV 责任 commit 列已同步刷新为 sub-commit 编号（T1a/T1b/T1c/T4a/T4c）
  - § 15 任务规划准备度段已重写：从"按 5 类拆 5 个 task / T4 是关键合流点"改为"按 9 个 sub-commit 拆 task / T4 已拆为 T4a/T4b/T4c 三个独立切片"
  - 这两条 informational 在本 commit 内顺手清理（reviewer 已说明非阻塞）
- Round 2 review: `docs/reviews/design-review-F008-coding-pack-and-writing-pack.md`（R2 段）— **`通过`**
  - 0 critical / 0 important / 0 minor
  - r1 全部 8 条 finding 闭合（8 closed / 0 open / 0 regressed）
  - finding #1 USER-INPUT 收敛路径独立评估合规，reviewer 收回 USER-INPUT 标记
  - 2 条 informational 残留已在本 approval 前清理
  - `needs_human_confirmation=true`（reviewer 指 design 真人确认环节由 auto-mode 父会话写 record）；不存在 USER-INPUT 类阻塞
  - `reroute_via_router=false`
- Auto-mode policy basis: `AGENTS.md` 未限制 coding cycle 内 design 子节点 auto resolve；本 cycle 由 router 路由为 `auto`，approval step 在 record 落盘后即可解锁下游 `hf-tasks`。

## Decision

**Approved**. Design 状态由 `草稿` → `已批准（auto-mode approval）`。下一步 = `hf-tasks`，输入为：

- 本 D008 design（已批准），含：
  - 8 项 ADR (D8-1..D8-8)
  - § 10.1 9 个 sub-commit 拆分（T1a/T1b/T1c + T2 + T3 + T4a/T4b/T4c + T5）
  - § 11.1 9 条 INV 不变量（每条对应具体 commit）
  - § 13.1 4 个新增测试文件（每个对应具体 sub-commit）
  - § 14 7 条失败模式与缓解
  - § 17 与 spec § 5 完整集合等价的延后项表
- F008 spec（已批准 r2，design 阶段同步收紧 wording 与 D7 工程边界对齐）
- F007 已落 packs/ 目录契约 + `garage init` 安装管道 + manifest（CON-801 严禁修改）

`hf-tasks` 阶段需产出可评审任务计划，每个 task 对应 § 10.1 sub-commit 之一（或合并若干，但不能比 sub-commit 更粗）；每个 task 至少含：覆盖的 INV / 触发的 spec FR/NFR / acceptance / 失败模式应对。

## Hash & 锚点

- Design 初稿提交: `fe14713` "f008(design): r1 设计草稿，含 8 项 ADR + 显式承认 §2.4 工程边界"
- r1 回修提交: `994883e` "f008(design): r1 design-review 通过定向回修 (1 important USER-INPUT 收敛 + 3 important + 4 minor LLM-FIXABLE)"
- approval 提交（含 informational 残留清理 + 状态 → 已批准）: 本 commit
- 关联 spec wording 同步修订（与 design ADR-D8-4 反向同步）: 在 commit `994883e` 内一同落地

## 后续 (informational, 不阻塞 approval)

- ADR-D8-2 候选 C 选定后，hf-tasks T4b commit 必须在 AGENTS.md 顶部新增 onboarding 段，让首次 clone 贡献者知道需要先跑 `garage init --hosts cursor,claude` 激活 IDE skill 加载
- ADR-D8-3 选定 "反向同步 + sentinel 测试" 后，hf-tasks T1c commit 必须在 `tests/adapter/installer/test_skill_anatomy_drift.py` 新增 SHA-256 sentinel
- F008 实施期间应保护 `.agents/skills/` 不被并行修改（spec ASM-801），PR 描述需显式声明
