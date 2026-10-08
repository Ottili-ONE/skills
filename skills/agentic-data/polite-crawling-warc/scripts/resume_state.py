#!/usr/bin/env python3
"""Persist crawl resume state: queue + per-URL last-seen + WARC offset. Offline, deterministic.

Machine-readable summary -> stdout; human detail (FAIL:/PASS:/WARN:/INFO:) -> stderr.
Exit 0 = ok; exit 1 = any FAIL.

Usage:
  python3 resume_state.py --state s.json --add http://x --offset 123
  python3 resume_state.py --state s.json --skip http://x
  python3 resume_state.py --state s.json --load
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return {"seen": {}, "queue": [], "offset": 0}
    except json.JSONDecodeError as e:
        print(f"FAIL: resume state corrupt: {e}", file=sys.stderr)
        return None


def save(path: str, state: dict) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)
    Path(tmp).replace(path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state", required=True)
    ap.add_argument("--add")
    ap.add_argument("--offset", type=int, default=None)
    ap.add_argument("--skip", help="mark a URL as already crawled")
    ap.add_argument("--load", action="store_true")
    ap.add_argument("--reset", action="store_true")
    args = ap.parse_args()

    if args.reset:
        save(args.state, {"seen": {}, "queue": [], "offset": 0})
        print("PASS: state reset", file=sys.stderr)
        return 0

    state = load(args.state)
    if state is None:
        return 1

    if args.load:
        print(json.dumps(state, indent=2))
        print(f"PASS: state loaded ({len(state['seen'])} seen, queue={len(state['queue'])})",
              file=sys.stderr)
        return 0

    if args.add:
        state["seen"][args.add] = _now_iso()
        state["offset"] = args.offset if args.offset is not None else state["offset"]
        if args.add not in state["queue"]:
            state["queue"].append(args.add)
        save(args.state, state)
        print(f"INFO: added {args.add} offset={state['offset']}", file=sys.stderr)
        print("PASS: state saved", file=sys.stderr)
        return 0

    if args.skip:
        state["seen"][args.skip] = _now_iso()
        state["queue"] = [u for u in state["queue"] if u != args.skip]
        save(args.state, state)
        print(f"INFO: skipped {args.skip}", file=sys.stderr)
        print("PASS: state saved", file=sys.stderr)
        return 0

    ap.error("one of --load/--add/--skip/--reset is required")
    return 2


if __name__ == "__main__":
    sys.exit(main())
