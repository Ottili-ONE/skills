# pg-rls-multitenant — SOURCES

All retrievals: 2026-10-14 (re-verification pass). Host: Biest. SEARCH_ENDPOINT none (search results were pointers only; the URLs below were fetched directly with `curl -L --max-time 20`).

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
6. Supabase docs, "Row Level Security" — https://supabase.com/docs/guides/database/postgres/row-level-security (HTTP 200, re-verified 2026-10-14; the old `/guides/auth/row-level-security` path 308-redirects to the `/guides/database/postgres/` path).
   Used for: grant-vs-policy ordering (missing grant → 42501 before any policy runs), `service_role` bypass, `auth.uid()` returning NULL when unauthenticated, views bypassing RLS by default, `set local request.jwt.claim.sub` for testing, and the pgTAP `results_eq`/`is_empty`/`throws_ok` testing idiom.

## Version-sensitive facts

- Postgres 18 is the current stable line, specifically **18.6** (re-verified 2026-10-14 against `https://www.postgresql.org/docs/18/`); `FORCE ROW LEVEL SECURITY` has existed since 9.5 and is unchanged. No version bump expected for the RLS feature set.
- Supabase changed its key model in 2025: the JWT-based `service_role` key is legacy; a "secret key" is preferred. The `service_role` Postgres role still has `bypassrls`. This is a Supabase-specific fact, not a Postgres one — do not state it as Postgres behaviour.

## Conflicts / open questions

- Supabase docs say a view "is usually created with the postgres user" and therefore bypasses RLS; the underlying Postgres rule is that views are `security definer` by default and inherit the creator's privileges. Both are consistent — the Supabase text is a special case of the Postgres rule. Recorded so the skill does not treat the Supabase phrasing as a separate mechanism.
- Whether the table owner bypasses RLS is the default but can be changed with `FORCE ROW LEVEL SECURITY`. The skill therefore states "owner bypasses unless FORCE is set", not "owner always bypasses".

## What this skill does better than existing public skills

- Existing: Supabase's own RLS guide and the Postgres manual are reference material, not agents. Community agent skills for RLS are thin and almost all assume Supabase's `auth.uid()` helper.
- Difference: this skill is framework-agnostic, treats the tenant key as a *first-class design decision* (column, JWT claim, or security-definer lookup), mandates `FORCE ROW LEVEL SECURITY` for anything that is not a dev-only table, gives an expand/contract migration recipe with rollback, and ships a deterministic leak-test harness that runs against a real Postgres (or Docker image) with PASS/FAIL assertions rather than prose advice.

## Re-verification (2026-10-14)
All primary URLs above were re-fetched with `curl -L --max-time 20` on 2026-10-14: HTTP 200 for every one. The `ddl-rowsecurity` page (owner-bypass, FORCE RLS, WITH CHECK, sub-SELECT race, covert channels) is live at the current-docs path; the older `ddl-rls.html` path 404s and must not be linked. The docs landing page reports PostgreSQL 18.6 as the current stable line.

## Dead / moved URLs (recorded 2026-10-13)
The following URLs from earlier passes no longer resolve and must not be linked:
- `https://www.postgresql.org/docs/current/ddl-rls.html` — 404; the canonical path is `ddl-rowsecurity.html`.
- `https://kafka.apache.org/documentation/producersemantics.html` — 404 as of 2026-10-13; re-confirmed 404 on 2026-10-14. Kafka's at-least-once / idempotent-producer semantics are now documented under the general Kafka documentation index; the specific page moved. The outbox skill records this and points at the Kafka documentation index rather than a stale path.
- `https://martinfowler.com/articles/transactional_outbox.html` — 404 as of 2026-10-13; re-confirmed 404 on 2026-10-14. The canonical article is reachable via the Martin Fowler site index; link to the site root or the bliki tag page and treat the article as the authoritative *description* (write business data and outbox row in one transaction; a relay publishes outbox rows asynchronously), not as a live URL to cite.
- `https://developers.cloudflare.com/workers/runtime-apis/http/` — 404 as of 2026-10-13. The Workers runtime docs index is live at `/workers/runtime-apis/`; the HTTP-specific subsection was restructured. Retry-after behaviour is verified against RFC 7231 §7.1.2 instead.

## Additional primary sources (verified 2026-10-13)
7. PostgreSQL 18 docs, GRANT — https://www.postgresql.org/docs/current/sql-grant.html — 200. `GRANT ALL ON ALL TABLES IN SCHEMA` and per-table grant forms; confirms that a bare `GRANT ALL` on a protected table silently overrides the scoped SELECT grant and defeats the policy.
8. PostgreSQL 18 docs, CREATE VIEW — https://www.postgresql.org/docs/current/sql-createview.html — 200. `security_invoker = true` makes the view run with the invoking user's privileges (RLS applies); the default is `security_definer` (view owner, RLS bypassed). This is the exact primitive behind the view rule in the skill.
9. PostgreSQL 18 docs, REVOKE — https://www.postgresql.org/docs/current/sql-revoke.html — 200. Revoke-only contract for the "contract old data later" step of expand/contract migrations.
10. PostgreSQL 18 docs, runtime config — https://www.postgresql.org/docs/current/runtime-config-connection.html — 200. `row_security` GUC (default on) and `current_setting('app.current_tenant')` semantics for the JWT-claim tenant-key strategy.

## Version-sensitive facts (re-verified 2026-10-13)
- Postgres 18 is the current stable line; `FORCE ROW LEVEL SECURITY` unchanged since 9.5.
- Supabase key model changed in 2025: JWT `service_role` key is legacy, a "secret key" is
  preferred. The `service_role` Postgres role still has `bypassrls`. Supabase-specific fact;
  do not state it as Postgres behaviour.
