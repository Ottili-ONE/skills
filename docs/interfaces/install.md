# `scripts/install.sh` — interface contract

Job SKL-W1-01 (TASK-0003). Owner: `skills-engineering-r3` (`docs/R3_OWNERS.json`).
Written: 2026-10-16. Rewritten: 2026-10-20 against the measured behaviour.

Everything in this document was executed in this repository. The commands and
their output are quoted verbatim; nothing here is a claim about a tool that was
not run.

## Purpose

`install.sh` copies (or links) selected Ottili ONE skill folders into an agent
skills directory. It is the ONLY installer in the repository
(`docs/truth/REPO_SHAPE.md`, "Tools — exactly one each").

A skill is a folder whose name is the skill's `name`, containing a `SKILL.md`
with YAML frontmatter. Copying the folder into the agent's skills directory is
enough; the agent discovers it on restart.

The script needs the repository layout: it sources the manifest library
`scripts/lib/install-manifest.sh` and refuses to run without it (exit 2, with a
readable message).

## Invocation

```sh
./scripts/install.sh --target <codex|claude|cursor|agents|/path> [options] <skill...>
```

### Options

| Option | Effect |
| --- | --- |
| `--target <name\|path>` | Agent skills directory (required). Named agents map to `$HOME` subdirs. |
| `--package <name>` | Install every skill in a package. |
| `--check` | Verify without writing. Without `--target` and without a selection it verifies the whole repository against a scratch directory that is never created. |
| `--dry-run` | Print actions, write nothing, exit 0. |
| `--force` | Overwrite an existing destination folder. |
| `--link` | Create a symlink instead of copying. |
| `--json` | Print the install manifest (one JSON object) instead of the human text. |
| `--version` | Print the contract id of the manifest, exit 0. |
| `-h`, `--help` | Print help, exit 0. |

### Named agents

| Name | Destination |
| --- | --- |
| `codex` | `$HOME/.codex/skills` |
| `claude` | `$HOME/.claude/skills` |
| `cursor` | `$HOME/.cursor/skills` |
| `agents` | `$HOME/.agents/skills` |
| any other value | treated as a literal directory path. |

## Packages

Packages are DERIVED from the `skills/` folders at install time — never a
hand-maintained list and never read from `catalog.json`. A package is any
top-level folder under `skills/` that contains at least one subfolder with a
`SKILL.md`.

| Package | Meaning |
| --- | --- |
| `<real>` | Every skill in `skills/<name>/`. |
| `generic` | Every skill in every package (39 in this tree). |
| `meta` | Reserved: accepted, ships nothing (there is no `skills/meta/` folder). |

**The `ref-*` folders are real packages, not reserved names.** `--package
ref-datev-extf` installs the skill of that folder. An earlier version of this
document (and of the README) claimed that `ref-*` resolved to no skills; that
was wrong, and the installer has always derived them from the tree. The name
is matched **literally** (`grep -qxF`), so `--package engineering+` is refused
as unknown.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Every requested skill was installed, linked, skipped or verified. |
| 1 | A skill or a package could not be resolved, or the target could not be created. |
| 2 | Usage error (missing `--target`, missing skill/package, unknown option, missing manifest library). |

`--help` and `--version` exit 0 and print their text; they never exit 2.

## Behaviour contract

- **Idempotent.** Without `--force`, an existing destination folder is left
  untouched and the script prints `skip: <dest> already exists (use --force to
  overwrite)` and exits 0. Re-running an install is therefore a no-op for
  already-installed skills.
- **`--force`** removes and re-copies the destination.
- **`--link`** creates a symbolic link to the source folder instead of copying.
- **`--dry-run`** prints `dry-run: copy|link <src> -> <dest>` for every skill
  and writes nothing; exit 0.
- **`--check`** resolves every skill, checks that the target is writable and
  writes nothing at all.
- **Source resolution** searches the `skills/` tree rooted at the script's own
  directory, so the folder name alone is enough — no catalogue lookup.
- **Order** is preserved and duplicates are deduplicated when a skill is named
  both explicitly and via `--package`.
- **Safety** a skill name is a plain folder name. A name that carries a path
  separator (`../pkg/skill`) would let the installer write — and with `--force`
  delete — outside the target; such a name is refused before anything is
  written (exit 2).

## Output formats

### Human (default)

One line per skill on stdout:

```
copied: /home/user/.codex/skills/honest-status
linked:  /home/user/.cursor/skills/pg-rls-multitenant -> /srv/ottili/repo/skills/skills/engineering/pg-rls-multitenant
skip:    /tmp/x/honest-status already exists (use --force to overwrite)
dry-run: copy  /srv/ottili/repo/skills/skills/engineering/honest-status  ->  /tmp/y/honest-status
```

Errors go to stderr. In `--check` mode the lines are `ok: <name> -> <dest>`,
`would skip: <dest> already exists (use --force to overwrite)` and
`would overwrite: <dest>`, followed by `check: N skill(s) verified, nothing
written` (or `check: FAILED` on stderr).

### JSON (`--json`)

**One JSON object on stdout and nothing else; stderr stays empty.** The object
is the install manifest of contract
`ottili.skills.install-manifest/v1`:

```json
{
  "contract": "ottili.skills.install-manifest/v1",
  "mode": "install",
  "target": "/home/user/.codex/skills",
  "link": false,
  "ok": true,
  "skills": [
    {
      "name": "honest-status",
      "package": "engineering",
      "source": "/srv/ottili/repo/skills/skills/engineering/honest-status",
      "destination": "/home/user/.codex/skills/honest-status",
      "action": "copied",
      "error": null
    }
  ],
  "error": null
}
```

| Field | Meaning |
| --- | --- |
| `contract` | The contract id, always `ottili.skills.install-manifest/v1`. |
| `mode` | `install`, `check` or `dry-run`. |
| `target` | The directory the run was about. |
| `link` | True when the run links instead of copying. |
| `ok` | The verdict of the whole run: false when a skill could not be resolved or the run could not start. |
| `skills` | One entry per requested skill, in the order of the request. |
| `error` | The reason the run could not start, `null` otherwise. |

| `action` | Meaning |
| --- | --- |
| `copied` | The folder was copied to the destination. |
| `linked` | The destination is a symlink to the source. |
| `skipped` | The destination existed and `--force` was not given. |
| `would-copy` / `would-link` | `--dry-run`: what would have happened. |
| `verified` | `--check`: the source resolves and the destination is free. |
| `would-skip` / `would-overwrite` | `--check`: what an install would do to an existing destination. |
| `error` | The skill could not be resolved; the reason is in the entry's `error` field. |

In `--json` mode every message of the human mode is carried by the manifest:
the reason of a run that could not start in `error`, the reason of a skill that
could not be resolved in the entry's `error`.

**CSV and parquet are not applicable.** The manifest is a nested payload (one
entry per skill, each with a path and an enumeration), not a table. A CSV
export would flatten it into a lossy row per skill; the JSON object is the
contract, and a consumer that needs rows reads `skills[]` and projects it.

## The contract

| | |
| --- | --- |
| Contract id | `ottili.skills.install-manifest/v1` |
| JSON Schema | `scripts/ottili_contracts/schemas/ottili.skills.install-manifest.v1.schema.json` |
| Typed view (pydantic) | `scripts/ottili_contracts/models.py` → `InstallManifest`, `InstallEntry` |
| Worked example | `scripts/ottili_contracts/examples/ottili.skills.install-manifest.v1.example.json` |
| Registry | `scripts/ottili_contracts/__init__.py` → `CONTRACTS` |

The JSON Schema is the normative artefact and is **generated** from the model:

```sh
python3 scripts/ottili_contracts/generate.py
```

The contract test `tests/interfaces/test_install_interface.py` asserts that the
committed schema is byte-identical with what the generator produces.

## Failure modes

- `--target` missing → stderr `error: --target is required` + usage, exit 2.
- No skill and no `--package` → stderr `error: at least one skill name or
  --package is required` + usage, exit 2.
- Unknown package → stderr `error: unknown package '<name>'` + the known
  packages, exit 1.
- Unknown skill name → stderr `error: source skill directory missing:
  <root>/skills/*/<name>`, exit 1.
- Source folder without `SKILL.md` → stderr `error: <src> has no SKILL.md`,
  exit 1.
- A skill name that exists in two packages → `error: skill '<name>' is
  ambiguous, found in packages: <packages>`, exit 1.
- Unknown option → stderr `error: unknown option <opt>` + usage, exit 2.
- A skill name that is not a plain folder name → `error: invalid skill name
  '<name>'`, exit 2.
- The target cannot be created → `error: target '<target>' cannot be created`,
  exit 1.
- The manifest library is missing → `error: <path>/install-manifest.sh is
  missing; the installer needs the repository layout`, exit 2.
- `meta` package → stdout `note: package 'meta' is reserved and ships no skills
  in this tree`, exit 0.

## Round-trip

- The manifest round-trips through the typed view:
  `InstallManifest.model_validate(manifest)` succeeds and `model_dump()`
  returns the same mapping.
- The manifest describes what really happened: the `skills` entries name the
  folders of the target directory, one for one, and the `action` of each entry
  matches the state of the destination.
- `--dry-run` round-trips: the set of skills a real install would copy is
  exactly the set `--dry-run` lists, in the same order, and a real install
  leaves a folder tree that a subsequent run reports as `skipped` for every
  skill.

## From a clean checkout

```sh
git clone <this repository> skills && cd skills
./scripts/install.sh --target "$(mktemp -d)" --package engineering
./scripts/install.sh --target "$(mktemp -d)" --package engineering --json
./scripts/install.sh --check
./scripts/install.sh --help
```

Measured in this repository on 2026-10-20:

```
$ ./scripts/install.sh --target "$(mktemp -d)" --package engineering
copied: /tmp/tmp.VtlIJDhmID/acceptance-harness
copied: /tmp/tmp.VtlIJDhmID/foundation-v2-conformance
copied: /tmp/tmp.VtlIJDhmID/honest-status
copied: /tmp/tmp.VtlIJDhmID/long-test-discipline
copied: /tmp/tmp.VtlIJDhmID/module-contract-first
copied: /tmp/tmp.VtlIJDhmID/outbox-idempotency
copied: /tmp/tmp.VtlIJDhmID/pg-rls-multitenant
copied: /tmp/tmp.VtlIJDhmID/playwright-a11y-e2e
copied: /tmp/tmp.VtlIJDhmID/problem-json-contracts
copied: /tmp/tmp.VtlIJDhmID/shared-tree-git
$ echo $?
0
```
