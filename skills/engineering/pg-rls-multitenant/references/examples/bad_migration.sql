-- BAD example: missing FORCE RLS, no policy, tenant column nullable, GRANT ALL.
CREATE TABLE IF NOT EXISTS bad_notes (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id  uuid,
    body       text
);

CREATE POLICY nothing ON bad_notes FOR SELECT TO web_app USING (true);

ALTER TABLE bad_notes ENABLE ROW LEVEL SECURITY;

GRANT ALL ON bad_notes TO web_app;
