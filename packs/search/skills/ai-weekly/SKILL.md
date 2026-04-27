---
name: ai-weekly
description: Use when the user wants a practical weekly AI roundup from recent X/Twitter posts, especially from a fixed source roster, with a 7-day window, real tweet links, and a Chinese markdown report layered as Priority 1 必看 / Priority 2 值得抄方法 / Priority 3 值得建立认知, optionally with candidate supplements. Not for generic AI news, benchmark recaps, infrastructure updates, funding coverage, or paper-only summaries.
---

# AI Weekly

Build a Chinese-first weekly digest from recent X/Twitter posts that a content creator can use immediately. This skill is for practical weekly curation with a three-tier priority stack plus optional candidate supplements, not for hype roundups or deep research essays.

## When to Use

Use this skill when:
- the user wants a weekly or past-7-day AI roundup from X/Twitter
- the user provides a fixed source roster or named accounts to scan
- the user cares about tools, workflows, tutorials, prompts, methods, or creator productivity
- the output must be a concise Chinese markdown report with links and explicit practical value
- the user wants the final report grouped by `Priority 1：必看 / Priority 2：值得抄方法 / Priority 3：值得建立认知`
- the user wants each priority layer to include a `候选补充` subsection so the report shows near-miss items too

Do not use this skill when:
- the request is for generic AI news, model launch recaps, or industry headlines
- the user wants a deep research report, competitive analysis, or long-form article
- the source is not X/Twitter posts
- the user mainly wants infrastructure, benchmark, funding, cybersecurity, or enterprise-only announcements

## Hard Gates

- Do not guess the meaning of "current board". Resolve the target from session context, the current board artifact, or an explicit file path first. If the board target is not uniquely identifiable, ask once before writing.
- Do not use screenshots, aggregators, newsletters, or secondary summaries as substitutes for the original post. Every selected item must link to the original `x.com/.../status/...` or `twitter.com/.../status/...` URL.
- Do not pad the report. If fewer than 5 items pass the usefulness bar, return fewer and explain why.
- Do not silently invent missing accounts. If the stated total and the explicit handle list disagree, treat the explicit roster as authoritative and note the discrepancy in the scan stats.
- Do not let "popular" replace "practical". Every item must pass the creator test: "Can the reader apply this immediately to improve work?"
- Do not flatten the final output. When the user provides `Priority 1 / 2 / 3`, the report must be grouped by those priority sections instead of one flat list.
- Do not omit `候选补充` when the user explicitly asks for a second layer of items under each priority.

## Quick Reference

| Step | Non-negotiable rule |
|---|---|
| Source scan | Scan all handles in the provided roster; scan the 6 priority accounts first |
| Search batching | Batch 10-15 handles per search pass after the priority batch |
| Time window | Restrict to the last 7 days |
| Search focus | `tool`, `workflow`, `method`, `tutorial`, `prompt`, `tip`, `guide`, `framework` |
| Inclusion bar | Practical, reusable, creator-relevant |
| Exclusions | Infra, security, benchmarks, funding, paper-only, enterprise-only |
| Classification | Assign every primary item to exactly one of `Priority 1：必看 / Priority 2：值得抄方法 / Priority 3：值得建立认知` |
| Candidate layer | Keep a short secondary pool for `候选补充` under each priority when requested |
| Output | Chinese markdown weekly report with real tweet URLs, `为什么有用`, priority layering, and candidate supplements |
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
   - `Priority 1: 必看` — immediately usable, highest-leverage items that a creator should act on this week.
   - `Priority 2: 值得抄方法` — reusable workflows, structures, and methodologies worth adapting into the creator's own system.
   - `Priority 3: 值得建立认知` — mindset shifts, recurring mistakes, or expert perspectives that improve long-term judgment.
   - Exclude anything that fails the test: "After reading this, can a content creator apply it right away?"
   - Exclude infrastructure, cybersecurity specialist content, academic papers without direct application, enterprise/B2B announcements without personal utility, fundraising/revenue news, and benchmark/model-comparison posts.

5. Select and classify the final 5-10 primary items.
   - Rank by immediacy, reusability, and creator relevance.
   - Prefer diversity across `可复用方法`, `工作流优化`, `提示词技巧`, and `新工具`.
   - Assign each primary item to exactly one priority section.
   - If an item could fit multiple priorities, place it in the highest applicable priority.
   - Keep a secondary near-miss pool for each priority. These become `候选补充` rather than primary items.

6. Write the report.
   - Use the exact structure in `references/report-template.md`.
   - Keep the title and commentary in Chinese.
   - Group the output under `Priority 1｜必看`, `Priority 2｜值得抄方法`, and `Priority 3｜值得建立认知`.
   - Each item must include:
     - a practical title
     - source handle
     - item type
     - 2-3 actionable takeaways
     - `为什么有用`
     - the real tweet URL
   - Keep each item concise; target roughly 150-200 Chinese characters.
   - If a priority section has no qualifying items, keep the heading and write `本周无符合条件内容。`
   - When the user asks for deeper layering, add `#### 候选补充` under each priority with 1-3 short bullets.
   - Each candidate bullet should include: handle, one-line reason it is worth opening, and the real original tweet URL.
   - Do not count candidate supplements as primary selected items in the main total.

7. Save to the current board.
   - Write the finished markdown report to the resolved board target.
   - If the board is file-backed, report the path after saving.
   - If the board supports appending sections, insert under a clear date heading such as `AI 周报 - YYYY-MM-DD`.
   - Do not treat "posted in chat" as equivalent to "saved to board".

## Output Contract

- Write one board-ready markdown weekly digest in Chinese.
- The report must include:
  - scan date
  - source coverage summary
  - 5-10 primary selected items or an explicit smaller count with reason
  - `Priority 1：必看 / Priority 2：值得抄方法 / Priority 3：值得建立认知` layered sections
  - `候选补充` under each priority when requested
  - priority distribution for the primary items
  - candidate supplement count when candidate sections are present
  - category distribution
  - real tweet URLs for every selected item
- The final save location must be explicit: board name, path, or section updated.
- If the user asked for priorities, the output must not collapse those sections into a flat list.
- If the user asked for candidate supplements, the output must not stop at the primary list.
- If the board target could not be resolved, stop before the write step and ask for the destination instead of guessing.

## Red Flags

- Using a secondary article, screenshot, or recap link instead of the original post
- Including anything outside the last 7 days
- Filling the list with "interesting" news that is not immediately useful
- Skipping the 6 priority handles because they are harder to verify
- Claiming "65 scanned" without reconciling the explicit roster count
- Returning a polished report but flattening the priority structure
- Returning a polished report with new priority labels but no `候选补充`
- Returning a polished report but never saving it to the current board

## Common Mistakes

| Mistake | Why it fails | Fix |
|---|---|---|
| Treating "hot" as "high-value" | Popular posts often fail the immediate-use bar | Re-score with the creator utility test |
| Trusting search snippets | Snippets can hide old posts, reposts, or wrong authors | Verify the original post URL and date before inclusion |
| Guessing the board target | The report lands in the wrong place or nowhere | Resolve board context first or ask once |
| Forcing 10 items | Padding dilutes the digest | Return fewer items if quality is low |
| Flattening the priorities into one list | The report ignores the user's requested structure | Keep explicit layered headings and classify every primary item |
| Keeping the old priority names | The report feels half-updated and inconsistent | Use `必看 / 值得抄方法 / 值得建立认知` everywhere |
| Omitting `候选补充` | The report still looks too thin for a full week | Add short near-miss bullets under each priority |
| Trusting the headline count over the roster | The agent invents or omits accounts | Use the explicit handle list as the authority |

## Verification

- [ ] Priority handles scanned first: `@zarazhangrui`, `@danshipper`, `@swyx`, `@karpathy`, `@rauchg`, `@amasad`
- [ ] Full roster coverage tracked from `references/source-roster.md` or the user's updated roster
- [ ] Any stated-count vs explicit-roster mismatch was noted instead of normalized away
- [ ] Every selected item is within the last 7 days
- [ ] Every selected item links to an original `x.com` or `twitter.com` status URL
- [ ] Every selected item passes the creator "immediately usable" test
- [ ] Every primary item is assigned to exactly one of `Priority 1：必看 / Priority 2：值得抄方法 / Priority 3：值得建立认知`
- [ ] `候选补充` sections are present under each priority when requested
- [ ] Output matches `references/report-template.md`
- [ ] The report was saved to the resolved current board
