"""The typed core of the Ottili tenant-isolation checker.

The package holds everything that is pure: the data model, the reader of the
tenant convention, the SQL scanner and the rules. The I/O lives in the
adapters next to it (``check_rls_migration.py``, ``check_leak_probe.py``,
``pg-rls-leak-test.sh``). A rule never reads a file, never prints and never
decides on its own what to do with a finding.
"""
from __future__ import annotations

from .convention import ConventionError, classify_guc, load_convention
from .leak import judge_probe_output, parse_measurements
from .logging import configure_logging, log_event, new_run_id
from .models import (
    Finding,
    FindingCode,
    GucName,
    GucStatus,
    LeakVerdict,
    Measurement,
    MigrationFacts,
    PolicyCommand,
    PolicyFacts,
    TableFacts,
    TenantConvention,
)
from .rules import canonical_gucs_used, evaluate_migration
from .scanner import (
    collect_facts,
    read_policy,
    split_column_definitions,
    split_statements,
)

__all__ = [
    "ConventionError",
    "Finding",
    "FindingCode",
    "GucName",
    "GucStatus",
    "LeakVerdict",
    "Measurement",
    "MigrationFacts",
    "PolicyCommand",
    "PolicyFacts",
    "TableFacts",
    "TenantConvention",
    "canonical_gucs_used",
    "classify_guc",
    "collect_facts",
    "configure_logging",
    "evaluate_migration",
    "judge_probe_output",
    "load_convention",
    "log_event",
    "new_run_id",
    "parse_measurements",
    "read_policy",
    "split_column_definitions",
    "split_statements",
]
