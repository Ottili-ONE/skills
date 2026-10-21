# `scripts/validate.py` — interface contract

Job SKL-W1-01 (TASK-0003). Owner: `skills-engineering-r3` (`docs/R3_OWNERS.json`).
Written: 2026-10-16. Rewritten: 2026-10-20 against the measured behaviour.

Everything in this document was executed in this repository. The commands and
their output are quoted verbatim; nothing here is a claim about a tool that was
not run.

## Purpose

`validate.py` is the aggregate repository validator. It cross-checks the
generated `catalog.json` against the `skills/` folders on disk and reports
structural drift: unknown packages, skills whose `SKILL.md` frontmatter does not
match their catalogue entry, missing directories, missing descriptions,
duplicate ids or names.

It is the ONLY aggregate validator in the repository
(`docs/truth/REPO_SHAPE.md`, "Tools — exactly one each"). `validate_skill.py` and
`validate_skills.py` are the per-skill validators and are out of scope for this
contract.

## Invocation

```sh
python3 scripts/validate.py                       # default scope: catalogue only
python3 scripts/validate.py --json                 # machine-readable report
python3 scripts/validate.py --jsonl                # machine-readable report as JSON Lines
python3 scripts/validate.py --everywhere           # catalogue + whole skills/ tree
python3 scripts/validate.py --everywhere --json    # machine-readable, whole tree
python3 scripts/validate.py --everywhere --jsonl   # JSON Lines, whole tree
python3 scripts/validate.py --version              # the contract id, exit 0
python3 scripts/validate.py --help                 # usage text, exit 0
```

`--json` and `--jsonl` render the SAME report and are therefore mutually
exclusive: asking for both is a usage error, `error: argument --jsonl: not
allowed with argument --json`, exit 2, with no report on stdout. Letting one
flag win silently would print a format the caller did not ask for.

The tool is **standard library only** (`python3 -I` works, no package is
installed). It therefore runs on the CI runner before anything is installed,
and the contract tests can copy it into a throwaway fixture tree.

`--help` names the schema of each machine format, so a consumer that reads
only the usage text knows which file to validate against.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | No findings. |
| 1 | At least one finding (printed to stderr in human form, or in the report). |
| 2 | Usage error, or the catalogue is missing or unreadable. |

`--help` and `--version` exit 0 and print their text; they never exit 2.

## Default scope vs `--everywhere`

- **Default** (no flag): validates the generated `catalog.json` against itself.
  This is the CI contract — it proves the committed catalogue is internally
  consistent.
- **`--everywhere`**: additionally scans the WHOLE `skills/` tree on disk and
  cross-checks it against the catalogue. It reports a skill that exists on disk
  but is missing from the catalogue, and a catalogue entry whose `SKILL.md` does
  not exist on disk. This is the "is the catalogue in sync with the tree" check.

Both scopes exit 0 when there are no findings.

## Output formats

### Human (default)

On success, a single line on stdout:

```
ok: 39 skills validated
```

On failure, a header on stderr followed by one indented finding per line:

```
validation failed:
  - on-disk skill 'beta' (skills/demo/beta) is missing from the catalog
```

### JSON (`--json`)

One JSON object on stdout; the exit code reflects the findings.

```json
{
  "contract": "ottili.skills.validate-report/v1",
  "scope": "everywhere",
  "skills": 1,
  "errors": [
    "on-disk skill 'beta' (skills/demo/beta) is missing from the catalog"
  ],
  "ok": false
}
```

### JSON Lines (`--jsonl`)

One JSON object per line: a summary line, then one line per finding. A consumer
can read the stream without knowing the number of findings in advance.

```jsonl
{"contract": "ottili.skills.validate-report/v1", "kind": "summary", "scope": "everywhere", "skills": 1, "findings": 1, "ok": false}
{"contract": "ottili.skills.validate-report/v1", "kind": "finding", "scope": "everywhere", "message": "on-disk skill 'beta' (skills/demo/beta) is missing from the catalog"}
```

**CSV and parquet are not applicable.** The payload of this contract is a list
of free-text findings, not a table: a CSV export would have to invent columns
that the contract does not define, and a parquet export would have to invent a
schema. The two machine formats that ARE defined — one JSON object and JSON
Lines — cover the two real use cases (a single report and a stream).

### The JSON Lines format has a schema of its own

The JSON Lines stream is a second rendering of the same contract, and a line
has a different shape than the report (`kind`, and one finding per line).
A line therefore does NOT validate against the report schema — a consumer that
tried got `Additional properties are not allowed ('findings', 'kind' were
unexpected')`. The contract publishes a second schema for it:

| | |
| --- | --- |
| Lines schema | `scripts/ottili_contracts/schemas/ottili.skills.validate-report.v1.lines.schema.json` |
| Lines `$id` | `https://contracts.ottili.one/skills/validate-report/v1.lines.schema.json` |
| Typed view | `scripts/ottili_contracts/models.py` → `ValidateLine` (`ValidateSummaryLine` \| `ValidateFindingLine`) |
| Worked example | `scripts/ottili_contracts/examples/ottili.skills.validate-report.v1.lines.example.jsonl` |

The lines schema describes ONE line: a `oneOf` of the summary line and the
finding line, discriminated on `kind`. A consumer validates every line of the
stream against it; the contract test
`test_the_jsonl_export_validates_against_the_published_lines_schema` does
exactly that on the real output of the tool.

## The contract

| | |
| --- | --- |
| Contract id | `ottili.skills.validate-report/v1` |
| JSON Schema (the `--json` object) | `scripts/ottili_contracts/schemas/ottili.skills.validate-report.v1.schema.json` |
| JSON Schema (one `--jsonl` line) | `scripts/ottili_contracts/schemas/ottili.skills.validate-report.v1.lines.schema.json` |
| Typed view (pydantic) | `scripts/ottili_contracts/models.py` → `ValidateReport`, `ValidateLine` |
| Worked examples | `scripts/ottili_contracts/examples/ottili.skills.validate-report.v1.example.json`, `...v1.lines.example.jsonl` |
| Registry | `scripts/ottili_contracts/__init__.py` → `CONTRACTS` |

The JSON Schema is the normative artefact; the pydantic model is the typed view
of the same payload. The schema is **generated** from the model:

```sh
python3 scripts/ottili_contracts/generate.py
```

The contract test `tests/interfaces/test_validate_interface.py` asserts that the
committed schema is byte-identical with what the generator produces, so the two
cannot drift apart.

A change of the payload shape needs a new version, a new schema file and a new
entry in `CONTRACTS` — never an edit of a published schema. Within a version a
field may be added, a field may not change its meaning, and a field may not
disappear.

## Findings (machine-stable strings)

- `<id>: unknown package '<name>'`
- `<id>: path '<rel>' not under package path '<pkg>'`
- `<id>: directory missing: <rel>`
- `<id>: SKILL.md missing: <path>`
- `<id>: missing YAML frontmatter: <path>`
- `<id>: catalog name '<a>' != SKILL.md name '<b>'`
- `<id>: directory '<dir>' must match skill name '<name>'`
- `<id>: SKILL.md missing description in frontmatter`
- `duplicate catalog id: <id>`
- `duplicate skill name: <name>`
- `on-disk skill '<name>' (<rel>) is missing from the catalog` (`--everywhere` only)
- `catalog entry '<name>' has no SKILL.md on disk` (`--everywhere` only)

## Failure modes

- `catalog.json` absent → stderr `error: catalog not found at <path>`, exit 2.
- `catalog.json` not valid JSON → stderr `error: catalog is not readable: <path>: <reason>`,
  exit 2. No traceback: the tool reports, it does not raise.
- `catalog.json` is not a JSON object → same message, exit 2.
- A catalogue entry without a required field → stderr `error: catalog entry is
  missing a required field: <field>`, exit 2.
- Unknown flag → argparse usage error on stderr, exit 2.
- A skill directory exists but has no `SKILL.md` → that skill is skipped with a
  finding (exit 1).
- A `SKILL.md` exists but has no YAML frontmatter → finding, that skill is
  skipped (exit 1).

## Round-trip

- The JSON report round-trips through the typed view: `ValidateReport.model_validate(report)`
  succeeds and `model_dump()` returns the same mapping.
- The JSON Lines export round-trips into the JSON report: the finding lines
  carry the findings of the report in the same order, the summary line carries
  their number and the verdict. The reconstruction is tested against a fixture
  tree that really has a finding, so the round trip is not vacuous.
- Every line of the JSON Lines export validates against the lines schema and
  round-trips through the `ValidateLine` model unchanged.
- The report is deterministic: two runs on the same tree produce byte-identical
  output (the validator reads no clock, no network and no environment state).

## From a clean checkout

```sh
git clone <this repository> skills && cd skills
python3 scripts/validate.py --everywhere            # ok: 39 skills validated
python3 scripts/validate.py --everywhere --json     # the report of contract v1
python3 scripts/validate.py --everywhere --jsonl    # the same report as JSON Lines
python3 scripts/validate.py --help                  # the full usage text
```

Measured in this repository on 2026-10-20:

```
$ python3 scripts/validate.py --everywhere
ok: 39 skills validated
$ echo $?
0
```
