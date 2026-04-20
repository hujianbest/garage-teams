# Approval Record - F007 Spec

- Artifact: `docs/features/F007-garage-packs-and-host-installer.md`
- Approval Type: `specApproval`
- Approver: cursor cloud agent (auto-mode policy approver)
- Date: 2026-04-19
- Workflow Profile / Execution Mode: `coding` / `auto-mode`
- Workspace Isolation: `in-place`

## Evidence

- Round 1 review: `docs/reviews/spec-review-F007-garage-packs-and-host-installer.md` (R1 部分) — `需修改`
  - 0 critical / 1 important / 3 minor (all LLM-FIXABLE)
  - F-1 [important][Q4/A3] FR-707 自相矛盾 + Python 函数签名固化（design 泄漏）
  - F-2 [minor][Q1] § 1.3 cli.py 行号锚点漂移
  - F-3 [minor][Q4] § 4.1 包含表 vs FR-708 优先级 wording 不一致
  - F-4 [minor][G1/GS3] FR-706 单条复合需求接近 oversized 边界
  - 全部 4 项均为 LLM-FIXABLE，USER-INPUT=0，可在同一回合内消化
- Round 1 follow-up commit: `eebc533` "F007 spec r2: address hf-spec-review findings (1 important + 3 minor, all LLM-FIXABLE)"
  - F-1 闭合：FR-707 statement 退到 capability-level，去掉 `target_skill_path / target_agent_path / render` 函数签名 + 类型注解；验收 #3 删除 `.claude/skills/hf-specify/SKILL.md` 字面值，与 NFR-701 显式 cross-link
  - F-2 闭合：§ 1.3 改为按符号定位（`DEFAULT_PLATFORM_CONFIG.host_type` / `DEFAULT_HOST_ADAPTER_CONFIG.host_type`）
  - F-3 闭合：§ 4.1 包含表"标记块"行加 `(Should，参 FR-708)` 注解 + manifest content_hash 回退说明
  - F-4 闭合：FR-706 拆为 FR-706a（未修改幂等）+ FR-706b（已修改保护与 `--force`）；"新增 host 追加" 验收并入 FR-704 末条；连带同步 FR-708、NFR-704 的 cross-ref
- Round 2 review: `docs/reviews/spec-review-F007-garage-packs-and-host-installer.md` (R2 Delta 部分) — `通过`
  - 0 critical / 0 important / 0 minor
  - r1 全部 4 条 finding 闭合（4 closed / 0 open / 0 regressed）
  - delta-focused 回归扫描覆盖 Q4 / A3 / Q3 / A6 / Q2 / G1 / C1 / C2 / C3 / C5 / G3 共 10 个回归点，全部 ✓
  - 1 条 informational 观察（§ 4.1 / § 12 速记签名残留）已说明非 finding，不要求 author 修订
  - `needs_human_confirmation=true` 但 reviewer 已说明 `auto` mode 下父会话可写 approval record；不存在 USER-INPUT 类阻塞
  - `reroute_via_router=false`
- Auto-mode policy basis: `AGENTS.md` 未限制 coding cycle 内 spec 子节点 auto resolve；本 cycle 由父会话路由为 `auto-mode`，approval step 在 record 落盘后即可解锁下游

## Decision

**Approved**. Spec 状态由 `草稿` → `已批准（auto-mode approval）`。下一步 = `hf-design`，输入为本 spec + F001 host adapter 抽象（`HostAdapterProtocol` 不变契约） + F002 既有 `garage init` 行为 (向后兼容承诺，CON-702) + F005 既有 stdout marker 风格（FR-709 同构）。

## Hash & 锚点

- Spec 初稿提交: `a92eef7` "F007 spec draft: Garage packs & host installer"
- r2 修订提交: `eebc533` "F007 spec r2: address hf-spec-review findings (1 important + 3 minor, all LLM-FIXABLE)"

## 后续 (informational, 不阻塞 approval)

- § 4.1 包含表与 § 12 术语表内的 `target_skill_path / target_agent_path / render` 速记可在 `hf-design` 完成命名定型后一次性回填，与 design 命名对齐。
- § 11 非阻塞性开放问题 4 条（Cursor surface 选型、安装标记块形式、交互 prompt 实现、pack-id 收敛）由 design 阶段消化。
