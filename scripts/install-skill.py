#!/usr/bin/env python3
"""Install skills from the Ottili ONE skills repository to agent skill directories."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "catalog.json"

AGENT_TARGETS = {
    "codex": Path.home() / ".codex" / "skills",
    "claude": Path.home() / ".claude" / "skills",
    "cursor": Path.home() / ".cursor" / "skills",
    "agents": Path.home() / ".agents" / "skills",
}


def load_catalog() -> dict:
    with CATALOG_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def find_skill(catalog: dict, skill_name: str) -> dict | None:
    for entry in catalog.get("skills", []):
        if entry["name"] == skill_name or entry["id"] == skill_name:
            return entry
    return None


def install_skill(entry: dict, dest_root: Path, force: bool) -> None:
    src = ROOT / entry["path"]
    dest = dest_root / entry["name"]

    if not src.is_dir():
        raise FileNotFoundError(f"skill source not found: {src}")

    if dest.exists():
        if not force:
            raise FileExistsError(f"destination already exists: {dest} (use --force to overwrite)")
        shutil.rmtree(dest)

    dest_root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest)
    print(f"installed {entry['name']} -> {dest}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Ottili ONE skills")
    parser.add_argument("skill", nargs="?", help="Skill name or id from catalog.json")
    parser.add_argument("--target", choices=list(AGENT_TARGETS.keys()), default="codex")
    parser.add_argument("--dest", type=Path, help="Override destination directory")
    parser.add_argument("--list", action="store_true", help="List installable skills")
    parser.add_argument("--force", action="store_true", help="Overwrite existing installation")
    args = parser.parse_args()

    if not CATALOG_PATH.is_file():
        print(f"error: catalog not found at {CATALOG_PATH}", file=sys.stderr)
        return 1

    catalog = load_catalog()

    if args.list:
        for entry in catalog.get("skills", []):
            print(f"{entry['name']:24s} [{entry.get('package', '?')}]")
        return 0

    if not args.skill:
        parser.error("provide a skill name or use --list")

    entry = find_skill(catalog, args.skill)
    if entry is None:
        print(f"error: skill '{args.skill}' not found in catalog", file=sys.stderr)
        return 1

    dest_root = args.dest or AGENT_TARGETS[args.target]

    try:
        install_skill(entry, dest_root, args.force)
    except (FileNotFoundError, FileExistsError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"restart your agent to load the new skill")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
