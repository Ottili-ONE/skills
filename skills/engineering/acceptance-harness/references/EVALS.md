# Acceptance Harness — EVALS (5 realistic prompts with expected behaviour and failure signs)
Retrieval date: 2026-10-07. Verified versions: pytest 8.x; IEEE 829-2008; ISTQB CTFL v4.0. Sources: istqb.org, pytest.org, github.com/actions/upload-artifact, repo AGENTS.md R3 LIVE DIRECTIVES. See also references/SOURCES.md for full provenance.

## E1 — Functional happy path with PASS evidence
Prompt: "Write an acceptance scenario for user login that passes when credentials are valid."
Expected behaviour: scenario defines route /login, action enter-valid-credentials, PASS criterion = HTTP 200 + session cookie set + dashboard visible, evidence = test log line + screenshot of dashboard. Failure sign: PASS recorded without screenshot or log pointer; criterion uses words like "looks good".
Exact command to verify evidence: `test -f tests/e2e/screenshots/dashboard-1024.png && grep -c 'PASS' tests/e2e/report.log`.
Thresholds: login must complete in <=3s p95 across 5 runs else BLOCKED for perf not functional.
Worked example good output: `PASS /login valid-credentials | evidence: tests/e2e/evidence/login.json screenshot dashboard-1024.png | p95=1.8s`.
Worked example bad output: `PASS /login` (no evidence pointer).
Near-miss trigger prompt: "The login works but I didn't capture a screenshot — is it still PASS?" Answer: no, downgrade to IN_PROGRESS until evidence attached.

## E2 — Expected FAIL with recovery evidence
Prompt: "Write a scenario for payment when the gateway times out."
Expected behaviour: scenario asserts FAIL (expected) on gateway timeout, recovery = retry once then fallback to stored card, evidence = error log + recovery action log. Failure sign: recorded as PASS because retry succeeded without recording the initial failure; or no rollback plan.
Exact command to verify: `grep -c 'FAIL.*gateway-timeout' tests/e2e/report.log && grep -c 'retry fallback' tests/e2e/recovery.log`.
Thresholds: retry must complete within 10s total else BLOCKED (external dependency).
Worked example good output: `FAIL /payment gateway-timeout (expected) | recovery: retry->fallback | evidence: tests/e2e/evidence/payment-fail.json`.
Worked example bad output: `PASS /payment` (hides the timeout).
Near-miss trigger prompt: "The retry succeeded so should I mark it PASS?" Answer: no, record FAIL for the timeout path and PASS only for the fallback path separately.

## E3 — BLOCKED by external dependency
Prompt: "Write a scenario for email notification when the SMTP server is unreachable."
Expected behaviour: outcome BLOCKED, evidence = blocker note + ticket + owner, not PASS or FAIL. Failure sign: marking PASS because "it works locally" without SMTP; or leaving BLOCKED forever with no owner.
Exact command to verify: `grep -c 'BLOCKED' tests/e2e/report.log && grep -c 'owner:' tests/e2e/scenarios.csv`.
Thresholds: BLOCKED older than 5 business days must be escalated (owner re-assigned).
Worked example good output: `BLOCKED /notify email-smtp-unreachable | ticket: PROJ-123 | owner: alice | date: 2026-10-07`.
Worked example bad output: `BLOCKED /notify` (no owner, no ticket).
Near-miss trigger prompt: "I'll just skip this scenario until SMTP is back." Answer: no, keep BLOCKED with owner and escalate after 5 days.
