#!/usr/bin/env python3
"""validate_skill.py — validate one or more Agent Skill folders against the open standard.

Implements the rules in the agentskills.io specification (docs/specification.mdx, retrieved
2026-10-13 from https://raw.githubusercontent.com/agentskills/agentskills/main/docs/specification.mdx):

  * SKILL.md is required; YAML frontmatter with `name` and `description` is required.
  * `name`: max 64 chars; lowercase letters, numbers, hyphens only; must not start or end with
    a hyphen; no consecutive hyphens; MUST equal the parent directory name.
  * `description`: 1-1024 characters; non-empty; must state what the skill does AND when to use it.
  * Optional fields: `license`, `compatibility` (max 500 chars), `metadata`, `allowed-tools`.
  * Body: no format restrictions, but long content should be split into `references/` linked one
    level deep (progressive disclosure).
  * Directory may contain `scripts/`, `references/`, `assets/`.

Usage:
  python3 scripts/validate_skill.py <skill-dir> [<skill-dir> ...]
  python3 scripts/validate_skill.py --all
Exit 0 on success, 1 on failure, 2 on malformed input.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME_MAX = 64
DESC_MAX = 1024
COMPAT_MAX = 500
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(text: str) -> dict[str, str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    fields: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" not in line or line.strip().startswith("#"):
            continue
        k, v = line.split(":", 1)
        fields[k.strip()] = v.strip().strip('"').strip("'")
    return fields


def validate_skill_dir(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_dir.is_dir():
        return [f"{skill_dir.name}: directory missing"]
    if not skill_md.is_file():
        return [f"{skill_dir.name}: SKILL.md missing"]

    text = skill_md.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)
    if not fm:
        return [f"{skill_dir.name}: missing or malformed YAML frontmatter"]

    name = fm.get("name", "")
    desc = fm.get("description", "")
    compat = fm.get("compatibility", "")

    if not name:
        errors.append(f"{skill_dir.name}: frontmatter `name` is required")
    else:
        if name != skill_dir.name:
            errors.append(f"{skill_dir.name}: name '{name}' must equal directory name '{skill_dir.name}'")
        if len(name) > NAME_MAX:
            errors.append(f"{skill_dir.name}: name '{name}' is {len(name)} chars (max {NAME_MAX})")
        if not NAME_RE.match(name):
            errors.append(f"{skill_dir.name}: name '{name}' must be lowercase letters, numbers, "
                          f"and single hyphens, no leading/trailing hyphen")
        if name.startswith("-") or name.endswith("-"):
            errors.append(f"{skill_dir.name}: name '{name}' must not start or end with a hyphen")

    if not desc:
        errors.append(f"{skill_dir.name}: frontmatter `description` is required")
    else:
        if len(desc) > DESC_MAX:
            errors.append(f"{skill_dir.name}: description is {len(desc)} chars (max {DESC_MAX})")
        if not re.search(r"\b(when|use|for|fires|do not)\b", desc, re.IGNORECASE):
            errors.append(f"{skill_dir.name}: description should state when to use the skill")

    if compat and len(compat) > COMPAT_MAX:
        errors.append(f"{skill_dir.name}: compatibility is {len(compat)} chars (max {COMPAT_MAX})")

    # Body length guidance (progressive disclosure): SKILL.md under 500 lines.
    lines = text.splitlines()
    if len(lines) > 500:
        errors.append(f"{skill_dir.name}: SKILL.md is {len(lines)} lines (recommended <= 500; "
                      f"move long material to references/)")

    # References: every relative link in the body must resolve to a file that exists.
    for m in re.finditer(r"\]\(([^)]+)\)", text):
        target = m.group(1)
        if target.startswith(("http://", "https://", "mailto:", "#", "data:")):
            continue
        # Markdown fragments (#anchor) are not part of the filesystem path; GitHub-style
        # anchors are generated from heading text and are checked separately below.
        path_part = target.split("#", 1)[0]
        if not path_part:
            continue
        resolved = (skill_md.parent / path_part).resolve()
        if not resolved.exists():
            errors.append(f"{skill_dir.name}: link '{target}' in SKILL.md does not resolve")
        elif "#" in target:
            anchor = target.split("#", 1)[1]
            # GitHub generates anchors from the target file's headings; check the
            # referenced file, not SKILL.md.
            target_text = resolved.read_text(encoding="utf-8").lower()
            expected = anchor.replace("-", " ")
            if expected not in target_text:
                errors.append(f"{skill_dir.name}: link '{target}' anchor not found in {path_part}")

    return errors


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    if args[0] == "--all":
        # Default scope is this job's owned tree (skills/engineering/**).
        # Pass --everywhere to validate every skill in the repository (read-only; other
        # jobs' skills are reported but their failures are not this job's to fix).
        skills_root = ROOT / "skills" / "engineering"
        targets = sorted(
            d for d in skills_root.rglob("*")
            if d.is_dir() and (d / "SKILL.md").is_file()
        )
    elif args[0] == "--everywhere":
        skills_root = ROOT / "skills"
        targets = sorted(
            d for d in skills_root.rglob("*")
            if d.is_dir() and (d / "SKILL.md").is_file()
        )
    else:
        targets = [Path(a).resolve() for a in args]

    total_errors: list[str] = []
    checked = 0
    for t in targets:
        errs = validate_skill_dir(t)
        checked += 1
        if errs:
            total_errors.extend(errs)
        else:
            print(f"ok: {t.name}")

    if total_errors:
        print(f"\n{len(total_errors)} problem(s) across {checked} skill(s):", file=sys.stderr)
        for e in total_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print(f"\nok: {checked} skill(s) validated against the agentskills.io standard")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
