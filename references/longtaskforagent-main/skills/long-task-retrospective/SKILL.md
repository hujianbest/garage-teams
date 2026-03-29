---
name: long-task-retrospective
description: "Use after ST Go verdict when retrospective records exist and user authorized feedback — consolidate records and POST to REST API"
---

# Retrospective Report — Consolidate & Upload Skill Improvement Records

Invoked conditionally by `long-task-st` Step 12.5 after Go verdict, when retrospective records exist and feedback is authorized. This skill consolidates collected records and uploads them to the configured REST API endpoint.

**Announce at start:** "I'm using the long-task-retrospective skill. Preparing to report skill improvement records."

**Core principle:** This skill only reports — it does NOT modify skill files. Improvement records are uploaded for analysis and potential integration into future skill releases.

## Checklist

### 1. Gate Check

Verify both conditions:

**a) Authorization**:
- Read `feature-list.json` — check `retro_authorized` field
- If absent or `false` → print "Retrospective: not authorized — skipping" → STOP

**b) Service reachability**:
```bash
python scripts/check_retro_auth.py feature-list.json
```
- Exit 0 (ready) → proceed
- Exit 1 (unavailable) → print "Retrospective: endpoint unavailable — skipping" → STOP
- Exit 2 (disabled) → print "Retrospective: no endpoint configured — skipping" → STOP

### 2. Read Records

Read all `docs/retrospectives/*.md` files (excluding `reported/` subdirectory):

```bash
python scripts/check_retrospective_readiness.py
```

For each record, validate:
```bash
python scripts/validate_retrospective_record.py docs/retrospectives/<file>.md
```

- Valid records → include in report
- Invalid records → log warning, exclude from upload

### 3. Summary

Compile statistics from record frontmatter:
- Total records (valid only)
- By severity: critical / important / minor
- By category: skill-gap / missing-rule / false-assumption / template-defect / process-gap
- By classification: systemic / one-off

Present summary to user.

### 4. User Confirmation

Use `AskUserQuestion`:
```
"本项目共搜集 {N} 条 Skill 改进记录（critical: {X}, important: {Y}, minor: {Z}）。
 其中系统性问题 {S} 条，一次性问题 {O} 条。是否上报到 {endpoint}？"

Options: "确认上报 (Recommended)" / "跳过本次上报"
```

- User chooses "跳过" → print "Retrospective: user skipped upload" → STOP
- User chooses "确认上报" → proceed

### 5. Upload

```bash
python scripts/post_retrospective_report.py --feature-list feature-list.json
```

The script:
1. Compresses `docs/retrospectives/*.md` into `retrospectives.tar.gz`
2. POSTs as multipart/form-data to the configured endpoint
3. Includes metadata: project name, date, branch, record count

- Exit 0 → print "Retrospective: {N} records uploaded successfully"
- Exit 1 → print error, do NOT retry — report the failure to user

### 6. Cleanup

- Move uploaded records to `docs/retrospectives/reported/` (audit trail)
- Git commit: `retro: upload {N} skill improvement records`
- Update `task-progress.md` with retrospective entry

## Critical Rules

- **Never modify skill files** — this skill only collects and reports
- **Gate check is non-negotiable** — both authorization AND reachability must pass
- **User confirmation required** — never upload without explicit user consent
- **Privacy first** — records must not contain project source code, business data, or credentials
- **One upload per ST cycle** — do not upload partial batches during Worker sessions
- **Failure is non-blocking** — upload failure does not affect ST verdict

## Integration

**Called by:** `long-task-st` (Step 12.5, after Persist, before Verdict)
**Requires:** `retro_authorized` = true in feature-list.json AND endpoint reachable
**Reads:** `docs/retrospectives/*.md`, `feature-list.json`
**Produces:** moves records to `docs/retrospectives/reported/`
**Scripts used:** `check_retro_auth.py`, `check_retrospective_readiness.py`, `validate_retrospective_record.py`, `post_retrospective_report.py`
