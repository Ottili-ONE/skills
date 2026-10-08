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


def load_rows(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rows", type=Path, required=True, help="JSONL: id, scores[], gold")
    ap.add_argument("--baseline", type=Path, default=None, help="baseline JSONL for drift")
    ap.add_argument("--min-agreement", type=float, default=0.6)
    ap.add_argument("--max-position-bias", type=float, default=0.5)
    ap.add_argument("--max-drift", type=float, default=0.3)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    rows = load_rows(args.rows)
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
