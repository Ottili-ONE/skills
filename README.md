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
scripts/                  # validate.py, install.sh, build-index.py, helpers
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

### `scripts/validate.py`

Validates every skill against the open standard: name rules, description length, front matter
fields, file size limits, link resolution, and catalog consistency.

```sh
python3 scripts/validate.py            # exit 0 on success
python3 scripts/validate.py --json      # machine-readable report
```

### `scripts/build-index.py`

Generates `index/INDEX.md` (human-readable) and `index/skills.json` (machine-readable) from the
skill folders and `catalog.json`.

```sh
python3 scripts/build-index.py
```

## Contributing

See `CONTRIBUTING.md` and `AGENTS.md`. New skills start from `templates/skill/SKILL.md`.
Run `python3 scripts/validate.py` before committing.

## License

MIT, see `LICENSE`.
