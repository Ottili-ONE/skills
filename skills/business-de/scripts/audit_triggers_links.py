#!/usr/bin/env python3
"""Trigger + cross-link audit for the ten business-de skills.

Two checks:
  1. trigger coverage -- every skill's body should name its sibling skills
     when they are relevant; the audit reports which named siblings are NOT
     linked in the `## Related skills` section (so we know what to add).
  2. cross-link graph -- every `## Related skills` section names sibling
     skills by folder name; the audit walks the graph and reports cycles.

Usage: python3 skills/business-de/scripts/audit_triggers_links.py
Exit 0 when the graph is acyclic and every named neighbour is linked.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKILLS_DIR = ROOT / "skills" / "business-de"
SKILL_NAMES = [
    "bank-reconciliation-camt", "carrier-apis-de", "datev-extf",
    "dsgvo-ai-act-labeling", "gobd-archive", "publish-reconcile-wp-meta",
    "skr-journal-mapping", "ust-edge-cases", "webhooks-safe",
    "xrechnung-zugferd",
]


def parse_body(text: str) -> str:
    m = re.match(r"^---\s*\n.*?\n---\s*\n(.*)$", text, re.DOTALL)
    return m.group(1) if m else text


def related_links(body: str) -> list[str]:
    m = re.search(r"^## Related skills\s*\n(.*?)(?=^## |\Z)", body, re.M | re.S)
    if not m:
        return []
    sec = m.group(1)
    names = re.findall(r"`([a-z][a-z0-9-]*)`", sec)
    names += re.findall(r"\[([a-z][a-z0-9-]*)\]\([^)]*\)", sec)
    return names


def find_cycle(graph: dict[str, set[str]]) -> list[str] | None:
    path: list[str] = []
    on_path: set[str] = set()
    visited: set[str] = set()

    def dfs(node: str):
        if node in on_path:
            return path[path.index(node):]
        if node in visited:
            return None
        visited.add(node)
        on_path.add(node)
        path.append(node)
        for nxt in graph.get(node, ()):
            c = dfs(nxt)
            if c:
                return c
        path.pop()
        on_path.discard(node)
        return None

    for start in graph:
        c = dfs(start)
        if c:
            return c
    return None


def main() -> int:
    graph: dict[str, set[str]] = {}
    problems = 0
    for name in SKILL_NAMES:
        body = parse_body((SKILLS_DIR / name / "SKILL.md").read_text(encoding="utf-8"))
        links = [l for l in related_links(body) if l in SKILL_NAMES]
        graph[name] = set(links)
        mentioned = {n for n in SKILL_NAMES
                     if n != name and re.search(rf"\b{re.escape(n)}\b", body)}
        missing = mentioned - set(links)
        if missing:
            problems += 1
            print(f"[trigger-gap] {name}: body mentions {sorted(missing)} "
                  f"but Related does not link them")
        extra = set(links) - mentioned
        if extra:
            print(f"[link-stale] {name}: links {sorted(extra)} but the body "
                  f"never mentions them by name")
    cycle = find_cycle(graph)
    if cycle:
        problems += 1
        print(f"[cycle] {' -> '.join(cycle)}")
    else:
        print("[graph] cross-link graph is acyclic")
    incoming: dict[str, set[str]] = defaultdict(set)
    for a, bs in graph.items():
        for b in bs:
            incoming[b].add(a)
    sinks = sorted(n for n in SKILL_NAMES if not graph.get(n))
    print(f"[sinks] {sinks}")
    print(f"\n{problems} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
