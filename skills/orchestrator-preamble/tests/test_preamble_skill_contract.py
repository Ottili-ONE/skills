#!/usr/bin/env python3
"""The orchestrator preamble skill must not drift from the canonical skills.

The skill quotes the gate command of each canonical engineering skill, and the
generated body quotes the same commands. This suite fails when a canonical
command, the skill and the body drift apart, so the drift is caught by the
gate instead of by a reader who compares them by hand.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / "skills" / "orchestrator-preamble" / "orchestrator-preamble"
SKILL = PACKAGE / "SKILL.md"
BODY = PACKAGE / "references" / "preamble.md"
GENERATOR = ROOT / "scripts" / "gen-preamble.mjs"

RULES = (
    (
        "company_id / RLS",
        "skills/engineering/pg-rls-multitenant/SKILL.md",
        "python3 scripts/check_rls_migration.py <migration.sql>",
    ),
    (
        "outbox",
        "skills/engineering/outbox-idempotency/SKILL.md",
        "python3 scripts/check_outbox.py <sql-file>",
    ),
    (
        "problem+json",
        "skills/engineering/problem-json-contracts/SKILL.md",
        "python3 scripts/check_problem_catalogue.py --catalogue <cat> --openapi <spec> --schema-dir <dir>",
    ),
    (
        "honest status",
        "skills/engineering/honest-status/SKILL.md",
        "python3 scripts/check_status_evidence.py STATUS.md --root .",
    ),
)


def test_every_gate_command_is_verbatim_in_its_canonical_skill() -> None:
    """Each quoted gate command is the command the canonical skill states."""
    for rule, source, command in RULES:
        canonical = (ROOT / source).read_text(encoding="utf-8")
        assert command in canonical, f"{rule}: {command} does not appear in {source}"


def test_the_skill_quotes_every_rule_with_its_command_and_source() -> None:
    """The skill names every rule, its canonical source and its gate command."""
    skill = SKILL.read_text(encoding="utf-8")
    for rule, source, command in RULES:
        assert rule in skill, f"rule missing from the skill: {rule}"
        assert source in skill, f"canonical source missing from the skill: {source}"
        assert command in skill, f"gate command missing from the skill: {command}"


def test_the_generated_body_carries_the_same_commands_as_the_skill() -> None:
    """The generated body and the skill quote the same four gate commands."""
    body = BODY.read_text(encoding="utf-8")
    for rule, _source, command in RULES:
        assert command in body, f"gate command missing from the generated body: {rule}"


def test_the_committed_body_is_in_sync_with_the_generator() -> None:
    """The committed body is what the generator produces right now."""
    result = subprocess.run(
        ["node", str(GENERATOR), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "up to date" in result.stdout
