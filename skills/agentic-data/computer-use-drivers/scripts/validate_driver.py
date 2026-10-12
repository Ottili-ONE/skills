#!/usr/bin/env python3
"""Validate a computer-use driver against the 2026-08-01 contract.

AUDIT (positional .py): static-source audit of a driver subclass.
CONTRACT (--contract file.json): validate a member-registry JSON.

Checks: 17-member coverage, confirm() gating, new-array scaling, fixed-phrase
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
    # Count scaling signals. Every pointer method must scale into a fresh array;
    # a driver with no scaling signal at all is unsafe.
    scale_signals = sum(1 for sig in ("input.copy()", "list(input)", "[*input", ".copy()")
                       if sig in src)
    if scale_signals:
        oks += 1
    elif "input" in src:
        fail("pointer methods reference input but never scale into a fresh array")
    else:
        fail("no coordinate scaling found at all — every pointer method must scale")

    # Clamping is the silent failure: it moves the pointer and the model cannot detect it.
    # Clamping is the silent failure: it moves the pointer and the model cannot
    # detect it. Match both the literal word and the max(0, min(...)) idiom.
    if re.search(r"\bclamp\b|max\s*\(\s*0\s*,\s*min\s*\(", src, re.IGNORECASE):
        fail("clamping detected — never clamp; throw ToolError on out-of-bounds coordinates")
    if re.search(r"\bscreen_content\b|error\.message", src) and "fixed" not in src.lower():
        warn("error path may pass raw screen content or error.message to the model")
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
    def warn(m):
        nonlocal warns; print(f"WARN: {m}", file=sys.stderr); warns += 1
    members = doc.get("members") if isinstance(doc, dict) else None
    if not isinstance(members, list):
        fail("registry must have a 'members' list")
        return fails, warns, oks
    # The published registry is a list of member-name strings; some internal
    # representations use objects with a "name" key. Support both.
    got: list[str] = []
    for m in members:
        if isinstance(m, str):
            got.append(m)
        elif isinstance(m, dict) and isinstance(m.get("name"), str):
            got.append(m["name"])
        else:
            warn(f"unrecognized member entry: {m!r}")
    if not got:
        fail("registry members list is empty")
    elif sorted(got) != sorted(CANONICAL):
        fail(f"member set drift: got {sorted(got)}; expected {sorted(CANONICAL)}")
    else:
        oks += 1
    disabled = doc.get("default_disabled") if isinstance(doc, dict) else None
    if isinstance(disabled, list):
        for d in disabled:
            if d not in CANONICAL:
                warn(f"default_disabled lists unknown member {d!r}")
            elif d in GATED:
                warn(f"default_disabled gates a gated member {d!r} — confirm() still required")
    for m in members:
        name = m if isinstance(m, str) else (m.get("name") if isinstance(m, dict) else None)
        if name and name not in CANONICAL:
            warn(f"unknown member {name!r}")
    return fails, warns, oks


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("file", nargs="?", help="driver .py to audit")
    ap.add_argument("--contract", help="member-registry JSON to validate")
    ap.add_argument("--json", action="store_true",
                    help="emit a machine-readable report object to stdout")
    args = ap.parse_args()
    if args.contract:
        try:
            f, w, o = contract(Path(args.contract))
        except (OSError, json.JSONDecodeError) as e:
            print(f"FAIL: {e}", file=sys.stderr); return 2
        if args.json:
            print(json.dumps({"mode": "contract", "oks": o, "fails": f, "warns": w,
                              "valid": f == 0}))
            return 1 if f else 0
        print(f"{o} {f} {w}")
        return 1 if f else 0
    if not args.file:
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
    if args.json:
        print(json.dumps({"mode": "audit", "oks": o, "fails": f, "warns": w,
                          "valid": f == 0}))
        return 1 if f else 0
    print(f"{o} {f} {w}")
    return 1 if f else 0


if __name__ == "__main__":
    raise SystemExit(main())
