#!/usr/bin/env python3
# truth:allow-german-file - this file reads the STATUS.md files of the product
# repositories, which are written in German. The German words below are the
# vocabulary of that user-facing prose (the success markers a German status
# table uses), not the prose of this code.
"""The table format of the product repositories' STATUS.md files.

The product repositories do not write the buckets of this skill; they write
markdown tables:

    | <what was run> | <result> | <evidence> |
    |---|---|---|
    | `npm test` | **13 passed, 0 failed**, exit 0 | `npm-test.log` |

A row that asserts a success is a *claim*. A claim must name the command that
was run, the exit code that command returned and the log file that proves it.
This module finds the claims and their three elements; the checker decides
whether they are honest.
"""
from __future__ import annotations

import re

CODE_SPAN_RE = re.compile(r"`([^`\n]+)`")
URL_RE = re.compile(r"^[a-z][a-z0-9+.-]*://", re.IGNORECASE)
EXIT_CODE_RE = re.compile(
    r"\b(?:exit(?:\s+code)?|rc)\s*[:=]?\s*(\d{1,3})\b", re.IGNORECASE
)
BARE_EXIT_RE = re.compile(r"^\s*(\d{1,3})\s*$")
SEPARATOR_CELL_RE = re.compile(r"^:?-{1,}:?$")
SUCCESS_RE = re.compile(
    r"\bexit\s*[:=]?\s*0\b"
    r"|\bgr[uü]n\b"
    r"|\bgreen\b"
    r"|\bpass(?:ed|es)?\b"
    r"|\bok\b"
    r"|\bbestanden\b"
    r"|\berfolg(?:reich)?\b"
    r"|\bsuccessful\b"
    r"|\bsucceeded\b"
    r"|[\u2713\u2705]"
    r"|\b0\s+(?:fail|failure|failures|fehler|fehlgeschlagen|findings|errors?)\b",
    re.IGNORECASE,
)

# Suffixes that make a backticked span a file name and not a command.
FILE_SUFFIXES = (
    ".log", ".txt", ".json", ".md", ".sql", ".py", ".mjs", ".cjs", ".js", ".ts",
    ".tsx", ".jsx", ".csv", ".xml", ".html", ".yaml", ".yml", ".out", ".err",
    ".diff", ".patch", ".png", ".jpg", ".jpeg", ".svg", ".mp4", ".webm", ".pdf",
)
# Tools the repositories run. A bare word from this list is a command.
KNOWN_COMMANDS = {
    "npm", "node", "npx", "pnpm", "yarn", "bun", "deno", "python", "python3",
    "pytest", "bash", "sh", "zsh", "docker", "git", "make", "curl", "psql",
    "pg_dump", "tsc", "eslint", "prettier", "ruff", "mypy", "go", "cargo",
    "java", "mvn", "gradle", "dotnet", "kubectl", "helm", "terraform", "jq",
    "rg", "grep", "sed", "awk", "tar", "unzip",
}


def split_cells(line: str) -> list[str] | None:
    """Return the cells of a markdown table row, or None if it is not one."""
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|") or len(stripped) < 3:
        return None
    return [cell.strip() for cell in stripped[1:-1].split("|")]


def is_separator_row(cells: list[str]) -> bool:
    """True for the `|---|---|` row that separates a header from its body."""
    values = [cell.replace(" ", "") for cell in cells if cell]
    return bool(values) and all(SEPARATOR_CELL_RE.match(value) for value in values)


def tables(text: str) -> list[list[tuple[int, list[str]]]]:
    """Return every markdown table of a text as a list of (line number, cells)."""
    found: list[list[tuple[int, list[str]]]] = []
    current: list[tuple[int, list[str]]] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        cells = split_cells(raw)
        if cells is None:
            if current:
                found.append(current)
                current = []
            continue
        current.append((lineno, cells))
    if current:
        found.append(current)
    return found


def is_path(span: str) -> bool:
    """True when a backticked span names a file rather than a command.

    A file name has a suffix (``npm-install.log``) or a dotted last segment
    (``docs/m1/FREEZE_REPORT_3.md``). A URL path (``/demo-thing``) and a
    connection string (``hq@127.0.0.1:18432/hq``) are not evidence files.
    """
    if URL_RE.match(span):
        return False
    if re.search(r"\s", span) or "@" in span:
        return False
    if span.lower().endswith(FILE_SUFFIXES):
        return True
    if "/" in span:
        return "." in span.rsplit("/", 1)[-1]
    return False


def is_command(span: str) -> bool:
    """True when a backticked span names something that can be run."""
    if URL_RE.match(span) or is_path(span):
        return False
    if re.search(r"\s", span):
        return True
    if ":" in span:
        return True
    head = span.strip().split()[0] if span.strip() else ""
    return head.lower() in KNOWN_COMMANDS


def find_exit_code(cells: list[str], text: str) -> str | None:
    """Return the exit code the row names, if it names one."""
    for cell in cells:
        match = BARE_EXIT_RE.match(cell)
        if match:
            return match.group(1)
    match = EXIT_CODE_RE.search(text)
    return match.group(1) if match else None


def claims(text: str) -> list[dict]:
    """Return every success claim of the table format.

    A claim is a table row that asserts a success ("12 passed", "exit 0",
    "grün"). For each claim the command, the exit code and the log path are
    collected; a claim that names none of them is still a claim — that is the
    finding the checker reports.
    """
    found: list[dict] = []
    for table in tables(text):
        body = [row for row in table if not is_separator_row(row[1])]
        if len(body) < 2:
            continue
        for lineno, cells in body[1:]:
            joined = " ".join(cells)
            if not SUCCESS_RE.search(joined):
                continue
            spans = CODE_SPAN_RE.findall(joined)
            found.append({
                "line": lineno,
                "claim": (cells[0] if cells else "")[:80],
                "commands": [span for span in spans if is_command(span)],
                "paths": [span for span in spans if is_path(span)],
                "exit_code": find_exit_code(cells, joined),
            })
    return found
