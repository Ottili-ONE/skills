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
