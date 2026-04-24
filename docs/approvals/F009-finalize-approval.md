# F009 Finalize Approval

- **日期**: 2026-04-23
- **关联 cycle**: F009 — `garage init` 双 Scope 安装 (project / user) + 交互式 Scope 选择
- **关联 PR**: #24 (`cursor/f009-init-scope-selection-bf33`)
- **Workflow profile**: `full`
- **Execution mode**: `auto`

## ✅ Approval

F009 cycle 完成. 全部质量链路通过, 测试基线 713 passed (+80 from F008 baseline, 0 regressions), manual smoke 4 tracks 全绿. cycle closeout.

## 完整 review/gate 链路

| Stage | Verdict | 文档 |
|---|---|---|
| hf-spec-review | APPROVED (r2) | `docs/reviews/spec-review-F009-r1+r2-2026-04-23.md` |
| hf-design-review | APPROVED (r2) | `docs/reviews/design-review-F009-r1+r2-2026-04-23.md` |
| hf-tasks-review | APPROVED (r3) | `docs/reviews/tasks-review-F009-r1+r2+r3-2026-04-23.md` |
| hf-test-review | APPROVE_WITH_FINDINGS (0 critical) | `docs/reviews/test-review-F009-r1-2026-04-23.md` |
| hf-code-review | APPROVE_WITH_FINDINGS (0 critical, I-3+I-4 in-cycle fix) | `docs/reviews/code-review-F009-r1-2026-04-23.md` |
| hf-traceability-review | APPROVE_WITH_FINDINGS (0 critical) | `docs/reviews/traceability-review-F009-r1-2026-04-23.md` |
| hf-regression-gate | PASS | `docs/reviews/regression-gate-F009-r1-2026-04-23.md` |
| hf-completion-gate | COMPLETE — Ready to finalize | `docs/reviews/completion-gate-F009-r1-2026-04-23.md` |
| hf-finalize | ✅ closed | 本文档 |

## Carry-forward (F010+ candidate / 下 cycle 修)

### Important (3)

**I-1 / F-1 (CON-902 phase 1+3 body 守门偏弱)**
- 当前: `tests/adapter/installer/test_pipeline_scope_routing.py::TestPhase1Phase3AlgorithmInvariance` 仅 `inspect.signature`, 未对 `_check_conflicts` body 做 `inspect.getsource` 字节级比对
- 影响: 未来 cycle 可能在 phase 3 内悄悄加业务逻辑而 test 不命中
- 处理: F010 candidate (与 garage uninstall/update --scope 同 cycle, 因为这两个反向操作天然要重审 phase 3 conflict 检测)
- 建议修复: 加 `inspect.getsource(_check_conflicts)` body 与 baseline hash 比对; 或 carry over baseline ast 节点比对

**I-2 / F-3 (`VersionManager` host-installer migration 链未注册)**
- 当前: `migrate_v1_to_v2` 函数存在但未通过 `@register_migration` 装饰器注册到 `VersionManager._MIGRATION_REGISTRY`
- 影响: 功能正确 (`read_manifest` 自动 detect + migrate 已工作), 但与 F001 platform contract 不对称; 未来若再加 schema 3 时 ad-hoc 分支会膨胀
- 处理: F010 candidate, 与 garage uninstall/update --scope 同 cycle (反向操作天然要走 VersionManager API)
- 建议修复: 在 `manifest.py` 模块加载时 `@register_migration(1, 2)` 包装 `migrate_v1_to_v2`, 或在 `platform/__init__.py` 显式注册

**F-2 (3 处用户面文档 schema_version=1 wording)**
- 当前: 在本 finalize 阶段已修复 (`AGENTS.md L35` + `docs/guides/garage-os-user-guide.md L687`)
- 处理: ✅ in-cycle fixed (本 commit)

### Minor (10) — 不阻塞

详见 prior reviews. 不展开. 下 cycle 参考.

## 实测填充字段 (RELEASE_NOTES.md F009 段已 sync)

| 字段 | 实测值 |
|---|---|
| `manual_smoke_wall_clock` | 0.11s (`garage init --hosts all --scope user`) |
| `pytest_total_count` | 713 passed (+80 from F008 baseline 633, 0 regressions) |
| `installed_packs_from_manifest` | dogfood 58 skills+1 agent / --hosts all 87+2 / user scope 87+2 (fake_home) |
| `commit_count_per_group` | 8 commits (T1-T6 各 1 + manual smoke 1 + post-code-review 1) |
| `release_notes_quality_chain` | ✅ 完整 |

## Cycle closeout

- F009 spec/design/tasks 三方 approved 文档保留
- 11 个 review/gate verdict 文档全部生成
- RELEASE_NOTES F009 段 status 更新为 ✅ 完成
- task-progress.md cycle status → closed
- 2 个 documentation cleanup (AGENTS.md + user-guide schema_version wording)

## Structured Return

```json
{
  "conclusion": "完成",
  "verdict": "APPROVED — F009 cycle closed",
  "next_action_or_recommended_skill": "null (cycle closed)",
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "测试基线": "713 passed (+80, 0 regressions)",
  "carry_forward_count": 3,
  "carry_forward_items": [
    "I-1/F-1 CON-902 body 守门 → F010 candidate",
    "I-2/F-3 VersionManager 注册链 → F010 candidate",
    "F-2 3 处文档 wording → ✅ in-cycle fixed"
  ]
}
```
