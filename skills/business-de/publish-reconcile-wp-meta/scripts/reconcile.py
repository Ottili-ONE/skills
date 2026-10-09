#!/usr/bin/env python3
"""Reconcile WordPress vs Meta state when a publish result is unknown.

Neither API guarantees exactly-once delivery, so the skill re-queries both
platforms by the client idempotency key and compares state. Never assume the
first response is authoritative. Emits a delta report; exit 0 on match, 1 on
mismatch or unknown.

Usage:
    python3 reconcile.py --key ORD-1 --wp post.json --meta post.json
"""
import argparse
import json
import sys
from pathlib import Path


def load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def reconcile(key: str, wp: dict, meta: dict) -> dict:
    deltas = []
    for platform, state in (("wordpress", wp), ("meta", meta)):
        if not state:
            deltas.append({"platform": platform, "found": False,
                           "match": False, "reason": "no record"})
            continue
        if state.get("idempotency_key") != key:
            deltas.append({"platform": platform, "idempotency_key": state.get("idempotency_key"),
                           "match": False, "reason": "key mismatch"})
    if not deltas:
        return {"ok": True, "key": key, "deltas": []}
    return {"ok": False, "key": key, "deltas": deltas}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--key", required=True, help="client idempotency key")
    ap.add_argument("--wp", help="WordPress state JSON")
    ap.add_argument("--meta", help="Meta state JSON")
    args = ap.parse_args()

    wp = load(args.wp) if args.wp else {}
    meta = load(args.meta) if args.meta else {}
    result = reconcile(args.key, wp, meta)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
