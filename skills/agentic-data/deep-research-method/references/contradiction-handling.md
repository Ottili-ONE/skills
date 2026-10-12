# Contradiction handling — deep-research-method

Two sources that disagree are a finding, not noise. This page records the
ordered procedure for resolving them and the failure modes that masquerade as
resolution.

## Ordered procedure

1. **State both claims verbatim** (short quote, under 15 words each). Do not
   paraphrase before you have established what they actually say.
2. **Record the source, score and retrieval date for each.** A contradiction
   between a score-9 primary and a score-4 blog is not a tie.
3. **Check for a category error** — are the two sources answering different
   questions? "When was X released?" vs "When was X released in Europe?" are
   not contradictory. If the questions differ, there is no contradiction.
4. **Check for a version error** — is one source describing an older version of
   a fact? A 2024 API behaviour and a 2026 API behaviour are not contradictory;
   the older one is stale. Re-fetch the older source.
5. **Weight by quality, not by count.** The higher-scoring source wins. If the
   scores are equal, the more recent source wins, and the disagreement is
   recorded as unresolved.
6. **State the resolution and the confidence.** If unresolved, say so and list
   what would resolve it (a primary source, a newer retrieval, a direct
   question to the maintainer).

## Decision table

| Situation | Resolution |
|-----------|-----------|
| Scores differ | higher score wins; note the loser as a minority view |
| Scores equal, recency differs | more recent wins |
| Scores equal, recency equal | unresolved; state both, name the tie-break needed |
| Different questions (category error) | not a contradiction; re-decompose |
| Different versions (stale source) | re-fetch the stale source; if still stale, discard it |
| One source retracted/corrigated | the correction wins; record the retraction |

## Near-miss triggers

- **Averaging** "one says one month, the other says two" into "one and a half
  months" -> the fake middle is the worst possible answer. Never do this.
- **Majority vote** on three low-quality sources vs one high-quality primary ->
  the majority is wrong. Weight, do not count.
- **Ignoring a contradiction because it is inconvenient** -> record it anyway;
  the answer must be as uncomfortable for the reader as it is for you.
- **Paraphrasing before quoting** -> you may have already changed the claim.
  Quote first, then paraphrase.
- **Treating a retraction as a second opinion** -> a retraction replaces the
  original claim. The original source is now evidence *against* its own
  earlier claim.
