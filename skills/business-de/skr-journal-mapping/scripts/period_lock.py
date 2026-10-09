#!/usr/bin/env python3
"""Lock a period and enforce it technically: flag + approval record + override.

A period lock is a policy decision, but the skill enforces it in code. Once
locked, no new bookings may be added to the period without an override that
carries documented evidence of review.

Usage:
    python3 period_lock.py --period 2026-12 --action lock --approver "Tax Advisor"
    python3 period_lock.py --period 2026-12 --action status
    python3 period_lock.py --period 2026-12 --action override --evidence "review-2026-12-01.md"
"""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

PERIOD_RE = re.compile(r"^(?:\d{6}|\d{4}-\d{2})$")  # YYYYMM or YYYY-MM


def load_state(path):
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"periods": {}}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--period", required=True, help="YYYYMM")
    ap.add_argument("--action", required=True,
                    choices=["lock", "status", "override", "unlock"])
    ap.add_argument("--approver", default="")
    ap.add_argument("--reason", default="")
    ap.add_argument("--evidence", default="")
    ap.add_argument("--state", default="period_lock_state.json")
    args = ap.parse_args()

    if not PERIOD_RE.match(args.period):
        print(json.dumps({"ok": False, "error": "period must be YYYYMM"},
                         indent=2, ensure_ascii=False))
        return 1

    state_path = Path(args.state)
    state = load_state(state_path)
    periods = state.setdefault("periods", {})
    rec = periods.get(args.period, {"locked": False, "history": []})

    if args.action == "status":
        print(json.dumps({"ok": True, "period": args.period, **rec},
                         indent=2, ensure_ascii=False))
        return 0

    if args.action == "lock":
        if rec.get("locked"):
            print(json.dumps({"ok": True, "period": args.period,
                              "already_locked": True}, indent=2, ensure_ascii=False))
            return 0
        if not args.approver:
            print(json.dumps({"ok": False, "error": "lock requires --approver"},
                             indent=2, ensure_ascii=False))
            return 1
        rec["locked"] = True
        rec["locked_at"] = str(date.today())
        rec["locked_by"] = args.approver
        rec["lock_reason"] = args.reason or "period-end closure"
        rec["history"].append({"action": "lock", "at": rec["locked_at"],
                               "by": args.approver})
        periods[args.period] = rec
        state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False),
                              encoding="utf-8")
        print(json.dumps({"ok": True, "period": args.period, "locked": True},
                         indent=2, ensure_ascii=False))
        return 0

    if args.action == "override":
        if not rec.get("locked"):
            print(json.dumps({"ok": False,
                              "error": "period is not locked; nothing to override"},
                             indent=2, ensure_ascii=False))
            return 1
        if not args.evidence:
            print(json.dumps({"ok": False,
                              "error": "override requires --evidence (documented review)"},
                             indent=2, ensure_ascii=False))
            return 1
        rec["override"] = {"at": str(date.today()), "by": args.approver,
                           "evidence": args.evidence,
                           "reason": args.reason or "unspecified"}
        rec["history"].append({"action": "override", "at": rec["override"]["at"],
                               "by": args.approver, "evidence": args.evidence})
        periods[args.period] = rec
        state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False),
                              encoding="utf-8")
        print(json.dumps({"ok": True, "period": args.period, "overridden": True},
                         indent=2, ensure_ascii=False))
        return 0

    if args.action == "unlock":
        if not rec.get("locked"):
            print(json.dumps({"ok": False, "error": "period is not locked"},
                             indent=2, ensure_ascii=False))
            return 1
        rec["locked"] = False
        rec["unlocked_at"] = str(date.today())
        rec["unlocked_by"] = args.approver or "unspecified"
        rec["history"].append({"action": "unlock", "at": rec["unlocked_at"],
                               "by": rec["unlocked_by"]})
        periods[args.period] = rec
        state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False),
                              encoding="utf-8")
        print(json.dumps({"ok": True, "period": args.period, "locked": False},
                         indent=2, ensure_ascii=False))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
