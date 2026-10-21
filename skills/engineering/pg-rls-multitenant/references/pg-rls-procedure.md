# PG RLS Multitenant — Full Procedure (progressive disclosure)
Retrieval date: 2026-10-13. All URLs re-fetched 2026-10-13 (see `references/SOURCES.md`).

## Verified versions
| Artifact | Version | Verified | Note |
|----------|---------|----------|------|
| PostgreSQL | 19 (current stable; re-verified 2026-10-14) | 2026-10-14 | `FORCE ROW LEVEL SECURITY` unchanged since 9.5; `/docs/19/` HTTP 200, `/docs/current/` resolves to 19 |
| Supabase RLS guide | current | 2026-10-13 | `service_role` key model changed 2025; see conflicts |

## 0. Tenant-key-first design decision
Every row table MUST have exactly one tenant discriminator column. Acceptable names:
`company_id`, `organization_id`, `org_id`, `namespace`, `account_id`.

- The column is `NOT NULL` with a `CHECK` constraint matching the application tenant format
  (UUID v4 for Ottili).
- Shared tables that span tenants get NO policy but are explicitly listed in a
  `shared_tables` registry so auditors can confirm they are intentional.
- **Threshold**: a table with no tenant column and no entry in the shared_tables registry
  blocks merge (the offline checker `scripts/check_rls_migration.py` reports it).

## 1. Policy creation recipe
```sql
CREATE POLICY name ON table
  [AS {PERMISSIVE | RESTRICTIVE}]
  [TO role ...]
  [USING (expr)]
  [WITH CHECK (expr)];
```
- Default role is `PUBLIC`; `FOR ALL / SELECT / INSERT / UPDATE / DELETE` scopes the policy.
- Permissive policies OR together; restrictive policies AND together.
- Use `RESTRICTIVE` only for deny overrides that must win over permissive rules.

**Decision table — policy form**
| Situation | Form | Example |
|-----------|------|---------|
| Tenant sees only its own rows | `PERMISSIVE FOR SELECT` | `USING (company_id = current_setting('app.company_id', true))` |
| Deny override (e.g. soft-deleted rows) | `RESTRICTIVE FOR SELECT` | `USING (deleted_at IS NULL)` |
| Write must stay in tenant scope | `PERMISSIVE FOR INSERT WITH CHECK` | `WITH CHECK (company_id = current_setting('app.company_id', true))` |

**The two guards are two different clauses.**
`USING` says which existing rows the policy applies to; `WITH CHECK` says which
new row may be written. A policy that names the tenant column in `USING` but
not in `WITH CHECK` closes the read path and leaves the write path open: the
company sees no foreign row, and can still write a row that claims a foreign
company. The read probe of this skill cannot see that leak - it measures what
is read, and nothing that should not be read is readable. The offline checker
sees it: a policy that applies to a write command (`INSERT`, `UPDATE` or
`ALL`) must name the tenant column in the guard that accepts the new row, and
that guard is the `WITH CHECK` clause when there is one and the `USING` clause
otherwise, because PostgreSQL falls back to `USING` when `WITH CHECK` is
omitted. A policy that applies to a read command (`SELECT`, `DELETE` or
`ALL`) must name the tenant column in its `USING` clause.

**The migration has to be re-runnable.** The product migrations create their
policy inside a `DO` block that asks `pg_policies` first, so a retry after a
failed deployment does not abort with "policy already exists" and leave the
schema half migrated. The example of this skill
(`references/examples/good_migration.sql`) does the same and is applied twice
by the test suite on a real PostgreSQL.

## 2. FORCE ROW LEVEL SECURITY
- `ENABLE ROW LEVEL SECURITY` enables RLS; `FORCE ROW LEVEL SECURITY` forces evaluation even
  for table owners and superusers.
- Dev-only tables get `NO FORCE ROW LEVEL SECURITY` with a comment explaining why; every
  non-dev table gets FORCE before merge.
- **Threshold**: any table without FORCE in a non-dev migration fails the offline checker.

```sql
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders FORCE ROW LEVEL SECURITY;
```

## 3. Expand/contract migration pattern
Expand (add a tenant column to an existing table):
1. Add column as `NULL` first if the table is non-empty (nullable during backfill).
2. Backfill existing rows with the owning tenant.
3. Add `NOT NULL` + `CHECK` constraint.
4. Add the tenant policy.
5. Run the leak test; only then contract old data.

Contract (drop the old column after N weeks):
- Separate migration named `V<version>__<description>__contract_*.sql`.
- Rollback SQL lives in the same file in a `-- ROLLBACK` block so a DBA can revert without
  reading git history.

**Threshold**: N = 4 weeks minimum after the expand migration lands in production; record the
date in the migration comment.

## 4. Leak test harness
`scripts/check_rls_migration.py` is the **offline gate** that runs before the leak probe.
It decides per table and reads the tenant convention from `guc-names.json`
(configuration, not a constant of the script): one tenant GUC (`app.company_id`), one tenant
column (`company_id`), and the legacy names that are findings (`app.current_company_id`,
`ottili.company_id`, `app.current_company`, `app.current_tenant`).

The leak harness (`scripts/pg-rls-leak-test.sh`) applies the migration to a real PostgreSQL,
seeds two companies as the superuser and then probes the table **as the application role**:
a non-superuser that is not the owner of the table, so row level security really decides
what it sees. Three measurements decide the verdict:

| Measurement | Expected | What a wrong value means |
|-------------|----------|-------------------------|
| `a_sees_own` | 1 | the own-company read is wrong: the policy does not match the seed |
| `a_sees_b` | 0 | cross-company leak: the policy is missing, wrong, or not forced |
| `unset_sees_rows` | 0 | rows are visible without a company: the table is not isolated by default |
| `write_leaks` | 0 | a row of another company was written: the `WITH CHECK` clause does not constrain the tenant column |

The first three measurements read, the fourth writes. The write probe gives
the session of the second company a row that claims the first one and expects
the database to refuse it; the transaction is rolled back, so a leak leaves no
row behind and the exit code of `psql` is the measurement. Both paths have to
be measured, because they are guarded by two different clauses of a policy: a
policy whose `USING` clause is the product standard and whose `WITH CHECK`
clause is wide open hides every foreign row and still accepts a foreign row.

The probe prints its measurements as `LABEL<tab>VALUE` lines; the verdict is taken by
`scripts/check_leak_probe.py`, which fails when a measurement is missing — a probe that did
not run proves nothing. `--print-probe-sql` and `--parse FILE` run the same logic without a
server.

Two servers are supported. `--server` uses a PostgreSQL that already runs and takes its URLs
from `--admin-url`/`--app-url` or from the truth kit with `--job <JOB>`; this is the mode
the committed tests use, because it needs no container runtime. The default mode spins up
`postgres:18-alpine` with Docker. The harness refuses to run against a table that already
exists, because the probe would measure a stale table; `--reset` drops it first.

**Test cases (all must PASS, any FAIL blocks merge):**
| Case | Assertion |
|------|-----------|
| Same-tenant read | tenant A sees its own rows |
| Cross-tenant read | tenant A sees ZERO rows belonging to tenant B |
| INSERT wrong tenant | rejected by `WITH CHECK` |
| UPDATE company_id | rejected when a RESTRICTIVE policy is present |
| View bypass | `security_invoker=false` view exposes cross-tenant rows → FAIL |
| Owner bypass | table without FORCE exposes all rows → FAIL |
| service_role bypass | `service_role` sees everything by design; never use client-side |
| Sub-select race | concurrent INSERT + SELECT may leak between policy eval and row write |

## 5. Worked examples
Good (permissive policy + FORCE + scoped grant):
```sql
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders FORCE ROW LEVEL SECURITY;
CREATE POLICY orders_tenant_select ON orders
  FOR SELECT
  TO web_app
  USING (company_id = current_setting('app.company_id', true));
GRANT SELECT ON orders TO web_app;
```
Bad (owner bypass — table created by migration role, no FORCE):
```sql
CREATE TABLE notes (id uuid, company_id uuid, body text);
-- migration role can read every tenant's notes until FORCE is added
```
Bad (write path open — the read path is closed, the write path is not):
```sql
CREATE POLICY notes_tenant ON notes
  FOR ALL TO web_app
  USING (company_id = current_setting('app.company_id', true))
  WITH CHECK (true);
-- no foreign row is readable, and a foreign row can still be written
```
Bad (view bypass):
```sql
CREATE VIEW active_notes AS SELECT * FROM tenant_isolated_notes;
-- runs as view owner; RLS on the base table is skipped
```

## 6. Pitfalls from research (real incidents)
- Owner bypasses RLS unless FORCE is set — a table created by a migration role silently exposes
  rows to that role's sessions.
- Views are security-definer by default and bypass RLS unless `security_invoker = true`.
- Missing GRANT before policy → error 42501 before any policy runs.
- `service_role` key bypasses all RLS — never use it client-side.
- Sub-select race condition between policy evaluation and INSERT can leak rows under concurrent load.

## 7. Verification checklist (all must pass before merge)
- [ ] Every row table has at least one policy matching its tenant column
- [ ] FORCE ROW LEVEL SECURITY is set on all non-dev tables
- [ ] No GRANT ALL on protected tables
- [ ] Leak test harness runs green against Docker Postgres
- [ ] Migration includes rollback SQL
- [ ] Views use security_invoker = true or are excluded from RLS scope
