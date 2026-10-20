"""The commands a skill documents must be runnable (SKL-W0-01, TASK-0008).

A skill is the instruction set of an agent: every command it prints is a
promise that the reader can copy and run. Two ways break that promise:

* the script a command names does not exist (it was renamed, moved or never
  shipped), and
* the command as written fails — a path that does not resolve, a flag that is
  wrong.

Both happened in this tree: ``problem-json-contracts`` documented a
``--schema-dir references/examples/schemas`` that never existed, and the
``honest-status`` skill pointed at a ``STATUS.md`` it does not ship.

The commands are read FROM the documents, never copied into this module, so a
document that drifts away from the tree fails here. A command whose input
file lives outside the skill (a ``STATUS.md`` of the repository an agent is
working on) is skipped: it is a template, not a promise about this tree.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

COMMAND_RE = re.compile(r"`((?:python3|node|bash)\s[^\n`]+)`")
SCRIPT_RE = re.compile(r"(?<![-\w/])([A-Za-z0-9_./-]+\.(?:py|mjs|sh))(?![-\w])")
FILE_TOKEN_RE = re.compile(
    r"(?<![-\w/])([A-Za-z0-9_./-]+\.(?:py|mjs|sh|json|ya?ml|md))(?![-\w])"
)


def skill_documents() -> list[Path]:
    """Every SKILL.md of the tree."""
    return sorted(ROOT.glob("skills/*/*/SKILL.md"))


def skill_folders() -> list[Path]:
    """The folder of every skill of the tree."""
    return [document.parent for document in skill_documents()]


def documented_commands(text: str) -> list[str]:
    """The single-line commands a document prints in backticks."""
    commands = []
    for match in COMMAND_RE.finditer(text):
        command = match.group(1).strip()
        if "<" in command or ">" in command:
            continue  # a template with a placeholder, not a runnable command
        commands.append(command)
    return commands


def resolve(script: str, document: Path) -> Path | None:
    """The folder the script of a command lives in, or None when it is lost.

    A skill names its own scripts without a folder, a package may hold a
    shared script, the repository root holds the entry points and a skill may
    point at the script of a sibling skill.
    """
    candidates = [document.parent, document.parent.parent, ROOT, *skill_folders()]
    for folder in candidates:
        if (folder / script).is_file():
            return folder
    return None


def test_every_documented_script_exists() -> None:
    """A command that names a script nobody ships is a broken promise."""
    missing = []
    for document in skill_documents():
        text = document.read_text(encoding="utf-8")
        for command in documented_commands(text):
            match = SCRIPT_RE.search(command)
            if match is None:
                continue
            script = match.group(1)
            if resolve(script, document) is None:
                missing.append(f"{document.relative_to(ROOT)}: {command}")
    assert not missing, "documented scripts that do not exist:\n" + "\n".join(missing)


def test_every_documented_command_whose_input_exists_runs_green() -> None:
    """A documented command whose input is part of the tree has to run green."""
    failures = []
    checked = 0
    for document in skill_documents():
        text = document.read_text(encoding="utf-8")
        for command in documented_commands(text):
            match = SCRIPT_RE.search(command)
            if match is None:
                continue
            script = match.group(1)
            folder = resolve(script, document)
            assert folder is not None, f"{document.relative_to(ROOT)}: {command}"
            tokens = FILE_TOKEN_RE.findall(command)
            broken = [
                token
                for token in tokens
                if "/" in token and not (folder / token).exists()
            ]
            if broken:
                # A path inside the tree that does not exist is a broken
                # reference, not a template: the command cannot work.
                failures.append(
                    f"{document.relative_to(ROOT)}: {command} -> missing {broken[0]}"
                )
                continue
            if any(
                "/" not in token and not (folder / token).exists() for token in tokens
            ):
                # A bare file name that the tree does not ship (a STATUS.md of
                # the repository an agent is working on) is a template.
                continue
            result = subprocess.run(
                command,
                shell=True,
                cwd=folder,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            checked += 1
            if result.returncode != 0:
                failures.append(
                    f"{document.relative_to(ROOT)}: {command} -> exit {result.returncode}\n"
                    f"{result.stdout}{result.stderr}"
                )
    assert not failures, "documented commands that fail:\n" + "\n".join(failures)
    assert checked >= 6, (
        f"only {checked} documented commands were checked — the guard is too weak"
    )
