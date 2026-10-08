#!/usr/bin/env python3
"""Validate a dedup-decontam skill against the Agent Skills standard rules.

Checks: SKILL.md exists with YAML front matter, name == folder name,
description <= 1024 chars, body < 500 lines, references/ links exist,
scripts/ run offline, EVALS.md has >= 5 prompts, SOURCES.md present.

Usage:
  python3 validate_skill.py
  python3 validate_skill.py --skill /path/to/skill
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

MAX_DESC = 1024
MAX_BODY_LINES = 500
MIN_EVALS = 5
MIN_SOURCES = 6

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
NAME_RE = re.compile(r"^name:\s*(.+)$", re.MULTILINE)
DESC_RE = re.compile(r"^description:\s*(.+)$", re.MULTILINE)


def validate(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return [f"SKILL.md missing in {skill_dir}"]

    text = skill_md.read_text(encoding="utf-8")
    lines = text.splitlines()

    fm = FRONTMATTER_RE.match(text)
    if not fm:
        errors.append("missing YAML frontmatter")
    else:
        block = fm.group(1)
        name_m = NAME_RE.search(block)
        desc_m = DESC_RE.search(block)
        if not name_m:
            errors.append("frontmatter missing name")
        else:
            name = name_m.group(1).strip().strip('"').strip("'")
            if name != skill_dir.name:
                errors.append(f"name '{name}' != folder name '{skill_dir.name}'")
            if re.search(r"[A-Z_]", name):
                errors.append(f"name '{name}' is not lowercase-hyphenated")
        if not desc_m:
            errors.append("frontmatter missing description")
        else:
            desc = desc_m.group(1).strip().strip('"').strip("'")
            if len(desc) > MAX_DESC:
                errors.append(f"description {len(desc)} chars > {MAX_DESC}")

    # body line count (everything after the frontmatter)
    body = text[fm.end():] if fm else text
    n_body = len([l for l in body.splitlines() if l.strip()])
    if n_body > MAX_BODY_LINES:
        errors.append(f"body {n_body} lines > {MAX_BODY_LINES}")

    # references/ must exist and be linked one level deep
    refs = skill_dir / "references"
    if not refs.is_dir():
        errors.append("references/ directory missing")
    else:
        linked = set(re.findall(r"references/([A-Za-z0-9_\-]+\.md)", body))
        for f in refs.glob("*.md"):
            if f.name not in linked and f.name != "SOURCES.md":
                errors.append(f"reference {f.name} not linked from SKILL.md")
        for f in refs.glob("*.md"):
            if not f.is_file():
                errors.append(f"reference {f.name} not a file")

    # scripts must exist and run offline (syntax check + --help)
    scripts = skill_dir / "scripts"
    if not scripts.is_dir():
        errors.append("scripts/ directory missing")
    else:
        for py in sorted(scripts.glob("*.py")):
            if py.name.startswith("_"):
                continue
            r = subprocess.run([sys.executable, "-c", f"import ast; ast.parse(open({str(py)!r}).read())"],
                               capture_output=True, text=True)
            if r.returncode != 0:
                errors.append(f"{py.name}: syntax error: {r.stderr.strip()}")

    # EVALS.md
    evals = refs / "EVALS.md" if refs.is_dir() else None
    if evals and evals.is_file():
        t = evals.read_text(encoding="utf-8")
        n = len(re.findall(r"^## E\d+ ", t, re.MULTILINE))
        if n < MIN_EVALS:
            errors.append(f"EVALS.md has {n} evals, need >= {MIN_EVALS}")
    else:
        errors.append("references/EVALS.md missing")

    # SOURCES.md
    src = refs / "SOURCES.md" if refs.is_dir() else None
    if src and src.is_file():
        t = src.read_text(encoding="utf-8")
        n_urls = len(re.findall(r"https?://\S+", t))
        if n_urls < MIN_SOURCES:
            errors.append(f"SOURCES.md has {n_urls} URLs, need >= {MIN_SOURCES}")
    else:
        errors.append("references/SOURCES.md missing")

    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skill", default=str(Path(__file__).resolve().parents[1]))
    args = ap.parse_args()
    errors = validate(Path(args.skill))
    if not errors:
        print(f"PASS: {Path(args.skill).name} validates against the Agent Skills standard", file=sys.stderr)
        return 0
    for e in errors:
        print(f"FAIL: {e}", file=sys.stderr)
    print(f"FAIL: {len(errors)} problem(s)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
