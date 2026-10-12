# Trigger evals — skill-authoring-evals

A skill that never fires is a documentation file with a folder. A skill that
fires on everything is noise. This page is the measurement protocol.

## The two sets

| Set | Meaning | How to collect |
|-----|---------|----------------|
| SHOULD fire | prompts whose intent matches the skill | real user tickets, support queries, past failures |
| SHOULD NOT fire | prompts that mention the skill's keywords but want something else | adversarial negatives, near-misses |

## Train/validation split

Split 70/30. Tune the description on the training set; measure on the
validation set. If the two sets score very differently, the description is
overfit to the training phrasing — recruit fresh prompts.

## Metrics

- **Precision** = should-not-fire prompts that did NOT fire / all should-not-fire.
  Low precision = description too broad.
- **Recall** = should-fire prompts that DID fire / all should-fire.
  Low recall = description too narrow.
- Target: precision >= 0.9, recall >= 0.9. Below 0.8 on either, rewrite the
  description, not the body.

## The with_skill / without_skill baseline

Every test case runs **twice**: once with the skill loaded, once without. The
baseline tells you whether the skill changed the output at all. A skill that
produces identical output to the baseline did nothing; a skill that makes
output worse is worse than no skill.

Record in `iteration-N/<eval>/with_skill/` and `without_skill/`, aggregated in
`benchmark.json`.

## Ordered procedure

1. Collect the two sets (train/validation split).
2. Run every prompt without the skill -> baseline.
3. Run every prompt with the skill -> with_skill.
4. Compute precision, recall, and output delta per prompt.
5. Identify the weakest section (lowest recall or lowest delta).
6. Rewrite that section; re-run evals; re-validate.
7. Never ship a skill whose evals were not run.

## Near-miss triggers

- All prompts are the author's own phrasing -> overfit; recruit fresh prompts.
- Only with_skill runs recorded -> no baseline; a skill that does nothing looks
  identical to a skill that works.
- Testing only with prompts the author wrote in the same style they will meet
  in production -> the eval is not representative.
- Tuning the description until the validation set passes -> the validation set
  is now part of the training set; re-split.
- Shipping because "it looks good" -> the evals were never run.
