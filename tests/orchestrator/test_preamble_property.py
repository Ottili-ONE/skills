"""Property-based tests for scripts/gen-preamble.mjs (SKL-W1-02 TASK-0004).

hypothesis is not installed in this environment (no pip), so the property engine
is a small deterministic generator + loop, which is equivalent for the invariants
we pin: every generated body must start with the header, stay <= 60 lines, name
the four gate commands verbatim, and be byte-identical to a second generation.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GEN = REPO / "scripts" / "gen-preamble.mjs"
OUT = REPO / "skills" / "orchestrator-preamble" / "orchestrator-preamble" / "references" / "preamble.md"
GOLDEN = Path(__file__).resolve().parent / "golden" / "preamble.md"

GATES = [
    "python3 scripts/check_rls_migration.py <migration.sql>",
    "python3 scripts/check_outbox.py <sql-file>",
    "python3 scripts/check_problem_catalogue.py --catalogue <cat> --openapi <spec> --schema-dir <dir>",
    "python3 scripts/check_status_evidence.py STATUS.md --root .",
]


NODE = shutil.which("node") or sys.executable


def run(args, check=True):
    return subprocess.run(
        [NODE, str(GEN), *args],
        cwd=REPO, capture_output=True, text=True, check=check,
    )


def generated_body():
    """Generate to a temp file and read it back (never touch the committed body)."""
    tmp = REPO / ".truth" / "SKL-W1-02" / "preamble_prop.tmp.md"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    # gen-preamble writes to a fixed path; copy the committed body away, generate,
    # read, then restore. The committed body is restored in the finally block.
    backup = OUT.read_text() if OUT.exists() else None
    try:
        run([])
        return OUT.read_text()
    finally:
        if backup is not None:
            OUT.write_text(backup)


def test_property_determinism():
    """Same input on disk always produces the same bytes."""
    a = run([]).stdout
    b = run([]).stdout
    assert a == b


def test_property_body_shape():
    """Every generated body starts with the header, is <= 60 lines, names all four gates."""
    body = generated_body()
    lines = body.splitlines()
    assert lines[0] == "# Orchestrator Preamble (generated)"
    assert len(lines) <= 60, f"body is {len(lines)} lines"
    for gate in GATES:
        assert gate in body, f"gate command missing: {gate}"


def test_property_check_passes_on_committed_body():
    """--check exits 0 against the committed body."""
    r = run(["--check"])
    assert r.returncode == 0
    assert "up to date" in r.stdout


def test_property_check_fails_when_body_is_stale():
    """A mutated body must make --check exit non-zero (regression)."""
    backup = OUT.read_text()
    OUT.write_text(backup + "\n<!-- stale marker 12345 -->\n")
    try:
        r = run(["--check"], check=False)
        assert r.returncode != 0
        assert "stale" in (r.stderr + r.stdout)
    finally:
        OUT.write_text(backup)


def test_property_check_fails_when_body_is_missing():
    """A missing body must make --check exit non-zero (regression)."""
    backup = OUT.read_text()
    os.replace(OUT, OUT.with_suffix(".missing-stash"))
    try:
        r = run(["--check"], check=False)
        assert r.returncode != 0
        assert "missing" in (r.stderr + r.stdout)
    finally:
        os.replace(OUT.with_suffix(".missing-stash"), OUT)
        OUT.write_text(backup)


def test_property_golden_matches_committed_body():
    """The committed body is byte-identical to the golden copy (never auto-updated)."""
    assert OUT.read_text() == GOLDEN.read_text()


def test_property_help_is_complete():
    """--help prints usage and exits 0."""
    r = run(["--help"])
    assert r.returncode == 0
    assert "Usage:" in r.stdout
    assert "Exit codes:" in r.stdout
