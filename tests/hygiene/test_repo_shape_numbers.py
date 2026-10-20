"""``docs/truth/REPO_SHAPE.md`` must describe the tree that actually exists.

The repository shape is a *claim* about the tree. A claim that drifts is worse
than no claim, because the next job reads it and acts on it. This test therefore
executes the command that ``REPO_SHAPE.md`` itself prints next to every number
and asserts that the printed number is the number the document claims.

The test is deliberately generic: it parses the markdown tables, takes the
command cell verbatim and runs it. It does not know any particular metric, so a
new row added to the document is checked automatically, and a stale row fails.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO_SHAPE = ROOT / "docs" / "truth" / "REPO_SHAPE.md"

#: Only read-only commands may be executed out of a markdown document.
ALLOWED_PREFIXES = ("git ls-files", "ls -d ", "python3 -c ", "find ")

#: The document must keep at least this many verifiable rows, otherwise a
#: truncated table would make this test pass without checking anything.
MIN_ROWS = 7


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


def documented_numbers() -> list[tuple[str, str, str]]:
    """Every ``(label, value, command)`` triple the document claims."""
    text = REPO_SHAPE.read_text(encoding="utf-8")
    rows: list[tuple[str, str, str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = split_cells(stripped)
        if len(cells) != 3:
            continue
        label, value, command = cells
        if not value.isdigit():
            continue
        command = command.strip().strip("`").replace("\\|", "|")
        if not command:
            continue
        rows.append((label, value, command))
    return rows


def run_command(command: str) -> str:
    """Run a documented command and return its stdout."""
    assert command.startswith(ALLOWED_PREFIXES), f"undocumented command kind: {command!r}"
    completed = subprocess.run(
        command,
        cwd=ROOT,
        shell=True,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def test_repo_shape_numbers_are_reproducible() -> None:
    """Every number in REPO_SHAPE.md is produced by the command beside it."""
    rows = documented_numbers()
    assert len(rows) >= MIN_ROWS, (
        f"REPO_SHAPE.md exposes only {len(rows)} verifiable rows, expected at least {MIN_ROWS}"
    )
    wrong = []
    for label, claimed, command in rows:
        observed = run_command(command)
        if observed != claimed:
            wrong.append(f"{label}: document says {claimed}, command says {observed} ({command})")
    assert not wrong, "REPO_SHAPE.md drifted from the tree:\n  " + "\n  ".join(wrong)
