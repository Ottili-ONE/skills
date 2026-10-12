# Staleness check — deep-research-method

A source that scores well but was retrieved years ago is not evidence for a
current question. The staleness check makes the re-fetch step explicit instead
of leaving it to memory.

## The check
```
python3 scripts/score_sources.py staleness <sources.jsonl> --question-date 2026-10-12
```
Exit 0 = every source is within the age window. Exit 1 = one or more sources are
stale, each listed with its retrieval date and age in days.

`--max-age-days` (default 365) sets the window. Fast-changing facts (laws, API
versions, vendor behaviour) use a shorter window; stable facts (mathematics,
historical dates) may use a longer one, but the choice must be recorded.

## Why the question date is explicit
"Today" is not a fact the script can know, and a script that guessed would
silently pass stale sources. The researcher supplies the date the question is
about, which is the date that matters: a fact verified in 2024 is evidence for a
2024 question and stale for a 2026 one.

## Staleness vs score
A stale source is **not** discarded by the score. The score decides whether the
source is usable *in principle*; staleness decides whether it is usable *now*.
A source that is both high-scoring and stale must be re-fetched, and the
re-fetched version re-scored. If the re-fetched version scores below the
minimum, the sub-question has no kept source and confidence drops to low.

## Procedure
1. Score all candidates (authority + recency + corroboration, >=6 kept).
2. Run the staleness check against the question date.
3. For each stale source: re-fetch it, re-score it, update the retrieval date.
4. Re-run the staleness check. It must pass before the answer is written.
5. Record the original retrieval date and the re-fetch date in the evidence
   chain, so the reader can see that the fact was re-verified.

## Near-miss triggers
- A source retrieved in 2024 used for a 2026 question with no re-fetch -> stale.
- The staleness check skipped because "the score was high enough" -> the score
  says nothing about whether the fact is current.
- A fixed 365-day window applied to a fast-changing fact -> too loose; use a
  shorter window and record why.
- The question date omitted so the script uses the system clock -> the script
  cannot know the question date; supply it explicitly.
- A re-fetched source whose score drops below 6 silently dropped from the
  citations -> the sub-question now has no kept source; say so and downgrade
  confidence.
