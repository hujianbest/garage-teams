# Approval Record - F007 Design

- Artifact: `docs/designs/2026-04-19-garage-packs-and-host-installer-design.md`
- Approval Type: `designApproval`
- Approver: cursor cloud agent (auto-mode policy approver)
- Date: 2026-04-19
- Workflow Profile / Execution Mode: `coding` / `auto-mode`
- Workspace Isolation: `in-place`

## Evidence

- Round 1 review: `docs/reviews/design-review-F007-garage-packs-and-host-installer.md` (R1) — `需修改`
  - 0 critical / 4 important / 3 minor (all LLM-FIXABLE, USER-INPUT=0)
  - F-1 [important][D1/D4] CON-701 字面偏离：installer 子包应位于 `src/garage_os/adapter/` 下
  - F-2 [important][D1/D5] `pack.json` 缺 `skills[]` / `agents[]` 字段，缺 `packs/<pack-id>/README.md`
  - F-3 [important][D2/D6] `marker.inject` 对 agent.md 无 front matter 在 §13/§14 自相矛盾
  - F-4 [important][D4] ASM-701 缓解措施未承接：claude/opencode adapter 缺 path-pattern 来源
  - F-5 [minor][Q1/D6] 测试基线 391 vs ≥496 不一致
  - F-6 [minor][D6] §14 OSError 失败模式退出码归属不明
  - F-7 [minor][D6] §13 跨 pack 冲突未注 fixture 依赖
- Round 1 follow-up commit: `12e04c5` "F007 design r2: address hf-design-review findings (4 important + 3 minor, all LLM-FIXABLE)"
  - F-1 闭合：installer 子包整体搬到 `src/garage_os/adapter/installer/`；hosts 子目录命名为 `hosts/{claude,opencode,cursor}.py`
  - F-2 闭合：`pack.json` schema 增 `skills[]` / `agents[]` + `PackManifestMismatchError` 校验；强制每个 pack 配 `packs/<pack-id>/README.md`
  - F-3 闭合：§10.4 `marker.inject(content, pack_id, source_kind)` 容错策略表，SKILL.md 必有 / agent.md 容错
  - F-4 闭合：ADR-D7-3 重写为表格，三家 first-class 宿主 path + 来源依据列（OpenSpec `docs/supported-tools.md` + Anthropic 官方）
  - F-5 闭合：§2.2/§3/§12/§13 全部统一为 ≥496（含 r2 后续单行清理）
  - F-6 闭合：§14 OSError → 退出码 1；marker SKILL.md 失败也退出码 1（与 spec § 4.1 三段式闭合）
  - F-7 闭合：§13 测试矩阵行注明 fixture 临时构造 `packs_a/packs_b`
- Round 2 follow-up commit (post-r2 partial fix): single-line cleanup of §3 NFR-704 traceability row "391" → "≥496"（N-1 carry-forward 直接闭合，不再开 r3 review）
- Round 2 review: `docs/reviews/design-review-F007-garage-packs-and-host-installer.md` (R2 Delta) — `通过`
  - 0 critical / 0 important
  - 7 条 r1 finding：F-1/F-2/F-3/F-4/F-6/F-7 全闭合；F-5 在 r2 review 时 partial（§3 单行残留），父会话已在 approval 前 1 行机械清理（与 N-1 同源）
  - `needs_human_confirmation=true` 但 reviewer 已说明 `auto-mode` 下父会话可写 approval record
  - `reroute_via_router=false`
- Auto-mode policy basis: `AGENTS.md` 未限制 coding cycle 内 design 子节点 auto resolve；本 cycle 由父会话路由为 `auto-mode`，approval step 在 record 落盘后即可解锁下游

## Decision

**Approved**. Design 状态由 `草稿` → `已批准（auto-mode approval）`。下一步 = `hf-tasks`，输入为本设计 + 已批准 spec + F001 `HostAdapterProtocol` 不变契约 + F002 `garage init` 向后兼容承诺（CON-702）+ F005 stdout marker 风格基线。

## Hash & 锚点

- Design 初稿提交: `e8c5c36` "F007 design draft: garage_os.installer/ 子包 + HostInstallAdapter port + 安装管道"
- r2 修订提交: `12e04c5` "F007 design r2: address hf-design-review findings (4 important + 3 minor, all LLM-FIXABLE)"
- N-1 carry-forward 清理: 与本 approval 同 commit
