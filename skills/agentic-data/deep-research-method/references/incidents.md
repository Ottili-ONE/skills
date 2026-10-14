# Incidents — deep-research-method

Real research failures, the observable signature that exposes them, and the
exact recovery procedure. Each incident is a case a generic agent gets wrong
because it trusts memory or a single page.

## I1 — The 2024 fact reused for a 2026 question

- **What happened**: an agent answered "what is the context window of model X"
  from a page it read in 2024. The vendor doubled the window in 2025. The
  answer was wrong and every citation pointed at the stale page.
- **Observable signature**: every source's `retrieved` date is >1 year before
  the current date, or the answer quotes a version string that is not the
  current one.
- **Recovery**: re-fetch every source whose fact is version-sensitive; pin the
  verified version in the answer; mark the old source `stale` in the evidence
  table rather than dropping it silently.
- **Prevention**: the staleness rule — a fact older than the question's
  relevant period is re-fetched before it is cited. See `references/staleness.md`.

## I2 — Secondary source used as primary

- **What happened**: a blog post summarising a spec was cited as the
  authoritative answer. The blog had the wrong default value. The actual spec
  corrected it.
- **Observable signature**: the highest-quality source in the evidence table
  is a domain that is not the standards body, the vendor repo, or the official
  docs.
- **Recovery**: fetch the primary; re-score; re-derive the answer. A secondary
  source that turns out to be right is still recorded as secondary with the
  primary listed alongside.
- **Prevention**: primary-first ordering. A secondary source used alone is a
  FAIL, not a shortcut.

## I3 — The fake middle (two sources agree on the wrong value)

- **What happened**: two independent-looking sources gave the same wrong
  number. Averaging or majority-voting made the error look confirmed. Both
  had copied from the same upstream FAQ.
- **Observable signature**: two sources with different domains agree exactly
  on a specific numeric value, and neither links the original primary.
- **Recovery**: trace each source to its upstream; if they share an upstream,
  they are one source, not two. Count corroboration by *independent* upstreams.
- **Prevention**: corroboration is counted from distinct primary origins, not
  from distinct URLs. Majority-vote and averaging are both forbidden.

## I4 — Contradiction swept under the rug

- **What happened**: two sources disagreed on a date. The agent picked the
  one that supported its draft conclusion and cited only that one.
- **Observable signature**: the evidence table has no `contradictions` section,
  or the section lists disagreements that never get resolved.
- **Recovery**: list the contradiction, weight by source quality, state the
  resolution explicitly, and record which source won and why.
- **Prevention**: the six-step contradiction procedure in
  `references/contradiction-handling.md`. A contradiction that is not resolved
  is a FAIL, not a footnote.

## I5 — Confidence claimed without evidence

- **What happened**: an agent wrote "high confidence" after reading one page
  that it had already memorised. There was no URL, no retrieval date, no score.
- **Observable signature**: an answer claims a confidence level but the
  evidence table has fewer than two primary sources, or any source is missing
  a retrieval date.
- **Recovery**: downgrade to the honest confidence level (medium = primary
  only, low = secondary only, none = no source) and say so in the answer.
- **Prevention**: the confidence ladder is stated in the answer, not hidden.

## I6 — Quotation that changes meaning

- **What happened**: a 14-word quote was trimmed to 4 words and the meaning
  flipped. The reader could not tell without fetching the original.
- **Observable signature**: a quote is used as evidence but the surrounding
  paraphrase does not match the quote's context.
- **Recovery**: quote only when the phrasing IS the evidence; otherwise
  paraphrase under 15 words and cite the URL. Never quote to make a point you
  cannot paraphrase.
- **Prevention**: the 15-word quotation ceiling is a hard rule, not a guideline.
