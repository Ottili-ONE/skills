# Community Skills

This package holds community-contributed skills.

## Submit a skill

1. Fork the repository
2. Add your skill under `skills/community/<skill-name>/SKILL.md`
3. Register it in `catalog.json` under the `community` package
4. Run `python3 scripts/validate.py`
5. Open a pull request

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for full guidelines.

## Quality expectations

Community skills should:

- Include valid YAML frontmatter with `name` and `description`
- Match the [Agent Skills open standard](https://agentskills.io)
- Be self-contained and executable without private dependencies
- Document any required environment variables or tools

Skills that are incomplete, placeholder-only, or tightly coupled to a private project will not be merged.
