# Procedures — deep-research-method

Verified 2026-10-09. Version-sensitive: laws, API versions and vendor behaviour
change; re-fetch and re-score before answering questions whose answer changes
with time.

## 0. The core invariant
Every claim in the answer traces to a scored, dated, primary-or-corroborated
source. A claim without a source is not an answer, it is an assertion.

## 1. Decompose
Split the question into sub-questions answerable by a single source. Example:
"What is the retention period for GDPR erasure requests?" decomposes into
(a) the legal text, (b) the supervisory authority guidance, (c) any case law.
Each sub-question gets its own source list.

## 2. Score before reading
Score each candidate on authority (0-4), recency (0-3), corroboration (0-3).
Keep only >=6. A blog post that looks authoritative scores 0-1 on authority and
is discarded before it is read.

| Authority | Score | Example |
|-----------|-------|---------|
| Official body / standards org | 4 | ISO, W3C, IETF, EU institutions |
| Major vendor | 3 | OpenAI docs, AWS docs |
| Academic (peer-reviewed) | 3 | arXiv paper with 50+ citations |
| Established media | 2 | Reuters, BBC, FT |
| Blog / unknown | 0-1 | personal blog, Medium |

Recency: <1 year = 3 (fast-changing), 1-3 = 2, 3-5 = 1, >5 = 0 unless stable.

## 3. Fetch primary first
Official docs, standards bodies, the source repository. Secondary summaries
(confirming blogs, news articles) are corroboration only. A secondary source
used as the sole evidence is a FAIL.

## 4. Record retrieval date
Every source gets: URL, retrieval date (ISO), pinned version, and the score.
`scripts/score_sources.py` enforces this on the source list.

## 5. Cite by short paraphrase
Quote under 15 words; paraphrase the rest. Never copy long passages. Record
the URL next to every claim.

## 6. Contradictions
1. List every contradiction with its sources and scores.
2. Weight by quality, not by count.
3. State the resolution and the confidence. If unresolved, say so.

Never average two views into a fake middle. If the primary source says X and a
lower-quality source says Y, the answer is X, with Y noted as a minority view.

## 7. Confidence
- High: primary source + >=2 independent corroborating sources.
- Medium: primary source only.
- Low: secondary source only.
- None: no source.

Never claim high without corroboration.

## Worked examples

Good — sourced claim:
> "The GDPR erasure request must be answered 'without undue delay' and within
> one month (Art. 12(3) GDPR, retrieved 2026-10-09)."

Bad — unsourced claim:
> "The erasure request must be answered within one month."

Good — contradiction handled:
> "The primary source (CNIL guidance, score 9) says erasure requests are
> answered within one month. A secondary blog (score 4) claims two months; this
> is rejected on quality. Confidence: high."

Bad — contradiction averaged:
> "Sources disagree on whether it is one or two months."
