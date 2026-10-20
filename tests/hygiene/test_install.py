"""Installer contract tests (SKL-W0-01, TASK-0002).

``scripts/install.sh`` is the only way skills reach an agent. Two things have to
hold:

* the source resolution finds every skill folder (the historic defect: the path
  was built from a catalogue lookup that returned an empty string, so every
  skill failed with "source skill directory missing"), and
* the package list is DERIVED from the ``skills/`` folders, so a package that
  exists on disk can always be installed and a package that does not exist is
  refused with a readable message.

``--check`` verifies all of that without writing anything.
"""
from __future__ import annotations

import subprocess
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INSTALL = ROOT / "scripts" / "install.sh"
SKILLS_DIR = ROOT / "skills"


def run_install(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(INSTALL), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def skill_folders() -> dict[str, list[str]]:
    """Map package name -> skill names for every skills/<package>/<skill>/ folder."""
    packages: dict[str, list[str]] = {}
    for skill_md in sorted(SKILLS_DIR.glob("*/*/SKILL.md")):
        rel = skill_md.parent.relative_to(ROOT)
        packages.setdefault(rel.parts[1], []).append(rel.parts[2])
    return packages


def test_every_skill_folder_resolves(tmp_path: Path) -> None:
    """Every skill folder in the tree is installable by name."""
    for package, skills in skill_folders().items():
        for skill in skills:
            result = run_install("--check", "--target", str(tmp_path / "t"), skill)
            assert result.returncode == 0, (
                f"{package}/{skill} does not resolve: {result.stdout}{result.stderr}"
            )


def test_check_mode_writes_nothing(tmp_path: Path) -> None:
    """--check verifies without creating the target directory."""
    target = tmp_path / "not-created"
    result = run_install("--check", "--target", str(target), "--package", "generic")
    assert result.returncode == 0, result.stdout + result.stderr
    assert not target.exists(), "--check must not write anything"
    assert "nothing written" in result.stdout


def test_check_mode_fails_on_an_unknown_skill(tmp_path: Path) -> None:
    """--check reports a skill that does not exist instead of pretending success."""
    result = run_install("--check", "--target", str(tmp_path / "t"), "no-such-skill-xyz")
    assert result.returncode == 1
    assert "source skill directory missing" in result.stderr


def test_every_package_installs_all_of_its_skills(tmp_path: Path) -> None:
    """Each real package installs every skill it contains, each with a SKILL.md."""
    for package, skills in skill_folders().items():
        target = tmp_path / package
        result = run_install("--target", str(target), "--package", package)
        assert result.returncode == 0, f"{package}: {result.stdout}{result.stderr}"
        for skill in skills:
            assert (target / skill / "SKILL.md").is_file(), (
                f"{package}: {skill} was not installed with its SKILL.md"
            )
        installed = {p.name for p in target.iterdir() if p.is_dir()}
        assert installed == set(skills), (
            f"{package}: installed {sorted(installed)}, expected {sorted(skills)}"
        )


def test_generic_package_installs_every_skill(tmp_path: Path) -> None:
    """'generic' installs every skill of every package."""
    target = tmp_path / "generic"
    result = run_install("--target", str(target), "--package", "generic")
    assert result.returncode == 0, result.stdout + result.stderr
    every = {skill for skills in skill_folders().values() for skill in skills}
    installed = {p.name for p in target.iterdir() if p.is_dir()}
    assert installed == every
    for skill in every:
        assert (target / skill / "SKILL.md").is_file()


def test_on_demand_reference_packages_install_their_skill(tmp_path: Path) -> None:
    """The on-demand ref-* packages are real packages and install their skill."""
    refs = {p: s for p, s in skill_folders().items() if p.startswith("ref-")}
    assert refs, "the tree has no on-demand ref-* packages any more"
    for package, skills in refs.items():
        target = tmp_path / package
        result = run_install("--target", str(target), "--package", package)
        assert result.returncode == 0, f"{package}: {result.stdout}{result.stderr}"
        for skill in skills:
            assert (target / skill / "SKILL.md").is_file()


def test_meta_package_is_accepted(tmp_path: Path) -> None:
    """'meta' is a reserved virtual package: accepted, ships nothing."""
    result = run_install("--target", str(tmp_path / "meta"), "--package", "meta")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "meta" in result.stdout


def test_unknown_package_is_rejected(tmp_path: Path) -> None:
    """A package that does not exist is refused and the known ones are listed."""
    result = run_install("--target", str(tmp_path / "t"), "--package", "no-such-package")
    assert result.returncode == 1
    assert "unknown package" in result.stderr
    assert "engineering" in result.stderr


def test_package_names_are_matched_literally(tmp_path: Path) -> None:
    """A package name is matched literally, not as a regular expression.

    The package lookup used ``grep -qx``, so a name that happens to be a valid
    regex matched a package that does not exist: ``--package engineering+``
    installed the engineering skills. The lookup now uses ``grep -qxF``.
    """
    packages = list(skill_folders())
    assert packages, "the tree has no packages"
    for name in ("engineering+", ".*", "engineering?", "engineering.*"):
        result = run_install("--target", str(tmp_path / "t"), "--package", name)
        assert result.returncode == 1, (
            f"--package {name!r} must be refused as unknown, it matched a real package: "
            f"{result.stdout}{result.stderr}"
        )
        assert "unknown package" in result.stderr


def test_every_derived_package_is_accepted_by_name(tmp_path: Path) -> None:
    """Every package folder on disk is accepted by its exact name."""
    for package in skill_folders():
        result = run_install("--check", "--target", str(tmp_path / "t"), "--package", package)
        assert result.returncode == 0, f"{package}: {result.stdout}{result.stderr}"


def test_existing_destination_is_not_overwritten_without_force(tmp_path: Path) -> None:
    """Safety: an existing skill folder is never replaced silently."""
    target = tmp_path / "t"
    target.mkdir()
    (target / "honest-status").mkdir()
    (target / "honest-status" / "MARKER").write_text("keep me", encoding="utf-8")
    result = run_install("--target", str(target), "honest-status")
    assert result.returncode == 0
    assert "skip" in result.stdout
    assert (target / "honest-status" / "MARKER").is_file()


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    """--dry-run prints the planned actions and creates nothing."""
    target = tmp_path / "dry"
    result = run_install("--dry-run", "--target", str(target), "--package", "engineering")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "dry-run: copy" in result.stdout
    assert not target.exists(), "--dry-run must not write anything"


def test_link_mode_creates_a_symlink(tmp_path: Path) -> None:
    """--link points the destination at the source folder instead of copying it."""
    target = tmp_path / "linked"
    result = run_install("--link", "--target", str(target), "honest-status")
    assert result.returncode == 0, result.stdout + result.stderr
    dest = target / "honest-status"
    assert dest.is_symlink(), f"{dest} is not a symlink"
    assert dest.resolve() == (ROOT / "skills" / "engineering" / "honest-status").resolve()


def test_missing_target_argument_is_refused(tmp_path: Path) -> None:
    """Without --target the installer refuses to run instead of guessing."""
    result = run_install("honest-status")
    assert result.returncode == 2
    assert "--target is required" in result.stderr


def test_check_without_a_target_verifies_the_whole_repository() -> None:
    """``install.sh --check`` alone verifies every skill of the repository."""
    result = run_install("--check")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "nothing written" in result.stdout
    for package, skills in skill_folders().items():
        for skill in skills:
            assert f"ok: {skill} ->" in result.stdout, f"{package}/{skill} was not verified"


def test_check_without_a_target_writes_nothing(tmp_path: Path) -> None:
    """The scratch directory of the default check stays empty."""
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    result = subprocess.run(
        ["bash", str(INSTALL), "--check"],
        cwd=ROOT,
        env=dict(os.environ, TMPDIR=str(scratch)),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert list(scratch.iterdir()) == [], "--check must not create the scratch target"


def test_check_fails_on_a_skill_folder_without_a_skill_md(tmp_path: Path) -> None:
    """A broken fixture: a skill folder without SKILL.md is reported.

    The fixture is a throwaway repository with its own copy of the installer,
    so the check is proven to fail without depending on the real tree.
    """
    fixture = tmp_path / "fixture"
    (fixture / "scripts").mkdir(parents=True)
    shutil.copy(INSTALL, fixture / "scripts" / "install.sh")
    skill = fixture / "skills" / "pkg" / "broken"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: broken\n---\n", encoding="utf-8")

    healthy = subprocess.run(
        ["bash", str(fixture / "scripts" / "install.sh"), "--check"],
        cwd=fixture,
        capture_output=True,
        text=True,
        check=False,
    )
    assert healthy.returncode == 0, healthy.stdout + healthy.stderr
    assert "ok: broken ->" in healthy.stdout

    (skill / "SKILL.md").unlink()
    broken = subprocess.run(
        ["bash", str(fixture / "scripts" / "install.sh"), "--check"],
        cwd=fixture,
        capture_output=True,
        text=True,
        check=False,
    )
    assert broken.returncode == 1, broken.stdout + broken.stderr
    assert "has no SKILL.md" in broken.stderr


def test_a_skill_name_that_escapes_the_target_is_refused(tmp_path: Path) -> None:
    """A skill name is a path component of the destination: it must not escape.

    The destination is ``$TARGET/$name``. A name like ``../pkg/good`` therefore
    points OUTSIDE the target directory, and with ``--force`` the installer
    deleted that directory (``rm -rf "$dest"``) before it wrote the skill
    there. The installer refused every such name instead, and it refuses it
    before it writes anything.
    """
    fixture = tmp_path / "fixture"
    (fixture / "scripts").mkdir(parents=True)
    shutil.copy(INSTALL, fixture / "scripts" / "install.sh")
    skill = fixture / "skills" / "pkg" / "good"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: good\n---\n", encoding="utf-8")
    target = fixture / "target"
    target.mkdir()
    # A directory OUTSIDE the target that must survive the attempt.
    outside = fixture / "pkg" / "good"
    outside.mkdir(parents=True)
    (outside / "MARKER").write_text("keep me", encoding="utf-8")

    for extra in ([], ["--force"]):
        result = subprocess.run(
            ["bash", str(fixture / "scripts" / "install.sh"), *extra,
             "--target", str(target), "../pkg/good"],
            cwd=fixture,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 2, (
            f"a traversing skill name must be refused (rc={result.returncode})\n"
            f"{result.stdout}{result.stderr}"
        )
        assert "invalid skill name" in result.stderr
        assert (outside / "MARKER").is_file(), "the installer touched a directory outside the target"


def test_a_skill_name_with_a_path_separator_is_refused(tmp_path: Path) -> None:
    """``skills/pkg/good`` is not a skill name; only plain folder names are."""
    result = run_install("--check", "--target", str(tmp_path / "t"), "engineering/honest-status")
    assert result.returncode == 2, result.stdout + result.stderr
    assert "invalid skill name" in result.stderr


def test_check_accepts_a_target_whose_parent_does_not_exist(tmp_path: Path) -> None:
    """The check mirrors the install: ``mkdir -p`` creates the target tree.

    The check used to refuse a target whose parent directory was missing,
    although the install creates that tree with ``mkdir -p``. A check that is
    stricter than the install reports a false failure.
    """
    target = tmp_path / "does" / "not" / "exist" / "yet"
    checked = run_install("--check", "--target", str(target), "--package", "engineering")
    assert checked.returncode == 0, checked.stdout + checked.stderr
    assert not target.exists(), "--check must not create the target"

    installed = run_install("--target", str(target), "--package", "engineering")
    assert installed.returncode == 0, installed.stdout + installed.stderr
    assert (target / "honest-status" / "SKILL.md").is_file()


def test_check_refuses_a_target_that_cannot_be_created(tmp_path: Path) -> None:
    """A target below a FILE cannot be created: the check has to say so."""
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")
    result = run_install("--check", "--target", str(blocker / "skills"), "--package", "engineering")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "cannot be created" in result.stderr
