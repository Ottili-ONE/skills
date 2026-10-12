# Front-matter rules — skill-authoring-evals

Verified 2026-10-12 against https://agentskills.io/specification.md (HTTP 200).
The YAML block at the top of SKILL.md is the only machine-read metadata.

## Required fields

| Field | Rule | Failure if absent |
|-------|------|------------------|
| `name` | Present, equals the folder name, slug `^[a-z0-9]+(-[a-z0-9]+)*$`, 1–64 chars, no leading/trailing hyphen, no `--` | Hard fail — the skill never registers |
| `description` | Present, non-empty, <=1024 chars, imperative, states what + when | Hard fail — the skill has no trigger |

## Optional fields

| Field | Rule |
|-------|------|
| `license` | SPDX identifier or custom text. Recommended. |
| `compatibility` | Free text; used by clients to filter. |
| `metadata` | Arbitrary key/value map; reserved for client use. |
| `allowed-tools` | **Experimental.** Never a hard failure when absent; never a hard gate. |

## Body rules

- SKILL.md body must be <=500 lines and roughly <=5,000 tokens at activation.
- Long material goes into `references/` linked one level deep (e.g. `references/procedures.md`).
- `scripts/` files must be deterministic and runnable offline; machine-readable counts to
  stdout, human detail to stderr.

## Progressive disclosure order

1. Startup: `name` + `description` only.
2. Activation: the SKILL.md body.
3. On demand: `references/*.md` and `scripts/*.py`.

A skill that puts 4,000 tokens of procedure in the description wastes the trigger budget.

## Ordered validation (what `scripts/validate_skill.py` checks)

1. Folder name is a valid slug.
2. `SKILL.md` exists.
3. Frontmatter parses; `name` present, == folder name, <=64 chars.
4. `description` present, <=1024 chars.
5. SKILL.md <=500 lines.
6. Every `references/*.md` link resolves to a real file.
7. Scripts do not fetch remote URLs at validation time (warn only).

Exit codes: 0 = pass, 1 = any FAIL, 2 = usage/input error.
