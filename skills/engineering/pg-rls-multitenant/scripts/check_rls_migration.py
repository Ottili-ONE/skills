#!/usr/bin/env python3
"""Static gate for a Postgres migration that touches tenant-scoped tables.

Every tenant table in the migration must, per table:
  (a) be created with ENABLE + FORCE ROW LEVEL SECURITY,
  (b) carry a tenant policy whose setting name is an accepted tenant GUC, and
  (c) carry a ``company_id`` discriminator column.

The accepted GUC names are configuration, not a constant of this script: they
live in ``guc-names.json`` next to this file (override with ``--guc-names``).
The product repositories use more than one name today and the canonical name
for all of them is an open owner decision that this repository does not make;
the measured inventory is in ``docs/truth/REPAIR_LOG.md``.

Exit codes: 0 = PASS, 1 = findings, 2 = malformed input.
Usage: check_rls_migration.py <migration.sql> [<migration.sql> ...]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_GUC_FILE = SKILL_DIR / "guc-names.json"

# A qualified SQL identifier: "notes" or "public.notes".
IDENT = r"[A-Za-z_][\w$]*(?:\.[A-Za-z_][\w$]*)?"
CREATE_TABLE_RE = re.compile(
    r"^\s*CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<name>" + IDENT + r")\s*\(",
    re.IGNORECASE,
)
ALTER_TABLE_RE = re.compile(
    r"^\s*ALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?:ONLY\s+)?(?P<name>" + IDENT + r")\s+(?P<action>.*)$",
    re.IGNORECASE | re.DOTALL,
)
CREATE_POLICY_RE = re.compile(
    r"^\s*CREATE\s+POLICY\s+(?P<pname>[^\s]+)\s+ON\s+(?P<name>" + IDENT + r")\b(?P<body>.*)$",
    re.IGNORECASE | re.DOTALL,
)
GRANT_ALL_RE = re.compile(r"\bGRANT\s+ALL\b", re.IGNORECASE)
ENABLE_RE = re.compile(r"\bENABLE\s+ROW\s+LEVEL\s+SECURITY\b", re.IGNORECASE)
FORCE_RE = re.compile(r"\bFORCE\s+ROW\s+LEVEL\s+SECURITY\b", re.IGNORECASE)
NO_FORCE_RE = re.compile(r"\bNO\s+FORCE\s+ROW\s+LEVEL\s+SECURITY\b", re.IGNORECASE)
COMPANY_ID_RE = re.compile(r"\bcompany_id\b", re.IGNORECASE)
GUC_USE_RE = re.compile(
    r"current_setting\(\s*'(?P<guc>[A-Za-z_][\w]*\.[A-Za-z_][\w]*)'", re.IGNORECASE
)
DOLLAR_TAG_RE = re.compile(r"\$(?P<tag>[A-Za-z_]\w*)?\$")
DOLLAR_BODY_RE = re.compile(
    r"\$(?P<tag>[A-Za-z_]\w*)?\$(?P<body>.*?)\$(?P=tag)\$", re.DOTALL
)


def load_guc_names(path: Path) -> list[str]:
    """Read the accepted tenant GUC names from the configuration file.

    The configuration is the single source of truth: this script must not
    hard-code a tenant setting name, because the repositories disagree about
    it and the decision belongs to the owner.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data["accepted_names"]
    names = [
        str(entry["name"] if isinstance(entry, dict) else entry) for entry in entries
    ]
    if not names:
        raise ValueError("accepted_names is empty")
    return names


def _end_of_string(sql: str, start: int) -> int:
    """Return the index just after the string literal that starts at ``start``."""
    index = start + 1
    length = len(sql)
    while index < length:
        if sql[index] == "'":
            if index + 1 < length and sql[index + 1] == "'":
                index += 2
                continue
            return index + 1
        index += 1
    return length


def split_statements(sql: str) -> list[str]:
    """Split SQL into statements.

    Comments become spaces (a comment is prose, not DDL), string literals and
    dollar-quoted bodies survive verbatim, and a ``;`` inside a literal does
    not end a statement.
    """
    statements: list[str] = []
    buf: list[str] = []
    index = 0
    length = len(sql)
    while index < length:
        char = sql[index]
        if char == "-" and sql.startswith("--", index):
            end = sql.find("\n", index)
            end = length if end == -1 else end
            buf.append(" " * (end - index))
            index = end
            continue
        if char == "/" and sql.startswith("/*", index):
            end = sql.find("*/", index + 2)
            end = length if end == -1 else end + 2
            buf.append(" " * (end - index))
            index = end
            continue
        if char == "'":
            end = _end_of_string(sql, index)
            buf.append(sql[index:end])
            index = end
            continue
        if char == "$":
            match = DOLLAR_TAG_RE.match(sql, index)
            if match:
                tag = match.group(0)
                end = sql.find(tag, match.end())
                end = length if end == -1 else end + len(tag)
                buf.append(sql[index:end])
                index = end
                continue
        if char == ";":
            statements.append("".join(buf))
            buf = []
            index += 1
            continue
        buf.append(char)
        index += 1
    tail = "".join(buf)
    if tail.strip():
        statements.append(tail)
    return statements


def _dollar_bodies(statement: str) -> list[str]:
    """Return the contents of the dollar-quoted bodies inside a statement."""
    return [match.group("body") for match in DOLLAR_BODY_RE.finditer(statement)]


def _table_body(text: str, open_index: int) -> str:
    """Return the column list of a CREATE TABLE, without the outer parentheses."""
    depth = 0
    index = open_index
    length = len(text)
    while index < length:
        char = text[index]
        if char == "'":
            index = _end_of_string(text, index)
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return text[open_index + 1:index]
        index += 1
    return text[open_index + 1:]


def _base(name: str) -> str:
    """Schema-qualified names are compared by their bare table name."""
    return name.split(".")[-1].lower()


class MigrationFacts:
    """What a migration says about tenant tables."""

    def __init__(self) -> None:
        self.created: dict[str, str] = {}
        self.enabled: set[str] = set()
        self.forced: set[str] = set()
        self.policies: dict[str, list[str]] = {}

    def tables(self) -> set[str]:
        return set(self.created) | set(self.enabled) | set(self.forced) | set(self.policies)


def collect(statements: list[str], facts: MigrationFacts, depth: int = 0) -> None:
    """Read the tenant facts out of a list of SQL statements.

    A policy inside a ``DO $$ ... $$`` block is a policy: the block is scanned
    as well, so the checker does not depend on how a migration spells it.
    """
    if depth > 3:
        return
    for statement in statements:
        text = statement.strip()
        if not text:
            continue
        match = CREATE_TABLE_RE.match(text)
        if match:
            facts.created[_base(match.group("name"))] = _table_body(
                text, text.index("(", match.end() - 1)
            )
            continue
        match = ALTER_TABLE_RE.match(text)
        if match:
            name = _base(match.group("name"))
            action = match.group("action")
            if ENABLE_RE.search(action):
                facts.enabled.add(name)
            if FORCE_RE.search(action) and not NO_FORCE_RE.search(action):
                facts.forced.add(name)
            continue
        match = CREATE_POLICY_RE.match(text)
        if match:
            facts.policies.setdefault(_base(match.group("name")), []).append(
                match.group("body")
            )
            continue
        for body in _dollar_bodies(text):
            collect(split_statements(body), facts, depth + 1)


def scan(text: str, guc_names: list[str]) -> tuple[list[str], list[str]]:
    """Check one migration. Returns (findings, accepted GUC names actually used)."""
    statements = split_statements(text)
    facts = MigrationFacts()
    collect(statements, facts)
    accepted = {name.lower() for name in guc_names}
    findings: list[str] = []
    used: set[str] = set()

    for table in sorted(facts.tables()):
        policies = facts.policies.get(table, [])
        body = facts.created.get(table, "")
        # A table this file creates must be protected here and now. A table that
        # already exists is only held to what this file touches: the file that
        # created it is the one that had to switch RLS on.
        created_here = table in facts.created
        # (c) the tenant discriminator column: from the column list of a table
        # created here, otherwise from the policy that guards the table.
        if created_here:
            if not COMPANY_ID_RE.search(body):
                findings.append(f"{table}: no company_id tenant discriminator column")
        elif policies and not any(COMPANY_ID_RE.search(p) for p in policies):
            findings.append(f"{table}: no company_id tenant discriminator column")
        # (a) ENABLE + FORCE, per table. The file that creates a tenant table is
        # the file that has to switch RLS on; an existing table keeps the state
        # of its own migration, so this file is not held to it.
        if created_here:
            if table not in facts.enabled:
                findings.append(f"{table}: missing ENABLE ROW LEVEL SECURITY")
            if table not in facts.forced:
                findings.append(
                    f"{table}: missing FORCE ROW LEVEL SECURITY (owner would bypass RLS)"
                )
        # (b) a tenant policy keyed on an accepted tenant GUC.
        if created_here or policies:
            if not policies:
                findings.append(f"{table}: no CREATE POLICY for tenant isolation")
            else:
                keys = {
                    match.group("guc").lower()
                    for policy in policies
                    for match in GUC_USE_RE.finditer(policy)
                }
                hit = keys & accepted
                used |= hit
                if not hit:
                    findings.append(
                        f"{table}: tenant policy is not keyed on an accepted tenant GUC "
                        f"({', '.join(sorted(accepted))})"
                    )

    clean = " ".join(statements)
    if GRANT_ALL_RE.search(clean):
        findings.append("GRANT ALL on a protected table overrides the policy grant")
    return findings, sorted(used)


def main() -> int:
    ap = argparse.ArgumentParser(description="Check tenant RLS in a migration.")
    ap.add_argument(
        "migrations", nargs="*", help="migration SQL file(s) to check"
    )
    ap.add_argument(
        "--guc-names",
        default=str(DEFAULT_GUC_FILE),
        help="JSON file with the accepted tenant GUC names",
    )
    ap.add_argument(
        "--json", action="store_true", help="emit machine-readable JSON instead of text"
    )
    ap.add_argument(
        "--list-guc-names",
        action="store_true",
        help="print the accepted tenant GUC names (one per line) and exit",
    )
    args = ap.parse_args()

    try:
        guc_names = load_guc_names(Path(args.guc_names))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(
            f"FAIL: cannot read the accepted tenant GUC names from "
            f"{args.guc_names}: {exc}",
            file=sys.stderr,
        )
        return 2

    if args.list_guc_names:
        for name in guc_names:
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
    reports: list[dict] = []
    for path in args.migrations:
        p = Path(path)
        if not p.is_file():
            print(f"FAIL: {path}: file not found", file=sys.stderr)
            malformed = True
            continue
        findings, used = scan(p.read_text(encoding="utf-8", errors="ignore"), guc_names)
        reports.append(
            {"file": str(p.resolve()), "findings": findings, "guc_used": used}
        )
        if findings:
            failures += 1
            if not args.json:
                print(f"FAIL: {path}")
            for finding in findings:
                print(f"  - {finding}", file=sys.stderr)
        elif not args.json:
            print(f"ok: {path}")
    if args.json:
        print(json.dumps({
            "status": "fail" if (failures or malformed) else "ok",
            "files_checked": len(args.migrations),
            "failures": failures,
            "malformed": malformed,
            "guc_names": guc_names,
            "reports": reports,
        }, indent=2, sort_keys=True))
    if malformed:
        return 2
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
