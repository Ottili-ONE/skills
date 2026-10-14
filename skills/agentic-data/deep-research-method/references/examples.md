# Worked examples — deep-research-method

Detection signal: what in the output tells you the procedure was followed or
skipped. Each example ends with the check that would have caught it.

## Good — contradiction resolved by quality weight

Source A (university preprint, score 8) says "the effect is +0.4".
Source B (industry report, score 6) says "the effect is +0.1".
Both are recent and on-topic.

1. Score both: A=8, B=6.
2. Record the contradiction in the claims file.
3. Resolve by weight: cite A as primary, note B as a lower-weight disagreement,
   and state the range (+0.1 to +0.4) in the summary.

Result: the reader sees the disagreement and the reason for the choice.
Detection signal: the summary names both sources and gives a range, not a
single number.

## Bad — unsourced claim dressed as a finding

"The model is 3x faster than the baseline." No URL, no retrieval date, no version.

Why it fails: the claim cannot be verified or re-checked. The rule is URL +
retrieval date + pinned version for every claim; a claim without a source is a
confidence of `low` and must be flagged, not asserted.
Detection signal: a sentence with a number and no citation.

## Bad — quoting 22 words to "prove" a point

`"the results show a statistically significant improvement in latency,
throughput, and accuracy across all benchmarks"`.

Why it fails: long quotations are paraphrase bait and easy to misquote. Keep
quotations under 15 words; anything longer is a summary with a citation, not a
quote.
Detection signal: a blockquote longer than 15 words that is not labelled a
summary.
