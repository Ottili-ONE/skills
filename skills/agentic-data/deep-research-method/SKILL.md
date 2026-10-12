---
name: deep-research-method
description: "Conduct verifiable deep research: source-quality scoring, citation discipline, contradiction handling and retrieval-date recording. Use when an agent must answer a factual question from the open web with auditable evidence; not for summarising a single document. Verified 2026-10-12."
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
   two views into a fake middle. The full four-step procedure, the re-weighting
   rule and the worked example are in `references/contradiction-handling.md`.
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
- **Contradiction resolution** (full procedure in `references/contradiction-handling.md`):
  | step | action | failure if skipped |
  |---|---|---|
  | list | quote each claim, its score and its retrieval date | resolved by whoever speaks last |
  | frame | same outcome/population/definition? many "contradictions" are orthogonal | comparing unlike things |
  | weight | higher quality wins; equal scores -> prefer the more recent | count beats quality, the wrong prior |
  | state | name the winner, keep the loser as a named disagreement, give the range | the reader cannot see the disagreement |
  | re-weight | if the primary is stale or a third source supports the minority, recompute and say so | a silent flip is unauditable |
  | no synthesis | never average into a middle value; if evidence is insufficient, downgrade confidence | fake precision |

## Near-miss triggers (stop and re-check before proceeding)
- A source with no retrieval date -> not evidence, re-fetch and record.
- A secondary source used as the sole evidence -> fetch the primary.
- A contradiction resolved by majority vote -> re-weight by quality.
- A fact stated without a source -> mark it as unverified.
- Two sources disagree and the answer averages the numbers -> fake precision;
  list, weight, state the range (see `references/contradiction-handling.md`).
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
- P7: Averaging two sources into a middle value produces a number no source
  claimed; it reads as precision and carries no evidence. List, weight, state the
  range — or downgrade confidence instead of synthesising.

## Verification checklist
- [ ] Question decomposed into sub-questions.
- [ ] Every source scored 0-10 before use; only >=6 kept.
- [ ] Every source has URL + retrieval date + pinned version.
- [ ] Every claim cites a source; no unsourced claims.
- [ ] Contradictions listed and resolved by quality weight.
- [ ] Confidence stated (high/medium/low) with the reason.
- [ ] Quotations under 15 words.

## Worked examples

### Good — contradiction resolved by quality weight
Source A (university preprint, score 8) says "the effect is +0.4".
Source B (industry report, score 6) says "the effect is +0.1".
Both are recent and on-topic.

1. Score both: A=8, B=6.
2. Record the contradiction in the claims file.
3. Resolve by weight: cite A as primary, note B as a lower-weight
   disagreement, and state the range (+0.1 to +0.4) in the summary.

Result: the reader sees the disagreement and the reason for the choice.

### Bad — unsourced claim dressed as a finding
"The model is 3x faster than the baseline." No URL, no retrieval date,
no version.

Why it fails: the claim cannot be verified or re-checked. The rule is
URL + retrieval date + pinned version for every claim; a claim without
a source is a confidence of `low` and must be flagged, not asserted.

### Bad — quoting 22 words to "prove" a point
`"the results show a statistically significant improvement in latency,
throughput, and accuracy across all benchmarks"`.

Why it fails: long quotations are paraphrase bait and easy to misquote.
Keep quotations under 15 words; anything longer is a summary with a
citation, not a quote.
## References
- procedures: references/procedures.md
- scoring: references/source-scoring.md
- contradiction handling: references/contradiction-handling.md
- EVALS: references/EVALS.md
- SOURCES: references/SOURCES.md
- scripts: scripts/score_sources.py (score, audit, contradictions, cite, fetch)
- citation and fetch: references/cite-fetch.md
