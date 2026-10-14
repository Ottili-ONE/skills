#!/usr/bin/env python3
"""Idempotency check for an inbound webhook event id.

Webhook providers re-deliver events (at-least-once). This script keeps a
small on-disk ledger of processed event ids and answers "new" or "duplicate".
A duplicate is acked with exit 1 and *no* side effects; the caller must never
re-run the ledger write.

Usage:
    python3 dedup_event.py --event-id evt_abc --ledger /tmp/ledger.jsonl
Exit 0 = new (process it). Exit 1 = duplicate (ack and stop).
"""
import argparse
import json
import sys
from pathlib import Path


def ledger_path(p: str) -> Path:
    path = Path(p)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def seen(path: Path, event_id: str) -> bool:
    if not path.exists():
        return False
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("event_id") == event_id:
            return True
    return False


def record(path: Path, event_id: str) -> None:
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"event_id": event_id}) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--event-id", required=True)
    ap.add_argument("--ledger", required=True, help="jsonl ledger path")
    args = ap.parse_args()

    path = ledger_path(args.ledger)
    if seen(path, args.event_id):
        print(json.dumps({"ok": False, "event_id": args.event_id,
                          "result": "duplicate"}))
        return 1
    record(path, args.event_id)
    print(json.dumps({"ok": True, "event_id": args.event_id,
                      "result": "new"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
