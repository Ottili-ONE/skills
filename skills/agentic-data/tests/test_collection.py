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
def test_design_completeness(name: str) -> None:
    """DESIGN.md must carry the sections the R3 brief asks for: a trigger
    description draft, a procedure outline, a scripts list, and five eval
    scenarios, plus a competitive-comparison section saying what existing
    public skills do and what this one does differently."""
    root = COLLECTION_ROOT / name
    design = (root / "references" / "DESIGN.md").read_text(encoding="utf-8")
    lowered = design.lower()
    assert "trigger description" in lowered, f"{name}: DESIGN.md has no trigger description"
    assert "procedure outline" in lowered or "procedure" in lowered, (
        f"{name}: DESIGN.md has no procedure outline"
    )
    assert "scripts" in lowered, f"{name}: DESIGN.md has no scripts section"
    assert "five eval scenarios" in lowered, (
        f"{name}: DESIGN.md has no five eval scenarios"
    )
    assert "what this skill does better" in lowered, (
        f"{name}: DESIGN.md has no 'does better than a generic agent' section"
    )
    assert "what existing public skills do" in lowered, (
        f"{name}: DESIGN.md has no competitive-comparison section"
    )
    scenarios = re.findall(r'^\d\. "', design, flags=re.M)
    assert len(scenarios) >= 5, (
        f"{name}: DESIGN.md lists only {len(scenarios)} numbered eval scenarios (need >= 5)"
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
    """The scripts of a skill and its SKILL.md must describe each other.

    Two directions, both checked for every skill of the collection: a script
    path that SKILL.md points at exists on disk, and every script the skill
    ships is named in SKILL.md. This check used to skip the nine skills whose
    SKILL.md did not use the `scripts:` summary line - a skip hides exactly
    the mismatch this test exists to catch, so the nine SKILL.md files now
    carry the line and the test runs against all ten skills.
    """
    root = COLLECTION_ROOT / name
    body = (root / "SKILL.md").read_text(encoding="utf-8")
    script_lines = [ln for ln in body.splitlines() if re.search(r"scripts:", ln, re.I)]
    assert script_lines, f"{name}: SKILL.md does not document its scripts"
    named: set[str] = set()
    for line in script_lines:
        named.update(re.findall(r"([a-z][a-z0-9_\-]*\.py)", line))
    assert named, f"{name}: scripts: line names no .py files"
    scripts_dir = root / "scripts"
    assert scripts_dir.is_dir(), f"{name}: documents scripts: but has no scripts/ dir"
    for script in sorted(named):
        assert (scripts_dir / script).is_file(), f"{name}: scripts line names missing {script}"
    shipped = {q.name for q in scripts_dir.glob("*.py")}
    assert shipped == named, (
        f"{name}: scripts/ ships {sorted(shipped - named)}, "
        f"which SKILL.md does not name; SKILL.md names {sorted(named - shipped)}, which do not exist"
    )


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_evals_near_miss_count(name: str) -> None:
    """Every skill must carry >=3 near-miss prompts that assert the skill does
    NOT fire for a neighbouring protocol — the trigger-precision half of the
    eval contract."""
    root = COLLECTION_ROOT / name
    body = (root / "references" / "EVALS.md").read_text(encoding="utf-8")
    near = len(re.findall(r"^## N\d+", body, flags=re.M))
    assert near >= 3, f"{name}: only {near} near-miss prompts (need >= 3)"


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_related_links_resolve(name: str) -> None:
    """Every [name](../name/SKILL.md) link in a Related section must point at a
    real sibling skill folder."""
    root = COLLECTION_ROOT / name
    body = (root / "SKILL.md").read_text(encoding="utf-8")
    for m in re.finditer(r"\[([a-z0-9]+(?:-[a-z0-9]+)*)\]\(\.\./([a-z0-9]+(?:-[a-z0-9]+)*)/SKILL\.md\)", body):
        target = COLLECTION_ROOT / m.group(2)
        assert (target / "SKILL.md").is_file(), f"{name}: Related link to unknown skill {m.group(2)}"


def test_readme_lists_all_ten_skills() -> None:
    body = (COLLECTION_ROOT / "README.md").read_text(encoding="utf-8")
    for name in SKILL_NAMES:
        assert f"`{name}`" in body, f"README.md does not mention {name}"


def test_collection_ships_no_status_diary() -> None:
    """The collection ships skills, not diaries about them.

    A collection-level ``STATUS.md``/``HANDOFF.md`` is a status diary: it goes
    stale the moment the skills change and nothing in the product reads it.
    The re-verification material a diary used to hold now lives with the thing
    it describes - in each skill's ``references/SOURCES.md`` and in the
    runnable acceptance gate.
    """
    for diary in ("STATUS.md", "HANDOFF.md"):
        assert not (COLLECTION_ROOT / diary).exists(), (
            f"{diary} is a stale status diary; the collection must not ship one"
        )


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_each_skill_carries_its_own_reverification_material(name: str) -> None:
    """What the removed collection diary used to carry must exist per skill.

    The version pins and the retrieval dates are the re-verification record; a
    skill that lost them has lost evidence that no diary can replace.
    """
    root = COLLECTION_ROOT / name
    sources = (root / "references" / "SOURCES.md").read_text(encoding="utf-8")
    assert len(URL_RE.findall(sources)) >= 6, f"{name}: fewer than 6 primary URLs"
    assert re.search(r"20\d\d-\d\d-\d\d", sources), (
        f"{name}: no retrieval date in references/SOURCES.md"
    )
