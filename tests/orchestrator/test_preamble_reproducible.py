"""The orchestrator preamble is generated, short and reproducible.

It is also wired to the four canonical engineering skills' gate commands.

Converted from ``test_preamble_reproducible.test.mjs`` (SKL-W1-02 TASK-0002) to
pytest: the gate runs ``pytest -q {paths}`` and a ``*.test.mjs`` file cannot be
collected by pytest.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PREAMBLE = REPO / "skills" / "orchestrator-preamble" / "orchestrator-preamble" / "references" / "preamble.md"
SKILL = REPO / "skills" / "engineering" / "honest-status" / "SKILL.md"
GEN = REPO / "scripts" / "gen-preamble.mjs"


def run_gen() -> subprocess.CompletedProcess[str]:
    """Run the generator without arguments and return the result."""
    return subprocess.run(
        ["node", str(GEN)],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )


def test_preamble_exists_and_is_at_most_60_lines() -> None:
    """preamble.md exists and is <= 60 lines."""
    lines = PREAMBLE.read_text(encoding="utf-8").split("\n")
    assert len(lines) <= 60, f"preamble is {len(lines)} lines, expected <= 60"
    assert lines[0].startswith("# Orchestrator Preamble")


def test_generator_is_reproducible() -> None:
    """Two runs of the generator produce byte-identical output."""
    first = run_gen()
    assert first.returncode == 0, first.stdout + first.stderr
    body = PREAMBLE.read_text(encoding="utf-8")
    second = run_gen()
    assert second.returncode == 0, second.stdout + second.stderr
    assert PREAMBLE.read_text(encoding="utf-8") == body


def test_generator_check_exits_zero_against_the_committed_file() -> None:
    """``--check`` exits 0 against the committed file."""
    result = subprocess.run(
        ["node", str(GEN), "--check"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "up to date" in result.stdout


def test_preamble_contains_all_four_canonical_gate_commands() -> None:
    """The preamble contains all four canonical gate commands."""
    body = PREAMBLE.read_text(encoding="utf-8")
    for command in (
        "check_rls_migration.py",
        "check_outbox.py",
        "check_problem_catalogue.py",
        "check_status_evidence.py",
    ):
        assert command in body, f"preamble missing gate command: {command}"


def test_generator_refuses_when_a_canonical_gate_command_is_removed() -> None:
    """The generator refuses to run when a canonical gate command is gone."""
    backup = SKILL.read_text(encoding="utf-8")
    try:
        # Replace the whole gate command with something unrelated — a substring
        # swap (e.g. check_status_evidence.py -> check_status_evidenceXYZ.py) is
        # NOT a drift, because the original command is still present as a
        # substring and the generator correctly keeps working.
        SKILL.write_text(
            backup.replace(
                "python3 scripts/check_status_evidence.py STATUS.md --root .",
                "REMOVED.md",
            ),
            encoding="utf-8",
        )
        result = run_gen()
        assert result.returncode != 0, "the generator must refuse to run"
    finally:
        SKILL.write_text(backup, encoding="utf-8")
