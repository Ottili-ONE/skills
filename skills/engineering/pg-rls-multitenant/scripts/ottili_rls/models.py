"""The data model of the Ottili tenant convention.

Every boundary of the checker is a model: the configuration file, the facts a
migration states, the findings the rules produce and the measurements a leak
probe reports. The models are frozen, so a rule cannot change the facts it
was handed, and each model validates its own input.
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class GucStatus(str, Enum):
    """How a setting name relates to the canonical tenant GUC."""

    CANONICAL = "canonical"
    REJECTED = "rejected"
    NON_TENANT = "non_tenant"
    UNKNOWN = "unknown"


class FindingCode(str, Enum):
    """Stable machine codes of a finding.

    A caller branches on the code, a human reads the message. The meaning of a
    code never changes, so findings stay comparable across runs and versions.
    """

    MISSING_COMPANY_ID = "missing_company_id"
    NULLABLE_COMPANY_ID = "nullable_company_id"
    MISSING_ENABLE_RLS = "missing_enable_rls"
    MISSING_FORCE_RLS = "missing_force_rls"
    MISSING_TENANT_POLICY = "missing_tenant_policy"
    NON_CANONICAL_GUC = "non_canonical_guc"
    UNKNOWN_GUC = "unknown_guc"
    GRANT_ALL = "grant_all"


class GucName(BaseModel):
    """One setting name and its relation to the canonical tenant GUC."""

    model_config = ConfigDict(frozen=True)

    name: str
    status: GucStatus = GucStatus.REJECTED
    occurrences: int = Field(default=0, ge=0)
    why: str | None = None
    files_by_repository: dict[str, int] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def _is_qualified(cls, value: str) -> str:
        cleaned = value.strip()
        if "." not in cleaned:
            raise ValueError(f"{value!r} is not a qualified setting name")
        return cleaned


class TenantConvention(BaseModel):
    """The tenant convention every Ottili product repository follows.

    The convention is configuration (``guc-names.json``), not a constant of
    the checker. It names exactly one tenant GUC, the column that carries it
    and the names that are not tenant names. A configuration that describes
    more than one tenant GUC is not a configuration of this platform and is
    rejected instead of being half applied.
    """

    model_config = ConfigDict(frozen=True)

    schema_version: int = Field(default=1, ge=1)
    measured_at: str = ""
    canonical_name: str = ""
    canonical_column: str = "company_id"
    canonical_decision: str = ""
    accepted_names: tuple[str, ...] = ()
    rejected_names: tuple[GucName, ...] = ()
    known_non_tenant_names: tuple[GucName, ...] = ()
    census_command: str = ""
    census_scope: tuple[str, ...] = ()

    @model_validator(mode="before")
    @classmethod
    def _normalise(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        out = dict(data)
        names: list[str] = []
        raw_names = out.get("accepted_names")
        if isinstance(raw_names, list):
            for entry in raw_names:
                name = entry.get("name") if isinstance(entry, dict) else entry
                if isinstance(name, str) and name.strip():
                    names.append(name.strip())
        out["accepted_names"] = names
        if not out.get("canonical_name") and len(names) == 1:
            out["canonical_name"] = names[0]
        out["rejected_names"] = [
            _with_status(entry, GucStatus.REJECTED)
            for entry in out.get("rejected_names") or []
        ]
        out["known_non_tenant_names"] = [
            _with_status(entry, GucStatus.NON_TENANT)
            for entry in out.get("known_non_tenant_names") or []
        ]
        return out

    @model_validator(mode="after")
    def _is_one_convention(self) -> TenantConvention:
        if len(self.accepted_names) != 1:
            raise ValueError(
                "accepted_names must hold exactly one name (the canonical tenant GUC), "
                f"got {list(self.accepted_names)}"
            )
        if self.canonical_name != self.accepted_names[0]:
            raise ValueError(
                f"canonical_name {self.canonical_name!r} must be the accepted name "
                f"{self.accepted_names[0]!r}"
            )
        if not self.canonical_column.strip():
            raise ValueError("canonical_column must not be empty")
        return self


class TableFacts(BaseModel):
    """What a migration states about one table."""

    model_config = ConfigDict(frozen=True)

    name: str
    created_here: bool = False
    column_list: str = ""
    enabled_rls: bool = False
    forced_rls: bool = False
    policies: tuple[str, ...] = ()


class MigrationFacts(BaseModel):
    """What a migration states about its tables."""

    model_config = ConfigDict(frozen=True)

    tables: tuple[TableFacts, ...] = ()

    def table(self, name: str) -> TableFacts | None:
        """Return the facts of one table, or None when the file says nothing."""
        for entry in self.tables:
            if entry.name == name:
                return entry
        return None


class Finding(BaseModel):
    """One rule violation found in a migration."""

    model_config = ConfigDict(frozen=True)

    code: FindingCode
    message: str
    table: str | None = None

    def render(self) -> str:
        """Return the finding as one line of human-readable text."""
        return f"{self.table}: {self.message}" if self.table else self.message


class Measurement(BaseModel):
    """One number a leak probe reported."""

    model_config = ConfigDict(frozen=True)

    name: str
    value: int = Field(ge=0)


class LeakVerdict(BaseModel):
    """The judgement of a leak probe output."""

    model_config = ConfigDict(frozen=True)

    passed: bool
    findings: tuple[str, ...] = ()
    measurements: tuple[Measurement, ...] = ()


def _with_status(entry: Any, status: GucStatus) -> Any:
    """Return a setting-name entry that carries the given status."""
    if isinstance(entry, dict):
        merged = dict(entry)
        merged["status"] = status.value
        return merged
    if isinstance(entry, str):
        return {"name": entry, "status": status.value}
    return entry
