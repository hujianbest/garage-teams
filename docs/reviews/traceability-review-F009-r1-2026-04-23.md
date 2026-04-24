# Traceability Review — F009 `garage init` 双 Scope 安装 + 交互式 Scope 选择 (r1)

- **日期**: 2026-04-23
- **Reviewer**: Independent generalPurpose subagent (read-only, hf-traceability-review SKILL)
- **关联 PR**: #24 (`cursor/f009-init-scope-selection-bf33`)
- **关联 spec**: `docs/features/F009-garage-init-scope-selection.md`
- **关联 design**: `docs/designs/2026-04-23-garage-init-scope-selection-design.md`
- **关联 tasks**: `docs/tasks/2026-04-23-garage-init-scope-selection-tasks.md`
- **前序 reviews**:
  - `docs/reviews/test-review-F009-r1-2026-04-23.md` (APPROVE_WITH_FINDINGS, 0 critical)
  - `docs/reviews/code-review-F009-r1-2026-04-23.md` (APPROVE_WITH_FINDINGS, 0 critical, I-3+I-4 in-cycle fix)

## Verdict: **APPROVE_WITH_FINDINGS**

证据链整体闭合且高质量. F009 全部 10 FR / 4 NFR / 4 CON / 4 ASM 均能从 spec 双向追溯到 design ADR (11 个) + tasks T (T1-T6) + 8 个 cycle commits + 12 个测试文件, 每条 FR/ADR/INV 在代码 + 测试中均有 grep-able anchor. FR-710 等价 5 分钟冷读链 (`AGENTS.md` → `packs/README.md` → `docs/guides/garage-os-user-guide.md` → spec/design) 完整可达, 三个核心问题 (project/user 区别 / 怎么选 / per-host override) 都能被 cold reader 5 分钟内回答. 6 维度均分 **8.50/10**, **无核心断链**.

**Findings**: `0 critical / 3 important / 5 minor` (全部 LLM-FIXABLE, 不阻塞 hf-regression-gate).

**Decision**: 直接派发 `hf-regression-gate`. 3 important 全部已被 prior reviews 识别, hf-finalize 阶段 carry-forward.

## 量化覆盖度

| 维度 | 应有 | 实际 | 通过率 |
|---|---|---|---|
| FR (FR-901..910) | 10 | 10 | 100% |
| NFR (NFR-901..904) | 4 | 4 | 100% |
| CON (CON-901..904) | 4 | 4 (CON-902 守门偏弱已 surface) | 100% |
| ASM (ASM-901..904) | 4 | 4 | 100% |
| INV (INV-F9-1..9) | 9 | 9 (INV-F9-2 守门偏弱已 surface) | 100% |
| ADR (ADR-D9-1..11) | 11 | 11 | 100% |
| Cycle commits | 6 task + 1 smoke + 1 postcr | 8 | 100% |
| 测试基线 | F008 baseline 633 | 713 (+80, 0 退绿) | ✓ |

## 量化 Findings

### Critical (0)
无.

### Important (3) — 全部已被 prior reviews 识别, hf-finalize carry-forward

**F-1** [TZ4]: **INV-F9-2 phase 1+3 守门偏弱** (与 test-review I-1 + code-review I-1 同源)
- 锚点: `tests/adapter/installer/test_pipeline_scope_routing.py::TestPhase1Phase3AlgorithmInvariance` 仅 `inspect.signature`, 未 `inspect.getsource`
- spec/design/tasks 三方一致要求 (CON-902 + INV-F9-2 + tasks T2 acceptance) 期望 phase 1+3 算法主体字节级守门
- carry-forward to hf-finalize approval

**F-2** [TZ5]: **3 处用户面文档 manifest schema 残留 `schema_version=1` wording**
- 锚点:
  - `AGENTS.md L35` ".garage/config/host-installer.json (schema_version=1, ...)"
  - `docs/guides/garage-os-user-guide.md L499 / L514 / L687-691` 残留 schema 1 描述
  - `packs/README.md` 在 manifest 描述段未提及 schema 升级
- 现状: `RELEASE_NOTES.md ## F009 数据与契约影响` 段完整说明 schema 1→2 升级 + 安全语义 + migrate_v1_to_v2 函数, 但其它入口文档未级联
- 影响: 冷读用户从 AGENTS.md 入口看到 "schema_version=1" 字面会与实际 (2) 矛盾
- 建议: hf-finalize 阶段把这 3 处 wording 统一改为 "schema_version=2 (F009 升级, F007/F008 schema 1 manifest 由 read_manifest 自动 migrate)" 等中性表述

**F-3** [TZ3+TZ5]: **`VersionManager` host-installer migration 链未通过 `@register_migration` 注册** (与 code-review I-2 同源)
- 锚点: `src/garage_os/platform/version_manager.py` (无 host-installer migration); `src/garage_os/adapter/installer/manifest.py:175` (`migrate_v1_to_v2` 函数存在但未注册)
- spec FR-905 + design § 11 + tasks T3 acceptance #6 三方一致要求未达成
- 功能正确 (`read_manifest` 自动 detect + migrate 已工作), 仅追溯断裂
- carry-forward to hf-finalize approval

### Minor (5)

- **M-1** [TZ4]: `_Target.scope` / `ManifestFileEntry.scope` 用 `str` 而非 `ScopeLiteral` (类型一致性轻度漂移; ADR-D9-1 明确 Literal)
- **M-2** [TZ5]: `prompt_scopes_per_host` docstring 引用 ADR-D9-5 candidate C 但未引用 spec FR-903 #4 (non-TTY 退化)
- **M-3** [TZ4]: `tests/adapter/installer/dogfood_baseline/skill_md_sha256.json` 无 README 解释生成方法
- **M-4** [TZ3]: `ASM-902` (Path.home() 在所有支持 OS 工作) 在代码中无 grep anchor (隐式假设, 由 stdlib 保证, 无需显式)
- **M-5** [TZ5]: F009 8 个 cycle commits 全部按 task 分组, 但 1 个 commit (postcr) 未在 task plan 内 enumerate (因为是 code-review fix); 不算违反, 仅记录

## 5 分钟冷读链 (FR-710 等价)

✅ **完整可达**:

1. `AGENTS.md` 顶部 "Packs & Host Installer (F007/F008/F009)" 段 + "Install Scope (F009 新增)" 子段
2. → `packs/README.md` "Install Scope (F009 新增)" 段 (3 种使用方式 + 对照表 + 三家路径表)
3. → `docs/guides/garage-os-user-guide.md` "Install Scope (F009 新增)" 子段 (端到端用法 + 决策树 + 已知限制)
4. → `docs/features/F009-garage-init-scope-selection.md` (已批准 spec, 完整 FR/NFR/CON/ASM)
5. → `docs/designs/2026-04-23-garage-init-scope-selection-design.md` (11 ADR + 9 INV)

冷读用户 5 分钟内能回答的核心问题:
- ✓ project / user scope 区别? (packs/README.md 对照表 + user-guide 决策树)
- ✓ 怎么选? (3 种使用方式: --scope flag / per-host syntax / 交互式两轮)
- ✓ per-host override 语法? (`--hosts claude:user,cursor:project`)
- ✓ 三家宿主 user scope path? (claude / opencode XDG / cursor)
- ✓ 已知限制? (user-guide 末尾 + RELEASE_NOTES F010 候选段)

## 下一步

✅ **派发 `hf-regression-gate`**.

3 important 在 hf-finalize approval 文档中显式记录:
- F-1 (CON-902 phase 1+3 body 守门) — F010 candidate
- F-2 (3 处文档 schema_version=1 wording 级联) — hf-finalize 文档同步小修
- F-3 (VersionManager 注册链) — F010 candidate, 与 garage uninstall/update --scope 同 cycle

## Structured Return

```json
{
  "conclusion": "通过",
  "verdict": "APPROVE_WITH_FINDINGS",
  "next_action_or_recommended_skill": "hf-regression-gate",
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "finding_count": {"critical": 0, "important": 3, "minor": 5},
  "覆盖度": {"FR": "10/10", "NFR": "4/4", "CON": "4/4", "ASM": "4/4", "INV": "9/9", "ADR": "11/11"},
  "测试基线": "713 passed (+80 from F008 baseline 633, 0 regressions)"
}
```
