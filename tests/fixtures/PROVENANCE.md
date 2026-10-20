# Test fixtures — provenance

Every file under `tests/fixtures/` is a **verbatim excerpt of a real Ottili
product repository**. The fixtures exist so that a committed test never has to
read a sibling repository (`/srv/ottili/repo/...`) — a checkout of this
repository must be able to run the whole suite on its own.

Rule for the checkers: the fixture is the input; the sibling repository is only
ever read as a *manual* proof, recorded under `.truth/` (git-ignored), never as
a committed test.

## `hq-migrations/`

| File | Source repository | Source path | Source commit |
|---|---|---|---|
| `20261002091600_reports_intelligence_saved_report.sql` | `hq-v2` | `modules/reports-intelligence/migrations/20261002091600_reports_intelligence_saved_report.sql` | `fe9a1cbbb5dff2ebee2c1e33a6844bbb818dfaff` |
| `20261002091630_reports_intelligence_signal_threshold.sql` | `hq-v2` | `modules/reports-intelligence/migrations/20261002091630_reports_intelligence_signal_threshold.sql` | `fe9a1cbbb5dff2ebee2c1e33a6844bbb818dfaff` |
| `20261010000000_hq_procure_to_stock_r3_04_audit.sql` | `hq-v2` | `modules/procure-to-stock/migrations/20261010000000_hq_procure_to_stock_r3_04_audit.sql` | `fe9a1cbbb5dff2ebee2c1e33a6844bbb818dfaff` |

- Retrieved: 2026-10-20.
- Source license: Ottili Proprietary License 6.1 (see `hq-v2/LICENSE`).
- Why these three: they are tenant tables that use `company_id` plus a tenant
  policy keyed on `current_setting('app.company_id', true)`, and they are
  written in three different shapes — plain `CREATE TABLE`, `CREATE TABLE IF
  NOT EXISTS` and a table whose policy is created in the same file as the
  index. The RLS checker must pass all three.
- The three hostile inputs are **not** fixtures: they are written inside the
  test that uses them, so a test can never pass because a bad file was fixed.

## `status/`

| File | Source repository | Source path | Source commit |
|---|---|---|---|
| `hq-v2-docs-STATUS.md` | `hq-v2` | `docs/STATUS.md` | `fe9a1cbbb5dff2ebee2c1e33a6844bbb818dfaff` |
| `console-v2-docs-STATUS.md` | `console-v2` | `docs/STATUS.md` | `2fda74bd02c972ce1cda559f24f4135543e90870` |

- Retrieved: 2026-10-20.
- Source license: Ottili Proprietary License 6.1.
- Excerpt: the first 60 lines of the file, unchanged, so the header and the
  first claim tables are present. The lines are numbered in the file itself by
  the upstream repository's prose — the excerpt starts at line 1, so a line
  number reported by the checker is the line number of the upstream file.
- `hq-v2-docs-STATUS.md` is 60 lines of the 3 022-line upstream file
  (commit `fe9a1cbbb5dff2ebee2c1e33a6844bbb818dfaff`);
  `console-v2-docs-STATUS.md` is 60 lines of the 6 225-line upstream file
  (commit `2fda74bd02c972ce1cda559f24f4135543e90870`). Both upstream files
  assert successes whose evidence files are **not** committed next to them, so
  the checker must report them — that is the behaviour the excerpts guard.
- The upstream files stay read-only. The manual proof against the full upstream
  files is under `.truth/SKL-W0-01/` (git-ignored), never in a committed test.
