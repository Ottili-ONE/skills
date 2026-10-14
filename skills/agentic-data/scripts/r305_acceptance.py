#!/usr/bin/env python3
"""skills-agentic-data-r3-05 acceptance gate.

Checks, for every skill under skills/agentic-data/:
  1. validate_skill.py exits 0 for all ten (validator green)
  2. references/EVALS.md exists with >= 5 primary prompts (## E<N> headings)
     and exactly 3 near-miss prompts (## N<N> headings in the Near-miss
     prompts section)
  3. SKILL.md has a Related section (cross-link graph checked separately)
  4. README.md and HANDOFF.md exist at the collection root

Usage: python3 skills/agentic-data/scripts/r305_acceptance.py
Exit code 0 only when every check passes.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # skills/agentic-data
SCRIPTS = ROOT.parent.parent / "scripts"  # repo root scripts
SKILL_DIRS = sorted(p for p in ROOT.iterdir()
                    if p.is_dir() and (p / "SKILL.md").exists())


def count_prompts(evals: Path) -> tuple[int, int]:
    """Return (primary_prompt_count, near_miss_count).

    Primary prompts are ``## E<N>`` headings; near-miss prompts are
    ``## N<N>`` headings inside the "Near-miss prompts" section.
    """
    text = evals.read_text(encoding="utf-8") if evals.exists() else ""
    near_idx = text.find("## Near-miss prompts")
    primary_section = text if near_idx < 0 else text[:near_idx]
    near_section = text[near_idx:] if near_idx >= 0 else ""
    primary = len(re.findall(r"^## E\d+\b", primary_section, re.M))
    near = len(re.findall(r"^## N\d+\b", near_section, re.M))
    return primary, near


def main() -> int:
    failures = []
    skills = [str(d) for d in SKILL_DIRS]
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "validate_skill.py")] + skills,
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        failures.append("validator failed:\n" + r.stdout + r.stderr)

    for d in SKILL_DIRS:
        name = d.name
        evals = d / "references" / "EVALS.md"
        if not evals.exists():
            failures.append(f"{name}: missing references/EVALS.md")
            continue
        prim, near = count_prompts(evals)
        if prim < 5:
            failures.append(f"{name}: only {prim} primary prompts (need >=5)")
        if near != 3:
            failures.append(f"{name}: {near} near-miss prompts (need 3)")
        related = (d / "SKILL.md").read_text(encoding="utf-8")
        if "Related" not in related:
            failures.append(f"{name}: SKILL.md missing Related section")

    for doc in ("README.md", "HANDOFF.md"):
        if not (ROOT / doc).exists():
            failures.append(f"missing collection {doc}")

    if failures:
        print("ACCEPTANCE FAIL")
        for f in failures:
            print(" -", f)
        return 1
    print("ACCEPTANCE OK: all ten skills green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
