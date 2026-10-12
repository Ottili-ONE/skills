# Contradiction Handling — deep-research-method

When two kept sources disagree, the disagreement is a finding, not a nuisance.
This page is the procedure the SKILL.md decision tables are derived from.

## 1. Never average two views into a fake middle
Averaging "+0.4" and "+0.1" into "+0.25" produces a number that no source
actually claimed. It reads as precision and carries none of the evidence. The
skill's rule: cite the higher-weight source as primary, note the lower-weight
disagreement, and state the range. The reader sees the disagreement and the
reason for the choice.

## 2. The four-step procedure
1. **List the contradiction.** Quote each source's claim and record its score
   (authority / recency / corroboration, 0-10) and its retrieval date. A
   contradiction that is not written down is a contradiction that will be
   resolved by whoever speaks last.
2. **Check for a real difference.** Same fact, different units? Different
   populations? Different definitions of the term? Many "contradictions" are
   orthogonal claims that only look like duplicates. Resolve the framing first;
   only then compare the numbers.
3. **Weight by quality, not by count.** Two low-quality blogs do not outweigh one
   primary source. Count is the weakest signal available; authority and
   corroboration are stronger. If the scores are equal, prefer the more recent
   source and say so.
4. **State the resolution.** Name the winning source, record the losing source
   as a named disagreement, and state the range of plausible values. If the
   evidence is genuinely insufficient to choose, say so and downgrade confidence
   rather than inventing a synthesis.

## 3. When the higher-weight source is wrong
Quality weighting is a prior, not a guarantee. A primary source can be
outdated, misread, or simply wrong. The checks:
- Is the primary source's retrieval date stale for this question? Then it loses
  its recency points and the balance may shift.
- Does a third, independent source agree with the minority view? Corroboration
  is recomputed at this step, not carried over from the scoring step.
- Is the primary source a secondary summary of the primary claim? Then it was
  never primary; re-score it and re-run step 3.

Record the re-weighting in the claims file. A silent flip is worse than a
stated one, because the reader cannot audit it.

## 4. Near-miss triggers
- Two sources disagree and the answer says "sources disagree" with no
  resolution -> the contradiction was listed and then abandoned.
- The majority view wins on count while a single primary source disagrees ->
  re-weight by quality.
- The answer averages two numbers into a middle value -> fake precision.
- A contradiction is resolved by picking the source that was fetched last ->
  order bias, not evidence.
- The losing source is dropped from the citations entirely -> the reader cannot
  see the disagreement.
- A contradiction is "resolved" by redefining one of the terms after the fact ->
  the comparison was never valid.

## 5. Worked example
Source A (university preprint, score 8, retrieved 2026-10-12): "the effect is
+0.4". Source B (industry report, score 6, retrieved 2026-10-12): "the effect
is +0.1".

1. List: A=+0.4 vs B=+0.1, both recent and on-topic.
2. Check framing: same outcome measure, same population. Real contradiction.
3. Weight: A (8) > B (6). Cite A as primary; note B as a lower-weight
   disagreement.
4. State: "+0.4 (primary, score 8); a lower-weight industry report puts it at
   +0.1. Plausible range +0.1 to +0.4."

Result: the reader sees the disagreement and the reason for the choice. No
averaging, no hidden minority view.
