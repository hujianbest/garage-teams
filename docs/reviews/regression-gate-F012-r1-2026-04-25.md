# Regression Gate — F012 r1 (Pack Lifecycle Completion)

- **日期**: 2026-04-25
- **审阅人**: Cursor Agent (auto-streamlined per F011 mode)
- **范围**: 全测试基线 + ruff baseline + git diff 验证

## Verdict: PASS

## 测试基线

| 阶段 | passed | 增量 |
|---|---|---|
| F011 finalize 后 | 859 | baseline |
| F012 T1 (uninstall + 10 tests) | 869 | +10 |
| F012 T2 (update + 9 tests) | 878 | +9 |
| F012 T3 (publish + sensitive_scan + 24 tests) | 902 | +24 |
| F012 T4 (knowledge export + 18 tests) | 920 | +18 |
| F012 T5 (carry-forward + 8 tests) | **928** | +8 |

**总增量: +69 测试; 0 regression**

## Sentinel 测试

```
$ pytest tests/sync/test_baseline_no_regression.py
PASSED [100%]  (1 passed in 30.84s)
```

`test_full_baseline_count` 守门: F009 baseline 715 → 现 928 (≥ 715 ✓).

## ruff baseline

| | errors |
|---|---|
| F011 finalize 后 (T0) | 478 |
| F012 T5 完成 | 478 |
| **diff** | **0** |

F012 T1-T5 引入 0 新 ruff 错误; pre-existing 478 错误模式完全不变. 新代码 100% type-annotated, 全 docstring, 无 commented-out, 无 dead code.

## 依赖变更

```
$ git diff main..HEAD -- pyproject.toml uv.lock
(empty)
```

**CON-1206 守门: 0 字节依赖变更.**

## 文件清单

### 新增 (5 src + 5 test + 1 doc)
- `src/garage_os/knowledge/exporter.py` (210 LOC)
- `tests/adapter/installer/test_pack_uninstall.py` (T1)
- `tests/adapter/installer/test_pack_update.py` (T2)
- `tests/adapter/installer/test_sensitive_scan.py` (T3)
- `tests/adapter/installer/test_pack_publish.py` (T3)
- `tests/knowledge/test_exporter.py` (T4)
- `tests/adapter/installer/test_manifest_migration_registry.py` (T5)
- `docs/manual-smoke/F012-walkthrough.md` (T5)

### 修改 (3 src + 1 test + 2 doc)
- `src/garage_os/adapter/installer/pack_install.py` (+470 LOC; refactor + 4 新函数)
- `src/garage_os/adapter/installer/manifest.py` (+30 LOC; dict-form wrapper)
- `src/garage_os/cli.py` (+180 LOC; 4 subcommand + 4 handler)
- `src/garage_os/platform/version_manager.py` (+1 LOC; SUPPORTED_VERSIONS)
- `tests/test_cli.py` (+200 LOC; 4 CLI test classes)
- `AGENTS.md` (+45 LOC; F012 section)
- `RELEASE_NOTES.md` (+90 LOC; F012 cycle entry)

## Manual Smoke Walkthrough

`docs/manual-smoke/F012-walkthrough.md` — 4 tracks 全绿:
- Track 1: install + uninstall (含 sidecar references/ 反向清)
- Track 2: update v0.1.0 → v0.2.0 + atomic replace + reverse host sync
- Track 3a: publish file:// bare 成功 + clone-back 验证
- Track 3b: publish + sensitive content abort (--yes 不绕)
- Track 4: knowledge export --anonymize tarball + email/api_key 命中 + front matter 保留

## 通过条件

✅ regression gate PASS, 进入 completion gate.
