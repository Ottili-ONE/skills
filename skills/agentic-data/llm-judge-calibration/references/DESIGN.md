# DESIGN: llm-judge-calibration

## Trigger description (SKILL.md description draft, <=1024 chars)
"Calibrate LLM judges: rubrics, calibration sets, inter-annotator agreement, drift
detection and judge/teacher separation. Use when an agent must build or audit an
LLM-as-judge scoring pipeline; not for building a single rubric from scratch."

## Procedure outline
1. Separate judge from teacher — the scoring model must not be the generator (or the
   same prompt). Record judge model, generator model and both prompt hashes in every
   report. Same model + same prompt = circular = fail.
2. Write the rubric BEFORE any scoring — each score point gets a definition and at least
   one example of each level. Points without examples produce 20+ point spread on
   re-annotation.
3. Build a calibration set of 30-50 items spanning the score range, each with a human
   gold label. Never calibrate on the training set.
4. Measure agreement — Fleiss' kappa or Krippendorff's alpha >= 0.6 before trusting.
   <0.4 = rubric unusable.
5. Check position/order bias — shuffle item order between runs; a score moving >0.5 on a
   5-point scale when neighbours change means the judge is order-sensitive; aggregate
   across shuffles.
6. Detect drift — re-run the calibration set weekly; mean shift >0.3 or agreement drop
   >0.1 means re-calibrate or retire.
7. Calibrate the pass rate — the threshold yielding the target pass rate on the
   calibration set is the operating threshold. Never fit it to make a specific agent
   pass.

## Scripts planned
- `scripts/calibrate_judge.py` — given a rubric, a calibration set with gold labels and
  judge outputs, reports agreement, position bias, drift and the derived threshold.

## Five eval prompts (mirrored in `references/EVALS.md`)
1. "The judge and the generator are the same model. Is the agreement number usable?" ->
   No: circular. Separate judge from teacher first.
2. "My rubric has definitions but no examples. What happens?" -> Annotator spread of 20+
   points; add per-level examples before scoring.
3. "I calibrated on the training set. Is that valid?" -> No: overfit, does not transfer.
   Use a held-out calibration set.
4. "A score moves by 0.7 when I shuffle the neighbours." -> Position bias present;
   aggregate scores across shuffles.
5. "The judge's mean score moved 0.4 since last week." -> Drift; re-calibrate or retire
   the judge.

## What this skill does better than a generic agent
A generic agent trusts a single judge run. This skill separates judge from teacher,
requires per-level rubric examples, measures agreement on a held-out set, checks position
bias by shuffling, and schedules drift re-checks. It prevents the common incident of a
"calibrated" judge whose agreement was measured on the very set the rubric was tuned on.
