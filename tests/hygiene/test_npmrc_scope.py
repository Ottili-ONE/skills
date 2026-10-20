"""Invariant: ``.npmrc`` maps the ``@ottili`` scope to the private registry
(SKL-W0-01, TASK-0006).

The packages of the private registry arrive under the ``@ottili`` scope. The
scope must resolve to the private registry and must not fall back to the
public one: a missing or empty mapping would silently send internal packages
to the public registry, and a second mapping would silently redirect the
scope. A bare ``registry=`` line is the default for unscoped packages and is
therefore allowed.
"""
from __future__ import annotations

from pathlib import Path

from hygiene.repo_guard import REPO_ROOT, FixtureFile, make_repo, npmrc_violations


def test_the_ottili_scope_points_at_the_private_registry() -> None:
    """The real ``.npmrc`` maps the scope exactly once, away from npmjs.org."""
    violations = npmrc_violations(REPO_ROOT)
    assert violations == [], f"the npm registry configuration is wrong: {violations}"


def test_detects_a_public_registry_for_the_scope_in_a_fixture(tmp_path: Path) -> None:
    """A scope that points at the public registry is reported."""
    repo = make_repo(
        tmp_path,
        [
            FixtureFile(
                path=".npmrc",
                content="@ottili:registry=https://registry.npmjs.org/\n",
            )
        ],
    )
    violations = npmrc_violations(repo)
    assert any("public registry" in violation for violation in violations), (
        f"the public fallback was not reported: {violations}"
    )


def test_detects_a_missing_scope_mapping_in_a_fixture(tmp_path: Path) -> None:
    """A ``.npmrc`` without a scope mapping is reported."""
    repo = make_repo(
        tmp_path,
        [FixtureFile(path=".npmrc", content="registry=https://registry.npmjs.org/\n")],
    )
    violations = npmrc_violations(repo)
    assert violations == ["no @ottili:registry mapping"]


def test_detects_a_second_scope_mapping_in_a_fixture(tmp_path: Path) -> None:
    """Two mappings for the same scope are reported."""
    repo = make_repo(
        tmp_path,
        [
            FixtureFile(
                path=".npmrc",
                content=(
                    "@ottili:registry=http://127.0.0.1:18873\n"
                    "@ottili:registry=http://127.0.0.1:18874\n"
                ),
            )
        ],
    )
    violations = npmrc_violations(repo)
    assert any("mappings" in violation for violation in violations), (
        f"the second mapping was not reported: {violations}"
    )


def test_detects_an_empty_scope_mapping_in_a_fixture(tmp_path: Path) -> None:
    """An empty scope mapping is reported: it would fall back."""
    repo = make_repo(
        tmp_path,
        [FixtureFile(path=".npmrc", content="@ottili:registry=\n")],
    )
    violations = npmrc_violations(repo)
    assert any("fall back" in violation for violation in violations), (
        f"the empty mapping was not reported: {violations}"
    )


def test_accepts_a_private_scope_with_a_public_default_in_a_fixture(tmp_path: Path) -> None:
    """A public default registry for unscoped packages is allowed."""
    repo = make_repo(
        tmp_path,
        [
            FixtureFile(
                path=".npmrc",
                content=(
                    "@ottili:registry=http://127.0.0.1:18873\n"
                    "registry=https://registry.npmjs.org/\n"
                ),
            )
        ],
    )
    assert npmrc_violations(repo) == []
