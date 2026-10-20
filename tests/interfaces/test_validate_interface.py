"""Contract tests for ``scripts/validate.py`` (SKL-W1-01, TASK-0003).

``scripts/validate.py`` is the aggregate validator of the repository and it
publishes a machine-readable result: the versioned contract
``ottili.skills.validate-report/v1``.

What these tests hold:

* the interface is complete: ``--help`` names every flag, every exit code and
  the contract id, and ``--version`` prints the contract id,
* the published result matches the contract: the JSON report and the JSON
  Lines export validate against the committed JSON Schema and against the
  typed (pydantic) view, and the two views never drift apart,
* the output formats round-trip: the JSON Lines export rebuilds the JSON
  report, both machine formats validate against their published schema and
  two runs of the same tree produce the same bytes,
* the failure modes are the documented ones: a missing or broken catalogue is
  a usage error (exit 2) and a finding is a validation error (exit 1),
* every public function documents its inputs, its outputs and its failure
  modes.
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[2]
VALIDATE = ROOT / "scripts" / "validate.py"

if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from ottili_contracts import (  # noqa: E402
    CONTRACT_VALIDATE_REPORT,
    lines_example_path,
    lines_model_for,
    lines_schema_path,
    load_example,
    load_lines_example,
    load_lines_schema,
    load_schema,
    model_for,
    schema_path,
)
from ottili_contracts.generate import render_lines_schema, render_schema  # noqa: E402

SKILL_MD = """---
name: {name}
title: {name}
description: A demo skill used by the validator contract test.
version: 1.0.0
category: demo
license: MIT
author: test
---

# {name}

Body.
"""


def run_validator(
    *args: str, cwd: Path = ROOT, script: Path = VALIDATE
) -> subprocess.CompletedProcess[str]:
    """Run the validator and capture its output.

    Inputs:
        args: the command line arguments of the validator.
        cwd: the working directory of the run.
        script: the validator to run. The tool resolves the repository it
            validates from the location of its own file, so a fixture tree has
            to run its own copy of the script.
    Outputs:
        the completed process.
    Failure modes:
        none. A non-zero exit code is the tool's answer, not an error here.
    """
    return subprocess.run(
        ["python3", "-I", str(script), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def make_fixture_tree(tmp_path: Path) -> Path:
    """Build a throwaway repository with one catalogue and two skill folders.

    Inputs:
        tmp_path: the directory the fixture is built in.
    Outputs:
        the root of the fixture tree. It holds a copy of the validator, a
        catalogue with one entry and two skill folders (one of them unknown to
        the catalogue).
    Failure modes:
        OSError when the fixture cannot be written.
    """
    tree = tmp_path / "tree"
    (tree / "scripts").mkdir(parents=True)
    (tree / "skills" / "demo").mkdir(parents=True)
    (tree / "scripts" / "validate.py").write_text(
        VALIDATE.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (tree / "catalog.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "repository": "demo",
                "packages": {
                    "demo": {"label": "Demo", "description": "d", "path": "skills/demo"}
                },
                "skills": [
                    {
                        "id": "alpha",
                        "name": "alpha",
                        "title": "Alpha",
                        "package": "demo",
                        "path": "skills/demo/alpha",
                        "description": "d",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (tree / "skills" / "demo" / "alpha").mkdir()
    (tree / "skills" / "demo" / "alpha" / "SKILL.md").write_text(
        SKILL_MD.format(name="alpha"), encoding="utf-8"
    )
    (tree / "skills" / "demo" / "beta").mkdir()
    (tree / "skills" / "demo" / "beta" / "SKILL.md").write_text(
        SKILL_MD.format(name="beta"), encoding="utf-8"
    )
    return tree


def test_the_help_text_names_every_flag_and_exit_code() -> None:
    """--help is the contract of the command line: it must be complete."""
    result = run_validator("--help")
    assert result.returncode == 0, result.stdout + result.stderr
    for needle in (
        "--json",
        "--jsonl",
        "--everywhere",
        "--version",
        "exit codes:",
        "0  no findings",
        "1  at least one finding",
        "2  usage error",
        CONTRACT_VALIDATE_REPORT,
    ):
        assert needle in result.stdout, f"--help does not mention {needle!r}:\n{result.stdout}"


def test_the_version_prints_the_contract_id() -> None:
    """--version tells the consumer which contract the tool publishes."""
    result = run_validator("--version")
    assert result.returncode == 0
    assert CONTRACT_VALIDATE_REPORT in result.stdout


def test_the_json_report_matches_the_published_contract() -> None:
    """The JSON report validates against the schema and against the typed view."""
    result = run_validator("--everywhere", "--json")
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["contract"] == CONTRACT_VALIDATE_REPORT
    assert report["scope"] == "everywhere"
    assert report["ok"] is True
    assert report["errors"] == []
    jsonschema.validate(report, load_schema(CONTRACT_VALIDATE_REPORT))
    validated = model_for(CONTRACT_VALIDATE_REPORT).model_validate(report)
    assert validated.model_dump() == report


def test_the_jsonl_export_round_trips_into_the_json_report() -> None:
    """The JSON Lines export carries exactly the information of the report."""
    report = json.loads(run_validator("--everywhere", "--json").stdout)
    result = run_validator("--everywhere", "--jsonl")
    assert result.returncode == 0, result.stdout + result.stderr
    lines = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    assert lines, "the JSON Lines export is empty"
    summary, findings = lines[0], lines[1:]
    assert summary["kind"] == "summary"
    assert summary["contract"] == CONTRACT_VALIDATE_REPORT
    assert summary["findings"] == len(report["errors"])
    assert summary["ok"] == report["ok"]
    assert summary["skills"] == report["skills"]
    assert [line["message"] for line in findings] == report["errors"]
    assert all(line["kind"] == "finding" for line in findings)


def test_the_jsonl_export_rebuilds_the_json_report(tmp_path: Path) -> None:
    """The JSON Lines export is a rendering of the report, not a summary of it.

    A consumer that reads only the stream has to be able to reconstruct the
    report it carries — that is what makes the round trip a round trip. The
    fixture tree has a finding, so the stream really carries findings and the
    reconstruction is not vacuous.
    """
    tree = make_fixture_tree(tmp_path)
    fixture = tree / "scripts" / "validate.py"
    report = json.loads(run_validator("--everywhere", "--json", cwd=tree, script=fixture).stdout)
    assert report["errors"], "the fixture must have a finding"
    lines = [
        json.loads(line)
        for line in run_validator(
            "--everywhere", "--jsonl", cwd=tree, script=fixture
        ).stdout.splitlines()
        if line.strip()
    ]
    summary, findings = lines[0], lines[1:]
    rebuilt = {
        "contract": summary["contract"],
        "scope": summary["scope"],
        "skills": summary["skills"],
        "errors": [line["message"] for line in findings],
        "ok": summary["ok"],
    }
    assert rebuilt == report
    jsonschema.validate(rebuilt, load_schema(CONTRACT_VALIDATE_REPORT))
    # The summary counts the findings the stream carries, and every line
    # belongs to the scope and the contract of the report.
    assert summary["findings"] == len(findings)
    assert all(line["scope"] == report["scope"] for line in lines)
    assert all(line["contract"] == report["contract"] for line in lines)


def test_the_report_is_deterministic() -> None:
    """Two runs of the same tree produce the same bytes."""
    first = run_validator("--everywhere", "--json")
    second = run_validator("--everywhere", "--json")
    assert first.stdout == second.stdout
    assert first.returncode == second.returncode == 0


def test_a_finding_is_reported_in_every_output_format(tmp_path: Path) -> None:
    """A skill that the catalogue does not know is a finding, not a crash."""
    tree = make_fixture_tree(tmp_path)
    fixture = tree / "scripts" / "validate.py"
    human = run_validator("--everywhere", cwd=tree, script=fixture)
    assert human.returncode == 1, human.stdout + human.stderr
    assert "missing from the catalog" in human.stderr

    report = json.loads(
        run_validator("--everywhere", "--json", cwd=tree, script=fixture).stdout
    )
    assert report["ok"] is False
    assert any("missing from the catalog" in message for message in report["errors"])

    lines = [
        json.loads(line)
        for line in run_validator(
            "--everywhere", "--jsonl", cwd=tree, script=fixture
        ).stdout.splitlines()
        if line.strip()
    ]
    assert lines[0]["ok"] is False
    assert lines[0]["findings"] == len(report["errors"])
    assert any(
        "missing from the catalog" in line.get("message", "") for line in lines[1:]
    )


def test_a_missing_catalogue_is_a_usage_error(tmp_path: Path) -> None:
    """Without a catalogue the tool cannot run: exit 2, no traceback."""
    tree = tmp_path / "empty"
    (tree / "scripts").mkdir(parents=True)
    (tree / "scripts" / "validate.py").write_text(
        VALIDATE.read_text(encoding="utf-8"), encoding="utf-8"
    )
    result = run_validator("--everywhere", cwd=tree, script=tree / "scripts" / "validate.py")
    assert result.returncode == 2
    assert "catalog not found" in result.stderr
    assert "Traceback" not in result.stderr


def test_a_broken_catalogue_is_a_usage_error(tmp_path: Path) -> None:
    """A catalogue that is not valid JSON is reported, not raised."""
    tree = tmp_path / "broken"
    (tree / "scripts").mkdir(parents=True)
    (tree / "scripts" / "validate.py").write_text(
        VALIDATE.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (tree / "catalog.json").write_text("{not json", encoding="utf-8")
    result = run_validator("--everywhere", cwd=tree, script=tree / "scripts" / "validate.py")
    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert "error:" in result.stderr


def test_the_committed_schema_matches_the_typed_view() -> None:
    """The JSON Schema is generated from the model: the two cannot drift."""
    assert schema_path(CONTRACT_VALIDATE_REPORT).read_text(encoding="utf-8") == render_schema(
        CONTRACT_VALIDATE_REPORT
    )


def test_the_example_validates_against_the_contract() -> None:
    """The published example is a valid payload of the contract."""
    example = load_example(CONTRACT_VALIDATE_REPORT)
    jsonschema.validate(example, load_schema(CONTRACT_VALIDATE_REPORT))
    model_for(CONTRACT_VALIDATE_REPORT).model_validate(example)


def test_every_public_function_documents_its_contract() -> None:
    """Every public function states its inputs, its outputs and its failures."""
    for path in (
        VALIDATE,
        ROOT / "scripts" / "ottili_contracts" / "__init__.py",
        ROOT / "scripts" / "ottili_contracts" / "models.py",
        ROOT / "scripts" / "ottili_contracts" / "generate.py",
    ):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name.startswith("_"):
                continue
            docstring = ast.get_docstring(node) or ""
            assert docstring, f"{path.name}:{node.name} has no docstring"
            for marker in ("inputs", "outputs", "failure modes"):
                assert marker in docstring.lower(), (
                    f"{path.name}:{node.name} does not state its {marker}"
                )


def test_the_two_machine_formats_cannot_be_asked_for_at_once() -> None:
    """--json and --jsonl render the same report: asking for both is a usage error.

    Silently letting one flag win would print a format the caller did not
    ask for, so the two are mutually exclusive and the tool exits 2.
    """
    result = run_validator("--everywhere", "--json", "--jsonl")
    assert result.returncode == 2, result.stdout + result.stderr
    assert result.stdout == "", "a usage error prints no report at all"
    assert "not allowed with" in result.stderr


def test_a_catalogue_entry_without_a_name_is_a_usage_error(tmp_path: Path) -> None:
    """A broken entry is reported, never raised: no traceback, exit 2.

    The entry points at a folder that does not exist, so the catalogue
    validation returns before it reaches the name — the tree cross-check is
    then the first code that touches it. It used to raise a bare KeyError and
    print a traceback with exit 1.
    """
    tree = tmp_path / "nameless"
    (tree / "scripts").mkdir(parents=True)
    (tree / "scripts" / "validate.py").write_text(
        VALIDATE.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (tree / "catalog.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "repository": "demo",
                "packages": {
                    "demo": {"label": "d", "description": "d", "path": "skills/demo"}
                },
                "skills": [
                    {
                        "id": "alpha",
                        "package": "demo",
                        "path": "skills/demo/alpha",
                        "description": "d",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    result = run_validator(
        "--everywhere", cwd=tree, script=tree / "scripts" / "validate.py"
    )
    assert result.returncode == 2, result.stdout + result.stderr
    assert "Traceback" not in result.stderr
    assert "missing a required field" in result.stderr
    assert "'name'" in result.stderr


def test_the_jsonl_export_validates_against_the_published_lines_schema() -> None:
    """Every line of the JSON Lines export is a valid line of the contract.

    The report schema describes the single JSON object; the lines schema
    describes one line of the stream. Without it a consumer that validated a
    ``--jsonl`` line against the only published schema failed.
    """
    schema = load_lines_schema(CONTRACT_VALIDATE_REPORT)
    result = run_validator("--everywhere", "--jsonl")
    assert result.returncode == 0, result.stdout + result.stderr
    lines = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    assert lines, "the JSON Lines export is empty"
    for line in lines:
        jsonschema.validate(line, schema)
        assert lines_model_for(CONTRACT_VALIDATE_REPORT).model_validate(
            line
        ).model_dump() == line


def test_a_finding_line_is_a_valid_line_of_the_lines_schema(tmp_path: Path) -> None:
    """The lines schema covers the finding line, not only the summary."""
    tree = make_fixture_tree(tmp_path)
    result = run_validator(
        "--everywhere", "--jsonl", cwd=tree, script=tree / "scripts" / "validate.py"
    )
    assert result.returncode == 1, result.stdout + result.stderr
    lines = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    kinds = [line["kind"] for line in lines]
    assert kinds[0] == "summary"
    assert "finding" in kinds, "the fixture has a finding, so a finding line must exist"
    schema = load_lines_schema(CONTRACT_VALIDATE_REPORT)
    for line in lines:
        jsonschema.validate(line, schema)


def test_the_committed_lines_schema_matches_the_typed_view() -> None:
    """The lines schema is generated from its model: the two cannot drift."""
    assert lines_schema_path(CONTRACT_VALIDATE_REPORT).read_text(
        encoding="utf-8"
    ) == render_lines_schema(CONTRACT_VALIDATE_REPORT)


def test_the_lines_example_validates_against_the_lines_contract() -> None:
    """The published JSON Lines example is a valid payload of the contract."""
    schema = load_lines_schema(CONTRACT_VALIDATE_REPORT)
    example = load_lines_example(CONTRACT_VALIDATE_REPORT)
    assert example, "the JSON Lines example is empty"
    assert example[0]["kind"] == "summary"
    for line in example:
        jsonschema.validate(line, schema)
        lines_model_for(CONTRACT_VALIDATE_REPORT).model_validate(line)
    assert lines_example_path(CONTRACT_VALIDATE_REPORT).name.endswith(".jsonl")


def test_the_lines_schema_rejects_a_line_the_tool_never_prints() -> None:
    """The lines schema is a contract, not a rubber stamp."""
    schema = load_lines_schema(CONTRACT_VALIDATE_REPORT)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            {
                "contract": CONTRACT_VALIDATE_REPORT,
                "kind": "summary",
                "scope": "everywhere",
                "skills": 1,
                "ok": True,
            },
            schema,
        )
