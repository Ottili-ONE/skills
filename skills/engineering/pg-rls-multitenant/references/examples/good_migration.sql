-- GOOD example: the product standard (verified 2026-10-16 against hq-v2).
-- The tenant discriminator column is `company_id` and the RLS policy is keyed on
-- the single GUC the product repos use: `current_setting('app.company_id', true)`.
-- See docs/truth/REPAIR_LOG.md for the GUC decision and the evidence counts.

CREATE TABLE IF NOT EXISTS tenant_isolated_notes (
    id           uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id   text        NOT NULL,
    body         text        NOT NULL,
    created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE POLICY tenant_isolation ON tenant_isolated_notes
    AS PERMISSIVE
    FOR SELECT
    TO web_app
    USING (company_id = current_setting('app.company_id', true));

CREATE POLICY tenant_write ON tenant_isolated_notes
    AS PERMISSIVE
    FOR INSERT
    TO web_app
    WITH CHECK (company_id = current_setting('app.company_id', true));

ALTER TABLE tenant_isolated_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_isolated_notes FORCE ROW LEVEL SECURITY;

GRANT SELECT, INSERT ON tenant_isolated_notes TO web_app;

-- ROLLBACK
-- DROP POLICY IF EXISTS tenant_isolation ON tenant_isolated_notes;
-- DROP POLICY IF EXISTS tenant_write ON tenant_isolated_notes;
-- DROP TABLE IF EXISTS tenant_isolated_notes;
