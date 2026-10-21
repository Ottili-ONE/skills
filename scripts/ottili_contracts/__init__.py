"""The versioned contracts of this repository's command line tools.

Every tool that publishes a machine-readable result owns a *contract*: a
versioned payload with a JSON Schema, a typed (pydantic) view and a worked
example. This package is the single registry of those contracts, so a
consumer has exactly one place to look for "what does this tool publish and
where is the schema?".

The JSON Schema is the normative artefact: it is plain JSON, needs no
dependency and can be read by any product. The pydantic models are the typed
view of the same payload for Python consumers.

Contracts are additive within a version: a field may be added, a field may not
change its meaning, and a field may not disappear. A change of the payload
shape needs a new version, a new schema file and a new entry in
:data:`CONTRACTS`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from .models import (
    CONTRACT_INSTALL_MANIFEST,
    CONTRACT_VALIDATE_REPORT,
    InstallAction,
    InstallEntry,
    InstallManifest,
    InstallMode,
    ValidateFindingLine,
    ValidateLine,
    ValidateLineInner,
    ValidateReport,
    ValidateScope,
    ValidateSummaryLine,
)

__all__ = [
    "CONTRACTS",
    "CONTRACT_INSTALL_MANIFEST",
    "CONTRACT_VALIDATE_REPORT",
    "EXAMPLE_DIR",
    "InstallAction",
    "InstallEntry",
    "InstallManifest",
    "InstallMode",
    "PACKAGE_DIR",
    "SCHEMA_DIR",
    "ValidateFindingLine",
    "ValidateLine",
    "ValidateLineInner",
    "ValidateReport",
    "ValidateScope",
    "ValidateSummaryLine",
    "example_path",
    "lines_example_path",
    "lines_model_for",
    "lines_schema_path",
    "load_example",
    "load_lines_example",
    "load_lines_schema",
    "load_schema",
    "model_for",
    "schema_path",
]

PACKAGE_DIR = Path(__file__).resolve().parent
SCHEMA_DIR = PACKAGE_DIR / "schemas"
EXAMPLE_DIR = PACKAGE_DIR / "examples"

#: Every contract of the repository: the contract id, the file names of its
#: schema and of its example, and the canonical ``$id`` of the schema.
#: Every contract of the repository: the contract id, the file names of its
#: schema(s) and of its example(s), and the canonical ``$id`` of each schema.
#:
#: A contract has ONE payload shape and therefore one schema. The validate
#: report is the exception: the same report is published twice — as one JSON
#: object and as a JSON Lines stream — and the lines have a different shape
#: (``kind`` plus one finding per line). A second schema file, the *lines*
#: schema, is therefore published next to the report schema. Without it the
#: published schema described only half of what the tool prints: a consumer
#: that validated a ``--jsonl`` line against the report schema failed on
#: ``additionalProperties``.
CONTRACTS: dict[str, dict[str, str]] = {
    CONTRACT_VALIDATE_REPORT: {
        "schema": "ottili.skills.validate-report.v1.schema.json",
        "example": "ottili.skills.validate-report.v1.example.json",
        "id": "https://contracts.ottili.one/skills/validate-report/v1.schema.json",
        "lines_schema": "ottili.skills.validate-report.v1.lines.schema.json",
        "lines_example": "ottili.skills.validate-report.v1.lines.example.jsonl",
        "lines_id": "https://contracts.ottili.one/skills/validate-report/v1.lines.schema.json",
    },
    CONTRACT_INSTALL_MANIFEST: {
        "schema": "ottili.skills.install-manifest.v1.schema.json",
        "example": "ottili.skills.install-manifest.v1.example.json",
        "id": "https://contracts.ottili.one/skills/install-manifest/v1.schema.json",
    },
}

#: The typed view of every contract.
_MODELS: dict[str, type[BaseModel]] = {
    CONTRACT_VALIDATE_REPORT: ValidateReport,
    CONTRACT_INSTALL_MANIFEST: InstallManifest,
}

#: The typed view of the JSON Lines rendering of a contract. Only a contract
#: that publishes a lines schema has an entry here.
_LINES_MODELS: dict[str, type[BaseModel]] = {
    CONTRACT_VALIDATE_REPORT: ValidateLine,
}


def _entry(contract_id: str) -> dict[str, str]:
    """Return the registry entry of one contract.

    Inputs:
        contract_id: the id of the contract, e.g. ``ottili.skills.validate-report/v1``.
    Outputs:
        the mapping with the keys ``schema``, ``example`` and ``id``.
    Failure modes:
        KeyError when the contract id is unknown. The caller never guesses:
        an unknown contract is a programming error, not a runtime condition.
    """
    return CONTRACTS[contract_id]


def schema_path(contract_id: str) -> Path:
    """Return the path of the JSON Schema of one contract.

    Inputs:
        contract_id: the id of the contract.
    Outputs:
        the path of the committed JSON Schema file. The file exists; the
        contract test asserts that it matches the typed view.
    Failure modes:
        KeyError when the contract id is unknown.
    """
    return SCHEMA_DIR / _entry(contract_id)["schema"]


def example_path(contract_id: str) -> Path:
    """Return the path of the worked example of one contract.

    Inputs:
        contract_id: the id of the contract.
    Outputs:
        the path of the committed example file.
    Failure modes:
        KeyError when the contract id is unknown.
    """
    return EXAMPLE_DIR / _entry(contract_id)["example"]


def load_schema(contract_id: str) -> dict[str, Any]:
    """Read the JSON Schema of one contract.

    Inputs:
        contract_id: the id of the contract.
    Outputs:
        the parsed JSON Schema as a mapping.
    Failure modes:
        KeyError when the contract id is unknown, OSError when the schema file
        is missing, json.JSONDecodeError when it is not valid JSON.
    """
    with schema_path(contract_id).open(encoding="utf-8") as handle:
        return json.load(handle)


def load_example(contract_id: str) -> dict[str, Any]:
    """Read the worked example of one contract.

    Inputs:
        contract_id: the id of the contract.
    Outputs:
        the parsed example as a mapping.
    Failure modes:
        KeyError when the contract id is unknown, OSError when the example file
        is missing, json.JSONDecodeError when it is not valid JSON.
    """
    with example_path(contract_id).open(encoding="utf-8") as handle:
        return json.load(handle)


def model_for(contract_id: str) -> type[BaseModel]:
    """Return the typed view of one contract.

    Inputs:
        contract_id: the id of the contract.
    Outputs:
        the pydantic model class of the contract.
    Failure modes:
        KeyError when the contract id is unknown.
    """
    return _MODELS[contract_id]


def lines_schema_path(contract_id: str) -> Path:
    """Return the path of the JSON Lines schema of one contract.

    Inputs:
        contract_id: the id of the contract.
    Outputs:
        the path of the committed lines schema. Every contract that publishes
        a JSON Lines export has one; the contract test asserts that the file
        matches the typed view.
    Failure modes:
        KeyError when the contract id is unknown or publishes no JSON Lines
        export.
    """
    return SCHEMA_DIR / _entry(contract_id)["lines_schema"]


def lines_example_path(contract_id: str) -> Path:
    """Return the path of the worked example of the JSON Lines export.

    Inputs:
        contract_id: the id of the contract.
    Outputs:
        the path of the committed ``.jsonl`` example file.
    Failure modes:
        KeyError when the contract id is unknown or publishes no JSON Lines
        export.
    """
    return EXAMPLE_DIR / _entry(contract_id)["lines_example"]


def load_lines_schema(contract_id: str) -> dict[str, Any]:
    """Read the JSON Lines schema of one contract.

    Inputs:
        contract_id: the id of the contract.
    Outputs:
        the parsed lines schema as a mapping. It describes ONE line: either
        the summary or one finding, discriminated on ``kind``.
    Failure modes:
        KeyError when the contract id is unknown or publishes no JSON Lines
        export, OSError when the file is missing, json.JSONDecodeError when it
        is not valid JSON.
    """
    with lines_schema_path(contract_id).open(encoding="utf-8") as handle:
        return json.load(handle)


def load_lines_example(contract_id: str) -> list[dict[str, Any]]:
    """Read the worked example of the JSON Lines export.

    Inputs:
        contract_id: the id of the contract.
    Outputs:
        the lines of the example as a list of mappings, in file order. The
        first line is the summary, every further line is one finding.
    Failure modes:
        KeyError when the contract id is unknown or publishes no JSON Lines
        export, OSError when the file is missing, json.JSONDecodeError when a
        line is not valid JSON.
    """
    with lines_example_path(contract_id).open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def lines_model_for(contract_id: str) -> type[BaseModel]:
    """Return the typed view of the JSON Lines rendering of one contract.

    Inputs:
        contract_id: the id of the contract.
    Outputs:
        the pydantic root model of one line of the export. ``model_validate``
        accepts one line, ``model_dump`` returns it unchanged.
    Failure modes:
        KeyError when the contract id is unknown or publishes no JSON Lines
        export.
    """
    return _LINES_MODELS[contract_id]
