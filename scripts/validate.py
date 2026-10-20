#!/usr/bin/env python3
"""Validate the Ottili skills repository: the catalogue against the tree on disk.

Two scopes:

* the **default** scope validates the committed ``catalog.json`` entry by entry
  against the skill folders it points at, and
* ``--everywhere`` additionally walks the WHOLE ``skills/`` tree and reports a
  skill folder the catalogue does not know about (and a catalogue entry that has
  no folder on disk).

The machine-readable output of this tool is the versioned contract
``ottili.skills.validate-report/v1``. Its JSON Schema lives in
``scripts/ottili_contracts/schemas/ottili.skills.validate-report.v1.schema.json``,
its typed (pydantic) view in ``scripts/ottili_contracts/models.py`` and a worked
example in ``scripts/ottili_contracts/examples/``.

This module is deliberately dependency-free (standard library only): it runs on
the CI runner before any package is installed, and the contract tests copy it
into throwaway fixture trees where nothing else of the repository exists.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "catalog.json"

#: The contract id of the machine-readable report. Bump it only together with a
#: new JSON Schema file in ``scripts/ottili_contracts/schemas/``.
CONTRACT_ID = "ottili.skills.validate-report/v1"

SCOPE_CATALOG = "catalog"
SCOPE_EVERYWHERE = "everywhere"

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def load_catalog(path: Path = CATALOG_PATH) -> dict[str, Any]:
    """Read the generated catalogue.

    Inputs:
        path: the ``catalog.json`` file to read.
    Outputs:
        the parsed catalogue as a mapping.
    Failure modes:
        FileNotFoundError when the file does not exist, json.JSONDecodeError
        when the file is not valid JSON. Both are caught by :func:`main`, which
        reports them on stderr and exits with :data:`EXIT_USAGE`.
    """
    with path.open(encoding="utf-8") as handle:
        catalog = json.load(handle)
    if not isinstance(catalog, dict):
        raise ValueError(f"catalogue must be a JSON object, got {type(catalog).__name__}")
    return catalog


def parse_frontmatter(skill_md: Path) -> dict[str, str]:
    """Read the YAML frontmatter of a ``SKILL.md`` as flat ``key: value`` pairs.

    Inputs:
        skill_md: the ``SKILL.md`` file to read.
    Outputs:
        a mapping of the frontmatter keys to their raw (unquoted) values.
    Failure modes:
        OSError when the file cannot be read, ValueError when the file has no
        YAML frontmatter block. The caller turns the ValueError into a finding
        and skips that skill.
    """
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


def validate_skill_entry(entry: dict[str, Any], packages: dict[str, Any]) -> list[str]:
    """Validate one catalogue entry against the folder it points at.

    Inputs:
        entry: one entry of ``catalog.json``.
        packages: the ``packages`` mapping of the catalogue.
    Outputs:
        a list of findings; an empty list means the entry is consistent.
    Failure modes:
        none. A missing folder or a broken ``SKILL.md`` is reported as a
        finding, not raised, so that one broken skill never hides the others.
    """
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


def validate_catalog(catalog: dict[str, Any]) -> list[str]:
    """Validate the catalogue against itself and against the tree it points at.

    Inputs:
        catalog: the parsed ``catalog.json``.
    Outputs:
        a list of findings; an empty list means the catalogue is consistent.
    Failure modes:
        KeyError when an entry lacks the fields the catalogue format requires.
        The caller treats that as a broken catalogue and exits with
        :data:`EXIT_USAGE`.
    """
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


def scan_tree(root: Path = ROOT) -> dict[str, list[str]]:
    """Map every skill folder name of the tree to the folders that carry it.

    Inputs:
        root: the repository root whose ``skills/`` tree is scanned.
    Outputs:
        a mapping of folder name to the sorted relative paths of the folders
        with that name. A name that lives in two packages maps to two paths.
    Failure modes:
        OSError when the tree cannot be walked; unreadable sub-trees are
        skipped by the caller, an unreadable root is fatal.
    """
    found: dict[str, list[str]] = {}
    skills_root = root / "skills"
    if not skills_root.is_dir():
        return found
    for skill_dir in sorted(skills_root.rglob("*")):
        if not skill_dir.is_dir():
            continue
        if not (skill_dir / "SKILL.md").is_file():
            continue
        rel = skill_dir.relative_to(root).as_posix()
        found.setdefault(skill_dir.name, []).append(rel)
    return found


def validate_tree(catalog: dict[str, Any], root: Path = ROOT) -> list[str]:
    """Cross-check the whole ``skills/`` tree against the catalogue.

    One folder name can live in more than one package. A mapping that keeps
    only the LAST folder of a name silently drops the other one, so a skill
    that is missing from the catalogue would stay invisible. Every folder of a
    name is therefore kept, and a name that lives twice is reported as the
    duplicate it is.

    Inputs:
        catalog: the parsed ``catalog.json``.
        root: the repository root whose ``skills/`` tree is scanned.
    Outputs:
        a list of findings; an empty list means the tree and the catalogue
        describe the same set of skills.
    Failure modes:
        none. Every inconsistency is a finding.
    """
    errors: list[str] = []
    on_disk = scan_tree(root)
    catalog_names = {entry["name"] for entry in catalog.get("skills", [])}
    for name, found in sorted(on_disk.items()):
        if len(found) > 1:
            errors.append(
                f"duplicate skill name '{name}' on disk: {', '.join(sorted(found))}"
            )
        if name not in catalog_names:
            errors.append(f"on-disk skill '{name}' ({found[0]}) is missing from the catalog")
    for name in sorted(catalog_names - set(on_disk)):
        errors.append(f"catalog entry '{name}' has no SKILL.md on disk")
    return errors


def build_report(scope: str, catalog: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    """Build the machine-readable report of contract ``v1``.

    Inputs:
        scope: ``"catalog"`` or ``"everywhere"``; the scope that was validated.
        catalog: the parsed ``catalog.json`` (for the number of skills).
        errors: the findings of that scope.
    Outputs:
        a mapping that validates against
        ``ottili.skills.validate-report.v1.schema.json``.
    Failure modes:
        none. The report is built from data that is already in memory.
    """
    return {
        "contract": CONTRACT_ID,
        "scope": scope,
        "skills": len(catalog.get("skills", [])),
        "errors": list(errors),
        "ok": not errors,
    }


def render_json(report: dict[str, Any]) -> str:
    """Render the report as a single JSON object.

    Inputs:
        report: the mapping built by :func:`build_report`.
    Outputs:
        the report as pretty-printed JSON with a trailing newline.
    Failure modes:
        TypeError when the report holds a value ``json`` cannot serialise.
        The report only holds strings, integers and booleans, so this cannot
        happen for a report built by :func:`build_report`.
    """
    return json.dumps(report, indent=2) + "\n"


def render_jsonl(report: dict[str, Any]) -> str:
    """Render the report as JSON Lines: one JSON object per line.

    The first line is the summary, every further line is one finding. The
    format is a stream: a consumer can read it line by line without knowing
    the number of findings in advance.

    Inputs:
        report: the mapping built by :func:`build_report`.
    Outputs:
        the report as JSON Lines with a trailing newline.
    Failure modes:
        TypeError when a finding holds a value ``json`` cannot serialise.
    """
    lines = [
        json.dumps(
            {
                "contract": report["contract"],
                "kind": "summary",
                "scope": report["scope"],
                "skills": report["skills"],
                "findings": len(report["errors"]),
                "ok": report["ok"],
            }
        )
    ]
    lines.extend(
        json.dumps(
            {
                "contract": report["contract"],
                "kind": "finding",
                "scope": report["scope"],
                "message": message,
            }
        )
        for message in report["errors"]
    )
    return "\n".join(lines) + "\n"


def render_human(report: dict[str, Any]) -> tuple[str, str]:
    """Render the report as human-readable text.

    Inputs:
        report: the mapping built by :func:`build_report`.
    Outputs:
        a tuple of (stdout text, stderr text). On success the stdout text is
        ``ok: N skills validated``; on failure the stdout text is empty and
        the stderr text holds the header and one indented finding per line.
    Failure modes:
        none.
    """
    if report["ok"]:
        return f"ok: {report['skills']} skills validated\n", ""
    lines = ["validation failed:"]
    lines.extend(f"  - {message}" for message in report["errors"])
    return "", "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    """Build the command line parser.

    Inputs:
        none.
    Outputs:
        the parser of the tool.
    Failure modes:
        none. ``--help`` prints the usage text and exits 0, an unknown flag
        makes argparse print its usage on stderr and exit 2.
    """
    parser = argparse.ArgumentParser(
        prog="validate.py",
        description=(
            "Validate the Ottili skills repository: the generated catalogue "
            "against the skill folders on disk."
        ),
        epilog=(
            "exit codes:\n"
            "  0  no findings\n"
            "  1  at least one finding (listed on stderr, or in the report)\n"
            "  2  usage error, or the catalogue is missing or unreadable\n"
            "\n"
            "output formats:\n"
            "  (default)  human text: 'ok: N skills validated' or one finding per line\n"
            "  --json     one JSON object (contract ottili.skills.validate-report/v1)\n"
            "  --jsonl    JSON Lines: a summary line, then one line per finding\n"
            "\n"
            "examples:\n"
            "  python3 scripts/validate.py --everywhere\n"
            "  python3 scripts/validate.py --everywhere --json\n"
            "  python3 scripts/validate.py --everywhere --jsonl\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="machine-readable report on stdout (contract ottili.skills.validate-report/v1)",
    )
    parser.add_argument(
        "--jsonl",
        action="store_true",
        help="machine-readable report as JSON Lines on stdout (one summary line, one line per finding)",
    )
    parser.add_argument(
        "--everywhere",
        action="store_true",
        help="validate every skill in the repository (not just the catalogue)",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="print the contract id of the machine-readable report and exit 0",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the validator.

    Inputs:
        argv: the command line arguments; ``None`` means ``sys.argv[1:]``.
    Outputs:
        the process exit code: 0 without findings, 1 with findings, 2 for a
        usage error or an unreadable catalogue.
    Failure modes:
        an unreadable or malformed ``catalog.json`` is reported on stderr and
        exits 2. Every other inconsistency is a finding and exits 1.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(f"validate.py — contract {CONTRACT_ID}")
        return EXIT_OK

    if not CATALOG_PATH.is_file():
        print(f"error: catalog not found at {CATALOG_PATH}", file=sys.stderr)
        return EXIT_USAGE

    try:
        catalog = load_catalog()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: catalog is not readable: {CATALOG_PATH}: {exc}", file=sys.stderr)
        return EXIT_USAGE

    scope = SCOPE_EVERYWHERE if args.everywhere else SCOPE_CATALOG
    try:
        errors = validate_catalog(catalog)
    except KeyError as exc:
        print(f"error: catalog entry is missing a required field: {exc}", file=sys.stderr)
        return EXIT_USAGE

    if args.everywhere:
        errors.extend(validate_tree(catalog))

    report = build_report(scope, catalog, errors)

    if args.jsonl:
        sys.stdout.write(render_jsonl(report))
    elif args.json:
        sys.stdout.write(render_json(report))
    else:
        stdout_text, stderr_text = render_human(report)
        if stdout_text:
            sys.stdout.write(stdout_text)
        if stderr_text:
            sys.stderr.write(stderr_text)

    return EXIT_OK if report["ok"] else EXIT_FINDINGS


if __name__ == "__main__":
    raise SystemExit(main())
