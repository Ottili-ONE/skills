#!/usr/bin/env python3
"""Write a PASS/FAIL/BLOCKED result + evidence path into a results JSON.

Usage:
  python3 report_result.py --scenario SCENARIO-1 --outcome PASS --evidence path --criterion "..."
Exit 0 on write; 2 on malformed input.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

VALID = {"PASS", "FAIL", "BLOCKED"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--outcome", required=True, choices=sorted(VALID))
    ap.add_argument("--evidence", required=True)
    ap.add_argument("--criterion", default="")
    ap.add_argument("--rollback", default="")
    ap.add_argument("--output", default="tests/e2e/results.json")
    args = ap.parse_args()

    if args.outcome not in VALID:
        print(f"error: outcome must be one of {sorted(VALID)}", file=sys.stderr)
        return 2

    out = Path(args.output)
    data = json.loads(out.read_text()) if out.is_file() else {"results": []}
    data.setdefault("results", [])
    data["results"] = [r for r in data["results"] if r["scenario"] != args.scenario]
    data["results"].append(
        {
            "scenario": args.scenario,
            "outcome": args.outcome,
            "evidence": args.evidence,
            "criterion": args.criterion,
            "rollback": args.rollback,
        }
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"ok: {args.scenario} -> {args.outcome} ({args.evidence})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
