# Acceptance Harness — Full Procedure

Retrieval date: 2026-10-13. Host: Biest. SEARCH_ENDPOINT: none (URLs fetched directly with curl).
Verified versions: pytest 8.x; IEEE 829-2008; ISTQB CTFL v4.0; GitHub actions/upload-artifact v4.
Sources: `references/SOURCES.md`. Evals: `references/EVALS.md`.

## 0. Purpose and tri-state contract
An acceptance scenario is not a test script. It is a *criterion* with a recorded outcome and a
kept evidence artifact. Outcomes are exactly three:

| Outcome | Meaning | Never reported as |
|---------|---------|-------------------|
| PASS | observed == expected, evidence attached | — |
| FAIL | observed != expected, evidence attached | PASS |
| BLOCKED | could not execute (missing env, blocked dep, flaky infra) | PASS |

A scenario that "always passes" has no discriminating power. A scenario with no evidence file is
a claim, not a result.

## Step 1 — Enumerate requirements (one scenario per requirement)
Each scenario maps to exactly one requirement ID. Never combine two requirements in one row.

Template: `SCENARIO-<ID> \| requirement:<req-id> \| outcome:PASS\|FAIL\|BLOCKED`.

- Failure sign: a scenario covers login AND payment — two requirements in one row.
- Threshold: if a requirement has no scenario, block merge until one is written.

## Step 2 — Write PASS criteria as observable assertions
Every criterion must be checkable by a script or human in under 60 seconds.

- Bad: "the page feels fast".
- Good: "HTTP 200 within 2s p95 across 5 runs".
- Bad: "looks correct".
- Good: "axe zero A/AA violations".

Evidence types: `log`, `screenshot`, `metric report`, `trace pointer`.

Thresholds for common checks:

| Check | Threshold |
|-------|-----------|
| HTTP response | <= 500 ms p95 |
| axe violations | == 0 (A/AA) |
| keyboard reachability | <= 5 Tab presses |
| responsive overflow | == 0 px at any breakpoint |
| selector stability | no `nth-child`; role/text-based only |
| workaround markers | every marker links an `ISSUE-<digits>` |

Worked example good output:
```
PASS /login | criterion=HTTP200+p95<=500ms | evidence=tests/e2e/evidence/login.json
```
Worked example bad output: `PASS /login` (no criterion).

Pitfall: scenarios without concrete PASS criteria drift into opinion. Every scenario needs a
checkable assertion with threshold numbers attached.

## Step 3 — Assign the outcome
Use the decision table:

| Observed | Expected | Outcome |
|----------|----------|---------|
| matches | matches | PASS |
| differs | matches | FAIL |
| could not run | any | BLOCKED |

- A negative case must exist: wrong input should FAIL.
- Fault injection that crashes the system without recovery is *destructive*, not a resilience
  proof. Require recovery and a return to PASS after injection stops.

## Step 4 — Fault injection
Inject exactly one fault per scenario, at the seam the scenario exercises. Assert the system
*reacts*, not just that the happy path passes.

Fault catalogue (Ottili seams): DB timeout, SMTP unreachable, DHL sandbox 503, Keycloak 401,
network partition, clock skew, partial payload.

## Step 5 — Run under long-test-discipline
Run in the FOREGROUND with a timeout wrapper, structured logs, and resource caps. Never use
`&`/`nohup`/`setsid` — those are killed when the command returns and their logs never appear.

```
timeout 900 /usr/local/bin/heavy pytest tests/e2e/ --reporter=json \
    --output=tests/e2e/report.json > tests/e2e/run.log 2>&1
```

## Step 6 — Collect evidence
- Keep the log, HAR, or screenshot per scenario.
- Evidence must open in under 60 seconds (file path or URL).
- Collision avoidance: evidence files are named by scenario ID, not requirement ID, and written
  to a lane-specific subdir `tests/e2e/evidence/<lane>/<scenario-id>.json`. `EVIDENCE_LANE`
  defaults to `git config user.name` sanitized, fallback `unknown`. Max concurrent writers =
  the number of parallel CI shards (`CI_NODE_TOTAL`, default 4), NOT the number of agents locally.

## Step 7 — Report
Run all four checks; any non-zero exit code makes the build red:

```
node scripts/check_audit_selectors.js tests/e2e/report.json
python3 scripts/check_keyboard.py tests/e2e/report.json
python3 scripts/check_workaround_markers.py src/
python3 scripts/check_axe_evidence.py tests/e2e/evidence/
```

Summary printed to stdout lists failing routes first, then failing viewports, then failing
selectors, then missing evidence files.

Common trap: checking only one subset. Axe alone misses keyboard traps; desktop alone misses
mobile overflow; ignoring workaround markers hides drift.

## Verification checklist (all must pass before merge)
- [ ] Setup completes without browser install errors
- [ ] Axe zero A/AA violations across all routes and viewports
- [ ] Keyboard: every interactive element reachable in <= 5 Tab presses
- [ ] Responsive: no overflow > 0 px at any breakpoint
- [ ] Selectors: role/text-based only; no `nth-child`, no class-only attributes
- [ ] Workaround markers: all link an `ISSUE-<digits>`
- [ ] Evidence JSON + screenshots committed per route/viewport pair
- [ ] Resume-from-failure logic works end-to-end (smoke test in EVALS)
