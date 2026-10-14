#!/usr/bin/env python3
"""Collection-level acceptance test for the ten engineering playbook skills.

Checks the acceptance criteria of skills-engineering-r3-01 and the r3-05 quality pass:
  * RESEARCH.md exists with the ranked list and final names
  * every skill folder has a SKILL.md with valid front matter
  * every skill has references/SOURCES.md with >= 6 unique URLs
  * every skill has references/DESIGN.md (trigger, what-it-does-better, procedure, scripts, 5 evals)
  * every skill has references/EVALS.md with >= 5 prompts
  * every SKILL.md `## Related skills` section links to real skill folders and the
    cross-link graph is acyclic with `shared-tree-git` as the unique sink
  * every references/EVALS.md has >= 3 near-miss prompts (trigger-precision guard)
  * every SOURCES.md records a retrieval date of 2026-10-14 (re-verification pass)
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ENGINEERING = ROOT / "skills" / "engineering"

EXPECTED = [
    "pg-rls-multitenant",
    "outbox-idempotency",
    "problem-json-contracts",
    "module-contract-first",
    "shared-tree-git",
    "long-test-discipline",
    "playwright-a11y-e2e",
    "foundation-v2-conformance",
    "acceptance-harness",
    "honest-status",
]

URL_RE = re.compile(r"https?://[^\s)\]<]+")


def check() -> list[str]:
    errors: list[str] = []
    research = ENGINEERING / "RESEARCH.md"
    if not research.is_file():
        errors.append("missing skills/engineering/RESEARCH.md")
    else:
        text = research.read_text(encoding="utf-8")
        for name in EXPECTED:
            if name not in text:
                errors.append(f"RESEARCH.md does not mention skill '{name}'")

    for name in EXPECTED:
        skill_dir = ENGINEERING / name
        skill_md = skill_dir / "SKILL.md"
        sources = skill_dir / "references" / "SOURCES.md"
        design = skill_dir / "references" / "DESIGN.md"
        evals = skill_dir / "references" / "EVALS.md"

        if not skill_md.is_file():
            errors.append(f"{name}: SKILL.md missing")
            continue
        fm = skill_md.read_text(encoding="utf-8")
        if not fm.startswith("---"):
            errors.append(f"{name}: SKILL.md has no YAML frontmatter")
        else:
            m = re.match(r"^---\s*\n(.*?)\n---\s*\n", fm, re.DOTALL)
            if not m:
                errors.append(f"{name}: malformed frontmatter")
            else:
                block = m.group(1)
                nm = re.search(r"^name:\s*(.+)$", block, re.MULTILINE)
                if not nm or nm.group(1).strip() != name:
                    errors.append(f"{name}: frontmatter name != {name}")

        if not sources.is_file():
            errors.append(f"{name}: references/SOURCES.md missing")
        else:
            urls = set(URL_RE.findall(sources.read_text(encoding="utf-8")))
            if len(urls) < 6:
                errors.append(f"{name}: SOURCES.md has {len(urls)} unique URLs (< 6 required)")

        # SOURCES.md re-verification date (r3-05 task item 3)
        stext = sources.read_text(encoding="utf-8")
        if "2026-10-14" not in stext:
            errors.append(f"{name}: SOURCES.md not re-verified on 2026-10-14")

        # EVALS near-miss prompts (r3-05 task item 2)
        etext = evals.read_text(encoding="utf-8")
        nm_section = etext.split("Near-miss", 1)[-1] if "Near-miss" in etext else ""
        nm_count = len(re.findall(r"^\s*-\s+\*\*N\d", nm_section, re.MULTILINE))
        if nm_count < 3:
            errors.append(f"{name}: EVALS.md has {nm_count} near-miss prompts (< 3 required)")

        if not design.is_file():
            errors.append(f"{name}: references/DESIGN.md missing")
        else:
            d = design.read_text(encoding="utf-8").lower()
            for needle in ("trigger", "does better", "procedure outline",
                           "scripts", "five eval prompts"):
                if needle not in d:
                    errors.append(f"{name}: DESIGN.md missing section '{needle}'")

        if not evals.is_file():
            errors.append(f"{name}: references/EVALS.md missing")
        else:
            prompts = re.findall(r"^##\s+(?:\d+\.|E\d+|Prompt\s+\d+)", evals.read_text(encoding="utf-8"), re.MULTILINE)
            if len(prompts) < 5:
                errors.append(f"{name}: EVALS.md has {len(prompts)} prompts (< 5 required)")

    # Cross-link graph: acyclic, shared-tree-git is the unique sink (r3-05 task item 4)
    edges: dict[str, set[str]] = {name: set() for name in EXPECTED}
    for name in EXPECTED:
        skill_md = ENGINEERING / name / "SKILL.md"
        body = skill_md.read_text(encoding="utf-8")
        section = body.split("## Related", 1)[-1] if "## Related" in body else ""
        for m in re.finditer(r"\[([a-z0-9-]+)\]\(\.\./([a-z0-9-]+)/SKILL\.md\)", section):
            target = m.group(2)
            if target not in edges:
                errors.append(f"{name}: Related section links unknown skill '{target}'")
                continue
            edges[name].add(target)
    # every skill must have a Related section
    for name in EXPECTED:
        body = (ENGINEERING / name / "SKILL.md").read_text(encoding="utf-8")
        if "## Related" not in body:
            errors.append(f"{name}: SKILL.md has no '## Related skills' section")
    # shared-tree-git must be a sink: its Related section may *describe* other skills
    # (informational mentions) but must not link them, otherwise the graph has a cycle.
    stg_body = (ENGINEERING / "shared-tree-git" / "SKILL.md").read_text(encoding="utf-8")
    stg_section = stg_body.split("## Related", 1)[-1] if "## Related" in stg_body else ""
    if re.search(r"\]\(\.\./[a-z0-9-]+/SKILL\.md\)", stg_section):
        errors.append("shared-tree-git must not link other skills in its Related section (it is the sink)")
    # DFS cycle detection
    WHITE, GRAY, BLACK = 0, 1, 2
    colour: dict[str, int] = {n: WHITE for n in EXPECTED}

    def dfs(node: str) -> bool:
        colour[node] = GRAY
        for nxt in edges.get(node, ()):
            if colour[nxt] == GRAY:
                return True
            if colour[nxt] == WHITE and dfs(nxt):
                return True
        colour[node] = BLACK
        return False

    for n in EXPECTED:
        if colour[n] == WHITE and dfs(n):
            errors.append("cross-link graph has a cycle")
            break

    return errors


def main() -> int:
    errors = check()
    if errors:
        print("collection acceptance FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"ok: all {len(EXPECTED)} skills pass collection acceptance (RESEARCH + SOURCES>=6 + DESIGN + EVALS>=5)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
