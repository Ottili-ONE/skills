#!/usr/bin/env python3
"""Agent-Skills-standard validator for the ten business-de skills.

Checks: name==folder, description<=1024 chars (states what+when),
SKILL.md <=500 lines, frontmatter portable fields only, references/
links one level deep, EVALS.md >=5 prompts + 3 near-miss prompts,
SOURCES.md >=6 URLs with retrieval dates, no verbatim 15-word runs
between SKILL.md body and its own references/.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # repo root (business-de/scripts/validate_skills.py)
SKILLS_DIR = ROOT / "skills" / "business-de"
MAX_DESC = 1024
MAX_LINES = 500
PORTABLE = {"name", "description", "license", "compatibility", "metadata",
            "allowed-tools"}


def count_prompts(text: str) -> int:
    return len(re.findall(r"^## \d+\.\s", text, re.M))


def count_nearmiss(text: str) -> int:
    # near-miss prompt entries: "### N1. ..." style, or numbered bullets
    n = len(re.findall(r"^### \s*N?\d+[.\)]\s", text, re.M))
    if n:
        return n
    return len(re.findall(r"(?i)near[- ]?miss", text)) - 1


def check_skill(d: Path) -> list[str]:
    errs: list[str] = []
    rel = d.relative_to(ROOT)
    skill_md = d / "SKILL.md"
    if not skill_md.is_file():
        return [f"{rel}: SKILL.md missing"]
    text = skill_md.read_text(encoding="utf-8")
    lines = text.splitlines()
    if len(lines) > MAX_LINES:
        errs.append(f"{rel}: SKILL.md {len(lines)} lines > {MAX_LINES}")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        errs.append(f"{rel}: missing YAML frontmatter")
        return errs
    fm = m.group(1)
    body = text[m.end():]
    fields: dict[str, str] = {}
    for line in fm.splitlines():
        if ":" not in line or line.strip().startswith("#"):
            continue
        k, v = line.split(":", 1)
        fields[k.strip()] = v.strip().strip('"').strip("'")
    name = fields.get("name", "")
    if name != d.name:
        errs.append(f"{rel}: name '{name}' != folder '{d.name}'")
    desc = fields.get("description", "")
    if not desc:
        errs.append(f"{rel}: no description")
    elif len(desc) > MAX_DESC:
        errs.append(f"{rel}: description {len(desc)} chars > {MAX_DESC}")
    elif not re.search(r"Use when|when to use", desc, re.I):
        errs.append(f"{rel}: description lacks 'when to use' trigger")
    extra = set(fields) - PORTABLE
    if extra:
        errs.append(f"{rel}: non-portable frontmatter fields {sorted(extra)}")
    for ln in body.splitlines():
        mm = re.search(r"\]\(([^)]+)\)", ln)
        if mm:
            tgt = mm.group(1)
            # one-level-deep rule: allow SKILL.md -> references/ and
            # sibling-skill links (../name/), but reject ../../ or /abs
            if tgt.startswith(("http", "#")):
                continue
            if tgt.startswith("/"):
                errs.append(f"{rel}: absolute link '{tgt}'")
                continue
            if tgt.count("..") > 1 or tgt.startswith("../../"):
                errs.append(f"{rel}: deep link '{tgt}' (must be one level deep)")
    ev = d / "references" / "EVALS.md"
    if not ev.is_file():
        errs.append(f"{rel}: references/EVALS.md missing")
    else:
        et = ev.read_text(encoding="utf-8")
        p = count_prompts(et)
        nm = count_nearmiss(et)
        if p < 5:
            errs.append(f"{rel}: EVALS has {p} prompts (<5)")
        if nm < 3:
            errs.append(f"{rel}: EVALS has {nm} near-miss prompts (<3)")
    so = d / "references" / "SOURCES.md"
    if not so.is_file():
        errs.append(f"{rel}: references/SOURCES.md missing")
    else:
        st = so.read_text(encoding="utf-8")
        urls = re.findall(r"https?://[^\s)\]]+", st)
        dates = re.findall(r"20\d{2}-\d{2}-\d{2}", st)
        if len(urls) < 6:
            errs.append(f"{rel}: SOURCES has {len(urls)} URLs (<6)")
        if len(dates) < 2:
            errs.append(f"{rel}: SOURCES has {len(dates)} retrieval dates (<2)")
    refdir = d / "references"
    refblob = " ".join(
        p.read_text(encoding="utf-8") for p in refdir.glob("*.md")
    ).lower()
    words = re.findall(r"[a-z0-9]+", body.lower())
    runs = {" ".join(words[i:i + 15]) for i in range(len(words) - 14)}
    overlap = [r for r in runs if r and r in refblob]
    if overlap:
        errs.append(f"{rel}: {len(overlap)} verbatim 15-word runs overlap references/")
    return errs


def main() -> int:
    all_errs: list[str] = []
    skills = sorted(p for p in SKILLS_DIR.iterdir()
                    if (p / "SKILL.md").is_file())
    for d in skills:
        errs = check_skill(d)
        all_errs.extend(errs)
        print(f"{'OK  ' if not errs else 'FAIL'} {d.name}: "
              f"{len(errs)} issues")
        for e in errs:
            print(f"      - {e}")
    print(f"\n{len(skills)} skills checked, {len(all_errs)} total issues")
    return 1 if all_errs else 0


if __name__ == "__main__":
    raise SystemExit(main())
