#!/usr/bin/env bash
# pg-rls-leak-test.sh - Docker Postgres leak-test harness for tenant-isolated tables.
# Usage: ./pg-rls-leak-test.sh <path-to-sql-migration-or-schema>
# Spins up postgres:18-alpine, applies the SQL, seeds two tenants as superuser,
# then runs the probe AS the app role (web_app) with the tenant key set in the
# session and asserts cross-tenant reads return ZERO rows. Any FAIL blocks merge.
set -euo pipefail

SQL_FILE="${1:-}"
if [[ -z "$SQL_FILE" || ! -f "$SQL_FILE" ]]; then
  echo "usage: $0 <migration.sql>" >&2
  exit 2
fi

IMAGE="postgres:18-alpine"
CONTAINER="pg-rls-leak-$$"
TMPD="$(mktemp -d)"
cleanup() {
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  rm -rf "$TMPD"
}
trap cleanup EXIT

echo ">> pulling $IMAGE (skip if cached)"
docker pull "$IMAGE" >/dev/null 2>&1 || true

echo ">> starting Postgres"
docker run --rm --name "$CONTAINER" -e POSTGRES_PASSWORD=secret \
  -e POSTGRES_USER=postgres -d "$IMAGE" >/dev/null

for i in $(seq 1 30); do
  if docker exec "$CONTAINER" pg_isready -U postgres >/dev/null 2>&1; then break; fi
  sleep 1
done

echo ">> applying schema + policies"
docker exec -i "$CONTAINER" psql -U postgres -d postgres -v ON_ERROR_STOP=1 \
  -f - < "$SQL_FILE" 2>&1 | tail -20

cat > "$TMPD/probe.sql" <<'PROBE'
-- app role (the migration grants SELECT to this role; missing role == missing grant)
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'web_app') THEN
    CREATE ROLE web_app NOLOGIN;
  END IF;
END
$$;

GRANT CONNECT ON DATABASE postgres TO web_app;
GRANT USAGE ON SCHEMA public TO web_app;

-- Seed two tenants as the superuser (bypasses RLS by design, so seeding is safe).
\set ON_ERROR_STOP off
INSERT INTO tenant_isolated_notes (id, tenant_id, body)
VALUES ('00000000-0000-4000-8000-000000000001',
        '11111111-1111-4111-8111-111111111111', 'A row') ON CONFLICT DO NOTHING;
INSERT INTO tenant_isolated_notes (id, tenant_id, body)
VALUES ('00000000-0000-4000-8000-000000000002',
        '22222222-2222-4222-8222-222222222222', 'B row') ON CONFLICT DO NOTHING;
\set ON_ERROR_STOP on

-- Re-grant so the policy applies even if the migration already granted.
GRANT SELECT ON tenant_isolated_notes TO web_app;

-- Run the probe AS the app role with the tenant key set in the session.
-- This is exactly what the application does; RLS policies read current_setting.
SELECT set_config('app.current_tenant',
  '11111111-1111-4111-8111-111111111111', true);
SELECT count(*) AS a_sees_own FROM tenant_isolated_notes;
SELECT count(*) AS a_sees_b FROM tenant_isolated_notes
WHERE tenant_id = '22222222-2222-4222-8222-222222222222';
PROBE

echo ">> running probe as web_app"
OUT=$(docker exec -i "$CONTAINER" psql -U web_app -d postgres -t -A -F $'\t' \
  -v ON_ERROR_STOP=1 -f "$TMPD/probe.sql" 2>&1 || true)

OWN=$(echo "$OUT" | grep "a_sees_own" | tail -1 | cut -f2)
CROSS=$(echo "$OUT" | grep "a_sees_b" | tail -1 | cut -f2)

echo "   tenant A sees own rows : ${OWN:-?}"
echo "   tenant A sees tenant B : ${CROSS:-?}"

PASS=1
if [[ "${OWN:-0}" != "1" ]]; then echo "FAIL: same-tenant read wrong ($OWN)"; PASS=0; fi
if [[ "${CROSS:-0}" != "0" ]]; then echo "FAIL: cross-tenant leak ($CROSS)"; PASS=0; fi

if [[ $PASS -eq 1 ]]; then
  echo "PASS: RLS leak test green"
  exit 0
else
  echo "FAIL: RLS leak test - block merge"
  exit 1
fi
