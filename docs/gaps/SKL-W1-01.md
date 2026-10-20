# SKL-W1-01 gaps

Job: SKL-W1-01 — Canonical skills: rewritten to the real Ottili conventions.
Owner of the paths this job writes: `skills-engineering-r3` (`docs/R3_OWNERS.json`).
Written: 2026-10-16. Last updated: 2026-10-20 (TASK-0002, the tenant convention).
Everything here is measured, not asserted.

## G-001 — the truth harness does not exist in this repo — RESOLVED 2026-10-20

- The kit landed with SKL-W0-01: `scripts/truth/{preflight,gate,safe-commit}.mjs`,
  `heavy.sh`, `port.mjs`, `db.mjs`, `config.json`. `node scripts/truth/preflight.mjs
  --job SKL-W1-01 --status` prints `ok` and exits 0.
- The fallback described in the original entry (committing by hand because the kit was
  missing) is not used: every commit of this job goes through
  `node scripts/truth/safe-commit.mjs --job SKL-W1-01 --message ... --paths ... --integrate`.
- The kit needs its own npm dependencies (`npm install --prefix scripts/truth`). They are
  untracked and live on the EXCLUDE list, so they are never committed. See G-004 for the
  second way they bite.

## F-001 — the platform repository is not on this host (read-only, not owned)

- The `skills` repo is a CATALOGUE: no routes, no policy rules, no events, no migrations,
  no i18n runtime, no platform client. All of those live in the platform repository, and
  that repository is **not** checked out here: `/srv/ottili/repo/ottili-platform` contains
  only `.germo/` — no `packages/`, no `services/`, no `docs/`, no git repository. The same
  holds for `hq-v2`, `console-v2`, `ld3-v2`, `ottili-apps`, `alran-core-v2`,
  `alran-clients-v2`, `synth` and `alranbot`.
- What the skill therefore rests on: the convention file `guc-names.json` (the census of
  2026-10-20 over the eight product repositories, with the command and the scope that
  produced it) and the three real `hq-v2` migrations kept as fixtures under
  `tests/fixtures/hq-migrations/` (provenance in `tests/fixtures/PROVENANCE.md`).
- **Requested from the Platform lane:** a pinned, readable snapshot of
  `packages/events-core/src/outbox.ts` + `packages/events-core/src/contracts.ts` (the
  `EventOutboxRecord` field list and `planOutboxWrite`),
  `services/audit/migrations/002-audit-outbox.up.sql`, `docs/m1/ERROR_CATALOG.md`,
  `packages/foundation-ui/src/primitives/{tokens,display}.ts` and one `hq-v2` migration.
  Until then the counts in `guc-names.json` are the last measurement of the real trees
  (2026-10-20), not a live reading.

## F-002 — the Foundation example does not compile — RESOLVED (stale since 2026-10-16)

- The original finding was true on 2026-10-16 and is false today: the example uses the real
  `padded` prop and the real `duration`/`density` exports, and `scripts/check_foundation_tokens.py`
  passes on the good consumer. `skills/engineering/foundation-v2-conformance` is therefore
  **kept**, not deleted (the job card allows either, "delete unless its example and checker
  are made real").

## G-002 — the job card's owned paths do not exist in this repository (BLOCKER for the card's own commands)

- The card names six skills: `evidence-based-status`, `tenant-rls-postgres`, `outbox-events`,
  `problem-details`, `foundation-ui-usage`, `e2e-a11y-playwright`. None of those directories
  exists. The six canonical engineering skills live at
  `skills/engineering/{honest-status,pg-rls-multitenant,outbox-idempotency,problem-json-contracts,foundation-v2-conformance,playwright-a11y-e2e}/`.
  The card's names are labels, not folder names.
- Measured consequence: the card's globs match **zero** of the 809 tracked files (the 46
  matches are all `tests/**`). `gate.mjs` reports every changed file outside the owned paths
  as "other jobs own them" and fails, and `safe-commit.mjs` refuses to commit anything the
  gate did not see. The card's own gate command therefore fails on every commit.
- The folders were **not** moved: `skills/engineering` is a package in `catalog.json` and
  `scripts/gen-catalog.mjs` derives the package from the containing folder, so a second copy
  under `skills/evidence-based-status/` would be a second implementation of the same skill.
- **Requested:** re-issue the card's `--owned` / `--paths` / `--exclude` with the real globs:
  ```
  --owned   "skills/engineering/honest-status/**,skills/engineering/pg-rls-multitenant/**,skills/engineering/outbox-idempotency/**,skills/engineering/problem-json-contracts/**,skills/engineering/foundation-v2-conformance/**,skills/engineering/playwright-a11y-e2e/**,tests/**"
  --exclude "scripts/truth/**,scripts/truth/lib/**,scripts/truth/checks/**"
  ```
  The gate and the commit in this pass were run with exactly these values (the kit requires
  the gate and the commit to use identical globs).

## G-003 — the legacy tenant GUC names are still in the product repositories (cross-job, product debt)

- Measured 2026-10-20 (`guc-names.json`): `app.current_company_id` 919 occurrences
  (`ld3-v2` 218 files, `alran-clients-v2` 23, `ottilionev1` 18), `ottili.company_id` 267
  (`ottili-apps` 39 files, `ottili-platform` 34, `hq-v2` 3), `app.current_company` 51
  (`hq-v2` 17, `skills` 1). The canonical name is `app.company_id` with 3027 occurrences.
- Consequence of this job: the checker now **rejects** a policy that keys on a legacy name,
  because no session of the platform sets it — the policy isolates nobody. One real
  `ottili-apps` migration is kept as a fixture under `tests/fixtures/rls-shapes/` and is now
  a negative example; the test that reads it asserts both halves: the `EXECUTE` spelling with
  doubled quotes is read, and the legacy name is reported.
- **Requested from the Platform and Apps lanes:** migrate the policies of the repositories
  above to `current_setting('app.company_id', true)` (and the session that sets it), or
  publish the measured counts and the decision if a repository must keep its own name. The
  checker is the enforcement; the migrations are the work.

## G-004 — git 2.53.0 on this host hides untracked files from `status --untracked-files=all` (operator)

- Measured 2026-10-20 on this host (git 2.53.0, the only git on `PATH`):
  `git status --porcelain=v1 --untracked-files=all` prints **nothing** for an untracked
  file, while `git status --porcelain=v1` prints the directory and
  `git ls-files --others --exclude-standard` prints every file. Reproduced in a fresh
  repository outside this worktree, so it is not a property of this checkout.
- Consequence: `safe-commit.mjs` finds its new files with
  `git status --porcelain=v1 -z --untracked-files=all` and therefore never sees a file that
  is not staged yet. The first commit of this pass landed without the new package for
  exactly that reason.
- Workaround used (and the request): the new files are staged with an explicit path list
  (`git add -- <paths>` — never `add -A` or `add .`, which are blocked) before the commit.
  **Requested from the operator:** a git whose `status --untracked-files=all` lists the
  untracked files, or a kit that falls back to `git ls-files --others --exclude-standard`.

## G-005 — the `ottili.skill/v1` manifest generator is not this job's (cross-job, still open)

- The card requires every skill to carry a manifest fragment (`skill_id`, `version`, `owner`,
  `digest`, `signature`, `status`, `intents`, `requires_context`, `approval_policy`,
  `data_use_profile`) generated from the SKILL.md by the W0 catalogue generator.
  `scripts/gen-catalog.mjs` (owned by `skills-engineering-r3`) does not emit it and
  `schema/catalog.schema.json` has no such fields; the field names occur nowhere in the
  repository outside the job text.
- **Requested from the generator owner / the PLT extensions job:** the schema (field names,
  types, and whether the fragment is a `manifest` block in the frontmatter or a sidecar
  file), the generator change, and the `digest`/`signature` algorithm with the identity that
  signs it. This job prepares the SKILL.md inputs; the fragment lands when the generator
  does.

## G-006 — the container mode of the leak harness is unverified on this host

- `scripts/pg-rls-leak-test.sh` has two server modes. The `--server` mode was **verified**
  on 2026-10-20 against the real PostgreSQL 18.6 of this job: the positive case measures
  `a_sees_own 1`, `a_sees_b 0`, `unset_sees_rows 0` (PASS) and the negative case (a table
  without a policy) measures `2`, `1`, `2` (FAIL, "cross-tenant leak").
- The container mode (Docker `postgres:18-alpine`) could not be run: this host has no Docker
  daemon. It is kept because a developer machine needs it, but it is **unverified here**.
  The exact command is `bash skills/engineering/pg-rls-multitenant/scripts/pg-rls-leak-test.sh
  <migration.sql> [table]` on a host with Docker.

## G-007 — the application role in the policy is not verified against the platform

- The skill's examples name the role in the policy (`TO web_app`), and the leak harness
  creates that role. The three real `hq-v2` migrations omit the `TO` clause, which means the
  policy applies to `PUBLIC`. The platform repository is not on this host (F-001), so which
  spelling the platform uses cannot be checked here.
- **Requested from the Platform lane:** the application role name and whether the platform
  policies name it or apply to `PUBLIC`. The skill states both possibilities instead of
  guessing.

## What this pass did NOT do (and why)

- The five other canonical skills (`honest-status`, `outbox-idempotency`,
  `problem-json-contracts`, `foundation-v2-conformance`, `playwright-a11y-e2e`) are the
  subject of the remaining tasks of this job (TASK-0003 … TASK-0006). Only the tenant/RLS
  skill was rewritten in this pass.
- The three skills the canonical set drops that live in `skills/engineering/**`
  (`shared-tree-git`, `long-test-discipline`, `module-contract-first`) were **not** deleted
  here: the deletion belongs to TASK-0006 together with the catalogue change, so that no
  pass leaves the repository with a broken "Related skills" link.
