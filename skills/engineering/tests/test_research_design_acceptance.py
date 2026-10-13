#!/usr/bin/env python3
"""Acceptance test for skills-engineering-r3-01 (research + design).

Mechanically proves the task brief's acceptance criteria for every engineering skill:
  * references/SOURCES.md exists and names >= 6 distinct http(s) URLs
  * references/DESIGN.md exists and names >= 5 eval prompts
  * references/EVALS.md exists and names >= 5 test prompts
  * the SKILL.md frontmatter name equals the folder name (standard rule)
Run: python3 skills/engineering/tests/test_research_design_acceptance.py
Exit 0 on success, 1 on failure.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ENGINEERING = ROOT / "skills" / "engineering"

URL_RE = re.compile(r"https?://[^\s)\]\"'<>]+")
PROMPT_RE = re.compile(r"^\s*(?:#{1,4}\s+|\*\*)?(?:Prompt|Scenario|Q\d|E\d|\d+\.)", re.MULTILINE)


def skill_dirs() -> list[Path]:
    return sorted(p for p in ENGINEERING.iterdir() if p.is_dir() and (p / "SKILL.md").is_file())


def check_skill(skill: Path) -> list[str]:
    problems: list[str] = []
    sources = skill / "references" / "SOURCES.md"
    design = skill / "references" / "DESIGN.md"
    evals = skill / "references" / "EVALS.md"
    skill_md = skill / "SKILL.md"

    if not skill_md.is_file():
        return [f"{skill.name}: SKILL.md missing"]
    front = skill_md.read_text(encoding="utf-8").splitlines()
    name = next((l.split(":", 1)[1].strip() for l in front if l.startswith("name:")), None)
    if name != skill.name:
        problems.append(f"{skill.name}: frontmatter name {name!r} != folder {skill.name!r}")

    if not sources.is_file():
        problems.append(f"{skill.name}: references/SOURCES.md missing")
    else:
        urls = set(URL_RE.findall(sources.read_text(encoding="utf-8")))
        if len(urls) < 6:
            problems.append(f"{skill.name}: SOURCES.md has {len(urls)} URLs, need >= 6")

    if not design.is_file():
        problems.append(f"{skill.name}: references/DESIGN.md missing")
    else:
        n = len(PROMPT_RE.findall(design.read_text(encoding="utf-8")))
        if n < 5:
            problems.append(f"{skill.name}: DESIGN.md has {n} eval prompts, need >= 5")

    if not evals.is_file():
        problems.append(f"{skill.name}: references/EVALS.md missing")
    else:
        n = len(PROMPT_RE.findall(evals.read_text(encoding="utf-8")))
        if n < 5:
            problems.append(f"{skill.name}: EVALS.md has {n} prompts, need >= 5")

    return problems


def main() -> int:
    skills = skill_dirs()
    if not skills:
        print("FAIL: no engineering skills found under", ENGINEERING)
        return 1
    failures: list[str] = []
    for s in skills:
        failures.extend(check_skill(s))
    if failures:
        print("FAIL:")
        for f in failures:
            print("  -", f)
        return 1
    print(f"ok: {len(skills)} engineering skills meet research+design acceptance criteria")
    return 0


if __name__ == "__main__":
    sys.exit(main())
