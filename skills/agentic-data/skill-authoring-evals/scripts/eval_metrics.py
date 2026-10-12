#!/usr/bin/env python3
"""Compute trigger-eval metrics from an evals.json and a firing log.

Given an evals.json (should_fire ground truth) and a firing log (one line per
case: "<id> <fired>"), computes precision, recall and output delta and prints a
machine-readable benchmark. Fully offline and deterministic.

stdout: "oks fails warns" plus, with --json, a benchmark object.
Exit 0 when precision and recall meet target, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TARGET_PRECISION = 0.9
TARGET_RECALL = 0.9


def load_evals(path: str) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("evals.json must be a list")
    return data


def load_firings(path: str) -> dict[str, bool]:
    out: dict[str, bool] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            raise ValueError(f"bad firing line: {line!r}")
        val = parts[1].lower()
        if val not in ("0", "1", "true", "false", "yes", "no", "fired", "not fired"):
            raise ValueError(f"bad firing value {parts[1]!r} on line {line!r}")
        out[parts[0]] = val in ("1", "true", "yes", "fired")
    return out


def metrics(evals: list[dict], firings: dict[str, bool]) -> dict:
    tp = fp = tn = fn = 0
    cases = []
    for e in evals:
        eid = e["id"]
        should = bool(e["should_fire"])
        fired = firings.get(eid)
        if fired is None:
            fn += 1  # missing firing record counts as a miss
            cases.append({"id": eid, "should_fire": should, "fired": None,
                          "verdict": "missing"})
            continue
        cases.append({"id": eid, "should_fire": should, "fired": fired,
                      "verdict": "ok"})
        if should and fired:
            tp += 1
        elif should and not fired:
            fn += 1
        elif not should and fired:
            fp += 1
        else:
            tn += 1

    denom_p = tp + fp
    denom_r = tp + fn
    precision = tp / denom_p if denom_p else 0.0
    recall = tp / denom_r if denom_r else 0.0
    return {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "target_precision": TARGET_PRECISION,
        "target_recall": TARGET_RECALL,
        "pass": precision >= TARGET_PRECISION and recall >= TARGET_RECALL,
        "cases": cases,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("evals", help="evals.json path")
    ap.add_argument("firings", help="firing log: '<id> <0|1>' per line")
    ap.add_argument("--json", action="store_true", help="emit benchmark object")
    args = ap.parse_args()

    try:
        evals = load_evals(args.evals)
        firings = load_firings(args.firings)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    m = metrics(evals, firings)
    ok = 1 if m["pass"] else 0
    bad = 0 if m["pass"] else 1
    if args.json:
        print(json.dumps(m))
        return 0 if m["pass"] else 1
    print(f"{ok} {bad} 0")
    if m["pass"]:
        print(f"PASS: precision {m['precision']}, recall {m['recall']}", file=sys.stderr)
    else:
        print(f"FAIL: precision {m['precision']} (target {TARGET_PRECISION}), "
              f"recall {m['recall']} (target {TARGET_RECALL})", file=sys.stderr)
    return 0 if m["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
