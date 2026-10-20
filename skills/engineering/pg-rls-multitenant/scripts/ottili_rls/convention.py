"""Reading the tenant convention from its configuration file.

The convention is configuration, not a constant of the checker: the file
``guc-names.json`` next to the skill holds the canonical tenant GUC, the
column that carries it, the names that are not canonical and the names that
are not tenant names at all. The checker reads that file, so a repository
that changes the convention changes one file, and a configuration that is not
one convention is an error instead of a silent second answer.
"""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from .models import GucStatus, TenantConvention


class ConventionError(Exception):
    """The tenant convention cannot be read, or is not one convention."""


def load_convention(path: Path) -> TenantConvention:
    """Read the tenant convention from ``path``.

    Raises:
        ConventionError: the file is missing, unreadable, not JSON, or does
            not describe exactly one canonical tenant GUC.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConventionError(f"cannot read {path}: {exc}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConventionError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ConventionError(f"{path} must hold a JSON object")
    try:
        return TenantConvention.model_validate(data)
    except ValidationError as exc:
        raise ConventionError(
            f"{path} does not describe one tenant convention: {exc}"
        ) from exc


def classify_guc(name: str, convention: TenantConvention) -> GucStatus:
    """Classify a setting name against the convention.

    The answer is one of four: the canonical tenant GUC, a tenant GUC name
    that the platform rejected, a name that carries something other than the
    tenant, or a name nobody knows.
    """
    cleaned = name.strip().lower()
    if not cleaned:
        return GucStatus.UNKNOWN
    if cleaned == convention.canonical_name.strip().lower():
        return GucStatus.CANONICAL
    for entry in convention.rejected_names:
        if entry.name.strip().lower() == cleaned:
            return GucStatus.REJECTED
    for entry in convention.known_non_tenant_names:
        if entry.name.strip().lower() == cleaned:
            return GucStatus.NON_TENANT
    return GucStatus.UNKNOWN
