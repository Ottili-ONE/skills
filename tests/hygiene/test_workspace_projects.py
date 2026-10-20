"""Invariants of the npm workspaces (SKL-W0-01, TASK-0006).

Two rules apply to a repository with npm workspaces:

1. every workspace project name is unique;
2. every internal dependency uses the ``workspace:`` protocol.

The skills repository has **no** ``package.json`` and therefore no workspaces:
the two invariants do not apply to it. The tests say so instead of skipping
(the truth gate treats a skipped test as a failed test), and the checkers are
proven against fixtures that do have workspaces.
"""
from __future__ import annotations

import json
from pathlib import Path

from hygiene.repo_guard import (
    REPO_ROOT,
    FixtureFile,
    dependency_violations,
    duplicate_project_names,
    make_repo,
    workspace_projects,
)


def _package(name: str, dependencies: dict[str, str] | None = None) -> str:
    """The text of a package.json of a fixture project."""
    return json.dumps(
        {"name": name, "version": "1.0.0", "dependencies": dependencies or {}}
    )


def test_workspace_project_names_are_unique() -> None:
    """No workspace project name is used twice."""
    projects = workspace_projects(REPO_ROOT)
    if projects is None:
        assert not (REPO_ROOT / "package.json").exists(), (
            "the repository now has a package.json: the workspace invariants "
            "have to be enabled"
        )
        return
    duplicates = duplicate_project_names(REPO_ROOT)
    assert duplicates == [], f"workspace project names are used twice: {duplicates}"


def test_every_internal_dependency_uses_the_workspace_protocol() -> None:
    """Internal dependencies are resolved through the workspace protocol."""
    projects = workspace_projects(REPO_ROOT)
    if projects is None:
        assert not (REPO_ROOT / "package.json").exists(), (
            "the repository now has a package.json: the workspace invariants "
            "have to be enabled"
        )
        return
    violations = dependency_violations(REPO_ROOT)
    assert violations == [], f"internal dependencies without workspace protocol: {violations}"


def test_detects_a_duplicated_project_name_in_a_fixture(tmp_path: Path) -> None:
    """Two projects with the same name are reported."""
    repo = make_repo(
        tmp_path,
        [
            FixtureFile(path="package.json", content='{"workspaces": ["packages/*"]}'),
            FixtureFile(path="packages/one/package.json", content=_package("@acme/one")),
            FixtureFile(path="packages/two/package.json", content=_package("@acme/one")),
        ],
    )
    assert duplicate_project_names(repo) == ["@acme/one"]


def test_detects_an_internal_dependency_without_the_workspace_protocol(tmp_path: Path) -> None:
    """A registry-pinned internal dependency is reported."""
    repo = make_repo(
        tmp_path,
        [
            FixtureFile(path="package.json", content='{"workspaces": ["packages/*"]}'),
            FixtureFile(path="packages/one/package.json", content=_package("@acme/one")),
            FixtureFile(
                path="packages/two/package.json",
                content=_package("@acme/two", {"@acme/one": "^1.0.0"}),
            ),
        ],
    )
    violations = dependency_violations(repo)
    assert violations == ["packages/two/package.json: @acme/one -> ^1.0.0"]


def test_accepts_the_workspace_protocol_in_a_fixture(tmp_path: Path) -> None:
    """A dependency with the workspace protocol is accepted."""
    repo = make_repo(
        tmp_path,
        [
            FixtureFile(path="package.json", content='{"workspaces": ["packages/*"]}'),
            FixtureFile(path="packages/one/package.json", content=_package("@acme/one")),
            FixtureFile(
                path="packages/two/package.json",
                content=_package("@acme/two", {"@acme/one": "workspace:*"}),
            ),
        ],
    )
    assert dependency_violations(repo) == []


def test_accepts_a_third_party_dependency_in_a_fixture(tmp_path: Path) -> None:
    """A dependency outside the repository and outside its scope is accepted."""
    repo = make_repo(
        tmp_path,
        [
            FixtureFile(path="package.json", content='{"workspaces": ["packages/*"]}'),
            FixtureFile(path="packages/one/package.json", content=_package("@acme/one")),
            FixtureFile(
                path="packages/two/package.json",
                content=_package("@acme/two", {"@types/node": "^22.0.0"}),
            ),
        ],
    )
    assert dependency_violations(repo) == []
