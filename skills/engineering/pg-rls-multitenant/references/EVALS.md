# pg-rls-multitenant — EVALS

Each prompt is a realistic request an agent would receive. Expected behaviour shows what the skill should produce; failure signs show what would indicate the skill did not fire or misfired.

## 1. "Add a `notes` table to the Ottili workspace schema. Each workspace is a tenant."
- Expected: SKILL.md fires. Agent writes a migration with `tenant_id uuid NOT NULL`, a permissive SELECT policy keyed on `current_setting('app.current_tenant')`, `ENABLE` + `FORCE ROW LEVEL SECURITY`, `GRANT SELECT` (never ALL), and a `-- ROLLBACK` block. It links `references/pg-rls-procedure.md` for the full recipe.
- Failure signs: no `tenant_id` column; `FORCE ROW LEVEL SECURITY` absent; `GRANT ALL`; no rollback block; agent invents a shared-table policy instead of marking the table bypassrls.

## 2. "A migration adds an `organization_id` column to `projects`. Is this safe?"
- Expected: Agent treats the new column as a tenant discriminator. It writes an expand migration: add column NOT NULL with backfill default, add the policy, run the leak test, then contract old data in a follow-up migration. It checks the existing policy references `organization_id` and updates it.
- Failure signs: agent adds the column but leaves the old policy referencing a different key, or adds the column nullable, or skips the leak test.

## 3. "User A reports seeing User B's row in `tenant_isolated_notes`."
- Expected: Agent opens `references/pg-rls-procedure.md`, runs the leak test harness against a Docker Postgres, and inspects for: missing FORCE RLS (owner bypass), a view with `security_invoker=false`, a missing GRANT (error 42501), or the sub-select race. It reproduces the leak with two parallel sessions.
- Failure signs: agent only reads the code, never runs the harness, or blames the application layer without checking `FORCE ROW LEVEL SECURITY`.

## 4. "Review this migration for RLS compliance."
- Expected: Agent runs `scripts/check_rls_migration.py` on the file. It reports PASS or lists concrete findings (missing tenant column, missing policy, no FORCE, GRANT ALL, no rollback, view without security_invoker). It fixes each finding inside the migration.
- Failure signs: agent gives prose reassurance without running the checker, or the checker returns ok on a file that clearly violates the rules.

## 5. "We use Supabase. Should we keep using `service_role` in the client?"
- Expected: Agent states `service_role` bypasses RLS entirely and must never reach client code; it recommends the Supabase secret-key model and a server-side RPC for privileged writes. It records this as Supabase-specific, not Postgres behaviour.
- Failure signs: agent says `service_role` is fine for client use, or treats the Supabase key model as a Postgres feature.
