#!/usr/bin/env python3
"""Client-side idempotency store for WP/Meta publishing.

Neither WordPress nor Meta natively supports idempotency keys, so the skill
implements idempotency in a reconciliation layer: store the key -> post id
mapping, and on a duplicate key return the stored post id and never create a
second post. The store is append-only JSONL; mutating an entry in place would
break the audit trail.

Usage:
    python3 idempotency_store.py --key ORD-1 --platform wordpress --post-id 42 --store /tmp/ids.jsonl
    python3 idempotency_store.py --key ORD-1 --platform wordpress --lookup --store /tmp/ids.jsonl
"""
import argparse
import json
import sys
import time
from pathlib import Path


def lookup(store: str, key: str, platform: str) -> dict:
    p = Path(store)
    if not p.exists():
        return {"found": False}
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("key") == key and rec.get("platform") == platform:
            return {"found": True, "post_id": rec.get("post_id"),
                    "created_at": rec.get("created_at")}
    return {"found": False}


def record(store: str, key: str, platform: str, post_id) -> dict:
    p = Path(store)
    p.parent.mkdir(parents=True, exist_ok=True)
    rec = {"key": key, "platform": platform, "post_id": str(post_id),
           "created_at": int(time.time())}
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")
    return rec


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--key", required=True, help="client idempotency key")
    ap.add_argument("--platform", required=True, choices=["wordpress", "meta"])
    ap.add_argument("--post-id", help="post id to store (omit with --lookup)")
    ap.add_argument("--lookup", action="store_true", help="look up an existing mapping")
    ap.add_argument("--store", required=True, help="JSONL idempotency store")
    args = ap.parse_args()

    if args.lookup:
        if args.post_id:
            ap.error("--post-id cannot be used with --lookup")
        result = lookup(args.store, args.key, args.platform)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result["found"] else 1
    if not args.post_id:
        ap.error("--post-id is required without --lookup")
    rec = record(args.store, args.key, args.platform, args.post_id)
    print(json.dumps({"ok": True, "record": rec}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
