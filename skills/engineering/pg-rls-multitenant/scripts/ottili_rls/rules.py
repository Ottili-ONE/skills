"""The rules of the Ottili tenant convention.

The rules take what a migration says (the facts) and what the platform agrees
on (the convention) and return findings. They are pure and deterministic: the
same facts and the same convention always produce the same findings in the
same order.
"""
from __future__ import annotations

import re

from .convention import classify_guc
from .models import (
    Finding,
    FindingCode,
    GucStatus,
    MigrationFacts,
    TableFacts,
    TenantConvention,
)
from .scanner import guc_names_in, split_column_definitions, split_statements

GRANT_ALL_RE = re.compile(r"\bGRANT\s+ALL\b", re.IGNORECASE)
NOT_NULL_RE = re.compile(r"\bNOT\s+NULL\b", re.IGNORECASE)


def evaluate_migration(sql: str, convention: TenantConvention) -> list[Finding]:
    """Return the findings of one migration.

    A tenant table must carry the tenant column, must switch row level
    security on and must force it, and must be guarded by a policy that reads
    the canonical tenant GUC. The order of the findings is stable: tables in
    alphabetical order, the rules of a table in a fixed order, the file-wide
    rule last.
    """
    statements = split_statements(sql)
    facts = collect_facts_from(statements)
    findings: list[Finding] = []
    for table in facts.tables:
        findings.extend(_table_findings(table, convention))
    if GRANT_ALL_RE.search(" ".join(statements)):
        findings.append(
            Finding(
                code=FindingCode.GRANT_ALL,
                message="GRANT ALL on a protected table overrides the policy grant",
            )
        )
    return findings


def canonical_gucs_used(
    facts: MigrationFacts, convention: TenantConvention
) -> set[str]:
    """Return the canonical tenant GUCs a migration actually reads."""
    canonical = convention.canonical_name.strip().lower()
    used: set[str] = set()
    for table in facts.tables:
        for policy in table.policies:
            for name in guc_names_in(policy):
                if name == canonical:
                    used.add(name)
    return used


def collect_facts_from(statements: list[str]) -> MigrationFacts:
    """Return the facts of a list of statements."""
    from .scanner import collect_facts

    return collect_facts(statements)


def _table_findings(
    table: TableFacts, convention: TenantConvention
) -> list[Finding]:
    """Return the findings of one table."""
    findings: list[Finding] = []
    column = convention.canonical_column
    # The tenant column. A table this file creates must carry it; a table that
    # already exists is held to what this file touches.
    if table.created_here:
        definition = _column_definition(table.column_list, column)
        if definition is None:
            findings.append(
                Finding(
                    code=FindingCode.MISSING_COMPANY_ID,
                    message=f"no {column} tenant discriminator column",
                    table=table.name,
                )
            )
        elif not NOT_NULL_RE.search(definition):
            findings.append(
                Finding(
                    code=FindingCode.NULLABLE_COMPANY_ID,
                    message=f"{column} tenant discriminator column is nullable",
                    table=table.name,
                )
            )
    elif table.policies and not any(
        re.search(rf"\b{re.escape(column)}\b", policy, re.IGNORECASE)
        for policy in table.policies
    ):
        findings.append(
            Finding(
                code=FindingCode.MISSING_COMPANY_ID,
                message=f"no {column} tenant discriminator column",
                table=table.name,
            )
        )
    # RLS. The file that creates a tenant table is the file that has to switch
    # RLS on; an existing table keeps the state of its own migration, so this
    # file is not held to it.
    if table.created_here:
        if not table.enabled_rls:
            findings.append(
                Finding(
                    code=FindingCode.MISSING_ENABLE_RLS,
                    message="missing ENABLE ROW LEVEL SECURITY",
                    table=table.name,
                )
            )
        if not table.forced_rls:
            findings.append(
                Finding(
                    code=FindingCode.MISSING_FORCE_RLS,
                    message=(
                        "missing FORCE ROW LEVEL SECURITY (owner would bypass RLS)"
                    ),
                    table=table.name,
                )
            )
    # The policy. It has to read the canonical tenant GUC: a policy keyed on
    # another name isolates nobody, because nothing sets that name.
    if table.created_here or table.policies:
        if not table.policies:
            findings.append(
                Finding(
                    code=FindingCode.MISSING_TENANT_POLICY,
                    message="no CREATE POLICY for tenant isolation",
                    table=table.name,
                )
            )
        else:
            findings.extend(_policy_findings(table, convention))
    return findings


def _policy_findings(
    table: TableFacts, convention: TenantConvention
) -> list[Finding]:
    """Return the findings of the policies of one table."""
    findings: list[Finding] = []
    used: set[str] = set()
    for policy in table.policies:
        used |= guc_names_in(policy)
    canonical = convention.canonical_name
    for name in sorted(used):
        status = classify_guc(name, convention)
        if status is GucStatus.CANONICAL:
            continue
        if status is GucStatus.REJECTED:
            findings.append(
                Finding(
                    code=FindingCode.NON_CANONICAL_GUC,
                    message=(
                        "tenant policy is not keyed on an accepted tenant GUC "
                        f"({canonical}): it uses the non-canonical tenant GUC "
                        f"'{name}'"
                    ),
                    table=table.name,
                )
            )
        elif status is GucStatus.NON_TENANT:
            findings.append(
                Finding(
                    code=FindingCode.NON_CANONICAL_GUC,
                    message=(
                        "tenant policy is not keyed on an accepted tenant GUC "
                        f"({canonical}): it uses '{name}', which carries "
                        "something other than the tenant"
                    ),
                    table=table.name,
                )
            )
        else:
            findings.append(
                Finding(
                    code=FindingCode.UNKNOWN_GUC,
                    message=(
                        "tenant policy is not keyed on an accepted tenant GUC "
                        f"({canonical}): it uses the unknown setting '{name}'"
                    ),
                    table=table.name,
                )
            )
    if not findings:
        # A policy that reads no setting at all isolates nobody.
        for policy in table.policies:
            if not guc_names_in(policy):
                findings.append(
                    Finding(
                        code=FindingCode.UNKNOWN_GUC,
                        message=(
                            "tenant policy is not keyed on an accepted tenant GUC "
                            f"({canonical}): it reads no tenant setting at all"
                        ),
                        table=table.name,
                    )
                )
                break
    return findings


def _column_definition(column_list: str, name: str) -> str | None:
    """Return the definition of one column, or None when the table lacks it."""
    pattern = re.compile(rf"^{re.escape(name)}\b(.*)$", re.IGNORECASE | re.DOTALL)
    for part in split_column_definitions(column_list):
        match = pattern.match(part.strip())
        if match is not None:
            return match.group(1)
    return None
