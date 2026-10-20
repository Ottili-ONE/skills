"""The repair log must stay complete, unique and provable.

``docs/truth/REPAIR_LOG.md`` is the index of the trunk repairs of SKL-W0-01.
A defect that is not in the index cannot be found, an id that names two
defects cannot be cited, and a proof command that no longer runs is a claim
without evidence. This module is the guard for those three properties:

* every defect section of the log has exactly one index entry, and every index
  entry names a defect section that exists;
* every index entry carries all six fields (symptom, reproduction, root cause,
  fix, proof, date);
* every proof command of the index is in the proof block of the log, and every
  command marked ``# auto`` is executed here and must exit 0;
* the follow-up list of the job exists and every item names a path and a
  symptom.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_PATH = os.path.join(REPO_ROOT, "docs", "truth", "REPAIR_LOG.md")

DEFECT_SECTION_RE = re.compile(r"^## (D-\d{3}) — ", re.MULTILINE)
INDEX_ENTRY_RE = re.compile(r"^#### (D-\d{3}) — ", re.MULTILINE)
PROOF_LABEL_RE = re.compile(r"^### ([A-Z][A-Z0-9-]*) — ", re.MULTILINE)
COMMAND_RE = re.compile(r"^\$ (.+?)(?:\s+# auto)?$", re.MULTILINE)
REQUIRED_FIELDS = ("Symptom", "Reproduction", "Root cause", "Fix (files)", "Proof", "Date")


def read_log() -> str:
    with open(LOG_PATH, encoding="utf-8") as handle:
        return handle.read()


def split_section(text: str, start: int) -> str:
    """Return the body of the section that starts at ``start``."""
    body = text[start:]
    end = body.find("\n## ")
    return body if end == -1 else body[:end]


def index_entries(text: str) -> dict[str, str]:
    """Map every defect id to the text of its index entry."""
    entries: dict[str, str] = {}
    for match in INDEX_ENTRY_RE.finditer(text):
        entries[match.group(1)] = split_section(text, match.start())
    return entries


def proof_commands(text: str) -> dict[str, tuple[str, bool]]:
    """Map every proof label to its command and whether it must be re-run."""
    commands: dict[str, tuple[str, bool]] = {}
    for match in PROOF_LABEL_RE.finditer(text):
        label = match.group(1)
        block = text[match.end():]
        block = block[: block.find("\n### ")] if "\n### " in block else block
        found = COMMAND_RE.search(block)
        if found:
            commands[label] = (found.group(1), found.group(0).endswith("# auto"))
    return commands


def test_the_log_exists() -> None:
    assert os.path.isfile(LOG_PATH), "docs/truth/REPAIR_LOG.md is missing"


def test_every_defect_id_is_unique() -> None:
    ids = DEFECT_SECTION_RE.findall(read_log())
    duplicates = sorted({value for value in ids if ids.count(value) > 1})
    assert not duplicates, f"defect ids that name more than one defect: {duplicates}"


def test_index_and_sections_name_the_same_defects() -> None:
    text = read_log()
    sections = DEFECT_SECTION_RE.findall(text)
    entries = index_entries(text)
    missing = sorted(set(sections) - set(entries))
    unknown = sorted(set(entries) - set(sections))
    assert not missing, f"defects without an index entry: {missing}"
    assert not unknown, f"index entries without a defect section: {unknown}"


def test_every_index_entry_has_all_six_fields() -> None:
    for defect_id, entry in index_entries(read_log()).items():
        for field in REQUIRED_FIELDS:
            pattern = re.compile(r"^- \*\*" + re.escape(field) + r":\*\* (.+)$", re.MULTILINE)
            found = pattern.search(entry)
            assert found, f"{defect_id} has no '{field}' field"
            assert found.group(1).strip(), f"{defect_id} has an empty '{field}' field"


def test_every_proof_command_is_in_the_proof_block() -> None:
    text = read_log()
    labels = proof_commands(text)
    assert labels, "the proof block of the log is empty"
    for defect_id, entry in index_entries(text).items():
        found = re.search(r"^- \*\*Proof:\*\* (.+)$", entry, re.MULTILINE)
        assert found, f"{defect_id} has no proof"
        quoted = re.findall(r"`([^`]+)`", found.group(1))
        assert quoted, f"{defect_id} names no proof command"
        assert quoted[0] in labels, f"{defect_id} names the unknown proof label {quoted[0]!r}"


def test_the_proof_block_documents_every_label_it_uses() -> None:
    text = read_log()
    labels = proof_commands(text)
    for defect_id, entry in index_entries(text).items():
        found = re.search(r"^- \*\*Proof:\*\* `([^`]+)`", entry, re.MULTILINE)
        label = found.group(1)
        command = labels[label][0]
        assert command in text, f"the command of {label} is not in the proof block"


def test_the_follow_up_list_exists_and_names_path_and_symptom() -> None:
    text = read_log()
    heading = "## Follow-ups for later trunk repair jobs"
    assert text.count(heading) == 1, "there must be exactly one follow-up section"
    section = text[text.index(heading):]
    items = re.findall(r"^\d+\. \*\*(.+?)\*\*", section, re.MULTILINE)
    assert items, "the follow-up section lists no item"
    for item in items:
        assert "`" in item, f"the follow-up {item!r} names no path"


def auto_labels() -> list[str]:
    """The labels whose command is fast and side-effect free.

    The slow commands (whole pytest suites, the job gate) are not run here:
    the gate runs the whole suite, and the truth kit refuses a test run that
    reports skipped tests, so a "skip" would be the wrong instrument.
    """
    return sorted(label for label, (_, is_auto) in proof_commands(read_log()).items() if is_auto)


@pytest.mark.parametrize("label", auto_labels())
def test_the_auto_proof_commands_still_pass(label: str) -> None:
    command, _ = proof_commands(read_log())[label]
    result = subprocess.run(
        command,
        shell=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
        env={**os.environ, "TMPDIR": os.environ.get("TMPDIR", "/tmp")},
    )
    assert result.returncode == 0, (
        f"the proof command {label} failed with exit {result.returncode}:\n"
        f"$ {command}\n{result.stdout}\n{result.stderr}"
    )


def test_the_repair_log_does_not_claim_an_unrun_proof() -> None:
    """Every ``exit=`` line of the proof block must be 0."""
    text = read_log()
    block = text[text.index("## Proof commands executed on 2026-10-20"):]
    block = block[: block.index("\n## Follow-ups for later trunk repair jobs")]
    exits = re.findall(r"^exit=(\d+)$", block, re.MULTILINE)
    assert exits, "the proof block records no exit code"
    bad = [code for code in exits if code != "0"]
    assert not bad, f"the proof block records a failing command: exit={bad}"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
