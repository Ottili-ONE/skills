"""Guard: the tenant skill teaches the tenant convention of the platform (SKL-W1-01).

A skill that documents a different tenant name than the checker enforces is
worse than a skill that documents nothing: the reader trusts the prose. These
tests hold the documentation of ``pg-rls-multitenant`` to the convention that
``guc-names.json`` holds.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "engineering" / "pg-rls-multitenant"
CONVENTION_FILE = SKILL / "guc-names.json"
SKILL_MD = SKILL / "SKILL.md"
PROCEDURE = SKILL / "references" / "pg-rls-procedure.md"
DESIGN = SKILL / "references" / "DESIGN.md"
EVALS = SKILL / "references" / "EVALS.md"
SOURCES = SKILL / "references" / "SOURCES.md"


def convention() -> dict[str, object]:
    """Return the tenant convention of the skill."""
    return json.loads(CONVENTION_FILE.read_text(encoding="utf-8"))


def test_the_convention_names_one_tenant_guc_and_one_column() -> None:
    """``app.company_id`` and ``company_id``, and nothing else."""
    config = convention()
    accepted = [entry["name"] for entry in config["accepted_names"]]
    assert accepted == ["app.company_id"], accepted
    assert config["canonical_name"] == "app.company_id", config["canonical_name"]
    assert config["canonical_column"] == "company_id", config["canonical_column"]


def test_the_skill_md_teaches_the_canonical_name() -> None:
    """The quick reference names the one tenant GUC and the one column."""
    text = SKILL_MD.read_text(encoding="utf-8")
    assert "app.company_id" in text, "the skill must name the tenant GUC"
    assert "company_id" in text, "the skill must name the tenant column"


def test_the_skill_does_not_hedge_about_the_tenant_name() -> None:
    """A decision that was taken is written as a decision, not as a question."""
    for path in (SKILL_MD, PROCEDURE, DESIGN, EVALS, SOURCES):
        text = path.read_text(encoding="utf-8")
        assert "open decision" not in text, f"{path.name} still hedges the tenant name"
        assert "open owner decision" not in text, f"{path.name} still hedges the tenant name"


def test_the_legacy_names_are_only_mentioned_as_findings() -> None:
    """A legacy name may appear in the skill only as a name that is rejected."""
    config = convention()
    legacy = [entry["name"] for entry in config["rejected_names"]]
    assert legacy, "the convention must record the legacy names it rejects"
    text = SKILL_MD.read_text(encoding="utf-8")
    for name in legacy:
        if name == "app.current_tenant":
            continue
        assert name in text, f"{name} must be named as a rejected spelling"


def test_the_procedure_documents_the_three_measurements() -> None:
    """The leak probe decides on three measurements; the procedure says so."""
    text = PROCEDURE.read_text(encoding="utf-8")
    for name in ("a_sees_own", "a_sees_b", "unset_sees_rows"):
        assert name in text, f"{name} must be documented in the procedure"


def test_the_procedure_documents_the_real_server_mode() -> None:
    """The leak probe runs against a real PostgreSQL, not only against Docker."""
    text = PROCEDURE.read_text(encoding="utf-8")
    assert "--server" in text, "the procedure must document the server mode"
    assert "check_leak_probe.py" in text, "the procedure must name the judge"


def test_the_sources_record_the_census_and_the_real_database() -> None:
    """The evidence behind the decision and the probe is recorded with its date."""
    text = SOURCES.read_text(encoding="utf-8")
    assert "2026-10-20" in text, "the census must carry its date"
    assert "app.company_id" in text, "the census must name the canonical GUC"
    assert "unset_sees_rows" in text, "the real-database proof must be recorded"
