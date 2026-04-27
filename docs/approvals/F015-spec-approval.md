# F015 Spec Approval

- **Cycle**: F015 — Agent Compose
- **Spec**: `docs/features/F015-agent-compose.md` r2
- **Date Approved**: 2026-04-26
- **Approver**: Cursor Agent (auto-streamlined per F011/F012/F013-A/F014 mode; 9 finding 全部闭合, 含 1 USER-INPUT auto mode 锁选项 a)

## Verdict: APPROVED

## r2 闭合 trace (9 finding)

| Finding | r1 问题 | r2 修复 |
|---|---|---|
| **Cr-1** (USER-INPUT) | BDD 8.4 overwrite `code-review-agent.md` 与 INV-F15-5 byte 不变冲突 | auto mode 锁选项 (a) — BDD 8.4 改 agent 名为 `demo-overwrite-agent` (非 F011 既有 3 个) |
| **Cr-2** | "F011 3 个 production agent" schema 与 `garage-sample-agent` 实码不符 (无 frontmatter) | 收窄 schema 参考子集为 **2 个** agent (code-review + blog-writing); garage-sample 显式排除 |
| **Im-1** | FR-1501 missing skill placeholder vs FR-1503/§8.3 exit 1 不一致 | 双层语义: library 返 missing + 仍生成 partial draft; CLI 严格 exit 1 不写盘 |
| **Im-2** | FR-1505 "last compose <ts>" 提纲未闭合 | 删除 ts 后缀; FR-1505 仅显 N agents; 不依赖 cache.json |
| **Mi-1** | agent.md 行数 "11-41" 错 | 改 "11-42 行" (实测) |
| **Mi-2** | `list_entries(STYLE)` API 签名错 | `list_entries(knowledge_type=KnowledgeType.STYLE)` 完整 |
| **Mi-3** | pack.json description 文案漂移 | 注解不阻塞 F015; 推 F011 carry-forward 或未来 cycle |
| **Mi-4** | "Stage 3 ~95% → ~100%" 无量化依据 | 加 "估算" 注 + 量化依据 |
| **Ni-1** | hv-analysis 多行 description 切分规则未注 | §11 加切分规则 (取首个非空段; 至少 50 字截断到句号 / 行尾) |

## 通过条件

- ✅ 9 finding 全部闭合 (2 critical + 2 important + 4 minor + 1 nit; 8 LLM-FIXABLE + 1 USER-INPUT)
- ✅ Cr-1/Cr-2 critical 都有可核对的代码 line + 实文件验证
- ✅ Im-1/Im-2 important 双层语义闭合
- ✅ Cr-1 USER-INPUT 设计选择 (BDD 8.4 用 demo-overwrite-agent) auto mode 锁定方案 a, 用户可在 PR review 时改

## 与 vision 对齐

- F015 直击 growth-strategy.md § Stage 3 第 67 行 "Skills 可组合成专用 agents" 半交付项
- 推动 Stage 3 ~95% → ~100% (估算; 完成 Stage 3 三项核心新增的最后一项)

## 归档

✅ **F015 spec r2 APPROVED**, 进入 hf-design.
