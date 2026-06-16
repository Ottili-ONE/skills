# Contributing

Thank you for contributing to Ottili ONE Skills.

## Skill packages

Choose the right package before adding a skill:

| Package | When to use |
|---------|-------------|
| `core` | Team-maintained official skills only (maintainer approval required) |
| `curated` | Complete, general-purpose skills vetted for broad use |
| `community` | Community contributions; may be less polished |
| `ottili-ai` | Skills for Ottili AI runtime and platform integrations |

## Adding a skill

1. **Create the directory**

   ```
   skills/<package>/<skill-name>/
   └── SKILL.md
   ```

2. **Write SKILL.md** with YAML frontmatter as the first block:

   ```yaml
   ---
   name: my-skill-name
   description: Use when [triggering conditions only — not the workflow]
   ---
   ```

   Required fields: `name`, `description`

   Recommended: `version`, `category`, `license`, `compatibility`

3. **Register in catalog.json**

   Add an entry to the `skills` array:

   ```json
   {
     "id": "my-skill-name",
     "name": "my-skill-name",
     "title": "My Skill Name",
     "version": "1.0.0",
     "package": "community",
     "path": "skills/community/my-skill-name",
     "category": "general",
     "license": "MIT",
     "description": "Short summary for humans and tooling."
   }
   ```

4. **Validate**

   ```bash
   python3 scripts/validate.py
   ```

5. **Open a pull request**

## Conventions

- **Slug = name**: Directory name, `name:` in frontmatter, and `catalog.json` → `name` must match.
- **English code and skill content**: Skill bodies should be written in English unless the skill explicitly targets another language audience.
- **Description triggers, not summaries**: The `description` field tells agents *when* to use the skill, not *how* it works. Follow [agentskills.io](https://agentskills.io/specification).
- **Self-contained**: Skills must work without private repos, credentials, or project-specific paths unless documented as required inputs.
- **No placeholders**: Do not submit stub skills with `<PLACEHOLDER>` or TODO-only content.
- **Supporting files**: Put scripts next to `SKILL.md` or in `references/`. Keep dependencies stdlib-only when possible.
- **One skill per directory**: Do not nest multiple skills in one folder.

## Review criteria

Maintainers check:

- Valid frontmatter and catalog entry
- `scripts/validate.py` passes
- Clear triggering conditions in `description`
- No secrets, hardcoded credentials, or private URLs
- License compatibility (prefer MIT)

## Extending the catalog schema

To add a new package:

1. Create `skills/<new-package>/`
2. Add an entry under `packages` in `catalog.json`
3. Document it in README.md

No code changes required unless validation rules need updating.

## Questions

Open an issue at [github.com/Ottili-ONE/skills/issues](https://github.com/Ottili-ONE/skills/issues) or contact [support@ottili.one](mailto:support@ottili.one).
