---
name: llm-judge-calibration
description: "Calibrate LLM judges: rubrics, calibration sets, inter-annotator agreement, drift detection and judge/teacher separation. Use when an agent must build or audit an LLM-as-judge scoring pipeline; not for building a single rubric from scratch."
compatibility: Python 3.10+, any LLM API; verified 2026-10-09
license: MIT
---
# LLM Judge Calibration

Trigger: building or auditing an LLM-as-judge scoring pipeline where the judge's
scores must be reliable, reproducible and free of position/order bias.

## Core invariant
A judge score is only evidence if it was produced by a judge that is separated
from the generator, scored against a rubric with per-level examples, and measured
on a calibration set that was never used to tune the rubric. Without all three,
the number is circular.

## Procedure (numbered — follow in order)
1. **Separate judge from teacher** — the judge that scores submissions must not be
   the same model (or same prompt) that generated them. If the judge can see its
   own outputs, agreement is meaningless. Record judge model, generator model and
   both prompt hashes in every report.
2. **Write a rubric before any scoring** — each score point gets a definition and
   at least one example of each level. Score points without examples are
   ambiguous and produce 20+ point spread on re-annotation.
3. **Build a calibration set** — 30-50 items spanning the score range, each with
   a human gold label. Never calibrate on the training set.
4. **Measure agreement** — Fleiss' kappa or Krippendorff's alpha >= 0.6 before
   trusting the judge. Below 0.4 the rubric is not usable.
5. **Check for position/order bias** — shuffle item order between judge runs; if
   a score moves by >0.5 on a 5-point scale when its neighbours change, the judge
   is order-sensitive and scores must be aggregated across shuffles.
6. **Detect drift** — re-run the calibration set weekly; if the mean score moves
   by >0.3 or agreement drops by >0.1, re-calibrate or retire the judge.
7. **Calibrate the pass rate** — the threshold that yields the target pass rate on
   the calibration set is the operating threshold. Never fit it to make a
   specific agent pass.

## Decision tables
- **Agreement**: >=0.6 usable; 0.4-0.6 fix the rubric; <0.4 unusable.
- **Drift**: mean shift 0-0.2 = stable; 0.2-0.3 = watch; >0.3 = re-calibrate.
- **Position bias**: 0-0.3 = acceptable; >0.5 = aggregate across shuffles.
- **Judge/teacher separation**: same model + same prompt = fail; different model
  or different prompt = acceptable; different model = preferred.

## Near-miss triggers (stop and re-check before proceeding)
- Judge and generator are the same model -> agreement is circular.
- Rubric has no per-level examples -> ambiguous, low agreement.
- Calibration set is the training set -> overfit, does not transfer.
- Agreement measured on a set the rubric was tuned on -> inflated.
- A score moves when neighbours change -> position bias present.
- Drift >0.3 or agreement drops >0.1 since last week -> re-calibrate.

## Pitfalls from research
- P1: Same-model judging of same-model outputs produces circular agreement.
- P2: Rubrics without per-level examples cause annotator spread.
- P3: Calibrating on the training set inflates agreement and does not transfer.
- P4: Position/order bias is common in LLM judges; always shuffle.
- P5: Drift is real; a judge calibrated in March may not be valid in June.
- P6: A rubric with only a definition and no examples reads as identical to a
  5-point scale and collapses onto the middle point.

## Verification checklist
- [ ] Judge and teacher are separated (different model or prompt).
- [ ] Rubric has per-level definitions and examples.
- [ ] Calibration set has 30-50 items with gold labels.
- [ ] Agreement >= 0.6 measured on a held-out set.
- [ ] Position bias < 0.5 or scores aggregated across shuffles.
- [ ] Drift check scheduled weekly with thresholds recorded.
- [ ] Pass-rate threshold derived from the calibration set, not the training set.
- [ ] Judge model, generator model and prompt hashes recorded in the report.

## References
- procedures: references/procedures.md
- rubric template: references/rubric-template.md
- EVALS: references/EVALS.md
- SOURCES: references/SOURCES.md
- scripts: scripts/calibrate_judge.py
