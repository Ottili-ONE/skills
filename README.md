# Ottili ONE Skills

> ⚠️ **Important Note:** These capabilities and skills were developed within a fully automated, blind, and zero-Human-In-The-Loop (no-HITL) multi-agent system. Consequently, they may contain bugs, edge cases, or features that do not function as intended in all environments.


A repository of **Agent Skills** — folders of instructions, scripts and references that an
AI agent discovers and applies to a specific task — together with the tooling that
validates, indexes, catalogues and installs them.

A skill is a folder that contains a `SKILL.md` with YAML frontmatter:

```yaml
---
name: honest-status
description: Use when writing a status report that claims something works.
---
```

The frontmatter must be followed by the skill body; optional `references/`, `scripts/`,
`tests/` and `config/` subfolders carry supporting material. The format follows the open
Agent Skill standard at [agentskills.io](https://agentskills.io/specification).

This repository holds **39 skills** in 12 packages, the generated `catalog.json` that
describes them, the tools that work with them, and the ten engineering playbooks
(`skills/engineering/**`) that Ottili agents use to build reliable software.

## Repository layout

```
skills/
├── agentic-data/          # 10 data-plane agent skills (browsing, research, MCP, LLM judges, …)
├── business-de/           # 10 German business-domain skills (DATEV, XRechnung/ZUGFeRD, GoBD, …)
├── core/                  # team-maintained official skills
├── curated/               # vetted third-party skills
├── community/             # placeholder for community contributions (no skills yet)
├── ottili-ai/             # placeholder for Ottili AI runtime skills (no skills yet)
├── engineering/           # 10 engineering playbooks + checkers, self-tests and docs
├── orchestrator-preamble/ # the generated orchestrator preamble (1 skill)
└── ref-<subject>/         # 6 reference skills, one per business-de subject
scripts/                   # install, validate, generate, index
schema/catalog.schema.json # JSON Schema for catalog.json
templates/skill/SKILL.md   # starting point for a new skill
catalog.json               # GENERATED catalogue of every skill (39 entries)
index/                     # GENERATED index/INDEX.md and index/skills.json
docs/                      # interfaces/, truth/, gaps/, reviews/, R3_OWNERS.json
tests/                     # repository-level test suites (hygiene, orchestrator, reviews)
.github/workflows/         # CI: validate.yml
```

Packages are **derived from the folders** under `skills/` at generation time — there is no
hand-maintained package or skill list anywhere in the tooling.

## Requirements

- `bash`, `git`
- `python3` (CI runs 3.12)
- `node` (the generators and the Node test suites)
- optional: `pip install pyyaml` (required by the problem+json catalogue checker),
  `pip install pytest` for the pytest-style suites

## Install the repository

There is no build step and no package manifest — the repository is Markdown, Python and
Node scripts.

```sh
git clone https://github.com/Ottili-ONE/skills.git
cd skills
```

## Install skills into an agent

Each agent reads skills from its own directory. The convention is the same everywhere: a
skill is a folder named after the skill's `name` containing a `SKILL.md` with YAML
frontmatter. Copy (or symlink) the folder into the agent's skills directory and restart
the agent.

`scripts/install.sh` does this for you.

```sh
# Dry-run first: prints every action, writes nothing, exits 0.
./scripts/install.sh --target codex --dry-run pg-rls-multitenant

# Install (copies the skill folder into ~/.codex/skills/).
./scripts/install.sh --target codex pg-rls-multitenant

# Replace an existing installation.
./scripts/install.sh --target claude --force honest-status

# Symlink instead of copy.
./scripts/install.sh --target cursor --link shared-tree-git

# Install every skill of a package.
./scripts/install.sh --target cursor --package engineering
```

| Option | Effect |
| --- | --- |
| `--target <name\|path>` | Required. Named agent, or a literal directory path. |
| `--package <name>` | Install every skill in a package. |
| `--dry-run` | Print the actions, write nothing, exit 0. |
| `--force` | Remove and re-copy an existing destination folder. |
| `--link` | Create a symlink instead of copying. |
| `-h`, `--help` | Print help, exit 0. |

| `--target` | Destination |
| --- | --- |
| `codex` | `$HOME/.codex/skills` |
| `claude` | `$HOME/.claude/skills` |
| `cursor` | `$HOME/.cursor/skills` |
| `agents` | `$HOME/.agents/skills` |
| any other value | treated as a literal directory path |

Behaviour:

- **Idempotent** — without `--force` an existing destination folder is left untouched and
  the script prints `skip: … already exists (use --force to overwrite)` and exits 0.
- **Source resolution** — a skill is located by its folder name alone, searched in the
  `skills/` tree next to the script; no catalogue lookup is involved.
- **Packages** — derived at install time from the folders. `generic` installs every skill
  in the repository (39); `meta` and any package name starting with `ref-` are reserved
  on-demand names that resolve to no skills, so the six `ref-*` skills have to be
  installed by name.
- **Exit codes** — `0` all requested skills installed or skipped, `1` a skill or package
  could not be resolved, `2` usage error (missing `--target`, missing skill/package,
  unknown option).

The full contract lives in [`docs/interfaces/install.md`](docs/interfaces/install.md).

### Where agents look for skills

Directory conventions verified against the vendor documentation (retrieved 2026-10-07):

- **Claude Code** — `~/.claude/skills/<name>/SKILL.md`; skills are auto-discovered from
  the skills directory. <https://docs.anthropic.com/en/docs/claude-code/skills>
- **Codex (OpenAI)** — `$CODEX_HOME/skills/<name>/SKILL.md`, typically `~/.codex/skills/`.
  <https://github.com/openai/skills>
- **Cursor** — `~/.cursor/skills/<name>/SKILL.md` (a project-scoped `.cursor/skills/`
  also works). <https://docs.cursor.com/agent/skills>
- **Generic agent runtimes** — `~/.agents/skills/<name>/SKILL.md`, or any directory the
  runtime announces; the folder + `SKILL.md` layout is identical.

`https://github.com/anthropics/skills` ships reusable skill folders in exactly this
layout and is a useful reference for what a well-formed skill looks like.

## Browse and install from the catalogue

`catalog.json` is **generated**, never hand-edited: `scripts/gen-catalog.mjs` walks every
`skills/<package>/<name>/SKILL.md`, reads the frontmatter and writes one entry per skill.
Packages are derived from the `skills/` folders at generation time.

```sh
node scripts/gen-catalog.mjs            # regenerate catalog.json
node scripts/gen-catalog.mjs --check    # exit 1 if the committed catalog would change
```

Two catalogue-driven helpers sit next to it:

```sh
python3 scripts/list-skills.py                       # grouped by package
python3 scripts/list-skills.py --package business-de --format json
python3 scripts/list-skills.py --target codex        # marks already-installed skills
python3 scripts/install-skill.py --list              # list installable skills
python3 scripts/install-skill.py honest-status --target claude
```

`install-skill.py` resolves a skill by name or id in `catalog.json` and copies it into
the target directory (`--dest` overrides the target path, `--force` overwrites an
existing folder). `scripts/install.sh` is the primary installer; both use the same
`codex` / `claude` / `cursor` / `agents` target names.

`index/INDEX.md` (human-readable) and `index/skills.json` (machine-readable) are
generated from the same tree:

```sh
python3 scripts/build-index.py
```

## Validate

| Tool | What it checks |
| --- | --- |
| `scripts/validate.py` | Aggregate validator: `catalog.json` against the `skills/` tree — unknown packages, missing directories, frontmatter/catalog mismatches, duplicate ids or names. |
| `scripts/validate_skill.py` | One skill folder against the agentskills.io standard. |
| `scripts/validate_skills.py` | All ten engineering skills at once: portable frontmatter fields, `references/EVALS.md` with ≥5 prompts, `references/SOURCES.md`, offline-runnable helper scripts. |
| `scripts/validate_reviewed_by.py` | Sign-off gate: a skill with `reviewed_by:` may only be certified when `docs/reviews/<skill>.md` carries a filled reviewer/date/signature block. |
| `scripts/check_related_graph.py` | The `Related` graph of the engineering playbooks is acyclic and every link resolves. |
| `scripts/verify-status.mjs` | A `STATUS.md` claim table: every row needs a claim, a command and an existing log path. |

```sh
python3 scripts/validate.py                       # catalogue vs. tree (exit 0 = clean)
python3 scripts/validate.py --json                # machine-readable report
python3 scripts/validate.py --everywhere          # also scan the whole skills/ tree
python3 scripts/validate_skill.py --all           # the ten engineering skills
python3 scripts/validate_skill.py --everywhere     # every skill in the repository
python3 scripts/validate_skill.py <skill-dir>...   # explicit paths
```

`validate_skill.py` needs one of `--all` (the engineering tree), `--everywhere` (the
whole repository) or explicit paths; called with no arguments it prints its usage and
exits 2. Its rules are: `name` present, ≤64 characters, lowercase-hyphenated and equal
to the folder name; `description` present, ≤1024 characters and stating when to use the
skill; `compatibility` ≤500 characters; `SKILL.md` ≤500 lines; and every relative link in
the body resolving to an existing file (anchors included).

The validator contracts are documented in
[`docs/interfaces/validate.md`](docs/interfaces/validate.md) and
[`docs/interfaces/install.md`](docs/interfaces/install.md).

## Run the tests

CI (`.github/workflows/validate.yml`) runs on every push and pull request to `main` and
executes, in order:

1. `python3 scripts/validate.py`
2. `node scripts/gen-catalog.mjs --check`
3. `python3 scripts/list-skills.py --format json` (smoke test)
4. `python3 scripts/validate_skill.py --all`
5. `pip install jsonschema`
6. `node scripts/gen-preamble.mjs --check`
7. the orchestrator contract tests, `tests/orchestrator/*.test.mjs`
8. the engineering skill self-tests (see the table below)

The same checks run locally:

```sh
# Node suites (node:test — no test runner to install).
for t in tests/orchestrator/*.test.mjs; do node "$t" || exit 1; done
for t in tests/hygiene/*.test.mjs tests/reviews/*.test.mjs; do node "$t" || exit 1; done

# Python suites.
python3 -m pytest tests skills/engineering/tests

# Engineering skill self-tests.
for t in skills/engineering/*/scripts/*_test.py; do python3 "$t" || exit 1; done
bash skills/engineering/long-test-discipline/scripts/run_long_test_test.sh
bash skills/engineering/foundation-v2-conformance/scripts/fresh_consumer_test.sh
```

`tests/hygiene/` guards repository hygiene (no large files, no database files, no bad
symlinks, scoped npm registry, clean tree), `tests/orchestrator/` covers the preamble
generator (golden file, reproducibility, property and contract tests) and
`tests/reviews/` covers the sign-off gate.

## Engineering playbooks

`skills/engineering/` holds ten playbooks for coding and operations agents, each with an
offline, deterministic checker and a self-test:

| Skill | Checker | Self-test |
|-------|---------|-----------|
| `acceptance-harness` | `check_audit_selectors.py`, `report_result.py` | `check_audit_selectors_test.py`, `report_result_test.py` |
| `foundation-v2-conformance` | `check_foundation_tokens.py` | `check_foundation_tokens_test.py`, `fresh_consumer_test.sh` |
| `honest-status` | `check_status_evidence.py` | `check_status_evidence_test.py` |
| `long-test-discipline` | `run_long_test.sh` | `run_long_test_test.sh` |
| `module-contract-first` | `check_contract_drift.py` | `check_contract_drift_test.py` |
| `outbox-idempotency` | `check_outbox.py` | `check_outbox_test.py` |
| `pg-rls-multitenant` | `check_rls_migration.py` | `check_rls_migration_test.py` |
| `playwright-a11y-e2e` | `check_axe_evidence.py`, `check_keyboard.py`, `check_workaround_markers.py` | `check_axe_evidence_test.py`, `check_workaround_markers_test.py` |
| `problem-json-contracts` | `check_problem_catalogue.py`, `validate_problem_examples.py` | `check_problem_catalogue_test.py`, `validate_problem_examples_test.py` |
| `shared-tree-git` | `check_shared_tree.py` | `check_shared_tree_test.py` |

Repository-level tests for the engineering tree live in `skills/engineering/tests/`
(`test_collection_acceptance.py`, `test_evals_completeness.py`,
`test_research_design_acceptance.py`, `test_sources_freshness.py`). The playbooks
themselves are documented in [`skills/engineering/README.md`](skills/engineering/README.md).

## Orchestrator preamble

`skills/orchestrator-preamble/orchestrator-preamble/` is the ≤60-line rules block that
every GERMO job loads as the first part of its base prompt. It is **generated** from the
four canonical engineering skills (`pg-rls-multitenant`, `outbox-idempotency`,
`problem-json-contracts`, `honest-status`) and must never be hand-edited:

```sh
node scripts/gen-preamble.mjs          # regenerate the body
node scripts/gen-preamble.mjs --check  # exit 1 if the committed body is stale
```

The generator is deterministic: the same skills on disk always produce the same bytes.
The skill's own `SKILL.md` is the human-readable contract.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the skill conventions and the review
criteria, and [`AGENTS.md`](AGENTS.md) for the live working directives and the path
ownership map (`docs/R3_OWNERS.json`).

New skills start from `templates/skill/SKILL.md`. The catalogue is generated, so adding
or renaming a skill means running `node scripts/gen-catalog.mjs` (and
`python3 scripts/build-index.py`) instead of editing `catalog.json` by hand. Before
committing, run `python3 scripts/validate.py` and `python3 scripts/validate_skill.py --all`.

## License

MIT, see [`LICENSE`](LICENSE).
