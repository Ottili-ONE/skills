#!/usr/bin/env python3
"""Static gate for a Postgres migration that touches tenant-scoped tables.

Every tenant table in the migration must, per table:
  (a) be created with ENABLE + FORCE ROW LEVEL SECURITY,
  (b) carry a tenant policy that reads the canonical tenant GUC, and
  (c) carry a ``company_id`` discriminator column that is NOT NULL.

The tenant convention is configuration, not a constant of this script: it
lives in ``guc-names.json`` next to this skill (override with ``--guc-names``).
The convention names exactly one tenant GUC - ``app.company_id`` - because
that is the name the product repositories set in a session. A policy keyed on
any other name is a finding: nothing sets that name, so the policy isolates
nobody.

The rules live in the ``ottili_rls`` package next to this file: this script is
the adapter that reads files, prints the verdict and returns an exit code.

Exit codes: 0 = PASS, 1 = findings, 2 = malformed input.
Usage: check_rls_migration.py <migration.sql> [<migration.sql> ...]
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from ottili_rls.convention import ConventionError, load_convention
from ottili_rls.logging import configure_logging, log_event, new_run_id
from ottili_rls.rules import canonical_gucs_used, evaluate_migration
from ottili_rls.scanner import collect_facts, split_statements

SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_GUC_FILE = SKILL_DIR / "guc-names.json"


def build_parser() -> argparse.ArgumentParser:
    """Return the command line of the checker."""
    ap = argparse.ArgumentParser(description="Check tenant RLS in a migration.")
    ap.add_argument("migrations", nargs="*", help="migration SQL file(s) to check")
    ap.add_argument(
        "--guc-names",
        default=str(DEFAULT_GUC_FILE),
        help="JSON file with the tenant convention",
    )
    ap.add_argument(
        "--json", action="store_true", help="emit machine-readable JSON instead of text"
    )
    ap.add_argument(
        "--list-guc-names",
        action="store_true",
        help="print the accepted tenant GUC names (one per line) and exit",
    )
    ap.add_argument(
        "--log-level",
        default="WARNING",
        help="level of the structured run log (default WARNING)",
    )
    return ap


def main() -> int:
    """Check the migrations named on the command line."""
    args = build_parser().parse_args()
    logger = configure_logging(args.log_level)
    run_id = new_run_id()

    try:
        convention = load_convention(Path(args.guc_names))
    except ConventionError as exc:
        print(
            f"FAIL: cannot read the accepted tenant GUC names from "
            f"{args.guc_names}: {exc}",
            file=sys.stderr,
        )
        return 2

    if args.list_guc_names:
        for name in convention.accepted_names:
            print(name)
        return 0

    if not args.migrations:
        print(
            "FAIL: no migration file given "
            "(usage: check_rls_migration.py <migration.sql> ...)",
            file=sys.stderr,
        )
        return 2

    failures = 0
    malformed = False
    reports: list[dict[str, object]] = []
    for path in args.migrations:
        migration = Path(path)
        if not migration.is_file():
            print(f"FAIL: {path}: file not found", file=sys.stderr)
            malformed = True
            continue
        text = migration.read_text(encoding="utf-8", errors="ignore")
        findings = evaluate_migration(text, convention)
        facts = collect_facts(split_statements(text))
        reports.append(
            {
                "file": str(migration.resolve()),
                "findings": [finding.render() for finding in findings],
                "guc_used": sorted(canonical_gucs_used(facts, convention)),
            }
        )
        if findings:
            failures += 1
            if not args.json:
                print(f"FAIL: {path}")
            for finding in findings:
                print(f"  - {finding.render()}", file=sys.stderr)
        elif not args.json:
            print(f"ok: {path}")
        log_event(
            logger,
            logging.INFO,
            "migration checked",
            run_id,
            file=str(migration),
            findings=len(findings),
        )

    if args.json:
        print(
            json.dumps(
                {
                    "status": "fail" if (failures or malformed) else "ok",
                    "files_checked": len(args.migrations),
                    "failures": failures,
                    "malformed": malformed,
                    "guc_names": list(convention.accepted_names),
                    "reports": reports,
                },
                indent=2,
                sort_keys=True,
            )
        )
    if malformed:
        return 2
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
