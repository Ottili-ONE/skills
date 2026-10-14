# Incidents — llm-judge-calibration

Real calibration failures, the observable signature that exposes them, and the
exact recovery procedure. Each incident is a case a generic agent gets wrong
because it trusts a single judge run.

## I1 — Circular self-judgement

- **What happened**: a team scored 200 agent outputs with the same model and
  prompt that generated them. Agreement was 0.98. A different judge model
  scored the same outputs at 0.41. The 0.98 was self-fulfilling.
- **Observable signature**: `JUDGE_MODEL == GENERATOR_MODEL` with the same
  prompt hash; the report records no provenance fields at all.
- **Recovery**: re-score with a separated judge. Record judge model, generator
  model and both prompt hashes in every report.
- **Prevention**: the provenance gate in `scripts/calibrate_judge.py` — the
  four fields are mandatory and identical model + identical prompt is rejected.

## I2 — Rubric with definitions only

- **What happened**: a 5-point rubric with only definitions ("poor" / "fair"
  / "good" / "very good" / "excellent") was used to score 100 items. Two
  annotators re-annotated 20 of them and agreed on 4 of 20. The rubric
  collapsed onto the middle point.
- **Observable signature**: a rubric whose points carry `definition` but no
  `example` and no `anti_examples`; re-annotation spread > 20%.
- **Recovery**: add a definition, an example and anti-examples for every point.
  Re-lint with `scripts/calibrate_judge.py rubric` and re-measure agreement on
  a held-out set.
- **Prevention**: `scripts/rubric_lint.py` rejects rubrics missing examples or
  anti-examples, with non-increasing scores, or whose scale does not start at 1.

## I3 — Calibration on the training set

- **What happened**: the rubric was tuned on the same 100 items used to
  measure agreement. Agreement came back at 0.85. On a fresh set of 100 items
  the same rubric scored 0.47. The threshold was useless in production.
- **Observable signature**: the calibration set file is the training set; the
  rubric was edited after seeing the calibration scores.
- **Recovery**: split the data. Build the rubric on a development set, measure
  agreement on a held-out calibration set, and derive the pass threshold from
  the calibration set only. Never fit the threshold to make a specific agent
  pass.
- **Prevention**: the calibration set is versioned and never the training set.

## I4 — Position bias mistaken for quality

- **What happened**: a judge scored the first item in every batch one point
  higher. The team read the high agreement as "the judge is good". When items
  were shuffled, 30% of scores moved by more than one point.
- **Observable signature**: `position_bias > 0.5` reported against a threshold
  of 0.5, with no aggregation step in the runbook.
- **Recovery**: aggregate scores across shuffles before reporting. Re-measure
  position bias on the aggregated scores.
- **Prevention**: `scripts/calibrate_judge.py` computes position bias as the
  mean absolute deviation of the first rating from the median of the rest and
  flags it.

## I5 — Drift ignored because the set was old

- **What happened**: a judge was calibrated in March against a set built in
  February. In June the same set still scored well, but a fresh set built in
  May scored 0.4 against the world. The old set was a snapshot of a
  distribution that had moved.
- **Observable signature**: the `calibration.jsonl` file unchanged since build;
  drift measured only against an aged set; no re-collection step.
- **Recovery**: re-collect 30-50 fresh items spanning the current score range,
  re-label them, retire the old set, and schedule weekly drift re-checks.
- **Prevention**: drift is measured against a baseline and re-run weekly; a
  mean shift > 0.3 or agreement drop > 0.1 triggers re-calibration.

## I6 — Ceiling effect reported as success

- **What happened**: a judge gave every item a 4 or 5 on a 1-5 scale. The
  mean was high and agreement looked fine. The rubric had no way to
  distinguish good from excellent, so the judge could not tell apart the best
  agents.
- **Observable signature**: all scores in the top two points; `degenerate`
  flag set; the spread of scores is near zero.
- **Recovery**: re-train the rubric on edge cases that separate the top
  points; report the squeeze in the calibration report rather than treating
  the high mean as a pass.
- **Prevention**: `scripts/calibrate_judge.py` sets `degenerate` when alpha is
  1.0 and every score is identical.
