-- HOSTILE 2: FORCE present but no company_id column and no product-GUC policy.
CREATE TABLE IF NOT EXISTS hostile_rows (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id  text        NOT NULL,
    body       text        NOT NULL
);

CREATE POLICY hostile_rows_tenant ON hostile_rows
  FOR SELECT TO web_app
  USING (tenant_id = current_setting('app.current_tenant', true));

ALTER TABLE hostile_rows ENABLE ROW LEVEL SECURITY;
ALTER TABLE hostile_rows FORCE ROW LEVEL SECURITY;
