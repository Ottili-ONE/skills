#!/usr/bin/env python3
"""Best-of-N jailbreak attempt cap for browser-agent runs.

The cap is a *count*, not a suggestion: exhausting it stops the run and
reports the cap, never silently switches to a different element or retries
forever. This script is the counter; the agent checks it before every
repeated action on a page that keeps refusing.

Usage:
  python3 bon_cap.py --task t1 --attempt click          # record one attempt
  python3 bon_cap.py --task t1 --check                   # is the run still allowed?
  python3 bon_cap.py --task t1 --reset                   # clear the counters

State lives in a JSON file (default .bon_cap.json in CWD, --state to override).
Fully offline and deterministic. Exit 0 allowed, 1 cap hit, 2 usage error.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PER_TASK = 50
PER_HOUR = 300


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load(path: Path) -> dict:
    if not path.is_file():
        return {"tasks": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"FAIL: state file is not valid JSON: {exc}", file=sys.stderr)
        return {"_bad": True}


def save(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def current_hour_bucket(state: dict) -> list[str]:
    """Return the list of attempt timestamps in the current rolling hour."""
    try:
        last = datetime.fromisoformat(state.get("hour_since", "2000-01-01T00:00:00+00:00"))
    except ValueError:
        return []
    if (datetime.now(timezone.utc) - last).total_seconds() >= 3600:
        return []
    return list(state.get("hour_attempts", []))


def cmd_attempt(state: dict, task: str, action: str) -> int:
    if state.get("_bad"):
        print("FAIL: state file unreadable", file=sys.stderr)
        return 2
    tasks = state.setdefault("tasks", {})
    t = tasks.setdefault(task, {"count": 0, "actions": []})
    t["count"] += 1
    t["actions"].append({"at": now(), "action": action})
    state["hour_since"] = now()
    state["hour_attempts"] = current_hour_bucket(state) + [now()]
    task_hit = t["count"] > PER_TASK
    hour_hit = len(state["hour_attempts"]) > PER_HOUR
    if task_hit or hour_hit:
        print(f"FAIL: cap hit — task {task} at {t['count']}/{PER_TASK}, "
              f"hour at {len(state['hour_attempts'])}/{PER_HOUR}", file=sys.stderr)
        return 1
    print(f"PASS: attempt recorded for {task} ({t['count']}/{PER_TASK} task, "
          f"{len(state['hour_attempts'])}/{PER_HOUR} hour)", file=sys.stderr)
    return 0


def cmd_check(state: dict, task: str) -> int:
    if state.get("_bad"):
        print("FAIL: state file unreadable", file=sys.stderr)
        return 2
    t = state.get("tasks", {}).get(task, {"count": 0})
    hour = len(current_hour_bucket(state))
    if t["count"] > PER_TASK or hour > PER_HOUR:
        print(f"FAIL: cap hit — task {t['count']}/{PER_TASK}, hour {hour}/{PER_HOUR}", file=sys.stderr)
        return 1
    print(f"PASS: under cap — task {t['count']}/{PER_TASK}, hour {hour}/{PER_HOUR}", file=sys.stderr)
    return 0


def cmd_reset(state: dict, task: str) -> int:
    if state.get("_bad"):
        print("FAIL: state file unreadable", file=sys.stderr)
        return 2
    state.setdefault("tasks", {}).pop(task, None)
    print(f"PASS: counters reset for {task}", file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--task", required=True)
    ap.add_argument("--state", type=Path, default=Path(".bon_cap.json"))
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--attempt", metavar="ACTION")
    g.add_argument("--check", action="store_true")
    g.add_argument("--reset", action="store_true")
    args = ap.parse_args()
    state = load(args.state)
    if args.attempt:
        rc = cmd_attempt(state, args.task, args.attempt)
    elif args.check:
        rc = cmd_check(state, args.task)
    else:
        rc = cmd_reset(state, args.task)
    # Persist unconditionally once the state was readable: a missing file is a
    # valid initial state, and skipping the save when the file does not yet
    # exist means the counters never survive to the next call.
    if not state.get("_bad"):
        save(args.state, state)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
