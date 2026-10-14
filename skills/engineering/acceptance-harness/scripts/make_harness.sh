#!/bin/bash
# make_harness.sh — scaffold one acceptance scenario file from a criterion ID.
# Usage: make_harness.sh <scenario-id> <requirement-id> <outdir>
# Foreground only: no '&', nohup, setsid (shared-host rule).
set -euo pipefail
SCENARIO="${1:?usage: make_harness.sh <scenario-id> <requirement-id> <outdir>}"
REQ="${2:?usage: make_harness.sh <scenario-id> <requirement-id> <outdir>}"
OUTDIR="${3:?usage: make_harness.sh <scenario-id> <requirement-id> <outdir>}"
mkdir -p "$OUTDIR"

cat > "$OUTDIR/$SCENARIO.md" <<EOF
# SCENARIO-$SCENARIO
requirement: $REQ
outcome: BLOCKED
evidence:
rollback:

## PASS criteria
- (observable assertion, e.g. HTTP 200 within 500 ms p95 across 5 runs)

## Fault injection
- (one fault at the seam this scenario exercises)

## Notes
- owner:
- date:
echo "wrote $OUTDIR/$SCENARIO.md"
