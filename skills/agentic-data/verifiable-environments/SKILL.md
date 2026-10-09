---
name: verifiable-environments
description: "Design verifiers that resist reward hacking: spec-derived checks, oracle-free tests, pass-rate calibration, sandboxing and failure-mode auditing. Use when building or auditing an eval harness, benchmark or agent-environment pair so that an agent cannot game its own score; not for writing unit tests for ordinary software."
compatibility: Python 3.10+, any sandbox API; verified 2026-10-09
license: MIT
---
# Verifiable Environments

Trigger: building or auditing an eval harness, benchmark, or agent+environment pair
where the agent must not be able to game its own score.

## Core invariant
A verifier is trustworthy only if a *rational but lazy* agent cannot reach a pass
without doing the intended work. Every check is derived from a spec the agent
cannot edit, and every bypass is written down. If you cannot write the bypass
for a check, you have not audited it.

## Procedure (numbered — follow in order)
1. **Separate spec from implementation** — write the verifier against a `SPEC.md`
   document, never against the environment code. A verifier that imports the
   environment module shares its bugs and can be reverse-engineered. Keep the
   spec in a directory the agent cannot write to.
2. **Prefer oracle-free checks** — observable outcomes (file at path, exit code,
   stdout equality) beat hidden internal-state checks. Hidden checks are
   legitimate only for state with no observable side effect, and must carry a
   comment justifying them.
3. **Pin the sandbox contract** — the environment exposes a fixed API (container
   exec, filesystem, network policy). Pin the API version and record it in
   `references/sandbox-contract.md`; never let the agent choose tools mid-run.
   The harness asserts the contract is active *before* any agent runs.
4. **Calibrate the pass rate** — run a known-good, a deliberately broken and a
   deliberately lazy agent. A usable harness has
   `pass_good - pass_lazy >= 0.30` and `pass_good - pass_broken >= 0.30`.
   Re-derive thresholds on a held-out set; never fit to the training set.
5. **Audit for reward hacking** — for every check ask: can the agent reach this
   outcome without the intended work? Write every bypass into
   `references/bypass-register.md` (direct / indirect / cosmetic, with severity).
   A check with no entry is a FAIL.
6. **Sandbox the agent's actions** — network off by default, filesystem scoped to
   a temp dir, no code execution that survives the run, time bounded.
7. **Verify the verifier** — run the same checks on a *broken* agent and on a
   *lazy* agent; the verifier must distinguish them. Also require the known-good
   agent to pass >=80%: checks that are too strict are as useless as checks that
   are too loose. Then flip one check to always-pass and re-run: the power must
   drop and the harness must exit 1.

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
- **Discriminating power**: `min(pass_good - pass_lazy, pass_good - pass_broken)`
  must be >= 0.30. Below that the checks have no discriminating power.

## Near-miss triggers (stop and re-check before proceeding)
- A check passes on a deliberately broken agent -> the check is decorative.
- The verifier imports the environment module -> it shares the bug.
- Pass rate 100% on every agent -> the checks have no discriminating power.
- The agent can `curl` an internal service -> sandbox policy is wrong.
- A check depends on wall-clock time -> flaky and gameable.
- A check has no `spec_ref` pointing at the spec -> it was not derived from a spec.
- A check has no bypass-register entry -> nobody has audited it.
- Known-good agent passes <80% -> the checks are too strict, relax them.
- The harness exits 0 after a check is neutered -> the verifier is not verified.

## Pitfalls from research
- P1: Verifiers that read the environment source are trivially reverse-engineered.
- P2: Process proxies (token count, tool calls) are easily faked; never score on them.
- P3: A verifier tuned until a known agent passes is overfit and will not transfer.
- P4: Unbounded network or filesystem access lets an agent fetch the answer.
- P5: Time-based checks are flaky; use deterministic completion signals.
- P6: A check nobody has tried to game will be gamed later; the bypass register is
  insurance, not paperwork.
- P7: A harness that only checks "did it finish" has no discriminating power;
  an agent that stalls to the timeout scores 100%.

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
- [ ] Harness re-run after neutering a check drops power and exits 1.

## References
- procedures: references/procedures.md
- sandbox contract: references/sandbox-contract.md
- bypass register: references/bypass-register.md
- EVALS: references/EVALS.md
- SOURCES: references/SOURCES.md
- scripts: scripts/verify_harness.py
