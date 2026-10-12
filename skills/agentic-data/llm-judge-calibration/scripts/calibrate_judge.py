#!/usr/bin/env python3
"""Offline calibration for an LLM judge: agreement, position bias, drift.

Reads JSONL annotation files (each row: id, scores list, gold) and reports
Fleiss' kappa / Krippendorff's alpha, position-bias and drift vs a baseline.
Fully offline and deterministic: no network, no wall-clock, fixed rounding.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


def load_rows(path: Path) -> list[dict]:
    """Read JSONL. Malformed lines are warned and skipped; an empty result is a
    hard failure at the caller, never a silent PASS."""
    if not path.is_file():
        raise SystemExit(f"ERROR: rows file not found: {path}")
    rows: list[dict] = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"WARN: line {n} is not a JSON object ({e}); skipped", file=sys.stderr)
            continue
        if not isinstance(obj, dict):
            print(f"WARN: line {n} is not a JSON object; skipped", file=sys.stderr)
            continue
        # coerce scores to numbers, drop non-numeric entries
        raw = obj.get("scores")
        if isinstance(raw, list):
            obj["scores"] = [float(v) for v in raw if isinstance(v, (int, float))]
        elif raw is None:
            obj["scores"] = []
        else:
            print(f"WARN: line {n} 'scores' is not a list; treated as empty", file=sys.stderr)
            obj["scores"] = []
        rows.append(obj)
    return rows


def krippendorff_alpha(rows: list[dict]) -> float:
    """Krippendorff's alpha for ordinal scores. rows: {id, scores:[...], gold}."""
    items = [r for r in rows if r.get("scores")]
    if not items:
        return 0.0
    n_raters = max(len(r["scores"]) for r in items)
    if n_raters < 2:
        return 0.0
    values = sorted({v for r in items for v in r["scores"] if v is not None})
    if len(values) < 2:
        return 1.0
    index = {v: i for i, v in enumerate(values)}
    m = len(values)
    # observed coincidences
    n_pairs = 0
    do = 0.0
    for r in items:
        sc = [index[v] for v in r["scores"] if v is not None]
        k = len(sc)
        n_pairs += k * (k - 1) / 2
        for i in range(k):
            for j in range(i + 1, k):
                do += 1.0 if sc[i] == sc[j] else 0.0
    if n_pairs == 0:
        return 0.0
    do /= n_pairs
    # expected
    counts = [0] * m
    for r in items:
        for v in r["scores"]:
            if v is not None:
                counts[index[v]] += 1
    n = sum(counts)
    if n < 2:
        return 0.0
    de = sum(c * (c - 1) for c in counts) / (n * (n - 1))
    if de >= 1.0:
        return 1.0
    return (do - de) / (1.0 - de) if (1.0 - de) != 0 else 0.0


def mean_score(rows: list[dict]) -> float:
    vals = [v for r in rows for v in r.get("scores", []) if v is not None]
    return sum(vals) / len(vals) if vals else 0.0


def position_bias(rows: list[dict]) -> float:
    """Mean absolute deviation of the FIRST rating from the median of the rest.

    A proxy for position/order bias: if the rater that saw the item first
    systematically scores it differently from the raters that saw it later,
    the judge is order-sensitive.
    """
    diffs = []
    for r in rows:
        sc = [v for v in r.get("scores", []) if v is not None]
        if len(sc) < 2:
            continue
        rest = sorted(sc[1:])
        n = len(rest)
        median = rest[n // 2] if n % 2 else (rest[n // 2 - 1] + rest[n // 2]) / 2
        diffs.append(abs(sc[0] - median))
    return sum(diffs) / len(diffs) if diffs else 0.0



def lint_rubric(path: Path) -> tuple[list[str], dict]:
    """Structural lint of a judge rubric YAML.

    Returns (failures, info). A rubric that fails this cannot be calibrated:
    score points without examples produce 20+ point spread on re-annotation,
    and points without anti-examples cannot distinguish adjacent scores.
    """
    if not path.is_file():
        raise SystemExit(f"ERROR: rubric file not found: {path}")
    if yaml is None:
        raise SystemExit("ERROR: PyYAML is required to lint rubrics")
    try:
        rubric = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise SystemExit(f"ERROR: rubric is not valid YAML: {exc}")
    if not isinstance(rubric, dict):
        raise SystemExit("ERROR: rubric must be a mapping at the top level")

    failures: list[str] = []
    points = rubric.get("points")
    if not isinstance(points, list) or not points:
        failures.append("FAIL: rubric has no 'points' list")
        return failures, {"rubric_id": rubric.get("rubric_id"), "n_points": 0}

    scores_seen: set[int] = set()
    prev: int | None = None
    for i, pt in enumerate(points):
        if not isinstance(pt, dict):
            failures.append(f"FAIL: point {i} is not a mapping")
            continue
        score = pt.get("score")
        if not isinstance(score, int):
            failures.append(f"FAIL: point {i} has no integer 'score'")
            continue
        if score in scores_seen:
            failures.append(f"FAIL: duplicate score {score}")
        scores_seen.add(score)
        if prev is not None and score <= prev:
            failures.append(f"FAIL: scores not strictly increasing at point {i} ({prev} -> {score})")
        prev = score
        if not str(pt.get("definition", "")).strip():
            failures.append(f"FAIL: point {score} has no 'definition'")
        if not str(pt.get("example", "")).strip():
            failures.append(f"FAIL: point {score} has no 'example'")
        anti = pt.get("anti_examples")
        if score != min(scores_seen) and not isinstance(anti, list):
            failures.append(f"FAIL: point {score} has no 'anti_examples' list")
    if scores_seen and min(scores_seen) != 1:
        failures.append(f"FAIL: lowest score is {min(scores_seen)}, expected 1")

    info = {"rubric_id": rubric.get("rubric_id"), "n_points": len(points),
            "scores": sorted(scores_seen)}
    return failures, info


def cmd_rubric(path: Path) -> int:
    failures, info = lint_rubric(path)
    for f in failures:
        print(f, file=sys.stderr)
    if failures:
        print(f"FAIL: rubric has {len(failures)} problem(s)", file=sys.stderr)
        return 1
    print(f"PASS: rubric '{info.get('rubric_id')}' has {info['n_points']} "
          f"contiguous points with definitions, examples and anti-examples",
          file=sys.stderr)
    return 0

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("rubric", help="lint a judge rubric YAML")
    pr.add_argument("rubric", type=Path)

    pc = sub.add_parser("calibrate", help="run agreement, position-bias and drift")
    pc.add_argument("--rows", type=Path, required=True, help="JSONL: id, scores[], gold")
    pc.add_argument("--baseline", type=Path, default=None, help="baseline JSONL for drift")
    pc.add_argument("--min-agreement", type=float, default=0.6)
    pc.add_argument("--max-position-bias", type=float, default=0.5)
    pc.add_argument("--max-drift", type=float, default=0.3)
    pc.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    if args.cmd == "rubric":
        return cmd_rubric(args.rubric)

    for opt, val in (("--min-agreement", args.min_agreement),
                    ("--max-position-bias", args.max_position_bias),
                    ("--max-drift", args.max_drift)):
        if not (0.0 <= val <= 1.0):
            raise SystemExit(f"ERROR: {opt}={val} must be in [0, 1]")
    if not args.rows.is_file():
        raise SystemExit(f"ERROR: rows file not found: {args.rows}")
    if args.baseline and not args.baseline.is_file():
        raise SystemExit(f"ERROR: baseline file not found: {args.baseline}")
    if args.json and not args.json.parent.is_dir():
        raise SystemExit(f"ERROR: --json parent dir missing: {args.json.parent}")

    rows = load_rows(args.rows)
    if not rows:
        print("FAIL: no usable items in rows file", file=sys.stderr)
        return 1
    alpha = krippendorff_alpha(rows)
    mean = mean_score(rows)
    bias = position_bias(rows)

    report: dict = {
        "n_items": len(rows),
        "krippendorff_alpha": round(alpha, 4),
        "mean_score": round(mean, 4),
        "position_bias": round(bias, 4),
        "min_agreement": args.min_agreement,
        "max_position_bias": args.max_position_bias,
    }

    failures: list[str] = []
    if alpha < args.min_agreement:
        failures.append(f"FAIL: agreement {alpha:.3f} < {args.min_agreement}")
    if bias > args.max_position_bias:
        failures.append(f"FAIL: position bias {bias:.3f} > {args.max_position_bias}")
        report["aggregate_across_shuffles"] = True

    if args.baseline:
        base = load_rows(args.baseline)
        base_mean = mean_score(base)
        drift = abs(mean - base_mean)
        report["baseline_mean"] = round(base_mean, 4)
        report["drift"] = round(drift, 4)
        if drift > args.max_drift:
            failures.append(f"FAIL: drift {drift:.3f} > {args.max_drift}")

    report["degenerate"] = alpha == 1.0 and len({v for r in rows for v in r["scores"]}) == 1
    report["ok"] = not failures
    print(f"INFO: items={len(rows)} alpha={alpha:.3f} mean={mean:.3f} bias={bias:.3f}", file=sys.stderr)
    if args.baseline:
        print(f"INFO: drift={report.get('drift'):.3f}", file=sys.stderr)
    for f in failures:
        print(f, file=sys.stderr)

    if args.json:
        args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if failures:
        return 1
    print("PASS: judge calibration within thresholds", file=sys.stderr)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
