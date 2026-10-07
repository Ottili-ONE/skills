---
name: acceptance-harness
description: "Design acceptance scenarios with PASS/FAIL/BLOCKED semantics, collect per-scenario evidence, and inject faults to prove resilience. Use when defining what 'done' means, writing acceptance criteria, or proving failure recovery."
license: MIT-compat
compatibility: "framework-agnostic; any test runner; Linux"
metadata: {}
allowed-tools: []
---
# Acceptance Harness Skill (body <500 lines)

Full procedure: references/acceptance-harness-procedure.md
Sources: references/SOURCES.md
Evals: references/EVALS.md
Helpers: scripts/

## When to use this skill (trigger)
- Defining what "done" means for a feature or change.
- Writing scenarios that must produce PASS, FAIL, or BLOCKED.
- Collecting evidence that a requirement is actually met.
- Proving failure paths and recovery (fault injection).
- A reviewer asks "what would break this, and how do we know?"

## When NOT to use this skill
- Exploratory testing without a defined scenario (use a QA session).
- Pure performance or load testing (use a benchmark harness).
- Scenarios whose PASS criteria are opinions, not observable facts.

## Decision table — scenario outcome
| Requirement type | Outcome | Evidence to attach |
|-----------------|---------|--------------------|
| Functional happy path | PASS | test log + screenshot/trace |
| Functional error path | FAIL (expected) | error log + recovery action |
| Non-functional (perf, security) | PASS | metric report (p95, count) |
| Blocked by external dependency | BLOCKED | blocker note + ticket/owner |
| Fault tolerance / recovery | FAIL then PASS | fault injection log |
| Ambiguous / not yet specified | BLOCKED | open question + owner |

## Numbered procedure (summary; full recipe in references/acceptance-harness-procedure.md)
1. Enumerate every requirement; one scenario per requirement, never two requirements per scenario.
2. Write the PASS criteria as an observable assertion, not a feeling.
3. Choose the evidence type: log, screenshot, metric, or trace.
4. Write the rollback plan: how to undo the scenario's effects.
5. Run the scenario; record the outcome (PASS/FAIL/BLOCKED) and the evidence pointer.
6. If FAIL, distinguish "system under test failed" from "scenario is wrong"; fix the scenario, not the claim, only if the requirement genuinely changed.
7. Inject a fault on a passing scenario; the system must recover and the scenario must return to PASS.
8. Commit the scenario file, evidence, and outcome; re-run on every change.

## Pitfalls from research
- Scenarios without a concrete PASS criterion drift into opinion; every scenario needs a checkable assertion.
- Evidence not attached to a scenario is unverifiable; a pointer must open in under 60 seconds.
- Fault injection that crashes the system without recovery is destructive, not resilience proof: require recovery and a return to PASS.
- A scenario that always passes is not a scenario; it has no discriminating power.
- Reusing one scenario for two requirements hides which requirement failed.

## Verification checklist (all must pass before you finish)
- [ ] 1 scenario = 1 requirement = 1 expected outcome = 1 evidence type = 1 rollback plan.
- [ ] Every PASS has a runnable evidence pointer.
- [ ] Every FAIL names the failing assertion and the recovery step.
- [ ] Every BLOCKED names an owner and a concrete next question.
- [ ] At least one fault-injection scenario proves recovery.
