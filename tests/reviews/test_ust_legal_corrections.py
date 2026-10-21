"""Pins the two corrected legal rules (SKL-W1-02 TASK-0002).

The rules are pinned into the ref-ust-edge-cases wrapper and its sign-off
placeholder. These assertions fail against the uncorrected canonical skill text
(which says "services only" and "§4a UStG").

Converted from ``test_ust_legal_corrections.test.mjs`` to pytest: the gate runs
``pytest -q {paths}`` and a ``*.test.mjs`` file cannot be collected by pytest.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "skills" / "ref-ust-edge-cases" / "ref-ust-edge-cases" / "SKILL.md"
REVIEW = REPO / "docs" / "reviews" / "ref-ust-edge-cases.md"


def test_ref_ust_edge_cases_is_marked_reviewed_by_unverified() -> None:
    """ref-ust-edge-cases is marked reviewed_by: UNVERIFIED."""
    text = SKILL.read_text(encoding="utf-8")
    assert re.search(r"^reviewed_by: UNVERIFIED$", text, flags=re.MULTILINE)
    assert "Status: UNVERIFIED" in text


def test_13b_is_stated_as_the_full_goods_and_services_scope() -> None:
    """§13b is stated as the full goods+services scope, not "services only"."""
    text = SKILL.read_text(encoding="utf-8")
    # The phrase "services only" may only appear as the *quotation of the error*
    # being corrected (e.g. `reverse charge (§13b) applies to services only`),
    # never as a statement of the rule itself.
    error_quotations = re.findall(r"applies to services only", text)
    assert len(error_quotations) <= 1, (
        f'unexpected "services only" occurrences: {len(error_quotations)}'
    )
    assert "goods AND services" in text
    # The Abs. 1 list reference is split across two lines in the SKILL.md quote,
    # so match the pieces separately rather than one anchored regex.
    assert "§13b Abs. 1" in text
    assert "Nr. 1-11" in text
    assert "Werklieferungen" in text


def test_13b_is_not_narrowed_to_services() -> None:
    """§13b is NOT narrowed to services; goods may fall inside the list."""
    text = SKILL.read_text(encoding="utf-8")
    # Substring checks (the wrapper prose is multi-line, so anchored regexes
    # are brittle).
    assert "A goods supply" in text, "wrapper must discuss a goods supply"
    assert "may fall inside the §13b reverse-charge list" in text, (
        "wrapper must state goods may fall inside the §13b reverse-charge list"
    )
    assert 'is NOT "services only"' in text, (
        "wrapper must say the rule is NOT services only"
    )
    assert "the full §13b Abs. 1 list must be consulted per transaction" in text, (
        "wrapper must require consulting the full Abs. 1 list per transaction"
    )


def test_igl_is_cited_as_4_nr_1b_and_6a() -> None:
    """igL is cited as §4 Nr. 1b / §6a, never §4a."""
    text = SKILL.read_text(encoding="utf-8")
    assert "§4 Nr. 1b" in text
    assert "§6a" in text
    # The German phrase is the subject under test, not prose of this file.
    assert '§4a UStG is "Steuervergütung"' in text  # truth:allow-german
    assert not re.search(r"igL.*=.*§4a(?!.*Nr)", text), "igL must not be equated with §4a"


def test_the_review_placeholder_mirrors_both_corrections() -> None:
    """The review placeholder mirrors both corrections."""
    text = REVIEW.read_text(encoding="utf-8")
    assert '§13b reverse charge is NOT "services only"' in text
    assert "igL) is NOT §4a UStG" in text
    assert "§4 Nr. 1b" in text
    assert "§6a" in text
    assert "Reviewed by | **UNVERIFIED — pending signature**" in text
    assert "Date | **pending**" in text
