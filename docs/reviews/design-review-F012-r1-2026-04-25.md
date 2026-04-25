# Design Review F012 r1 — 2026-04-25

## Verdict: **需修改 (CHANGES_REQUESTED)** — 1 critical + 6 important + 2 minor + 1 nit

## Critical (1)

**F-1** [LLM-FIXABLE]: ADR-D12-6 wrapper 签名与 `VersionManager.migrate()` 真实调用约定不兼容
- Real `migrator(data)` 只传 1 arg (version_manager.py:323), wrapper 写了 `(data, target_version)`
- Real `migrate_v1_to_v2(prior_v1: Manifest, workspace_root: Path)` 需 workspace_root, wrapper 拿不到
- 与 F010 r1 critical typo 同型: 设计写真实代码片段但与真实 API 不能 link
- **修方案 C**: wrapper 直接 dict-level 等价实现 v1→v2 transformation; 不调 migrate_v1_to_v2; 单元测试同时跑两路径 assert 等价

## Important (6)

- **F-2**: ADR-D12-3 `_clone_pack_to_tempdir(url) -> Path` 与 `tempfile.TemporaryDirectory` 寿命冲突 → 改 `@contextmanager` 形式
- **F-3**: ADR-D12-5 ANONYMIZE_RULES 缺 spec FR-1212 的 `secret` + `token` 两条; "5 类" → 实际 7 类 (与 FR-1208 SENSITIVE_RULES 1:1)
- **F-4**: ADR-D12-4 缺 FR-1207 r2 9 行 flag 状态表代码化 → 加 dispatch 伪代码 + 9 sub-test enum
- **F-5**: ADR-D12-3 step 5 调 `install_packs` 缺 `packs_root` 必需位置参数 + 必须传 `force=True` (覆盖 F009 locally-modified protection)
- **F-6**: ADR-D12-4 publish step 缺 `git init -b main` 显式 (旧 git 默认 master)
- **F-7**: ADR-D12-2 缺 CON-1205 sync-manifest.json (+ knowledge + experience + sessions) guard wording — 显式 enum 不读不写

## Minor (2) + Nit (1)

- **F-8**: design ADR-D12-4 git author fallback 与 spec FR-1207 step 5 wording 不一致 (`Garage <garage-publish@local>` vs reverse)
- **F-9**: ADR-D12-7 commit 表加 "Depends" 列 (T2 → T1 helper)
- **F-10**: 7 ADR 缺 Status 字段, 但 § 6 自检 ✓

## Structured Return

```json
{
  "conclusion": "需修改",
  "verdict": "CHANGES_REQUESTED",
  "next_action_or_recommended_skill": "hf-design",
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "finding_count": {"critical": 1, "important": 6, "minor": 2, "nit": 1, "total": 10},
  "blocker": "F-1: ADR-D12-6 wrapper signature incompatible (F010 r1 typo recurrence type)",
  "all_llm_fixable": true
}
```
