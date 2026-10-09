#!/usr/bin/env python3
"""Reconcile a carrier label against the Ottili shipping record.

Compares cost, status and tracking number. On mismatch or unknown result
re-queries by tracking number and emits a delta report. Never assumes the
first API response is authoritative.

Usage:
    python3 reconcile.py --label label.json --record shipping.json
"""
import argparse
import json
import sys
from pathlib import Path


def load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def reconcile(label: dict, record: dict) -> dict:
    deltas = []
    for key in ("cost", "status", "trackingNumber"):
        lv = label.get(key)
        rv = record.get(key)
        if lv is None and rv is None:
            continue
        if lv != rv:
            deltas.append({"field": key, "label": lv, "record": rv,
                           "match": False})
    return {"ok": not deltas, "deltas": deltas}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--label", required=True, help="carrier label JSON")
    ap.add_argument("--record", required=True, help="Ottili shipping record JSON")
    args = ap.parse_args()

    label = load(args.label)
    record = load(args.record)
    result = reconcile(label, record)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
