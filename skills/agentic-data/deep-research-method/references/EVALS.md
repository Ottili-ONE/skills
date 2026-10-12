# EVALS — deep-research-method

Each eval is a realistic prompt an agent might receive, the expected behaviour
per this skill, and failure signs to look for.

## E1 — research a factual question with scored sources
Prompt: "What is the retention period for GDPR erasure requests?"
Expected: decompose into sub-questions, score every candidate source 0-10
(authority/recency/corroboration) before reading, keep only >=6, fetch the
primary legal text first, record retrieval date on every source, cite by short
paraphrase, state confidence. Acceptance: every claim has a URL + retrieval
date; confidence is high only with >=2 corroborating sources.
Failure signs: a claim with no source; a secondary source used as the sole
evidence; no retrieval date; confidence high with one source.

## E2 — reject a low-quality source
Prompt: "A blog says the GDPR retention period is 5 years. Use it."
Expected: Score the blog: authority 0-1, recency 1, corroboration 0 -> total
<=2, below the 6 threshold -> discard. Fetch the primary legal text instead.
If it is the only source for a sub-question, keep it but flag the answer
low-confidence and state the lack of corroboration.
Failure signs: a blog used as the main evidence; no score recorded.

## E3 — handle a contradiction
Prompt: "One source says one month, another says two months."
Expected: List the contradiction with both sources and their scores. Weight by
quality, not count. If the primary source (score 9) says one month and a
secondary blog (score 4) says two months, the answer is one month with the
minority view noted. Never average into a fake middle.
Failure signs: "sources disagree" with no resolution; the lower-quality view
winning.

## E4 — record retrieval dates
Prompt: "I verified this fact last year. Is that good enough?"
Expected: No. Record the retrieval date on every source. A fact verified in
2025 used for a 2026 question must be re-fetched, because the answer may have
changed. `scripts/score_sources.py score` rejects any source without an ISO
retrieval date.
Failure signs: a source with no `retrieved` field; a 2024 fact reused without
re-checking.

## E5 — audit the claim-to-source coverage
Prompt: "Make sure every claim in my answer cites a kept source."
Expected: Write the claims as JSON with `cites` lists and run
`scripts/score_sources.py audit sources.jsonl claims.json`. Exit 0 means every
claim cites a source that scored >=6. Exit 1 with `cites no source` or `not
kept` means the answer is not auditable — fix it before shipping.
Failure signs: audit exit 1; claims with empty `cites`.

## E6 — state confidence honestly
Prompt: "Give me a confident answer."
Expected: Confidence is high only with a primary source + >=2 corroborating
sources. Medium = primary only. Low = secondary only. Never claim high without
corroboration. State the reason for the level next to the answer.
Failure signs: "high confidence" with a single secondary source; no confidence
stated at all.

## E7 — record retrieval dates and re-fetch stale facts
Prompt: "I have a source retrieved in 2025. Can I reuse it for a 2026 answer?"
Expected: No. Re-fetch the source and record the new retrieval date. Version-sensitive
facts (laws, API revisions, security advisories) change; a 2025 retrieval date on a
2026 answer is itself a failure signal. `scripts/score_sources.py score` rejects any
source without an ISO `retrieved` date. If the source is unreachable, say so and
downgrade confidence rather than citing a stale snapshot.
Failure signs: a 2025 retrieval date on a 2026 answer with no re-fetch attempt;
a source with no `retrieved` field.

## E8 — reject a source that scores below the threshold
Prompt: "A source scores 5. Keep it."
Expected: No. The threshold is >=6; a 5 is discarded before it is read, unless it
is the *only* source for a sub-question, in which case it is kept, flagged
low-confidence, and the lack of corroboration is stated in the answer.
`scripts/score_sources.py score` exits 1 with `FAIL: source N score 5 < 6`.
Failure signs: a kept source with score <6 and no low-confidence flag.


## E9 — cite by short paraphrase, never a long quotation
Prompt: "Prove your claim about the MCP 12-month deprecation window by quoting
the changelog."
Expected: Cite by paraphrase under 15 words with the URL next to the claim. Quote
only when the phrasing *is* the evidence (a threshold, a version number, a
verbatim rule). Never copy a long passage to "prove" a point — a 22-word block
is a summary with a citation, not a quote. Record URL + retrieval date + pinned
version for every claim.
Failure signs: a 20+ word quotation presented as evidence; a claim with a URL but
no retrieval date; paraphrase with no URL.

## E10 — score a source before reading it
Prompt: "I found a promising URL. Read it."
Expected: Score it first with `scripts/score_sources.py score`. A source that
scores below 6 is discarded before it is read, unless it is the only source for a
sub-question (then keep, flag low confidence, state the lack of corroboration).
Never read a low-scoring source and then decide whether to use it — the score
is the gate.
Failure signs: reading the source before scoring; a low-scoring source used as
the main evidence with no low-confidence flag.
