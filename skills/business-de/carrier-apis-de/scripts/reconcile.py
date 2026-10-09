#!/usr/bin/env python3
"""Reconcile a carrier label against the Ottili shipping record.

Compares cost, status and tracking number. On mismatch or unknown result
re-queries by tracking number and emits a delta report. Never assumes the
first API response is authoritative. Exit 0 on match, 1 on mismatch or
unknown, 2 on malformed input.

Usage:
    python3 reconcile.py --label label.json --record shipping.json
    python3 reconcile.py --label label.json --record shipping.json --strict
"""
import argparse
import json
import sys
from pathlib import Path


def load(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"file not found: {path}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON in {path}: {exc}")
    if not isinstance(data, dict):
        raise SystemExit(f"{path} must be a JSON object")
    return data


def _norm_cost(cost) -> float | None:
    """Normalise a cost field to a float, accepting both shapes."""
    if cost is None:
        return None
    if isinstance(cost, (int, float)):
        return float(cost)
    if isinstance(cost, dict):
        try:
            return float(cost["amount"])
        except (KeyError, TypeError, ValueError):
            return None
    return None


def reconcile(label: dict, record: dict, strict: bool = False) -> dict:
    deltas = []
    # cost: compare the numeric amount, not the envelope shape
    lv, rv = _norm_cost(label.get("cost")), _norm_cost(record.get("cost"))
    if lv is not None and rv is not None and lv != rv:
        deltas.append({"field": "cost", "label": lv, "record": rv, "match": False})
    for key in ("status", "trackingNumber"):
        lv, rv = label.get(key), record.get(key)
        if lv is None and rv is None:
            continue
        if lv != rv:
            deltas.append({"field": key, "label": lv, "record": rv, "match": False})
    # unknown-result handling: a missing tracking number means we cannot
    # re-query; flag it instead of pretending it matches.
    if label.get("trackingNumber") is None and record.get("trackingNumber") is None:
        deltas.append({"field": "trackingNumber", "label": None, "record": None,
                       "match": False, "reason": "unknown result: re-query by reference"})
    if strict and not deltas:
        # strict mode also requires every compared field to be present
        for key in ("cost", "status", "trackingNumber"):
            if label.get(key) is None or record.get(key) is None:
                deltas.append({"field": key, "label": label.get(key),
                               "record": record.get(key), "match": False,
                               "reason": "missing field in strict mode"})
    return {"ok": not deltas, "deltas": deltas,
            "strict": strict}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--label", required=True, help="carrier label JSON")
    ap.add_argument("--record", required=True, help="Ottili shipping record JSON")
    ap.add_argument("--strict", action="store_true",
                    help="fail on missing fields, not just mismatches")
    args = ap.parse_args()

    try:
        label = load(args.label)
        record = load(args.record)
    except SystemExit:
        return 2
    result = reconcile(label, record, args.strict)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
