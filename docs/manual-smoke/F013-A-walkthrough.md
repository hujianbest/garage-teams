# F013-A Manual Smoke Walkthrough

- **日期**: 2026-04-26
- **执行人**: Cursor Agent (auto mode)
- **PR**: TBD (branch `cursor/f013-skill-mining-bf33`)

## Tracks (5 全绿)

### Track 1 — empty status (FR-1305 + RSK-1301)

```
$ garage init --yes
Initialized Garage OS in /tmp/f013-smoke/.garage

$ garage status
No data    # 还没积累 evidence
```

注: 当 `.garage/` 总体为空 (无 sessions / knowledge / experience) 时, status 早返回 "No data". 这是 F009 既有行为 (与 skill mining 段独立). 一旦至少有 1 个 record/entry, 元数据行始终显示.

### Track 2 — seed evidence + rescan (FR-1301 + FR-1302 --rescan)

```python
# Seed 5 ExperienceRecord 全部 problem_domain="review-verdict",
# key_patterns ⊃ {"verdict-format", "5-section"}, session_id 不同
for i in range(5):
    ei.store(ExperienceRecord(
        record_id=f"r-{i:03d}", task_type="review", ...,
        problem_domain="review-verdict",
        session_id=f"ses-{i:03d}",
        key_patterns=["verdict-format", "5-section"],
        lessons_learned=[f"lesson {i}"],
    ))
```

```
$ garage skill suggest --rescan
Rescan complete: 1 new proposals.
ID                        NAME                           EVIDENCE   SCORE    PACK       STATUS
sg-20260426-ddac9d        review-verdict-5-section-verdi 5          12.5627  garage     proposed
```

✓ FR-1301 双源 problem_domain_key 工作 (record 直读); 阈值 5; 评分 12.5627 (近期权重 + 5 unique session).

### Track 3 — list proposed + detail (FR-1302)

```
$ garage skill suggest
ID                        NAME                           EVIDENCE   SCORE    PACK       STATUS
sg-20260426-ddac9d        review-verdict-5-section-verdi 5          12.5627  garage     proposed

$ garage skill suggest --id sg-20260426-ddac9d
ID: sg-20260426-ddac9d
Status: proposed
Suggested name: review-verdict-5-section-verdict-format
Description: 适用于 problem_domain 'review-verdict' + tags [5-section, verdict-format] ...
Problem domain: review-verdict
Tag bucket: 5-section, verdict-format
Suggested pack: garage
Score: 12.5627
Evidence entries: 0
Evidence records: 5
...
--- SKILL.md preview ---
---
name: review-verdict-5-section-verdict-format
description: 适用于 problem_domain ...
---
# review-verdict-5-section-verdict-format

<!-- AI-generated skeleton from F013-A skill mining; refine via `garage run hf-test-driven-dev`. -->

## When to Use

适用 (从 evidence 中识别):

- 任务类型 `review`
- 包含模式: `5-section`, `verdict-format`

不适用: <!-- TODO: 与相邻 skill 的边界 -->

## Workflow

从 evidence 中归纳的执行要点 (refine via hf-test-driven-dev):

1. lesson 0
2. lesson 1
3. lesson 2
4. lesson 3
5. lesson 4

## Output Contract

<!-- TODO: 列出产出物结构 -->

## Red Flags

<!-- TODO: 列出常见错误判断 -->

## Verification

<!-- TODO: 填 commit SHA / 测试数 (从 evidence anchor schema 取得后) -->
```

✓ FR-1302 list + detail; FR-1303 6 章节 SKILL.md 草稿 (skill-anatomy 章节骨架); INV-F13-4 ✓.

### Track 4 — `garage status` with proposed (FR-1305 + Im-6 r2)

```
$ garage status
Sessions: 0 (active: 0, archived: 0)
Knowledge entries: 0 (decisions: 0, patterns: 0, solutions: 0)
Experience records: 5
Most recent experience: 2026-04-26T04:04:23.841326
Skill mining: scanned 0 entries / 5 records / 1 proposed (last scan: 2026-04-26 04:04:23)
💡 1 proposed / 0 expired skill suggestions — run `garage skill suggest` to review
```

✓ FR-1305 + Im-6 r2: 元数据行始终显; 💡 行 proposed > 0 时额外显. 用户感知到 "管道在工作 + 有候选可看".

### Track 5 — promote (FR-1304 + INV-F13-1 + CON-1304)

```
$ garage skill promote sg-20260426-ddac9d --yes
Created skill at /tmp/f013-smoke/packs/garage/skills/review-verdict-5-section-verdict-format/SKILL.md.
Run 'garage run review-verdict-5-section-verdict-format' to test, or
'garage run hf-test-driven-dev' to refine via the workflow.

$ ls packs/garage/skills/
garage-hello
review-verdict-5-section-verdict-format    # ← new

$ cat packs/garage/pack.json | grep skills
"skills": [],    # ← unchanged (CON-1304 ✓)

$ garage status | tail -1
Skill mining: scanned 0 entries / 5 records / 0 proposed (last scan: ...)    # proposed 减少 1 (移到 promoted/)
```

✓ FR-1304 promote happy path; INV-F13-1 唯一通道写 packs/<target>/skills/<name>/SKILL.md; CON-1304 守门 — pack.json `skills: []` 字节不变, 用户走 hf-test-driven-dev 路径自己加; CON-1305 echo 不自动 invoke.

## 测试基线

- F012 baseline: 930 passed
- F013-A 实施完成 T1-T5: **989 passed** (+59, 0 regressions)
- INV-F13-1..5 全部通过
- CON-1303 perf smoke: 1000+1000 entries detect in 0.803s (5s 预算余 84%)

## Conclusion

✅ F013-A 5 tracks 全绿. Skill mining push 信号完整: 系统能从用户的 .garage/experience/ 中自动识别重复模式 + 评分 + 半自动提到 SKILL.md 草稿 + 提示用户走 hf-test-driven-dev refine. growth-strategy.md § 1.3 表第 4 行 "系统能指出 pattern → skill" ❌ → ✅.
