# Ottili ONE Skills

Agent Skills for **Claude Code**, **Codex**, **Cursor**, **OpenClaw**, and **Ottili AI** — maintained by [Ottili ONE](https://ottili.one).

Skills are folders of instructions, scripts, and resources that AI agents discover and apply to specific tasks. Write once, use everywhere.

Learn more:

- [Agent Skills open standard](https://agentskills.io)
- [Using skills in Codex](https://developers.openai.com/codex/skills)
- [Ottili ONE](https://ottili.one)

## Repository layout

```
skills/
├── core/          # Official Ottili skills
├── curated/       # Vetted general-purpose skills
├── community/     # Community contributions
└── ottili-ai/     # Ottili AI runtime skills (growing)

catalog.json       # Machine-readable skill registry
scripts/           # Validate, list, and install helpers
templates/skill/   # Starter template for new skills
```

Each skill lives at `skills/<package>/<skill-name>/SKILL.md` with optional supporting files (scripts, references, agent configs).

## Available skills

| Skill | Package | Version | Description |
|-------|---------|---------|-------------|
| [work-untill-i-die](skills/core/work-untill-i-die/) | core | 1.4.0 | Long-horizon execution mode — build, test, fix, repeat until truly done |
| [cursor-cli](skills/curated/cursor-cli/) | curated | 2.1.0 | Cursor CLI installation, commands, and automation patterns |

Run `python3 scripts/list-skills.py` for the full list.

## Install a skill

### Local clone

```bash
git clone https://github.com/Ottili-ONE/skills.git
cd skills
python3 scripts/install-skill.py work-untill-i-die --target codex
python3 scripts/install-skill.py cursor-cli --target claude
```

Targets: `codex`, `claude`, `cursor`, `agents` (defaults to `~/.codex/skills`, `~/.claude/skills`, etc.)

Override destination:

```bash
python3 scripts/install-skill.py work-untill-i-die --dest ~/.agents/skills
```

### From GitHub URL (Codex skill-installer)

If you use Codex with the skill-installer:

```
Install https://github.com/Ottili-ONE/skills/tree/main/skills/core/work-untill-i-die
```

Restart your agent after installing.

## Add a new skill

1. Copy `templates/skill/SKILL.md` to `skills/<package>/<skill-name>/SKILL.md`
2. Fill in frontmatter (`name` must match directory name)
3. Register the skill in `catalog.json`
4. Validate: `python3 scripts/validate.py`
5. Open a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for conventions and review criteria.

## Packages

| Package | Purpose |
|---------|---------|
| `core` | Official Ottili skills, maintained by the team |
| `curated` | Production-ready third-party and general skills |
| `community` | Community submissions (review before production use) |
| `ottili-ai` | Ottili AI / Velo platform skills |

New packages can be added by extending `catalog.json` → `packages` and creating the matching directory under `skills/`.

## Validation

```bash
python3 scripts/validate.py
python3 scripts/list-skills.py --format json
python3 scripts/list-skills.py --target codex
```

CI runs validation on every push and pull request.

## License

Repository: [MIT](LICENSE)

Individual skills may declare their own license in frontmatter. Default for skills in this repo: MIT.
