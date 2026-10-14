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

SCHEMA_VERSION = "trajectory-ledger-v1"
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
    if not path.is_file():
        raise SystemExit(f"ERROR: ledger file not found: {path}")
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
    if not isinstance(ev, dict):
        failures.append(f"FAIL: event {idx} is not a JSON object")
        return failures
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
    c = ev.get("cost", {})
    if isinstance(c, dict):
        for k in ("tokens_in", "tokens_out"):
            v = c.get(k)
            if v is not None and (not isinstance(v, (int, float)) or v < 0):
                failures.append(f"FAIL: event {idx} cost.{k} must be a non-negative number")
        for k in ("seconds", "usd"):
            v = c.get(k)
            if v is not None and (not isinstance(v, (int, float)) or v < 0):
                failures.append(f"FAIL: event {idx} cost.{k} must be a non-negative number")
    if "state" in ev:
        if state_hash(ev["state"]) != ev.get("state_hash"):
            failures.append(f"FAIL: event {idx} state_hash does not recompute")
    return failures


def cmd_audit(events: list[dict], strict: bool = False,
               max_usd: float | None = None, max_seconds: float | None = None) -> int:
    failures: list[str] = []
    for i, ev in enumerate(events):
        failures += check_event(ev, i)
    if strict:
        failures += audit_cost_units(events)
    if max_usd is not None or max_seconds is not None:
        total = {"tokens_in": 0, "tokens_out": 0, "seconds": 0.0, "usd": 0.0}
        for ev in events:
            c = ev.get("cost", {})
            for k in total:
                total[k] += c.get(k, 0)
        if max_usd is not None and total["usd"] > max_usd:
            failures.append(
                f"FAIL: total cost ${total['usd']:.4f} exceeds --max-usd ${max_usd:.4f}"
            )
        if max_seconds is not None and total["seconds"] > max_seconds:
            failures.append(
                f"FAIL: total time {total['seconds']:.2f}s exceeds "
                f"--max-seconds {max_seconds:.2f}s"
            )
    # Step monotonicity: a ledger whose steps are not strictly increasing is
    # not a sequence and cannot be replayed deterministically. Reordering
    # events is the most common silent corruption of a hand-written ledger.
    prev_step: int | None = None
    for i, ev in enumerate(events):
        st = ev.get("step")
        if not isinstance(st, int):
            failures.append(f"FAIL: event {i} has non-integer 'step'")
            continue
        if prev_step is not None and st <= prev_step:
            failures.append(
                f"FAIL: event {i} step {st} is not strictly greater than "
                f"event {i - 1} step {prev_step}; the ledger is not a sequence"
            )
        prev_step = st
    # Schema version: a ledger that does not declare the schema it was written
    # against may have been written against a draft and cannot be replayed
    # against the current schema. The first event carries the schema; the
    # header line (schema + run_id) is optional.
    declared = {ev.get("schema") for ev in events if ev.get("schema")}
    if len(declared) > 1:
        failures.append(
            f"FAIL: ledger mixes schema versions {sorted(str(x) for x in declared)}"
        )
    if events and SCHEMA_VERSION not in declared:
        failures.append(
            f"FAIL: no event declares schema '{SCHEMA_VERSION}'; the ledger "
            f"was not written against the current schema and cannot be replayed"
        )
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


def cmd_cost(events: list[dict], max_usd: float | None = None,
             max_seconds: float | None = None) -> int:
    total = {"tokens_in": 0, "tokens_out": 0, "seconds": 0.0, "usd": 0.0}
    for ev in events:
        c = ev.get("cost", {})
        for k in total:
            total[k] += c.get(k, 0)
    print(json.dumps(total))
    failures: list[str] = []
    if max_usd is not None and total["usd"] > max_usd:
        failures.append(f"FAIL: total cost ${total['usd']:.4f} exceeds --max-usd ${max_usd:.4f}")
    if max_seconds is not None and total["seconds"] > max_seconds:
        failures.append(
            f"FAIL: total time {total['seconds']:.2f}s exceeds --max-seconds {max_seconds:.2f}s"
        )
    for f in failures:
        print(f, file=sys.stderr)
    if failures:
        return 1
    print(f"INFO: cost within budget (usd={total['usd']:.4f}, seconds={total['seconds']:.2f})",
          file=sys.stderr)
    return 0


def audit_cost_units(events: list[dict]) -> list[str]:
    """A cost ledger without a unit is not a ledger. Every event that carries
    a cost dict must carry all four units (tokens_in, tokens_out, seconds,
    usd); a partial cost cannot be summed meaningfully and is rejected."""
    failures: list[str] = []
    for i, ev in enumerate(events):
        c = ev.get("cost")
        if not isinstance(c, dict):
            continue
        for k in ("tokens_in", "tokens_out", "seconds", "usd"):
            if k not in c:
                failures.append(f"FAIL: event {i} cost is missing '{k}' (no unit)")
    return failures



def cmd_normalize(events: list[dict], out_path: Path) -> int:
    """Rewrite a ledger with canonical JSON and recomputed state_hash.

    Lets an agent hand-write a trajectory and then have it normalised before
    audit: every line is re-serialised with sort_keys=True and every event that
    carries a `state` gets its `state_hash` recomputed. Events that already have
    a correct hash are left alone. Malformed lines fail the whole run.
    """
    out: list[dict] = []
    for i, ev in enumerate(events):
        if not isinstance(ev, dict):
            print(f"FAIL: event {i} is not a JSON object", file=sys.stderr)
            return 1
        ev = dict(ev)
        if "state" in ev:
            ev["state_hash"] = state_hash(ev["state"])
        out.append(ev)
    with out_path.open("w", encoding="utf-8") as fh:
        for ev in out:
            fh.write(canonical(ev) + "\n")
    print(f"PASS: normalised {len(out)} event(s) to {out_path}", file=sys.stderr)
    return 0


def cmd_record_non_det(ledger_path: Path, step: int, reason: str) -> int:
    """Record a replay divergence as an observe event with non_determinism: true.

    The replay procedure says: on first divergence, record it and stop. This
    subcommand appends that record so the ledger carries the evidence instead
    of the run being silently marked non-reproducible.

    The appended event's `step` is the next step after the last recorded one,
    not the diverging step: the divergence *is* the divergence at `step`, and
    the record itself is a new event that must come after every existing one.
    Passing a step that is not strictly greater than the last recorded step
    would itself break the monotonicity the audit enforces, so it is rejected
    rather than silently appended out of order.
    """
    existing = load_events(ledger_path) if ledger_path.is_file() else []
    last_step = max((e.get("step", -1) for e in existing if isinstance(e.get("step"), int)), default=-1)
    if step <= last_step:
        print(
            f"FAIL: step {step} is not strictly greater than the last recorded "
            f"step {last_step}; the non-determinism record must be appended after "
            f"every existing event",
            file=sys.stderr,
        )
        return 1
    ev = {
        "step": step,
        "timestamp": _now(),
        "type": "observe",
        "non_determinism": True,
        "reason": reason,
        "state": {"divergence_at_step": step, "reason": reason},
        "cost": {"tokens_in": 0, "tokens_out": 0, "seconds": 0.0, "usd": 0.0},
    }
    ev["state_hash"] = state_hash(ev["state"])
    failures = check_event(ev, step)
    if failures:
        for f in failures:
            print(f, file=sys.stderr)
        return 1
    with ledger_path.open("a", encoding="utf-8") as fh:
        fh.write(canonical(ev) + "\n")
    print(f"INFO: recorded non-determinism at step {step}", file=sys.stderr)
    return 0


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("normalize")
    p.add_argument("ledger", type=Path)
    p.add_argument("out", type=Path)

    p = sub.add_parser("record-non-det")
    p.add_argument("ledger", type=Path)
    p.add_argument("step", type=int)
    p.add_argument("reason")

    p = sub.add_parser("append")
    p.add_argument("ledger", type=Path)
    p.add_argument("event")

    p = sub.add_parser("replay")
    p.add_argument("ledger", type=Path)
    p.add_argument("other", type=Path)

    p = sub.add_parser("cost")
    p.add_argument("ledger", type=Path)
    p.add_argument("--max-usd", type=float, default=None,
                   help="reject the run if total USD cost exceeds this")
    p.add_argument("--max-seconds", type=float, default=None,
                   help="reject the run if total wall-clock exceeds this")

    p = sub.add_parser("audit")
    p.add_argument("ledger", type=Path)
    p.add_argument("--strict", action="store_true",
                   help="also require every cost dict to carry all four units")
    p.add_argument("--max-usd", type=float, default=None)
    p.add_argument("--max-seconds", type=float, default=None)

    args = ap.parse_args()
    if args.cmd == "append":
        try:
            ev = json.loads(args.event)
        except json.JSONDecodeError as e:
            print(f"FAIL: event is not valid JSON: {e}", file=sys.stderr)
            return 2
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
    if args.cmd == "normalize":
        events = load_events(args.ledger)
        return cmd_normalize(events, args.out)
    if args.cmd == "record-non-det":
        return cmd_record_non_det(args.ledger, args.step, args.reason)
    if args.cmd == "cost":
        events = load_events(args.ledger)
        return cmd_cost(events, max_usd=args.max_usd, max_seconds=args.max_seconds)
    events = load_events(args.ledger)
    if args.cmd == "audit":
        return cmd_audit(events, strict=args.strict, max_usd=args.max_usd,
                         max_seconds=args.max_seconds)
    if args.cmd == "replay":
        return cmd_replay(events, args.other)
    return cmd_cost(events)


if __name__ == "__main__":
    raise SystemExit(main())
