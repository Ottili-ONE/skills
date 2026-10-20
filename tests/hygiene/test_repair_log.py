"""The repair log must stay complete, unique and provable.

``docs/truth/REPAIR_LOG.md`` is the index of the trunk repairs of SKL-W0-01.
A defect that is not in the index cannot be found, an id that names two
defects cannot be cited, and a proof command that no longer runs is a claim
without evidence. This module is the guard for those three properties:

* every defect section of the log has exactly one index entry, and every index
  entry names a defect section that exists;
* every index entry carries all six fields (symptom, reproduction, root cause,
  fix, proof, date) — per entry, not per document;
* every index entry cites a proof label, and the command it writes next to the
  label is the command the proof block runs;
* every defect section repeats the proof label and the date of its index entry,
  so the narrative and the map cannot drift apart;
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
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED_FIELDS = ("Symptom", "Reproduction", "Root cause", "Fix (files)", "Proof", "Date")
FOLLOW_UP_HEADING = "## Follow-ups for later trunk repair jobs"
MIN_SYMPTOM_CHARS = 40


def read_log() -> str:
    with open(LOG_PATH, encoding="utf-8") as handle:
        return handle.read()


def headings(text: str) -> list[tuple[int, int]]:
    """Return the position and the level of every heading of the text.

    A line inside a fenced code block is not a heading, even when it starts
    with a hash.
    """
    found: list[tuple[int, int]] = []
    position = 0
    inside_fence = False
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("```"):
            inside_fence = not inside_fence
        elif not inside_fence:
            match = re.match(r"^(#{1,6}) ", line)
            if match:
                found.append((position, len(match.group(1))))
        position += len(line) + 1
    return found


def block(text: str, start: int, level: int) -> str:
    """Return the body of the heading block that starts at ``start``.

    The block ends at the next heading of the same or a higher level, so a
    ``####`` entry ends at the next ``####`` entry and not at the end of the
    document. Bounding the block correctly is what makes a per-entry check a
    per-entry check (D-055).
    """
    for position, heading_level in headings(text):
        if position > start and heading_level <= level:
            return text[start:position]
    return text[start:]


def defect_sections(text: str) -> dict[str, str]:
    """Map every defect id to the text of its narrative section."""
    sections: dict[str, str] = {}
    for match in DEFECT_SECTION_RE.finditer(text):
        sections[match.group(1)] = block(text, match.start(), 2)
    return sections


def index_entries(text: str) -> dict[str, str]:
    """Map every defect id to the text of its index entry."""
    entries: dict[str, str] = {}
    for match in INDEX_ENTRY_RE.finditer(text):
        entries[match.group(1)] = block(text, match.start(), 4)
    return entries


def proof_block(text: str) -> str:
    """Return the section of the log that holds the proof commands."""
    for position, heading_level in headings(text):
        if heading_level != 2:
            continue
        body = block(text, position, 2)
        if PROOF_LABEL_RE.search(body):
            return body
    return ""


def proof_commands(text: str) -> dict[str, tuple[str, bool]]:
    """Map every proof label to its command and whether it must be re-run."""
    commands: dict[str, tuple[str, bool]] = {}
    for match in PROOF_LABEL_RE.finditer(text):
        label = match.group(1)
        body = block(text, match.start(), 3)
        found = COMMAND_RE.search(body)
        if found:
            commands[label] = (found.group(1), found.group(0).endswith("# auto"))
    return commands


def entry_field(entry: str, field: str) -> str | None:
    """Return the value of a ``- **Field:** value`` line of an index entry."""
    pattern = re.compile(r"^- \*\*" + re.escape(field) + r":\*\* (.+)$", re.MULTILINE)
    found = pattern.search(entry)
    return found.group(1).strip() if found else None


def entry_label_and_command(entry: str, field: str = "Proof") -> tuple[str | None, str | None]:
    """Return the proof label and the command an entry writes down.

    The command is ``None`` when the entry names the label only; the index
    entries must name the command, a defect section may leave it out.
    """
    value = entry_field(entry, field)
    if not value:
        return None, None
    quoted = re.findall(r"`([^`]+)`", value)
    if not quoted:
        return None, None
    return quoted[0], (quoted[1] if len(quoted) > 1 else None)


def field_problems(text: str) -> list[str]:
    """Every index entry that does not carry all six fields."""
    problems: list[str] = []
    for defect_id, entry in index_entries(text).items():
        for field in REQUIRED_FIELDS:
            value = entry_field(entry, field)
            if value is None:
                problems.append(f"{defect_id} has no '{field}' field")
            elif not value:
                problems.append(f"{defect_id} has an empty '{field}' field")
    return problems


def section_index_problems(text: str) -> list[str]:
    """Every defect whose narrative section and index entry disagree."""
    problems: list[str] = []
    commands = proof_commands(text)
    entries = index_entries(text)
    sections = defect_sections(text)
    for defect_id, section in sections.items():
        entry = entries.get(defect_id, "")
        label, command = entry_label_and_command(entry)
        if not label:
            problems.append(f"{defect_id} has no proof label in its index entry")
            continue
        if label not in commands:
            problems.append(f"{defect_id} names the unknown proof label {label!r}")
            continue
        if not command:
            problems.append(f"{defect_id} names no command next to the proof label")
            continue
        if command != commands[label][0]:
            problems.append(
                f"{defect_id} writes the command {command!r} but the proof block of "
                f"{label} runs {commands[label][0]!r}"
            )
        section_label, section_command = entry_label_and_command(section, "Index proof")
        if not section_label:
            problems.append(f"{defect_id} has no 'Index proof' line in its section")
        else:
            if section_label != label:
                problems.append(
                    f"{defect_id} cites {section_label!r} in its section but {label!r} in the index"
                )
            if section_command and section_command != command:
                problems.append(
                    f"{defect_id} writes the command {section_command!r} in its section but "
                    f"{command!r} in the index"
                )
        section_date = entry_field(section, "Date")
        entry_date = entry_field(entry, "Date")
        if not section_date:
            problems.append(f"{defect_id} has no 'Date' line in its section")
        elif not DATE_RE.match(section_date):
            problems.append(f"{defect_id} has the malformed date {section_date!r}")
        elif section_date != entry_date:
            problems.append(
                f"{defect_id} is dated {section_date} in its section but {entry_date} in the index"
            )
    return problems


def follow_up_problems(text: str) -> list[str]:
    """Every problem of the follow-up list of the job."""
    problems: list[str] = []
    if text.count(FOLLOW_UP_HEADING) != 1:
        return ["there must be exactly one follow-up section"]
    section = text[text.index(FOLLOW_UP_HEADING):]
    items = list(re.finditer(r"^\d+\. \*\*(.+?)\*\*(.*?)(?=^\d+\. \*\*|\Z)", section, re.MULTILINE | re.DOTALL))
    if not items:
        return ["the follow-up section lists no item"]
    for item in items:
        title, body = item.group(1), item.group(2)
        if "`" not in title:
            problems.append(f"the follow-up {title!r} names no path")
        symptom = re.sub(r"[`*]", " ", body)
        symptom = re.sub(r"\s+", " ", symptom).strip()
        if len(symptom) < MIN_SYMPTOM_CHARS:
            problems.append(f"the follow-up {title!r} names no symptom")
    return problems


def remove_index_field(text: str, defect_id: str, field: str) -> str:
    """Return the log with one field line removed from one index entry."""
    entry = index_entries(text)[defect_id]
    stripped = re.sub(r"^- \*\*" + re.escape(field) + r":\*\* .*\n", "", entry, count=1, flags=re.MULTILINE)
    assert stripped != entry, f"{defect_id} has no '{field}' field to remove"
    return text.replace(entry, stripped, 1)


def replace_inline_command(text: str, defect_id: str, command: str) -> str:
    """Return the log with the command of one index entry replaced."""
    entry = index_entries(text)[defect_id]
    replaced = re.sub(r"(- \*\*Proof:\*\* `[^`]+` — `)[^`]+(`)", r"\g<1>" + command + r"\g<2>", entry, count=1)
    assert replaced != entry, f"{defect_id} has no inline command to replace"
    return text.replace(entry, replaced, 1)


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
    problems = field_problems(read_log())
    assert not problems, "; ".join(problems)


def test_a_missing_index_field_is_detected() -> None:
    """The field check must be per entry: a broken entry must be reported."""
    problems = field_problems(remove_index_field(read_log(), "D-030", "Date"))
    assert any("D-030" in problem and "Date" in problem for problem in problems), problems


def test_a_missing_index_symptom_is_detected() -> None:
    problems = field_problems(remove_index_field(read_log(), "D-031", "Symptom"))
    assert any("D-031" in problem and "Symptom" in problem for problem in problems), problems


def test_every_proof_command_is_in_the_proof_block() -> None:
    text = read_log()
    labels = proof_commands(text)
    assert labels, "the proof block of the log is empty"
    for defect_id, entry in index_entries(text).items():
        label, command = entry_label_and_command(entry)
        assert label, f"{defect_id} names no proof label"
        assert command, f"{defect_id} names no command next to the proof label"
        assert label in labels, f"{defect_id} names the unknown proof label {label!r}"


def test_the_proof_block_documents_every_label_it_uses() -> None:
    text = read_log()
    labels = proof_commands(text)
    for defect_id, entry in index_entries(text).items():
        label, command = entry_label_and_command(entry)
        assert label is not None, f"the entry of {defect_id} names no proof label"
        assert command == labels[label][0], (
            f"the command of {label} in the index is not the command of the proof block"
        )


def test_the_inline_command_matches_the_proof_block() -> None:
    """The command the index writes must be the command the block runs."""
    problems = section_index_problems(read_log())
    assert not problems, "; ".join(problems)


def test_a_drifted_inline_command_is_detected() -> None:
    broken = replace_inline_command(read_log(), "D-001", "bash scripts/install.sh --totally-wrong")
    problems = section_index_problems(broken)
    assert any("D-001" in problem for problem in problems), problems


def test_every_proof_label_is_used_by_a_defect() -> None:
    """A proof command that no defect cites is dead weight or a missing entry."""
    text = read_log()
    used: set[str] = set()
    for entry in index_entries(text).values():
        label, _ = entry_label_and_command(entry)
        if label:
            used.add(label)
    orphan = sorted(set(proof_commands(text)) - used)
    assert not orphan, f"proof commands that no defect cites: {orphan}"


def test_the_follow_up_list_exists_and_names_path_and_symptom() -> None:
    problems = follow_up_problems(read_log())
    assert not problems, "; ".join(problems)


def test_a_follow_up_without_a_symptom_is_detected() -> None:
    """The first follow-up item must keep its symptom when it is checked."""
    text = read_log()
    section = text[text.index(FOLLOW_UP_HEADING):]
    items = list(
        re.finditer(r"^\d+\. \*\*(.+?)\*\*(.*?)(?=^\d+\. \*\*|\Z)", section, re.MULTILINE | re.DOTALL)
    )
    first = items[0]
    shortened = section[: first.start()] + f"1. **{first.group(1)}**\n" + section[first.end():]
    broken = text.replace(section, shortened, 1)
    problems = follow_up_problems(broken)
    assert any("symptom" in problem for problem in problems), problems


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
        check=False,
        env={**os.environ, "TMPDIR": os.environ.get("TMPDIR", "/tmp")},
    )
    assert result.returncode == 0, (
        f"the proof command {label} failed with exit {result.returncode}:\n"
        f"$ {command}\n{result.stdout}\n{result.stderr}"
    )


def test_the_repair_log_does_not_claim_an_unrun_proof() -> None:
    """Every ``exit=`` line of the proof block must be 0."""
    text = read_log()
    block_text = proof_block(text)
    exits = re.findall(r"^exit=(\d+)$", block_text, re.MULTILINE)
    assert exits, "the proof block records no exit code"
    bad = [code for code in exits if code != "0"]
    assert not bad, f"the proof block records a failing command: exit={bad}"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
