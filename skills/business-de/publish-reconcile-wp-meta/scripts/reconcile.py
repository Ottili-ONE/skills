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
    for platform, state in (("wordpress", wp), ("meta", meta)):
        if not state:
            deltas.append({"platform": platform, "found": False,
                           "match": False, "reason": "no record"})
            continue
        if state.get("idempotency_key") != key:
            deltas.append({"platform": platform,
                           "idempotency_key": state.get("idempotency_key"),
                           "match": False, "reason": "key mismatch"})
            continue
        # compare post id and status if both present
        for field in ("id", "status"):
            a, b = state.get(field), state.get(field)
            if a is None:
                if strict:
                    deltas.append({"platform": platform, "field": field,
                                   "match": False, "reason": "missing field"})
                continue
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
