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
python3 scripts/check_audit_selectors.py tests/e2e/report.json
python3 scripts/check_keyboard.py tests/e2e/report.json
python3 scripts/check_workaround_markers.py src/
python3 scripts/check_axe_evidence.py tests/e2e/evidence/
```
All four scripts ship in `scripts/` (offline, deterministic, self-tested).

Summary printed to stdout lists failing routes first, then failing viewports, then failing
selectors, then missing evidence files.

Common trap: checking only one subset. Axe alone misses keyboard traps; desktop alone misses
mobile overflow; ignoring workaround markers hides drift.


## Step 4b — Fault-injection decision table (recovery proof)
Injecting a fault is only useful if the scenario proves *recovery*, not just that the system
reacted. Use this table to decide the expected sequence:

| Injected fault | Expected system reaction | Recovery assertion | If no recovery |
|----------------|--------------------------|--------------------|----------------|
| DB timeout (5s) | 503 problem + retry | second attempt within 10s returns 200 | BLOCKED: infra cannot recover |
| SMTP unreachable | 503 problem, outbox row | outbox row exists, `sent_at IS NULL` | FAIL: event lost |
| DHL sandbox 503 | problem document, retry | retry succeeds within 3 attempts | BLOCKED: vendor SLA not met |
| Keycloak 401 | 401 problem, no retry | token refresh path re-authenticates | FAIL: session dead |
| network partition | 503, circuit opens | circuit closes within 60s of partition end | FAIL: no circuit breaker |
| clock skew +/- 5 min | 401/403, re-sync | re-sync via NTP within 30s | BLOCKED: clock source down |
| partial payload | 400 problem, no state change | DB unchanged (transaction rolled back) | FAIL: partial write |

Threshold: the recovery assertion must return to PASS within the scenario timeout. If it does
not, the outcome is FAIL (system under test failed), never "the fault was too strong".

Worked example — good fault injection:
```
scenario: outbox survives SMTP down
inject:   block port 25 (iptables DROP for 30s)
expect:   POST /orders -> 503 {"type":".../smtp-unreachable"}
recover:  remove the block; poller retries; POST /orders -> 201
outcome:  PASS (recovery proven)
evidence: tests/e2e/evidence/outbox-smtp-down.json
```
Worked example — bad fault injection (destructive, not a proof):
```
scenario: "system survives DB kill"
inject:   kill -9 the primary (no recovery step planned)
expect:   ... nothing recorded, host left broken
outcome:  INVALID — no recovery assertion, no evidence, host damaged
```
A fault injection with no recovery assertion is not a scenario; it is a host outage.

## Step 4b-2 — Near-miss triggers for acceptance work
- "The scenario passed once, so it is fine" — run it 10x in a loop; flake = BLOCKED.
- "We do not need a rollback for a read-only scenario" — even reads can lock rows or
  hold connections; write the rollback anyway.
- "Evidence can go in /tmp" — /tmp is not committed; evidence must live in the tree or in a
  run artifact with a URL that survives 60 days.
- "The fault is too artificial" — every seam in the fault catalogue above came from a real
  incident; artificiality is not a reason to skip it.

## Verification checklist (all must pass before merge)
- [ ] Setup completes without browser install errors
- [ ] Axe zero A/AA violations across all routes and viewports
- [ ] Keyboard: every interactive element reachable in <= 5 Tab presses
- [ ] Responsive: no overflow > 0 px at any breakpoint
- [ ] Selectors: role/text-based only; no `nth-child`, no class-only attributes
- [ ] Workaround markers: all link an `ISSUE-<digits>`
- [ ] Evidence JSON + screenshots committed per route/viewport pair
- [ ] Resume-from-failure logic works end-to-end (smoke test in EVALS)
