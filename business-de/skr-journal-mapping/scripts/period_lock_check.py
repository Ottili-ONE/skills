#!/usr/bin/env python3
"""Enforce and audit SKR period locks (Monatsschluss / year-end).

State file (JSON), default <skill>/config/period_lock.json:
  {"period": "2026-12", "locked": false, "locked_at": null,
   "locked_by": "", "reason": "", "approved_by": "",
   "evidence": "", "overrides": []}

Commands:
  --status   print the state; exit 0 locked, 1 open
  --check    exit 0 locked-clean, 1 locked-with-override, 2 not-locked
  --lock     require approved_by + reason + evidence path that exists
  --unlock   require an override record naming the evidence path
  --history print the override log

All amounts/paths are read from the state file or CLI args; nothing is
hardcoded. Deterministic and offline.
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_STATE = SKILL_DIR / "config" / "period_lock.json"


def load(path: Path) -> dict:
    if not path.is_file():
        return {"period": None, "locked": False, "locked_at": None,
                "locked_by": "", "reason": "", "approved_by": "",
                "evidence": "", "overrides": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    tmp.replace(path)


def cmd_status(state: dict, args) -> int:
    print(json.dumps(state, indent=2, ensure_ascii=False))
    return 0 if state.get("locked") else 1


def cmd_check(state: dict, args) -> int:
    if not state.get("locked"):
        print("FAIL period is not locked", file=sys.stderr)
        return 2
    if state.get("overrides"):
        print("FAIL period locked but override present: %s"
              % state["overrides"], file=sys.stderr)
        return 1
    print("OK period %s locked, no override" % state.get("period"))
    return 0


def cmd_lock(state: dict, args) -> int:
    errors = []
    period = args.period or state.get("period")
    if not period:
        errors.append("period required (--period YYYY-MM)")
    approved_by = args.approved_by or state.get("approved_by")
    if not approved_by:
        errors.append("approved_by required (tax advisor name/ID)")
    reason = args.reason or state.get("reason")
    if not reason:
        errors.append("reason required (e.g. Monatsschluss, year-end close)")
    evidence = args.evidence
    if not evidence:
        errors.append("evidence path required on every lock (documented review record)")
    elif not Path(evidence).is_file():
        errors.append(f"evidence path does not exist: {evidence}")
    if errors:
        for e in errors:
            print("FAIL", e, file=sys.stderr)
        return 2
    state.update({
        "period": period, "locked": True,
        "locked_at": date.today().isoformat(),
        "locked_by": args.locked_by or state.get("locked_by") or "agent",
        "reason": reason, "approved_by": approved_by, "evidence": evidence,
    })
    save(Path(args.state), state)
    print("OK period %s locked by %s (approved by %s, evidence %s)"
          % (period, state["locked_by"], approved_by, evidence))
    return 0


def cmd_unlock(state: dict, args) -> int:
    if not state.get("locked"):
        print("FAIL period is not locked", file=sys.stderr)
        return 2
    evidence = args.evidence or ""
    if not evidence or not Path(evidence).is_file():
        print("FAIL unlock requires --evidence pointing at a real file",
              file=sys.stderr)
        return 2
    state.setdefault("overrides", []).append({
        "at": date.today().isoformat(),
        "by": args.by or "agent",
        "reason": args.reason or "override",
        "evidence": evidence,
    })
    state["locked"] = False
    state["unlocked_at"] = date.today().isoformat()
    save(Path(args.state), state)
    print("OK period %s unlocked; override logged" % state.get("period"))
    return 0


def cmd_history(state: dict, args) -> int:
    overrides = state.get("overrides") or []
    if not overrides:
        print("no overrides recorded")
        return 0
    for o in overrides:
        print("- %s by %s: %s (evidence %s)"
              % (o.get("at"), o.get("by"), o.get("reason"), o.get("evidence")))
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="SKR period lock enforcement")
    p.add_argument("--state", default=str(DEFAULT_STATE))
    p.add_argument("--period")
    p.add_argument("--approved-by", dest="approved_by")
    p.add_argument("--locked-by", dest="locked_by")
    p.add_argument("--reason")
    p.add_argument("--evidence")
    p.add_argument("--by")
    p.add_argument("action", choices=["status", "check", "lock", "unlock", "history"])
    args = p.parse_args(argv)
    state = load(Path(args.state))
    return {
        "status": cmd_status,
        "check": cmd_check,
        "lock": cmd_lock,
        "unlock": cmd_unlock,
        "history": cmd_history,
    }[args.action](state, args)


if __name__ == "__main__":
    sys.exit(main())
