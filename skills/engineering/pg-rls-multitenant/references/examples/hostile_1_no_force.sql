-- HOSTILE 1: table with RLS but NO FORCE, policy keyed on the legacy GUC.
CREATE TABLE IF NOT EXISTS hostile_notes (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id text        NOT NULL,
    body       text        NOT NULL
);

CREATE POLICY hostile_notes_tenant ON hostile_notes
  FOR SELECT TO web_app
  USING (company_id = current_setting('app.current_company', true));

ALTER TABLE hostile_notes ENABLE ROW LEVEL SECURITY;
-- no FORCE ROW LEVEL SECURITY: owner/migration role bypasses RLS.
