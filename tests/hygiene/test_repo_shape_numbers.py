"""``docs/truth/REPO_SHAPE.md`` must describe the tree that actually exists.

The repository shape is a *claim* about the tree. A claim that drifts is worse
than no claim, because the next job reads it and acts on it. This test therefore
executes the command that ``REPO_SHAPE.md`` itself prints next to every number
and asserts that the printed number is the number the document claims.

The test is deliberately generic: it parses the markdown tables, takes the
command cell verbatim and runs it. It does not know any particular metric, so a
new row added to the document is checked automatically, and a stale row fails.

Every row carries a **scope**, because the document holds two kinds of claims:

``live``
    An invariant of the tree. The command must print the claimed value in the
    checkout under test. These rows survive the next job: a job that adds a
    skill does not have to edit a document it does not own (D-066).

``snapshot@<commit>``
    The size of the tree at a named commit. The command is run in a checkout of
    that commit, so the row stays true for ever and can never block a job that
    legitimately grows the tree.
"""
from __future__ import annotations

import contextlib
import json
import re
import shutil
import subprocess
import tempfile
import warnings
from dataclasses import dataclass
from pathlib import Path

from .worktree import temporary_worktree

ROOT = Path(__file__).resolve().parents[2]
REPO_SHAPE = ROOT / "docs" / "truth" / "REPO_SHAPE.md"
TRUTH_CONFIG = ROOT / "scripts" / "truth" / "config.json"

#: Only read-only commands may be executed out of a markdown document.
ALLOWED_PREFIXES = ("git ls-files", "ls -d ", "python3 -c ", "find ")

#: The document must keep at least this many verifiable rows, otherwise a
#: truncated table would make this test pass without checking anything.
MIN_ROWS = 7

LIVE = "live"
SCOPE_RE = re.compile(r"^(live|snapshot@[0-9a-f]{7,40})$")


@dataclass(frozen=True)
class Row:
    """One verifiable claim of the shape document."""

    label: str
    value: str
    command: str
    scope: str

    @property
    def commit(self) -> str:
        """The commit a snapshot row is bound to (empty for a live row)."""
        return self.scope.split("@", 1)[1] if self.scope.startswith("snapshot@") else ""


def split_cells(row: str) -> list[str]:
    """Split a markdown table row into its cells.

    The outer pipes of the row are removed first, so a row yields exactly as
    many cells as it has columns. ``\\|`` is an escaped pipe and stays inside
    the cell; every other pipe ends a cell. A naive ``row.split("|")`` would cut
    the command cell of a row that contains a pipeline such as
    ``git ls-files | wc -l`` in two.
    """
    stripped = row.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    cells: list[str] = []
    buffer: list[str] = []
    index = 0
    while index < len(stripped):
        char = stripped[index]
        if char == "\\" and index + 1 < len(stripped) and stripped[index + 1] == "|":
            buffer.append("|")
            index += 2
            continue
        if char == "|":
            cells.append("".join(buffer))
            buffer = []
            index += 1
            continue
        buffer.append(char)
        index += 1
    cells.append("".join(buffer))
    return [cell.strip() for cell in cells]


def documented_rows(document: Path = REPO_SHAPE) -> list[Row]:
    """Every ``(label, value, command, scope)`` claim the document makes."""
    text = document.read_text(encoding="utf-8")
    rows: list[Row] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = split_cells(stripped)
        if len(cells) != 4:
            continue
        label, value, command, scope = cells
        if not value.isdigit():
            continue
        command = command.strip().strip("`").replace("\\|", "|")
        if not command:
            continue
        rows.append(Row(label, value, command, scope.strip().strip("`")))
    return rows


def run_command(command: str, cwd: Path) -> str:
    """Run a documented command and return its stdout."""
    assert command.startswith(ALLOWED_PREFIXES), f"undocumented command kind: {command!r}"
    completed = subprocess.run(
        command,
        cwd=cwd,
        shell=True,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def commit_is_available(commit: str) -> bool:
    """Whether the repository knows the commit."""
    completed = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode == 0


def repository_is_shallow() -> bool:
    """Whether the checkout was cloned without its history."""
    completed = subprocess.run(
        ["git", "rev-parse", "--is-shallow-repository"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout.strip() == "true"


@contextlib.contextmanager
def snapshot_checkouts(commits: list[str]):
    """Yield a checkout of every commit, created next to the repository."""
    if not commits:
        yield {}
        return
    holder = Path(tempfile.mkdtemp(prefix="repo-shape-"))
    created: list[Path] = []
    try:
        for commit in commits:
            target = holder / commit[:12]
            subprocess.run(
                ["git", "worktree", "add", "--detach", "--quiet", str(target), commit],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            created.append(target)
        yield {commit: target for commit, target in zip(commits, created)}
    finally:
        for target in created:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(target)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
        subprocess.run(
            ["git", "worktree", "prune"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        shutil.rmtree(holder, ignore_errors=True)


def check_rows(tree: Path, document: Path = REPO_SHAPE) -> tuple[list[str], list[str]]:
    """Check every row of the document against ``tree``.

    Returns the problems and the notes. A note is a row that could not be
    checked because the repository does not know its commit — only possible in a
    shallow clone, where the history is not there to be checked against.
    """
    rows = documented_rows(document)
    problems: list[str] = []
    notes: list[str] = []

    missing = sorted({row.commit for row in rows if row.commit and not commit_is_available(row.commit)})
    if missing and not repository_is_shallow():
        problems.append(
            "the snapshot commit(s) "
            + ", ".join(missing)
            + " are not in this repository; the document points at a commit that does not exist"
        )
        return problems, notes
    if missing:
        notes.append(
            "the snapshot commit(s) "
            + ", ".join(missing)
            + " are not in this shallow clone; the snapshot rows are not checked here"
        )
        warnings.warn(
            "the snapshot rows of REPO_SHAPE.md are not checked in this shallow clone",
            RuntimeWarning,
            stacklevel=2,
        )

    live = [row for row in rows if not row.commit]
    snapshot = [row for row in rows if row.commit and commit_is_available(row.commit)]

    for row in live:
        if not SCOPE_RE.match(row.scope):
            problems.append(f"{row.label}: unknown scope {row.scope!r}")
            continue
        try:
            observed = run_command(row.command, tree)
        except (subprocess.CalledProcessError, AssertionError) as exc:
            problems.append(f"{row.label}: the command failed: {exc}")
            continue
        if observed != row.value:
            problems.append(
                f"{row.label}: document says {row.value}, command says {observed} ({row.command})"
            )

    commits = sorted({row.commit for row in snapshot})
    with snapshot_checkouts(commits) as checkouts:
        for row in snapshot:
            try:
                observed = run_command(row.command, checkouts[row.commit])
            except (subprocess.CalledProcessError, AssertionError) as exc:
                problems.append(f"{row.label}: the command failed at {row.commit}: {exc}")
                continue
            if observed != row.value:
                problems.append(
                    f"{row.label}: document says {row.value}, the command says {observed} "
                    f"at {row.commit} ({row.command})"
                )
    return problems, notes


def root_entries_claimed(document: Path = REPO_SHAPE) -> list[str]:
    """The root entries the "Root contents" block lists."""
    text = document.read_text(encoding="utf-8")
    section = text.split("## Root contents", 1)[1]
    block = section.split("```", 2)[1]
    entries = []
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        entries.append(stripped.split("#", 1)[0].strip().rstrip("/"))
    return entries


def tracked_root_entries(tree: Path) -> list[str]:
    """Every top-level entry the git index knows."""
    completed = subprocess.run(
        "git ls-files | cut -d/ -f1 | sort -u",
        cwd=tree,
        shell=True,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in completed.stdout.split() if line]


def root_allowlist() -> list[str]:
    """The root entries the truth kit allows."""
    config = json.loads(TRUTH_CONFIG.read_text(encoding="utf-8"))
    return list(config.get("rootAllowlist", []))


def test_repo_shape_numbers_are_reproducible() -> None:
    """Every number in REPO_SHAPE.md is produced by the command beside it."""
    rows = documented_rows()
    assert len(rows) >= MIN_ROWS, (
        f"REPO_SHAPE.md exposes only {len(rows)} verifiable rows, expected at least {MIN_ROWS}"
    )
    problems, _ = check_rows(ROOT)
    assert not problems, "REPO_SHAPE.md drifted from the tree:\n  " + "\n  ".join(problems)


def test_every_row_declares_a_scope() -> None:
    """A row without a scope cannot be checked and must not exist."""
    unknown = [f"{row.label}: {row.scope!r}" for row in documented_rows() if not SCOPE_RE.match(row.scope)]
    assert not unknown, "rows without a known scope:\n  " + "\n  ".join(unknown)


def test_the_root_block_of_the_document_matches_the_tree() -> None:
    """The block that calls itself authoritative must list every root entry.

    The block was a claim without a command: it listed 14 entries while the
    tree had 15 (``.npmrc`` was missing), and the table of the document could
    not see it because the block is not a table.
    """
    claimed = sorted(root_entries_claimed())
    tracked = sorted(tracked_root_entries(ROOT))
    assert claimed == tracked, (
        "the root block of REPO_SHAPE.md drifted from the tree:\n"
        f"  missing from the document: {sorted(set(tracked) - set(claimed))}\n"
        f"  not in the tree any more: {sorted(set(claimed) - set(tracked))}"
    )


def test_no_root_entry_outside_the_allowlist() -> None:
    """The live root rule: the tree may not hold a root entry the kit forbids.

    This is the invariant that survives the next job. The block of the document
    is a snapshot; this check is not, because it is a rule and not a count.
    """
    allowed = set(root_allowlist())
    tracked = set(tracked_root_entries(ROOT))
    unexpected = sorted(tracked - allowed)
    assert not unexpected, (
        "tracked root entries that scripts/truth/config.json does not allow: "
        f"{unexpected}; the allowlist is {sorted(allowed)}"
    )


def test_the_shape_guard_survives_a_healthy_tree_growth() -> None:
    """A job that adds a skill must not have to edit a document it does not own.

    The counts of the document (skills, packages, tracked files) move whenever
    the next job does its job. Before D-066 every count was checked against the
    current tree, so adding a skill turned the suite of a job that does not own
    ``docs/truth/`` red — a failure the job was not allowed to fix. The live
    rows are the invariants; the counts are bound to the commit they describe.
    """
    with temporary_worktree("HEAD") as tree:
        demo = tree / "skills" / "engineering" / "zz-shape-growth-demo"
        demo.mkdir(parents=True)
        (demo / "SKILL.md").write_text(
            "---\nname: zz-shape-growth-demo\ndescription: demo skill for the growth guard.\n---\n\n# demo\n",
            encoding="utf-8",
        )
        # The next job regenerates the catalogue, as the shape document demands.
        subprocess.run(
            ["node", "scripts/gen-catalog.mjs"],
            cwd=tree,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "add", "--", "skills/engineering/zz-shape-growth-demo", "catalog.json"],
            cwd=tree,
            check=True,
            capture_output=True,
            text=True,
        )
        problems, _ = check_rows(tree)
        assert not problems, (
            "the shape guard turned red on a healthy tree change:\n  " + "\n  ".join(problems)
        )
