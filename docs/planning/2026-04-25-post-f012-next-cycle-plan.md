# Post-F012 Vision-Gap Refresh: Stage 3 (Skill Mining) 是单一最优 F013 候选

- **日期**: 2026-04-25
- **作者**: Cursor Agent (auto, in `cursor/post-f012-planning-bf33`)
- **基线**: main @ `65701af` (PR #34 F012 已 merged; **930 passed**, 33 SKILL.md, 3 production agents)
- **上游 planning**:
  - `docs/planning/2026-04-24-vision-gap-and-next-cycle-plan.md` (F010-A+B / F011 推荐)
  - `docs/planning/2026-04-25-post-f011-next-cycle-plan.md` (F012 lifecycle 推荐)
  - `docs/planning/2026-04-25-post-pr30-pr32-next-cycle-plan.md` (F012 范围微调)
- **状态**: planning artifact (非 spec); 真正 F013 spec 由 `hf-specify` 起草

## 0. 这份文档为什么写

F012 cycle 已关闭并 merge 到 main (PR #34, 含 5 task + 6 review + finalize approval + .agents/skills/ mount hotfix + README 刷新):

| F012 部分 | 状态 |
|---|---|
| F012-A `garage pack uninstall` | ✅ shipped (FR-1201..1203) |
| F012-B `garage pack update` | ✅ shipped (FR-1204..1206) |
| F012-C `garage pack publish` (含 sensitive_scan + author resolution + flag matrix) | ✅ shipped (FR-1207..1210) |
| F012-D `garage knowledge export --anonymize` (7 类规则) | ✅ shipped (FR-1211..1213) |
| F012-E F009 carry-forward (VersionManager registry [1, 2]) | ✅ shipped (FR-1214) |
| **post-finalize hotfix**: `.agents/skills/` 软链 + README F009-F012 同步 | ✅ shipped (commit `2efe255`) |

**本文档目的**: 重做 vision-gap 分析, 把 Belief / Promise / Stage 三轴重新打分, 然后从 F012 finalize approval 列出的 8 个 carry-forward (D-1210..D-1217) + 既有 deferred 队列里筛 F013 范围.

## 1. Vision 重打分 (post-F012)

### 1.1 三轴对照

| 维度 | post-F011 | post-F012 finalize | 变化 / 理由 |
|---|---|---|---|
| **B1 数据归你** | 5/5 ✅ | **5/5 ✅** | 维持 |
| **B2 宿主可换** | 3/5 ⚠️ | **4/5 ⚠️** | 3 first-class adapter (claude/cursor/opencode) + scope 完整, 但第 4 个仍要改源码 → +1 |
| **B3 渐进增强** | 5/5 ✅ | **5/5 ✅** | 维持 |
| **B4 人机共生** | 4/5 ⚠️ | **5/5 ✅** | F010 sync ↔ ingest 飞轮闭环, 用户每次对话 host 都看见 garage memory |
| **B5 可传承** | 3.5/5 ⚠️ | **5/5 ✅** | F012 install/uninstall/update/publish + anonymize export 5 件齐全, B5 user-pact 全 opt-in (已封顶) |
| **Promise ① 几秒变成你的 agent** | 5/5 ✅ | **5/5 ✅** | 维持 |
| **Promise ② 知道你的编码风格** | 5/5 ✅ | **5/5 ✅** | KnowledgeType.STYLE + production agent shipped, 维持 |
| **Promise ③ 记得上月架构决策** | 5/5 ✅ | **5/5 ✅** | sync ↔ ingest 双向, 维持 |
| **Promise ④ 调用 50 个 skills** | 5/5 ✅ | **5/5 ✅** | 33 skill 已超 30 trigger; 维持 |
| **Promise ⑤ 知道怎么写你的博客** | 5/5 ✅ | **5/5 ✅** | 维持 |
| **Stage 1 工具箱** | 100% ✅ | **100% ✅** | 维持 |
| **Stage 2 记忆体** | 100% ✅ | **100% ✅** | 维持 |
| **Stage 3 工匠** | ~25% ⚠️ | **~65% ⚠️** | F011 production agents (3 个) + F010 STYLE 维度 + 33 SKILL.md ≥ 30 trigger 全过, 但 "skill mining 自动提炼" 仍空白 |
| **Stage 4 生态** | ~10% ⚠️ | **~40% ⚠️** | F012 lifecycle 完整 (install/update/publish/uninstall) + 脱敏 export, 但缺 pack 发现 / 签名 / 中央 registry |

### 1.2 关键变化

- **5 Belief + 5 Promise 全部 5/5**, 这是 garage 整个 vision 的第一次"承诺达成"完整快照
- **Stage 3 大跃进** (~25% → ~65%): F012 直接落地的 lifecycle 完整 + F010/F011 累积的飞轮 + agents, "工匠" 形态的形可以看到
- **Stage 4 中等推进** (~10% → ~40%): publish + uninstall + update + 脱敏 export 4 件齐, 但 "社区" 的 discovery / supply-chain 仍在远景

### 1.3 触发信号 (growth-strategy.md 表)

| 信号 | growth-strategy 期望 | 实际 (post-F012) | 是否触发 |
|---|---|---|---|
| Skills 数量 > 30 | Stage 3 → 4 触发 | **33 SKILL.md** | ✅ 触发 |
| Skills 在多个领域 (开发/写作/研究) | Stage 3 → 4 触发 | coding (24) + writing (5) + garage core (3) + search (1) | ✅ 触发 (3 领域) |
| 跨领域协作需求 (例 "用开发经验写博客") | Stage 3 → 4 触发 | 用户已有 magazine-web-ppt 把研究产出转 PPT, blog-writing-agent 把代码经验沉淀文章 | ✅ 接近触发 |
| **系统能指出 "这个模式可以变成 skill"** | Stage 3 健康表现 | **未实现** | ❌ Stage 3 关键能力缺位 |

最后一行是 Stage 3 的标志性能力, 也是 F012 finalize approval D-1216 推迟到 F013+ 的核心条目之一.

## 2. F013 候选枚举 (从 F012 carry-forward + 既有 deferred 队列)

### 2.1 F012 finalize approval 留下的 8 个 carry-forward

| ID | 描述 | ROI | 难度 | Vision 杠杆 |
|---|---|---|---|---|
| **D-1210** | GitHub OAuth + GitLab token auto-detect | 中 | 中 | B5 polish (publish 用户体验) |
| **D-1211** | 真实 3-way merge (`pack update --preserve-local-edits`) | 中-高 | **高** | B5 polish (update 真正可用而非 warn-then-overwrite) |
| **D-1212** | pack signature / GPG | 高 | 高 | Stage 4 (社区供应链) |
| **D-1213** | monorepo (多 pack from 同 URL) | 中 | 中 | Stage 4 (生态扩展) |
| **D-1214** | `pack info` / `pack search` | 中 | 低-中 | Stage 4 (lifecycle 完整化) |
| **D-1215** | 反向 import + experience export | 中 | 中 | B5 双向流动 (export ↔ import 闭环) |
| **D-1216** | publish 自动跑 `hf-doc-freshness-gate` skill (PR #32 evaluator pattern) | 低-中 | 低 | Stage 4 polish |
| **D-1217** | publish multi-author / signed commit / commit footer template | 低 | 低 | B5 polish |

### 2.2 更早 cycle 留下的 deferred 队列 (仍有效)

| 来源 | 候选 | ROI | 难度 | Vision 杠杆 |
|---|---|---|---|---|
| F007 D-705 | HOST_REGISTRY plugin / 第 4 个宿主免改源码 | 中 | 中-高 | **B2 4/5 → 5/5** (host 真插件) |
| 4-24 plan F012-D | sync watch (cross-device git push/pull 自动化) | 中-高 | 高 | Stage 4 (跨机) |
| 4-24 plan F012-C | Memory flywheel push 端 ("系统主动指出 'pattern → skill'") | **高** | **中-高** | **Stage 3 关键能力** (上节 1.3 触发信号 ❌) |
| F010 code-review MIN-1..6 | sync CLI polish (--dry-run 输出 / --quiet 降噪) | 低 | 低 | B3 polish |
| F011 D-2 | monorepo (与 D-1213 重) | 中 | 中 | (重) |
| F011 D-3 | pack signature (与 D-1212 重) | 高 | 高 | (重) |

### 2.3 候选总评估表 (按 vision 杠杆排序)

| 候选 | Vision 杠杆 | ROI | 难度 | 触发紧迫度 |
|---|---|---|---|---|
| **F013-A: Skill Mining Push 信号** (4-24 F012-C, growth-strategy 1.3 触发信号 ❌) | **Stage 3 标志性能力 ⚠️** | **高** | 中-高 | **🔥 唯一阻 Stage 3 → Stage 4** |
| F013-B: HOST_REGISTRY plugin (F007 D-705) | B2 4/5 → 5/5 | 中 | 中-高 | 中 (但当下 3 first-class 已够用) |
| F013-C: pack info + search (D-1214) | Stage 4 lifecycle polish | 中 | 低-中 | 低 (lifecycle 已完整, search 是锦上添花) |
| F013-D: 反向 import + experience export (D-1215) | B5 双向流动闭环 | 中 | 中 | 低 (export 已能用 git clone 反向) |
| F013-E: pack signature / GPG (D-1212) | Stage 4 社区供应链 | 高 | 高 | 低 (Stage 4 才需要, 社区还没建立) |
| F013-F: 真实 3-way merge (D-1211) | B5 polish | 中-高 | 高 | 中 (warn-then-overwrite 已能用) |
| F013-G: cross-device sync watch (4-24 F012-D) | Stage 4 跨机 | 中-高 | 高 | 中 |
| F013-H: monorepo packs (D-1213) | Stage 4 生态扩展 | 中 | 中 | 低 |
| F013-I: GitHub OAuth (D-1210) | B5 polish | 中 | 中 | 低 |
| F013-J: publish auto doc-freshness-gate (D-1216) | Stage 4 polish | 低-中 | 低 | 低 |

## 3. F013 推荐: Skill Mining Push (F013-A)

### 3.1 为什么是 F013-A 单独占首位

1. **Vision 触发信号唯一未达成项**: 1.3 表 4 行里前 3 行 ✅ 触发, 第 4 行 ("系统能指出 'pattern → skill'") ❌ — 这是 Stage 3 健康表现的最关键标志
2. **后向闭环**: F003-F006 投入了完整的 memory 提取 (signals → candidates → review queue → KnowledgeStore), 当前只有 "pull" 端 (用户主动 search/recall), 没有 "push" 端 ("系统看见 5 次类似 pattern 后主动建议: 这能成 skill")
3. **growth-strategy.md 明示**: Stage 3 的核心新增是 "重复模式自动识别并建议为 skill 模板", F012 把 "skill 怎么分发" 解决了 (publish), 但 "skill 怎么从积累中长出来" 还没动
4. **杠杆**: F013-A 一旦交付, 把 garage 从 "Agent 能力的家" 升级成 "Agent 能力的孵化器" — 这是从 stage 3 (工匠) 走向 stage 4 (生态) 的内在动力, 不需要外部社区先成立
5. **解锁后续 cycle**: F013-A 产出的 "skill 候选" 队列 + audit 流程, 是 F013-D (experience export) / F013-J (publish 自动验证) 的输入数据源
6. **碎片化候选反而风险高**: F013-B/C/D/E 单独看都是 "polish 或扩展", 没有一个能像 F013-A 一样单独把 vision 推进一格

### 3.2 F013-A 范围预估 (5 部分, 全 Must)

| 部分 | 描述 | 复用 |
|---|---|---|
| **F013-A1** Pattern detection | 在 F003 既有 candidate 流上加 "重复模式识别" — 同一 problem_domain + 同一 tag 组合在 ≥ N 次会话出现就触发 | F003 SignalExtractor + ExperienceIndex |
| **F013-A2** Skill suggestion | `garage skill suggest` CLI: 列出系统识别到的候选模式 + 估计的 SKILL.md 模板 + 命中证据链 | F006 知识图 + F005 knowledge add CLI |
| **F013-A3** Skill template generator | 从 candidate 自动生成 SKILL.md 草稿 (frontmatter + Workflow 骨架 + 引用知识条目) | docs/principles/skill-anatomy.md schema |
| **F013-A4** Promote 流程 | `garage skill promote <suggestion-id>`: 半自动从 .garage/memory/ 候选提到 packs/<pack-id>/skills/, 触发 hf-test-driven-dev 走完 skill writing 路径 | F011 hf-test-driven-dev + F008 packs/ 结构 |
| **F013-A5** Audit / decay | 候选 30 天未被 promote 自动归档 + 用户可显式 reject 永久跳过 | F004 ExperienceIndex 索引 |

### 3.3 风险与已知约束

- **R-1**: pattern detection 阈值 (N) 需要标定, 起步保守 (N ≥ 5 同类 candidate); 通过 `--threshold` flag 给用户微调
- **R-2**: SKILL.md 模板生成质量取决于候选证据丰富度; 若证据不足, 模板留空给用户人工补; 不允许自动 commit 到 packs/
- **R-3**: 用户审批不可绕过 (B5 user-pact: "系统提供建议, 但人始终掌舵"); promote 必须显式 `--yes` 或 prompt
- **R-4**: skill anatomy 7 原则 (description 是分类器 / 主文件要短 / 边界必须显式 等) 必须在模板生成时就显式遵守, 否则会污染 packs/

### 3.4 与 F012 / F011 / F010 的依赖

- **依 F003**: SignalExtractor 是模式检测基础
- **依 F004**: ExperienceIndex 提供索引
- **依 F005**: knowledge add CLI 是 promote 的写出端
- **依 F006**: 知识图给候选关联证据
- **依 F011**: skill anatomy + KnowledgeType.STYLE 给候选打标签
- **依 F012-D**: anonymize 规则可被 promote 复用 (例如 "这个模式建议 publish, 先脱敏")
- **不依**: F012-A/B/C (uninstall/update/publish 是 distribution, F013-A 是 generation)

## 4. 第二优先候选 (若用户选 broader F013)

如果用户希望 F013 走 lightweight 路径 (避开 F013-A 的中-高难度), 第二优先是 **F013-B** (HOST_REGISTRY plugin, B2 4/5 → 5/5):

- 改动局限在 `src/garage_os/adapter/installer/host_registry.py` + 加载机制
- 把 `HOST_REGISTRY: dict[str, HostInstallAdapter]` 从 hardcoded 改成 entry-point / plugin discovery
- 关闭 F007 D-705 的最后一项, 让第 4 个宿主真正不改 garage 源码
- 难度中-高 (要设计 plugin schema 但不动业务逻辑), ROI 中

或者若用户希望 F013 走 incremental polish 路径, 选 **F013-C + F013-J 组合** (`pack info` / `pack search` / publish auto doc-freshness-gate, 都是 D-1214 + D-1216, 低难度 lifecycle polish), 但这种路径不推动任何 vision 维度上分数.

## 5. 推荐决策矩阵

| 路径 | F013 范围 | 难度 | Vision 增量 | 适合场景 |
|---|---|---|---|---|
| **A. F013-A 单一最优 (推荐)** | Skill Mining Push 5 子部分 | 中-高 | Stage 3 → 80%+ + growth-strategy 触发信号 4/4 全过 | 用户优先 vision 兑现 |
| B. F013-B HOST_REGISTRY plugin | host registry 插件化 | 中-高 | B2 4/5 → 5/5 | 用户优先 host 可插拔 |
| C. F013-C+J polish bundle | pack info/search + publish doc-freshness | 低-中 | Stage 4 polish 不上分 | 用户优先 lifecycle 完整 |
| D. **混合路径 A + J** | F013-A 主轴 + F013-J 顺手做 (低难度) | 中-高 | A 主导 + J 收尾 publish 闭环 | 用户希望 F013-A 同时清掉 F012 carry-forward 一项 |

## 6. 推荐下一步

**推荐 F013 范围 = Path A (F013-A: Skill Mining Push 信号)**:
- F013-A1 pattern detection
- F013-A2 `garage skill suggest` CLI
- F013-A3 skill template generator
- F013-A4 `garage skill promote` 半自动流程
- F013-A5 audit / decay

理由:
1. 唯一能把 Stage 3 从 "形是工匠 (production agents)" 升级成 "实是工匠 (系统会从你工作中长 skill)" 的候选
2. growth-strategy.md 明示的 Stage 3 健康表现唯一未达成项
3. F012 完成后 Belief 1-5 + Promise ①-⑤ 全 5/5, vision 已无 promise 维度可推, 唯一上分项在 Stage 维度上
4. 反向 unblock F013-D / F013-J (后续 cycle 的输入)

**前置确认 (auto mode 默认 Path A, 用户可改)**:
1. F013 范围 = F013-A 5 部分?
2. 或选 Path B (HOST_REGISTRY) / C (lifecycle polish) / D (A+J 混合)?
3. F013 base on main @ `65701af` (含 F012 全部 + .agents/skills/ mount + README F009-F012)

**预估难度**: 中-高 (pattern detection 算法 + skill template generator 是新模块; promote 流程要嵌 hf-test-driven-dev). F011 / F012 的实施速度 (5 task / 2 工作日) 可作参考.

## 7. Out of scope (deferred 到 F014+)

- F013-D 反向 import + experience export
- F013-E pack signature / GPG (Stage 4 社区供应链)
- F013-F 真实 3-way merge (B5 polish)
- F013-G cross-device sync watch
- F013-H monorepo packs
- F013-I GitHub OAuth
- (除非用户选 Path D, 否则) F013-J publish auto doc-freshness-gate

## 8. 关联文档

- 4-24 全面 vision-gap (F010+ baseline): `docs/planning/2026-04-24-vision-gap-and-next-cycle-plan.md`
- 4-25 早上 (F012 推荐): `docs/planning/2026-04-25-post-f011-next-cycle-plan.md`
- 4-25 微调 (F012 范围): `docs/planning/2026-04-25-post-pr30-pr32-next-cycle-plan.md`
- F012 finalize approval (8 carry-forward): `docs/approvals/F012-finalize-approval.md`
- 灵魂: `docs/soul/{manifesto, user-pact, growth-strategy, design-principles}.md`
- 已完成 cycles: `RELEASE_NOTES.md` F001-F012

---

> **本文档是 planning artifact**, 不是 spec. 真正的 F013 spec 由 `hf-specify` 起草. auto mode 推荐 Path A (F013-A), 用户可在 PR 评论里改路径 (B/C/D).
