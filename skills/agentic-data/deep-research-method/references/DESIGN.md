# DESIGN: deep-research-method

## Trigger description (SKILL.md description draft, <=1024 chars)
"Conduct verifiable deep research: source-quality scoring, citation discipline,
contradiction handling and retrieval-date recording. Use when an agent must answer a
factual question from the open web with auditable evidence; not for summarising a single
document."

## Procedure outline
1. Decompose the question into sub-questions answerable by one source each.
2. Score source quality BEFORE reading: authority (0-4) + recency (0-3) + corroboration
   (0-3) = 0-10; keep only >=6.
3. Fetch primary sources first (official docs, standards bodies, source repos); secondary
   sources confirm only. A secondary source used alone is a FAIL.
4. Record retrieval date + pinned version on every source. Stale facts (>1 year) are
   re-fetched for a current question.
5. Cite by paraphrase under 15 words; quote only when the phrasing IS the evidence.
6. Handle contradictions explicitly: list, weight by source quality, state resolution.
   Never majority-vote and never average two views.
7. State confidence: high (primary + >=2 corroborating), medium (primary only),
   low (secondary only), none (no source).

## Scripts planned
- `scripts/score_sources.py` — computes the 0-10 score from authority/recency/corroboration
  inputs; rejects <6 with a reason; emits a scored evidence table.

## Five eval scenarios (expanded in `references/EVALS.md`)
1. "My only source is a blog post from 2023. Can I cite it as high confidence?" -> No:
   secondary only = low confidence; fetch the primary.
2. "Two sources disagree on a date. Which do I use?" -> List the contradiction, weight by
   quality score, state the resolution; do not silently pick the majority.
3. "What must I record for every source?" -> URL, retrieval date, pinned version, score.
   A source without a retrieval date is memory, not evidence.
4. "A fact was verified in 2024 and the question is about 2026." -> Re-fetch; stale facts
   are not reusable without re-verification.
5. "I found one primary source. What confidence can I claim?" -> Medium (primary only).
   High requires >=2 corroborating sources.

## What this skill does better than a generic agent
A generic agent paraphrases a single page and calls it an answer. This skill forces
pre-reading quality scoring, mandatory retrieval dates, contradiction surfacing, and an
explicit confidence ladder. It prevents the common incident of reusing a 2024 fact for a
2026 question because "it was verified once".

## What existing public skills do (and what this one does differently)

Surveyed on 2026-10-12. The Fastio 2026 directory lists `Paper Search` and `Claude
Scientific Skills` (paper discovery + summary), and `skills.cat` carries research
helpers — but none of them enforce citation discipline, retrieval-date recording
or contradiction resolution. `anthropics/skills` ships no research-method skill.
A generic agent answers a factual question by paraphrasing one page it happened to
remember.

This skill is the only one that makes the evidence chain auditable:
- **Pre-read quality scoring**: authority (0-4) + recency (0-3) + corroboration
  (0-3) = 0-10; sources scoring below 6 are rejected *before* they are read.
- **Primary-first ordering**: a secondary source used alone is a FAIL, not a
  shortcut. Official docs, standards bodies and source repos first; secondary
  sources confirm only.
- **Retrieval date on every source**: a source without a URL + retrieval date +
  pinned version is memory, not evidence. Facts older than the question's window
  are re-fetched, not reused.
- **Contradiction resolution is a six-step procedure** (list / frame / weight by
  quality score / state the conflict / re-weight on new evidence / no-synthesis),
  with the "fake-middle" near-miss (two sources that agree on a wrong value)
  called out explicitly. Majority-vote and averaging are both forbidden.
- **Confidence ladder**: high (primary + >=2 corroborating), medium (primary
  only), low (secondary only), none (no source). The ladder is stated in the
  answer, not hidden.

Public sources surveyed (2026-10-12, all HTTP 200):
| Source | What it has | Gap this skill fills |
|--------|-------------|---------------------|
| `Paper Search` (Fastio listing) | finds papers | no citation discipline, no contradiction handling |
| `Claude Scientific Skills` | reads papers | no retrieval dates, no quality scoring |
| CRAAP test article (retrieved 2026-10-12) | a rubric | not an agent procedure; no scripts |
