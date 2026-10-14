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


def cmd_delta(with_dir: Path, without_dir: Path, min_delta: float = 0.05) -> int:
    """Compare with_skill vs without_skill outputs and report the delta.

    A skill that produces output identical to the baseline did nothing; a skill
    that makes output worse is worse than no skill. Reads one text file per case
    (<case_id>.txt) from each directory. Fully offline.
    """
    if not with_dir.is_dir():
        print(f"FAIL: with_skill dir not found: {with_dir}", file=sys.stderr)
        return 2
    if not without_dir.is_dir():
        print(f"FAIL: without_skill dir not found: {without_dir}", file=sys.stderr)
        return 2
    with_files = {p.stem: p for p in with_dir.glob("*.txt")}
    without_files = {p.stem: p for p in without_dir.glob("*.txt")}
    cases = sorted(set(with_files) & set(without_files))
    if not cases:
        print("FAIL: no case id present in both directories", file=sys.stderr)
        return 1
    missing = sorted(set(without_files) - set(with_files)) + sorted(set(with_files) - set(without_files))
    for m in missing:
        print(f"FAIL: case {m} missing from one side (baseline incomplete)", file=sys.stderr)
    failures = 0
    for cid in cases:
        w = with_files[cid].read_text(encoding="utf-8")
        b = without_files[cid].read_text(encoding="utf-8")
        if w == b:
            print(f"FAIL: case {cid} output identical to baseline -- skill did nothing", file=sys.stderr)
            failures += 1
        else:
            ratio = abs(len(w) - len(b)) / max(1, max(len(w), len(b)))
            if ratio < min_delta:
                print(f"WARN: case {cid} output delta {ratio:.3f} below {min_delta}", file=sys.stderr)
            else:
                print(f"INFO: case {cid} output changed ({ratio:.0%} length delta)", file=sys.stderr)
    if failures:
        print(f"FAIL: {failures}/{len(cases)} cases identical to baseline", file=sys.stderr)
        return 1
    print(f"PASS: all {len(cases)} cases differ from baseline", file=sys.stderr)
    return 0


def cmd_split(evals_path: Path, train_ratio: float = 0.7) -> int:
    """Verify a train/validation split exists and is not degenerate.

    A single eval set used for both tuning and declaring success is overfitting.
    Expects evals.json to carry a `split` field per case (`train` or `val`).
    """
    try:
        evals = json.loads(evals_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: cannot read evals: {exc}", file=sys.stderr)
        return 2
    if not isinstance(evals, list) or not evals:
        print("FAIL: evals must be a non-empty list", file=sys.stderr)
        return 2
    splits = [str(e.get("split", "")).lower() for e in evals if isinstance(e, dict)]
    if not any(s in ("train", "val", "validation") for s in splits):
        print("FAIL: no case carries a `split` field -- you tuned and declared on the same set", file=sys.stderr)
        return 1
    train = [e for e in evals if str(e.get("split", "")).lower() == "train"]
    val = [e for e in evals if str(e.get("split", "")).lower() in ("val", "validation")]
    if not train or not val:
        print("FAIL: both train and val splits must be non-empty", file=sys.stderr)
        return 1
    print(f"PASS: {len(train)} train / {len(val)} val cases", file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("metrics")
    p.add_argument("evals")
    p.add_argument("firings")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("delta")
    p.add_argument("with_dir", type=Path)
    p.add_argument("without_dir", type=Path)
    p.add_argument("--min-delta", type=float, default=0.05)

    p = sub.add_parser("split")
    p.add_argument("evals", type=Path)
    p.add_argument("--train-ratio", type=float, default=0.7)

    args = ap.parse_args()
    if args.cmd == "metrics":
        try:
            evals = load_evals(args.evals)
            firings = load_firings(args.firings)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"FAIL: {exc}", file=sys.stderr)
            return 2
        m = metrics(evals, firings)
        if args.json:
            print(json.dumps(m))
        print(f"{1 if m['pass'] else 0} {0 if m['pass'] else 1} 0")
        if m["pass"]:
            print(f"PASS: precision {m['precision']}, recall {m['recall']}", file=sys.stderr)
        else:
            print(f"FAIL: precision {m['precision']} (target {TARGET_PRECISION}), "
                  f"recall {m['recall']} (target {TARGET_RECALL})", file=sys.stderr)
        return 0 if m["pass"] else 1
    if args.cmd == "delta":
        return cmd_delta(args.with_dir, args.without_dir, args.min_delta)
    if args.cmd == "split":
        return cmd_split(args.evals, args.train_ratio)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())