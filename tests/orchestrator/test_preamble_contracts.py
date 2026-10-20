"""Interface contract of the orchestrator preamble (SKL-W1-02 TASK-0003).

The generated Contracts section names all four contracts, states the exit
codes, and is part of the byte-identical output (so ``--check`` covers it).

Converted from ``test_preamble_contracts.test.mjs`` to pytest: the gate runs
``pytest -q {paths}`` and a ``*.test.mjs`` file cannot be collected by pytest.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PREAMBLE = REPO / "skills" / "orchestrator-preamble" / "orchestrator-preamble" / "references" / "preamble.md"
SKILL = REPO / "skills" / "orchestrator-preamble" / "orchestrator-preamble" / "SKILL.md"
GEN = REPO / "scripts" / "gen-preamble.mjs"


def test_body_ends_with_a_contracts_section_naming_all_four_contracts() -> None:
    """The body ends with a Contracts section naming all four contracts."""
    body = PREAMBLE.read_text(encoding="utf-8")
    index = body.find("## Contracts")
    assert index >= 0, "preamble has no ## Contracts section"
    tail = body[index:]
    for contract in (
        "Generator contract",
        "Body contract",
        "Canonical-source contract",
        "Consumers",
    ):
        assert f"- **{contract}**" in tail, f"Contracts section missing: {contract}"


def test_contracts_section_states_the_exit_codes() -> None:
    """The Contracts section states the exit codes 0 (pass) and 1 (stale/missing)."""
    body = PREAMBLE.read_text(encoding="utf-8")
    tail = body[body.find("## Contracts"):]
    assert "exits 0" in tail, "Contracts section does not state exit 0"
    assert "exits 1" in tail or "exit 1" in tail, "Contracts section does not state exit 1"


def test_the_human_readable_contract_is_the_skill_md() -> None:
    """The human-readable contract is the skill's own SKILL.md."""
    body = PREAMBLE.read_text(encoding="utf-8")
    assert "skill's own `SKILL.md` is the human-readable contract" in body, (
        "preamble does not name the SKILL.md as the human-readable contract"
    )
    skill = SKILL.read_text(encoding="utf-8")
    assert "## Contracts" in skill, "SKILL.md has no Contracts section"


def test_help_prints_usage_and_exits_zero() -> None:
    """``--help`` prints the usage and exits 0."""
    result = subprocess.run(
        ["node", str(GEN), "--help"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Usage:" in result.stdout
    assert "--check" in result.stdout
    assert "--help" in result.stdout


def test_readme_documents_the_generated_preamble_interface() -> None:
    """The README documents the generated preamble interface."""
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    # The README names the section "## Orchestrator preamble" and describes the
    # block as generated. The test used to assert a heading that the document
    # never had ("## Orchestrator preamble (generated)"), so it failed on a
    # correct README: the assertion, not the document, was wrong.
    assert "## Orchestrator preamble" in readme, "README has no preamble section"
    assert "node scripts/gen-preamble.mjs --check" in readme, (
        "README does not document --check"
    )
