"""Shared helpers and checkers for the SKL-W0-01 repository invariants.

The invariants of this module are the executable form of the hygiene decisions
of job SKL-W0-01. They are written against a *repository* (a directory with a
``.git``), never against a hard-coded list, so the very same checker runs
against the real checkout and against a deliberately broken fixture.

Only the Python standard library and ``git`` are used: the test suite of this
repository must run without a third-party dependency.

The single source of truth for the allow-lists is ``scripts/truth/config.json``
(``rootAllowlist`` and ``largeFileAllowlist``); a fixture repository that wants
to be judged by these rules has to carry its own copy of that file.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_REL = "scripts/truth/config.json"

#: A tracked file above this size must be allow-listed with a reason.
MAX_LARGE_FILE_BYTES = 5 * 1024 * 1024

#: Runtime state of a local database. It must never be committed.
DB_FILE_RE = re.compile(r"(\.db(-wal|-shm)?|\.sqlite.*|\.journal(-wal|-shm)?)$")

#: Hosts that serve the public npm registry. The @ottili scope must never
#: resolve to one of them.
PUBLIC_NPM_HOSTS = ("registry.npmjs.org", "registry.npmjs.com", "npmjs.com")

#: The scope of this repository. A dependency on it is internal by definition.
INTERNAL_SCOPE = "@ottili/"


@dataclass(frozen=True)
class TrackedFile:
    """A file as the git index knows it."""

    path: str
    mode: str

    @property
    def is_symlink(self) -> bool:
        """True when the index records the path as a symbolic link."""
        return self.mode == "120000"


@dataclass(frozen=True)
class FixtureFile:
    """One file of a fixture repository.

    ``link`` creates a symbolic link with that target, ``size`` creates a
    zero-filled file of that many bytes, ``content`` writes text.
    """

    path: str
    content: str | None = None
    link: str | None = None
    size: int | None = None


def git(repo: Path, *args: str) -> tuple[int, str]:
    """Run ``git`` inside ``repo`` and return ``(returncode, stdout)``."""
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout


def tracked_files(repo: Path) -> list[TrackedFile]:
    """Every file the git index of ``repo`` tracks, with its file mode."""
    code, out = git(repo, "ls-files", "-s", "-z")
    if code != 0:
        raise AssertionError(f"git ls-files failed in {repo}")
    files: list[TrackedFile] = []
    for entry in out.split("\0"):
        if not entry:
            continue
        meta, _, path = entry.partition("\t")
        files.append(TrackedFile(path=path, mode=meta.split(" ", 1)[0]))
    return files


def read_config(repo: Path) -> dict[str, Any]:
    """Read ``scripts/truth/config.json`` of ``repo``."""
    config_path = repo / CONFIG_REL
    if not config_path.is_file():
        raise AssertionError(f"{CONFIG_REL} is missing in {repo}")
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], raw)


def root_allowlist(repo: Path) -> list[str]:
    """The allow-list of repository-root entries, read from the config."""
    config = read_config(repo)
    entries = cast(list[str], config.get("rootAllowlist", []))
    return entries


def large_file_allowlist(repo: Path) -> list[dict[str, str]]:
    """The allow-list of large tracked files, read from the config."""
    config = read_config(repo)
    entries = cast(list[dict[str, str]], config.get("largeFileAllowlist", []))
    return entries


# -- symlinks ----------------------------------------------------------------


def symlink_target(repo: Path, path: str) -> str | None:
    """The target text of a tracked symlink, read from the git object store."""
    code, out = git(repo, "cat-file", "blob", f":{path}")
    if code != 0:
        return None
    return out


def symlink_violations(repo: Path) -> list[str]:
    """Tracked symlinks that are absolute, a self-loop, escaping or dangling."""
    violations: list[str] = []
    for entry in tracked_files(repo):
        if not entry.is_symlink:
            continue
        target = symlink_target(repo, entry.path)
        if target is None:
            violations.append(f"{entry.path}: symlink target is unreadable")
            continue
        if os.path.isabs(target):
            violations.append(f"{entry.path}: absolute symlink target {target!r}")
            continue
        resolved = os.path.normpath(os.path.join(os.path.dirname(entry.path), target))
        if resolved == entry.path:
            violations.append(f"{entry.path}: symlink points at itself ({target!r})")
            continue
        if resolved == ".." or resolved.startswith(f"..{os.sep}"):
            violations.append(f"{entry.path}: symlink leaves the repository ({target!r})")
            continue
        if not os.path.exists(repo / resolved):
            violations.append(f"{entry.path}: dangling symlink target {target!r}")
    return violations


# -- database and journal files ----------------------------------------------


def database_violations(repo: Path) -> list[str]:
    """Tracked database or journal files."""
    return [
        entry.path
        for entry in tracked_files(repo)
        if DB_FILE_RE.search(entry.path)
    ]


# -- repository root ----------------------------------------------------------


def root_violations(repo: Path) -> list[str]:
    """Tracked root entries that the root allow-list does not cover."""
    allowed = set(root_allowlist(repo))
    seen = {entry.path.split("/", 1)[0] for entry in tracked_files(repo)}
    return sorted(seen - allowed)


def stale_allowlist_entries(repo: Path) -> list[str]:
    """Allow-list entries that no tracked root entry matches any more."""
    present = {entry.path.split("/", 1)[0] for entry in tracked_files(repo)}
    return sorted(set(root_allowlist(repo)) - present)


# -- large files --------------------------------------------------------------


def large_file_violations(repo: Path) -> list[str]:
    """Tracked files above 5 MiB that are not allow-listed with a reason."""
    allowed = {entry.get("path", "") for entry in large_file_allowlist(repo)}
    violations: list[str] = []
    for entry in tracked_files(repo):
        path = repo / entry.path
        if not path.is_file() or path.is_symlink():
            continue
        size = path.stat().st_size
        if size > MAX_LARGE_FILE_BYTES and entry.path not in allowed:
            violations.append(f"{entry.path}: {size} bytes")
    return violations


def allowlist_without_reason(repo: Path) -> list[str]:
    """Large-file allow-list entries that carry no reason."""
    return [
        entry.get("path", "<unnamed>")
        for entry in large_file_allowlist(repo)
        if not str(entry.get("reason", "")).strip()
    ]


# -- npm workspaces -----------------------------------------------------------


def workspace_projects(repo: Path) -> dict[str, list[str]] | None:
    """The workspace projects of ``repo`` as ``{name: [paths]}``.

    ``None`` means: the repository has no ``package.json`` with workspaces, so
    the workspace invariants do not apply to it.
    """
    package_json = repo / "package.json"
    if not package_json.is_file():
        return None
    data = cast(dict[str, Any], json.loads(package_json.read_text(encoding="utf-8")))
    workspaces = data.get("workspaces")
    if not workspaces:
        return None
    if isinstance(workspaces, dict):
        patterns = cast(list[str], workspaces.get("packages", []))
    else:
        patterns = cast(list[str], workspaces)
    projects: dict[str, list[str]] = {}
    for pattern in patterns:
        for package_json_path in sorted(repo.glob(f"{pattern}/package.json")):
            project = cast(
                dict[str, Any],
                json.loads(package_json_path.read_text(encoding="utf-8")),
            )
            name = str(project.get("name", ""))
            if not name:
                continue
            projects.setdefault(name, []).append(
                str(package_json_path.parent.relative_to(repo))
            )
    return projects


def duplicate_project_names(repo: Path) -> list[str]:
    """Workspace project names that are used more than once."""
    projects = workspace_projects(repo)
    if projects is None:
        return []
    return sorted(name for name, paths in projects.items() if len(paths) > 1)


def dependency_violations(repo: Path) -> list[str]:
    """Internal dependencies that do not use the ``workspace:`` protocol."""
    projects = workspace_projects(repo)
    if projects is None:
        return []
    violations: list[str] = []
    for pattern in _workspace_patterns(repo):
        for package_json_path in sorted(repo.glob(f"{pattern}/package.json")):
            project = cast(
                dict[str, Any],
                json.loads(package_json_path.read_text(encoding="utf-8")),
            )
            for section in ("dependencies", "devDependencies", "peerDependencies"):
                dependencies = cast(dict[str, str], project.get(section, {}))
                for name, raw_range in dependencies.items():
                    if not _is_internal(name, projects):
                        continue
                    if not str(raw_range).startswith("workspace:"):
                        violations.append(
                            f"{package_json_path.relative_to(repo)}: {name} -> {raw_range}"
                        )
    return violations


def _workspace_patterns(repo: Path) -> list[str]:
    package_json = repo / "package.json"
    data = cast(dict[str, Any], json.loads(package_json.read_text(encoding="utf-8")))
    workspaces = data.get("workspaces")
    if not workspaces:
        return []
    if isinstance(workspaces, dict):
        return cast(list[str], workspaces.get("packages", []))
    return cast(list[str], workspaces)


def _is_internal(name: str, projects: dict[str, list[str]]) -> bool:
    """True when ``name`` belongs to this repository (a workspace or the scope)."""
    return name in projects or name.startswith(INTERNAL_SCOPE)


# -- npm registry configuration ----------------------------------------------


def npmrc_violations(repo: Path) -> list[str]:
    """Violations of the npm registry configuration of ``repo``."""
    npmrc = repo / ".npmrc"
    if not npmrc.is_file():
        return ["no .npmrc in the repository"]
    violations: list[str] = []
    scope_lines = [
        line.strip()
        for line in npmrc.read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("@ottili:registry=")
    ]
    if not scope_lines:
        violations.append("no @ottili:registry mapping")
        return violations
    if len(scope_lines) > 1:
        violations.append(f"{len(scope_lines)} @ottili:registry mappings")
    value = scope_lines[0].split("=", 1)[1].strip()
    if not value:
        violations.append("@ottili:registry is empty: the scope would fall back")
    for host in PUBLIC_NPM_HOSTS:
        if host in value:
            violations.append(f"@ottili scope points at the public registry ({value})")
    return violations


# -- fixture repositories -----------------------------------------------------


def make_repo(root: Path, files: list[FixtureFile], config: dict[str, Any] | None = None) -> Path:
    """Create a throwaway git repository and return its path.

    ``root`` is a directory that the caller owns (pytest's ``tmp_path``); the
    repository is created in ``root/repo`` so that the caller can delete the
    whole tree afterwards.
    """
    repo = root / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "hygiene@example.com")
    git(repo, "config", "user.name", "Hygiene Fixture")
    git(repo, "config", "commit.gpgsign", "false")
    for entry in files:
        target = repo / entry.path
        target.parent.mkdir(parents=True, exist_ok=True)
        if entry.link is not None:
            os.symlink(entry.link, target)
        elif entry.size is not None:
            target.write_bytes(b"\0" * entry.size)
        else:
            target.write_text(entry.content or "", encoding="utf-8")
    if config is not None:
        config_path = repo / CONFIG_REL
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    git(repo, "add", "-A")
    code, _ = git(repo, "commit", "-q", "-m", "fixture")
    if code != 0:
        raise AssertionError(f"fixture commit failed in {repo}")
    return repo
