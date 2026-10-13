---
name: pg-rls-multitenant
description: "Enforces Postgres row-level security for multi-tenant Ottili workloads: tenant-key-first design, FORCE RLS, expand/contract migrations, and automated leak tests that fail on policy gaps. Use when adding a tenant-isolated table or view, reviewing tenant_id/organization_id/namespace columns for missing RLS, or investigating 'user X saw user Y's data' incidents."
license: MIT-compat
compatibility: "PostgreSQL 15+ (verified 18); framework-agnostic"
metadata: {}
allowed-tools: []
---
# PG RLS Multitenant Skill — Quick Reference (body <500 lines; full procedure in references/pg-rls-procedure.md)

## When to use this skill (trigger)
Any of these fires it:
- Adding a new tenant-isolated table or view to an Ottili schema.
- A code review mentions `tenant_id`, `organization_id`, or `namespace` columns without RLS.
- A migration adds a column that becomes the tenant discriminator.
- An incident report says "user X saw user Y's data".
- Reviewing Supabase, Hasura, Prisma, or direct SQL for missing RLS.

## When NOT to use this skill
- Single-tenant databases (no tenant discriminator needed).
- Read-only analytics replicas where RLS is enforced upstream.
- Tables that intentionally share rows across tenants (e.g., global config) — mark them `bypassrls` explicitly instead of omitting policies.

## Decision table — tenant key strategy
| Pattern | When to pick | Pitfall |
|---------|-------------|---------|
| `tenant_id` column on every row table | Default; works with any ORM | Must be NOT NULL; FK from shared tables |
| JWT claim `tenant_id` via `current_setting('app.current_tenant')` | Serverless / connection-pool reuse | Claim must be set per-request, never cached globally |
| Security-definer lookup function (`current_tenant()`) | Complex hierarchies (org > team > user) | Function must be IMMUTABLE false; test for SQL injection |

## Near-miss triggers (act before the incident)
- A table is created by a migration role and has no FORCE RLS → that role's sessions see all tenants' rows.
- A view is created without `security_invoker = true` → it runs as the view owner and bypasses RLS.
- `GRANT ALL` appears on a protected table → silently overrides the policy grant.
- `service_role` is used in client-side code → bypasses every RLS policy by design.
- A policy uses a sub-select on the same table → the check-then-insert race leaks rows under concurrent load.
- A migration adds the tenant column AFTER data exists, with no backfill → old rows have NULL tenant_id and match no policy (silent exclusion, not a leak, but a data-loss trap).

## Numbered procedure (summary; full recipe in references/pg-rls-procedure.md)
1. **Choose tenant key** — column preferred; document the choice in the migration comment.
2. **CREATE POLICY** per role-permission combination; use PERMISSIVE for additive rules, RESTRICTIVE for deny overrides.
3. **ALTER TABLE ... ENABLE ROW LEVEL SECURITY** then **FORCE ROW LEVEL SECURITY** on every non-dev table (dev tables get NO FORCE with a comment).
4. **Grant SELECT only** — never GRANT ALL on RLS-protected tables; service_role bypasses RLS so restrict it in Supabase/Postgres auth layer separately.
5. **Expand/contract migration**: add column → backfill → add policy → verify leak test → contract old data later via separate migration with rollback SQL in same file.
6. **Run the leak test** against a real Postgres Docker image before merge; expect all PASS or block merge. The harness is a two-session script (one per tenant) that asserts cross-tenant reads return zero rows; `scripts/check_rls_migration.py` is the offline gate that runs before the Docker harness.

## Worked examples
Good (permissive policy + FORCE + scoped grant):
```sql
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders FORCE ROW LEVEL SECURITY;
CREATE POLICY orders_tenant_select ON orders
  FOR SELECT
  USING (tenant_id = current_setting('app.current_tenant')::uuid);
GRANT SELECT ON orders TO app_anon;
```
Bad (owner bypass — table created by migration role, no FORCE):
```sql
CREATE TABLE notes (id uuid, tenant_id uuid, body text);
-- migration role can read every tenant's notes until FORCE is added
```
Bad (view bypass):
```sql
CREATE VIEW active_orders AS SELECT * FROM orders;
-- runs as view owner; RLS on orders is skipped
```

## Pitfalls from research (real incidents)
- Owner bypasses RLS unless FORCE is set — a table created by a migration role silently exposes rows to that role's sessions.
- Views are security-definer by default and bypass RLS unless `security_invoker = true`.
- Missing GRANT before policy → error 42501 before any policy runs.
- `service_role` key bypasses all RLS — never use it client-side.
- Sub-select race condition between policy evaluation and INSERT can leak rows under concurrent load.

## Verification checklist (all must pass before merge)
- [ ] Every row table has at least one policy matching its tenant column
- [ ] FORCE ROW LEVEL SECURITY is set on all non-dev tables
- [ ] No GRANT ALL on protected tables
- [ ] Leak test harness runs green against Docker Postgres
- [ ] Migration includes rollback SQL
- [ ] Views use security_invoker = true or are excluded from RLS scope

## Related skills
- [outbox-idempotency](../outbox-idempotency/SKILL.md)
- [problem-json-contracts](../problem-json-contracts/SKILL.md)
