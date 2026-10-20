"""Validator contract tests (SKL-W0-01, TASK-0002).

``scripts/validate.py`` is the aggregate validator of the repository. It has two
modes:

* the default mode validates the committed catalogue, entry by entry, against the
  skill folders it points at, and
* ``--everywhere`` additionally walks the WHOLE ``skills/`` tree and reports a
  skill folder that the catalogue does not know about (or a catalogue entry that
  has no folder on disk). That is the mode that proves "the catalogue lists every
  skill", because the catalogue alone can never prove its own completeness.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATE = ROOT / "scripts" / "validate.py"
SKILLS_DIR = ROOT / "skills"

SKILL_MD = """---
name: {name}
title: {name}
description: A demo skill used by the validator contract test.
version: 1.0.0
category: demo
license: MIT
author: test
---

# {name}

Body.
"""


def run_validator(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", "-I", str(script), *args],
        cwd=script.parents[1],
        capture_output=True,
        text=True,
        check=False,
    )


def skill_count_on_disk() -> int:
    return len(list(SKILLS_DIR.glob("*/*/SKILL.md")))


def test_validator_reports_every_skill() -> None:
    """The default mode validates the whole catalogue and reports the full count."""
    result = run_validator(VALIDATE)
    assert result.returncode == 0, result.stdout + result.stderr
    expected = skill_count_on_disk()
    assert f"ok: {expected} skills validated" in result.stdout, result.stdout


def test_everywhere_mode_is_green_on_the_real_tree() -> None:
    """--everywhere validates every skill folder of the repository."""
    result = run_validator(VALIDATE, "--everywhere")
    assert result.returncode == 0, result.stdout + result.stderr
    expected = skill_count_on_disk()
    assert f"ok: {expected} skills validated" in result.stdout, result.stdout


def test_everywhere_mode_detects_a_skill_missing_from_the_catalogue(tmp_path: Path) -> None:
    """A skill folder that the catalogue does not know is a validation error."""
    tree = tmp_path / "tree"
    (tree / "scripts").mkdir(parents=True)
    (tree / "skills" / "demo").mkdir(parents=True)

    (tree / "scripts" / "validate.py").write_text(
        VALIDATE.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (tree / "catalog.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "repository": "demo",
                "packages": {
                    "demo": {"label": "Demo", "description": "d", "path": "skills/demo"}
                },
                "skills": [
                    {
                        "id": "alpha",
                        "name": "alpha",
                        "title": "Alpha",
                        "package": "demo",
                        "path": "skills/demo/alpha",
                        "description": "d",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (tree / "skills" / "demo" / "alpha").mkdir()
    (tree / "skills" / "demo" / "alpha" / "SKILL.md").write_text(
        SKILL_MD.format(name="alpha"), encoding="utf-8"
    )
    # 'beta' exists on disk but not in the catalogue.
    (tree / "skills" / "demo" / "beta").mkdir()
    (tree / "skills" / "demo" / "beta" / "SKILL.md").write_text(
        SKILL_MD.format(name="beta"), encoding="utf-8"
    )

    catalogue_only = run_validator(tree / "scripts" / "validate.py")
    assert catalogue_only.returncode == 0, catalogue_only.stdout + catalogue_only.stderr

    everywhere = run_validator(tree / "scripts" / "validate.py", "--everywhere")
    assert everywhere.returncode == 1, everywhere.stdout + everywhere.stderr
    assert "beta" in everywhere.stderr and "missing from the catalog" in everywhere.stderr


def test_everywhere_mode_detects_a_catalogue_entry_without_a_folder(tmp_path: Path) -> None:
    """A catalogue entry that has no skill folder on disk is a validation error."""
    tree = tmp_path / "tree"
    (tree / "scripts").mkdir(parents=True)
    (tree / "skills" / "demo").mkdir(parents=True)

    (tree / "scripts" / "validate.py").write_text(
        VALIDATE.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (tree / "catalog.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "repository": "demo",
                "packages": {
                    "demo": {"label": "Demo", "description": "d", "path": "skills/demo"}
                },
                "skills": [
                    {
                        "id": "alpha",
                        "name": "alpha",
                        "title": "Alpha",
                        "package": "demo",
                        "path": "skills/demo/alpha",
                        "description": "d",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    # 'alpha' is in the catalogue but has no folder on disk.

    everywhere = run_validator(tree / "scripts" / "validate.py", "--everywhere")
    assert everywhere.returncode == 1, everywhere.stdout + everywhere.stderr
    assert "no SKILL.md on disk" in everywhere.stderr
