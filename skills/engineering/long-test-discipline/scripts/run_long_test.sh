#!/bin/bash
set -euo pipefail
TEST_NAME="${1:?usage: run_long_test.sh <test_name>}"
LOG="logs/${TEST_NAME}.log"
mkdir -p logs
# Resource limits
ulimit -v $((4 * 1024 * 1024))
ulimit -u 8
# Timeout: 900 s = 15 min
timeout 900 /usr/local/bin/heavy pytest "$TEST_NAME" \n  --randomly-seed "${SEED:-42}" \n  --tb=short \n  > "$LOG" 2>&1
EXIT=$?
echo "EXIT=$EXIT LOG=$LOG"
exit $EXIT
