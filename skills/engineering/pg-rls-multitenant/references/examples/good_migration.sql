-- Migration 20261007_001: add tenant_isolated_notes table with RLS.
-- Expand/contract: add column -> backfill -> add policy -> verify leak test -> contract old data later.

CREATE TABLE IF NOT EXISTS tenant_isolated_notes (
    id           uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id    uuid        NOT NULL,
    body         text        NOT NULL,
    created_at   timestamptz NOT NULL DEFAULT now()
);

-- Backfill any pre-existing rows (none expected here; pattern shown for expand).
-- UPDATE tenant_isolated_notes SET tenant_id = '00000000-0000-0000-0000-000000000000'
-- WHERE tenant_id IS NULL;

CREATE POLICY tenant_isolation ON tenant_isolated_notes
    AS PERMISSIVE
    FOR SELECT
    TO web_app
    USING (tenant_id = current_setting('app.current_tenant')::uuid);

CREATE POLICY tenant_write ON tenant_isolated_notes
    AS PERMISSIVE
    FOR INSERT
    TO web_app
    WITH CHECK (tenant_id = current_setting('app.current_tenant')::uuid);

ALTER TABLE tenant_isolated_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_isolated_notes FORCE ROW LEVEL SECURITY;

GRANT SELECT, INSERT ON tenant_isolated_notes TO web_app;

-- ROLLBACK
-- DROP POLICY IF EXISTS tenant_isolation ON tenant_isolated_notes;
-- DROP POLICY IF EXISTS tenant_write ON tenant_isolated_notes;
-- DROP TABLE IF EXISTS tenant_isolated_notes;
