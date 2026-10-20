#!/usr/bin/env bash
# pg-rls-leak-test.sh - leak-test harness for tenant-isolated tables.
#
# It applies a migration to a PostgreSQL server, seeds two tenants as the
# superuser (the superuser bypasses RLS by design, so seeding cannot leak),
# then runs the probe AS the application role with the tenant key set in the
# session and asserts three measurements:
#
#   a_sees_own       = 1   the tenant sees its own row
#   a_sees_b         = 0   the tenant sees no row of another tenant
#   unset_sees_rows  = 0   nobody sees a row while the session carries no tenant
#
# Two servers are supported:
#
#   --server  a PostgreSQL that already runs: the truth-kit database of this
#             job, or any server the caller names. This is the mode the
#             committed tests use, because it needs no container runtime.
#   docker   a throwaway PostgreSQL 18 container (default when neither
#             --server nor --job is given).
#
# Usage:
#   pg-rls-leak-test.sh <migration.sql> [table] [options]   # needs Docker
#   pg-rls-leak-test.sh --server <migration.sql> [table]     # needs a server
#   pg-rls-leak-test.sh --print-probe-sql <migration.sql>   # no server
#   pg-rls-leak-test.sh --parse <probe-output-file>         # no server
#
# Options:
#   --guc NAME        set only this tenant GUC (default: the canonical one)
#   --guc-names FILE  JSON file with the tenant convention
#   --image IMAGE     docker image to run (default postgres:18-alpine)
#   --columns LIST    columns of the seeded row (default id,company_id,body)
#   --admin-url URL   superuser URL of the server (server mode)
#   --app-url URL     URL of the application login role (server mode)
#   --app-role NAME   role the probe switches to (default web_app)
#   --job ID          truth-kit job whose database is used (server mode)
#   --reset           drop the probe table if it already exists (server mode)
#   --print-probe-sql print the probe SQL and exit
#   --parse FILE      judge an already captured probe output and exit
#
# Exit 0 = PASS, 1 = FAIL, 2 = usage error.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$SKILL_DIR/../../.." && pwd)"
GUC_NAMES_FILE="$SKILL_DIR/guc-names.json"
GUC_READER="$SCRIPT_DIR/check_rls_migration.py"
PROBE_JUDGE="$SCRIPT_DIR/check_leak_probe.py"
KIT="$REPO_ROOT/scripts/truth/db.mjs"
PYTHON="${PYTHON:-python3}"
PSQL="${PSQL:-psql}"

SQL_FILE=""
IMAGE="postgres:18-alpine"
TABLE="tenant_isolated_notes"
COLUMNS="id,company_id,body"
MODE="docker"
PARSE_FILE=""
GUC_OVERRIDE=""
ADMIN_URL=""
APP_URL=""
APP_ROLE="web_app"
JOB=""
RESET=0

usage() {
  sed -n '2,38p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

die() {
  echo "FAIL: $*" >&2
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --guc) GUC_OVERRIDE="${2:-}"; shift 2 ;;
    --guc-names) GUC_NAMES_FILE="${2:-}"; shift 2 ;;
    --image) IMAGE="${2:-}"; shift 2 ;;
    --columns) COLUMNS="${2:-}"; shift 2 ;;
    --admin-url) ADMIN_URL="${2:-}"; MODE="server"; shift 2 ;;
    --app-url) APP_URL="${2:-}"; MODE="server"; shift 2 ;;
    --app-role) APP_ROLE="${2:-}"; shift 2 ;;
    --job) JOB="${2:-}"; MODE="server"; shift 2 ;;
    --reset) RESET=1; shift ;;
    --server) MODE="server"; shift ;;
    --print-probe-sql) MODE="print"; shift ;;
    --parse) MODE="parse"; PARSE_FILE="${2:-}"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    -*) die "unknown option: $1" ;;
    *)
      if [[ -z "$SQL_FILE" ]]; then SQL_FILE="$1"; else TABLE="$1"; fi
      shift
      ;;
  esac
done

# ---------------------------------------------------------------------------
# The tenant GUC is configuration, never a constant of this script: the
# convention file names the one tenant GUC of the platform, and the probe
# sets that one name to the tenant it probes. A second spelling would set a
# setting no session of the platform reads.
# ---------------------------------------------------------------------------
guc_names() {
  if [[ -n "$GUC_OVERRIDE" ]]; then
    printf '%s\n' "$GUC_OVERRIDE"
    return
  fi
  [[ -f "$GUC_NAMES_FILE" ]] || die "the tenant convention is missing: $GUC_NAMES_FILE"
  [[ -f "$GUC_READER" ]] || die "the convention reader is missing: $GUC_READER"
  "$PYTHON" "$GUC_READER" --guc-names "$GUC_NAMES_FILE" --list-guc-names
}

TENANT_A="11111111-1111-4111-8111-111111111111"
TENANT_B="22222222-2222-4222-8222-222222222222"

# The probe SQL. Every measurement is printed as a LABEL/VALUE pair on one
# tab-separated line: `psql -t -A` drops column aliases, so an aliased
# `SELECT count(*) AS a_sees_own` prints a bare `1` and the parser cannot tell
# which measurement it is. Printing the label as a value is what makes the
# output parseable.
build_tenant_probe_sql() {
  local guclines="" guc
  while IFS= read -r guc; do
    [[ -n "$guc" ]] || continue
    guclines+="SELECT set_config('${guc}', '${TENANT_A}', true) IS NOT NULL;"$'\n'
  done < <(guc_names)

  cat <<PROBE
-- pg-rls-multitenant leak probe (generated by pg-rls-leak-test.sh).
-- One transaction: set_config(..., true) is transaction-local, so outside a
-- transaction the policy would see NULL and the count would be 0 for the
-- wrong reason.
BEGIN;
SET ROLE ${APP_ROLE};
${guclines}SELECT 'a_sees_own', count(*) FROM __TABLE__;
SELECT 'a_sees_b', count(*) FROM __TABLE__ WHERE company_id = '${TENANT_B}';
COMMIT;
PROBE
}

# The second measurement runs in its own session: no transaction, no tenant
# setting, so it measures what anybody sees when the session carries no
# tenant at all. A tenant table that answers this with a row is not isolated.
build_unset_probe_sql() {
  cat <<PROBE
-- pg-rls-multitenant unset-tenant probe (generated by pg-rls-leak-test.sh).
SET ROLE ${APP_ROLE};
SELECT 'unset_sees_rows', count(*) FROM __TABLE__;
PROBE
}

build_seed_sql() {
  local columns_sql
  columns_sql="$(printf '%s' "$COLUMNS" | sed 's/,/, /g')"
  cat <<SEED
-- The seed runs as the superuser before SET ROLE, so it cannot leak.
INSERT INTO __TABLE__ (__COLUMNS__)
VALUES ('00000000-0000-4000-8000-000000000001', '${TENANT_A}', 'A row')
  ON CONFLICT DO NOTHING;
INSERT INTO __TABLE__ (__COLUMNS__)
VALUES ('00000000-0000-4000-8000-000000000002', '${TENANT_B}', 'B row')
  ON CONFLICT DO NOTHING;
SEED
}

render() {
  local sql="$1" columns_sql
  columns_sql="$(printf '%s' "$COLUMNS" | sed 's/,/, /g')"
  printf '%s' "$sql" | sed \
    -e "s/__TABLE__/$TABLE/g" \
    -e "s/__COLUMNS__/$columns_sql/g"
}

if [[ "$MODE" == "print" ]]; then
  [[ -n "${SQL_FILE:-}" ]] || die "--print-probe-sql needs a migration file"
  render "$(build_tenant_probe_sql)"
  render "$(build_unset_probe_sql)"
  exit 0
fi

if [[ "$MODE" == "parse" ]]; then
  [[ -f "$PROBE_JUDGE" ]] || die "the probe judge is missing: $PROBE_JUDGE"
  [[ -n "$PARSE_FILE" ]] || die "--parse needs a file"
  "$PYTHON" "$PROBE_JUDGE" "$PARSE_FILE"
  exit $?
fi

[[ -n "${SQL_FILE:-}" ]] || { usage >&2; exit 2; }
[[ "$TABLE" =~ ^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?$ ]] \
  || die "invalid table name: $TABLE"
[[ "$COLUMNS" =~ ^[A-Za-z_][A-Za-z0-9_]*(,[A-Za-z_][A-Za-z0-9_]*)*$ ]] \
  || die "invalid column list: $COLUMNS"
[[ -f "$SQL_FILE" ]] || die "no such migration file: $SQL_FILE"
[[ -f "$PROBE_JUDGE" ]] || die "the probe judge is missing: $PROBE_JUDGE"

TMPD="$(mktemp -d)"
cleanup() { rm -rf "$TMPD"; }
trap cleanup EXIT

# ---------------------------------------------------------------------------
# The server path: a PostgreSQL that already runs.
# ---------------------------------------------------------------------------
if [[ "$MODE" == "server" ]]; then
  command -v "$PSQL" >/dev/null 2>&1 || die "psql is not installed: the server mode needs a PostgreSQL client"
  if [[ -z "$ADMIN_URL" && -n "$JOB" ]]; then
    [[ -f "$KIT" ]] || die "the truth kit is missing: $KIT"
    ADMIN_URL="$(node "$KIT" url --job "$JOB" --role admin)" \
      || die "the truth kit cannot hand out the admin URL (npm install --prefix scripts/truth)"
  fi
  if [[ -z "$APP_URL" && -n "$JOB" ]]; then
    [[ -f "$KIT" ]] || die "the truth kit is missing: $KIT"
    APP_URL="$(node "$KIT" url --job "$JOB" --role app)" \
      || die "the truth kit cannot hand out the app URL (npm install --prefix scripts/truth)"
  fi
  [[ -n "$ADMIN_URL" ]] || die "no server: pass --admin-url, or --job with a truth-kit database"
  [[ -n "$APP_URL" ]] || die "no application role: pass --app-url, or --job with a truth-kit database"

  LOGIN_ROLE="$(printf '%s' "$APP_URL" | sed -E 's#^[a-z]+://([^:@/]+).*#\1#')"
  DB_NAME="$(printf '%s' "$APP_URL" | sed -E 's#^[a-z]+://[^/]+/([^?]*).*#\1#')"
  [[ -n "$LOGIN_ROLE" ]] || die "cannot read the application role out of $APP_URL"

  if ! "$PSQL" "$ADMIN_URL" -q -c "SELECT 1" >/dev/null 2>"$TMPD/ping.err"; then
    sed 's/^/   | /' "$TMPD/ping.err" >&2
    die "the server of $DB_NAME is not reachable: $(head -1 "$TMPD/ping.err")"
  fi

  echo ">> preparing the application role $APP_ROLE on $DB_NAME"
  {
    echo "DO \$\$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${APP_ROLE}') THEN CREATE ROLE ${APP_ROLE} NOLOGIN; END IF; END \$\$;"
    echo "GRANT CONNECT ON DATABASE \"${DB_NAME}\" TO ${APP_ROLE};"
    echo "GRANT USAGE ON SCHEMA public TO ${APP_ROLE};"
    echo "GRANT ${APP_ROLE} TO ${LOGIN_ROLE};"
  } | "$PSQL" "$ADMIN_URL" -q -v ON_ERROR_STOP=1 -f - >/dev/null

  EXISTING="$(printf "SELECT to_regclass('public.%s') IS NOT NULL;\n" "$TABLE" \
    | "$PSQL" "$ADMIN_URL" -t -A -v ON_ERROR_STOP=1 -f - 2>/dev/null | tr -d '[:space:]')"
  if [[ "$EXISTING" == "t" ]]; then
    [[ "$RESET" == "1" ]] \
      || die "the table $TABLE already exists in $DB_NAME: the probe would measure a stale table. Pass --reset to drop it, or use another database."
    echo ">> dropping the stale table $TABLE"
    "$PSQL" "$ADMIN_URL" -q -v ON_ERROR_STOP=1 -c "DROP TABLE IF EXISTS \"$TABLE\" CASCADE;" >/dev/null
  fi

  echo ">> applying the migration as the superuser"
  if ! "$PSQL" "$ADMIN_URL" -q -v ON_ERROR_STOP=1 -f "$SQL_FILE" >"$TMPD/apply.out" 2>&1; then
    sed 's/^/   | /' "$TMPD/apply.out" >&2
    echo "FAIL: the migration under test does not apply on $DB_NAME" >&2
    exit 1
  fi

  echo ">> seeding two tenants as the superuser"
  render "$(build_seed_sql)" | "$PSQL" "$ADMIN_URL" -q -v ON_ERROR_STOP=1 -f - >/dev/null

  echo ">> running the probe as $LOGIN_ROLE (table $TABLE)"
  {
    render "$(build_tenant_probe_sql)"
    render "$(build_unset_probe_sql)"
  } | "$PSQL" "$APP_URL" -t -A -F $'\t' -v ON_ERROR_STOP=1 -f - > "$TMPD/probe.out" 2>&1 || true
  sed 's/^/   | /' "$TMPD/probe.out"
  "$PYTHON" "$PROBE_JUDGE" "$TMPD/probe.out"
  exit $?
fi

# ---------------------------------------------------------------------------
# The Docker path.
# ---------------------------------------------------------------------------
CONTAINER="pg-rls-leak-$$"

cleanup_docker() {
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  rm -rf "$TMPD"
}
trap cleanup_docker EXIT

echo ">> pulling $IMAGE (skip if cached)"
docker pull "$IMAGE" >/dev/null 2>&1 || true

echo ">> starting Postgres"
docker run --rm --name "$CONTAINER" -e POSTGRES_PASSWORD=secret \
  -e POSTGRES_USER=postgres -d "$IMAGE" >/dev/null

for _ in $(seq 1 30); do
  if docker exec "$CONTAINER" pg_isready -U postgres >/dev/null 2>&1; then break; fi
  sleep 1
done

echo ">> applying schema + policies"
# The migration grants to the app role (web_app). Create it first so the GRANT
# does not fail; the harness also uses it to run the probe.
cat > "$TMPD/pre.sql" <<'PRE'
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'web_app') THEN
    CREATE ROLE web_app NOLOGIN;
  END IF;
END
$$;
GRANT CONNECT ON DATABASE postgres TO web_app;
GRANT USAGE ON SCHEMA public TO web_app;
PRE
cat "$TMPD/pre.sql" "$SQL_FILE" > "$TMPD/full.sql"
docker exec -i "$CONTAINER" psql -U postgres -d postgres -v ON_ERROR_STOP=1 \
  -f - < "$TMPD/full.sql" 2>&1 | tail -20

echo ">> seeding and probing as web_app (table $TABLE)"
{
  render "$(build_seed_sql)"
  render "$(build_tenant_probe_sql)"
} | docker exec -i "$CONTAINER" psql -U postgres -d postgres -t -A -F $'\t' \
  -v ON_ERROR_STOP=1 -f - > "$TMPD/probe.out" 2>&1 || true
render "$(build_unset_probe_sql)" | docker exec -i "$CONTAINER" psql -U postgres -d postgres \
  -t -A -F $'\t' -v ON_ERROR_STOP=1 -f - >> "$TMPD/probe.out" 2>&1 || true

sed 's/^/   | /' "$TMPD/probe.out"

# The judgement is delegated to check_leak_probe.py: one implementation of
# "what does a probe output mean", used by the tests as well.
"$PYTHON" "$PROBE_JUDGE" "$TMPD/probe.out"
