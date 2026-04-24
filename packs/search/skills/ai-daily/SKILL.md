---
name: ai-daily
description: Use when the user wants a practical AI digest built from recent X/Twitter posts, especially from a fixed source roster, with a 7-day window, real tweet links, reusable tools/workflows/prompts, and a board-ready markdown report. Not for generic AI news, benchmark recaps, infrastructure updates, funding coverage, or paper-only summaries.
---

# AI Daily

Build a Chinese-first weekly digest from recent X/Twitter posts that a content creator can use immediately. This skill is for practical signal extraction and board-ready reporting, not for hype roundups or deep research essays.

## When to Use

Use this skill when:
- the user wants a weekly or daily AI digest from X/Twitter
- the user provides a source roster or named accounts to scan
- the user cares about prompts, tools, workflows, tutorials, methods, or creator productivity
- the output must be a concise markdown report with links and clear "why this matters"

Do not use this skill when:
- the request is for generic AI news, product launches, or industry recap
- the user wants a deep research report, competitive landscape, or long-form article
- the source is not X/Twitter posts
- the user mainly wants infrastructure, benchmark, funding, or enterprise-only announcements

## Hard Gates

- Do not guess the meaning of "current board". Resolve the target from session context, the current board artifact, or an explicit file path first. If the board target is not uniquely identifiable, ask once before writing.
- Do not use screenshots, aggregators, newsletters, or secondary summaries as substitutes for the original post. Every selected item must link to the original `x.com/.../status/...` or `twitter.com/.../status/...` URL.
- Do not pad the report. If fewer than 5 items pass the "immediately usable" bar, return fewer and explain why.
- Do not silently invent missing accounts. If the stated total and the explicit handle list disagree, treat the explicit roster as authoritative and note the discrepancy in the scan stats.
- Do not let "popular" replace "practical". Every item must pass the content-creator test: "Can the reader apply this immediately to improve work?"

## Quick Reference

| Step | Non-negotiable rule |
|---|---|
| Source scan | Scan all handles in the provided roster; scan the 6 priority accounts first |
| Search batching | Batch 10-15 handles per search pass after the priority batch |
| Time window | Restrict to the last 7 days |
| Search focus | `tool`, `workflow`, `method`, `tutorial`, `prompt`, `tip`, `guide`, `framework` |
| Inclusion bar | Practical, reusable, creator-relevant |
| Exclusions | Infra, security, benchmarks, funding, paper-only, enterprise-only |
| Output | Chinese markdown report with real tweet URLs and "为什么有用" |
| Save | Write the finished report to the resolved current board |

## Workflow

1. Resolve scope before searching.
   - Confirm the exact source roster. Use `references/source-roster.md` if the user did not override it.
   - Resolve the storage target for "current board" before drafting the final report.
   - Treat the explicit handle list as source of truth, even if the headline count is inconsistent.

2. Build the search plan.
   - Scan these priority handles first: `@zarazhangrui`, `@danshipper`, `@swyx`, `@karpathy`, `@rauchg`, `@amasad`.
   - After the priority pass, batch the remaining handles into groups of 10-15.
   - Prefer the host's Google-style search tool. If `googleSearch` is available, use it with `freshness="week"`.
   - Use search queries that combine handle batches with the intent keywords. Example:
     - `site:x.com (@swyx OR @karpathy OR @rauchg) (tool OR workflow OR method OR tutorial OR prompt OR tip OR guide OR framework)`
   - Keep a lightweight internal scan ledger: `handle`, `batch`, `query`, `hit/no hit`, `candidate URL`, `reason kept/dropped`.

3. Verify candidate posts.
   - Open only shortlisted results deeply enough to verify author, time window, and original post URL.
   - Prefer original posts over replies, reposts, screenshots, or third-party mirrors.
   - If a result points to a thread, keep the root tweet URL and summarize only the immediately useful takeaway.

4. Filter with the utility rubric.
   - Priority 1: immediately usable tools, plugins, apps, step-by-step tutorials, prompt templates, workflow tips.
   - Priority 2: reusable creator methodologies, AI best practices, productivity systems, skill-building frameworks.
   - Priority 3: mindset shifts that clearly change how a creator uses AI in practice.
   - Exclude anything that fails the test: "After reading this, can a content creator apply it right away?"
   - Exclude infrastructure, cybersecurity specialist content, academic papers without direct application, enterprise/B2B announcements without personal utility, fundraising/revenue news, and benchmark/model-comparison posts.

5. Select the final 5-10 items.
   - Rank by immediacy, reusability, and creator relevance.
   - Prefer diversity across `可复用方法`, `工作流优化`, `提示词技巧`, and `新工具`.
   - Avoid duplicate angles from the same topic unless one item is clearly stronger.

6. Write the report.
   - Use the exact structure in `references/report-template.md`.
   - Keep the title and commentary in Chinese.
   - Each item must include:
     - a practical title
     - source handle
     - item type
     - 2-3 actionable takeaways
     - "为什么有用"
     - the real tweet URL
   - Keep each item concise; target roughly 150-200 Chinese characters.

7. Save to the current board.
   - Write the finished markdown report to the resolved board target.
   - If the board is file-backed, report the path after saving.
   - If the board supports appending sections, insert under a clear date heading such as `AI 干货周报 - YYYY-MM-DD`.
   - Do not treat "posted in chat" as equivalent to "saved to board".

## Output Contract

- Write one board-ready markdown digest in Chinese.
- The report must include:
  - scan date
  - source coverage summary
  - 5-10 selected items or an explicit smaller count with reason
  - category distribution
  - real tweet URLs for every selected item
- The final save location must be explicit: board name, path, or section updated.
- If the board target could not be resolved, stop before the write step and ask for the destination instead of guessing.

## Red Flags

- Using a secondary article, screenshot, or recap link instead of the original post
- Including anything outside the last 7 days
- Filling the list with "interesting" news that is not immediately useful
- Skipping the 6 priority handles because they are harder to verify
- Claiming "65 scanned" without reconciling the explicit roster count
- Returning a polished report but never saving it to the current board

## Common Mistakes

| Mistake | Why it fails | Fix |
|---|---|---|
| Treating "hot" as "high-value" | Popular posts often fail the immediate-use bar | Re-score with the creator utility test |
| Trusting search snippets | Snippets can hide old posts, reposts, or wrong authors | Verify the original post URL and date before inclusion |
| Guessing the board target | The report lands in the wrong place or nowhere | Resolve board context first or ask once |
| Forcing 10 items | Padding dilutes the digest | Return fewer items if quality is low |
| Trusting the headline count over the roster | The agent invents or omits accounts | Use the explicit handle list as the authority |

## Verification

- [ ] Priority handles scanned first: `@zarazhangrui`, `@danshipper`, `@swyx`, `@karpathy`, `@rauchg`, `@amasad`
- [ ] Full roster coverage tracked from `references/source-roster.md` or the user's updated roster
- [ ] Any stated-count vs explicit-roster mismatch was noted instead of normalized away
- [ ] Every selected item is within the last 7 days
- [ ] Every selected item links to an original `x.com` or `twitter.com` status URL
- [ ] Every selected item passes the "content creator can use this immediately" test
- [ ] Output matches `references/report-template.md`
- [ ] The report was saved to the resolved current board
