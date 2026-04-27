# Post-PR#30+PR#32 Refresh: F012 Pack Lifecycle 仍是单一最优, 范围微调

- **日期**: 2026-04-25
- **作者**: Cursor Agent (auto, in `cursor/post-pr30-pr32-planning-bf33`)
- **基线**: main @ `d5d772e` (PR #30 + #31 + #32 全 merged; **859 passed**)
- **上游 planning**: `docs/planning/2026-04-25-post-f011-next-cycle-plan.md` (本日早上, F012 lifecycle 推荐)
- **状态**: planning artifact (非 spec); 真正 F012 spec 由 `hf-specify` 起草

## 0. 这份文档为什么写

早上的 planning artifact (`2026-04-25-post-f011-next-cycle-plan.md`) 推荐 F012 = pack lifecycle 完整化 (uninstall + update + publish + 脱敏). 然后:

- **PR #30 merged**: 加 `magazine-web-ppt` skill 到 writing pack + **实施 F012-E sidecar 复制** + **修 discover_packs 跳过无 pack.json 子目录** (search hotfix 根因修)
- **PR #32 merged**: packs/coding v0.2.0 → v0.3.0 reverse-sync, 加 `hf-doc-freshness-gate` skill + DDD tactical modeling reference

**净结果**:
- packs 总 skill 数: 31 → **33** (+2)
- F012-E (sidecar 复制) 已完成, 不再是候选
- F012-D (discover_packs friction) 间接处理
- Stage 3 触发信号 "Skills > 30" **更强地达成** (33 vs 31)
- 测试基线 855 → 859 (+4 sidecar 测试 from PR #30)

本文档目的: **重排 F012 范围**, 显式承认 F012-E 已完成, 把节省下来的 spec/design 容量用在 F012-I (publish) + F012-K (脱敏) 上.

## 1. Vision 重打分 (post PR#30+#32)

| 维度 | post-F011 | post-PR#30+#32 | 变化 |
|---|---|---|---|
| B1 数据归你 | 5/5 ✅ | **5/5 ✅** | - |
| B2 宿主可换 | 3/5 ⚠️ | **3/5 ⚠️** | - |
| B3 渐进增强 | 5/5 ✅ | **5/5 ✅** | - |
| B4 人机共生 | 4/5 ⚠️ | **4/5 ⚠️** | - |
| B5 可传承 | 3.5/5 ⚠️ | **3.5/5 ⚠️** | - (publish 仍缺) |
| Stage 1 工具箱 | 100% ✅ | **100% ✅** | - |
| Stage 2 记忆体 | 95% ✅ | **95% ✅** | - |
| Stage 3 工匠 | ~25% ⚠️ | **~25% ⚠️** | - (但 trigger "Skills > 30" 更强达成 31 → 33) |
| Stage 4 生态 | ~10% ⚠️ | **~10% ⚠️** | - (publish 仍缺) |

**5 promise 全部 5/5 ✅** (与 post-F011 一致, PR #30 + #32 是 polish + content 不影响 promise 评分).

PR #30 + #32 是 **content & polish, 不直接动 vision dimensions**. F012 推荐的语义指向不变.

## 2. F012 范围微调

### 2.1 4-25 早上推荐 vs 当前推荐

| 候选 | 早上推荐 | 当前状态 | 当前推荐 |
|---|---|---|---|
| F012-B uninstall + update | 含 | 仍未实施 | **含** |
| F012-I publish | 含 | 仍未实施 | **含** |
| F012-K knowledge 脱敏导出 | 含 (与 publish 一起) | 仍未实施 | **含** |
| F012-F F009 carry-forward (VersionManager 注册) | 含 | 仍未实施 | **含** |
| F012-E sidecar 复制 | (4-24 P2, post-F011 标"已 PR #30 实施待 merge") | **PR #30 已 merge** | **移出** ✅ |
| F012-D discover_packs friction | (隐性) | **PR #30 已修** | **移出** ✅ |

### 2.2 节省下来的 spec/design 容量, 加什么?

PR #30 帮 F012 解了 2 件杂活. 节省下来的容量考虑加:

**候选 add-1**: `garage pack info <pack-id>` — 读取已装 pack 的 pack.json + 列 skills/agents 详情 + source_url. 是 `pack ls` 的 detail 版.
- ROI: 低-中. 用户多数靠 `cat packs/<pack-id>/pack.json` 也能看
- 但与 lifecycle 完整化 family 自洽 (install/ls/info/update/uninstall/publish)
- 改动小 (复用 F011 既有 list_installed_packs)

**候选 add-2**: `garage pack search <query>` — 在已装 packs 内搜 skill (按 SKILL.md front matter description / tags)
- ROI: 中. F006 既有 `garage recall` 是搜知识库; F012 search 是搜 skill catalog
- 但与 F010 sync 路径无重叠 (sync 装到 host context, search 是给用户 CLI 浏览)
- 改动中 (新模块 + index)

**评估**: 两个 add candidate 都不阻塞 F012 主轴 (uninstall/update/publish/脱敏). **先做主轴, add candidates 留 deferred**.

### 2.3 推荐 F012 范围 (锁定)

| 部分 | 描述 | 优先级 |
|---|---|---|
| **F012-A** (新编号) | `garage pack uninstall <pack-id>` (反向 install) | Must |
| **F012-B** (新编号) | `garage pack update <pack-id>` (从 source_url 重新拉) | Must |
| **F012-C** (新编号) | `garage pack publish <pack-id> --to <git-url>` (push to remote) | Must |
| **F012-D** (新编号) | knowledge 脱敏导出: `garage knowledge export --anonymize` (与 publish 一起) | Must |
| **F012-E** (新编号) | F009 carry-forward: VersionManager 注册 host-installer migration 链 | Should |

**Deferred 到 F013+**:
- `garage pack info` / `garage pack search` (add candidates)
- F010 code-review carry-forward MIN-1..6 (cli polish)
- F011 deferred D-2 (monorepo) / D-3 (signature) / 4-24 F012-A (HOST_REGISTRY plugin) / 4-24 F012-D (sync watch) / 4-24 F012-C (Memory flywheel push 端)

### 2.4 与 PR #32 关系 (hf-doc-freshness-gate skill)

PR #32 加 `hf-doc-freshness-gate` skill 到 packs/coding/. 这是 **HF workflow 的新 skill** (检查文档新鲜度). 与 F012 lifecycle 无直接耦合, 但有间接关系:
- F012-C `pack publish` 可能借鉴 `hf-doc-freshness-gate` 思路 (publish 前检查 README / pack.json 元数据是否陈旧)
- F012-E F009 carry-forward 涉及 VersionManager 注册, 可能触发 doc freshness 提示

**结论**: PR #32 不影响 F012 范围, 仅为 F012-C/E 提供可借鉴的 evaluator pattern.

## 3. 推荐下一步 (与早上一致, 范围已微调)

**F012 = pack lifecycle 完整化 (4 部分 Must + 1 部分 Should)**:
- F012-A uninstall + F012-B update (4-24 P2 旧编号 F012-B)
- F012-C publish (F011 deferred D-1)
- F012-D knowledge 脱敏导出 (F011 deferred D-4)
- F012-E F009 carry-forward (4-24 P2 旧编号 F012-F): VersionManager 注册

**预估难度**: 中 (publish 涉及 git remote + 脱敏需要规则; F012-A/B 复用 F011-C `install` 反向)

**Out of scope (deferred)**:
- pack info / search (add candidates)
- monorepo / signature (F011 D-2/3)
- HOST_REGISTRY plugin / sync watch / Memory push (4-24 F012-A/D/C)

## 4. 决策提议

**建议**: 启 `hf-specify` 起草 F012 spec, 范围按 § 2.3 锁定 (5 子部分: uninstall/update/publish/脱敏/F009 carry-forward).

**前置确认**:
1. 用户是否同意 F012 范围 = § 2.3 5 部分?
2. 是否考虑加 `pack info` 或 `pack search` (add candidates)?
3. PR #30 + #32 已 merge, F012 spec base on post-merge main (含 33 skills + sidecar copy + discover_packs friction fix)

## 5. 关联文档

- 早上 planning (4-25 第一份): `docs/planning/2026-04-25-post-f011-next-cycle-plan.md`
- 4-24 完整 vision-gap: `docs/planning/2026-04-24-vision-gap-and-next-cycle-plan.md`
- F010 / F011 finalize approval: `docs/approvals/F0{10,11}-finalize-approval.md`
- 灵魂: `docs/soul/{manifesto, user-pact, growth-strategy, design-principles}.md`
- 已完成 cycles: `RELEASE_NOTES.md` F001-F011

---

> **本文档是 planning artifact 增量更新, 不是 spec**. 真正的 F012 spec 由 `hf-specify` 起草.
