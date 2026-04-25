# Task Progress

## Goal

- Goal: Post-PR#30+PR#32 refresh + F012 范围微调 (sidecar copy 与 discover_packs friction 已被 PR #30 解决, 移出 F012 范围)
- Owner: hujianbest
- Status: 🟡 Planning refresh 已落, 待用户确认 F012 范围 (5 部分锁定) 后启 hf-specify
- Last Updated: 2026-04-25 (午后, post-PR#30+#32)

## Previous Milestones

- F001 Phase 1: ✅ 完成（T1-T22，416 测试通过）
- F002 Garage Live: ✅ 完成（CLI + 真实 Claude Code 集成，436 测试通过）
- F003 Garage Memory: ✅ 完成（T1-T9，384 测试通过）
- F004 Garage Memory v1.1: ✅ 完成（T1-T5，414 测试通过）
- F005 Garage Knowledge Authoring CLI: ✅ 完成（T1-T6，451 测试通过）
- F006 Garage Recall & Knowledge Graph: ✅ 完成（T1-T5，496 测试通过；workflow closeout 见 `docs/verification/F006-finalize-closeout-pack.md`）
- F007 Garage Packs 与宿主安装器: ✅ 完成（T1-T5，586 测试通过；workflow closeout 见 `docs/verification/F007-finalize-closeout-pack.md`）
- F008 Garage Coding Pack 与 Writing Pack: ✅ 完成（T1a/T1b/T1c + T2 + T3 + T4a/T4b/T4c + T5，633 测试通过；workflow closeout 见 `docs/verification/F008-finalize-closeout-pack.md`）
- F009 garage init 双 Scope 安装: ✅ 完成（T1-T6 + manual smoke + post-code-review，713 测试通过；finalize approval 见 `docs/approvals/F009-finalize-approval.md`）
- packs/search hotfix: ✅ 落地（补 pack metadata + INV-1 30→31 + dogfood baseline 59→63，715 测试通过；PR #27）
- vision-gap planning (4-24): ✅ 落地（`docs/planning/2026-04-24-vision-gap-and-next-cycle-plan.md`；PR #27）
- **F010 Context Handoff + Host Session Ingest**: ✅ 完成（T1-T7 + smoke + post-code-review fix + StrEnum lint + e2e + finalize，825 测试通过；finalize approval 见 `docs/approvals/F010-finalize-approval.md`；PR #28 merged）
- **F011 KnowledgeType.STYLE + 2 production agents + garage pack install**: ✅ 完成（5 cycle commits，855 测试通过；finalize approval 见 `docs/approvals/F011-finalize-approval.md`；PR #29 merged）
- **PR #30 (writing magazine-web-ppt + sidecar copy + discover_packs friction fix)**: ✅ merged（user-driven; sidecar copy = F012-E 候选已实施; discover_packs 跳过无 pack.json = search hotfix 根因修；855 → 859 +4 sidecar 测试）
- **PR #31 (post-F011 planning artifact)**: ✅ merged（早上推荐 F012 lifecycle 完整化）
- **PR #32 (packs/coding v0.2.0 → v0.3.0 reverse-sync, +hf-doc-freshness-gate skill)**: ✅ merged（HF workflow 新 skill, 与 F012 lifecycle 无直接耦合, 但提供 evaluator pattern）

## Current Workflow State

- Current Stage: `planning` (post-PR#30+#32 refresh; F012 范围微调锁定为 5 部分)
- Workflow Profile: `N/A` (planning artifact, not a workflow cycle)
- Execution Mode: `auto`
- Workspace Isolation: `in-place`（工作分支 `cursor/post-pr30-pr32-planning-bf33`）
- Current Active Task: 无 (planning refresh 已落)
- Pending Reviews And Gates: 用户确认 F012 范围 (5 部分锁定 + 是否加 add candidates) → 启 `hf-specify`
- Next Action Or Recommended Skill: 用户确认后, 派发 `hf-specify` 起草 F012 spec (基于 `docs/planning/2026-04-25-post-pr30-pr32-next-cycle-plan.md` § 2.3 推荐)

## Next Step

post-PR#30+#32 refresh: PR #30 已实施 sidecar copy + discover_packs friction fix, F012 范围**移出** F012-D/E, 节省下来的容量加深 publish + 脱敏.

### F012 锁定范围 (5 部分)

| 部分 | 描述 | 优先级 |
|---|---|---|
| **F012-A** | `garage pack uninstall <pack-id>` (反向 install) | Must |
| **F012-B** | `garage pack update <pack-id>` (从 source_url 重新拉) | Must |
| **F012-C** | `garage pack publish <pack-id> --to <git-url>` (push to remote) | Must |
| **F012-D** | knowledge 脱敏导出: `garage knowledge export --anonymize` (与 publish 一起) | Must |
| **F012-E** | F009 carry-forward: VersionManager 注册 host-installer migration 链 | Should |

**Out of scope (deferred)**:
- pack info / search (add candidates, 与 lifecycle 主轴正交)
- monorepo / signature (F011 D-2/3)
- HOST_REGISTRY plugin / sync watch / Memory push (4-24 P2 三项, 触发信号未到)
- F010 code-review carry-forward MIN-1..6 (cli polish)

**预估难度**: 中 (publish 涉及 git remote + 脱敏需要规则; F012-A/B 复用 F011-C `install` 反向)

### 三 cycle 推荐组合 (与早上一致)

```
F012 (pack lifecycle 完整化)
  → F013 (Stage 3 工匠自动化, 等 session 数累积)
  → F014 (Stage 4 生态最小可证, 等社区分享活动)
```

详见 `docs/planning/2026-04-25-post-pr30-pr32-next-cycle-plan.md`.

## Vision Progress 快照 (post-PR#30+#32, 与 post-F011 一致 — PR #30/#32 是 polish + content 不影响 vision dimensions)

- 5 promise: 全部 5/5 ✅
- 5 信念: B1/B3 5/5 ✅; B4 4/5 ⚠️; B2/B5 3-3.5/5 ⚠️
- 4 stage: 1: 100% ✅; 2: 95% ✅; 3: ~25% ⚠️ (但 trigger "Skills > 30" 更强达成 31 → **33**); 4: ~10% ⚠️

**重心仍是"Stage 3/4 飞轮 + 信念 B5 闭环" — F012 lifecycle 完整化是关键步**.

## 完成证据 (累积)

- 测试基线增长曲线: 416 (F001) → 633 (F008) → 715 (F009 + search hotfix) → 825 (F010) → 855 (F011) → **859 (post-PR#30+#32, +4 sidecar 测试)**
- packs 累积: 1 sample → 31 (F011 末) → **33 skills** (post-PR#30 +1 magazine-web-ppt + post-PR#32 +1 hf-doc-freshness-gate)
- F010 cycle: 12 commits + 13 ADR + 10 INV + 9 review/gate verdict
- F011 cycle: 5 commits + 7 ADR + 7 INV (auto-streamlined)
- 完成 P0 + P1 全部 vision-gap candidate
- PR #30 顺手解决 F012-D/E 两个候选 (sidecar copy + discover_packs friction)
