# Robustness — llm-judge-calibration

A calibrated judge that crashes on real input is not calibrated. This skill's
`scripts/calibrate_judge.py` is offline and deterministic; this page records the
edge cases it handles and the failure modes it must not silently swallow.

## Edge cases and behaviour

| Input | Behaviour |
|-------|-----------|
| Empty file / all-blank lines | `n_items=0`, alpha 0.0, exit 1 with `FAIL: no items` |
| Rows with no `scores` field | skipped from agreement; if all rows are empty, alpha 0.0 |
| Single rater per item | alpha 0.0 (no pairs to compare) — the run is invalid, not passing |
| All scores identical | alpha 1.0 by definition; report `degenerate` flag |
| Non-numeric `scores` | the value is dropped (filtered by `v is not None` after float coercion); log which rows were affected |
| Missing `gold` | ignored — gold is advisory, the judge's own scores are the measurement |
| `--baseline` file missing | hard error, exit 2, before any computation |
| `--json` parent dir missing | hard error, exit 2 |
| `--min-agreement` > 1.0 or < 0 | hard error, exit 2 |
| Scale mismatch between rows and baseline | drift is still computed on the raw mean; the report carries `scale_warning` |

## Determinism contract

- No `time`, `datetime`, `random` or wall-clock calls anywhere in the script.
- Sorting is by insertion order only where the input order is the measurement
  (position bias depends on order). Where order must not matter (agreement),
  values are sorted before use.
- Rounding is fixed at 4 decimals in the JSON report; stdout is unbuffered text.

## Hardening added this pass

- `load_rows` validates each line is a JSON object; a malformed line prints
  `WARN: line N is not a JSON object, skipped` and continues (exit still 0 if some
  rows remain, 1 if none).
- Empty `scores` list after filtering -> the row is counted in `n_items` but
  contributes no pairs.
- `--baseline` and `--json` are validated before the main computation so a bad
  path cannot produce a misleading PASS.
- Exit codes: 0 = pass, 1 = threshold failure, 2 = usage/input error. A shell
  script that checks `$?` can distinguish "judge is bad" from "I typed it wrong".

## Near-miss triggers

- A JSONL file that is actually a single JSON array -> every line fails to parse,
  the script reports "no items" and exits 1. Do not mistake this for a clean
  empty run.
- `scores` as a string instead of a list -> the row is skipped silently. Check
  the `n_items` against what you expected.
- Baseline measured on a different scale (1-3 vs 1-5) -> drift is large but
  meaningless. Pin the scale in the rubric version and compare like with like.
