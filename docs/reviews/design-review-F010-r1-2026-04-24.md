# Design Review — F010 Garage Context Handoff + Host Session Ingest (r1)

- **Target**: `docs/designs/2026-04-24-garage-context-handoff-and-session-ingest-design.md` (草稿 r1)
- **Reviewer**: Independent generalPurpose subagent (read-only, hf-design-review SKILL)
- **Date**: 2026-04-24
- **关联 spec**: r2 已批准 (`docs/approvals/F010-spec-approval.md`)

## Verdict: **需修改** (REVISE)

3 critical / 5 important / 5 minor (全部 LLM-FIXABLE, 0 USER-INPUT). 1 轮定向回修可闭合.

## Findings

### Critical (3) — 阻塞 hf-tasks

- **C-1** [D5/D2]: ADR-D10-9 + § 3.2 伪代码与 `SessionManager.archive_session()` 实际签名不符. 设计写 `archive_session(..., outcome="imported", artifacts=[])` 与 `update_session(..., context=session.context)`, 但 `src/garage_os/runtime/session_manager.py:157` 实际签名是 `(session_id, reason="...", extraction_orchestrator=None)`; `update_session(**kwargs)` 不识别 `context=` (line 108-155 只接受 `state` / `current_node_id` / `pack_id` / `topic` / `context_metadata` / `artifacts`). 直接照抄会 TypeError + 静默丢失 provenance → INV-F10-7/8 红, SM-1002 链断.

- **C-2** [D6/D4/A2]: INV-F10-7 + manual smoke Track 3 + § 3.2 + ADR-D10-9 都默认 archive 自动触发 F003 提取链, 但 `DEFAULT_PLATFORM_CONFIG.memory.extraction_enabled=False` 是默认关闭, `_trigger_memory_extraction` (session_manager.py:240-246) `if not enabled: return` 早退, ingest 链空跑. FR-1005 BDD acceptance 默认环境无法满足.

- **C-3** [D6/D5]: 即便 C-2 修好, `_build_signals` (extraction_orchestrator.py:121-192) 只识别 `metadata.tags` / `metadata.problem_domain` / `archived_session.artifacts` 三种强 signal; 设计仅写 `metadata={"imported_from": ...}` 不会命中, 走 `no_evidence` 分支 (line 52-62) 写空 batch, 0 candidate item. INV-F10-7 不可重现.

### Important (5)

- **I-1** [D5/A2]: ADR-D10-3 SKIP_LOCALLY_MODIFIED 文字描述与 § 3.1 数据流不一致 (盘上现状 vs 上次 sync 写入快照混淆), 易让 hf-tasks 把 SKIP 实施成 "Garage 知识库每次更新都 SKIP".
- **I-2** [D2/D5]: ADR-D10-11 install `claude` vs ingest `claude-code` 命名差异无 alias 兜底, 仅 "文档化解决" 过于轻描. 建议 HOST_READERS registry 加 alias.
- **I-3** [D5]: `garage status` sync 段实施细节缺 ADR, FR-1009 字节级 fallback (sync-manifest.json 不存在时不打印任何 sync 字符) 易破 CON-1001 dogfood sentinel.
- **I-4** [D6]: INV-F10-2 (F009 baseline 715 测试 0 退绿) 测试矩阵无显式 sentinel 文件位, 与 INV-F10-1 不对称.
- **I-5** [D5]: `--force` flag 在 spec 未承诺, design 仅在 ADR-D10-3 + § 3.1 顺手提了; hf-tasks 不知是否要做. 必须 spec/design 协调收敛或 deferred.

### Minor (5)

- **M-1** [D3]: ADR-D10-4 budget=16KB 选取理由内部矛盾 ("conservative 上限" + "已激进").
- **M-2** [D6/A2]: § 4.3 manual smoke Track 3/4 fixture 文件位需明示.
- **M-3** [D5]: ADR-D10-2 `name` 参数对 claude/opencode unused 应在 adapter docstring 注明.
- **M-4** [D5]: `targets[].path` "absolute POSIX path" 跨平台语义不严, 建议 `Path(...).resolve(strict=False).as_posix()`.
- **M-5** [A4]: NFR-1004 sync ≤ 5s 大库 (200+ entries) scaling 未 ADR 锚定.

## 是否需要回到 hf-design

✅ **是** — 1 轮定向回修可闭合. C-1/C-2/C-3 是与既有 F003-F006 真实 API 不符, 必须修.

## Structured Return

```json
{
  "conclusion": "需修改",
  "verdict": "REJECT (1 round revise)",
  "next_action_or_recommended_skill": "hf-design",
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "finding_count": {"critical": 3, "important": 5, "minor": 5},
  "all_llm_fixable": true,
  "user_input_count": 0
}
```
