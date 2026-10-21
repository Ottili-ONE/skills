#!/usr/bin/env python3
"""Check a STATUS.md for false-done claims.

Two grammars are understood, because the product repositories write two:

* the buckets of this skill — DONE, VERIFIED, IN_PROGRESS, BLOCKED, FALSE_DONE.
  A claim in DONE or VERIFIED must name an evidence pointer that (a) exists on
  disk, (b) is non-empty and (c) can be checked in under 60 seconds;
* the claim table of the product repositories — a row that asserts a success
  must name the command that was run, the exit code it returned and the log
  file that proves it (see ``status_tables.py``).

The grammar is detected automatically; ``--format`` forces one.

Usage:
  python3 check_status_evidence.py STATUS.md [--root .] [--json] [--format auto|bucket|table]
Exit 0 = no false-done claims; 1 = findings; 2 = usage error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import status_tables  # noqa: E402  (the skill ships both files side by side)

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
        if mev and buckets[current]:
            buckets[current][-1]["evidence"] = mev.group("evidence")
            continue
        # Every bucket accepts claims. DONE/VERIFIED/FALSE_DONE additionally require
        # an evidence pointer (checked in main); IN_PROGRESS/BLOCKED additionally
        # require a blocker/owner so a stranded claim is visible.
        m = CLAIM_RE.match(line)
        if m:
            ev = EVIDENCE_RE.search(m.group("text"))
            buckets[current].append(
                {"checked": m.group("checked").lower() == "x",
                 "text": m.group("text").strip(),
                 "evidence": ev.group("evidence").strip() if ev else ""}
            )
            continue
        # A bare list item ("- prose") is still a claim: under DONE or VERIFIED it is
        # prose with no evidence and is FALSE_DONE. Without this the parser silently
        # drops every uncheckboxed line, so a lying STATUS.md reads as clean.
        if re.match(r"^\s*-\s+\S", line):
            buckets[current].append(
                {"checked": False, "text": line.strip().lstrip("- ").strip(),
                 "evidence": ""}
            )
    return buckets


BUCKET_HEADER_RE = re.compile(
    r"^##\s+(DONE|VERIFIED|IN_PROGRESS|BLOCKED|FALSE_DONE)\s*$", re.IGNORECASE | re.MULTILINE
)


def detect_format(text: str) -> str:
    """Return "bucket", "table" or "unknown" for the grammar a file uses."""
    if BUCKET_HEADER_RE.search(text):
        return "bucket"
    if status_tables.tables(text):
        return "table"
    return "unknown"


def table_findings(text: str, root: Path) -> tuple[list[dict], int]:
    """Check the claim tables of a STATUS.md.

    A claim is a row that asserts a success. It must name the command that was
    run, the exit code that command returned and the log file that proves it;
    a log file that does not exist proves nothing.
    """
    findings: list[dict] = []
    claim_rows = status_tables.claims(text)
    for claim in claim_rows:
        problems: list[str] = []
        if not claim["commands"]:
            problems.append("no command")
        if claim["exit_code"] is None:
            problems.append("no exit code")
        if not claim["paths"]:
            problems.append("no log path")
        else:
            for path in claim["paths"]:
                if not (root / path).exists():
                    problems.append(f"log path not found: {path}")
        if problems:
            findings.append(
                {"line": claim["line"], "claim": claim["claim"], "problems": problems}
            )
    return findings, len(claim_rows)


def report_table(status: str, text: str, root: Path, as_json: bool) -> int:
    """Report the findings of the claim-table grammar."""
    findings, checked = table_findings(text, root)
    if as_json:
        print(json.dumps({
            "status": "fail" if findings else "ok",
            "file": status,
            "format": "table",
            "rows_checked": checked,
            "findings": findings,
        }, indent=2, sort_keys=True))
        return 1 if findings else 0
    if findings:
        print(f"FAIL: {status} — {len(findings)} unverified row(s)", file=sys.stderr)
        for finding in findings:
            print(f"  - line {finding['line']}: {finding['claim'] or '(empty)'}", file=sys.stderr)
            for problem in finding["problems"]:
                print(f"      {problem}", file=sys.stderr)
        return 1
    print(f"ok: {status} — all {checked} claim rows verified")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("status", help="STATUS.md file")
    ap.add_argument("--root", default=".", help="root for resolving relative evidence paths")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    ap.add_argument(
        "--format",
        choices=("auto", "bucket", "table"),
        default="auto",
        help="the grammar of the file (auto detects buckets first, then tables)",
    )
    args = ap.parse_args()

    try:
        # A status file that is not valid UTF-8 is a broken file, not a reason
        # to crash: the claims that can be read are still worth judging.
        text = Path(args.status).read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        print(f"FAIL: {args.status}: cannot read ({exc})", file=sys.stderr)
        return 2

    root = Path(args.root).resolve()
    fmt = detect_format(text) if args.format == "auto" else args.format
    if fmt == "unknown":
        print(
            f"FAIL: {args.status}: no recognisable status format "
            "(no bucket headers and no claim table)",
            file=sys.stderr,
        )
        return 2
    if fmt == "table":
        return report_table(args.status, text, root, args.json)

    buckets = parse_status(text)

    findings: list[dict] = []
    for bucket in ("DONE", "VERIFIED"):
        for claim in buckets[bucket]:
            # VERIFIED means "the check ran and passed, but the change is not yet
            # integrated". It is a real status, not a synonym for DONE, so it must
            # carry its own evidence pointer — otherwise it is FALSE_DONE.
            if bucket == "VERIFIED" and not claim["checked"]:
                findings.append({"bucket": bucket, "claim": claim["text"][:60],
                                 "reason": "VERIFIED claim must be a checked item with an evidence pointer"})
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
    # A bare list item (no checkbox) under DONE or VERIFIED is prose, not a claim with
    # evidence: the skill's whole point is that "it's basically done" is FALSE_DONE.
    # Checkbox-less lines under other buckets are legitimate prose, so they are left alone.
    for bucket in ("DONE", "VERIFIED"):
        for claim in buckets[bucket]:
            if not claim["checked"] and not claim["evidence"]:
                findings.append({"bucket": bucket, "claim": claim["text"][:60],
                                 "reason": "prose claim with no evidence pointer"})
    # IN_PROGRESS must name a blocker, BLOCKED must name an owner and a question.
    # Without them the claim is stranded: nobody knows what is stuck or who to ask.
    for claim in buckets["IN_PROGRESS"]:
        if not re.search(r"blocker:", claim["text"], re.IGNORECASE):
            findings.append({"bucket": "IN_PROGRESS", "claim": claim["text"][:60],
                             "reason": "no blocker named"})
    for claim in buckets["BLOCKED"]:
        if not re.search(r"owner:", claim["text"], re.IGNORECASE):
            findings.append({"bucket": "BLOCKED", "claim": claim["text"][:60],
                             "reason": "no owner named"})
        elif not re.search(r"question:", claim["text"], re.IGNORECASE):
            findings.append({"bucket": "BLOCKED", "claim": claim["text"][:60],
                             "reason": "no next question named"})
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
            "format": "bucket",
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
