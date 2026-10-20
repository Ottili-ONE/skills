"""The kit's own dependencies must not be visible to the gate (SKL-W1-01).

The truth kit asks a pass to run ``npm install --prefix scripts/truth`` — its
``db.mjs`` needs the ``pg`` package. That install creates
``scripts/truth/node_modules/`` and ``scripts/truth/package-lock.json``.

Neither file may ever be committed (the kit owns them, and its own integrity
manifest skips both), but the gate's **ownership** step counts every
UNTRACKED file: ``scripts/truth/gate.mjs`` builds its changed set from
``git ls-files --others --exclude-standard``. So an installed kit made the
gate fail with "changed file(s) outside the owned paths" for files that no
job is allowed to commit, and the ``--exclude`` list did not help — it only
removes paths from the OWNED set, and these paths were never in it.

``.gitignore`` is the root cause and the root fix: the kit itself treats
these paths as artefacts it does not own (``scripts/truth/manifest.mjs``
skips them, ``scripts/truth/lib/common.mjs`` lists them in
``generatedGlobs``). These tests hold that they stay invisible to git.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GITIGNORE = ROOT / ".gitignore"

#: The artefacts ``npm install --prefix scripts/truth`` creates.
KIT_ARTEFACTS = (
    "scripts/truth/node_modules/pg/index.js",
    "scripts/truth/package-lock.json",
)


def git(*args: str) -> subprocess.CompletedProcess[str]:
    """Run one git command in the repository.

    Inputs:
        args: the arguments of the git command.
    Outputs:
        the completed process. The exit code is the answer of git.
    Failure modes:
        none. A non-zero exit code of git is checked by the caller.
    """
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    )


def test_the_kit_artefacts_are_git_ignored() -> None:
    """Git must not offer the kit's dependencies as files of the repository."""
    for artefact in KIT_ARTEFACTS:
        result = git("check-ignore", "-q", artefact)
        assert result.returncode == 0, (
            f"{artefact} is not ignored by .gitignore: the gate's ownership step "
            "counts every untracked file, so an installed kit would fail the gate"
        )


def test_no_tracked_file_is_shadowed_by_the_new_ignore_rules() -> None:
    """The ignore rules must not hide a file that the repository tracks."""
    tracked = git("ls-files", "-z").stdout.split("\0")
    tracked = [path for path in tracked if path]
    assert tracked, "the repository tracks no file at all"
    for path in tracked:
        result = git("check-ignore", "-q", path)
        assert result.returncode != 0, (
            f"{path} is tracked but also ignored: it would vanish from the checkout"
        )


def test_the_kit_integrity_check_still_passes() -> None:
    """Ignoring the kit's dependencies must not break the kit's own manifest."""
    manifest = ROOT / "scripts" / "truth" / "manifest.mjs"
    if not manifest.is_file():
        return
    result = subprocess.run(
        ["node", str(manifest), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
