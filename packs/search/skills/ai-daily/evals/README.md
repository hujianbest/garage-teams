# AI Daily Evals

These evals protect the behavior contract for `ai-daily`.

## What this skill must not regress on

- It must not guess what "current board" means.
- It must not substitute secondary summaries for original tweet URLs.
- It must not confuse "hot" posts with immediately usable creator value.
- It must not hide source-roster count mismatches by inventing missing accounts.

## Baseline failures observed before the skill existed

- The agent was tempted to treat the report as a fast AI-news roundup instead of a practical creator digest.
- The agent identified "real tweet links" and "last 7 days" as high-risk requirements under time pressure.
- The agent treated "save to current board" as ambiguous and likely to be skipped or guessed.
- The agent preferred heuristic shortcuts and lighter verification unless explicitly constrained.

## Minimum passing bar

1. Ask or resolve the board target before writing.
2. Require original `x.com` or `twitter.com` status URLs for all selected items.
3. Keep the selection bar centered on immediate usefulness for content creators.
4. Trust the explicit roster over the headline count when they disagree.
