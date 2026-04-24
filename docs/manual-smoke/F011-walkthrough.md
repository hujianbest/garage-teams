# F011 Manual Smoke Walkthrough

- **日期**: 2026-04-24
- **执行人**: Cursor Agent (auto mode, P1 三合一 cycle)
- **PR**: TBD; branch `cursor/f011-style-agents-pack-install-bf33`

## Tracks

### Track 1 — Dogfood `garage init` (3 agents 装到 host)

```
$ garage init --hosts cursor,claude
Initialized Garage OS in /workspace/.garage
Installed 62 skills, 3 agents into hosts: claude, cursor
```

✓ "1 agents" → "3 agents" (was: garage-sample-agent only; now + code-review-agent + blog-writing-agent).

### Track 2 — `garage knowledge add --type style`

```
$ garage knowledge add --type style --topic "F011 demo style" --content "Prefer explicit over implicit (F011 manual smoke)."
Knowledge entry 'style-20260424-31e155' added
```

✓ FR-1102 + INV-F11-1: STYLE entry created under `.garage/knowledge/style/`.

### Track 3 — `garage sync` includes style + 3 agents装载

```
$ garage sync --hosts claude
Synced 1 knowledge entries + 0 experience records into hosts: claude

$ ls .claude/agents/
blog-writing-agent.md
code-review-agent.md
garage-sample-agent.md

$ grep "Recent Style Preferences" CLAUDE.md
### Recent Style Preferences (1)
```

✓ FR-1103 + INV-F11-2: F010 sync compiler 自动 include STYLE 段; CLAUDE.md 含 `### Recent Style Preferences (1)`.
✓ INV-F11-3: 3 agents 全部装到 .claude/agents/.

### Track 4 — `garage pack ls` (4 existing local packs)

```
$ garage pack ls
Installed packs (4 total):
  coding v0.2.0 [local]
  garage v0.3.0 [local]
  search v0.1.0 [local]
  writing v0.1.0 [local]
```

✓ FR-1107 + ADR-D11-7: marker `Installed packs (N total):` 与 F007 family 一致.
✓ F007 既有 4 packs (no `source_url` field) → 列为 'local' (FR-1108 backward compat).
✓ garage v0.2.0 → v0.3.0 (F011 ADR-D11-X version bump).

### Track 5 — `garage pack install file://<local-pack>` (FR-1106)

```
$ # Build a test pack with git init at /tmp/f011-test-pack
$ # Then in fresh workspace:
$ garage pack install file:///tmp/f011-test-pack
Installed pack 'smoke-test-pack' v0.1.0 from file:///tmp/f011-test-pack
  → /tmp/f011-workspace/packs/smoke-test-pack

$ cat /tmp/f011-workspace/packs/smoke-test-pack/pack.json | tail -3
  "agents": [],
  "source_url": "file:///tmp/f011-test-pack"
}

$ garage pack ls --path /tmp/f011-workspace
Installed packs (1 total):
  smoke-test-pack v0.1.0 [file:///tmp/f011-test-pack]
```

✓ FR-1106 + INV-F11-5: shallow `git clone --depth=1` + 物化 + `source_url` 写入.
✓ FR-1108: `pack.json` 加 `source_url` 字段, F007 既有 schema 不破坏.

## 测试基线

- F010 baseline: 825 passed
- F011 实施完成: **855 passed** (+30, 0 regressions)
- INV-F11-1..7 全部通过

## Conclusion

✅ F011 5 tracks 全绿. 三 P1 candidates (style 维度 / 2 production agents / pack install) 端到端可用.

post-cleanup: re-dogfood `garage init --hosts cursor,claude` 恢复 IDE 加载入口.
