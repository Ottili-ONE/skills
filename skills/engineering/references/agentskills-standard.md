# The agentskills.io standard -- rules every engineering SKILL.md must follow

Source: `https://raw.githubusercontent.com/agentskills/agentskills/main/docs/specification.mdx`
(retrieved 2026-10-13, HTTP 200; re-verified 2026-10-14). Enforced by
`scripts/validate_skill.py --all`, which implements these rules from the spec text.

This file is the single reference for the *authoring* format the agent runtime reads.
Procedure-specific rules live in each skill's `references/*-procedure.md`; this file covers
only the format, not the engineering content.

## 1. SKILL.md front matter (YAML between `---` delimiters)

| Field | Rule | Enforcement |
|-------|------|-------------|
| `name` | <= 64 chars; `[a-z0-9-]`, starts with a letter; must equal the folder name | `validate_skill.py` |
| `description` | <= 1024 chars; states **what** the skill does **and when** to use it | `validate_skill.py` |
| `license` | SPDX identifier or `MIT-compat` | informational |
| `compatibility` | <= 500 chars; environment requirements, not prose | `validate_skill.py` |
| `metadata` | free-form map; `{}` is valid | -- |
| `allowed-tools` | list or `[]`; `[]` means "no tool restrictions declared" | -- |

A `description` that only says *what* fails the standard: it must name the trigger.

- Bad: `description: "Checks outbox tables for invariants."`
- Good: `description: "Transactional outbox pattern ... Use when adding event-driven integrations ..."`.

## 2. Body length and progressive disclosure

- SKILL.md body must be **<= 500 lines**. The runtime loads the whole file, so long
  material moves to `references/`, one level deep, linked from the body.
- The body is the *quick reference*: trigger, decision tables, numbered procedure summary,
  worked examples, pitfalls, verification checklist, scripts, related skills.
- `references/` holds the deep material: `SOURCES.md`, `DESIGN.md`, `EVALS.md`,
  `*-procedure.md`, examples, fixtures.

This is why every engineering SKILL.md opens with a line like
`Full procedure: references/<skill>-procedure.md`. The body summarizes; the reference
explains.

## 3. Name rules in detail

The folder name and the `name:` front matter must match exactly. The alphabet is
`[a-z0-9-]`, the name starts with a letter, length <= 64. Hyphens separate words; no
underscores, no capitals, no spaces.

- `pg-rls-multitenant` -- valid.
- `PG_RLS_Multitenant` -- invalid (capitals, underscore).
- `problem-json-contracts` -- valid.

The folder name is canonical. Renaming a folder requires renaming the front matter and
updating every cross-link (`Related skills` sections and `index/skills.json`).

## 4. Description rules in detail

The description is the field the runtime uses to decide whether to load the skill, so it
must answer two questions in <= 1024 chars: (1) what does it do, (2) when do I use it.
A description that omits the trigger is the most common validator failure in this
collection. The trigger must be a concrete situation an agent would actually encounter.

- Bad: `"Postgres row-level security guidance."`
- Good: `"Enforces Postgres row-level security for multi-tenant Ottili workloads: tenant-key-first design, FORCE RLS, expand/contract migrations, and automated leak tests that fail on policy gaps. Use when adding a tenant-isolated table or view, reviewing tenant_id/organization_id/namespace columns for missing RLS, or investigating 'user X saw user Y's data' incidents."`

## 5. Cross-links

Every SKILL.md ends with a `## Related skills` section using relative paths:
`[module-contract-first](../module-contract-first/SKILL.md)`. Relative paths keep the
collection installable into any target directory. Absolute paths and repo-internal paths
(`/srv/ottili/...`) are forbidden in SKILL.md -- they break when the skill is copied.

## 6. How to validate

```bash
python3 scripts/validate_skill.py --all          # skills/engineering/**
python3 scripts/validate_skill.py --everywhere   # whole repo
python3 scripts/validate.py                      # catalog + frontmatter
```

All three exit 0 on success. CI runs them in `.github/workflows/validate.yml`.
