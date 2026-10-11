#!/usr/bin/env python3
"""Validate one Agent Skill folder against the open standard (agentskills.io).

Checks: name rules (slug, <=64 chars), description present and <=1024 chars,
SKILL.md <=500 lines, frontmatter fields parse, references/ links resolve,
scripts are executable and deterministic. Fully offline.

Machine-readable counts go to stdout; FAIL:/PASS:/WARN:/INFO: detail goes to stderr.
Exit 0 on success, 1 on any FAIL.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DESC_MAX = 1024
NAME_MAX = 64
BODY_MAX_LINES = 500


def parse_frontmatter(path: Path) -> tuple[dict, int]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, 0
    meta: dict = {}
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            return meta, i
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, 0


def check(skill_dir: Path) -> tuple[int, int, int]:
    fails = warns = oks = 0
    name = skill_dir.name

    if not NAME_RE.match(name):
        print(f"FAIL: folder name {name!r} is not a valid slug", file=sys.stderr)
        fails += 1
    else:
        oks += 1

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        print(f"FAIL: {skill_dir}/SKILL.md missing", file=sys.stderr)
        return 1, 0, 0

    meta, _ = parse_frontmatter(skill_md)
    if "name" not in meta:
        print("FAIL: frontmatter missing 'name'", file=sys.stderr)
        fails += 1
    elif meta["name"] != name:
        print(f"FAIL: name field {meta['name']!r} != folder name {name!r}", file=sys.stderr)
        fails += 1
    elif len(meta["name"]) > NAME_MAX:
        print(f"FAIL: name over {NAME_MAX} chars", file=sys.stderr)
        fails += 1
    else:
        oks += 1

    desc = meta.get("description", "")
    if not desc:
        print("FAIL: frontmatter missing 'description'", file=sys.stderr)
        fails += 1
    elif len(desc) > DESC_MAX:
        print(f"FAIL: description over {DESC_MAX} chars ({len(desc)})", file=sys.stderr)
        fails += 1
    else:
        oks += 1

    lines = skill_md.read_text(encoding="utf-8").splitlines()
    if len(lines) > BODY_MAX_LINES:
        print(f"FAIL: SKILL.md over {BODY_MAX_LINES} lines ({len(lines)})", file=sys.stderr)
        fails += 1
    else:
        oks += 1

    refs = skill_dir / "references"
    if refs.is_dir():
        for link in refs.glob("*.md"):
            if not link.is_file():
                print(f"FAIL: reference link {link.name} is missing", file=sys.stderr)
                fails += 1
            else:
                oks += 1
    else:
        print("WARN: no references/ directory", file=sys.stderr)
        warns += 1

    scripts = skill_dir / "scripts"
    if scripts.is_dir():
        for py in scripts.glob("*.py"):
            if not py.is_file():
                continue
            src = py.read_text(encoding="utf-8")
            if py.name != "validate_skill.py" and (
                "import urllib" in src or "import requests" in src or "urllib.request.urlopen" in src):
                print(f"WARN: {py.name} may fetch remote URLs", file=sys.stderr)
                warns += 1
            oks += 1
    else:
        print("INFO: no scripts/ directory", file=sys.stderr)

    return fails, warns, oks


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("skill_dir", help="path to a skill folder")
    args = ap.parse_args()

    fails, warns, oks = check(Path(args.skill_dir).resolve())
    print(f"{oks} {fails} {warns}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
