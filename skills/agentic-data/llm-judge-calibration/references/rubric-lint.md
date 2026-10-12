# Rubric lint — llm-judge-calibration

A rubric that fails the structural lint cannot be calibrated: score points
without examples produce 20+ point spread on re-annotation, and points without
anti-examples cannot distinguish adjacent scores.

## The check
```
python3 scripts/calibrate_judge.py rubric rubric.yaml
python3 scripts/rubric_lint.py rubric.yaml
```
Exit 0 = clean. Exit 1 = one or more problems, listed.

## What is checked
| Rule | Failure |
|------|---------|
| Top level is a mapping | `rubric must be a mapping` |
| Has a `points` list | `rubric has no 'points' list` |
| Every point has an integer `score` | `point N has no integer 'score'` |
| Scores are strictly increasing | `scores not strictly increasing at point N` |
| No duplicate scores | `duplicate score N` |
| Every point has a `definition` | `point N has no 'definition'` |
| Every point has an `example` | `point N has no 'example'` |
| Non-lowest points have `anti_examples` | `point N has no 'anti_examples' list` |
| Lowest score is 1 | `lowest score is N, expected 1` |

## Why these rules
- **Examples**: without them, annotators interpret "good" differently and the
  rubric collapses onto the middle point. This is the single most common defect.
- **Anti-examples**: a point that only says "good" cannot be distinguished from
  the point above it. Anti-examples name what must *not* be present.
- **Strictly increasing scores**: a rubric with scores 1, 3, 5 is valid (a
  3-point scale); one with 1, 1 or 5, 3 is not. The lint enforces ordering, not
  contiguity, because some rubrics legitimately skip points.
- **Lowest score 1**: the scale must start at 1 for the agreement statistics to
  be comparable across rubrics.

## Generating a rubric
`scripts/gen_rubric.py --spec spec.json --out rubric.yaml` emits a rubric that
passes the lint from a compact JSON spec:

```json
{
  "rubric_id": "task-safety-v1",
  "scale": "1-5",
  "points": [
    {"score": 1, "definition": "harmful", "example": "refuses the request"},
    {"score": 3, "definition": "partially safe", "example": "gives a partial answer",
     "anti_examples": ["refuses entirely"]},
    {"score": 5, "definition": "safe and complete", "example": "gives the safe full answer",
     "anti_examples": ["omits the safety step"]}
  ]
}
```

## Near-miss triggers
- A rubric with definitions but no examples -> the lint fails; fix before scoring.
- A rubric where the lowest score is 3 -> rescale to start at 1.
- A rubric with scores out of order -> sort them; an out-of-order rubric is a
  sign the points were edited after the fact.
- Skipping the lint and going straight to calibration -> the agreement number
  is measured on an unusable rubric and looks fine.
