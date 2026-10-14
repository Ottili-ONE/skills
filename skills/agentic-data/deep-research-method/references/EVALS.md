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

## E4 — record retrieval dates and re-fetch stale facts
Prompt: "I verified this fact last year. Is that good enough?"
Expected: No. Record the retrieval date on every source. A fact verified in
2025 used for a 2026 question must be re-fetched, because the answer may have
changed. `scripts/score_sources.py score` rejects any source without an ISO
retrieval date. Run `scripts/score_sources.py staleness <sources.jsonl>
--question-date <date> --max-age-days <n>`; it flags a source whose retrieval
date is older than the window with its age in days and exits 1. Re-fetch, re-score,
update the retrieved date, and re-run until it passes. Keep the original
retrieval date in the evidence chain alongside the re-fetch date. If the source
is unreachable, say so and downgrade confidence rather than citing a stale
snapshot.
Failure signs: a source with no `retrieved` field; a 2024 fact reused without
re-checking; a 2025 retrieval date on a 2026 answer with no re-fetch attempt;
the staleness check skipped because the score was high; the question date
omitted so the script uses the system clock.

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

## E7 — reject a source that scores below the threshold
Prompt: "A source scores 5. Keep it."
Expected: No. The threshold is >=6; a 5 is discarded before it is read, unless it
is the *only* source for a sub-question, in which case it is kept, flagged
low-confidence, and the lack of corroboration is stated in the answer.
`scripts/score_sources.py score` exits 1 with `FAIL: source N score 5 < 6`.
Failure signs: a kept source with score <6 and no low-confidence flag.


## E8 — cite by short paraphrase, never a long quotation
Prompt: "Prove your claim about the MCP 12-month deprecation window by quoting
the changelog."
Expected: Cite by paraphrase under 15 words with the URL next to the claim. Quote
only when the phrasing *is* the evidence (a threshold, a version number, a
verbatim rule). Never copy a long passage to "prove" a point — a 22-word block
is a summary with a citation, not a quote. Record URL + retrieval date + pinned
version for every claim.
Failure signs: a 20+ word quotation presented as evidence; a claim with a URL but
no retrieval date; paraphrase with no URL.

## E9 — score a source before reading it
Prompt: "I found a promising URL. Read it."
Expected: Score it first with `scripts/score_sources.py score`. A source that
scores below 6 is discarded before it is read, unless it is the only source for a
sub-question (then keep, flag low confidence, state the lack of corroboration).
Never read a low-scoring source and then decide whether to use it — the score
is the gate.
Failure signs: reading the source before scoring; a low-scoring source used as
the main evidence with no low-confidence flag.

## E10 — reject a stale source for a current question
Prompt: "I verified this fact in 2024. The question is about 2026."
Expected: Re-fetch it. Run
`scripts/score_sources.py staleness <sources.jsonl> --question-date 2026-10-12`;
it flags the source as stale with its age in days. Re-fetch, re-score, update the
retrieved date, and re-run the check until it passes. Record the original and the
re-fetch date in the evidence chain. A stale source is not discarded by score --
it is flagged so it is re-fetched.
Failure signs: a 2024 source used for a 2026 question with no re-fetch; the
staleness check skipped because the score was high; the question date omitted so
the script uses the system clock.

## E11 — count corroboration by upstream, not by URL
Prompt: "I have three sources: the primary spec, a blog summarising it, and a
news article that also quotes the spec. Is that three independent sources?"
Expected: No. The blog and the news article share the spec as their upstream, so
there is one independent upstream, not three. Corroboration is counted from
distinct upstreams. Run
`scripts/score_sources.py corroboration <sources.jsonl>`; it exits 1 with
`FAIL: N kept URLs share upstream '<url>'` when two kept URLs trace to the same
upstream. Mark the shared-upstream rows with an `upstream` field pointing at the
primary they were derived from.
Failure signs: corroboration counted as 3 when the URLs share an upstream; the
`corroboration` subcommand not run at all; no `upstream` field recorded.

## E12 — every kept source must carry provenance
Prompt: "I kept a source. What must be recorded with it?"
Expected: URL + retrieval date + pinned version, all three. A source without a
retrieval date is memory, not evidence; a source without a pinned version
cannot be re-verified. Run
`scripts/score_sources.py provenance <sources.jsonl>`; it exits 0 with
`PASS: all N kept sources carry URL + retrieval date + version` and exits 1 with
a per-source failure naming the missing field.
Failure signs: a kept source with no `retrieved` or no `version`; the
provenance check skipped because the score was high.

## E13 — detect the fake middle
Prompt: "Two sources give the same exact number. Are they independent?"
Expected: Check whether they share an upstream. If both derive from the same
primary, they are one source and the agreement is an artefact of copying, not
corroboration. This is the "fake middle" failure: two sources that agree on a
wrong value look better than one source that is right. Trace each to its
upstream before counting it.
Failure signs: two URLs with different domains agreeing exactly on a numeric
value and neither linking the primary; corroboration counted as 2.

## E14 — recover from a real incident
Prompt: "A previous answer cited a 2024 page for a 2026 question and the fact
was wrong. How do I prevent this next time?"
Expected: Follow the incident in `references/incidents.md` (I1): every source's
retrieval date is checked against the question date with
`scripts/score_sources.py staleness <sources.jsonl> --question-date 2026-10-12`.
A source older than the window is flagged and re-fetched before it is cited, and
the original retrieval date is kept in the evidence chain alongside the
re-fetch date. The other five incidents (secondary-as-primary, fake middle,
swept contradiction, confidence without evidence, quotation that changes
meaning) each have a named observable signature and recovery procedure.
Failure signs: the staleness check skipped; a stale source cited without a
re-fetch attempt; an incident signature matched and ignored.


## E15 — compute confidence from upstreams, not from URL count
Prompt: "I have three kept sources for a claim. What confidence can I claim?"
Expected: It depends on how many *distinct upstreams* they trace to.
`scripts/score_sources.py confidence <sources.jsonl>` groups the kept sources
by `upstream` (falling back to `url`) and reads the ladder: >=2 upstreams =
high, 1 = medium, none kept = low. Three URLs that all trace to one upstream
score medium, not high -- that is the fake middle. The command emits
`{"n_kept": 3, "n_upstreams": 1, "confidence": "medium", ...}`.
Failure signs: confidence being read off the URL count; the upstream grouping
being skipped.

## E16 — the confidence subcommand rejects an empty kept set
Prompt: "I ran `confidence` on a file where every source scored below 6."
Expected: Reject. `scripts/score_sources.py confidence bad.jsonl` exits 1 with
`FAIL: no kept sources to compute confidence from`, because a claim with no
kept source cannot be assigned any confidence above low. Re-score the sources
or fetch a primary before claiming anything.
Failure signs: confidence being reported as `none` with exit 0; the empty case
not checked.
