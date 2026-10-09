---
name: deep-research-method
description: "Conduct verifiable deep research: source-quality scoring, citation discipline, contradiction handling and retrieval-date recording. Use when an agent must answer a factual question from the open web with auditable evidence; not for summarising a single document."
compatibility: Python 3.10+, curl; verified 2026-10-09
license: MIT
---
# Deep Research Method

Trigger: answering a factual question from the open web where the answer must
be auditable and the sources verifiable.

## Core invariant
Every claim in the answer traces to a scored, dated, primary-or-corroborated
source. A claim without a source is not an answer, it is an assertion. A source
without a retrieval date is not evidence, it is memory.

## Procedure (numbered — follow in order)
1. **Decompose the question** — split it into sub-questions answerable by a
   single source. A question that needs ten sources is ten questions.
2. **Score source quality before reading** — authority (domain, maintainer),
   recency (publication date vs the question's rate of change), corroboration
   (independent sources agreeing). Score 0-10; keep only >=6. Score before
   reading: a good-looking page can be wrong.
3. **Fetch primary sources first** — official docs, standards bodies, the
   source repository. Secondary summaries are for confirmation only. A
   secondary source used as the sole evidence is a FAIL.
4. **Record retrieval date on every source** — the URL, the date fetched, the
   version pinned. A source without a retrieval date is not evidence. Facts
   verified more than a year ago must be re-fetched for a current question.
5. **Cite by paraphrase under 15 words** — quote only when the phrasing is the
   evidence. Never copy long passages. Record the URL next to every claim.
6. **Handle contradictions explicitly** — list them, weight by source quality,
   state the resolution. Never silently pick the majority view and never average
   two views into a fake middle.
7. **State confidence** — high (primary + corroboration), medium (primary
   only), low (secondary only). Never claim high without corroboration.

## Decision tables
- **Quality score**: authority 0-4, recency 0-3, corroboration 0-3. >=6 keep.
- **Authority**: official body/standards org = 4; major vendor = 3; academic =
  3; established media = 2; blog/unknown = 0-1.
- **Recency**: <1 year for fast-changing = 3; 1-3 years = 2; 3-5 years = 1;
  >5 years = 0 unless the fact is stable.
- **Corroboration**: 3+ independent = 3; 2 = 2; 1 = 1; none = 0.
- **Confidence**: high = primary + >=2 corroborating; medium = primary only;
  low = secondary only; none = no source.

## Near-miss triggers (stop and re-check before proceeding)
- A source with no retrieval date -> not evidence, re-fetch and record.
- A secondary source used as the sole evidence -> fetch the primary.
- A contradiction resolved by majority vote -> re-weight by quality.
- A fact stated without a source -> mark it as unverified.
- A 2024 fact used for a 2026 question without re-checking -> re-fetch.
- A kept source with score <6 -> it was never scored.

## Pitfalls from research
- P1: Source quality is judged before reading; a good-looking page can be wrong.
- P2: Retrieval dates are mandatory; memory is not evidence.
- P3: Contradictions must be surfaced, not averaged away.
- P4: Secondary sources masquerading as primary are the common failure.
- P5: Stale facts are reused because they were once verified.
- P6: A source that scores 5 is not "close enough" — it is discarded, unless it
  is the only source for a sub-question, in which case it is flagged low.

## Verification checklist
- [ ] Question decomposed into sub-questions.
- [ ] Every source scored 0-10 before use; only >=6 kept.
- [ ] Every source has URL + retrieval date + pinned version.
- [ ] Every claim cites a source; no unsourced claims.
- [ ] Contradictions listed and resolved by quality weight.
- [ ] Confidence stated (high/medium/low) with the reason.
- [ ] Quotations under 15 words.

## References
- procedures: references/procedures.md
- scoring: references/source-scoring.md
- EVALS: references/EVALS.md
- SOURCES: references/SOURCES.md
- scripts: scripts/score_sources.py
