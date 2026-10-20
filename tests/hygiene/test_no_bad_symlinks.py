"""Invariant: no tracked symlink with an absolute target, a self-loop, a
target outside the checkout or a dangling target (SKL-W0-01, TASK-0006).

A symlink in version control pins the machine of whoever created it. An
absolute target escapes the checkout, a self-loop can never be resolved and a
dangling target breaks every clone that does not have the same layout as the
author. A relative target that leaves the checkout is the same escape as an
absolute one, only less visible. None of the four may be tracked.

Every test is proven twice: against the real repository the invariant must
hold, and against a deliberately broken fixture it must be reported.
"""
from __future__ import annotations

from pathlib import Path

from hygiene.repo_guard import REPO_ROOT, FixtureFile, make_repo, symlink_violations


def test_no_tracked_symlink_is_absolute() -> None:
    """The real repository tracks no symlink with an absolute target."""
    absolute = [
        violation
        for violation in symlink_violations(REPO_ROOT)
        if "absolute" in violation
    ]
    assert absolute == [], f"absolute symlinks are tracked: {absolute}"


def test_no_tracked_symlink_is_a_self_loop() -> None:
    """The real repository tracks no symlink that points at itself."""
    loops = [
        violation
        for violation in symlink_violations(REPO_ROOT)
        if "itself" in violation
    ]
    assert loops == [], f"self-looping symlinks are tracked: {loops}"


def test_no_tracked_symlink_is_dangling() -> None:
    """The real repository tracks no symlink whose target does not exist."""
    dangling = [
        violation
        for violation in symlink_violations(REPO_ROOT)
        if "dangling" in violation
    ]
    assert dangling == [], f"dangling symlinks are tracked: {dangling}"


def test_no_tracked_symlink_leaves_the_repository() -> None:
    """The real repository tracks no symlink that points outside the checkout."""
    escaping = [
        violation
        for violation in symlink_violations(REPO_ROOT)
 if "leaves the repository" in violation
    ]
    assert escaping == [], f"symlinks leave the repository: {escaping}"


def test_detects_an_absolute_symlink_in_a_fixture(tmp_path: Path) -> None:
    """The checker reports a fixture that tracks an absolute symlink."""
    repo = make_repo(
        tmp_path,
        [
            FixtureFile(path="real.txt", content="ok"),
            FixtureFile(path="abs-link", link="/etc/hostname"),
        ],
    )
    violations = symlink_violations(repo)
    assert any("abs-link" in violation and "absolute" in violation for violation in violations), (
        f"the absolute symlink was not reported: {violations}"
    )


def test_detects_a_self_loop_in_a_fixture(tmp_path: Path) -> None:
    """The checker reports a fixture that tracks a self-looping symlink."""
    repo = make_repo(
        tmp_path,
        [FixtureFile(path="loop-link", link="loop-link")],
    )
    violations = symlink_violations(repo)
    assert any("loop-link" in violation and "itself" in violation for violation in violations), (
        f"the self-loop was not reported: {violations}"
    )


def test_detects_a_dangling_symlink_in_a_fixture(tmp_path: Path) -> None:
    """The checker reports a fixture that tracks a dangling symlink."""
    repo = make_repo(
        tmp_path,
        [FixtureFile(path="dead-link", link="does-not-exist")],
    )
    violations = symlink_violations(repo)
    assert any("dead-link" in violation and "dangling" in violation for violation in violations), (
        f"the dangling symlink was not reported: {violations}"
    )


def test_detects_a_symlink_that_leaves_the_repository_in_a_fixture(tmp_path: Path) -> None:
    """A relative symlink that points outside the checkout is reported."""
    repo = make_repo(
        tmp_path,
 [FixtureFile(path="escape-link", link="../../outside/target.txt")],
    )
    violations = symlink_violations(repo)
    assert any("escape-link" in violation and "leaves" in violation for violation in violations), (
        f"the escaping symlink was not reported: {violations}"
    )


def test_accepts_a_relative_symlink_with_an_existing_target(tmp_path: Path) -> None:
    """A relative symlink that resolves inside the repository is accepted."""
    repo = make_repo(
        tmp_path,
        [
            FixtureFile(path="real.txt", content="ok"),
            FixtureFile(path="good-link", link="real.txt"),
        ],
    )
    assert symlink_violations(repo) == []
