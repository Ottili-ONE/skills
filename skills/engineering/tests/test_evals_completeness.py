#!/usr/bin/env python3
"""Every engineering skill's EVALS.md must carry >=5 prompts and >=3 near-miss prompts.

Assumption: prompts are numbered `## N. ...` or `## E<n> — ...`; near-miss prompts are
bulleted `- **N<n> — ...`. The counts are checked by regex, not by parsing prose, so a
mis-formatted heading silently counts as zero — that is the defect this test exists to catch.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # repo root (tests/ -> engineering/ -> skills/ -> root)
ENGINEERING = ROOT / "skills" / "engineering"
PROMPT_RE = re.compile(r"^##\s+(?:E\d+|\d+)\b", re.MULTILINE)
NEAR_MISS_RE = re.compile(r"^\-\s+\*\*N\d+\b", re.MULTILINE)
MIN_PROMPTS = 5
MIN_NEAR_MISSES = 3


def check_skill(skill_dir: Path) -> list[str]:
    evals = skill_dir / "references" / "EVALS.md"
    if not evals.is_file():
        return [f"{skill_dir.name}: EVALS.md missing"]
    text = evals.read_text(encoding="utf-8")
    prompts = PROMPT_RE.findall(text)
    near_misses = NEAR_MISS_RE.findall(text)
    errors: list[str] = []
    if len(prompts) < MIN_PROMPTS:
        errors.append(f"{skill_dir.name}: {len(prompts)} prompts (need >= {MIN_PROMPTS})")
    if len(near_misses) < MIN_NEAR_MISSES:
        errors.append(f"{skill_dir.name}: {len(near_misses)} near-miss prompts (need >= {MIN_NEAR_MISSES})")
    return errors


def main() -> int:
    errors: list[str] = []
    skills = sorted(p for p in ENGINEERING.iterdir()
                    if p.is_dir() and (p / "SKILL.md").is_file())
    for skill in skills:
        errors.extend(check_skill(skill))
    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1
    print(f"ok: {len(skills)} skills meet prompt + near-miss thresholds")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
