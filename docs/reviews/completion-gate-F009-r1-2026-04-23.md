# Completion Gate — F009 `garage init` 双 Scope 安装 + 交互式 Scope 选择 (r1)

- **日期**: 2026-04-23
- **Gate Owner**: hf-completion-gate (in-cycle, agent mode)
- **关联 PR**: #24 (`cursor/f009-init-scope-selection-bf33`)
- **前序 reviews**:
  - hf-test-review: APPROVE_WITH_FINDINGS (0 critical)
  - hf-code-review: APPROVE_WITH_FINDINGS (0 critical, I-3+I-4 in-cycle fix)
  - hf-traceability-review: APPROVE_WITH_FINDINGS (0 critical, 3 important hf-finalize carry-forward)
  - hf-regression-gate: PASS (713 passed, +80, 0 regressions)

## Verdict: **COMPLETE — Ready to finalize**

## 完成度评估 (10 FR + 4 NFR + 4 CON + 4 ASM + 9 INV)

### FR (10/10 完成 + 验证)

| FR | 完成 | 验证证据 |
|---|---|---|
| FR-901 (--scope flag) | ✓ | `cli.py` argparse choices + `test_cli.py::TestInitWithScope` |
| FR-902 (per-host override `<host>:<scope>`) | ✓ | `host_registry.resolve_hosts_arg` + manual smoke Track 4 |
| FR-903 (交互式两轮) | ✓ | `interactive.prompt_scopes_per_host` (candidate C 三个开关) + `test_interactive_two_round.py` |
| FR-904 (三家 user scope path) | ✓ | adapter `_user` 后缀 method + manual smoke Track 3 |
| FR-905 (manifest schema 1→2 migration + 安全语义) | ✓ | `manifest.read_manifest` 自动 migrate + `test_manifest_migration_v1_to_v2.py` (含 SHA-256 + mtime 双重守门) |
| FR-906 (pipeline scope 分流) | ✓ | `pipeline._resolve_targets` phase 2 分流 + `test_pipeline_scope_routing.py` |
| FR-907 (跨 scope 不冲突) | ✓ | `pipeline._check_conflicts` 三元组 key + `test_pipeline_scope_routing.py::TestPhase3ConflictsCrossScope` |
| FR-908 (status 按 scope 分组) | ✓ | `cli._status` ADR-D9-7 nested bullets + `test_cli.py::TestStatusScopeGrouped` |
| FR-909 (stdout marker 派生) | ✓ | F007 marker 字面不变 + 多 scope 附加段独立一行 + manual smoke Track 4 stdout 验证 |
| FR-910 (docs 同步) | ✓ | T6 commit (packs/README + user-guide + AGENTS + RELEASE_NOTES) |

### NFR (4/4 完成)

| NFR | 完成 | 验证证据 |
|---|---|---|
| NFR-901 (Dogfood 不变性硬门槛) | ✓ | `test_dogfood_invariance_F009` (59 文件 SHA-256) + manual smoke Track 1 |
| NFR-902 (零退绿) | ✓ | 633 → 713 passed (+80, 0 退绿); ruff baseline diff 0 |
| NFR-903 (perf) | ✓ | `garage init --hosts all --scope user` wall_clock 0.11s << 5s |
| NFR-904 (commit 可审计) | ✓ | 8 commits (T1-T6 + manual smoke + post-code-review), 每 commit 改动范围在 design § 11 估算内 |

### CON (4/4 完成)

| CON | 完成 | 验证证据 |
|---|---|---|
| CON-901 (F007/F008 字节级兼容) | ✓ | F007/F008 既有 installer 测试 23/23 通过 + dogfood stdout 字节级一致 |
| CON-902 (D7 phase 1+3 字节级) | ⚠️ | enum 守门通过 (函数签名 + 算法分支结构), 但 body 字节级守门偏弱 (I-1 carry-forward) |
| CON-903 (零依赖变更) | ✓ | `git diff main..HEAD -- pyproject.toml uv.lock` 输出空 |
| CON-904 (manifest migration 安全语义) | ✓ | `test_corrupted_manifest_not_overwritten` (SHA-256 + mtime 双重守门) |

### ASM (4/4 验证)

| ASM | 验证 |
|---|---|
| ASM-901 (XDG default 适用 OpenCode 多数用户) | manual smoke Track 3 验证 OpenCode XDG default 落盘 |
| ASM-902 (Path.home() 在所有支持 OS 工作) | stdlib 保证, 无显式守门; I-3 修复后 broken Path.home() 抛 UserHomeNotFoundError 而非 traceback |
| ASM-903 (UserHomeNotFoundError 真实场景能触发) | `test_code_review_fixes_F009::TestI3_UserHomeNotFoundErrorRealRaise` 守门 |
| ASM-904 (manifest 默认不入项目 git) | `.gitignore` 排除 `.garage/config/host-installer.json` (F008 既有, F009 沿用) |

### INV (9/9 完成)

| INV | 守门 |
|---|---|
| INV-F9-1 (Dogfood SHA-256 一致) | sentinel `test_dogfood_invariance_F009` |
| INV-F9-2 (CON-902 phase 1+3 字节级) | enum 守门通过, body 守门偏弱 (I-1 carry-forward) |
| INV-F9-3 (host_id 不含 `:`) | `host_registry._build_registry()` import-time assert + `test_host_registry_colon_assert.py` |
| INV-F9-4 (manifest schema 2 字段) | `test_manifest_schema_v2.py` |
| INV-F9-5 (跨 scope 不冲突) | `test_pipeline_scope_routing.py::TestPhase3ConflictsCrossScope` |
| INV-F9-6 (per-host override 解析) | `test_host_registry.py` (carry-forward) + manual smoke Track 4 |
| INV-F9-7 (manifest schema 2 user scope entries) | `test_full_init_user_scope.py::test_manifest_schema_v2_user_scope_entries` |
| INV-F9-8 (user scope 测试 fixture-isolated) | 5 个 user scope 测试文件统一 monkeypatch Path.home() |
| INV-F9-9 (extend mode 跨 scope 不漂移) | I-4 修复 + `test_code_review_fixes_F009::TestI4_MergeExistingCrossScopeNoDrift` |

## 完成证据

- **测试基线**: 633 (F008 baseline) → **713 passed** (+80 增量, 0 退绿)
- **新增测试文件**: 12 个 (含 1 个 baseline JSON fixture + post-code-review 1 个修复测试文件)
- **Cycle commits**: 8 个 (T1-T6 + manual smoke + post-code-review)
- **Manual smoke**: 4 tracks 全绿 (dogfood + project + user + mixed)
- **完整 review/gate 链路**: spec → design → tasks → impl → test-review → code-review (含 in-cycle fix) → traceability-review → regression-gate → completion-gate (本文档)

## 已知 carry-forward (hf-finalize approval 显式记录)

| 编号 | 描述 | 严重度 | 处理 |
|---|---|---|---|
| I-1 / F-1 | CON-902 phase 1+3 body 守门 (仅签名级, 未 inspect.getsource) | important | F010 candidate |
| I-2 / F-3 | VersionManager host-installer migration 链未注册 | important | F010 candidate, 与 garage uninstall/update --scope 同 cycle |
| F-2 | 3 处用户面文档 schema_version=1 wording 残留 | important | hf-finalize 文档同步小修 |
| 5 minor (test-review) + 5 minor (code-review) | 各类小瑕疵 | minor | 下 cycle 参考, 不阻塞 |

## 下一步

✅ **派发 `hf-finalize`**.

hf-finalize 阶段需要:
1. 更新 RELEASE_NOTES.md F009 段, 把 `状态: 🟡 实施完成, 待 review/gate 链路` → `状态: ✅ 完成 (closed by hf-finalize 2026-04-23)`
2. 把 5 项 TBD 占位字段填实测数据 (manual_smoke_wall_clock 0.11s / pytest_total_count 713 / installed_packs_from_manifest TBD / commit_count_per_group 8 / release_notes_quality_chain ✓)
3. 写 `docs/approvals/F009-finalize-approval.md` 显式记录 3 important carry-forward
4. 修 F-2 (3 处文档 schema_version=1 wording 同步)
5. 更新 task-progress.md → cycle closed
6. 必要时同步 `docs/features/INDEX.md` 等文档索引

## Structured Return

```json
{
  "conclusion": "完成",
  "verdict": "COMPLETE — Ready to finalize",
  "next_action_or_recommended_skill": "hf-finalize",
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "覆盖度": {"FR": "10/10", "NFR": "4/4", "CON": "4/4", "ASM": "4/4", "INV": "9/9"},
  "测试基线": "713 passed (+80, 0 regressions)",
  "carry_forward_to_finalize": ["I-1/F-1 CON-902 body 守门", "I-2/F-3 VersionManager 链", "F-2 3 处文档 wording"]
}
```
