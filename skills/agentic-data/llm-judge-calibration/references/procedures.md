# Procedures — llm-judge-calibration

Verified 2026-10-09. Version-sensitive: model APIs change; pin the model and
re-run the calibration set after any model upgrade.

## 0. The core invariant
A judge is trustworthy only if (a) it is not the generator, (b) its rubric is
unambiguous, and (c) its scores are stable across order and time. Measure all
three before trusting any score.

## 1. Judge/teacher separation
- The judge that scores submissions must not be the same model that generated
  them with the same prompt. Same model + same prompt = circular agreement.
- Acceptable: different model, or same model with a substantially different
  prompt. Preferred: a different model.
- Record the judge model, generator model and both prompt hashes in every report.

## 2. Rubric authoring
Each score point (1..N) needs:
1. A one-line definition.
2. At least one example of a submission that earns that score.
3. A list of things that must NOT be present to earn it (anti-examples).

Rubric without per-level examples -> 20+ point spread on re-annotation.

Template (5-point scale):
```yaml
scale: 1-5
points:
  - {score: 5, definition: "...", example: "...", anti_examples: ["..."]}
  - {score: 4, definition: "...", example: "...", anti_examples: ["..."]}
  ...
```

## 3. Calibration set
- 30-50 items spanning the full score range.
- Each item has a human gold label.
- Never calibrate on the training set; use a held-out set.
- Store as JSONL: `{"id", "prompt", "response", "gold": 5, "rubric_version": "v1"}`.

## 4. Agreement
- Fleiss' kappa (>=3 raters) or Krippendorff's alpha (>=2 raters).
- Thresholds: >=0.6 usable; 0.4-0.6 fix the rubric; <0.4 unusable.
- Always measure on a set the rubric was NOT tuned on.

## 5. Position/order bias
- Score each item at least twice with a different neighbour order.
- If `|score_run1 - score_run2| > 0.5` on a 5-point scale for >10% of items,
  the judge is order-sensitive -> aggregate across shuffles before reporting.

## 6. Drift detection
- Re-run the calibration set weekly (or after any model upgrade).
- Mean shift 0-0.2 = stable; 0.2-0.3 = watch; >0.3 = re-calibrate or retire.
- Agreement drop >0.1 -> re-calibrate.

## 7. Pass-rate calibration
- The operating threshold is the score that yields the target pass rate on the
  calibration set. Never fit it to make a specific agent pass.

## Worked examples

Good — rubric with examples:
```yaml
points:
  - {score: 5, definition: "correct and complete, all steps shown",
     example: "2+2=4. Step 1: ... Step 2: ...",
     anti_examples: ["answer only, no steps"]}
```

Bad — rubric without examples:
```yaml
points:
  - {score: 5, definition: "good"}
```

Good — judge/teacher separation:
```python
JUDGE_MODEL = "gpt-4o-2024-08-06"   # different from generator
GENERATOR_MODEL = "claude-3-5-sonnet-20241022"
```

Bad — circular:
```python
JUDGE_MODEL = GENERATOR_MODEL  # agreement is meaningless
```
