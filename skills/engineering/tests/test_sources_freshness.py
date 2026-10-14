#!/usr/bin/env python3
"""Every version-sensitive claim in a skill's SOURCES.md must carry a retrieval date.

A fact without a retrieval date cannot be re-verified and silently rots. This test
enforces that each `references/SOURCES.md` contains at least one line matching
`retrieved <YYYY>-<MM>-<DD>` and that the date is not older than 180 days.
"""
from __future__ import annotations

import re
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ENGINEERING = ROOT / "skills" / "engineering"
MAX_AGE_DAYS = 180
DATE_RE = re.compile(r"(?:retrieved|verified|re-verified)\s+(\d{4})-(\d{2})-(\d{2})", re.IGNORECASE)


def check_skill(skill_dir: Path) -> list[str]:
    sources = skill_dir / "references" / "SOURCES.md"
    if not sources.is_file():
        return [f"{skill_dir.name}: SOURCES.md missing"]
    text = sources.read_text(encoding="utf-8")
    dates = [datetime(int(y), int(m), int(d)).date()
             for y, m, d in DATE_RE.findall(text)]
    errors: list[str] = []
    if not dates:
        return [f"{skill_dir.name}: no dated retrieval line (retrieved/verified/re-verified YYYY-MM-DD) in SOURCES.md"]
    newest = max(dates)
    age = (date.today() - newest).days
    if age > MAX_AGE_DAYS:
        errors.append(
            f"{skill_dir.name}: newest retrieval {newest} is {age}d old (> {MAX_AGE_DAYS}d)"
        )
    return errors


def main() -> int:
    skills = sorted(p for p in ENGINEERING.iterdir()
                    if p.is_dir() and (p / "SKILL.md").is_file())
    errors: list[str] = []
    for s in skills:
        errors.extend(check_skill(s))
    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1
    print(f"ok: {len(skills)} skills have fresh, dated SOURCES")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
