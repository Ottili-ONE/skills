# EVALS — llm-judge-calibration

Each eval is a realistic prompt an agent might receive, the expected behaviour
per this skill, and failure signs to look for.

## E1 — build a calibration pipeline from scratch
Prompt: "Build an LLM judge to score student answers on a 5-point rubric."
Expected: separate judge from generator (different model or prompt), write a
rubric with per-level definitions, examples and anti-examples, build a 30-50
item calibration set with gold labels, run `scripts/calibrate_judge.py --rows
calibration.jsonl`. Acceptance: exit 0, alpha >= 0.6, position bias <= 0.5.
Failure signs: judge is the same model as the generator; rubric has no
per-level examples; calibration set is the training set; agreement below 0.6
with no action taken.

## E2 — detect circular judge/teacher separation
Prompt: "My judge is the same model that generated the answers, using the same
prompt. Is the agreement number real?"
Expected: No. Same model + same prompt = circular agreement. Change the judge
model or the judge prompt and re-measure. Record judge model, generator model
and both prompt hashes in every report.
Failure signs: `JUDGE_MODEL == GENERATOR_MODEL` with the same prompt; no model
hash recorded.

## E3 — detect a rubric without per-level examples
Prompt: "My rubric only has definitions like 'good' / 'bad'. Score with it."
Expected: Reject. A rubric without per-level examples produces 20+ point spread
on re-annotation. Add a definition, an example and anti-examples for every
point. See `references/rubric-template.md`.
Failure signs: rubric with no `example` fields; re-annotation spread > 20%.

## E4 — detect position/order bias
Prompt: "My judge scores the first item in every batch higher."
Expected: `calibrate_judge.py` computes position bias as the mean absolute
deviation of the first rating from the median of the rest. If >0.5, the judge
is order-sensitive -> aggregate scores across shuffles before reporting.
Failure signs: bias > 0.5 with no aggregation step; scores reported from a
single order.

## E5 — detect drift over time
Prompt: "My judge was calibrated in March; it is now June. Is it still valid?"
Expected: Re-run the calibration set. If the mean score moves by >0.3 or
agreement drops by >0.1, re-calibrate or retire the judge. Use
`--baseline baseline.jsonl --max-drift 0.3`.
Failure signs: no drift check scheduled; drift > 0.3 ignored.

## E6 — pass-rate threshold must come from the calibration set
Prompt: "Set the pass threshold so 90% of agents pass."
Expected: Reject. The operating threshold is the score that yields the target
pass rate on the *calibration set* (held-out, with gold labels), never fit to
make a specific agent pass. Derive it once and freeze it.
Failure signs: threshold moved after seeing agent scores; threshold fit to the
training set.

## E7 — low agreement means fix the rubric, not the scores
Prompt: "My judge has alpha 0.2. Can I still use it?"
Expected: No. Alpha < 0.4 is unusable; 0.4-0.6 means fix the rubric. Do not
post-process scores to force agreement. Re-author the rubric and re-measure on
a held-out set.
Failure signs: alpha < 0.6 with scores still reported; calibration measured on
the set the rubric was tuned on.

## E8 — the calibration set itself can go stale
Prompt: "I have been using the same calibration set for nine months. The judge
still scores well on it. Is the set still good?"
Expected: No. A calibration set that has not been refreshed is a snapshot of the
distribution it was built from, and distributions move. Re-collect 30-50 fresh
items spanning the current score range, re-label them, and retire the old set.
A judge that scores well on a nine-month-old set may be drifting against the
world while looking stable against its own artefact. Keep one active set and
archive each replacement with its collection date.
Failure signs: the same `calibration.jsonl` file unchanged since build; no
re-collection step in the runbook; drift measured only against an aged set.

## E9 — a calibration report must carry provenance
Prompt: "My report shows agreement 0.71. Is that enough?"
Expected: No. The report must also record the judge model, the generator model
and the hash of both prompts. Without provenance the agreement number cannot be
reproduced or audited. `scripts/calibrate_judge.py calibrate` requires all four
fields and exits 1 with `FAIL: --judge-model is required for every calibration
report` if any is missing; `--json report.json` writes all four. A report
written without them is not evidence.
Failure signs: a report with agreement but no model names; no prompt hashes;
the calibration run accepted without the four provenance flags.

## E10 — lint a rubric before calibrating it
Prompt: "I wrote a rubric. Calibrate the judge."
Expected: Lint it first with
`scripts/calibrate_judge.py rubric rubric.yaml`. It must exit 0 with
`PASS: rubric '<id>' has N contiguous points with definitions, examples and
anti-examples`. A rubric that fails the lint (a point without an example, a
point without anti-examples, a duplicate or out-of-order score, a scale not
starting at 1) cannot be calibrated — fix it before scoring. Generate a valid
one from a compact spec with `scripts/gen_rubric.py --spec spec.json --out rubric.yaml`.
Failure signs: calibration run on a rubric that fails the lint; a rubric whose
lowest score is not 1; a rubric with scores out of order.

## E11 — reject a circular judge and teacher
Prompt: "My judge is the same model that generated the answers, using the same
prompt. Calibrate it."
Expected: Reject. Same model + same prompt = circular agreement by construction.
`scripts/calibrate_judge.py calibrate --judge-model gpt-4.1
--generator-model gpt-4.1 --judge-prompt-sha same --generator-prompt-sha same`
exits 1 with `FAIL: judge and generator are the same model with the same
prompt; agreement is circular by construction`. Change the judge model or the
judge prompt and re-measure.
Failure signs: calibration passing with identical model and prompt; the
circular case not checked.

## E12 — separated models with the same prompt are acceptable
Prompt: "My judge is a different model but I reused the generator's prompt.
Is that allowed?"
Expected: Yes, per the decision table: different model OR different prompt =
acceptable (different model is preferred). `scripts/calibrate_judge.py
calibrate --judge-model claude-sonnet-4 --generator-model gpt-4.1
--judge-prompt-sha a --generator-prompt-sha b` exits 0 on the thresholds. Only
identical model AND identical prompt is circular.
Failure signs: rejecting a legitimately separated pair; accepting an identical
pair.


## E13 — reject a calibration set that is too small or too large
Prompt: "My calibration set has 3 items. Can I calibrate on it?"
Expected: No. `scripts/calibrate_judge.py calibrate --rows tiny.jsonl` exits 1
with `FAIL: calibration set has 3 items, minimum is 30`. The default window is
30-50 items; `--min-items` and `--max-items` are configurable. A set that is too
small cannot support a meaningful agreement statistic; a set that is too large
is not held-out.
Failure signs: calibration passing on a handful of items; the size bounds not
enforced.

## E14 — reject a calibration set with no gold labels or no spread
Prompt: "My calibration set has 30 items but no gold labels, and every score is
3."
Expected: No, on two grounds. A row with no `gold` fails with
`FAIL: N item(s) have no gold label`. A set spanning one distinct score fails
with `FAIL: calibration set spans 1 distinct score(s), minimum is 2; a
degenerate set cannot be calibrated` -- alpha would be 1.0 for a trivial
reason. Both checks run before agreement is measured.
Failure signs: calibration passing on an unlabelled or constant set; the
degenerate case not checked.
