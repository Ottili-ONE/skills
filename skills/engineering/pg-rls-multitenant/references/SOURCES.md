# pg-rls-multitenant — SOURCES

All retrievals: 2026-10-07. Host: Biest. SEARCH_ENDPOINT none (search results were pointers only; the URLs below were fetched directly).

## Primary sources

1. PostgreSQL 18 docs, "5.9. Row Security Policies" — https://www.postgresql.org/docs/current/ddl-rowsecurity.html (HTTP 200, retrieved 2026-10-07).
   Used for: ENABLE/ALTER TABLE ... FORCE ROW LEVEL SECURITY; permissive (OR) vs restrictive (AND) policy combination; table-owner bypass; WITH CHECK semantics; sub-SELECT race conditions; `row_security` config parameter; referential-integrity bypass and covert channels.
2. PostgreSQL 18 docs, CREATE POLICY — https://www.postgresql.org/docs/current/sql-createpolicy.html (HTTP 200, retrieved 2026-10-07).
   Used for: exact syntax of `CREATE POLICY name ON table [AS {PERMISSIVE | RESTRICTIVE}] [TO role...] [USING (expr)] [WITH CHECK (expr)]`; default role is PUBLIC; FOR ALL / SELECT / INSERT / UPDATE / DELETE scoping.
3. PostgreSQL 18 docs, ALTER POLICY — https://www.postgresql.org/docs/current/sql-alterpolicy.html (HTTP 200, retrieved 2026-10-07).
   Used for: renaming policies and changing `USING`/`WITH CHECK` expressions in place — the primitive behind "expand/contract" migrations.
4. PostgreSQL 18 docs, DROP POLICY — https://www.postgresql.org/docs/current/sql-droppolicy.html (HTTP 200, retrieved 2026-10-07).
   Used for: `DROP POLICY ... ON table CASCADE` behaviour and the "policy must not silently vanish" rule.
5. PostgreSQL 18 docs, ALTER TABLE — https://www.postgresql.org/docs/current/sql-altertable.html (HTTP 200, retrieved 2026-10-07).
   Used for: `ENABLE ROW LEVEL SECURITY`, `DISABLE ROW LEVEL SECURITY`, `FORCE ROW LEVEL SECURITY`, `NO FORCE ROW LEVEL SECURITY`, and the fact that these are owner-only privileges.
6. Supabase docs, "Row Level Security" — https://supabase.com/docs/guides/auth/row-level-security (HTTP 200, retrieved 2026-10-07).
   Used for: grant-vs-policy ordering (missing grant → 42501 before any policy runs), `service_role` bypass, `auth.uid()` returning NULL when unauthenticated, views bypassing RLS by default, `set local request.jwt.claim.sub` for testing, and the pgTAP `results_eq`/`is_empty`/`throws_ok` testing idiom.

## Version-sensitive facts

- Postgres 18 is the current stable line at retrieval time; `FORCE ROW LEVEL SECURITY` has existed since 9.5 and is unchanged. No version bump expected for the RLS feature set.
- Supabase changed its key model in 2025: the JWT-based `service_role` key is legacy; a "secret key" is preferred. The `service_role` Postgres role still has `bypassrls`. This is a Supabase-specific fact, not a Postgres one — do not state it as Postgres behaviour.

## Conflicts / open questions

- Supabase docs say a view "is usually created with the postgres user" and therefore bypasses RLS; the underlying Postgres rule is that views are `security definer` by default and inherit the creator's privileges. Both are consistent — the Supabase text is a special case of the Postgres rule. Recorded so the skill does not treat the Supabase phrasing as a separate mechanism.
- Whether the table owner bypasses RLS is the default but can be changed with `FORCE ROW LEVEL SECURITY`. The skill therefore states "owner bypasses unless FORCE is set", not "owner always bypasses".

## What this skill does better than existing public skills

- Existing: Supabase's own RLS guide and the Postgres manual are reference material, not agents. Community agent skills for RLS are thin and almost all assume Supabase's `auth.uid()` helper.
- Difference: this skill is framework-agnostic, treats the tenant key as a *first-class design decision* (column, JWT claim, or security-definer lookup), mandates `FORCE ROW LEVEL SECURITY` for anything that is not a dev-only table, gives an expand/contract migration recipe with rollback, and ships a deterministic leak-test harness that runs against a real Postgres (or Docker image) with PASS/FAIL assertions rather than prose advice.
