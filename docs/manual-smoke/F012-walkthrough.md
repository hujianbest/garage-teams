# F012 Manual Smoke Walkthrough

- **日期**: 2026-04-25
- **执行人**: Cursor Agent (auto mode)
- **PR**: TBD (branch `cursor/f012-pack-lifecycle-bf33`)

## Tracks (4 全绿)

### Track 1 — install + uninstall (FR-1201)

```
$ garage pack install file:///tmp/f012-pack-src
Installed pack 'smoke-pack' v0.1.0 from file:///tmp/f012-pack-src
$ garage init --hosts claude --yes
Installed 34 skills, 3 agents into hosts: claude
$ ls .claude/skills/hello/      # SKILL.md + references/
references
SKILL.md

$ garage pack uninstall smoke-pack --yes
Uninstalled pack 'smoke-pack' from 1 hosts (4 files removed)
$ ls packs/        # smoke-pack 不存在
coding garage README.md search writing
$ ls .claude/skills/   # hello 不存在
ai-weekly blog-writing find-skills garage-hello hf-bug-patterns ... (34 → 33)
```

✓ FR-1201 + ADR-D12-2 atomic 三步 transaction; pack dir + host 目录 + manifest 同步清; sidecar references/ 反向清.

### Track 2 — update (FR-1204)

```
$ garage pack install file:///tmp/f012-pack-src    # v0.1.0
$ # remote bumped to v0.2.0
$ garage pack update smoke-pack --yes
Updated pack 'smoke-pack' from v0.1.0 to v0.2.0
$ cat packs/smoke-pack/pack.json | grep version
  "version": "0.2.0",
```

✓ FR-1204 + ADR-D12-3 r2; 复用 _clone_pack_to_tempdir helper + install_packs(force=True) 反向同步 host.

### Track 3 — publish + sensitive scan (FR-1207 + FR-1208)

**Track 3a — clean pack publish**:
```
$ git init --bare -q /tmp/f012-bare-remote.git
$ garage pack publish smoke-pack --to file:///tmp/f012-bare-remote.git --yes
Published pack 'smoke-pack' v0.2.0 to file:///tmp/f012-bare-remote.git
$ git clone -q --branch main file:///tmp/f012-bare-remote.git /tmp/f012-clone-back
$ ls /tmp/f012-clone-back/
pack.json skills
$ cat /tmp/f012-clone-back/pack.json | grep version
  "version": "0.2.0",
```

✓ FR-1207 + ADR-D12-4 r2 + HYP-1203 + SM-1203; file:// bare push round-trip.

**Track 3b — sensitive scan abort**:
```
$ echo "password=should-not-publish" > packs/smoke-pack/secret.env
$ garage pack publish smoke-pack --to file:///tmp/f012-bare2.git --yes
Sensitive content detected in pack 'smoke-pack':
  secret.env:1 (password): password=should-not-publish
(0 binary/non-text files skipped). Use --force to override at your own risk (B5 user-pact).
```

✓ FR-1208 + flag matrix: `--yes` 不绕 sensitive scan (强约束).

### Track 4 — knowledge export --anonymize (FR-1211)

```
$ garage knowledge add --type decision --topic "F012 demo" \
    --content "Discussed with alice@example.com about api_key=sk-test123" --tags "smoke"
Knowledge entry 'decision-20260425-e76fab' added

$ garage knowledge export --anonymize
Exported 1 entries (2 sensitive matches redacted) to ~/.garage/exports/knowledge-2026-04-25T084125Z.tar.gz

$ tar -xzf ~/.garage/exports/knowledge-2026-04-25T084125Z.tar.gz -C /tmp/f012-extract
$ cat /tmp/f012-extract/knowledge-export/decisions/*.md
---
id: decision-20260425-e76fab
type: decision
topic: F012 demo
date: '2026-04-25T08:41:25.644993'
tags: [smoke]
...
---
Discussed with <REDACTED:email> about api_key=<REDACTED>
```

✓ FR-1211 + ADR-D12-5 r2; mixed strategy (front matter 字节级保留, body 脱敏); 7 类 ANONYMIZE_RULES 中 email + api_key 命中; tarball default `~/.garage/exports/`.

## 测试基线

- F011 baseline: 859 passed
- F012 实施完成 T1-T5: **928 passed** (+69, 0 regressions)
- INV-F12-1..9 全部通过

## Conclusion

✅ F012 4 tracks 全绿. Pack lifecycle (install ↔ uninstall + install ↔ update + install ↔ publish) 完整闭环 + knowledge export 脱敏 + F009 carry-forward 注册.
