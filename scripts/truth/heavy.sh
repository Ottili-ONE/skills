#!/usr/bin/env bash
# Heavy-command semaphore: at most N concurrent heavy commands per class on one machine, and only while enough
# memory is available. Use it for installs, builds, type checks, test runs and browser runs.
#
#   scripts/truth/heavy.sh [--class build|db|browser] [--timeout SECONDS] [--label TEXT] -- command [args...]
#   scripts/truth/heavy.sh --status
#
# Slots per class (override with environment variables or /etc/ottili-truth/limits.env):
#   TRUTH_HEAVY_SLOTS_BUILD (default 6)  TRUTH_HEAVY_SLOTS_DB (default 10)  TRUTH_HEAVY_SLOTS_BROWSER (default 5)
#   TRUTH_MIN_FREE_MB (default 1536)     TRUTH_HEAVY_TIMEOUT (default 5400)  TRUTH_LOCK_DIR (default /tmp/ottili-truth-locks)
# Exit code 75 means: no slot became free before the timeout (the machine is saturated; retry later).
# Never start a long-running server (dev server, watcher) through this script: the slot is held while the child lives.
set -u

CLASS=build
TIMEOUT=""
LABEL=""
STATUS=0

for f in "${TRUTH_CONFIG_DIR:-}/limits.env" /etc/ottili-truth/limits.env "${HOME:-/nonexistent}/.ottili-truth/limits.env"; do
  if [ -n "$f" ] && [ -r "$f" ]; then
    # shellcheck disable=SC1090
    . "$f"
    break
  fi
done

while [ $# -gt 0 ]; do
  case "$1" in
    --class) CLASS=$2; shift 2 ;;
    --timeout) TIMEOUT=$2; shift 2 ;;
    --label) LABEL=$2; shift 2 ;;
    --status) STATUS=1; shift ;;
    --) shift; break ;;
    *) break ;;
  esac
done

slots_for() {
  case "$1" in
    build) echo "${TRUTH_HEAVY_SLOTS_BUILD:-6}" ;;
    db) echo "${TRUTH_HEAVY_SLOTS_DB:-10}" ;;
    browser) echo "${TRUTH_HEAVY_SLOTS_BROWSER:-5}" ;;
    *) echo "${TRUTH_HEAVY_SLOTS_DEFAULT:-4}" ;;
  esac
}

MINMEM=${TRUTH_MIN_FREE_MB:-1536}
LOCKDIR=${TRUTH_LOCK_DIR:-${TMPDIR:-/tmp}/ottili-truth-locks}
mkdir -p "$LOCKDIR" 2>/dev/null
chmod 1777 "$LOCKDIR" 2>/dev/null || true

avail_mb() {
  awk '/^MemAvailable:/ {print int($2/1024); found=1} END {if (!found) print 999999}' /proc/meminfo 2>/dev/null || echo 999999
}

if [ "$STATUS" = "1" ]; then
  echo "free memory: $(avail_mb) MB (minimum $MINMEM MB), load: $(cut -d' ' -f1-3 /proc/loadavg 2>/dev/null)"
  for c in build db browser; do
    n=$(slots_for "$c")
    busy=0
    i=0
    while [ "$i" -lt "$n" ]; do
      lf="$LOCKDIR/$c.$i.lock"
      if [ -e "$lf" ]; then
        { exec {sfd}>>"$lf"; } 2>/dev/null
        if ! flock -n "$sfd"; then busy=$((busy + 1)); fi
        exec {sfd}>&-
      fi
      i=$((i + 1))
    done
    echo "class $c: $busy/$n slots busy"
  done
  exit 0
fi

if [ $# -eq 0 ]; then
  echo "usage: heavy.sh [--class build|db|browser] [--timeout SECONDS] -- command [args...]" >&2
  exit 2
fi

[ -z "$TIMEOUT" ] && TIMEOUT=${TRUTH_HEAVY_TIMEOUT:-5400}
SLOTS=$(slots_for "$CLASS")
deadline=$(( $(date +%s) + TIMEOUT ))
warned=0

while :; do
  avail=$(avail_mb)
  if [ "$avail" -ge "$MINMEM" ]; then
    i=0
    while [ "$i" -lt "$SLOTS" ]; do
      lockfile="$LOCKDIR/$CLASS.$i.lock"
      ( umask 000; : >>"$lockfile" ) 2>/dev/null
      if { exec {fd}>>"$lockfile"; } 2>/dev/null; then
        if flock -n "$fd"; then
          : >"$lockfile" 2>/dev/null
          printf '%s pid=%s job=%s label=%s\n' "$(date -u +%FT%TZ)" "$$" "${TRUTH_JOB:-}" "$LABEL" >&"$fd"
          "$@"
          rc=$?
          exec {fd}>&-
          exit "$rc"
        fi
        exec {fd}>&-
      fi
      i=$((i + 1))
    done
  fi
  if [ "$(date +%s)" -ge "$deadline" ]; then
    echo "heavy.sh: timed out after ${TIMEOUT}s waiting for a '$CLASS' slot (free memory ${avail} MB, need ${MINMEM} MB)" >&2
    exit 75
  fi
  if [ "$warned" = "0" ]; then
    echo "heavy.sh: waiting for a '$CLASS' slot (free memory ${avail} MB, slots $SLOTS)..." >&2
    warned=1
  fi
  sleep $(( (RANDOM % 4) + 2 ))
done
