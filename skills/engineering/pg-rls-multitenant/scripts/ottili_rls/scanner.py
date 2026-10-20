"""Reading the tenant facts out of a SQL migration.

The scanner is pure: it takes the text of a migration and returns what that
migration says about its tables. It never touches the file system, never
prints and never decides whether a migration is acceptable - that is the job
of the rules.
"""
from __future__ import annotations

import re

from .models import MigrationFacts, TableFacts

# A qualified SQL identifier: "notes" or "public.notes".
IDENT = r"[A-Za-z_][\w$]*(?:\.[A-Za-z_][\w$]*)?"
CREATE_TABLE_RE = re.compile(
    r"^\s*CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<name>" + IDENT + r")\s*\(",
    re.IGNORECASE,
)
ALTER_TABLE_RE = re.compile(
    r"^\s*ALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?:ONLY\s+)?(?P<name>" + IDENT
    + r")\s+(?P<action>.*)$",
    re.IGNORECASE | re.DOTALL,
)
CREATE_POLICY_RE = re.compile(
    r"^\s*CREATE\s+POLICY\s+(?P<pname>[^\s]+)\s+ON\s+(?P<name>" + IDENT
    + r")\b(?P<body>.*)$",
    re.IGNORECASE | re.DOTALL,
)
# Inside a PL/pgSQL body the statement follows a condition and therefore does
# not start the fragment:
#   IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE ...) THEN ALTER TABLE t ENABLE ROW LEVEL SECURITY;
# These variants are used only for the statements of a dollar-quoted body, so a
# top-level statement keeps its strict, anchored reading.
ALTER_TABLE_LOOSE_RE = re.compile(
    r"\bALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?:ONLY\s+)?(?P<name>" + IDENT
    + r")\s+(?P<action>.*)$",
    re.IGNORECASE | re.DOTALL,
)
CREATE_POLICY_LOOSE_RE = re.compile(
    r"\bCREATE\s+POLICY\s+(?P<pname>[^\s]+)\s+ON\s+(?P<name>" + IDENT + r")\b(?P<body>.*)$",
    re.IGNORECASE | re.DOTALL,
)
ENABLE_RE = re.compile(r"\bENABLE\s+ROW\s+LEVEL\s+SECURITY\b", re.IGNORECASE)
FORCE_RE = re.compile(r"\bFORCE\s+ROW\s+LEVEL\s+SECURITY\b", re.IGNORECASE)
NO_FORCE_RE = re.compile(r"\bNO\s+FORCE\s+ROW\s+LEVEL\s+SECURITY\b", re.IGNORECASE)
# The setting name is written once as `current_setting('app.company_id', true)`
# and twice as `current_setting(''app.company_id'', true)` when the policy is
# created with EXECUTE and the inner quotes are escaped.
GUC_USE_RE = re.compile(
    r"current_setting\(\s*'{1,2}(?P<guc>[A-Za-z_][\w]*\.[A-Za-z_][\w]*)'{1,2}",
    re.IGNORECASE,
)
DOLLAR_TAG_RE = re.compile(r"\$(?P<tag>[A-Za-z_]\w*)?\$")
DOLLAR_BODY_RE = re.compile(
    r"\$(?P<tag>[A-Za-z_]\w*)?\$(?P<body>.*?)\$(?P<ctag>[A-Za-z_]\w*)?\$", re.DOTALL
)


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


def collect_facts(statements: list[str]) -> MigrationFacts:
    """Read the tenant facts out of a list of SQL statements.

    A policy inside a ``DO $$ ... $$`` block is a policy: the block is scanned
    as well, so the checker does not depend on how a migration spells it. A
    statement of such a block may follow a condition
    (``IF NOT EXISTS (...) THEN ALTER TABLE t ENABLE ROW LEVEL SECURITY;``),
    so inside a body the keyword is looked for anywhere in the fragment and
    not only at its start.
    """
    created: dict[str, str] = {}
    enabled: set[str] = set()
    forced: set[str] = set()
    policies: dict[str, list[str]] = {}
    _collect(statements, created, enabled, forced, policies, depth=0)
    names = sorted(set(created) | set(enabled) | set(forced) | set(policies))
    tables = tuple(
        TableFacts(
            name=name,
            created_here=name in created,
            column_list=created.get(name, ""),
            enabled_rls=name in enabled,
            forced_rls=name in forced,
            policies=tuple(policies.get(name, [])),
        )
        for name in names
    )
    return MigrationFacts(tables=tables)


def split_column_definitions(column_list: str) -> list[str]:
    """Split a column list into its definitions.

    A comma inside parentheses or inside a string literal does not separate
    two columns, so ``PRIMARY KEY (company_id, id)`` stays one definition.
    """
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    index = 0
    length = len(column_list)
    while index < length:
        char = column_list[index]
        if char == "'":
            end = _end_of_string(column_list, index)
            buf.append(column_list[index:end])
            index = end
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        if char == "," and depth == 0:
            parts.append("".join(buf))
            buf = []
            index += 1
            continue
        buf.append(char)
        index += 1
    tail = "".join(buf)
    if tail.strip():
        parts.append(tail)
    return parts


def guc_names_in(text: str) -> set[str]:
    """Return the lower-cased setting names a fragment reads."""
    return {match.group("guc").lower() for match in GUC_USE_RE.finditer(text)}


def _collect(
    statements: list[str],
    created: dict[str, str],
    enabled: set[str],
    forced: set[str],
    policies: dict[str, list[str]],
    depth: int,
) -> None:
    """Collect the facts of one level of statements."""
    if depth > 3:
        return
    for statement in statements:
        text = statement.strip()
        if not text:
            continue
        match = CREATE_TABLE_RE.match(text)
        if match is not None:
            created[_base(match.group("name"))] = _table_body(
                text, text.index("(", match.end() - 1)
            )
        match = ALTER_TABLE_RE.match(text)
        if match is None and depth:
            match = ALTER_TABLE_LOOSE_RE.search(text)
        if match is not None:
            name = _base(match.group("name"))
            action = match.group("action")
            if ENABLE_RE.search(action):
                enabled.add(name)
            if FORCE_RE.search(action) and not NO_FORCE_RE.search(action):
                forced.add(name)
        match = CREATE_POLICY_RE.match(text)
        if match is None and depth:
            match = CREATE_POLICY_LOOSE_RE.search(text)
        if match is not None:
            name = _base(match.group("name"))
            policies.setdefault(name, []).append(match.group("body"))
        for body in _dollar_bodies(text):
            _collect(
                split_statements(body),
                created,
                enabled,
                forced,
                policies,
                depth + 1,
            )


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


def _dollar_bodies(statement: str) -> list[str]:
    """Return the contents of the dollar-quoted bodies inside a statement.

    Both spellings of a dollar quote are read: ``$$ body $$`` (no tag) and
    ``$tag$ body $tag$``. A back-reference to a group that did not take part
    in the match never succeeds, so the untagged spelling cannot be read with
    a back-reference - and the untagged spelling is the one the product
    repositories use for their ``DO`` blocks. The closing tag is compared with
    the opening one, so a body whose closing tag differs is not read.
    """
    bodies: list[str] = []
    for match in DOLLAR_BODY_RE.finditer(statement):
        if (match.group("tag") or "") != (match.group("ctag") or ""):
            continue
        bodies.append(match.group("body"))
    return bodies


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
