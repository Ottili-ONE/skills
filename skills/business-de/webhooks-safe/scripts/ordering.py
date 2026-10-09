#!/usr/bin/env python3
"""Preserve per-stream delivery order for inbound webhooks.

Ordering is enforced *within a single delivery stream* (one provider +
one account), never globally. Two independent providers may interleave. An
out-of-sequence event is held until the missing event arrives or the
provider's replay window expires.

Usage:
    python3 ordering.py --stream github:ottili --seq 3 --payload body.json --store /tmp/order.jsonl
    python3 ordering.py --stream github:ottili --seq 3 --payload body.json --store /tmp/order.jsonl --replay-seconds 86400 --now 1700000000
"""
import argparse
import json
import sys
import time
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from common import load_config  # noqa: E402


def load_state(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_state(path: str, state: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=2), encoding="utf-8")


def decide(stream: str, seq: int, now: int, replay_seconds: int,
           state: dict) -> dict:
    last = state.get("last_seq", 0)
    held = state.get("held", {})
    if seq <= last:
        return {"action": "duplicate_or_old", "seq": seq, "last_seq": last,
                "reason": "already processed"}
    if seq == last + 1:
        # in order: process, release any held events that now chain
        released = []
        next_seq = seq + 1
        while str(next_seq) in held:
            released.append({"seq": next_seq, "payload": held.pop(str(next_seq))})
            next_seq += 1
        state["last_seq"] = next_seq - 1
        return {"action": "process", "seq": seq, "released": released}
    # out of order: hold until the gap fills or the replay window expires
    held[str(seq)] = "held"
    expired = []
    for s in list(held):
        if now - int(s) > replay_seconds:
            expired.append(int(s))
            held.pop(s)
    return {"action": "hold", "seq": seq, "held_count": len(held),
            "expired": expired,
            "reason": "waiting for missing event or replay-window expiry"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stream", required=True, help="provider:account")
    ap.add_argument("--seq", type=int, required=True, help="sequence number")
    ap.add_argument("--payload", required=True, help="file with the raw body")
    ap.add_argument("--store", required=True, help="state file")
    ap.add_argument("--replay-seconds", type=int, default=86400)
    ap.add_argument("--now", type=int, default=0, help="unix ts (0 = time.time())")
    args = ap.parse_args()

    payload = Path(args.payload).read_bytes()
    now = args.now or int(time.time())
    state = load_state(args.store)
    result = decide(args.stream, args.seq, now, args.replay_seconds, state)
    if result["action"] == "process":
        save_state(args.store, state)
    print(json.dumps({"stream": args.stream, **result}, indent=2, ensure_ascii=False))
    # process and duplicate_or_old are both "handled"; hold/expiry are not
    return 0 if result["action"] in ("process", "duplicate_or_old") else 1


if __name__ == "__main__":
    sys.exit(main())
