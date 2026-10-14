#!/usr/bin/env python3
"""Validate an evals.json against the skill-authoring-evals schema.

Checks: every case has a unique id, a non-empty prompt, a boolean should_fire,
an expected_output, an optional files array of strings, and that the file is not
empty. Also flags overfitting (a case whose prompt is a substring of the
description of the skill under test) and duplicate prompts. Fully offline.

Machine-readable counts go to stdout; FAIL:/PASS:/WARN:/INFO: detail goes to stderr.
Exit 0 on success, 1 on any FAIL, 2 on usage/input error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load(path: str) -> list[dict]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"evals file does not exist: {path}")
    if p.is_dir():
        raise IsADirectoryError(f"evals path is a directory: {path}")
    raw = p.read_text(encoding="utf-8")
    if not raw.strip():
        raise ValueError("evals file is empty")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"evals file is not valid JSON: {exc}") from exc
    if not isinstance(data, list):
        raise ValueError("evals file must be a JSON list of cases")
    return data


def check(evals: list[dict], skill_desc: str = "") -> tuple[int, int, int]:
    """Return (fails, warns, oks)."""
    fails = warns = oks = 0

    def fail(msg: str) -> None:
        nonlocal fails
        print(f"FAIL: {msg}", file=sys.stderr)
        fails += 1

    def warn(msg: str) -> None:
        nonlocal warns
        print(f"WARN: {msg}", file=sys.stderr)
        warns += 1

    if not evals:
        fail("evals list is empty; author at least one case")
        return fails, warns, oks

    ids: set[str] = set()
    prompts: list[str] = []
    n_should = n_not = 0
    for i, case in enumerate(evals, 1):
        if not isinstance(case, dict):
            fail(f"case {i} is not an object")
            continue
        cid = case.get("id")
        if not cid or not isinstance(cid, str):
            fail(f"case {i} has no string id")
            continue
        if cid in ids:
            fail(f"duplicate case id {cid!r}")
        else:
            ids.add(cid)
            oks += 1

        prompt = case.get("prompt")
        if not prompt or not isinstance(prompt, str) or not prompt.strip():
            fail(f"case {cid} has an empty prompt")
        else:
            prompts.append(prompt.strip())

        if "should_fire" not in case:
            fail(f"case {cid} is missing should_fire")
        elif not isinstance(case["should_fire"], bool):
            fail(f"case {cid} should_fire is not a boolean")
        else:
            if case["should_fire"]:
                n_should += 1
            else:
                n_not += 1

        if "expected_output" not in case or not str(case.get("expected_output", "")).strip():
            fail(f"case {cid} is missing expected_output")

        files = case.get("files")
        if files is not None:
            if not isinstance(files, list) or not all(isinstance(f, str) for f in files):
                fail(f"case {cid} files must be a list of strings")

    if n_should == 0:
        fail("no should_fire cases; every skill needs positive examples")
    if n_not == 0:
        warn("no should-not-fire cases; without them precision is unmeasurable")

    seen: set[str] = set()
    for p in prompts:
        if p in seen:
            warn(f"duplicate prompt text: {p[:60]!r}...")
        seen.add(p)

    if skill_desc:
        desc = skill_desc.strip().lower()
        for p in prompts:
            words = [w for w in p.lower().split() if len(w) > 4]
            if len(words) >= 4 and all(w in desc for w in words):
                warn(f"case prompt {p[:60]!r} may echo the skill description (overfit)")

    return fails, warns, oks


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("evals", help="evals.json path")
    ap.add_argument("--skill-desc", default="",
                    help="skill description text to check prompts against for overfitting")
    ap.add_argument("--json", action="store_true",
                    help="emit a machine-readable report object to stdout")
    args = ap.parse_args()

    try:
        evals = load(args.evals)
    except (OSError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    fails, warns, oks = check(evals, args.skill_desc)
    n_should = sum(1 for e in evals if isinstance(e, dict) and e.get("should_fire") is True)
    n_not = sum(1 for e in evals if isinstance(e, dict) and e.get("should_fire") is False)
    if args.json:
        print(json.dumps({"cases": len(evals), "should_fire": n_should,
                          "should_not_fire": n_not, "oks": oks,
                          "fails": fails, "warns": warns, "valid": fails == 0}))
        return 1 if fails else 0
    print(f"{oks} {fails} {warns}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
