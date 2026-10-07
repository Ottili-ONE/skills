# Ottili ONE — Engineering Playbook Skills

Ten opinionated, testable engineering skills. Each one is a self-contained
playbook: a `SKILL.md` (when to fire + how), a `references/` folder with primary
sources and worked examples, and a `scripts/` folder with runnable helpers.

## List

| Skill | One-line value | Install hint |
|-------|----------------|--------------|
| [acceptance-harness](./acceptance-harness/SKILL.md) | Turn acceptance criteria into executable, traceable harness tests. | `./scripts/install.sh acceptance-harness` |
| [foundation-v2-conformance](./foundation-v2-conformance/SKILL.md) | Check a project against the Ottili Foundation v2 baseline. | `./scripts/install.sh foundation-v2-conformance` |
| [honest-status](./honest-status/SKILL.md) | Report build/test/deploy status without optimistic spin. | `./scripts/install.sh honest-status` |
| [long-test-discipline](./long-test-discipline/SKILL.md) | Run long tests with timeouts, resource caps and deterministic logs. | `./scripts/install.sh long-test-discipline` |
| [module-contract-first](./module-contract-first/SKILL.md) | Define module contracts up front and drift-check them against code. | `./scripts/install.sh module-contract-first` |
| [outbox-idempotency](./outbox-idempotency/SKILL.md) | Make outbox-driven side effects safely retryable and idempotent. | `./scripts/install.sh outbox-idempotency` |
| [pg-rls-multitenant](./pg-rls-multitenant/SKILL.md) | Enforce row-level security and tenant isolation in Postgres. | `./scripts/install.sh pg-rls-multitenant` |
| [playwright-a11y-e2e](./playwright-a11y-e2e/SKILL.md) | End-to-end tests with accessibility (a11y) assertions. | `./scripts/install.sh playwright-a11y-e2e` |
| [problem-json-contracts](./problem-json-contracts/SKILL.md) | Emit and validate RFC 7807 Problem Details responses. | `./scripts/install.sh problem-json-contracts` |
| [shared-tree-git](./shared-tree-git/SKILL.md) | Merge shared trees across repos without history collisions. | `./scripts/install.sh shared-tree-git` |

## Install

From the repository root:

```bash
# install every engineering skill
./scripts/install.sh

# install one skill
./scripts/install.sh acceptance-harness

# list what is installed
./scripts/list-skills.py
```

## Validate

```bash
python3 scripts/validate.py            # catalog + structure
python3 scripts/build-index.py         # regenerate index/INDEX.md, index/skills.json
```

## Conventions

- `SKILL.md` starts with YAML frontmatter (`name`, `description`, `version`).
- Long material lives in `references/`, never in `SKILL.md` (keep `SKILL.md`
  under 500 lines).
- Every skill that ships a script ships a deterministic, offline-capable test.
- Facts tied to a specific version carry a `references/SOURCES.md` entry with
  URL + retrieval date.
