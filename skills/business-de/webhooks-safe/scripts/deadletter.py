#!/usr/bin/env python3
"""Move a failed webhook event to the dead-letter queue.

Never silently drop a webhook. The dead-letter record contains the raw
payload, the event id, the failure reason and the timestamp.

Usage:
    python3 deadletter.py --event-id abc --reason 'timeout' --payload body.json --queue /tmp/dl.jsonl
"""
import argparse
import json
import sys
import time
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--event-id", required=True)
    ap.add_argument("--reason", required=True)
    ap.add_argument("--payload", required=True, help="file with the raw payload bytes")
    ap.add_argument("--queue", required=True)
    args = ap.parse_args()

    payload = Path(args.payload).read_bytes()
    record = {"event_id": args.event_id, "reason": args.reason,
              "payload": payload.decode("utf-8", "replace"),
              "timestamp": int(time.time())}
    q = Path(args.queue)
    q.parent.mkdir(parents=True, exist_ok=True)
    with q.open("a") as fh:
        fh.write(json.dumps(record) + "\n")
    print(json.dumps({"event_id": args.event_id, "queued": str(q), "reason": args.reason}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
