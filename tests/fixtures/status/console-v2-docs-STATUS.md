# Status — Console (console, platform.console)

This file says what actually works, what is stubbed and what is missing. It is updated in every task.
Last change: **2026-10-02**, task `wa-console-09` (Abschluss der Kern-Runde: `npm test`, `npm run verify`
und `npm run journey:shell` gemessen, ein Fehler im Modul-Host gefunden und behoben, alle roten
Schritte fremden Dateien zugeordnet — **Abschnitt 13**). Die Zahlen in Abschnitt 2 sind von dort und
gelten für den gemessenen Stand; ältere Zeilen tragen den Job, der sie gemessen hat.
Numbers below were measured on this host, not copied from a spec.

## 1. Versions and Platform freeze

| What | Version | Evidence |
|---|---|---|
| Platform freeze | **2.0.0-alpha.3**, tag `platform-m1-freeze-3` | `git log -1 platform-m1-freeze-3` -> `4494a3f` 2026-10-01 |
| All `@ottili/*` in `package.json` | `2.0.0-alpha.3`, exact pins, no `^`/`~` | `package.json`, never mixed |
| Registry for `@ottili/*` | Verdaccio `http://127.0.0.1:18873` | `.npmrc`; **never** npmjs (v1 names collide) |
| Node.js | v24.19.0 | `node -v` |
| npm | 11.17.0 | `npm -v` |
| PostgreSQL (dev) | **16.15**, `127.0.0.1:18432` | `select version()` via `npm run db:ping` |
| `pg` (Postgres driver) | 8.23.1, exact pin | `package.json` |
| esbuild | 0.24.2, exact pin | `package.json` |
| react / react-dom | 19.0.0 / 19.0.0 | `package.json`, peer range `^18.3.0 \|\| ^19.0.0` |

Console has its **own** Platform instance (AGENTS.md section 13): instance `18340`, product shell `18405`, `PLATFORM_DEV_PRODUCT=none` (the default world of that instance, not `/p/<name>`). The instance answers `contract_version 2.0.0-alpha.1` with 297 routes (`GET /v2/version` on 18340).

## 2. Green baseline (evidence)

All three were run on 2026-10-02 against this repo.

| Command | Result | Stand |
|---|---|---|
| `npm install --include=dev` | clean, `audited 33 packages`; the only lockfile change is the new `pg` tree | `wa-console-01` |
| `npm test` | **354 pass / 0 fail / 0 skipped** (354 Tests, exit 0). Fünf Minuten vorher: 348/3, aus zwei fremden Fixture-Dateien, die deren Besitzer inzwischen behoben hat — die Zahlen wandern, weil während der Messung geschrieben wird (Abschnitt 13) | `wa-console-09`, 2026-10-02 03:07 UTC |
| `npm run test:db` | **20 pass / 0 fail / 0 skipped** against the dev Postgres (`127.0.0.1:18432/console`) | `wa-console-03`, 2026-10-02 |
| `npm run journey:shell` | **16 PASS / 0 FAIL** — Hello-Entity, Suche, Datei, Export, Policy-Deny per role, Browser-Render (3 steps), Degraded State, Login (4 steps) | `wa-console-09`, 2026-10-02 03:00 UTC |
| `npm run gate` | 6 gates PASS, `check-secrets` with **1 finding in a foreign, untracked file** (`modules/integrations-credentials/ui/forms.mjs`; 03:00 waren es zwei in `modules/developer/tests/`, 03:08 null — Abschnitt 13) | `wa-console-09`, 2026-10-02 03:09 UTC |
| `npm run verify` | **RED — 19/21 Schritte** in 36 s. Rot sind `test` und `test:modules`; beide aus Dateien, die **während dieses Laufs** geschrieben wurden (`modules/integrations-credentials/ui/forms.mjs`, `modules/account-security/tests/forms.test.mjs`). `registry`, alle 14 Modul-Lints, `boundaries`, `gates`, `build` und `journey:shell` sind grün, siehe Abschnitt 13 | `wa-console-09`, 2026-10-02 03:08 UTC |
| `node --test test/gates.test.mjs` | **65 pass / 0 fail / 0 skipped**, one deliberately broken fixture per gate | `wa-console-05`, 2026-10-02 |
| `npm run journey:module -- tenancy-sample` | **15 pass / 0 fail** (`platform: live`, instance 18340) | `wa-console-03`, 2026-10-02 |
| `npm run test:runtime` | **19 pass / 0 fail / 0 skipped** against the dev Postgres — claim/replay/conflict/in-progress, outbox commit, delivery, backoff, dead letter, rate limit per company, the module end to end, RLS against a foreign company, and the new proof that an answer with a domain field `status` is stored whole and replayed whole (the `NaN` bug of section 13) | `wa-console-09`, 2026-10-02 |
| `npm run journey:module -- runtime-sample` | **25 pass / 0 fail** (`platform: live`, instance 18340) | `wa-console-04`, 2026-10-02 |
| `npm run test:module -- runtime-sample` | **13 pass / 0 fail** | `wa-console-04`, 2026-10-02 |
| `npm run lint:module -- runtime-sample` | **0 findings** (manifest, routes, migrations, tenant rules, UI contract) | `wa-console-04`, 2026-10-02 |
| `npm run test:module -- tenancy-sample` | **9 pass / 0 fail** | `wa-console-03`, 2026-10-02 |
| `npm run check:boundaries` | **438 files, 0 violations** | `wa-console-09`, 2026-10-02 |
| `npm run test:module -- <id>` | **15 pass / 0 fail** je Modul (4 Struktur + 11 Vertrag), 150 in den zehn Suiten | `wa-console-06`, 2026-10-02 |
| `node --test test/module-contracts.test.mjs` | **10 pass / 0 fail** — die Karte gegen sich selbst: keine doppelte Route/Action/Event/Tabelle, Tiers zeigen nach unten, jede Marker steht in `docs/platform-gaps.md` | `wa-console-06`, 2026-10-02 |
| `npm run prove:modules` | **OK — 13 PASS, 0 FAIL**, 217 shared files byte-identical | `wa-console-09`, 2026-10-02 |
| `npm run build` | `built dist/app.js (+app.css)` | `wa-console-01` |
| `npm run db:ping` | exit 0, see section 3 | `wa-console-01` |

`npm run test:db`, `npm run test:runtime` and the live pass of `npm run gate` need `DATABASE_URL` in the environment. On this
host the value is injected from `/mnt/ottili-nvme/ottili/keys/dev-postgres.env` (`CONSOLE_DATABASE_URL`)
and is never printed, never written to a file and never committed; see section 3.

`journey:shell` needs `PLATFORM_URL` and `PLATFORM_DEV_PRODUCT` in the environment. **There is no default address any more** (`integrator-console-01`, section 8): `src/platform.mjs`'s `platformRoot()` throws and names the variable, and `scripts/journey-shell.mjs` and `scripts/journey-module.mjs` skip with a sentence instead of probing the shared instance on 18150, which never existed on server B. `scripts/journey-shell.mjs` does not read `.env` itself, so an invocation without those variables now says so rather than talking to the wrong instance.

## 3. Postgres connectivity

`npm run db:ping` (`scripts/db-ping.mjs`) proves four things and prints no secret:
