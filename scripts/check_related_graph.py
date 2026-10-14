#!/usr/bin/env python3
"""check_related_graph.py — verify the Related-section graph of the ten engineering
playbook skills is acyclic (no circular dependencies) and that every link target
resolves to a real SKILL.md.

Usage:
  python3 scripts/check_related_graph.py [--skills DIR] [--json]
Exit 0 on success, 1 on failure.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINK_RE = re.compile(r"\[(?P<name>[a-z0-9]+(?:-[a-z0-9]+)*)\]\(\.\./(?P<target>[a-z0-9]+(?:-[a-z0-9]+)*)/SKILL\.md\)")


def discover_skills(skills_dir: Path) -> list[Path]:
    return sorted(
        p for p in skills_dir.iterdir()
        if p.is_dir() and (p / "SKILL.md").is_file() and p.name != "references" and p.name != "tests"
    )


def parse_links(skill_md: Path) -> list[str]:
    text = skill_md.read_text(encoding="utf-8")
    return [m.group("target") for m in LINK_RE.finditer(text)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skills", default=str(ROOT / "skills" / "engineering"))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    skills_dir = Path(args.skills)
    skills = discover_skills(skills_dir)
    errors: list[str] = []
    graph: dict[str, list[str]] = {}

    for skill in skills:
        name = skill.name
        links = parse_links(skill / "SKILL.md")
        graph[name] = links
        for target in links:
            if not (skills_dir / target / "SKILL.md").is_file():
                errors.append(f"{name}: link to unknown skill '{target}'")

    # cycle detection via DFS
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {s.name: WHITE for s in skills}

    def dfs(node: str, stack: list[str]) -> bool:
        color[node] = GRAY
        stack.append(node)
        for nxt in graph.get(node, []):
            if nxt not in color:
                continue
            if color[nxt] == GRAY:
                cycle = stack[stack.index(nxt):] + [nxt]
                errors.append(f"circular dependency: {' -> '.join(cycle)}")
                return False
            if color[nxt] == WHITE:
                if not dfs(nxt, stack):
                    return False
        stack.pop()
        color[node] = BLACK
        return True

    for node in list(color):
        if color[node] == WHITE:
            dfs(node, [])

    if args.json:
        print(json.dumps({"skills": len(skills), "edges": {k: v for k, v in graph.items()}, "errors": errors, "ok": not errors}, indent=2))
        return 0 if not errors else 1

    if errors:
        print("graph check failed:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print(f"ok: {len(skills)} skills, Related graph is acyclic")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
