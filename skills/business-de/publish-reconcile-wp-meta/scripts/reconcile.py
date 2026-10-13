#!/usr/bin/env python3
"""Reconcile WordPress vs Meta state when a publish result is unknown.

Neither API guarantees exactly-once delivery, so the skill re-queries both
platforms by the client idempotency key and compares state. Never assume the
first response is authoritative. Emits a delta report; exit 0 on match, 1 on
mismatch or unknown, 2 on malformed input.

Usage:
    python3 reconcile.py --key ORD-1 --wp post.json --meta post.json
    python3 reconcile.py --key ORD-1 --wp post.json --meta post.json --strict
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


def reconcile(key: str, wp: dict, meta: dict, strict: bool = False) -> dict:
    deltas = []
    platforms = {"wordpress": wp, "meta": meta}
    for platform, state in platforms.items():
        if not state:
            deltas.append({"platform": platform, "found": False,
                           "match": False, "reason": "no record"})
            continue
        if state.get("idempotency_key") != key:
            deltas.append({"platform": platform,
                           "idempotency_key": state.get("idempotency_key"),
                           "match": False, "reason": "key mismatch"})
            continue
        for field in ("id", "status"):
            if state.get(field) is None:
                if strict:
                    deltas.append({"platform": platform, "field": field,
                                   "match": False, "reason": "missing field"})
                continue
    # Cross-platform comparison: the old code read the same state twice
    # (`state.get(field), state.get(field)`) and never compared WordPress
    # against Meta at all. Compare the two platforms field by field.
    #
    # An "unknown result" is when BOTH platforms report nothing for a field
    # (a timeout on both, or neither ever published). That is NOT a match —
    # it is the case the skill exists for, and it must be flagged. Only a
    # genuine, identical, non-null value on both platforms is a match.
    for field in ("id", "status"):
        wv, mv = wp.get(field), meta.get(field)
        if wv is None and mv is None:
            deltas.append({"field": field, "wordpress": wv, "meta": mv,
                           "match": False,
                           "reason": "unknown result on both platforms — "
                                     "re-query by idempotency key"})
            continue
        if wv is None or mv is None:
            if strict:
                deltas.append({"field": field, "wordpress": wv, "meta": mv,
                               "match": False, "reason": "missing field"})
            continue
        if wv != mv:
            deltas.append({"field": field, "wordpress": wv, "meta": mv,
                           "match": False, "reason": "state differs between platforms"})
    if not deltas:
        return {"ok": True, "key": key, "deltas": []}
    return {"ok": False, "key": key, "deltas": deltas, "strict": strict}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--key", required=True, help="client idempotency key")
    ap.add_argument("--wp", help="WordPress state JSON")
    ap.add_argument("--meta", help="Meta state JSON")
    ap.add_argument("--strict", action="store_true",
                    help="fail on missing fields, not just mismatches")
    args = ap.parse_args()

    try:
        wp = load(args.wp) if args.wp else {}
        meta = load(args.meta) if args.meta else {}
    except SystemExit:
        return 2
    result = reconcile(args.key, wp, meta, args.strict)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
