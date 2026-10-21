-- GOOD example: the product standard (verified 2026-10-16 against hq-v2).
-- The tenant discriminator column is `company_id` and the RLS policy is keyed on
-- the single GUC the product repos use: `current_setting('app.company_id', true)`.
-- See docs/truth/REPAIR_LOG.md for the GUC decision and the evidence counts.
--
-- The file is re-runnable. The table is created with IF NOT EXISTS and the two
-- policies are created inside a DO block that asks pg_policies first - the shape
-- the product migrations use (see the hq accounting_gl migration and the
-- ottili-apps github_issue_link migration). A migration that cannot be applied
-- twice cannot be retried after a failed deployment, and a retry that aborts
-- leaves the schema half migrated.

CREATE TABLE IF NOT EXISTS tenant_isolated_notes (
    id           uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id   text        NOT NULL,
    body         text        NOT NULL,
    created_at   timestamptz NOT NULL DEFAULT now()
);

-- The read path: a company sees its own rows and nothing else. The USING
-- clause names the tenant column, so the row is compared with the company of
-- the session.
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
     WHERE tablename = 'tenant_isolated_notes'
       AND policyname = 'tenant_isolation'
  ) THEN
    CREATE POLICY tenant_isolation ON tenant_isolated_notes
        AS PERMISSIVE
        FOR SELECT
        TO web_app
        USING (company_id = current_setting('app.company_id', true));
  END IF;
END $$;

-- The write path: the WITH CHECK clause names the tenant column, so a company
-- cannot write a row that claims another company. A policy whose USING clause
-- is correct and whose WITH CHECK clause is wide open is a leak - the read
-- path hides every foreign row and the write path lets a foreign row in.
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
     WHERE tablename = 'tenant_isolated_notes'
       AND policyname = 'tenant_write'
  ) THEN
    CREATE POLICY tenant_write ON tenant_isolated_notes
        AS PERMISSIVE
        FOR INSERT
        TO web_app
        WITH CHECK (company_id = current_setting('app.company_id', true));
  END IF;
END $$;

ALTER TABLE tenant_isolated_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_isolated_notes FORCE ROW LEVEL SECURITY;

GRANT SELECT, INSERT ON tenant_isolated_notes TO web_app;

-- ROLLBACK
-- DROP POLICY IF EXISTS tenant_isolation ON tenant_isolated_notes;
-- DROP POLICY IF EXISTS tenant_write ON tenant_isolated_notes;
-- DROP TABLE IF EXISTS tenant_isolated_notes;
