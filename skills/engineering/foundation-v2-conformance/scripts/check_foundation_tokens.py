#!/usr/bin/env python3
"""Check that every raw design value in a consumer resolves to a Foundation token.

A raw literal (hex colour, rgb() function, px/rem/em spacing, numeric font-weight) is
only acceptable when it is *present in the token file* (i.e. token-derived) or sits on a
line exempted by an `ALLOWED` comment marker naming a ticket.

Offline-deterministic: no network, no subprocesses beyond stdlib.
Usage:
  python3 check_foundation_tokens.py --tokens token.json [--allow-comment ALLOWED] <file> [<file> ...]
Exit 0 = all values token-derived; 1 = findings; 2 = usage error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
# URLs and SVG fragment references contain `#`-prefixed tokens that are NOT colours:
#   url(#clip-1)   http://example.com/page#section   #fff in a hash
# Strip these spans before scanning so they do not false-positive as raw colours.
URL_RE = re.compile(r"[a-z]+://[^\s'\"<>]+")
SVG_URL_RE = re.compile(r"url\(\s*#[^\s)]+\s*\)")
RGB_RE = re.compile(r"rgba?\(\s*[\d.%\s,]+\)")
PX_RE = re.compile(r"(?<![\w-])(\d+(?:\.\d+)?)px\b")
REM_RE = re.compile(r"(?<![\w-])(\d+(?:\.\d+)?)rem\b")
EM_RE = re.compile(r"(?<![\w-])(\d+(?:\.\d+)?)em\b")


def _load_tokens(path: Path) -> set[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    values: set[str] = set()

    def walk(node):
        if isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
        elif isinstance(node, str):
            values.add(node)
            m = HEX_RE.search(node)
            if m:
                values.add(m.group(0))

    walk(data)
    return values


def _exempt_lines(text: str, allow_comment: str) -> set[int]:
    """Return the set of 0-based line indices exempted by an ALLOWED comment."""
    exempt: set[int] = set()
    for i, line in enumerate(text.splitlines()):
        if allow_comment and allow_comment in line:
            exempt.add(i)
    return exempt


def _strip_urls(line: str) -> str:
    """Return the line with URL/SVG url() spans blanked, so hash colours inside them
    are not mistaken for raw design values."""
    return URL_RE.sub(lambda m: " " * len(m.group(0)), SVG_URL_RE.sub(lambda m: " " * len(m.group(0)), line))


def check_file(path: Path, tokens: set[str], allow_comment: str) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    exempt = _exempt_lines(text, allow_comment)
    findings: list[str] = []
    for i, line in enumerate(text.splitlines()):
        if i in exempt:
            continue
        scan = _strip_urls(line)
        for m in HEX_RE.finditer(scan):
            if m.group(0) not in tokens:
                findings.append(f"{path}:{i + 1}: raw colour {m.group(0)} not in token set")
        for m in RGB_RE.finditer(line):
            findings.append(f"{path}:{i + 1}: raw colour function {m.group(0)} not token-derived")
        for m in PX_RE.finditer(line):
            if m.group(0) not in tokens:
                findings.append(f"{path}:{i + 1}: raw spacing {m.group(0)} not token-derived")
        for m in REM_RE.finditer(line):
            if m.group(0) not in tokens:
                findings.append(f"{path}:{i + 1}: raw spacing {m.group(0)} not token-derived")
        for m in EM_RE.finditer(line):
            if m.group(0) not in tokens:
                findings.append(f"{path}:{i + 1}: raw spacing {m.group(0)} not token-derived")
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tokens", required=True, help="Foundation token file (JSON)")
    ap.add_argument(
        "--allow-comment",
        default="ALLOWED",
        help="comment marker that exempts a line from the check",
    )
    ap.add_argument("files", nargs="+", help="consumer source files to scan")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON instead of text")
    ap.add_argument("--max-findings", type=int, default=0,
                    help="fail if any single file has more than N findings (0 = no per-file cap)")
    args = ap.parse_args()

    tokens = _load_tokens(Path(args.tokens))
    per_file: dict[str, list[str]] = {}
    findings: list[str] = []
    for f in args.files:
        f_findings = check_file(Path(f), tokens, args.allow_comment)
        per_file[str(Path(f).resolve())] = f_findings
        findings.extend(f_findings)

    if args.json:
        print(json.dumps({
            "status": "fail" if findings else "ok",
            "files_scanned": len(args.files),
            "total_findings": len(findings),
            "findings": findings,
            "per_file": {k: len(v) for k, v in per_file.items()},
        }, indent=2, sort_keys=True))
        return 1 if findings else 0

    if args.max_findings:
        worst = max(per_file.values(), key=len) if per_file else []
        if len(worst) > args.max_findings:
            print(f"FAIL: {Path(args.files[0]).name if args.files else '?'} has "
                  f"{len(worst)} findings, exceeds --max-findings {args.max_findings}")
            for f in worst[:10]:
                print(f"  - {f}")
            return 1

    if findings:
        print(f"FAIL: {len(findings)} raw-value finding(s)")
        for f in findings[:25]:
            print(f"  - {f}")
        if len(findings) > 25:
            print(f"  ... and {len(findings) - 25} more (use --json for the full list)")
        return 1
    print(f"ok: all values in {len(args.files)} file(s) are token-derived")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
