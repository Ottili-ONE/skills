"""Typed view of the versioned contracts of this repository's command line tools.

Two tools publish a machine-readable result:

* ``scripts/validate.py`` publishes the *validate report* of the catalogue
  against the tree on disk, and
* ``scripts/install.sh`` publishes the *install manifest* of one install run.

Both contracts are versioned. The version lives in the contract id
(``ottili.skills.<name>/v1``) and in the file name of the JSON Schema
(``<contract id with the slash replaced by a dot>.schema.json``). A change of
the payload shape therefore needs a new version, a new schema file and a new
entry in :data:`CONTRACTS` — never an edit of the published one.

The JSON Schema is the normative artefact (it is dependency-free and every
consumer can read it). The pydantic models below are the typed view of the
same contract for Python consumers, and the contract tests assert that the two
never drift apart: the committed schema must equal ``model_json_schema()`` and
the real output of the tool must validate against both.
"""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, RootModel

#: The contract id of the report published by ``scripts/validate.py``.
CONTRACT_VALIDATE_REPORT = "ottili.skills.validate-report/v1"

#: The contract id of the manifest published by ``scripts/install.sh``.
CONTRACT_INSTALL_MANIFEST = "ottili.skills.install-manifest/v1"

#: The scopes ``scripts/validate.py`` can validate.
ValidateScope = Literal["catalog", "everywhere"]

#: The actions ``scripts/install.sh`` can report for a single skill.
InstallAction = Literal[
    "copied",
    "linked",
    "skipped",
    "would-copy",
    "would-link",
    "verified",
    "would-skip",
    "would-overwrite",
    "error",
]

#: The modes ``scripts/install.sh`` can run in.
InstallMode = Literal["install", "check", "dry-run"]


class ValidateReport(BaseModel):
    """The report ``scripts/validate.py --json`` publishes.

    Inputs:
        contract: the contract id, always ``ottili.skills.validate-report/v1``.
        scope: ``catalog`` (the committed catalogue) or ``everywhere`` (the
        catalogue plus the whole ``skills/`` tree).
        skills: the number of catalogue entries the report covers.
        errors: the findings, in the order they were found.
        ok: true when there is no finding at all.
    Outputs:
        the mapping that is printed as the JSON report. Unknown keys are
        rejected, so a producer that grows a field fails the contract test
        instead of silently changing the contract.
    Failure modes:
        ValidationError when a value does not match the contract (a wrong
        scope, a negative skill count, an unknown key).
    """

    model_config = ConfigDict(extra="forbid")

    contract: Literal["ottili.skills.validate-report/v1"]
    scope: ValidateScope
    skills: int = Field(ge=0)
    errors: list[str]
    ok: bool


class InstallEntry(BaseModel):
    """One skill of an install manifest.

    Inputs:
        name: the skill folder name.
        package: the package the skill was resolved from.
        source: the absolute path of the skill folder in the repository.
        destination: the absolute path the skill was written to (or would be
        written to).
        action: what happened to that skill.
        error: the reason of a failed resolution, ``None`` otherwise.
    Outputs:
        the mapping that is printed as one entry of the manifest.
    Failure modes:
        ValidationError when the action is not one of the documented values or
        when an unknown key is present.
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    package: str
    source: str
    destination: str
    action: InstallAction
    error: str | None = None


class InstallManifest(BaseModel):
    """The manifest ``scripts/install.sh --json`` publishes.

    Inputs:
        contract: the contract id, always ``ottili.skills.install-manifest/v1``.
        mode: ``install``, ``check`` or ``dry-run``.
        target: the directory the run was about.
        link: true when the run links instead of copies.
        ok: true when every requested skill was resolved.
        skills: one entry per requested skill, in the order of the request.
        error: the reason the run could not start, ``None`` otherwise.
    Outputs:
        the mapping that is printed as the JSON manifest.
    Failure modes:
        ValidationError when a value does not match the contract.
    """

    model_config = ConfigDict(extra="forbid")

    contract: Literal["ottili.skills.install-manifest/v1"]
    mode: InstallMode
    target: str
    link: bool
    ok: bool
    skills: list[InstallEntry]
    error: str | None = None


class ValidateSummaryLine(BaseModel):
    """The summary line of the JSON Lines export of the validate report.

    It is the FIRST line of ``scripts/validate.py --jsonl`` and it carries the
    verdict of the run: the number of skills the report covers and the number
    of findings. It is a second rendering of the same contract
    (``ottili.skills.validate-report/v1``), not a contract of its own.

    Inputs:
        contract: the contract id, always ``ottili.skills.validate-report/v1``.
        kind: always ``summary``; it discriminates the line against
        :class:`ValidateFindingLine`.
        scope: ``catalog`` or ``everywhere``.
        skills: the number of catalogue entries the report covers.
        findings: the number of findings of the report.
        ok: true when there is no finding at all.
    Outputs:
        the mapping that is printed as the first JSON Lines line.
    Failure modes:
        ValidationError when a value does not match (a wrong kind, a negative
        count, an unknown key).
    """

    model_config = ConfigDict(extra="forbid")

    contract: Literal["ottili.skills.validate-report/v1"]
    kind: Literal["summary"]
    scope: ValidateScope
    skills: int = Field(ge=0)
    findings: int = Field(ge=0)
    ok: bool


class ValidateFindingLine(BaseModel):
    """One finding line of the JSON Lines export of the validate report.

    Every line after the summary is one finding, in the order the findings
    were found. A consumer can therefore read the stream without knowing the
    number of findings in advance.

    Inputs:
        contract: the contract id, always ``ottili.skills.validate-report/v1``.
        kind: always ``finding``.
        scope: ``catalog`` or ``everywhere``.
        message: one finding, byte-identical with the entry of the ``errors``
        list of the JSON report.
    Outputs:
        the mapping that is printed as one JSON Lines line.
    Failure modes:
        ValidationError when a value does not match (a wrong kind, an unknown
        key).
    """

    model_config = ConfigDict(extra="forbid")

    contract: Literal["ottili.skills.validate-report/v1"]
    kind: Literal["finding"]
    scope: ValidateScope
    message: str


#: One line of the JSON Lines export of the validate report: either the
#: summary or one finding. The union is discriminated on ``kind``.
ValidateLineInner = Annotated[
    Union[ValidateSummaryLine, ValidateFindingLine], Field(discriminator="kind")
]


class ValidateLine(RootModel[ValidateLineInner]):
    """One line of the JSON Lines export of the validate report.

    Inputs:
        the root value: a :class:`ValidateSummaryLine` or a
        :class:`ValidateFindingLine` mapping.
    Outputs:
        ``model_validate`` returns the line; ``model_dump`` returns the
        mapping unchanged, so a consumer round-trips a line without losing a
        field.
    Failure modes:
        ValidationError when the ``kind`` is neither ``summary`` nor
        ``finding``, or when the mapping does not match the shape that
        ``kind`` names.
    """
