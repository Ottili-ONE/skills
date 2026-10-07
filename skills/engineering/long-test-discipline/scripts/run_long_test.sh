#!/bin/bash
set -euo pipefail
TEST_NAME="${1:?usage: run_long_test.sh <test_name>}"
LOG="logs/${TEST_NAME}.log"
mkdir -p logs
# Resource limits (shared-host safe; override via env vars)
ulimit -v "${MAX_VMEM_KB:-$((8 * 1024 * 1024))}"   # default 8 GiB virtual mem
ulimit -u "${MAX_PROCS:-64}"                        # default max processes
# Timeout: 900 s = 15 min; foreground only - no '&', nohup, setsid
SEED="${SEED:-42}"
timeout 900 /usr/local/bin/heavy pytest "$TEST_NAME" \
  --randomly-seed "$SEED" \
  --tb=short \
  > "$LOG" 2>&1
EXIT=$?
echo "EXIT=$EXIT LOG=$LOG SEED=$SEED WALL=$(date +%s)" >> "$LOG"
exit $EXIT
