# pg-rls-multitenant — EVALS

Each prompt is a realistic request an agent would receive. Expected behaviour shows what the skill should produce; failure signs show what would indicate the skill did not fire or misfired.

## 1. "Add a `notes` table to the Ottili workspace schema. Each workspace is a tenant."
- Expected: SKILL.md fires. Agent writes a migration with `tenant_id uuid NOT NULL`, a permissive SELECT policy keyed on `current_setting('app.current_tenant')`, `ENABLE` + `FORCE ROW LEVEL SECURITY`, `GRANT SELECT` (never ALL), and a `-- ROLLBACK` block. It links `references/pg-rls-procedure.md` for the full recipe.
- Failure signs: no `tenant_id` column; `FORCE ROW LEVEL SECURITY` absent; `GRANT ALL`; no rollback block; agent invents a shared-table policy instead of marking the table bypassrls.
**What the skill changes vs no skill**: without the skill a table is created by the migration role with no FORCE RLS and that role's sessions see every tenant's rows, or a security-definer view silently bypasses the policy. The skill makes tenant-key-first design, FORCE RLS, `security_invoker` views and automated leak tests the gate, so a missing policy is a FAIL, not a footnote.

## 2. "A migration adds an `organization_id` column to `projects`. Is this safe?"
- Expected: Agent treats the new column as a tenant discriminator. It writes an expand migration: add column NOT NULL with backfill default, add the policy, run the leak test, then contract old data in a follow-up migration. It checks the existing policy references `organization_id` and updates it.
- Failure signs: agent adds the column but leaves the old policy referencing a different key, or adds the column nullable, or skips the leak test.
**What the skill changes vs no skill**: without the skill a table is created by the migration role with no FORCE RLS and that role's sessions see every tenant's rows, or a security-definer view silently bypasses the policy. The skill makes tenant-key-first design, FORCE RLS, `security_invoker` views and automated leak tests the gate, so a missing policy is a FAIL, not a footnote.

## 3. "User A reports seeing User B's row in `tenant_isolated_notes`."
- Expected: Agent opens `references/pg-rls-procedure.md`, runs the leak test harness against a Docker Postgres, and inspects for: missing FORCE RLS (owner bypass), a view with `security_invoker=false`, a missing GRANT (error 42501), or the sub-select race. It reproduces the leak with two parallel sessions.
- Failure signs: agent only reads the code, never runs the harness, or blames the application layer without checking `FORCE ROW LEVEL SECURITY`.
**What the skill changes vs no skill**: without the skill a table is created by the migration role with no FORCE RLS and that role's sessions see every tenant's rows, or a security-definer view silently bypasses the policy. The skill makes tenant-key-first design, FORCE RLS, `security_invoker` views and automated leak tests the gate, so a missing policy is a FAIL, not a footnote.

## 4. "Review this migration for RLS compliance."
- Expected: Agent runs `scripts/check_rls_migration.py` on the file. It reports PASS or lists concrete findings (missing tenant column, missing policy, no FORCE, GRANT ALL, no rollback, view without security_invoker). It fixes each finding inside the migration.
- Failure signs: agent gives prose reassurance without running the checker, or the checker returns ok on a file that clearly violates the rules.
**What the skill changes vs no skill**: without the skill a table is created by the migration role with no FORCE RLS and that role's sessions see every tenant's rows, or a security-definer view silently bypasses the policy. The skill makes tenant-key-first design, FORCE RLS, `security_invoker` views and automated leak tests the gate, so a missing policy is a FAIL, not a footnote.

## 5. "We use Supabase. Should we keep using `service_role` in the client?"
- Expected: Agent states `service_role` bypasses RLS entirely and must never reach client code; it recommends the Supabase secret-key model and a server-side RPC for privileged writes. It records this as Supabase-specific, not Postgres behaviour.
- Failure signs: agent says `service_role` is fine for client use, or treats the Supabase key model as a Postgres feature.
**What the skill changes vs no skill**: without the skill a table is created by the migration role with no FORCE RLS and that role's sessions see every tenant's rows, or a security-definer view silently bypasses the policy. The skill makes tenant-key-first design, FORCE RLS, `security_invoker` views and automated leak tests the gate, so a missing policy is a FAIL, not a footnote.

## Worked examples

**Good migration** (every clause present, checker passes):
```sql
CREATE TABLE tenant_isolated_notes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES workspaces(id),
  body text NOT NULL
);
ALTER TABLE tenant_isolated_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_isolated_notes FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON tenant_isolated_notes
  FOR ALL USING (tenant_id = current_setting('app.current_tenant')::uuid);
GRANT SELECT, INSERT, UPDATE ON tenant_isolated_notes TO app_role;
-- ROLLBACK: DROP TABLE tenant_isolated_notes;
```
**Bad migration** (owner sees every tenant; the checker flags it):
```sql
CREATE TABLE tenant_isolated_notes (id uuid PRIMARY KEY, body text);
-- no tenant_id, no policy, no FORCE RLS, no GRANT, no rollback
```
**Good leak-test evidence** (two parallel sessions, one row per tenant):
```json
{"tenant_a_rows": 1, "tenant_b_rows": 1, "cross_tenant_rows": 0, "result": "PASS"}
```
**Bad evidence** (checker cannot re-run it):
`"leak test passed"` with no file and no command.

## Near-miss prompts (act before the incident)
- **N1 — "The app connects as the owner and it works."** Answer: no. Owner bypasses RLS silently; always connect as a normal role and re-run the leak test.
- **N2 — "The policy uses `USING (tenant_id = current_setting('app.current_tenant'))` without FORCE."** Answer: no. `ENABLE` alone is not enough; `FORCE ROW LEVEL SECURITY` is mandatory or the owner can still see every row.
- **N3 — "GRANT ALL ON TABLE notes TO app_role."** Answer: no. Grant only the operations the app needs (SELECT/INSERT/UPDATE); `GRANT ALL` also grants TRUNCATE and ownership-style privileges.
- **N4 — "The migration has no rollback block."** Answer: no. Record the inverse DDL in the same file so a failed migration can be reverted without dropping data.
- **N5 — "service_role in the client is fine, it's just a key."** Answer: no. `service_role` bypasses RLS entirely and must never leave the server; use a server-side RPC or the Supabase secret-key model.
- **N6 — "The policy uses `current_setting('app.current_tenant')` and that's good enough."** Answer: no — the setting must be cast to the column type (`::uuid`) and be NOT NULL, or a missing setting yields NULL and the policy matches nothing (silent data loss, not a leak).
- **N7 — "A security_invoker view is slower, so let's skip it."** Answer: no — a security-definer (invoker=false) view runs as the view owner and bypasses the underlying table's policies; use `security_invoker=true` or a plain table.
- **N8 — "The leak test passed on my laptop, that's enough."** Answer: no — run it against Docker Postgres on Biest with two parallel sessions and record the JSON; a laptop run proves nothing about the shared host.
