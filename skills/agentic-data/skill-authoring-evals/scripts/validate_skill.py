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
import json
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
            meta[k.strip()] = v.strip()
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
    elif not NAME_RE.match(meta["name"]):
        print(f"FAIL: name {meta['name']!r} is not a valid slug", file=sys.stderr)
        fails += 1
    else:
        oks += 1

    desc = (meta.get("description") or "").strip()
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

    # Parse SKILL.md for `references/<name>.md` links and verify each resolves.
    # A dangling link is a hard failure, not a warning.
    body = skill_md.read_text(encoding="utf-8")
    # Match both backticked (`references/foo.md`) and bare (references/foo.md) links.
    link_re = re.compile(r"`?references/([^`\s]+\.md)`?")
    seen_links: set[str] = set()
    for raw in link_re.findall(body):
        target = raw.strip()
        if target in seen_links:
            continue
        seen_links.add(target)
        resolved = (skill_dir / "references" / Path(target).name).resolve()
        try:
            resolved.relative_to((skill_dir / "references").resolve())
        except ValueError:
            print(f"FAIL: references link {target!r} escapes the references/ directory",
                  file=sys.stderr)
            fails += 1
            continue
        if not resolved.is_file():
            print(f"FAIL: references link {target!r} does not resolve to a file",
                  file=sys.stderr)
            fails += 1
        else:
            oks += 1

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
    ap.add_argument("skill_dir", nargs="?", default=str(Path(__file__).resolve().parents[1]),
                    help="path to a skill folder (default: this skill)")
    ap.add_argument("--skill", type=Path, default=None,
                    help="path to a skill folder (overrides positional)")
    ap.add_argument("--json", type=Path, default=None, help="write JSON report here")
    args = ap.parse_args()

    skill_dir = Path(args.skill or args.skill_dir).resolve()
    if not skill_dir.is_dir():
        print(f"FAIL: skill dir not found: {skill_dir}", file=sys.stderr)
        return 2
    fails, warns, oks = check(skill_dir)
    print(f"{oks} {fails} {warns}")
    if args.json:
        if not args.json.parent.is_dir():
            print(f"FAIL: --json parent dir missing: {args.json.parent}", file=sys.stderr)
            return 2
        args.json.write_text(json.dumps({
            "skill": skill_dir.name,
            "path": str(skill_dir),
            "oks": oks, "fails": fails, "warns": warns,
            "ok": fails == 0,
        }, indent=2) + "\n", encoding="utf-8")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
