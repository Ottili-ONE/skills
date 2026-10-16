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
`scripts/check_rls_migration.py` is the **offline gate** that runs before the Docker harness.
The Docker harness (`scripts/pg-rls-leak-test.sh`, planned) spins up `postgres:19-alpine`,
applies schema + policies, then runs two sessions as different tenants and asserts
cross-tenant reads return zero rows.

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
