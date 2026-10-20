# Ottili truth kit

Executable gates that make "done" mean *it ran*. Every GERMO job uses these scripts; nothing here trusts a status document.

Requires Node >= 20 and git. The only npm dependency is `pg` (for `db.mjs`, `preflight.mjs --needs db`, and the gate's migrate step):
`npm install --prefix scripts/truth --no-audit --no-fund` (or let the repository's own `pg` resolve).

## Commands

| Command | Purpose |
| --- | --- |
| `node scripts/truth/preflight.mjs --job ID [--needs db,registry,browser,keycloak,platform,valkey,minio,mail,wordpress] [--requires-trunk] [--after JOB[@repo],...] [--owned GLOBS --stamp-block START-END]` | Fail-closed readiness check (kit integrity, machine, infrastructure, trunk status, predecessor jobs, migration stamp block). Exit 20 = BLOCKED (marker written outside the repo). `--status` only reads the marker, `--block "why"` marks the job blocked by hand, `--clear` removes the marker. |
| `node scripts/truth/gate.mjs job --job ID --owned GLOBS [--exclude GLOBS] [--ui] [--db] [--tests PATHS] [--e2e PATHS] [--stamp-block START-END]` | The definition of done for a job. Writes `<TRUTH_RESULTS_DIR>/<repo>/<ID>.json`. |
| `node scripts/truth/gate.mjs trunk` | Whole-repository gate (install, build, typecheck, lint, registry, migrate twice, RLS audit, boot, smoke, hygiene). Writes `docs/truth/TRUNK_STATUS.json` on success. |
| `node scripts/truth/safe-commit.mjs --job ID --message "type(scope): summary" --paths GLOBS [--integrate]` | The only way to commit and land code. Explicit paths only; refuses deletions/shrinkage/syntax errors/secrets; binds to the gate result; integrates by rebase + push (or fast-forward / branch). |
| `node scripts/truth/db.mjs create --job ID` | Isolated PostgreSQL database per job with a non-superuser application role (RLS really applies). `env`, `grant`, `exec`, `drop`, `list`, `reap`. |
| `scripts/truth/heavy.sh --class build\|db\|browser -- CMD...` | Machine-wide semaphore for installs, builds, test runs, browser runs. |
| `node scripts/truth/port.mjs --job ID` | A free TCP port (never hard-code ports). |
| `node scripts/truth/selftest.mjs` | Verifies the kit itself on this machine. |
| `node scripts/truth/manifest.mjs --check` | Verifies every kit file against `MANIFEST.sha256` (operator only: `--write` after updating the kit). Jobs never edit `scripts/truth` except `config.json` (W0 jobs). |

Scans can be run alone: `node scripts/truth/checks/scan.mjs language|stubs|secrets|size|i18n --paths GLOBS`, `node scripts/truth/checks/sqllint.mjs FILE...`.

## config.json

`scripts/truth/config.json` (written by the first W0 job of each repository, then maintained by humans):

```json
{
  "repo": "hq-v2", "repoCode": "HQ", "kind": "node-modular",
  "trunkBranch": "main", "remote": "origin", "integration": "auto",
  "install": "pnpm install --frozen-lockfile",
  "commands": {
    "build": "pnpm build", "typecheck": "pnpm typecheck", "lint": "pnpm exec eslint {paths}",
    "registryCheck": "node scripts/gen-registry.mjs --check --strict",
    "migrate": "node scripts/migrate.mjs", "test": "node --test {paths}", "e2e": "pnpm exec playwright test {paths}",
    "smokeTests": "node --test test/smoke"
  },
  "env": { "DATABASE_URL": "{migratorUrl}", "DATABASE_APP_URL": "{appUrl}", "PORT": "{port}" },
  "boot": { "command": "node src/server.mjs", "readyPath": "/readyz", "timeoutSeconds": 90 },
  "rootAllowlist": ["package.json", "pnpm-lock.yaml", "src", "modules", "scripts", "docs"],
  "sql": { "requireRls": true, "requireIdempotent": true }
}
```

`integration`: `push-trunk` (fetch, rebase, push to `<remote>/<trunkBranch>`), `local-trunk` (rebase, then fast-forward the worktree that has trunk checked out; no remote needed), `branch-only` (leave `truth/<JOB-ID>`), or `auto`.
`{paths}`, `{job}`, `{root}`, `{migratorUrl}`, `{appUrl}`, `{adminUrl}`, `{dbName}`, `{port}`, `{namespace}` are substituted.

Other keys:

| Key | Meaning |
| --- | --- |
| `sharedGlobs` | Files that every job may legitimately touch (lockfile, root `package.json`/`pyproject.toml` dependency sections). They are implicitly allowed by the ownership check, excluded from the evidence hash and from the content scans, and `safe-commit` includes them automatically when they changed. Keep this list tiny. |
| `rootAllowlist` | The only entries allowed at the repository root (the `hygiene` step of `gate trunk` fails on anything else). |
| `sql.requireRls` / `sql.requireIdempotent` | Migration lint switches. `requireRls=false` is a documented, temporary relaxation for repositories that still carry a legacy engine. |
| `language.allowGlobs`, `stubs.allowGlobs`, `secrets.allowGlobs`, `size.allowGlobs` | Per-scan exemptions (for example vendored fixtures). Every entry needs a justification comment in the W0 job's `docs/truth/REPAIR_LOG.md`. |
| `i18n.catalogGlobs`, `i18n.callPattern` | Where the catalogues live and how translation calls look. |
| `generatedGlobs` | Generated or vendored output that no scan reads. |
| `maxFileLines`, `maxSqlLines`, `maxTestLines` | Size ceilings enforced by the `size` step. |

## Environment

| Variable | Meaning | Default |
| --- | --- | --- |
| `TRUTH_RESULTS_DIR` | gate/preflight/commit records, logs (outside the repo) | `~/.ottili-truth/results` |
| `TRUTH_LOCK_DIR` | semaphore and port reservations | `/tmp/ottili-truth-locks` |
| `TRUTH_PG_ADMIN_URL` | superuser URL of the shared development PostgreSQL 17 | required for DB work |
| `TRUTH_PG_ROLE_PASSWORD` | password of `truth_migrator` / `truth_app` | `truth-dev-only` |
| `TRUTH_REGISTRY_URL` | private `@ottili` registry (else `.npmrc`) | - |
| `TRUTH_KEYCLOAK_URL`, `TRUTH_KEYCLOAK_REALM` | Keycloak | `http://127.0.0.1:50080`, `ottili-dev` |
| `TRUTH_PLATFORM_URL` | shared Platform development host used by product jobs (`/readyz`) | `http://127.0.0.1:50101` |
| `TRUTH_VALKEY_URL`, `TRUTH_MINIO_URL`, `TRUTH_MAILPIT_URL`, `TRUTH_WP_URL` | shared services | localhost defaults |
| `TRUTH_HEAVY_SLOTS_BUILD/DB/BROWSER`, `TRUTH_MIN_FREE_MB` | semaphore sizing | 6 / 10 / 5, 1536 MB |

Optional `/etc/ottili-truth/limits.env` (or `~/.ottili-truth/limits.env`) is sourced by `heavy.sh`.

## Test file conventions (what the gate discovers)

Unit and integration tests are named `*.test.mjs` (or `.test.ts` / `test_*.py`) and run with the configured test command. Browser specs are named `*.spec.mjs` (or `.spec.ts`) and live under an `e2e/` directory; they run with the configured Playwright command. Without `--tests` / `--e2e` the gate runs exactly the test files the job added or changed inside its owned paths.

## Rules the kit enforces

1. One job owns a set of paths; everything it changes must be inside them (`ownership`), and the gate result is bound to the exact content (`ownedHash`).
2. Deleting or shrinking a tracked file needs `--allow-delete` / `--allow-shrink` with a reason.
3. Migrations are PostgreSQL-only, repeatable, tenant-safe (`company_id`, forced RLS, policy) and applied twice on a fresh database.
4. Tests must exist, must not be skipped, must not use SQLite/in-memory/mocked `pg`.
5. Code, comments, identifiers, commit messages and docs are English; UI text lives in catalogues with equal keys in every locale.
6. No TODO/FIXME/STUB/not-implemented paths, no committed secrets, files stay small.
7. Honest gaps go to `docs/gaps/<JOB-ID>.md` (and only there). `WAIVE: e2e - <reason>` is the only waivable gate step.

Working notes of a job live in `.truth/<JOB-ID>/` (git-ignored).
