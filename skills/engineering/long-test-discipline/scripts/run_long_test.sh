#!/usr/bin/env bash
# run_long_test.sh — execute a long-running test in the FOREGROUND with a hard timeout,
# optional resource caps and a machine-readable result line.
# No background processes: AGENTS.md forbids `&`/`nohup`/`setsid`; this script is the
# sanctioned way to run a long test on the shared host (Biest).
#
# Usage:
#   run_long_test.sh --name <label> --timeout <s> [--cpu-time <s>] [--mem <MB>] \
#                     [--log <path>] -- <cmd...>
#
# Exit codes: 0 PASS  1 FAIL  2 TIMEOUT  3 RESOURCE_LIMIT  4 USAGE_ERROR
# The last line of the log is a JSON record, e.g.:
#   {"name":"smoke","status":"pass","elapsed_s":3,"pid":1234,"cmd":"true"}
set -uo pipefail

NAME="unnamed"
TIMEOUT=""
CPU_TIME=""
MEM_MB=""
LOG="${OTTLI_TEST_LOG:-long-test.log}"
CMD=()

usage() {
  cat >&2 <<USAGE
Usage: run_long_test.sh --name <label> --timeout <s> [--cpu-time <s>] \
    [--mem <MB>] [--log <path>] -- <cmd...>
Exit codes: 0=pass 1=fail 2=timeout 3=resource-limit 4=usage-error
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name) NAME="$2"; shift 2 ;;
    --timeout) TIMEOUT="$2"; shift 2 ;;
    --cpu-time) CPU_TIME="$2"; shift 2 ;;
    --mem) MEM_MB="$2"; shift 2 ;;
    --log) LOG="$2"; shift 2 ;;
    --) shift; CMD=("$@"); break ;;
    -*) echo "run_long_test: unknown option: $1" >&2; usage; exit 4 ;;
    *) CMD+=("$1"); shift ;;
  esac
done

# --- validate inputs (fail fast, clearly) ---
if [[ ${#CMD[@]} -eq 0 ]]; then
  echo "run_long_test: no command given (need -- <cmd...>)" >&2; usage; exit 4
fi
if [[ -z "$TIMEOUT" ]]; then
  echo "run_long_test: --timeout <seconds> is required" >&2; usage; exit 4
fi
if ! [[ "$TIMEOUT" =~ ^[0-9]+$ ]] || [[ "$TIMEOUT" -eq 0 ]]; then
  echo "run_long_test: --timeout must be a positive integer, got '$TIMEOUT'" >&2; exit 4
fi
for var in CPU_TIME MEM_MB; do
  val="${!var}"
  if [[ -n "$val" ]] && ! [[ "$val" =~ ^[0-9]+$ ]]; then
    echo "run_long_test: --${var,,} must be a positive integer, got '$val'" >&2; exit 4
  fi
done

# --- offline determinism: pin the locale and a stable PATH ordering ---
export LC_ALL=C
export TZ=UTC

# --- resource caps (best-effort; ulimit -v is unavailable in some containers) ---
if [[ -n "$MEM_MB" ]]; then
  if ! ulimit -v "$((MEM_MB * 1024))" 2>/dev/null; then
    echo "run_long_test: warning: ulimit -v unsupported; --mem ignored" >&2
  fi
fi
if [[ -n "$CPU_TIME" ]]; then
  if ! ulimit -t "$CPU_TIME" 2>/dev/null; then
    echo "run_long_test: warning: ulimit -t unsupported; --cpu-time ignored" >&2
  fi
fi

# --- run in the FOREGROUND with a hard wall-clock timeout ---
START=$(date +%s)
STATUS="fail"
PID="n/a"
set +e
timeout --signal=KILL "$TIMEOUT" "${CMD[@]}" >"${LOG}.out" 2>&1
RC=$?
set -e
END=$(date +%s)
ELAPSED=$((END - START))

case $RC in
  0) STATUS="pass" ;;
  124) STATUS="timeout" ;;   # timeout(1) exits 124 on kill
  137) STATUS="timeout" ;;   # KILL = 128+9, some shells report this
  *) STATUS="fail" ;;
esac

# --- resource-limit detection (cgroup OOM / ulimit hit) ---
if grep -Eq "Killed|out of memory|MemoryError" "${LOG}.out" 2>/dev/null; then
  STATUS="resource-limit"
fi

# --- machine-readable result line (append; never truncate the test log) ---
printf '{"name":"%s","status":"%s","elapsed_s":%s,"rc":%s,"pid":"%s","cmd":"%s"}\n' \
  "$NAME" "$STATUS" "$ELAPSED" "$RC" "$PID" "${CMD[*]}" >> "$LOG"

# --- also echo the record to stderr so a driver sees it immediately ---
printf 'run_long_test: %s -> %s (%ss, rc=%s)\n' "$NAME" "$STATUS" "$ELAPSED" "$RC" >&2

case $STATUS in
  pass) exit 0 ;;
  timeout) exit 2 ;;
  resource-limit) exit 3 ;;
  *) exit 1 ;;
esac
