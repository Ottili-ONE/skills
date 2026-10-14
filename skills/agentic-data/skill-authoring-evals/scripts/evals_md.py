#!/usr/bin/env python3
"""evals_md.py — convert a markdown EVALS.md into the evals.json schema and validate it.

The ten skills ship their evals as markdown (references/EVALS.md): a numbered
"## E1" / "## N1" heading followed by Prompt / Expected / Failure signs bullets.
This script parses that file into the JSON contract defined in
references/eval-schema.md and runs the same checks as scripts/evals_check.py,
so the markdown evals become machine-checkable without re-authoring them.

Usage:
  python3 evals_md.py <EVALS.md> [--skill-desc TEXT] [--json]
  python3 evals_md.py --all            # every skill in this collection

Exit 0 on success, 1 on any FAIL, 2 on usage/input error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Collection root: this script lives at <root>/skill-authoring-evals/scripts/, so
# the collection is two parents up (parents[0]=scripts, parents[1]=skill).
COLLECTION = Path(__file__).resolve().parents[2]

# A case is a markdown heading followed by its body until the next heading.
CASE_RE = re.compile(r"^##\s+([A-Z]?[0-9]+)[\s\u2014\-]+(.*)$", re.MULTILINE)
# Tolerant of both "- **Prompt**: ..." and "Prompt: ..." styles, and of
# em-dash separators ("E1 — title"). Continuation lines (a prompt that
# wraps across lines) are joined with a space.
FIELD_RE = re.compile(
    r"^-?\s*(?:\*\*)?(Prompt|Expected|Failure signs)(?:\*\*)?\s*:\s*(.*)$"
)


def _join(lines: list[str]) -> str:
    out: list[str] = []
    for ln in lines:
        if not ln.strip():
            continue
        out.append(ln.strip())
    return " ".join(out)


def parse_evals_md(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    headings = list(CASE_RE.finditer(text))
    cases: list[dict] = []
    for i, m in enumerate(headings):
        cid = m.group(1).strip()
        start = m.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        body = text[start:end]
        fields: dict[str, list[str]] = {}
        cur: str | None = None
        for line in body.splitlines():
            s = line.strip()
            fm = FIELD_RE.match(s)
            if fm:
                cur = fm.group(1).lower()
                fields.setdefault(cur, []).append(fm.group(2).strip())
            elif cur and s and not s.startswith("#"):
                # Continuation of the current field (a wrapped prompt).
                fields[cur].append(s)
            else:
                cur = None
        prompt = _join(fields.get("prompt", []))
        expected = _join(fields.get("expected", []))
        failures = _join(fields.get("failure signs", []))
        if not prompt or not expected:
            continue
        # E-cases fire the skill; N-cases (near-misses) must NOT fire it.
        should_fire = not cid.upper().startswith("N")
        cases.append({
            "id": cid,
            "prompt": prompt,
            "should_fire": should_fire,
            "expected_output": expected,
            "failure_signs": failures,
            "source": "references/EVALS.md",
        })
    return cases


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("evals", nargs="?", default=None, help="EVALS.md path, or pass --all")
    ap.add_argument("--skill-desc", default="", help="skill description for overfit checks")
    ap.add_argument("--json", action="store_true", help="machine-readable report on stdout")
    ap.add_argument("--all", action="store_true", help="validate every EVALS.md in this collection")
    args = ap.parse_args()

    if args.all:
        targets = sorted(p for p in COLLECTION.rglob("references/EVALS.md"))
    elif args.evals:
        targets = [Path(args.evals)]
    else:
        ap.print_help()
        return 2

    grand_fails = grand_warns = grand_oks = 0
    grand_cases = 0
    report = []
    for t in targets:
        skill = t.parent.parent.name
        try:
            cases = parse_evals_md(t)
        except OSError as exc:
            print(f"FAIL: {skill}: cannot read {t}: {exc}", file=sys.stderr)
            grand_fails += 1
            continue
        # Reuse evals_check.check() for the schema validation.
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from evals_check import check  # type: ignore
        fails, warns, oks = check(cases, args.skill_desc)
        n_should = sum(1 for c in cases if c["should_fire"])
        n_not = len(cases) - n_should
        # Extra markdown-specific checks.
        if n_not < 3:
            print(f"FAIL: {skill}: only {n_not} near-miss cases (need >= 3)", file=sys.stderr)
            fails += 1
        if len(cases) < 5:
            print(f"FAIL: {skill}: only {len(cases)} eval cases (need >= 5)", file=sys.stderr)
            fails += 1
        missing = [c["id"] for c in cases if not c.get("failure_signs")]
        if missing:
            print(f"WARN: {skill}: cases with no 'Failure signs' bullet: {missing}", file=sys.stderr)
            warns += 1
        grand_fails += fails
        grand_warns += warns
        grand_oks += oks
        grand_cases += len(cases)
        report.append({"skill": skill, "cases": len(cases), "should_fire": n_should,
                       "should_not_fire": n_not, "fails": fails, "warns": warns})
        if args.json:
            continue
        status = "ok" if not fails else "FAIL"
        print(f"{status:5} {skill:28} {len(cases)} cases ({n_should} fire / {n_not} near-miss), "
              f"{fails} fail, {warns} warn")

    if args.json:
        print(json.dumps({"skills": len(report), "cases": grand_cases,
                          "oks": grand_oks, "fails": grand_fails, "warns": grand_warns,
                          "per_skill": report, "valid": grand_fails == 0}, indent=2))
    return 1 if grand_fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
