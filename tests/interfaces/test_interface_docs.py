"""The interface documents must describe the tools that exist (SKL-W1-01, TASK-0003).

A document is a claim about a tool. When the tool changes and the document
does not, the document becomes a lie that a consumer trusts — the README
claimed for months that the ``ref-*`` packages resolved to no skills, and they
have always been installable (G-011 in ``docs/gaps/SKL-W1-01.md``).

These tests hold the three documents of the interfaces —
``README.md``, ``docs/interfaces/validate.md`` and ``docs/interfaces/install.md``
— against the tools themselves:

* every flag of a tool is documented, and every documented flag exists,
* every published contract id of the code is documented, and no other id is,
* every file the documents name exists,
* the false claim about the ``ref-*`` packages does not come back.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
VALIDATE_DOC = ROOT / "docs" / "interfaces" / "validate.md"
INSTALL_DOC = ROOT / "docs" / "interfaces" / "install.md"
VALIDATE = ROOT / "scripts" / "validate.py"
INSTALL = ROOT / "scripts" / "install.sh"

if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from ottili_contracts import (  # noqa: E402
    CONTRACT_INSTALL_MANIFEST,
    CONTRACT_VALIDATE_REPORT,
    CONTRACTS,
)

DOCUMENTS = (README, VALIDATE_DOC, INSTALL_DOC)


def readme_text() -> str:
    """The text of the README.

    Inputs:
        none.
    Outputs:
        the README as text.
    Failure modes:
        OSError when the README cannot be read.
    """
    return README.read_text(encoding="utf-8")


def help_of(script: Path) -> str:
    """The usage text of one tool.

    Inputs:
        script: the tool to ask.
    Outputs:
        the usage text on stdout.
    Failure modes:
        none. A non-zero exit code of the tool is a failure of the tool, and
        the assertion in the caller reports it.
    """
    command = (
        ["python3", "-I", str(script), "--help"]
        if script.suffix == ".py"
        else ["bash", str(script), "--help"]
    )
    result = subprocess.run(
        command, cwd=ROOT, capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


def test_the_readme_documents_every_flag_of_the_installer() -> None:
    """Every flag of the installer is in the README, and every flag exists."""
    text = readme_text()
    usage = help_of(INSTALL)
    for flag in ("--target", "--package", "--check", "--dry-run", "--force", "--link", "--json", "--version"):
        assert flag in text, f"the README does not document {flag}"
        assert flag in usage, f"the installer does not know {flag}"


def test_the_readme_documents_every_flag_of_the_validator() -> None:
    """Every flag of the validator is in the README, and every flag exists."""
    text = readme_text()
    usage = help_of(VALIDATE)
    for flag in ("--json", "--jsonl", "--everywhere", "--version"):
        assert flag in text, f"the README does not document {flag}"
        assert flag in usage, f"the validator does not know {flag}"


def test_the_interface_documents_document_their_own_flags() -> None:
    """Each interface document names the flags of its own tool."""
    validate_doc = VALIDATE_DOC.read_text(encoding="utf-8")
    install_doc = INSTALL_DOC.read_text(encoding="utf-8")
    for flag in ("--json", "--jsonl", "--everywhere", "--version"):
        assert flag in validate_doc, f"the validator contract does not document {flag}"
    for flag in ("--target", "--package", "--check", "--dry-run", "--force", "--link", "--json", "--version"):
        assert flag in install_doc, f"the installer contract does not document {flag}"


def test_the_documents_name_the_published_contract_ids() -> None:
    """The ids of the code are the ids of the documents — no more, no less."""
    expected = {
        README: set(CONTRACTS),
        VALIDATE_DOC: {CONTRACT_VALIDATE_REPORT},
        INSTALL_DOC: {CONTRACT_INSTALL_MANIFEST},
    }
    for document, wanted in expected.items():
        text = document.read_text(encoding="utf-8")
        for contract_id in wanted:
            assert contract_id in text, f"{document.name} does not name {contract_id}"
        found = set(re.findall(r"ottili\.skills\.[a-z-]+/v\d+", text))
        assert found == wanted, (
            f"{document.name} names contracts that do not exist or does not belong to it: "
            f"{found - wanted}"
        )


def test_every_file_the_documents_name_exists() -> None:
    """A documented path that does not exist is a broken promise."""
    for document in DOCUMENTS:
        text = document.read_text(encoding="utf-8")
        for path in re.findall(r"`(scripts/ottili_contracts/[^`]+)`", text):
            assert (ROOT / path).exists(), f"{document.name} names {path}, which does not exist"


def test_the_documents_state_the_exit_codes_of_the_tools() -> None:
    """Every document names the three exit codes of its tool."""
    for document in (README, VALIDATE_DOC, INSTALL_DOC):
        text = document.read_text(encoding="utf-8")
        assert re.search(r"`?0`?.*(no findings|installed|verified)", text, re.IGNORECASE), (
            f"{document.name} does not state the exit code 0"
        )
        assert "1" in text and "2" in text, f"{document.name} does not state the exit codes 1 and 2"


def test_the_false_claim_about_the_reference_packages_does_not_come_back() -> None:
    """The `ref-*` packages are real packages; no document may say otherwise."""
    for document in DOCUMENTS:
        text = document.read_text(encoding="utf-8")
        assert "resolve to no skills" not in text, (
            f"{document.name} claims that the ref-* packages resolve to no skills; they are "
            "real packages and --package ref-datev-extf installs that skill"
        )
        assert "reserved on-demand names" not in text, (
            f"{document.name} claims that the ref-* packages are reserved on-demand names"
        )


def test_the_entry_points_are_executable_in_the_index() -> None:
    """A consumer runs ``./scripts/install.sh``; the bit must be set.

    The README tells the consumer to run ``./scripts/install.sh --target ...``.
    A rewrite of the script that loses the executable bit breaks every one of
    those commands, and nothing in the test suite notices: the tests call the
    script with ``bash``. The mode of the tracked file is therefore part of
    the contract and is checked here.
    """
    for script in (INSTALL, VALIDATE):
        relative = script.relative_to(ROOT).as_posix()
        result = subprocess.run(
            ["git", "ls-files", "-s", relative],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.stdout.startswith("100755"), (
            f"{relative} is not executable in the index: {result.stdout.strip()}"
        )
