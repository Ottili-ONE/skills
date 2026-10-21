"""Write the JSON Schema files of the contracts from their typed view.

The schema is generated, never hand-edited: a hand-edited schema drifts from
the payload the tool actually prints, and the drift is invisible until a
consumer breaks.

Usage:

    python3 scripts/ottili_contracts/generate.py

It rewrites every schema file of ``scripts/ottili_contracts/schemas/`` — the
payload schema of every contract and the lines schema of every contract that
publishes a JSON Lines export — and prints the paths it wrote. The contract
test asserts that the committed files are byte-identical with what this script
produces, so a forgotten regeneration fails the suite.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in (None, ""):  # pragma: no cover - direct execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from ottili_contracts import (  # noqa: F401
        CONTRACTS,
        lines_model_for,
        lines_schema_path,
        model_for,
        schema_path,
    )
else:
    from . import (
        CONTRACTS,
        lines_model_for,
        lines_schema_path,
        model_for,
        schema_path,
    )


def render_schema(contract_id: str) -> str:
    """Render the JSON Schema of one contract.

    Inputs:
        contract_id: the id of the contract.
    Outputs:
        the schema as a pretty-printed JSON text with a trailing newline. The
        text is deterministic: the same model always renders the same bytes.
    Failure modes:
        KeyError when the contract id is unknown.
    """
    schema = model_for(contract_id).model_json_schema()
    schema["$id"] = CONTRACTS[contract_id]["id"]
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["title"] = contract_id
    return json.dumps(schema, indent=2, sort_keys=True) + "\n"


def render_lines_schema(contract_id: str) -> str:
    """Render the JSON Lines schema of one contract.

    A contract whose output is published as a JSON Lines stream (the validate
    report) owns a second schema: the report schema describes the single JSON
    object, the lines schema describes ONE LINE of the stream — the summary or
    one finding, discriminated on ``kind``.

    Inputs:
        contract_id: the id of a contract that publishes a JSON Lines export.
    Outputs:
        the schema as a pretty-printed JSON text with a trailing newline.
    Failure modes:
        KeyError when the contract id is unknown or publishes no JSON Lines
        export.
    """
    schema = lines_model_for(contract_id).model_json_schema()
    schema["$id"] = CONTRACTS[contract_id]["lines_id"]
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["title"] = f"{contract_id} (JSON Lines)"
    return json.dumps(schema, indent=2, sort_keys=True) + "\n"


def write_schemas() -> list[Path]:
    """Write every schema file of the registry.

    Every contract contributes its payload schema; a contract that also
    publishes a JSON Lines export contributes its lines schema as well.

    Inputs:
        none.
    Outputs:
        the list of the paths that were written, payload schemas first.
    Failure modes:
        OSError when a schema file cannot be written.
    """
    written: list[Path] = []
    for contract_id in sorted(CONTRACTS):
        path = schema_path(contract_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_schema(contract_id), encoding="utf-8")
        written.append(path)
    for contract_id in sorted(CONTRACTS):
        if "lines_schema" not in CONTRACTS[contract_id]:
            continue
        path = lines_schema_path(contract_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_lines_schema(contract_id), encoding="utf-8")
        written.append(path)
    return written


def main() -> int:
    """Write the schema files and report what was written.

    Inputs:
        none.
    Outputs:
        the process exit code, 0 on success.
    Failure modes:
        OSError when a schema file cannot be written; the traceback is
        printed by the interpreter and the exit code is non-zero.
    """
    for path in write_schemas():
        print(f"wrote: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
