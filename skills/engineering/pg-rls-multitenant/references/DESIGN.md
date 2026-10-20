# DESIGN — pg-rls-multitenant

## Trigger description (draft)
Fires when: an agent writes or reviews a Postgres migration for a tenant-scoped table; when
auditing a schema for cross-tenant leaks; when choosing a tenant-key strategy (`app.company_id`
vs JWT claim vs subquery); when a migration adds or removes a tenant discriminator; or when a
test reports a possible RLS bypass. Does NOT fire for: single-tenant internal tables with no
Pii, or non-Postgres databases.

## What it does better than existing public skills
Postgres docs and Supabase docs explain RLS as a feature; they do not give the Ottili
decision procedure. This skill fixes the tenant-key-first rule (set the key in the session
*before* any policy runs, or the policy sees NULL and denies), the expand/contract migration
shape (add column with backfill default → add policy → leak test → contract), the `FORCE ROW
LEVEL SECURITY` requirement (without it the table owner bypasses RLS and every audit fails),
the `GRANT SELECT` (never ALL) rule, and the leak-test recipe with two database roles. It also
records the real incident: a `security_invoker` view that was *not* marked as such leaked
tenant rows to a reporting role, because the migration omitted the invoker flag.

## Procedure outline
1. Every tenant-scoped table gets `company_id <type> NOT NULL`, an index on `company_id`, and
   `ENABLE ROW LEVEL SECURITY` + `FORCE ROW LEVEL SECURITY` in the same migration.
2. The tenant key is set first: `SELECT set_config('app.company_id', '<id>', true)` in the
   session; policies read `current_setting('app.company_id')`.
3. Policy shape: `CREATE POLICY ... ON table FOR SELECT USING (company_id =
   current_setting('app.company_id')::uuid)`; permissive for SELECT, restrictive for write
   if write-scoping is needed.
4. Grants: `GRANT SELECT` only (never ALL); the app role gets SELECT, the owner keeps DDL.
5. Expand/contract: adding a tenant column is an expand migration (add NOT NULL with backfill,
   add policy, run leak test) followed by a contract migration that drops the old key.
6. Leak test: run `scripts/pg-rls-leak-test.sh --server` against a real PostgreSQL. The probe
   runs as a non-superuser application role and reports four measurements: `a_sees_own = 1`
   (the company sees its own row), `a_sees_b = 0` (it sees no row of another company) and
   `unset_sees_rows = 0` (nobody sees a row while the session carries no company) and
   `write_leaks = 0` (a row of another company was refused).
7. Views: mark `security_invoker` explicitly; an unmarked view inherits the creator's privileges
   and bypasses RLS.

## Scripts (shipped)
- `scripts/check_rls_migration.py` — the adapter: reads the migration files, applies the rules
   of the `ottili_rls` package and prints the verdict; exits 0/1/2. Self-tested via
   `check_rls_migration_test.py`.
- `scripts/ottili_rls/` — the core: the data model (`models.py`), the reader of the tenant
   convention (`convention.py`), the SQL scanner (`scanner.py`), the rules (`rules.py`), the
   judgement of a probe output (`leak.py`) and the structured run log (`logging.py`). Every
   part of it is pure and typed; the I/O lives in the adapters.
- `scripts/pg-rls-leak-test.sh` — the leak harness: applies a migration to a real PostgreSQL
   (`--server`) or to a throwaway container, seeds two companies and probes the table as the
   application role.
- `scripts/check_leak_probe.py` — the judge of a probe output: PASS only when the three
   measurements are 1, 0 and 0.

## Five eval prompts
1. "Add a `notes` table for the workspace tenant." → migration must include `company_id`, policy,
   `ENABLE` + `FORCE`, `GRANT SELECT`, and a rollback block.
2. "A migration adds `organization_id` to `projects`." → agent treats it as an expand
   migration: add with backfill, add policy, leak test, contract later.
3. "The table owner can see all tenants." → agent sets `FORCE ROW LEVEL SECURITY`; without it
   the owner bypass is legal but an audit finding.
4. "Review this migration for RLS compliance." → agent runs `scripts/check_rls_migration.py` and
   fixes every finding; prose reassurance is not accepted.
5. "We use Supabase; keep `service_role` in the client?" → agent states `service_role` bypasses
   RLS and must never reach client code; records it as Supabase-specific.
