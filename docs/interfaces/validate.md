# `scripts/validate.py` — interface contract

Job SKL-W1-01 (TASK-0003). Owner: `skills-engineering-r3` (`docs/R3_OWNERS.json`).
Written: 2026-10-16. Everything here is measured, not asserted.

## Purpose

`validate.py` is the aggregate repository validator. It cross-checks the generated
`catalog.json` against the `skills/` folders on disk and reports structural drift:
unknown packages, skills whose `SKILL.md` frontmatter does not match their catalog
entry, missing directories, missing descriptions, duplicate ids or names.

It is the ONLY aggregate validator in the repository
(`docs/truth/REPO_SHAPE.md`, "Tools — exactly one each"). `validate_skill.py` and
`validate_skills.py` are the per-skill validators and are out of scope for this contract.

## Invocation

```sh
python3 scripts/validate.py                       # default scope: catalog only
python3 scripts/validate.py --json                 # machine-readable report
python3 scripts/validate.py --everywhere           # catalog + whole skills/ tree
python3 scripts/validate.py --everywhere --json    # machine-readable, whole tree
python3 scripts/validate.py --help                 # usage text, exit 0
```

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | No findings. |
| 1 | At least one finding (printed to stderr in human form, or in the JSON `errors` array). |
| 2 | Usage error (unknown flag, missing catalog file). |

`--help` exits 0 and prints the usage text; it never exits 2.

## Default scope vs `--everywhere`

- **Default** (no flag): validates the generated `catalog.json` against itself. This is
  the CI contract — it proves the committed catalog is internally consistent.
- **`--everywhere`**: additionally scans the WHOLE `skills/` tree on disk and
  cross-checks it against the catalog. It reports a skill that exists on disk but is
  missing from the catalog, and a catalog entry whose `SKILL.md` does not exist on disk.
  This is the "is the catalogue in sync with the tree" check; it is NOT run by CI
  (the catalogue is generated, so the two cannot drift in CI) but is the human-facing
  contract a maintainer runs by hand.

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
  - on-disk skill 'pg-rls-multitenant' (skills/engineering/pg-rls-multitenant) is missing from the catalog
```

### JSON (`--json`)

A single JSON object on stdout, exit code reflecting findings:

```json
{
  "skills": 39,
  "errors": [],
  "ok": true
}
```

`errors` is an array of strings, empty when `ok` is true. `skills` is the number of
catalog entries. The JSON report is IDENTICAL between the default and `--everywhere`
scopes when the tree is in sync; the only difference is what `errors` may contain.

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

- `catalog.json` absent -> stderr `error: catalog not found at <path>`, exit 2.
- Unknown flag -> argparse usage error on stderr, exit 2.
- A skill directory exists but has no `SKILL.md` -> that skill is skipped with a finding.
- A `SKILL.md` exists but has no YAML frontmatter -> finding, that skill is skipped.
- The catalog is empty or malformed JSON -> `json.load` raises, non-zero exit.

## Round-trip

The JSON report round-trips: `python3 scripts/validate.py --json` on a clean tree
produces `{"skills": N, "errors": [], "ok": true}` and re-running it on the same tree
produces byte-identical output (the validator is deterministic; it reads no clock,
network or environment state).
