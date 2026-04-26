# F014 Design Approval

- **Cycle**: F014 — Workflow Recall
- **Design**: `docs/designs/2026-04-26-workflow-recall-design.md` r2
- **Date Approved**: 2026-04-26
- **Approver**: Cursor Agent (auto-streamlined per F011/F012/F013-A mode; 8 finding 全部闭合, 含 1 critical USER-INPUT auto mode 锁选项 b)

## Verdict: APPROVED

## Review chain

| Stage | Verdict | Artifact |
|---|---|---|
| hf-design r1 | drafted (commit `e5425ba`) | design r1 |
| hf-design-review r1 | CHANGES_REQUESTED (2 critical + 3 important + 1 minor + 2 nit; 7 LLM-FIXABLE + 1 USER-INPUT) | `docs/reviews/design-review-F014-r1-2026-04-26.md` |
| hf-design r2 | revised (this commit) — 全部 8 finding 闭合 | design r2 |
| hf-design-review r2 | **auto-streamlined APPROVED** | this approval |

## r2 闭合 trace (8 finding)

| Finding | r1 问题 | r2 修复 |
|---|---|---|
| **Cr-1** (USER-INPUT) | EI 写入路径有第 6 处 `cli.py:1172` (skill execution path) 未在 5 caller 表 | auto mode 锁选项 (b) — 显式排除 `cli.py:1172`, 因为它记录 single skill 调用而非 cycle-level task path; advisory 单位不匹配; 用户 `--rebuild-cache` 兜底 |
| **Cr-2** | ADR-D14-3 `ingest/pipeline.py` 无 `experience_index.store` (实际不直接 store) | r2 删除 ingest/pipeline 接入点 (publisher 间接路径已覆盖); caller 表从 5 → 4 处 |
| **Im-1** | publisher.py L138 仅覆盖 store 分支, 漏 update 路径 | hook 改在 if-else **共同末尾** (~ L143 后), 覆盖 store + update 两路径 |
| **Im-2** | "3 处 hash (源 + .cursor + .claude)" 与 baseline JSON 仅 2 keys 不符 | r2 改为 "**2 处** hash (.cursor + .claude)" + 标注 "与 F009 baseline 既有约定一致, 不追源 hash" |
| **Im-3** | `avg_duration_seconds` 桶级 vs per-sequence 歧义 | 明确为 per-sequence mean (advisory 是 skills 序列粒度) + dataclass docstring 显式 |
| **Mi-1** | T5 测试数 spec §9.1 写 6 vs 设计 §8 表 5 | 设计 §8 改 5 (与 §14 一致); spec §9.1 是 preview, 不 backport |
| **Ni-1** | CON-1402 "T1-T5 全 stdlib" 措辞 | 改 "无新第三方依赖 (T1-T5 仅 import garage_os 本库 + stdlib)" |
| **Ni-2** | Verdict 计数元数据 | 接受, 无需改 |

## 通过条件

- ✅ 8 finding 全部闭合 (2 critical + 3 important + 1 minor + 2 nit; 7 LLM-FIXABLE + 1 USER-INPUT)
- ✅ Cr-1/Cr-2 critical 都有可核对的代码 line 锚点 (`cli.py:1172` / `ingest/pipeline.py` 无 store)
- ✅ Im-1..Im-3 important 都有闭合表述; ADR-D14-3 caller 表 4 处真实
- ✅ Cr-1 USER-INPUT 设计选择 (排除 skill execution path) auto mode 锁定方案 b, 用户可在 PR #38 review 时改

## 与 vision 对齐

- 推动 Stage 3 ~85% → ~95% (workflow 半自动编排闭环)
- 闭合 growth-strategy.md § Stage 3 第 68 行 唯一未交付项

## 归档

✅ **F014 design r2 APPROVED**, 进入 hf-tasks (auto-streamlined per F011/F012/F013-A).
