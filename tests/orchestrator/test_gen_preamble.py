"""Unit + property + golden-file tests for scripts/gen-preamble.mjs.

Converted from ``test_gen_preamble.test.mjs`` (SKL-W1-02 TASK-0004) to pytest:
the gate runs ``pytest -q {paths}`` and a ``*.test.mjs`` file cannot be
collected by pytest, so the assertions of that file would never run again.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GEN = REPO / "scripts" / "gen-preamble.mjs"
OUT = REPO / "skills" / "orchestrator-preamble" / "orchestrator-preamble" / "references" / "preamble.md"
GOLDEN = Path(__file__).resolve().parent / "golden" / "preamble.md"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the generator and return the result instead of raising on failure."""
    return subprocess.run(
        ["node", str(GEN), *args],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )


def test_help_prints_usage_and_exits_zero() -> None:
    """``--help`` prints the usage and exits 0."""
    result = run("--help")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Usage: node scripts/gen-preamble.mjs" in result.stdout
    assert "--check" in result.stdout
    assert "Exit codes:" in result.stdout


def test_check_passes_on_the_committed_body() -> None:
    """``--check`` passes on the committed body (exit 0)."""
    result = run("--check")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "preamble.md is up to date" in result.stdout


def test_golden_file_matches_the_committed_preamble_byte_for_byte() -> None:
    """The committed preamble.md matches tests/golden/preamble.md byte-for-byte."""
    committed = OUT.read_text(encoding="utf-8")
    golden = GOLDEN.read_text(encoding="utf-8")
    assert committed == golden, "committed preamble.md diverges from the golden copy"


def test_committed_preamble_is_at_most_60_lines() -> None:
    """The committed preamble.md is <= 60 lines."""
    lines = OUT.read_text(encoding="utf-8").split("\n")
    assert len(lines) <= 60, f"preamble.md is {len(lines)} lines (> 60)"


def test_preamble_lists_the_four_rules_with_their_check_commands() -> None:
    """The preamble lists the four rules with their exact check commands."""
    text = OUT.read_text(encoding="utf-8")
    assert "# Orchestrator Preamble (generated)" in text
    for gate in (
        "python3 scripts/check_rls_migration.py <migration.sql>",
        "python3 scripts/check_outbox.py <sql-file>",
        "python3 scripts/check_problem_catalogue.py --catalogue <cat> --openapi <spec> --schema-dir <dir>",
        "python3 scripts/check_status_evidence.py STATUS.md --root .",
    ):
        assert gate in text, f"gate command missing: {gate}"


def test_generator_is_deterministic() -> None:
    """The generator is deterministic (same input -> same bytes)."""
    first = run()
    second = run()
    assert first.returncode == 0, first.stdout + first.stderr
    assert first.stdout == second.stdout


def test_check_fails_when_the_body_is_stale() -> None:
    """``--check`` exits non-zero when the body is stale."""
    backup = OUT.read_text(encoding="utf-8")
    try:
        OUT.write_text(backup + "\n// stale marker\n", encoding="utf-8")
        result = run("--check")
        assert result.returncode != 0, "--check must exit non-zero on a stale body"
        assert "stale" in (result.stderr + result.stdout)
    finally:
        OUT.write_text(backup, encoding="utf-8")


def test_check_fails_when_the_body_is_missing() -> None:
    """``--check`` exits non-zero when the body is missing."""
    stash = OUT.with_name(OUT.name + ".missing-stash")
    backup = OUT.read_text(encoding="utf-8")
    try:
        OUT.rename(stash)
        result = run("--check")
        assert result.returncode != 0, "--check must exit non-zero on a missing body"
        assert "missing" in (result.stderr + result.stdout)
    finally:
        stash.rename(OUT)
        OUT.write_text(backup, encoding="utf-8")
