-- Additive migration: tax_codes table with RLS, company-scoped, effective dating.
-- company_id is first in every key and index.
--
-- WHY THIS FILE CREATES THE TABLE IT ALTERS. Measured 2026-10-09: the original version of this
-- file was a pure `ALTER TABLE accounting_gl.tax_codes ADD COLUMN ...` run, on the assumption
-- that some earlier migration had created the table. Nothing in the tree does - a search of the
-- whole platform repo and this one turns up no `CREATE TABLE ... tax_codes` at all. On a fresh
-- test schema the ALTER therefore refused with `relation "accounting_gl.tax_codes" does not
-- exist`, and because the runner aborts the whole plan on the first failing file, the two later
-- migrations (trial_balance/ledger_row and the reconciliation tables) never ran either, so the
-- reconciliation DB tests could not run at all.
--
-- The fix is to make the file self-contained: `CREATE TABLE IF NOT EXISTS` carries every column
-- the ALTERs used to add, so the table exists before the first ALTER, the file is idempotent on
-- a schema where it already ran, and it no longer depends on an ordering nobody has documented.
-- It is still additive: it never drops or renames anything, and on a schema where the table
-- already exists with the old column set the `ADD COLUMN IF NOT EXISTS` lines below are no-ops.
CREATE SCHEMA IF NOT EXISTS accounting_gl;

CREATE TABLE IF NOT EXISTS accounting_gl.tax_codes (
    company_id       TEXT        NOT NULL,
    id               TEXT        NOT NULL,
    code             TEXT        NOT NULL,
    name             TEXT,
    kind             TEXT        NOT NULL DEFAULT 'standard',
    rate             NUMERIC(5,2) CHECK (rate >= 0 AND rate <= 100),
    effective_from   DATE        NOT NULL DEFAULT '1970-01-01',
    effective_to     DATE,
    state            TEXT        NOT NULL DEFAULT 'draft',
    created_by       TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (company_id, id)
);

-- Idempotent additions for schemas where the table pre-existed without these columns.
ALTER TABLE accounting_gl.tax_codes ADD COLUMN IF NOT EXISTS kind TEXT NOT NULL DEFAULT 'standard';
ALTER TABLE accounting_gl.tax_codes ADD COLUMN IF NOT EXISTS rate NUMERIC(5,2) CHECK (rate >= 0 AND rate <= 100);
ALTER TABLE accounting_gl.tax_codes ADD COLUMN IF NOT EXISTS effective_from DATE NOT NULL DEFAULT '1970-01-01';
ALTER TABLE accounting_gl.tax_codes ADD COLUMN IF NOT EXISTS effective_to DATE;
ALTER TABLE accounting_gl.tax_codes ADD COLUMN IF NOT EXISTS state TEXT NOT NULL DEFAULT 'draft';
ALTER TABLE accounting_gl.tax_codes ADD COLUMN IF NOT EXISTS created_by TEXT;
ALTER TABLE accounting_gl.tax_codes ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

COMMENT ON COLUMN accounting_gl.tax_codes.kind IS 'standard|reduced|zero|reverse_charge_13b|small_business_19|intra_eu|oss_cross_border_b2c';
COMMENT ON COLUMN accounting_gl.tax_codes.state IS 'draft|active|superseded (terminal)';

CREATE INDEX IF NOT EXISTS idx_taxcodes_co_kind_state_eff ON accounting_gl.tax_codes (company_id, kind, state, effective_from DESC);
CREATE INDEX IF NOT EXISTS idx_taxcodes_co_state_eff ON accounting_gl.tax_codes (company_id, state, effective_from);

-- RLS: enforce company isolation on tax_codes if not already enabled for the table.
DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'tax_codes' AND policyname = 'company_isolation') THEN ALTER TABLE accounting_gl.tax_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE accounting_gl.tax_codes FORCE ROW LEVEL SECURITY; END IF; END $$;
DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'tax_codes' AND policyname = 'taxcodes_company_access') THEN CREATE POLICY taxcodes_company_access ON accounting_gl.tax_codes USING (company_id = current_setting('app.company_id', true)) WITH CHECK (company_id = current_setting('app.company_id', true)); END IF; END $$;

