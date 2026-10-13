#!/usr/bin/env bash
# pg-rls-leak-test.sh -- real Postgres leak-test harness for pg-rls-multitenant.
#
# Spins up postgres:18-alpine in Docker, applies a migration file, then runs two
# sessions as different tenants and asserts that cross-tenant reads return zero
# rows. Any FAIL blocks merge; this is the live counterpart of the offline gate
# scripts/check_rls_migration.py.
#
# Usage:
#   ./pg-rls-leak-test.sh <migration.sql> [--table NAME] [--image NAME]
# Exit 0 = all assertions PASS; 1 = a leak or infra failure; 2 = usage error.
set -euo pipefail

TABLE="tenant_isolated_notes"
IMAGE="postgres:18-alpine"
MIGRATION=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --table) TABLE="$2"; shift 2 ;;
    --image) IMAGE="$2"; shift 2 ;;
    -*) echo "unknown option: $1" >&2; exit 2 ;;
    *)  MIGRATION="$1"; shift ;;
  esac
done

if [[ -z "$MIGRATION" ]]; then
  echo "usage: $0 <migration.sql> [--table NAME] [--image NAME]" >&2
  exit 2
fi
MIGRATION="$(realpath "$MIGRATION")"
[[ -f "$MIGRATION" ]] || { echo "migration not found: $MIGRATION" >&2; exit 2; }

WORKDIR="$(mktemp -d)"
cleanup() { docker rm -f pg-rls-leak-test >/dev/null 2>&1 || true; rm -rf "$WORKDIR"; }
trap cleanup EXIT

cp "$MIGRATION" "$WORKDIR/migration.sql"
export RLS_TABLE="$TABLE"

TENANT_A="11111111-1111-4111-8111-111111111111"
TENANT_B="22222222-2222-4222-8222-222222222222"

docker run --rm --name pg-rls-leak-test -e POSTGRES_PASSWORD=pass \
  -d "$IMAGE" >/dev/null

for i in $(seq 1 30); do
  if docker exec pg-rls-leak-test pg_isready -U postgres >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

docker exec pg-rls-leak-test psql -U postgres -c "CREATE ROLE web_app NOLOGIN;" >/dev/null
docker cp "$WORKDIR/migration.sql" pg-rls-leak-test:/tmp/migration.sql
docker exec pg-rls-leak-test psql -U postgres -f /tmp/migration.sql >/dev/null

# Seed rows for both tenants via a superuser session (RLS bypassed for the seed;
# the test is whether the *scoped* sessions can see across tenants).
docker exec pg-rls-leak-test psql -U postgres -tAc \
  "INSERT INTO "${RLS_TABLE}" (id, tenant_id, body) VALUES
     ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', '${TENANT_A}', 'A row'),
     ('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb', '${TENANT_B}', 'B row');" >/dev/null

run_count() {  # $1 = tenant uuid ; prints the row count that tenant can see
  docker exec pg-rls-leak-test psql -U postgres -tAc \
    "DO \$\$ BEGIN PERFORM set_config('app.current_tenant', '$1', true); END \$\$;
     SELECT count(*) FROM "${RLS_TABLE}";" | tr -d '[:space:]'
}

cross_count() {  # $1 = tenant uuid ; count of rows whose tenant_id differs
  docker exec pg-rls-leak-test psql -U postgres -tAc \
    "DO \$\$ BEGIN PERFORM set_config('app.current_tenant', '$1', true); END \$\$;
     SELECT count(*) FROM "${RLS_TABLE}"
      WHERE tenant_id <> '$1'::uuid;" | tr -d '[:space:]'
}

A_SEEN="$(run_count "$TENANT_A")"
B_SEEN="$(run_count "$TENANT_B")"
A_CROSS="$(cross_count "$TENANT_A")"
B_CROSS="$(cross_count "$TENANT_B")"

fail=0
check() {  # check <label> <actual> <expected>
  if [[ "$2" != "$3" ]]; then
    echo "FAIL: $1 -- got '$2', expected '$3'" >&2
    fail=1
  else
    echo "ok: $1 -- '$2'"
  fi
}

check "tenant A sees its own row"         "$A_SEEN"  "1"
check "tenant B sees its own row"         "$B_SEEN"  "1"
check "tenant A sees zero rows of tenant B" "$A_CROSS" "0"
check "tenant B sees zero rows of tenant A" "$B_CROSS" "0"

if [[ $fail -ne 0 ]]; then
  echo "LEAK DETECTED -- block merge" >&2
  exit 1
fi
echo "all leak-test assertions passed"
exit 0
