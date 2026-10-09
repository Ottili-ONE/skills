---
name: verifiable-environments
description: "Design verifiers that resist reward hacking: spec-derived checks, oracle-free tests, pass-rate calibration, sandboxing and failure-mode auditing. Use when building or auditing an eval harness, benchmark or agent-environment pair so that an agent cannot game its own score; not for writing unit tests for ordinary software."
compatibility: Python 3.10+, any sandbox API; verified 2026-10-09
license: MIT
---
# Verifiable Environments

Trigger: building or auditing an eval harness, benchmark, or agent+environment pair
where the agent must not be able to game its own score.

## Procedure (numbered — follow in order)
1. **Separate spec from implementation** — write the verifier against a *spec*
   document, never against the environment code. A verifier that reads the
   environment source can be reverse-engineered.
2. **Prefer oracle-free checks** — observable outcome checks (did the file land
   where it should, does the command exit 0, does the test pass) beat hidden
   internal-state checks; hidden checks are legitimate only for state that has
   no observable side effect.
3. **Pin the sandbox contract** — the environment exposes a fixed API (container
   exec, filesystem, network policy). Pin the API version and record it; never
   let the agent choose its own tools mid-run.
4. **Calibrate the pass rate** — on a known-good agent run, record the pass rate.
   A verifier whose pass rate jumps by >20 points on an unmodified agent is
   suspect; re-derive thresholds on a held-out set.
5. **Audit for reward hacking** — for every check, ask: can the agent reach this
   outcome without doing the intended work? Write every bypass into
   `references/bypass-register.md` (direct / indirect / cosmetic, with severity).
   A check with no entry is a FAIL.
6. **Sandbox the agent's actions** — network off by default, filesystem scoped to a
   temp dir, no code execution that survives the run.
7. **Verify the verifier** — run the same checks on a *broken* agent and on a
   *lazy* agent; the verifier must distinguish them. If both score 100%, the
   verifier is broken. Also require the known-good agent to pass >=80%: checks
   that are too strict are as useless as checks that are too loose.

## Decision tables
- **Check type**: observable outcome > hidden state > process proxy. Never
  process-only (a proxy can be faked).
- **Sandbox policy**: network=deny, fs=scoped tmp, exec=allowlisted only,
  time=bounded. Anything else is a leak.
- **Pass-rate drift**: 0-5 points = noise; 6-20 = re-derive thresholds; >20 =
  verifier compromised, halt the run.
- **Bypass severity**: direct (agent edits the check/spec/harness) = critical;
  indirect (agent finds an unintended path) = high; cosmetic (agent reorders
  output) = low. Every check must have a written entry in the bypass register.
- **Known-good pass rate**: >=80% required; below that the checks are too
  strict and will reject correct agents.

## Near-miss triggers (stop and re-check before proceeding)
- A check passes on a deliberately broken agent -> the check is decorative.
- The verifier imports the environment module -> it shares the bug.
- Pass rate 100% on every agent -> the checks have no discriminating power.
- The agent can `curl` an internal service -> sandbox policy is wrong.
- A check depends on wall-clock time -> flaky and gameable.
- A check has no `spec_ref` pointing at the spec -> it was not derived from a spec.
- A check has no bypass-register entry -> nobody has audited it.
- Known-good agent passes <80% -> the checks are too strict, relax them.

## Pitfalls from research
- P1: Verifiers that read the environment source are trivially reverse-engineered.
- P2: Process proxies (token count, tool calls) are easily faked; never score on them.
- P3: A verifier tuned until a known agent passes is overfit and will not transfer.
- P4: Unbounded network or filesystem access lets an agent fetch the answer.
- P5: Time-based checks are flaky; use deterministic completion signals.
- P6: A check nobody has tried to game will be gamed later; the bypass register is
  insurance, not paperwork.

## Verification checklist
- [ ] Verifier written from a spec, not from the environment code.
- [ ] Every check carries a `spec_ref` found in the spec text.
- [ ] Every check is observable or justified as a hidden state check.
- [ ] Every check has a bypass-register entry (direct/indirect/cosmetic).
- [ ] Sandbox policy pinned: network=deny, fs=scoped, exec=allowlisted.
- [ ] Pass rate calibrated on a known-good run and recorded.
- [ ] Bypass list exists per check.
- [ ] Broken and lazy agents score measurably below the good agent.
- [ ] Known-good agent passes >=80%.
- [ ] No check depends on wall-clock time.

## References
- procedures: references/procedures.md
- sandbox contract: references/sandbox-contract.md
- bypass register: references/bypass-register.md
- EVALS: references/EVALS.md
- SOURCES: references/SOURCES.md
- scripts: scripts/validate_skill.py
