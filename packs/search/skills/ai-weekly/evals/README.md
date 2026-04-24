# AI Weekly Evals

These evals protect the behavior contract for `ai-weekly`.

## What this skill must not regress on

- It must not guess what "current board" means.
- It must not substitute secondary summaries for original tweet URLs.
- It must not confuse "hot" posts with immediately usable creator value.
- It must not hide source-roster count mismatches by inventing missing accounts.
- It must not flatten `Priority 1 / 2 / 3` into one flat list when the user asks for layered output.
- It must not keep the old daily identity after the skill has been renamed to `ai-weekly`.

## Baseline failures observed before the skill existed

- The agent was tempted to treat the report as a fast AI-news roundup instead of a practical creator digest.
- The agent identified "real tweet links" and "last 7 days" as high-risk requirements under time pressure.
- The agent treated "save to current board" as ambiguous and likely to be skipped or guessed.
- The agent preferred heuristic shortcuts and lighter verification unless explicitly constrained.
- The agent was likely to preserve the old daily naming even though the behavior had already drifted to a weekly roundup.
- The agent was likely to use `Priority 1 / 2 / 3` only as an internal rubric, while still outputting one flat ranked list.

## Minimum passing bar

1. Ask or resolve the board target before writing.
2. Require original `x.com` or `twitter.com` status URLs for all selected items.
3. Keep the selection bar centered on immediate usefulness for content creators.
4. Trust the explicit roster over the headline count when they disagree.
5. Keep the final report grouped by `Priority 1 / Priority 2 / Priority 3`.
6. Keep the skill name and wording consistent with `ai-weekly`.
