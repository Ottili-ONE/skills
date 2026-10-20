"""A skill's eval set is content, not a status diary.

The delete list of TASK-0004 names ``EVALS.md``. That name belongs to the
*pass-by-pass* eval diaries of the earlier waves, which are gone. The thirty
per-skill ``references/EVALS.md`` files are different: they hold the eval
prompts of one skill and are a required input of
``scripts/validate_skills.py`` — with ``references/EVALS.md`` moved aside,
that validator exits 1 with ``missing references/EVALS.md`` (repair log D-039).

These tests keep the three facts honest:

1. every engineering skill keeps the eval set the validator demands;
2. a skill that links an eval set has the file, and a skill that ships one has
   it in the generated catalogue — no dangling link, no invisible file;
3. the root-level eval diaries stay deleted.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINEERING = ROOT / "skills" / "engineering"


def catalogue_skills() -> list[dict]:
    """Every skill of the generated catalogue."""
    catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    return catalog["skills"]


def tracked_paths() -> list[str]:
    """Every tracked path in the repository."""
    out = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    )
    return [line for line in out.stdout.splitlines() if line]


def test_engineering_skills_keep_their_eval_set() -> None:
    """``scripts/validate_skills.py`` fails an engineering skill without one."""
    skills = sorted(p for p in ENGINEERING.iterdir() if (p / "SKILL.md").is_file())
    assert skills, "no engineering skills found"
    missing = [p.name for p in skills if not (p / "references" / "EVALS.md").is_file()]
    assert not missing, (
        "engineering skills without references/EVALS.md — scripts/validate_skills.py "
        f"would exit 1: {missing}"
    )


def test_every_link_to_an_eval_set_resolves() -> None:
    """A SKILL.md that points at an eval set must point at an existing file."""
    dangling = []
    for skill in catalogue_skills():
        folder = ROOT / skill["path"]
        body = (folder / "SKILL.md").read_text(encoding="utf-8")
        if "references/EVALS.md" in body and not (folder / "references" / "EVALS.md").is_file():
            dangling.append(skill["path"])
    assert not dangling, f"skills link an eval set that does not exist: {dangling}"


def test_every_shipped_eval_set_is_catalogued() -> None:
    """A skill that ships an eval set has it in the generated catalogue."""
    invisible = []
    for skill in catalogue_skills():
        folder = ROOT / skill["path"]
        evals = folder / "references" / "EVALS.md"
        if not evals.is_file():
            continue
        relative = str(evals.relative_to(ROOT))
        if relative not in skill.get("paths", []):
            invisible.append(relative)
    assert not invisible, f"eval sets missing from catalog.json: {invisible}"


def test_no_eval_diary_survives_outside_a_skill_folder() -> None:
    """The root-level ``EVALS.md`` diaries stay deleted."""
    diaries = sorted(
        path
        for path in tracked_paths()
        if Path(path).name == "EVALS.md" and not path.startswith("skills/")
    )
    assert not diaries, f"eval diaries are committed again: {diaries}"
