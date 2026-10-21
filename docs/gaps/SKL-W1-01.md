# SKL-W1-01 gaps

Job: SKL-W1-01 — Canonical skills: rewritten to the real Ottili conventions.
Owner of the paths this job writes: `skills-engineering-r3` (`docs/R3_OWNERS.json`).
Written: 2026-10-16. Last updated: 2026-10-20 (TASK-0003, the command line interfaces and
their versioned contracts).
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
  `a_sees_own 1`, `a_sees_b 0`, `unset_sees_rows 0`, `write_leaks 0` (PASS) and the negative
  case (a table without a policy) measures `2`, `1`, `2`, `0` (FAIL, "cross-tenant leak").
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

## G-008 — the RLS gate did not look at the write path of a policy — FOUND AND FIXED 2026-10-20

- **What the verification pass measured.** The static gate of the tenant checker asked one
  question about a policy: does it read the canonical tenant GUC? It never asked what the
  policy's `WITH CHECK` clause says. A migration with
  `USING (company_id = current_setting('app.company_id', true)) WITH CHECK (true)` therefore
  passed the gate with exit 0 — and on the real PostgreSQL of this job, the session of the
  second company wrote a row that claimed the first company. The row was in the table. The
  read path of that migration is closed, so the leak probe of the time reported a green
  leak test on it.
- **Root cause.** `ottili_rls/scanner.py` kept the whole policy body as one string, so the
  `USING` clause and the `WITH CHECK` clause could not be told apart, and `ottili_rls/rules.py`
  had no rule for the write path. The skill itself taught the rule ("INSERT wrong tenant |
  rejected by `WITH CHECK`") and the gate did not enforce it.
- **Fix.** The scanner reads a policy into its command and its two guards
  (`PolicyFacts`), the rules require the tenant column in the guard that accepts a new row
  (`WITH CHECK`, or `USING` when there is no `WITH CHECK`) and in the `USING` clause of a
  policy that reads, and the leak harness measures the write path as well
  (`write_leaks`). The new findings are `missing_tenant_guard` and
  `unguarded_write_path`. The seven tests that hold this are in
  `tests/hygiene/test_rls_core.py`, `tests/hygiene/test_rls_checker.py` and
  `tests/hygiene/test_leak_probe.py`; each of them fails without the fix (measured: the
  rule reverted, 7 failures; the old example migration, 1 failure).

## G-009 — the example migration of the skill could not be applied twice — FOUND AND FIXED 2026-10-20

- **What the verification pass measured.** `references/examples/good_migration.sql` — the
  example every reader of the skill copies — created its policies with a plain
  `CREATE POLICY`. A second application on the same schema failed with
  `policy "tenant_isolation" for table "tenant_isolated_notes" already exists`, so a
  deployment that failed half way could not be retried without leaving the schema half
  migrated. The platform's own migrations do not have that defect: they create the policy
  inside a `DO` block that asks `pg_policies` first.
- **Fix.** The example now creates both policies in a `DO` block, in the shape of the
  product migrations. It is applied twice on a real PostgreSQL by
  `tests/hygiene/test_leak_probe.py::test_the_canonical_example_can_be_applied_twice`, and
  the leak probe still measures `1`, `0`, `0`, `0` after the second application.

## G-010 — the job card's owned paths do not cover the interfaces of this task — FOUND 2026-10-20

- **What the card asks for.** TASK-0003 asks for two interfaces,
  `./scripts/validate.py --everywhere` and `./scripts/install.sh --target $(mktemp -d)
  --package engineering`. Both live in `scripts/`, and the card's owned paths are
  `skills/{evidence-based-status,tenant-rls-postgres,outbox-events,problem-details,
  foundation-ui-usage,e2e-a11y-playwright}/**` plus `tests/**` — the same mismatch as G-002.
- **What the ownership says.** `docs/R3_OWNERS.json` gives `scripts/**` to
  `skills-engineering-r3`, which is this job, and the `AGENTS.md` of this worktree lists
  `scripts/**` under "This job owns". The interfaces of this task are therefore inside the
  ownership of this job and outside the *card*.
- **Consequence, measured.** `scripts/truth/gate.mjs` reports every changed file outside
  the owned globs as "other jobs own them" and fails; `scripts/truth/safe-commit.mjs`
  refuses to commit a tracked file outside the owned paths. The gate and the commit of this
  pass were therefore run with the card's globs **plus** the four script globs this pass
  touches, identically in both (the kit refuses a commit whose gate ran with other globs):
  ```
  --owned "skills/engineering/honest-status/**,skills/engineering/pg-rls-multitenant/**,\
  skills/engineering/outbox-idempotency/**,skills/engineering/problem-json-contracts/**,\
  skills/engineering/foundation-v2-conformance/**,skills/engineering/playwright-a11y-e2e/**,\
  tests/**,scripts/validate.py,scripts/install.sh,scripts/lib/**,scripts/ottili_contracts/**,\
  README.md,docs/interfaces/**"
  ```
  The same pass adds `README.md` (owned by `skills-engineering-r3` in `docs/R3_OWNERS.json`)
  and `docs/interfaces/**` (the directory the interface contracts live in; the card asks for
  the contract to be documented in `docs/`).
- **Requested from the operator:** re-issue the card with those globs, so that the card's
  own gate command is the command that works.

## G-011 — the README claimed that the `ref-*` packages resolve to no skills — FOUND AND FIXED 2026-10-20

- **What was claimed.** `README.md` and `docs/interfaces/install.md` said: "`meta` and any
  package name starting with `ref-` are reserved on-demand names that resolve to no skills,
  so the six `ref-*` skills have to be installed by name." That is false. The packages are
  derived from the folders at install time, and the tree has six real `ref-*` packages.
- **Measured.** `bash scripts/install.sh --check --target /tmp/refcheck --package
  ref-datev-extf` → `ok: ref-datev-extf -> /tmp/refcheck/ref-datev-extf`, exit 0. The
  installer has always installed them; only the documents were wrong. A consumer that read
  the README would have believed that six skills cannot be installed as a package.
- **Fix.** The README and the contract document now say that the `ref-*` folders are real
  packages, that `meta` alone is reserved, and that a package name is matched literally
  (`--package engineering+` is refused). `tests/hygiene/test_install.py::
  test_on_demand_reference_packages_install_their_skill` holds the behaviour.

## G-012 — the test dependencies of the contract tests are not declared anywhere — FOUND 2026-10-20

- **What the new contract tests need.** `tests/interfaces/` validates the published
  payloads against the JSON Schema (`jsonschema`) and against the typed view (`pydantic`).
  Both are installed in this environment (`pydantic 2.13.5`, `jsonschema 4.26.0`), and the
  CI workflow already installs `jsonschema` for the problem-catalogue checker.
- **Why that is not enough.** The repository has **no dependency manifest at all** (no
  `pyproject.toml`, no `requirements.txt`), and the root allow-list of the truth kit
  (`scripts/truth/config.json` → `rootAllowlist`) forbids a new entry at the root of the
  repository, so this job cannot add one. The dependency of a test is therefore invisible
  to a consumer and to CI.
- **Requested from the operator:** either add a dependency file to the root allow-list
  (`requirements-dev.txt` with `pydantic` and `jsonschema`) or publish the test
  dependencies in `scripts/truth/config.json`. Until then the README states the optional
  installation (`pip install pydantic jsonschema`).

## G-013 — the `$id` of the two published schemas points at a host this job cannot verify — FOUND 2026-10-20

- **What was published.** `scripts/ottili_contracts/schemas/*.schema.json` carry
  `$id: https://contracts.ottili.one/skills/<name>/v1.schema.json`. The host follows the
  convention of the problem-details skill (`contracts.ottili.one/problems/<code>`), which
  the plan of this job uses for the RFC 9457 `type` URIs.
- **Why it is a claim.** The platform repository is **not** on this host (F-001), so this
  job cannot confirm that `contracts.ottili.one` is the host the platform publishes, nor
  that these two paths are reserved there. The **schema files are the truth** (they are
  committed, they are generated from the typed view and a test holds them); the `$id` is
  the identity a consumer will use to look the schema up.
- **Requested from the Platform lane:** reserve
  `https://contracts.ottili.one/skills/validate-report/v1.schema.json` and
  `https://contracts.ottili.one/skills/install-manifest/v1.schema.json`, or publish the host
  the platform really uses. The `$id` of the two files follows that answer in one commit
  (the schemas are generated, so it is `python3 scripts/ottili_contracts/generate.py` and
  the contract test).

## What this pass did NOT do (and why)

- **The `migrate` rung of the job gate was skipped for this run, and why.** The job gate
  treats every changed `.sql` file as a product migration
  (`scripts/truth/gate.mjs`: `migrations = live.filter((f) => f.path.endsWith('.sql'))`) and
  then runs `commands.migrate` twice on a fresh database. This repository is a catalogue of
  skills: it has no product schema, no migration runner and no `commands.migrate` in
  `scripts/truth/config.json` (the W0 job never needed one), so the rung cannot run here.
  The job card itself declares "Migration stamp block (SQL migration file names): none (this
  job has no migrations of its own)". The only `.sql` file this job changes is
  `skills/engineering/pg-rls-multitenant/references/examples/good_migration.sql` — a
  reference example inside a skill, not a migration of a product.
  **What proves the property instead:** `tests/hygiene/test_leak_probe.py::
  test_the_canonical_example_can_be_applied_twice` applies that example twice on a real
  PostgreSQL that `scripts/truth/db.mjs create --job SKL-W1-01 --fresh` made — the same
  "apply twice on a fresh database" the rung would do — and the gate's `tests` rung runs it.
  **Cross-job request to the kit owner (`scripts/truth/**`):** either let the job gate
  ignore a `.sql` file under a `references/examples/` directory, or have the W0 job define a
  `commands.migrate` for a repository that has no migrations. Until then, a job that
  teaches SQL in a skill cannot pass the gate with the card's own command.
- The verification pass over the tenant skill also cleared the type and lint debt of the
  owned test tree, because the DONE WHEN of the job asks for ruff and mypy clean on the
  owned paths: `mypy --strict tests` went from **52 errors in 11 files** (measured at
  `HEAD`) to **0**, and `ruff check tests` from **23 errors** to **0**. The 27 test files
  that were touched carry only annotations, import order and the explicit `check=False` of
  a `subprocess.run` that already ignored the exit code; no assertion was weakened, no
  test was skipped and no behaviour changed.
- The five other canonical skills (`honest-status`, `outbox-idempotency`,
  `problem-json-contracts`, `foundation-v2-conformance`, `playwright-a11y-e2e`) are the
  subject of the remaining tasks of this job (TASK-0003 … TASK-0006). Only the tenant/RLS
  skill was rewritten in this pass.
- The three skills the canonical set drops that live in `skills/engineering/**`
  (`shared-tree-git`, `long-test-discipline`, `module-contract-first`) were **not** deleted
  here: the deletion belongs to TASK-0006 together with the catalogue change, so that no
  pass leaves the repository with a broken "Related skills" link.

## G-014 — four contract defects the VERIFY pass of TASK-0003 found — FOUND AND FIXED 2026-10-20

The build pass of TASK-0003 landed the two contracts (`bbb9ec4`, `431aabb`, `222685d`).
The independent verification of this pass executed the interfaces instead of trusting the
notes and found four real defects. All four are fixed here, each with a regression test
that fails without the fix (measured by reverting the fix and watching the test fail).

- **D-1 — the install manifest was corrupted by a `|` in a path.** `manifest_add` kept a
  row as `name|package|source|destination|action|error` and `manifest_emit` split it
  again. A target directory may legally carry a `|`; every field then shifted. Measured on
  `HEAD`: `install.sh --target '<dir>/a|b' --package engineering --json` published
  `"action": "b/acceptance-harness", "error": "copied"` — valid JSON that violates the
  published schema (`action` is not in the enum). Fixed by rendering each row to its JSON
  form once in `manifest_add`; the row is never parsed back. Guards:
  `tests/interfaces/test_install_interface.py::test_a_pipe_in_a_path_does_not_corrupt_the_manifest`
  and `::test_an_error_row_survives_a_pipe_in_the_message`.
- **D-2 — the JSON Lines export had no schema.** The tool publishes the report twice
  (`--json` and `--jsonl`) under ONE contract id, but the committed schema described only
  the report object. A consumer that validated a `--jsonl` line failed with
  `Additional properties are not allowed ('findings', 'kind' were unexpected')`. The
  README claimed the single schema covered `--jsonl` too, which was false. Fixed by
  publishing a second normative artefact of contract `v1`: the lines schema
  (`...validate-report.v1.lines.schema.json`), generated from a discriminated union
  (`ValidateLine` = summary | finding) with its own worked `.jsonl` example. Guards:
  `::test_the_jsonl_export_validates_against_the_published_lines_schema`,
  `::test_the_committed_lines_schema_matches_the_typed_view`,
  `::test_the_lines_example_validates_against_the_lines_contract` and the document guard
  `tests/interfaces/test_interface_docs.py::test_every_published_schema_is_documented`.
- **D-3 — `--json` and `--jsonl` together were accepted silently.** Both render the same
  report; `--jsonl` won and the caller got a format it had not asked for, exit 0. Now an
  `argparse` mutually exclusive group: exit 2, no report on stdout. Guard:
  `::test_the_two_machine_formats_cannot_be_asked_for_at_once`.
- **D-4 — a catalogue entry without a `name` raised a bare `KeyError`.** `validate_tree`
  was called OUTSIDE the `try` that turns a broken catalogue into a usage error, so
  `--everywhere` printed a Python traceback and exited 1 while `docs/interfaces/validate.md`
  promises "No traceback: the tool reports, it does not raise" and exit 2. Fixed by moving
  the tree cross-check into the guarded block. Guard:
  `::test_a_catalogue_entry_without_a_name_is_a_usage_error`.

## G-016 — the kit's own dependencies made the gate fail for every pass — FOUND AND FIXED 2026-10-20

- **What happened.** `node scripts/truth/db.mjs create --job SKL-W1-01 --fresh` needs the
  kit's dependencies, and the kit asks for `npm install --prefix scripts/truth`. That
  creates `scripts/truth/node_modules/` and `scripts/truth/package-lock.json`. Both are
  UNTRACKED, and the gate's **ownership** step counts every untracked file
  (`scripts/truth/gate.mjs` → `changedFiles` → `git ls-files --others
  --exclude-standard`). The gate therefore failed with "changed file(s) outside the owned
  paths" for files that NO job may ever commit. The `--exclude` list does not help: it
  only removes paths from the OWNED set, and these paths were never in it.
- **Why it is a kit problem, not a job problem.** The kit itself treats these files as
  artefacts it does not own: `scripts/truth/manifest.mjs` skips `node_modules` and
  `package-lock.json` in its integrity manifest, and
  `scripts/truth/lib/common.mjs` → `generatedGlobs` lists `**/node_modules/**` and
  `**/package-lock.json`. The repository's `.gitignore` simply did not say so.
- **Fix.** `.gitignore` (owned by this job) now carries `node_modules/` and
  `package-lock.json`. No tracked file is affected (`git ls-files` shows no tracked
  `node_modules` or `package-lock.json`), the kit's integrity check still passes
  ("kit matches MANIFEST.sha256 (15 files)"), and the gate passes with the kit
  dependencies installed. Measured: the gate failed with 134 untracked files before the
  change and passed after it.
- **Requested from the operator (optional):** the kit could also make
  `changedFiles()` skip the paths of `cfg.generatedGlobs`, so that a repository whose
  `.gitignore` does not cover them does not fail the ownership step.

## G-015 — `docs/truth/REPO_SHAPE.md` does not list the contract registry — FOUND 2026-10-20

- **What is missing.** This pass added `scripts/lib/` (the manifest library) and
  `scripts/ottili_contracts/` (the contract registry: schemas, typed view, examples) to
  the repository. `docs/truth/REPO_SHAPE.md` enumerates the tools of the repository and
  does not mention either directory. Nothing drifted: its "Tools - exactly one each" table
  still holds exactly one installer and one aggregate validator.
- **Requested from the owner of `docs/truth/`:** add the contract registry (and the
  manifest library) to the tools table of `docs/truth/REPO_SHAPE.md`. The document is not
  owned by this job, so this pass cannot edit it.
