"""The recipe for the next job must be executable, not only written down.

``docs/gaps/SKL-W0-01.md`` (G37) tells the job that comes after this one what a new
engineering skill has to ship, because the suite of the repository checks it. A
recipe that is written down but does not work is a claim, not a contract — and the
job that has to follow it is not allowed to change the validator.

This module therefore *executes* the recipe: it builds the skill the recipe
describes in a throwaway checkout, runs the repository validator over it and
asserts that the validator is satisfied. It then removes one part of the recipe
and asserts that the validator complains again, so the test cannot pass with a
validator that has stopped checking anything.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .worktree import temporary_worktree

DEMO = "w1-recipe-demo"

SKILL_MD = """---
name: w1-recipe-demo
description: Use when a job adds a skill to this repository and the skill has to pass the validator of the engineering package.
---

# w1-recipe-demo

The demo skill of the recipe.

- The eval set: [references/EVALS.md](references/EVALS.md)
- The sources: [references/SOURCES.md](references/SOURCES.md)
"""

EVALS_MD = """# Evals

1. prompt: "one" expect: "ok"
2. prompt: "two" expect: "ok"
3. prompt: "three" expect: "ok"
4. prompt: "four" expect: "ok"
5. prompt: "five" expect: "ok"
"""

SOURCES_MD = "# Sources\n\n- none\n"


def write_demo_skill(tree: Path) -> Path:
    """Write the skill of the recipe into a checkout."""
    folder = tree / "skills" / "engineering" / DEMO
    (folder / "references").mkdir(parents=True, exist_ok=True)
    (folder / "SKILL.md").write_text(SKILL_MD, encoding="utf-8")
    (folder / "references" / "EVALS.md").write_text(EVALS_MD, encoding="utf-8")
    (folder / "references" / "SOURCES.md").write_text(SOURCES_MD, encoding="utf-8")
    return folder


def run_validator(tree: Path) -> subprocess.CompletedProcess[str]:
    """Run the validator of the engineering package in a checkout."""
    return subprocess.run(
        ["python3", "scripts/validate_skills.py"],
        cwd=tree,
        capture_output=True,
        text=True,
        check=False,
    )


def test_the_skill_of_the_recipe_passes_the_validator() -> None:
    """The recipe of G37 produces a skill the validator accepts."""
    with temporary_worktree("HEAD") as tree:
        write_demo_skill(tree)
        result = run_validator(tree)
        assert result.returncode == 0, (
            "the skill of the recipe does not pass the validator:\n"
            f"{result.stdout}\n{result.stderr}"
        )


def test_the_validator_still_complains_when_the_recipe_is_broken() -> None:
    """The check of the recipe is real: a missing source file is reported."""
    with temporary_worktree("HEAD") as tree:
        folder = write_demo_skill(tree)
        (folder / "references" / "SOURCES.md").unlink()
        result = run_validator(tree)
        assert result.returncode == 1, (
            "the validator did not report the missing sources file:\n"
            f"{result.stdout}\n{result.stderr}"
        )
        assert "missing references/SOURCES.md" in result.stdout, result.stdout


def test_the_catalogue_of_the_recipe_contains_the_new_skill() -> None:
    """The recipe also regenerates the catalogue, and the skill is in it."""
    with temporary_worktree("HEAD") as tree:
        write_demo_skill(tree)
        result = subprocess.run(
            ["node", "scripts/gen-catalog.mjs"],
            cwd=tree,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
        catalog = json.loads((tree / "catalog.json").read_text(encoding="utf-8"))
        names = {entry["name"] for entry in catalog["skills"]}
        assert DEMO in names, f"the regenerated catalogue does not hold {DEMO}"
