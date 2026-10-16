#!/usr/bin/env python3
"""validate_reviewed_by.py — enforce the adviser sign-off gate.

A skill whose frontmatter carries ``reviewed_by: <name>`` (anything other than the
UNVERIFIED sentinel) may only be loaded as certified when ``docs/reviews/<skill>.md``
exists and contains a *filled* Steuerberater/DPO sign-off block (reviewer name, date,
signature). Skills left at ``reviewed_by: UNVERIFIED`` are reported but never block.

Usage:
  python3 scripts/validate_reviewed_by.py              # exit 0 / 1
  python3 scripts/validate_reviewed_by.py --json        # machine-readable report
  python3 scripts/validate_reviewed_by.py --strict      # also fail on UNVERIFIED skills
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEWS = ROOT / "docs" / "reviews"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
UNVERIFIED = "UNVERIFIED"

# A sign-off block is "filled" when reviewer name, date and signature are all
# non-blank. The placeholder uses underscores; a real signature replaces them.
REVIEWED_BY_RE = re.compile(r"^Reviewed by:\s*(.+)$", re.MULTILINE)
DATE_RE = re.compile(r"^Date:\s*(.+)$", re.MULTILINE)
SIGNATURE_RE = re.compile(r"^Signature:\s*(.+)$", re.MULTILINE)


def parse_frontmatter(skill_md: Path) -> dict[str, str]:
    """Read the YAML-ish frontmatter block of a SKILL.md into a flat dict."""
    text = skill_md.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line or line.strip().startswith("#"):
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields


def discover_skills() -> list[Path]:
    """Every SKILL.md under skills/ (the canonical + the ref-* wrappers)."""
    return sorted(p for p in (ROOT / "skills").rglob("SKILL.md") if p.is_file())


def signoff_path(skill_name: str) -> Path:
    return REVIEWS / f"{skill_name}.md"


def signoff_is_filled(path: Path) -> tuple[bool, str]:
    """Return (ok, reason). A block is filled when name/date/signature are non-blank."""
    if not path.is_file():
        return False, f"sign-off file missing: {path.relative_to(ROOT)}"
    text = path.read_text(encoding="utf-8")
    rb = REVIEWED_BY_RE.search(text)
    dt = DATE_RE.search(text)
    sg = SIGNATURE_RE.search(text)
    if not rb or not dt or not sg:
        return False, f"sign-off block incomplete in {path.relative_to(ROOT)}"
    for label, m in (("reviewed_by", rb), ("date", dt), ("signature", sg)):
        value = m.group(1).strip().strip("_").strip()
        if not value:
            return False, f"sign-off {label} is empty in {path.relative_to(ROOT)}"
    return True, ""


def audit(strict: bool) -> dict:
    certified: list[dict] = []
    unverified: list[dict] = []
    problems: list[str] = []

    for skill_md in discover_skills():
        fm = parse_frontmatter(skill_md)
        reviewed_by = fm.get("reviewed_by", "").strip()
        name = fm.get("name") or skill_md.parent.name
        if not reviewed_by:
            if strict:
                problems.append(f"{name}: no reviewed_by field")
            continue
        if reviewed_by == UNVERIFIED:
            unverified.append({
                "skill": name,
                "path": str(skill_md.relative_to(ROOT)),
                "reviewed_by": reviewed_by,
            })
            continue
        ok, why = signoff_is_filled(signoff_path(name))
        entry = {"skill": name, "path": str(skill_md.relative_to(ROOT)),
                 "reviewed_by": reviewed_by, "ok": ok}
        if ok:
            certified.append(entry)
        else:
            entry["reason"] = why
            certified.append(entry)
            problems.append(f"{name}: certified ({reviewed_by}) but {why}")

    return {
        "skills": len(discover_skills()),
        "certified": certified,
        "unverified": unverified,
        "problems": problems,
        "ok": not problems,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    report = audit(args.strict)
    if args.json:
        # Fail-closed: a certified skill with an unresolved problem (missing or
        # incomplete sign-off block) must make the audit exit non-zero, even in
        # machine-readable mode. Returning 0 here would let a broken certification
        # slip through any caller that only inspects the exit code.
        print(json.dumps(report, indent=2))
        return 0 if report["ok"] else 1

    print(f"skills scanned: {report['skills']}")
    print(f"certified: {len(report['certified'])}")
    print(f"unverified (UNVERIFIED sentinel): {len(report['unverified'])}")
    for p in report["problems"]:
        print(f"  - {p}", file=sys.stderr)
    if report["ok"]:
        print("ok: every certified skill has a filled sign-off block")
        return 0
    print(f"{len(report['problems'])} problem(s)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
