#!/usr/bin/env python3
"""Trajectory ledger: append, audit, replay and cost aggregation.

Subcommands:
  append  <ledger.jsonl> '<json event>'   append one validated event
  audit   <ledger.jsonl>                  walk the ledger, exit 0 if clean
  replay  <ledger.jsonl> '<jsonl events>' compare hash sequences
  cost    <ledger.jsonl>                  sum the cost ledger

Fully offline and deterministic. Machine-readable counts to stdout,
detail lines prefixed FAIL:/PASS:/INFO: to stderr.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

VALID_TYPES = {"think", "tool", "observe"}
VALID_OUTCOMES = {"pending", "running", "succeeded", "failed", "blocked", "timeout"}
REQUIRED_BY_OUTCOME = {
    "succeeded": "evidence",
    "failed": "reason",
    "blocked": "blocker",
    "timeout": "elapsed_seconds",
}


def canonical(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def state_hash(state: object) -> str:
    return "sha256:" + hashlib.sha256(canonical(state).encode("utf-8")).hexdigest()


def load_events(path: Path) -> list[dict]:
    events: list[dict] = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as exc:
            print(f"FAIL: line {i} is not valid JSON: {exc}", file=sys.stderr)
            raise SystemExit(1)
    return events


def check_event(ev: dict, idx: int) -> list[str]:
    failures: list[str] = []
    for field in ("step", "timestamp", "type", "state_hash", "cost"):
        if field not in ev:
            failures.append(f"FAIL: event {idx} missing mandatory field '{field}'")
    if ev.get("type") not in VALID_TYPES:
        failures.append(f"FAIL: event {idx} has invalid type '{ev.get('type')}'")
    if ev.get("type") == "tool":
        if "args" not in ev:
            failures.append(f"FAIL: event {idx} tool call missing 'args'")
        res = ev.get("result")
        if not isinstance(res, dict) or "exit_code" not in res:
            failures.append(f"FAIL: event {idx} tool call missing 'result.exit_code'")
    outcome = ev.get("outcome")
    if outcome is not None and outcome not in VALID_OUTCOMES:
        failures.append(f"FAIL: event {idx} has invalid outcome '{outcome}'")
    if outcome in REQUIRED_BY_OUTCOME:
        req = REQUIRED_BY_OUTCOME[outcome]
        if req not in ev:
            failures.append(f"FAIL: event {idx} outcome '{outcome}' missing '{req}'")
    if "state" in ev:
        if state_hash(ev["state"]) != ev.get("state_hash"):
            failures.append(f"FAIL: event {idx} state_hash does not recompute")
    return failures


def cmd_audit(events: list[dict]) -> int:
    failures: list[str] = []
    for i, ev in enumerate(events):
        failures += check_event(ev, i)
    if failures:
        for f in failures:
            print(f, file=sys.stderr)
        print(f"FAIL: audit found {len(failures)} problem(s)", file=sys.stderr)
        return 1
    print(f"PASS: audit clean ({len(events)} events)", file=sys.stderr)
    return 0


def cmd_replay(events: list[dict], other_path: Path) -> int:
    other = load_events(other_path)
    mine = [ev.get("state_hash") for ev in events]
    theirs = [ev.get("state_hash") for ev in other]
    n = min(len(mine), len(theirs))
    divergence = None
    for i in range(n):
        if mine[i] != theirs[i]:
            divergence = i
            break
    if divergence is None and len(mine) != len(theirs):
        divergence = n
    if divergence is None:
        print(f"PASS: replay reproduces all {n} hashes", file=sys.stderr)
        return 0
    print(f"FAIL: replay diverges at step {divergence}", file=sys.stderr)
    return 1


def cmd_cost(events: list[dict]) -> int:
    total = {"tokens_in": 0, "tokens_out": 0, "seconds": 0.0, "usd": 0.0}
    for ev in events:
        c = ev.get("cost", {})
        for k in total:
            total[k] += c.get(k, 0)
    print(json.dumps(total))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("append")
    p.add_argument("ledger", type=Path)
    p.add_argument("event")

    p = sub.add_parser("audit")
    p.add_argument("ledger", type=Path)

    p = sub.add_parser("replay")
    p.add_argument("ledger", type=Path)
    p.add_argument("other", type=Path)

    p = sub.add_parser("cost")
    p.add_argument("ledger", type=Path)

    args = ap.parse_args()
    if args.cmd == "append":
        ev = json.loads(args.event)
        ev.setdefault("step", 0)
        if "state" in ev and "state_hash" not in ev:
            ev["state_hash"] = state_hash(ev["state"])
        failures = check_event(ev, ev.get("step", 0))
        for f in failures:
            print(f, file=sys.stderr)
        if failures:
            return 1
        with args.ledger.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(ev, sort_keys=True, ensure_ascii=False) + "\n")
        print(f"INFO: appended step {ev['step']}", file=sys.stderr)
        return 0
    events = load_events(args.ledger)
    if args.cmd == "audit":
        return cmd_audit(events)
    if args.cmd == "replay":
        return cmd_replay(events, args.other)
    return cmd_cost(events)


if __name__ == "__main__":
    raise SystemExit(main())
