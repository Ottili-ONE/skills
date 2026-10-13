# Procedures — deep-research-method

Verified 2026-10-13. Version-sensitive: laws, API versions and vendor behaviour
change over time, so re-fetch and re-score before answering a question whose
answer depends on the current state of the world.

## 0. The grounding rule
Every statement in the final answer must point at a source that was scored and
dated at retrieval time. A sentence with no source behind it is an assertion, not
an answer — mark it as such and say so.

## 1. Decompose the question
Split the question into sub-questions, each answerable from a single source or a
small set. Example: "What is the retention period for GDPR erasure requests?"
decomposes into (a) the legal text, (b) the supervisory authority's guidance,
(c) any case law. Each sub-question gets its own source list and its own
retrieval record.

## 2. Score candidates before reading them
Score each candidate on authority (0-4), recency (0-3) and corroboration (0-3).
Discard anything scoring below 6 *before* opening it. A blog post that looks
authoritative scores 0-1 on authority and is discarded before it is read, which
keeps the reading list short and the answer clean.

| Authority | Score | Example |
|-----------|-------|---------|
| Official body / standards organisation | 4 | ISO, W3C, IETF, EU institutions |
| Major vendor | 3 | OpenAI docs, AWS docs |
| Academic (peer-reviewed) | 3 | arXiv paper with 50+ citations |
| Established media | 2 | Reuters, BBC, FT |
| Blog / unknown | 0-1 | personal blog, Medium |

Recency: <1 year = 3 (fast-changing topic), 1-3 years = 2, 3-5 years = 1,
>5 years = 0 unless the fact is stable (e.g. a statutory provision).

## 3. Fetch primary sources first
Pull from official docs, standards bodies and the source repository. Secondary
summaries (confirming blogs, news articles) are corroboration only — they may
confirm a primary, never stand in for one. Relying on a secondary source as the
sole evidence for a claim is a FAIL and the claim must be downgraded.

## 4. Record the retrieval date on every source
Each source records its URL, retrieval date (ISO 8601), pinned version, and the
score it received. A source without a retrieval date is not evidence. Facts
verified more than a year ago must be re-fetched for a current question.
`scripts/score_sources.py` enforces this on the source list and refuses to score
a row that is missing a date.

## 5. Cite by short paraphrase
Quote under 15 words; paraphrase the rest. Never copy long passages. Place the
URL next to every claim so the reader can trace it. The 15-word limit is not a
style preference — longer quotes are the author's voice, not the source's, and
they erode the distinction between reporting and reproducing.

## 6. Contradictions
Full procedure in `references/contradiction-handling.md`. The short form:
1. List every contradiction with its sources and scores.
2. Weight by quality, not by count.
3. State the resolution and the confidence. If unresolved, say so.

Never average two views into a fake middle. If the primary source says X and a
lower-quality source says Y, the answer is X, with Y recorded as a minority view
and the reason for rejecting it.

## 7. Confidence levels
- High: primary source plus at least two independent corroborating sources.
- Medium: primary source only.
- Low: secondary source only.
- None: no source at all.

Never claim high without corroboration, and never inflate a level to make the
answer feel solid.

## Worked examples

Good — sourced claim:
> "The GDPR erasure request must be answered 'without undue delay' and within
> one month (Art. 12(3) GDPR, retrieved 2026-10-13)."

Bad — unsourced claim:
> "The erasure request must be answered within one month."

Good — contradiction handled:
> "The primary source (CNIL guidance, score 9) says erasure requests are
> answered within one month. A secondary blog (score 4) claims two months; this
> is rejected on quality. Confidence: high."

Bad — contradiction averaged:
> "Sources disagree on whether it is one or two months."
