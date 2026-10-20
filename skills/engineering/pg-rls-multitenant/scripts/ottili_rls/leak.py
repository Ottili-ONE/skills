"""Judging the output of an RLS leak probe.

The probe runs as the application role and prints one measurement per line:

    a_sees_own<TAB>1
    a_sees_b<TAB>0
    unset_sees_rows<TAB>0
    write_leaks<TAB>0

``a_sees_own`` is the number of rows tenant A may see (it seeded exactly
one), ``a_sees_b`` is the number of rows of tenant B that tenant A may see
and ``unset_sees_rows`` is the number of rows that anybody may see while the
session carries no tenant at all. A leak test passes when the three numbers
are 1, 0 and 0: the tenant sees its own row, sees no row of another tenant
and sees nothing at all when no tenant is set.

``write_leaks`` is the number of rows the session of the second tenant wrote
while claiming the first tenant. It is 0 when the write was refused and 1
when the database accepted it. The read path and the write path are guarded
by two different clauses of a policy, so the probe measures both: a policy
whose USING clause is correct and whose WITH CHECK clause is wide open hides
every foreign row and still accepts a foreign row.

A measurement that is missing is a failure, not a zero: the probe did not run,
and a probe that did not run proves nothing.
"""
from __future__ import annotations

import re

from .models import LeakVerdict, Measurement

MEASUREMENT_RE = re.compile(r"^(?P<name>[a-z_]+)\t(?P<value>\d+)\s*$")
ERROR_RE = re.compile(r"^\s*(?:psql:.*)?\s*ERROR:", re.IGNORECASE)

# The measurement every leak probe has to report, and the value it has to
# have. The order is the order of the report.
EXPECTED_MEASUREMENTS: tuple[tuple[str, int], ...] = (
    ("a_sees_own", 1),
    ("a_sees_b", 0),
    ("unset_sees_rows", 0),
    ("write_leaks", 0),
)


def parse_measurements(text: str) -> tuple[dict[str, int], list[str]]:
    """Return the measurements of a probe output and the error lines it holds."""
    measurements: dict[str, int] = {}
    errors: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if ERROR_RE.match(line):
            errors.append(line)
            continue
        match = MEASUREMENT_RE.match(line)
        if match:
            measurements[match.group("name")] = int(match.group("value"))
    return measurements, errors


def judge_probe_output(text: str) -> LeakVerdict:
    """Return the verdict of a probe output."""
    measurements, errors = parse_measurements(text)
    findings: list[str] = []
    for error in errors:
        findings.append(f"probe error: {error}")
    for name, expected in EXPECTED_MEASUREMENTS:
        value = measurements.get(name)
        if value is None:
            findings.append(f"probe did not report {name} (the probe did not run)")
        elif value != expected:
            findings.append(_wrong_measurement(name, expected, value))
    return LeakVerdict(
        passed=not findings,
        findings=tuple(findings),
        measurements=tuple(
            Measurement(name=name, value=value)
            for name, value in sorted(measurements.items())
        ),
    )


def _wrong_measurement(name: str, expected: int, value: int) -> str:
    """Return the finding for one measurement that has the wrong value."""
    if name == "a_sees_own":
        return f"same-tenant read wrong (expected {expected}, got {value})"
    if name == "a_sees_b":
        return f"cross-tenant leak (expected {expected}, got {value})"
    if name == "write_leaks":
        return f"write leak (expected {expected}, got {value})"
    return f"rows visible without a tenant (expected {expected}, got {value})"
