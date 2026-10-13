#!/usr/bin/env bash
# Self-test for run_long_test.sh — verifies every exit code and the JSON record.
set -uo pipefail
SCRIPT="$(cd "$(dirname "$0")" && pwd)/run_long_test.sh"
TMP="$(mktemp -d)"
FAIL=0

check() { # <expected> <label> <script-args...>
  local want="$1" label="$2"; shift 2
  "$SCRIPT" "$@" >/dev/null 2>&1
  local got=$?
  if [[ "$got" -eq "$want" ]]; then
    echo "ok   $label -> exit $got"
  else
    echo "FAIL $label -> expected exit $want, got $got"; FAIL=1
  fi
}

check 4 "usage-no-cmd" --name x --timeout 5
check 4 "missing-timeout" --name x -- true
check 4 "bad-timeout" --name x --timeout 0 -- true
check 4 "bad-mem" --name x --timeout 5 --mem abc -- true
check 0 "pass" --name pass --timeout 10 -- true
check 1 "fail" --name fail --timeout 10 -- false
check 2 "timeout" --name slow --timeout 2 -- sleep 30
check 3 "resource-limit" --name oom --timeout 10 -- bash -c 'echo Killed; exit 137'

# JSON record: pass case must append a status=pass line to the log
LOG="$TMP/lt.log"
"$SCRIPT" --name rec --timeout 10 --log "$LOG" -- true >/dev/null 2>&1
if grep -q '"status":"pass"' "$LOG"; then
  echo "ok   json-record"
else
  echo "FAIL json-record: no status=pass line in $LOG"; FAIL=1
fi

# resource-limit detection via OOM-style message
LOG2="$TMP/oom.log"
"$SCRIPT" --name oom2 --timeout 10 --log "$LOG2" -- bash -c 'echo "out of memory" >&2; exit 1' >/dev/null 2>&1
if grep -q '"status":"resource-limit"' "$LOG2"; then
  echo "ok   oom-detection"
else
  echo "FAIL oom-detection"; FAIL=1
fi

if [[ "$FAIL" -eq 0 ]]; then
  echo "run_long_test self-test: PASS"; exit 0
else
  echo "run_long_test self-test: FAIL"; exit 1
fi
