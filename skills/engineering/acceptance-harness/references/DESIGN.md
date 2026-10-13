# DESIGN — acceptance-harness

## Trigger description (draft)
Fires when: an agent must turn acceptance criteria into an executable, traceable test harness;
when a scenario needs PASS/FAIL/BLOCKED semantics with evidence; when fault injection is
required to prove a failure path; or when a reviewer asks "what evidence does this test keep"?
Does NOT fire for: unit tests that need no scenario, or manual QA checklists.

## What it does better than existing public skills
Public testing skills teach *how to write a test*; none teach how to bind a test to a written
acceptance criterion, how to decide PASS vs FAIL vs BLOCKED, or how to inject a fault and
record the evidence artifact. This skill ships `scripts/` harness helpers and a procedure that
makes every scenario result traceable to a criterion ID and a kept evidence file (log, HAR,
screenshot). The PASS/FAIL/BLOCKED tri-state is the differentiator: BLOCKED means the test
could not run, which is a distinct outcome from failure and must never be reported as pass.

## Procedure outline
1. Write the criterion first, in the form `AC-<n>: <actor> <action> under <condition>, observed via <artifact>`.
2. Derive the scenario: inputs, setup, steps, expected result, and the evidence artifact per step.
3. Assign a tri-state contract: PASS (observed == expected), FAIL (observed != expected),
   BLOCKED (could not execute — missing env, blocked dependency, flaky infra).
4. Inject one fault per scenario at the seam the scenario exercises; assert the system reacts,
   not just that the happy path passes.
5. Run via `long-test-discipline` conventions (foreground, timeout, log to file, resource caps).
6. Record evidence: keep the log/HAR/screenshot; a PASS with no evidence file is a claim, not a result.

## Scripts (shipped)
- `scripts/check_audit_selectors.py` — flags `nth-child` / class-only selectors in a Playwright JSON
  report. Self-tested via `check_audit_selectors_test.py`.
- `scripts/make_harness.sh <scenario-id> <requirement-id> <outdir>` — scaffold a scenario file.
- `scripts/report_result.py` — writes PASS/FAIL/BLOCKED + evidence path into a results JSON.
  Self-tested via `report_result_test.py`.

## Five eval prompts
1. "Write a harness for 'a user can reset their password'. The mail provider is unavailable in CI." → scenario must be BLOCKED, not PASS or FAIL; evidence = the SMTP error log.
2. "My test passes but I have no screenshot or log." → agent must keep an evidence artifact or mark the result BLOCKED/claim.
3. "Inject a fault: make the DB return a timeout during checkout." → agent must assert the checkout fails gracefully and records the fault in evidence.
4. "Is this a PASS or a FAIL: the API returned 500 instead of 200?" → FAIL, with the response body as evidence.
5. "The scenario depends on DHL sandbox credentials we do not have." → BLOCKED, with the reason recorded; never skip or fake.
