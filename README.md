# Ottili ONE Skills

Agent Skills for Claude Code, Codex, Cursor, OpenClaw, Ottili AI and Ottili Coder.

Skills are folders of instructions, scripts, and resources that AI agents discover and apply to
specific tasks. This repository is the single source of truth for those skills: it hosts the
skill folders, the catalog that describes them, the tooling that validates and installs them,
and the engineering playbooks (`skills/engineering/**`) that Ottili agents use to build reliable
software.

## Repository layout

```
skills/
├── core/                 # Official Ottili ONE skills
├── curated/              # Vetted third-party skills
├── community/            # Community-contributed skills (review before production use)
├── ottili-ai/            # Skills for Ottili AI runtime and Ottili Velo agents
├── business-de/          # German business-domain skills (DATEV, XRechnung/ZUGFeRD, GoBD)
├── agentic-data/         # Data-plane agent skills
└── engineering/          # Engineering playbooks (this job's output)
scripts/                  # validate.py, validate_skill.py, install.sh, build-index.py, helpers
schema/                   # catalog.schema.json
templates/skill/          # SKILL.md template for new skills
catalog.json              # Machine-readable catalog of every skill
index/                    # Generated index/INDEX.md and index/skills.json
docs/                     # Ownership, requests, status
```

## Installing skills into an agent

Each agent looks for skills in its own directory. The convention for every tool below is: a skill
is a folder whose name is the skill's `name`, containing a `SKILL.md` with YAML frontmatter.
Copying (or symlinking) the folder into the agent's skills directory is enough; restart the
agent to load it.

Verified skill-directory conventions (retrieved 2026-10-07):

- **Claude Code** — `~/.claude/skills/<name>/SKILL.md`. Skills are auto-discovered from the
  skills directory; `--settings` and `CLAUDE.md` can scope which skills load.
  Source: <https://docs.anthropic.com/en/docs/claude-code/skills> (HTTP 301 -> 200).
- **Codex (OpenAI)** — `$CODEX_HOME/skills/<name>/SKILL.md`, typically `~/.codex/skills/`.
  Skills are loaded from this directory and invoked by name.
  Source: <https://github.com/openai/skills> (HTTP 200).
- **Cursor** — `~/.cursor/skills/<name>/SKILL.md` (project-scoped `.cursor/skills/` also works).
  Source: <https://docs.cursor.com/agent/skills> (HTTP 308 redirect).
- **OpenClaw / generic** — `~/.agents/skills/<name>/SKILL.md` or any directory the runtime
  announces; the layout is the same folder + SKILL.md convention.
- **Anthropic skills collection** — <https://github.com/anthropics/skills> (HTTP 200) ships
  reusable skill folders in exactly this layout; use it as a reference for what a well-formed
  skill looks like.

### `scripts/gen-catalog.mjs`

`catalog.json` is **generated**, never hand-edited. `scripts/gen-catalog.mjs` walks
every `skills/<package>/<name>/SKILL.md`, reads the YAML frontmatter and writes one
entry per skill. Packages are **derived from the skills/ folders** at generation time —
a package is any top-level folder under `skills/` that contains skill subfolders — so
there is no hand-maintained package or skill list.

```sh
node scripts/gen-catalog.mjs            # regenerate catalog.json
node scripts/gen-catalog.mjs --check    # fail if catalog.json is out of date
```

CI runs `node scripts/gen-catalog.mjs --check` on every push and PR
(`.github/workflows/validate.yml`), so a hand-edited `catalog.json` cannot land.

### `scripts/install.sh`

```sh
# Dry-run first: never overwrites without a flag.
./scripts/install.sh --target codex --dry-run pg-rls-multitenant
# Install (copies the skill folder into ~/.codex/skills/).
./scripts/install.sh --target codex pg-rls-multitenant
# Force-replace an existing skill.
./scripts/install.sh --target claude --force honest-status
# Install every skill in a package.
./scripts/install.sh --target cursor --package engineering
```

`--target` accepts `codex`, `claude`, `cursor`, `agents`, or an explicit directory path.
Without `--force`, an existing target folder is left untouched and the script exits non-zero.
`--dry-run` prints the source and destination paths it would touch and exits without writing.

Packages are **derived from the `skills/` folders at install time** — never a
hand-maintained list and never read from `catalog.json`. A package is any top-level
folder under `skills/` that contains at least one subfolder with a `SKILL.md`, so a
new package or skill appears automatically. `--package <name>` installs every skill in
that package:

```sh
./scripts/install.sh --target cursor --package engineering   # 10 engineering skills
./scripts/install.sh --target cursor --package business-de   # 11 German business skills
./scripts/install.sh --target cursor --package agentic-data  # 10 data-plane skills
./scripts/install.sh --target cursor --package generic       # every skill in the repo
```

Virtual packages: `generic` installs every skill; `meta` and `ref-*` are reserved
on-demand names that currently resolve to the empty set. The source path for each
skill is resolved by searching the `skills/` tree rooted at the script's own
directory, so the folder name alone is enough — no catalog lookup.

### `scripts/validate.py`

Validates every skill against the open standard: name rules, description length, front matter
fields, file size limits, link resolution, and catalog consistency.

```sh
python3 scripts/validate.py            # exit 0 on success
python3 scripts/validate.py --json      # machine-readable report
```

### `scripts/validate_skill.py`

Validates Agent Skill folders against the open standard at
[agentskills.io](https://agentskills.io/specification) (specification text fetched
2026-10-13 from `raw.githubusercontent.com/agentskills/agentskills/main/docs/specification.mdx`).
Rules: `SKILL.md` with YAML frontmatter; `name` (≤64 chars, lowercase-hyphenated, must equal the
folder name); `description` (1–1024 chars, must state what the skill does *and* when to use it);
`compatibility` ≤500 chars; SKILL.md ≤500 lines; every relative link in the body resolves to a
file with a valid anchor. Defaults to `skills/engineering/**` (this job's owned tree);
`--everywhere` scans the whole repository.

```sh
python3 scripts/validate_skill.py --all            # engineering skills only (default)
python3 scripts/validate_skill.py --everywhere      # every skill in the repo
python3 scripts/validate_skill.py <skill-dir>...   # explicit paths
```

### `scripts/build-index.py`

Generates `index/INDEX.md` (human-readable) and `index/skills.json` (machine-readable) from the
skill folders and `catalog.json`.

```sh
python3 scripts/build-index.py
```

## Engineering scripts (this job: `skills-engineering-r3`)

Each engineering skill ships an offline, deterministic checker plus a self-test that
exercises it on good/bad fixtures. Run them all before committing:

```sh
python3 scripts/validate.py                       # catalog + skill consistency
python3 scripts/validate_skill.py --all            # agentskills.io standard, all 10
for t in skills/engineering/*/scripts/*_test.py skills/engineering/tests/*.py; do
  python3 "$t" || exit 1
done
```

| Skill | Checker | Self-test |
|-------|---------|-----------|
| pg-rls-multitenant | `scripts/check_rls_migration.py` | `check_rls_migration_test.py` |
| outbox-idempotency | `scripts/check_outbox.py` | `check_outbox_test.py` |
| problem-json-contracts | `scripts/check_problem_catalogue.py` | (examples in `examples/`) |
| module-contract-first | `scripts/check_contract_drift.py` | `check_contract_drift_test.py` |
| shared-tree-git | `scripts/check_shared_tree.py` | `check_shared_tree_test.py` |
| long-test-discipline | `scripts/run_long_test.sh` | (procedural) |
| playwright-a11y-e2e | `check_axe_evidence.py`, `check_keyboard.py`, `check_workaround_markers.py` | `check_axe_evidence_test.py`, `check_workaround_markers_test.py` |
| foundation-v2-conformance | `scripts/check_foundation_tokens.py`, `scripts/fresh_consumer_test.sh` | `check_foundation_tokens_test.py` |
| acceptance-harness | `scripts/check_audit_selectors.py` | `check_audit_selectors_test.py` |
| honest-status | `scripts/check_status_evidence.py` | `check_status_evidence_test.py` |

CI runs `validate.py`, `validate_skill.py --all`, and every `*_test.py` on every push and
PR (`.github/workflows/validate.yml`).

## Contributing

See `CONTRIBUTING.md` and `AGENTS.md`. New skills start from `templates/skill/SKILL.md`.
Run `python3 scripts/validate.py` and `python3 scripts/validate_skill.py --all` before committing.

## License

MIT, see `LICENSE`.
