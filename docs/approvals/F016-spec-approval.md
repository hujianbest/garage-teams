# F016 Spec Approval

- **Cycle**: F016 — Memory Activation
- **Spec**: `docs/features/F016-memory-activation.md` r2
- **Date Approved**: 2026-04-27
- **Approver**: Cursor Agent (auto-streamlined per F011-F015 mode; 12 finding 全部闭合, 含 2 USER-INPUT auto mode 锁选项)

## Verdict: APPROVED

## r2 闭合 trace (12 finding)

| Finding | r1 问题 | r2 修复 |
|---|---|---|
| **Cr-1** (USER-INPUT 选 a) | `garage init --yes` 重载与 F007 host 行为冲突 | F016 不重载 --yes; --yes 默认 disabled; enable 仅 (1) interactive prompt y (2) `memory enable` |
| **Cr-2** (USER-INPUT) | HYP-1605 假设无 LLM = no-op 不符 F003 实现 | HYP 改写: F003 是本地 signal-driven 候选生成, 不调 LLM |
| **Cr-3** | --from-sessions vs 背景示例不一 | 删 --from-sessions (F010 既有覆盖) |
| **Cr-4** | --strict 缺 FR-1602 | 加 --strict flag |
| **Cr-5** | "Last extraction" 无持久化锚点 | 用 max(record.created_at) 计算 |
| **Im-1** | _status No data 早退 + STYLE 计数缺 | Memory extraction 行跨早退; STYLE 计数加入 total |
| **Im-2** | "复用 _knowledge_add" 措辞不准 | 改 "复用 F004 store API" |
| **Im-3** | problem_domain 大小写不一 | 全 lowercase |
| **Im-4** | knowledge/style 目录建议 | F011 KnowledgeStore.store 自动 ensure_dir |
| **Mi-1** | 锚点行号偏差 | 171-184 |
| **Mi-2** | F013-A sg- ID 误用 | 改 F005 exp- 模式 |
| **Mi-3** | "14 个 verdict" 夸大 | 改 "N 个" |

## 通过条件

- ✅ 12 finding 全闭 (5 critical + 4 important + 3 minor; 10 LLM-FIXABLE + 2 USER-INPUT)
- ✅ Cr-1 USER-INPUT auto mode 锁选项 a (不重载 --yes); 用户可在 PR review 时改
- ✅ Cr-2 USER-INPUT HYP 改写与 F003 实际代码一致

## 归档

✅ **F016 spec r2 APPROVED**, 进入 hf-design.
