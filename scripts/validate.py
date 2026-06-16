#!/usr/bin/env python3
"""Validate Ottili ONE skills repository structure and catalog consistency."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "catalog.json"
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
NAME_RE = re.compile(r"^name:\s*(.+)$", re.MULTILINE)
DESC_RE = re.compile(r"^description:\s*(.+)$", re.MULTILINE)


def load_catalog() -> dict:
    with CATALOG_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def parse_frontmatter(skill_md: Path) -> dict[str, str]:
    text = skill_md.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"missing YAML frontmatter: {skill_md}")
    block = match.group(1)
    fields: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line or line.strip().startswith("#"):
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields


def validate_skill_entry(entry: dict, packages: dict) -> list[str]:
    errors: list[str] = []
    skill_id = entry["id"]
    package = entry["package"]
    rel_path = Path(entry["path"])
    skill_dir = ROOT / rel_path
    skill_md = skill_dir / "SKILL.md"

    if package not in packages:
        errors.append(f"{skill_id}: unknown package '{package}'")
    expected_pkg_path = Path(packages.get(package, {}).get("path", ""))
    if expected_pkg_path and not str(rel_path).startswith(str(expected_pkg_path)):
        errors.append(f"{skill_id}: path '{rel_path}' not under package path '{expected_pkg_path}'")

    if not skill_dir.is_dir():
        errors.append(f"{skill_id}: directory missing: {skill_dir}")
        return errors

    if not skill_md.is_file():
        errors.append(f"{skill_id}: SKILL.md missing: {skill_md}")
        return errors

    try:
        frontmatter = parse_frontmatter(skill_md)
    except ValueError as exc:
        errors.append(f"{skill_id}: {exc}")
        return errors

    if frontmatter.get("name") != entry["name"]:
        errors.append(
            f"{skill_id}: catalog name '{entry['name']}' != SKILL.md name '{frontmatter.get('name')}'"
        )

    if skill_dir.name != entry["name"]:
        errors.append(
            f"{skill_id}: directory '{skill_dir.name}' must match skill name '{entry['name']}'"
        )

    if not frontmatter.get("description"):
        errors.append(f"{skill_id}: SKILL.md missing description in frontmatter")

    return errors


def validate_catalog(catalog: dict) -> list[str]:
    errors: list[str] = []
    packages = catalog.get("packages", {})
    skills = catalog.get("skills", [])
    seen_ids: set[str] = set()
    seen_names: set[str] = set()

    for entry in skills:
        skill_id = entry.get("id", "<missing>")
        if skill_id in seen_ids:
            errors.append(f"duplicate catalog id: {skill_id}")
        seen_ids.add(skill_id)

        name = entry.get("name", "")
        if name in seen_names:
            errors.append(f"duplicate skill name: {name}")
        seen_names.add(name)

        errors.extend(validate_skill_entry(entry, packages))

    return errors


def main() -> int:
    if not CATALOG_PATH.is_file():
        print(f"error: catalog not found at {CATALOG_PATH}", file=sys.stderr)
        return 1

    catalog = load_catalog()
    errors = validate_catalog(catalog)

    if errors:
        print("validation failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"ok: {len(catalog.get('skills', []))} skills validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
