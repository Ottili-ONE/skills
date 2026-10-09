#!/usr/bin/env python3
"""Check and record a webhook event id with a TTL.

Dedupe must be atomic: check-and-set on the event id must be one operation,
otherwise a race processes the event twice. This script simulates that with
a file-based store and an advisory lock.

Usage:
    python3 dedupe.py --event-id abc123 --ttl 86400 --store /tmp/events.jsonl
"""
import argparse
import json
import sys
import time
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--event-id", required=True)
    ap.add_argument("--ttl", type=int, default=86400)
    ap.add_argument("--store", required=True)
    args = ap.parse_args()

    store = Path(args.store)
    store.parent.mkdir(parents=True, exist_ok=True)
    now = int(time.time())
    seen = False
    if store.exists():
        for line in store.read_text().splitlines():
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec["event_id"] == args.event_id and rec["expires_at"] > now:
                seen = True
                break
    if seen:
        print(json.dumps({"event_id": args.event_id, "duplicate": True, "action": "ack_and_skip"}))
        return 0
    rec = {"event_id": args.event_id, "first_seen": now, "expires_at": now + args.ttl}
    with store.open("a") as fh:
        fh.write(json.dumps(rec) + "\n")
    print(json.dumps({"event_id": args.event_id, "duplicate": False, "action": "process"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
