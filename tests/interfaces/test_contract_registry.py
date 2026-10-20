"""The registry and the committed contract files must describe the same set.

Job SKL-W1-01 (TASK-0003). The registry
(``scripts/ottili_contracts/__init__.py`` → ``CONTRACTS``) is the single place a
consumer looks up "what does this tool publish, and where is the schema?".

A file that lives in ``schemas/`` or ``examples/`` without an entry in the
registry is invisible: no test reads it, no document names it, and a consumer
that finds it cannot tell whether it is normative or a leftover. An entry whose
file is missing is worse — it is a broken promise.

These tests hold the two directories and the registry together:

* every registered schema and example exists and parses,
* no file lives in the two directories without a registry entry,
* the lines artefacts (the JSON Lines rendering of the validate report) are
  registered, so a rendering cannot be published without its schema.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from ottili_contracts import (  # noqa: E402
    CONTRACTS,
    EXAMPLE_DIR,
    SCHEMA_DIR,
    load_example,
    load_lines_example,
    load_lines_schema,
    load_schema,
)

SCHEMA_KEYS = ("schema", "lines_schema")
EXAMPLE_KEYS = ("example", "lines_example")


def registered(keys: tuple[str, ...]) -> set[str]:
    """The file names the registry publishes for the given keys.

    Inputs:
        keys: the registry keys to collect, e.g. ``("schema", "lines_schema")``.
    Outputs:
        the set of registered file names of those keys.
    Failure modes:
        none, a key a contract does not carry is skipped.
    """
    return {
        entry[key] for entry in CONTRACTS.values() for key in keys if key in entry
    }


def committed(directory: Path) -> set[str]:
    """The file names that are really committed in one contract directory.

    Inputs:
        directory: the schema or the example directory.
    Outputs:
        the set of file names, ignoring ``__pycache__`` and dot files.
    Failure modes:
        OSError when the directory cannot be listed.
    """
    return {
        path.name
        for path in directory.iterdir()
        if path.is_file() and not path.name.startswith(".")
    }


def test_every_registered_schema_is_committed() -> None:
    """A registry entry whose file is missing is a broken promise."""
    for name in registered(SCHEMA_KEYS):
        path = SCHEMA_DIR / name
        assert path.is_file(), f"the registry names {name}, which is not committed"
        schema = json.loads(path.read_text(encoding="utf-8"))
        assert schema.get("$id"), f"{name} carries no $id"
        assert schema.get("$schema", "").endswith("2020-12/schema"), f"{name} has no dialect"


def test_every_registered_example_is_committed() -> None:
    """A registry entry whose example is missing is a broken promise too."""
    for name in registered(EXAMPLE_KEYS):
        path = EXAMPLE_DIR / name
        assert path.is_file(), f"the registry names {name}, which is not committed"


def test_no_committed_schema_or_example_is_unregistered() -> None:
    """A contract file nobody registered is invisible to every consumer."""
    orphan_schemas = committed(SCHEMA_DIR) - registered(SCHEMA_KEYS)
    assert not orphan_schemas, (
        f"these schema files are committed but not registered: {sorted(orphan_schemas)}"
    )
    orphan_examples = committed(EXAMPLE_DIR) - registered(EXAMPLE_KEYS)
    assert not orphan_examples, (
        f"these examples are committed but not registered: {sorted(orphan_examples)}"
    )


def test_every_contract_loads_through_the_registry() -> None:
    """Every registered contract is readable through its own accessors."""
    for contract_id in sorted(CONTRACTS):
        schema = load_schema(contract_id)
        assert schema["$id"] == CONTRACTS[contract_id]["id"]
        if "lines_schema" in CONTRACTS[contract_id]:
            lines = load_lines_schema(contract_id)
            assert lines["$id"] == CONTRACTS[contract_id]["lines_id"]
            assert load_lines_example(contract_id), "the lines example is empty"
        assert load_example(contract_id), "the example is empty"
