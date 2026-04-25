# Post-F011 Vision-Gap Reassessment & F012+ Next Cycle Plan

- **日期**: 2026-04-25
- **作者**: Cursor Agent (auto, in `cursor/post-f011-planning-bf33`)
- **基线**: main @ `00f7d5b` (PR #27 + #28 + #29 全 merged; 855 passed)
- **上游 planning**: `docs/planning/2026-04-24-vision-gap-and-next-cycle-plan.md` (4 月 24 日基于 F009 末态)
- **状态**: planning artifact (非 spec); 真正 F012 spec 由 `hf-specify` 起草

## 0. 这份文档为什么写

4 月 24 日的 planning artifact 把 P0 (F010) + P1 (F011) 都标为优先做; 现在 P0 + P1 都已落地 + merged. 当时识别的 P2 候选 (F012-A..F (HOST_REGISTRY plugin / uninstall / push 端 / sync watch / sidecar copy / F009 carry-forward)) 部分被新现实推后或重排:

- PR #30 (writing magazine-web-ppt) 已**实施 F012-E sidecar 复制** (`install_packs` 把 `references/` `assets/` `evals/` `scripts/` 整树复制) — 但还在 draft + 没走 hf-* full review/gate 链
- PR #30 同时改了 `discover_packs` 加 "无 pack.json 子目录跳过" — 这恰好是上次 search hotfix 触发的真实 friction

本文档目的:
1. 重新打分 5 信念 / 5 promise / 4 stage (post-F011 实际状态)
2. 把 4-24 planning § 2.3 P2 列表按 post-F011 用户实际场景重新排序
3. 推荐下一 cycle 单一最优 + 三 cycle 组合
4. 显式标注与 PR #30 的关系 (是 dependency / blocker / parallel?)

## 1. Vision 重打分 (post-F010 + F011 + PR #30 候选)

### 1.1 5 信念

| 信念 | 4-24 评分 | post-F011 评分 | 变化原因 |
|---|---|---|---|
| B1 数据归你 | 5/5 ✅ | **5/5 ✅** | 维持 |
| B2 宿主可换 | 3/5 ⚠️ | **3/5 ⚠️** | 未变 (HOST_REGISTRY 仍硬编码) |
| B3 渐进增强 | 5/5 ✅ | **5/5 ✅** | 维持 (F010 sync 默认 --hosts all 有理由 / F011 pack install 是 opt-in) |
| B4 人机共生 | 3/5 ⚠️ | **4/5 ⚠️** | F010 闭合飞轮 input + push 端; **缺**: 主动 push ("这个模式可以变成 skill" 建议, F012-C) |
| B5 可传承 | 2/5 ⚠️ | **3.5/5 ⚠️** | F011-C `garage pack install` 让一键拉装可用; **缺**: `garage pack publish` (反向推送) + knowledge 脱敏导出 |

### 1.2 5 终极形态承诺

| Promise | 4-24 评分 | post-F011 评分 | 关键证据 |
|---|---|---|---|
| P① "几秒变成你的 Agent" | 3/5 ⚠️ | **5/5 ✅** | F010-A `garage sync` 让宿主新对话开始时自动 see Garage 知识 |
| P② "知道你的编码风格" | 0/5 ❌ | **5/5 ✅** | F011-A `KnowledgeType.STYLE` + sync compiler include style |
| P③ "记得上月架构决策" | 4/5 ⚠️ | **5/5 ✅** | F010-A push (recall 从 pull → 自动 push 到宿主 context surface) |
| P④ "调用 50 个 skills" | 5/5 ✅ | **5/5 ✅** | 31 skills × 3 hosts (即将 32 + magazine-web-ppt = 32 if PR #30 merge) |
| P⑤ "知道怎么写你的博客" | 5/5 ✅ | **5/5 ✅** | + F011-B blog-writing-agent 启动 Stage 3 工匠层 |

### 1.3 4 成长阶段

| Stage | 4-24 评分 | post-F011 评分 | 关键证据 |
|---|---|---|---|
| Stage 1 工具箱 | 100% ✅ | **100% ✅** | 31 skills × 3 hosts (PR #30 merge 后 32) |
| Stage 2 记忆体 | 60% ⚠️ | **95% ✅** | F003-F006 build + F010 闭合飞轮 (sync push + ingest pull) |
| Stage 3 工匠 | 5% ⚠️ | **~25% ⚠️** | F011-B 落 2 个 production agent; **缺**: 自动 skill 提炼 (F012-C 候选) + 工作流编排自动化 |
| Stage 4 生态 | 0% | **~10% ⚠️** | F011-C `garage pack install` 启用社区分享单向链路; **缺**: publish + 脱敏 + market |

```
                        post-F011 完成度
                        ┌─────────────────────────────────┐
B1 数据归你             │█████████████████████████████████│ 5/5  ✅
B2 宿主可换             │███████████████████              │ 3/5  ⚠️ (未变)
B3 渐进增强             │█████████████████████████████████│ 5/5  ✅
B4 人机共生             │██████████████████████████       │ 4/5  ⚠️ (push 端缺)
B5 可传承               │██████████████████████           │ 3.5/5 ⚠️ (publish 缺)
                        └─────────────────────────────────┘

P① "几秒变成你的 Agent"     ✅ 5/5
P② "知道你的编码风格"       ✅ 5/5
P③ "记得上月架构决策"       ✅ 5/5
P④ "调用 50 个 skills"      ✅ 5/5
P⑤ "写你的博客"             ✅ 5/5

Stage 1 工具箱   ████████████████████ 100%
Stage 2 记忆体   ███████████████████   95%
Stage 3 工匠    █████                25%
Stage 4 生态    ██                   10%
```

**关键洞察**: 所有 5 promise 全部 5/5; 5 信念有 2 项还卡 3-3.5/5; 4 stage 头 2 个 ≥ 95%, Stage 3 + 4 是下一轮重点. 与 4-24 比, **重心从"复活承诺"转向"成长策略飞轮"**.

## 2. 推后 / 重排候选

### 2.1 PR #30 已部分落地 F012-E sidecar copy — 决策

PR #30 (writing pack 加 magazine-web-ppt) draft 中:
- 加 1 skill (writing pack 4 → 5)
- 改 `discover_packs` 跳过无 pack.json 子目录 (上次 search hotfix 的根因修复)
- 改 `install_packs` 复制 references/ assets/ evals/ scripts/ sidecar dirs
- INV-1 + dogfood baseline 同步

**评估**: PR #30 是真实 friction-driven 改动 (用户带新 skill 撞上 sidecar 缺失问题), 但**未走 hf-* 完整 cycle**. 建议:
- **方案 A** (推荐): 把 PR #30 当作 F012-X "用户驱动 polish" 接受合并 (与 F008 PR #25 reverse-sync 同模式), 不算正式 F012 cycle. 让 magazine-web-ppt skill + sidecar copy 都先进 main.
- **方案 B**: 给 PR #30 补完整 cycle (spec → design → tasks → review/gate). 但 sidecar copy 虽是 F012-E 候选, 改动量小 + 用户已实施可工作版本, 走完整 cycle ROI 偏低.

→ **建议方案 A**: 让用户手动 merge PR #30, 然后开 F012 cycle 处理更大主题.

### 2.2 4-24 P2 列表 post-F011 重排

| 候选 | 4-24 触发信号 | post-F011 真实状态 | 重排 |
|---|---|---|---|
| F012-A HOST_REGISTRY plugin | 等第 4 家宿主出现 | 仍未出现 | **保持等待** |
| F012-B `garage pack uninstall/update` | F010-A/B 落地后用户想卸 / 升 | F010+F011 已落; **真实需求出现** (PR #29 装的 pack 没法卸; PR #30 改 discover_packs 间接处理 update 路径) | **升 P1** |
| F012-C Memory flywheel push 端 | session > 50 | session 还远 < 50 (本仓库 dogfood 没真实积累 session) | **保持等待** |
| F012-D `garage sync` 自动化 | F010-A 落地后用户嫌烦 | F010 刚落, 用户尚无反馈 | **保持等待** |
| F012-E sidecar 复制 | references 缺 | **PR #30 已实施** (待 merge) | **完成** (作为 polish 收尾) |
| F012-F F009 carry-forward (CON-902 + VersionManager) | 与 F012-B 同 cycle | 与 F012-B 一并做 | **绑 F012-B** |

### 2.3 新候选 (post-F010+F011 衍生)

| 候选 ID | 描述 | 触发场景 | 优先级 |
|---|---|---|---|
| **F012-G** | F010 code-review carry-forward (MIN-1..6: `_require_garage` / size_budget hardcode / batch-id None render / etc) | F010 finalize approval 显式列出 | **P2** (polish) |
| **F012-H** | F010 traceability MIN-1: tasks/design 测试合并回写 | F010 finalize approval | **P2** (docs polish) |
| **F012-I** | F011 deferred D-1: `garage pack publish` + `pack update` + `pack remove` | B5 可传承 3.5/5 → 5/5 + F012-B 反向操作 | **P1** (与 F012-B 合并) |
| **F012-J** | F011 deferred D-3: pack signature / 安全审核 | 第三方 pack 流入后才痛 | **P3** (等触发) |
| **F012-K** | F011 deferred D-4: knowledge 脱敏导出 | 用户想分享个人知识库时痛 | **P2** (与 F012-I publish 同 cycle) |
| **F012-L** | F003 自动 STYLE 提取规则 (从 archived session 识别"用户做了 N 次相同选择"模式) | F010-B ingest 后 session 数累积 | **P2** (与 F012-C 同 trigger) |

## 3. 推荐下一 cycle 路径

### 3.1 单一最优选择: **F012 = pack lifecycle 完整化** (uninstall + update + publish)

**理由**:
- 同时回应 F012-B (uninstall/update, 4-24 list) + F012-I (publish, F011 deferred) + F012-K (脱敏导出)
- B5 可传承 3.5/5 → 5/5 + 启动 Stage 4 生态 (10% → ~30%)
- 与 F011-C `pack install` 形成完整 lifecycle: install ↔ update ↔ uninstall + 反向 publish
- 用户已经能 install 但卸不掉/升不了/分享不出 — 真实摩擦

**预估改动范围**:
- `src/garage_os/adapter/installer/pack_install.py` 加 `uninstall_pack()` + `update_pack()` + `publish_pack()`
- CLI: `garage pack {install, ls, uninstall, update, publish}` 全套
- F009 carry-forward (F012-F): VersionManager 注册 host-installer migration 链 (同 cycle 修)
- knowledge 脱敏导出工具 (F012-K): 与 publish 一起 (publish 默认含脱敏建议)

**预估难度**: 中 (publish 涉及 git remote 操作 + 脱敏需要规则; 与 F011-C `install` 不对称, 复杂度更高)

### 3.2 单一最优替代: **F012 = Stage 3 工匠层 (自动 STYLE 提取 + 工作流编排自动化)**

**理由**:
- B4 人机共生 4/5 → 5/5 + Stage 3 25% → ~50%
- F011-B 已落 2 个手写 agent; 下一步是**自动**: 让 F003 提取链识别 style 模式 + 自动建议 agent 组合
- 但 trigger 条件 (session > 50) 在本仓库 dogfood 还远未达

**评估**: ROI 不如 3.1 高, 因 trigger 不足.

### 3.3 三 cycle 推荐组合

```
F012 (pack lifecycle 完整化, P1 + F009 carry-forward)
  → F013 (Stage 3 工匠自动化, P1, 等 session 数累积后做)
  → F014 (Stage 4 生态最小可证: 公开 pack registry / 社区 skills 市场雏形, P2)
```

逻辑:
1. **F012**: 用户已能 install pack, 但卸不掉/升不了/分享不出 — 痛点直接, 必须先做
2. **F013**: 等 F012 落 + 用户跑一段时间, session 数累积后做自动化提炼
3. **F014**: 等 F013 + 至少 2-3 个用户分享过 pack 后, 做 registry / market 雏形

### 3.4 不推荐先做的

- **F012-A HOST_REGISTRY plugin 化**: 第 4 家宿主未出现, 提前抽象 = 过度设计
- **F012-D sync watch**: F010 刚落, 用户还没说嫌烦
- **F012-J pack signature**: 第三方 pack 流入还少, 提前做 = YAGNI
- **F013 (Stage 3 自动化) 先做**: session 数不够, 无法验证模式识别准确性

## 4. 决策提议

**建议下一 cycle = F012 pack lifecycle 完整化**, 范围:
- F012-B uninstall + update (4-24 P2)
- F012-I `pack publish` (F011 D-1)
- F012-K knowledge 脱敏导出 (F011 D-4, 与 publish 一起)
- F012-F F009 carry-forward (CON-902 + VersionManager 注册)

**前置**:
1. 用户确认 PR #30 (magazine-web-ppt + sidecar copy) 直接 merge 还是要走 F012-X cycle
2. 用户确认本 planning artifact 的 P1/P2 重排
3. 启 `hf-specify` 起草 F012 spec

**与 PR #30 的关系**:
- PR #30 是 polish (writing pack +1 skill + sidecar copy bug fix), **不阻塞** F012 cycle
- 建议 PR #30 单独 merge (与 PR #25 同精神 — user-driven content sync); F012 spec 起草时 base on post-#30 main

## 5. 关联文档

- 灵魂: `docs/soul/{manifesto, user-pact, growth-strategy, design-principles}.md`
- 上一份 planning (4-24): `docs/planning/2026-04-24-vision-gap-and-next-cycle-plan.md`
- F010 finalize approval (carry-forward 列表): `docs/approvals/F010-finalize-approval.md`
- F011 finalize approval (D-1..4 deferred): `docs/approvals/F011-finalize-approval.md`
- 已完成 cycles: `RELEASE_NOTES.md` F001-F011

---

> **本文档是 planning artifact, 不是 spec**. 真正的 F012 spec 由 `hf-specify` 起草, 经 `hf-spec-review` 评审后落 `docs/features/F012-...md`.
