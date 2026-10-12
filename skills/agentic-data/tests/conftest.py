"""Shared pytest fixtures for the skills-agentic-data collection.

Each skill ships its own tests, but until now there was no shared harness: every
suite re-implemented temp-dir and sample-input setup independently, and nothing
exercised the collection as a whole. This conftest provides:

  * ``agentic_data_root``  - absolute path to ``skills/agentic-data``
  * ``skill_dir``          - parametrised fixture yielding each of the ten skills
  * ``tmp_skill``          - copy a skill into a temp dir so tests can mutate it
  * ``write_file``         - helper to create nested files under a temp root

All fixtures are offline and deterministic: no network, no I/O beyond the local
filesystem, no random values (fixed seeds only where a script needs them).
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

# The collection root is two levels up from this file: .../agentic-data/tests
COLLECTION_ROOT = Path(__file__).resolve().parent.parent

# The ten skills, in RESEARCH.md dependency order. Kept here so the collection
# tests and the per-skill tests agree on what "the collection" means.
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


@pytest.fixture(scope="session")
def agentic_data_root() -> Path:
    """Absolute path to the collection root (skills/agentic-data)."""
    return COLLECTION_ROOT


def _skill_path(name: str) -> Path:
    return COLLECTION_ROOT / name


@pytest.fixture(params=SKILL_NAMES)
def skill_dir(request, agentic_data_root: Path) -> Path:
    """Parametrised fixture: yields each of the ten skill directories in turn."""
    path = agentic_data_root / request.param
    assert path.is_dir(), f"skill folder missing: {path}"
    assert (path / "SKILL.md").is_file(), f"SKILL.md missing in {path}"
    return path


@pytest.fixture()
def tmp_skill(tmp_path: Path, skill_dir: Path) -> Path:
    """Copy a whole skill into a temp dir so tests can mutate it freely."""
    dest = tmp_path / skill_dir.name
    shutil.copytree(skill_dir, dest)
    return dest


@pytest.fixture()
def write_file():
    """Return a helper that creates nested files under a root and returns the path."""
    def _write(root: Path, rel: str, content: str) -> Path:
        path = Path(root) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path
    return _write


@pytest.fixture()
def isolated_cwd(tmp_path: Path, monkeypatch):
    """Run a test with the CWD set to a temp dir (scripts must not touch the repo)."""
    monkeypatch.chdir(tmp_path)
    return tmp_path
