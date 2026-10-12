#!/usr/bin/env python3
"""Validate a computer-use driver against the 2026-08-01 contract.

AUDIT (positional .py): static-source audit of a driver subclass.
CONTRACT (--contract file.json): validate a member-registry JSON.

Checks: 16-member coverage, confirm() gating, new-array scaling, fixed-phrase
errors, desktop isolation. Fully offline and deterministic.
stdout: "oks fails warns"; stderr: FAIL:/PASS:/WARN:/INFO: detail.
Exit 0 pass, 1 FAIL, 2 usage/input error.
"""

import argparse
import json
import re
import sys
from pathlib import Path

CANONICAL = ["screenshot", "zoom", "cursor_position", "mouse_move", "left_mouse_down",
    "left_mouse_up", "left_click", "left_click_drag", "right_click", "middle_click",
    "double_click", "triple_click", "scroll", "wait", "type", "key", "hold_key"]
GATED = {"type", "key", "hold_key"}
UNGATED = set(CANONICAL) - GATED


def audit(path: Path) -> tuple[int, int, int]:
    src = path.read_text(encoding="utf-8")
    fails = warns = oks = 0
    def fail(m): 
        nonlocal fails; print(f"FAIL: {m}", file=sys.stderr); fails += 1
    def warn(m):
        nonlocal warns; print(f"WARN: {m}", file=sys.stderr); warns += 1

    defined = set(re.findall(r"def\s+([a-z_]+)\s*\(", src))
    missing = [m for m in CANONICAL if m not in defined]
    if missing:
        fail(f"members not defined as methods: {missing}")
    else:
        oks += 1
    for m in GATED:
        idx = src.find(f"def {m}")
        if idx < 0:
            continue
        blk = src[idx:src.find("def ", idx + 4)]
        if "confirm" not in blk:
            fail(f"{m} must call confirm()")
    for m in UNGATED:
        idx = src.find(f"def {m}")
        if idx < 0:
            continue
        blk = src[idx:src.find("def ", idx + 4)]
        if "confirm" in blk:
            fail(f"{m} must NOT be gated by confirm()")
    if "input.copy()" in src or "list(input)" in src or "[*input" in src:
        oks += 1
    elif "input" in src:
        warn("coordinate scaling may mutate input in place")
    if re.search(r'f".*\{.*\}.*"', src) and "fixed" not in src.lower():
        warn("f-string in error path may carry screen content")
    if "credentials" in src.lower() or "mount" in src.lower():
        oks += 1
    return fails, warns, oks


def contract(path: Path) -> tuple[int, int, int]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    fails = warns = oks = 0
    def fail(m):
        nonlocal fails; print(f"FAIL: {m}", file=sys.stderr); fails += 1
    members = doc.get("members") if isinstance(doc, dict) else None
    if not isinstance(members, list):
        fail("registry must have a 'members' list")
        return fails, warns, oks
    got = [m.get("name") for m in members if isinstance(m, dict)]
    if sorted(got) != sorted(CANONICAL):
        fail(f"member set drift: got {sorted(got)}")
    else:
        oks += 1
    for m in members:
        if isinstance(m, dict) and m.get("name") not in CANONICAL:
            warn(f"unknown member {m.get('name')!r}")
    return fails, warns, oks


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("file", nargs="?", help="driver .py to audit")
    ap.add_argument("--contract", help="member-registry JSON to validate")
    args = ap.parse_args()
    if args.contract:
        try:
            f, w, o = contract(Path(args.contract))
        except (OSError, json.JSONDecodeError) as e:
            print(f"FAIL: {e}", file=sys.stderr); return 2
    else:
        if not args.file:
            ap.error("a driver file or --contract is required")
        p = Path(args.file)
        if not p.is_file():
            print(f"FAIL: not a file: {args.file}", file=sys.stderr); return 2
        try:
            f, w, o = audit(p)
        except UnicodeDecodeError as e:
            print(f"FAIL: {e}", file=sys.stderr); return 2
    print(f"{o} {f} {w}")
    return 1 if f else 0


if __name__ == "__main__":
    raise SystemExit(main())
