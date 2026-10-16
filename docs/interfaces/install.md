# `scripts/install.sh` — interface contract

Job SKL-W1-01 (TASK-0003). Owner: `skills-engineering-r3` (`docs/R3_OWNERS.json`).
Written: 2026-10-16. Everything here is measured, not asserted.

## Purpose

`install.sh` copies (or links) selected Ottili ONE skill folders into an agent skills
directory. It is the ONLY installer in the repository
(`docs/truth/REPO_SHAPE.md`, "Tools — exactly one each").

A skill is a folder whose name is the skill's `name`, containing a `SKILL.md` with YAML
frontmatter. Copying the folder into the agent's skills directory is enough; the agent
discovers it on restart.

## Invocation

```sh
./scripts/install.sh --target <codex|claude|cursor|agents|/path> [options] <skill...>
```

### Options

| Option | Effect |
| --- | --- |
| `--target <name\|path>` | Agent skills directory (required). Named agents map to `$HOME` subdirs. |
| `--package <name>` | Install every skill in a package. |
| `--dry-run` | Print actions, write nothing, exit 0. |
| `--force` | Overwrite an existing destination folder. |
| `--link` | Create a symlink instead of copying. |
| `-h`, `--help` | Show help, exit 0. |

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
hand-maintained list and never read from `catalog.json`. A package is any top-level
folder under `skills/` that contains at least one subfolder with a `SKILL.md`.

| Package | Meaning |
| --- | --- |
| `<real>` | Every skill in `skills/<name>/`. |
| `generic` | Every skill in every package. |
| `meta`, `ref-*` | Reserved on-demand names; resolve to the empty set today. |

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | All requested skills installed (or skipped because they already existed). |
| 1 | A requested skill or package could not be resolved, or a source folder is missing its `SKILL.md`. |
| 2 | Usage error (missing `--target`, missing skill/package, unknown option). |

`--help` exits 0 and prints the usage text; it never exits 2.

## Behaviour contract

- **Idempotent.** Without `--force`, an existing destination folder is left untouched
  and the script prints `skip: <dest> already exists (use --force to overwrite)` and
  exits 0. Re-running an install is therefore a no-op for already-installed skills.
- **`--force`** removes and re-copies the destination.
- **`--link`** creates a symbolic link to the source folder instead of copying.
- **`--dry-run`** prints `dry-run: copy|link <src> -> <dest>` for every skill and
  writes nothing; exit 0.
- **Source resolution** searches the `skills/` tree rooted at the script's own
  directory, so the folder name alone is enough — no catalog lookup.
- **Order** is preserved and duplicates are deduplicated when a skill is named both
  explicitly and via `--package`.

## Output format

Human-readable text on stdout, one line per skill:

```
copied: /home/user/.codex/skills/honest-status
linked:  /home/user/.cursor/skills/pg-rls-multitenant -> /srv/ottili/repo/skills/skills/engineering/pg-rls-multitenant
skip:    /tmp/x/honest-status already exists (use --force to overwrite)
dry-run: copy  /srv/ottili/repo/skills/skills/engineering/honest-status  ->  /tmp/y/honest-status
```

Errors go to stderr and are followed by the usage text.

## Failure modes

- `--target` missing -> stderr `error: --target is required`, exit 2.
- No skill and no `--package` -> stderr `error: at least one skill name or --package is required`, exit 2.
- Unknown package -> stderr `error: unknown package '<name>'` + known packages, exit 1.
- Unknown skill name -> stderr `error: source skill directory missing: <root>/skills/*/<name>`, exit 1.
- Source folder without `SKILL.md` -> stderr `error: <src> has no SKILL.md`, exit 1.
- Unknown option -> stderr `error: unknown option <opt>` + usage, exit 2.
- `meta`/`ref-*` package -> stdout `note: package '<name>' resolves to no skills (reserved / on-demand)`, exit 0.

## Round-trip

`--dry-run` round-trips: the set of skills a real install would copy is exactly the
set `--dry-run` lists, in the same order, and a real install leaves a folder tree that
a subsequent `--dry-run` reports as `skip` for every skill.
