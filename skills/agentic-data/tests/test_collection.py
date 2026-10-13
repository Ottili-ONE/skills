"""Collection-level acceptance tests for skills-agentic-data-r3.

These are the checks the R3 brief calls "validate by hand against the standard
rules" — name == folder, description <= 1024 chars, SKILL.md body <= 500 lines,
every `references/` link resolves one level deep, no escapes, EVALS >= 5 prompts,
SOURCES >= 6 primary URLs with a retrieval date, and DESIGN.md present.

They are deliberately offline and deterministic: no network, no subprocess
other than the per-skill validators that already ship with each skill.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

COLLECTION_ROOT = Path(__file__).resolve().parent.parent
SKILL_NAMES = [
    "mcp-2026-07-28",
    "skill-authoring-evals",
    "computer-use-drivers",
    "browser-agent-playwright",
    "polite-crawling-warc",
    "dedup-decontam",
    "verifiable-environments",
    "llm-judge-calibration",
    "trajectory-ledger",
    "deep-research-method",
]

URL_RE = re.compile(r"https?://[^\s)\]\|\"'<>]+")
REF_LINK_RE = re.compile(r"`(references/[^`]+)`")


def _front_matter(body: str) -> tuple[str, str, str]:
    """Return (name, description, rest) parsed from a SKILL.md front matter block."""
    assert body.startswith("---\n"), "SKILL.md must start with a YAML front matter block"
    end = body.find("\n---\n", 4)
    assert end != -1, "SKILL.md front matter is not closed"
    fm = body[4:end]
    name = ""
    desc = ""
    for line in fm.splitlines():
        if line.startswith("name:"):
            name = line.split(":", 1)[1].strip().strip('"').strip("'")
        elif line.startswith("description:"):
            desc = line.split(":", 1)[1].strip().strip('"').strip("'")
    return name, desc, body[end + 5:]


def _body_lines(body: str) -> int:
    return len([ln for ln in body.splitlines() if ln.strip()])


def _eval_count(body: str) -> int:
    return len(re.findall(r"^## E\d+", body, flags=re.M))


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_skill_structure(name: str) -> None:
    root = COLLECTION_ROOT / name
    assert root.is_dir(), f"missing skill dir: {root}"
    skill_md = root / "SKILL.md"
    assert skill_md.is_file(), f"missing SKILL.md in {name}"
    body = skill_md.read_text(encoding="utf-8")
    fname, desc, rest = _front_matter(body)
    assert fname == name, f"name {fname!r} != folder {name!r}"
    assert len(desc) <= 1024, f"{name}: description {len(desc)} chars > 1024"
    assert _body_lines(rest) <= 500, f"{name}: body {_body_lines(rest)} lines > 500"
    # every references/ link resolves one level deep, no escapes
    for link in REF_LINK_RE.findall(rest):
        assert not link.startswith("/"), f"{name}: absolute references link {link!r}"
        assert ".." not in link.split("/"), f"{name}: escaping references link {link!r}"
        target = root / link
        assert target.is_file(), f"{name}: references link {link!r} does not resolve"
        assert target.parent == root / "references", f"{name}: {link!r} is not one level deep"


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_design_and_sources(name: str) -> None:
    root = COLLECTION_ROOT / name
    design = root / "references" / "DESIGN.md"
    assert design.is_file(), f"{name}: missing references/DESIGN.md"
    sources = root / "references" / "SOURCES.md"
    assert sources.is_file(), f"{name}: missing references/SOURCES.md"
    text = sources.read_text(encoding="utf-8")
    urls = URL_RE.findall(text)
    assert len(urls) >= 6, f"{name}: only {len(urls)} source URLs (need >= 6)"
    assert "2026-10-12" in text or re.search(r"retrieval date", text, re.I), (
        f"{name}: SOURCES.md has no retrieval date"
    )


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_evals_present(name: str) -> None:
    root = COLLECTION_ROOT / name
    evals = root / "references" / "EVALS.md"
    assert evals.is_file(), f"{name}: missing references/EVALS.md"
    body = evals.read_text(encoding="utf-8")
    assert _eval_count(body) >= 5, f"{name}: only {_eval_count(body)} eval prompts (need >= 5)"


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_scripts_match_skill_md(name: str) -> None:
    """The scripts line in SKILL.md must name scripts that actually exist."""
    root = COLLECTION_ROOT / name
    body = (root / "SKILL.md").read_text(encoding="utf-8")
    scripts_line = next(
        (ln for ln in body.splitlines() if re.search(r"scripts:", ln.strip(), re.I)),
        "",
    )
    if not scripts_line:
        pytest.skip(f"{name}: no scripts: line")
    scripts_dir = root / "scripts"
    if not scripts_dir.is_dir():
        pytest.skip(f"{name}: no scripts/ dir")
    names = re.findall(r"([a-z][a-z0-9_\-]*\.py)", scripts_line)
    assert names, f"{name}: scripts: line names no .py files"
    for n in names:
        assert (scripts_dir / n).is_file(), f"{name}: scripts line names missing {n}"
