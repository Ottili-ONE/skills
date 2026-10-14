# Calibration protocol — llm-judge-calibration

Verified 2026-10-14. A calibration report is only evidence if it was produced by
a judge separated from the generator, scored against a rubric with per-level
examples, and measured on a calibration set that was never used to tune the
rubric. Without all three, the number is circular.

## 1. The three conditions (all required)
| Condition | Why |
|-----------|-----|
| Judge separated from teacher | same model + same prompt = circular agreement |
| Rubric with per-level examples | definitions alone produce 20+ point spread |
| Calibration set never used to tune | agreement measured on the tuning set is inflated |

## 2. Calibration set requirements
| Property | Value | Enforced by |
|----------|-------|-------------|
| Size | 30-50 items | `--min-items` / `--max-items` |
| Gold labels | every item | `--gold` presence check |
| Score spread | >= 2 distinct scores | `--min-scale-spread` |
| Held-out | never the training set | the operator's responsibility |

A set that is too small cannot support a meaningful agreement statistic; a set
that is too large is not held-out. A set where every score is identical makes
alpha=1.0 meaningless.

## 3. Agreement thresholds
| Krippendorff's alpha | Action |
|----------------------|--------|
| >= 0.6 | usable |
| 0.4 - 0.6 | fix the rubric |
| < 0.4 | unusable |

## 4. Position-bias protocol
Shuffle item order between judge runs. If a score moves by >0.5 on a 5-point
scale when its neighbours change, the judge is order-sensitive and scores must
be aggregated across shuffles. The script's `position_bias` statistic measures
the mean absolute deviation of the first rating from the median of the rest.

## 5. Drift protocol
Re-run the calibration set weekly. If the mean score moves by >0.3 or
agreement drops by >0.1, re-calibrate or retire the judge. Drift is only
meaningful if the baseline covers the same items as the current set; the
script enforces id alignment.

## 6. Provenance gate
Every report must record: judge model, generator model, judge prompt sha256,
generator prompt sha256. A report missing any of the four is not auditable and
the script rejects it. Decision table: same model + same prompt = fail;
different model OR different prompt = acceptable; different model = preferred.

## 7. Worked examples

### Good — separated judge, calibrated threshold
Generator `gpt-4.1` produces 100 summaries. Judge `claude-sonnet-4` scores them
on a 4-point rubric with per-level examples. Calibration set of 40 items with
human gold labels gives agreement 0.71 and a pass threshold of >=3. The
threshold is recorded with the date and the judge/generator hashes.

### Bad — same model judges its own outputs
`gpt-4.1` generates the summaries and `gpt-4.1` scores them. Agreement is
circular by construction. The script rejects this with "circular".

### Bad — calibration set of 3 items
A 3-item set cannot support a meaningful alpha. The script rejects it with
"minimum is 30".
