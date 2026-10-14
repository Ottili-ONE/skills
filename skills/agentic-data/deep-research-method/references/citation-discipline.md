# Citation Discipline

Citation discipline is the rule that every claim in the final answer traces to a
specific source that the reader (and the agent, on re-run) can re-fetch. It is
the part of `deep-research-method` that survives longest: a fact that was true
in June must still be findable in December, and the reader must be able to tell
whether the agent checked it last week or last year.

## The three questions every citation answers
A complete citation answers:

1. **What** was claimed (the statement, verbatim or near-verbatim).
2. **Where** it came from (URL, document title, publisher, page or section).
3. **When** it was retrieved (date, plus the version/revision the agent saw).

If any of the three is missing, the citation is not auditable and the claim
must be downgraded to the confidence ladder's next-lower rung.

## Recording retrieval dates
Record the retrieval date on the same line as the URL, in ISO format, e.g.:

```
Retrieved 2026-10-14: https://www.w3.org/TR/html52/ (W3C Recommendation, editors'
draft as of 2026-10-14).
```

Do not record only "accessed recently". A date is the only evidence that the
fact was checked at a time when it was still true. `scripts/score_sources.py`
flags any source in `references/SOURCES.md` whose recorded date is older than
the staleness window for its tier (see `references/staleness.md`).

## Quotation rules
- Quotations of **15 words or fewer** may be used verbatim without further
  attribution beyond the citation.
- Quotations of **more than 15 words** must be marked as quotations and must
  carry a page or section reference.
- **Never paraphrase a passage so closely that a reader could mistake it for the
  original** — that is plagiarism by rearrangement, not a summary. If the
  sentence structure survives, quote it.
- A summary must change at least one of: wording, argument order, or level of
  abstraction. If it does not, quote.

## Version-sensitive facts
Facts about versions, release dates, API shapes, deprecations and pricing are
the most likely to go stale. For each such fact:

1. Record the **exact version** the agent saw (e.g. "PostgreSQL 16.4", not
   "PostgreSQL 16").
2. Re-fetch the source before writing the final answer if the fact is
   version-sensitive and the fetch is older than 7 days.
3. Mark the fact with the version in the text, e.g. "as of PostgreSQL 16.4".

`references/SOURCES.md` records the verified version and retrieval date for
every version-sensitive source.

## Contradictions between sources
When two sources disagree, do not silently pick one. Record the disagreement
in `references/incidents.md` with:

- The two claims and their sources (with retrieval dates).
- Which source is more recent / higher tier / more authoritative.
- The resolution: which claim is used, and why.
- A note on what would change if the other source were right.

See `references/contradiction-handling.md` for the full protocol.

## Self-check before publishing
- [ ] Every claim in the answer has a citation with URL, title, and retrieval date.
- [ ] No quotation exceeds 15 words without a page/section reference.
- [ ] No passage is a paraphrase of a single source's wording.
- [ ] Every version-sensitive fact records the exact version seen.
- [ ] Every contradiction is recorded in `references/incidents.md`.
- [ ] `scripts/score_sources.py --check-citations` reports no orphan claims.
