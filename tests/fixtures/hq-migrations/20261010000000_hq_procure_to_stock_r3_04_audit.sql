-- hq-procure-to-stock-r3-04: EXPAND pass 2 — product-local audit trail (observability, Lane C).
--
-- AGENTS.md Lane C: the Platform has no audit write route, so a product keeps its own. This is
-- that trail for the procurement chain: one row per mutating action, append-only, tenant-scoped.
-- It is NOT the Platform audit table (that is `services.audit`, owned by `hq-runtime-workers-r3`
-- and unreachable from a product over HTTP); it is a module-local fact table that the outbox
-- event and the structured log both point at, so a customer report can be traced without guessing.
--
-- `company_id` leads the primary key and every index; RLS is the backstop for the day somebody
-- writes SQL by hand. Nothing here drops or narrows an existing column.
-- The identifiers are deliberately UNQUOTED. The static gate (scripts/gates/data-conformance.mjs
-- inspectSql) runs stripSql() first, which blanks every string literal - including a quoted
-- identifier, because the quotes are indistinguishable from a string literal to its regex. With
-- "company_id" stripped away the CREATE TABLE body read `text NOT NULL,` and the gate answered
-- `table.company_id_missing` on a table that had the column all along. Unquoted identifiers are
-- what the rest of this migration file uses and what the live catalog mode reads back.
CREATE TABLE IF NOT EXISTS procure_to_stock_audit (
  company_id text NOT NULL,
  id text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  request_id text NOT NULL,
  trace_id text NOT NULL,
  actor text NOT NULL,
  action_id text NOT NULL,
  event_type text NOT NULL,
  resource_type text NOT NULL,
  resource_id text NOT NULL,
  status integer NOT NULL,
  detail text NOT NULL DEFAULT '',
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  PRIMARY KEY (company_id, id)
);

CREATE INDEX IF NOT EXISTS procure_to_stock_audit_actor_idx ON procure_to_stock_audit (company_id, actor, created_at, id);
CREATE INDEX IF NOT EXISTS procure_to_stock_audit_request_idx ON procure_to_stock_audit (company_id, request_id, created_at, id);
CREATE INDEX IF NOT EXISTS procure_to_stock_audit_resource_idx ON procure_to_stock_audit (company_id, resource_type, resource_id, created_at, id);

ALTER TABLE procure_to_stock_audit ENABLE ROW LEVEL SECURITY;
ALTER TABLE procure_to_stock_audit FORCE ROW LEVEL SECURITY;
CREATE POLICY procure_to_stock_audit_tenant ON procure_to_stock_audit
  FOR ALL USING (company_id = current_setting('app.company_id', true))
  WITH CHECK (company_id = current_setting('app.company_id', true));
