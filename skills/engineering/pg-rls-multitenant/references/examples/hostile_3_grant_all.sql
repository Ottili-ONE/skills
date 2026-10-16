-- HOSTILE 3: the product standard on paper, then GRANT ALL overrides it.
CREATE TABLE IF NOT EXISTS hostile_ledger (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id text        NOT NULL,
    body       text        NOT NULL
);

CREATE POLICY hostile_ledger_tenant ON hostile_ledger
  FOR SELECT TO web_app
  USING (company_id = current_setting('app.company_id', true));

ALTER TABLE hostile_ledger ENABLE ROW LEVEL SECURITY;
ALTER TABLE hostile_ledger FORCE ROW LEVEL SECURITY;

GRANT ALL ON hostile_ledger TO web_app;
