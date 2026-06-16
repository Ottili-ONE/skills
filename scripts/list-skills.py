#!/usr/bin/env python3
"""List skills from the Ottili ONE skills catalog."""

from __future__ import annotations

import argparse
import json
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


def is_installed(skill_name: str, target: Path | None) -> bool:
    if target is None:
        return False
    return (target / skill_name).is_dir()


def filter_skills(catalog: dict, package: str | None) -> list[dict]:
    skills = catalog.get("skills", [])
    if package:
        return [s for s in skills if s.get("package") == package]
    return skills


def main() -> int:
    parser = argparse.ArgumentParser(description="List Ottili ONE skills")
    parser.add_argument("--package", help="Filter by package (core, curated, community, ottili-ai)")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--target", choices=list(AGENT_TARGETS.keys()), help="Mark installed skills for target")
    args = parser.parse_args()

    if not CATALOG_PATH.is_file():
        print(f"error: catalog not found at {CATALOG_PATH}", file=sys.stderr)
        return 1

    catalog = load_catalog()
    skills = filter_skills(catalog, args.package)
    install_target = AGENT_TARGETS.get(args.target or "", None)

    if args.format == "json":
        print(json.dumps(skills, indent=2))
        return 0

    packages = catalog.get("packages", {})
    current_pkg = None
    for entry in skills:
        pkg = entry.get("package", "")
        if pkg != current_pkg:
            current_pkg = pkg
            label = packages.get(pkg, {}).get("label", pkg)
            print(f"\n[{label}]")
        installed = ""
        if install_target is not None:
            installed = " (installed)" if is_installed(entry["name"], install_target) else ""
        version = entry.get("version", "")
        version_suffix = f" v{version}" if version else ""
        print(f"  - {entry['name']}{version_suffix}{installed}")
        print(f"    {entry.get('description', '')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
