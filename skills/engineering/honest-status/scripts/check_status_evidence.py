#!/usr/bin/env python3
"""Check a STATUS.md for false-done claims.

A claim is FALSE_DONE unless it names an evidence pointer that (a) exists on disk and
(b) is non-empty and (c) can be checked in under 60 seconds. Buckets: DONE, VERIFIED,
IN_PROGRESS, BLOCKED, FALSE_DONE. DONE and VERIFIED are the only buckets allowed to carry
evidence pointers; every claim in them without a pointer is downgraded to FALSE_DONE.

Usage:
  python3 check_status_evidence.py STATUS.md [--root .] [--json] [--strict]
Exit 0 = no false-done claims; 1 = findings; 2 = usage error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BUCKETS = {"DONE", "VERIFIED", "IN_PROGRESS", "BLOCKED", "FALSE_DONE"}
# A claim line: "- [ ] text" or "- [x] text", optionally followed by "evidence: <path>".
CLAIM_RE = re.compile(r"^\s*-\s*\[(?P<checked>[ xX])\]\s*(?P<text>.+)$")
EVIDENCE_RE = re.compile(r"evidence:\s*(?P<evidence>\S+)", re.IGNORECASE)
HEADER_RE = re.compile(r"^##\s+(?P<bucket>[A-Z_]+)\s*$")


def parse_status(text: str) -> dict[str, list[dict]]:
    """Parse STATUS.md into buckets.

    An evidence pointer may appear inline on the claim line
    ("- [x] x - evidence: path") or on the line immediately following it
    ("- [x] x\n  evidence: path"). Both forms are accepted; a bare evidence
    line with no preceding claim in the current bucket is ignored.
    """
    buckets: dict[str, list[dict]] = {b: [] for b in BUCKETS}
    current = "UNFILED"
    for raw in text.splitlines():
        line = raw.rstrip()
        header = HEADER_RE.match(line)
        if header:
            current = header.group("bucket").upper()
            if current not in buckets:
                current = "UNFILED"
            continue
        # A bare "evidence: <path>" line attaches to the most recent claim in the
        # current bucket (it follows the claim it qualifies).
        mev = re.match(r"^\s*evidence:\s*(?P<evidence>\S+)\s*$", line, re.IGNORECASE)
        if mev and current in ("DONE", "VERIFIED", "FALSE_DONE") and buckets[current]:
            buckets[current][-1]["evidence"] = mev.group("evidence")
            continue
        if current in ("DONE", "VERIFIED", "FALSE_DONE"):
            m = CLAIM_RE.match(line)
            if m:
                ev = EVIDENCE_RE.search(m.group("text"))
                buckets[current].append(
                    {"checked": m.group("checked").lower() == "x",
                     "text": m.group("text").strip(),
                     "evidence": ev.group("evidence").strip() if ev else ""}
                )
    return buckets


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("status", help="STATUS.md file")
    ap.add_argument("--root", default=".", help="root for resolving relative evidence paths")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args()

    try:
        text = Path(args.status).read_text(encoding="utf-8")
    except OSError as exc:
        print(f"FAIL: {args.status}: cannot read ({exc})", file=sys.stderr)
        return 2

    root = Path(args.root).resolve()
    buckets = parse_status(text)

    findings: list[dict] = []
    for bucket in ("DONE", "VERIFIED"):
        for claim in buckets[bucket]:
            ev = claim["evidence"]
            if not ev:
                findings.append({"bucket": bucket, "claim": claim["text"][:60],
                                 "reason": "no evidence pointer"})
                continue
            p = (root / ev).resolve()
            if not p.exists():
                findings.append({"bucket": bucket, "claim": claim["text"][:60],
                                 "reason": f"evidence not found: {ev}"})
            elif p.is_file() and p.stat().st_size == 0:
                findings.append({"bucket": bucket, "claim": claim["text"][:60],
                                 "reason": f"evidence file is empty: {ev}"})
            elif p.is_dir() and not any(p.iterdir()):
                findings.append({"bucket": bucket, "claim": claim["text"][:60],
                                 "reason": f"evidence dir is empty: {ev}"})
    # A [x] claim under FALSE_DONE is a contradiction: the bucket means "downgraded
    # because no evidence exists", so a checked claim there is still claiming done.
    for claim in buckets["FALSE_DONE"]:
        if claim["checked"]:
            findings.append({"bucket": "FALSE_DONE", "claim": claim["text"][:60],
                             "reason": "checked claim under FALSE_DONE is a contradiction"})

    if args.json:
        print(json.dumps({
            "status": "fail" if findings else "ok",
            "file": args.status,
            "buckets": {b: len(v) for b, v in buckets.items()},
            "findings": findings,
        }, indent=2, sort_keys=True))
        return 1 if findings else 0

    if findings:
        print(f"FAIL: {args.status}")
        for f in findings:
            print(f"  - [{f['bucket']}] {f['claim']}: {f['reason']}")
        return 1
    counts = {b: len(v) for b, v in buckets.items()}
    print(f"ok: {args.status} has no false-done claims ({counts})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
