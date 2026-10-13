# DESIGN: verifiable-environments

## Trigger description (SKILL.md description draft, <=1024 chars)
"Design verifiers that resist reward hacking: spec-derived checks, oracle-free tests,
pass-rate calibration, sandboxing and failure-mode auditing. Use when building or
auditing an eval harness, benchmark or agent-environment pair so that an agent cannot
game its own score; not for writing unit tests for ordinary software."

## Core invariant
A verifier is trustworthy only if a *rational but lazy* agent cannot reach a pass
without doing the intended work. Every check is derived from a spec the agent cannot
edit, and every bypass is written down. If you cannot write the bypass for a check,
you have not audited it.

## Procedure outline
1. Separate spec from implementation — write the verifier against a `SPEC.md`, never
   against the environment code. A verifier that imports the environment module shares
   its bugs and can be reverse-engineered. Keep the spec outside the agent's write
   scope.
2. Prefer oracle-free checks — observable outcomes (file at path, exit code, stdout
   equality) beat hidden internal-state checks. Hidden checks are legitimate only for
   state with no observable side effect, and must carry a justifying comment.
3. Pin the sandbox contract — network=deny, filesystem=scoped, exec=allowlisted,
   time=bounded, secrets=none/redacted. The harness asserts the contract is active
   *before* any agent runs. A contract with network=allow or filesystem=open fails the
   whole harness.
4. Calibrate the pass rate — run known-good, deliberately broken and deliberately lazy
   agents. Require `pass_good - pass_lazy >= 0.30` and `pass_good - pass_broken >= 0.30`,
   and `pass_good >= 0.80`. Re-derive thresholds on a held-out set; never fit to the
   training set.
5. Audit for reward hacking — for every check ask: can the agent reach this outcome
   without the intended work? Write every bypass into `references/bypass-register.md`
   (direct / indirect / cosmetic, with severity). A check with no entry is a FAIL.
6. Sandbox the agent's actions — network off by default, filesystem scoped to a temp
   dir, no code execution that survives the run, time bounded.
7. Verify the verifier — run the checks on broken and lazy agents (must distinguish
   them), require known-good >=80%, then flip one check to always-pass: the power must
   drop and the harness must exit 1.

## Decision tables
- **Check type**: observable outcome > hidden state > process proxy. Never
  process-only (a proxy can be faked).
- **Pass-rate drift**: 0-5 points = noise; 6-20 = re-derive thresholds; >20 =
  verifier compromised, halt the run.
- **Bypass severity**: direct (agent edits the check/spec/harness) = critical;
  indirect (agent finds an unintended path) = high; cosmetic (reorders output) = low.
- **Discriminating power**: `min(pass_good - pass_lazy, pass_good - pass_broken)` must
  be >= 0.30.

## Scripts planned
- `scripts/verify_harness.py` — runs the three agents (good/broken/lazy), reports pass
  rates, discriminating power, and exits 1 if the harness cannot distinguish them.

## Five eval scenarios (expanded in `references/EVALS.md`)
1. "My verifier imports the environment module. Is that a problem?" -> Yes: it shares
   the environment's bugs and can be reverse-engineered. Write against a SPEC.md.
2. "A check has no bypass entry. What do I do?" -> FAIL the check; you have not audited
   it.
3. "pass_good is 0.6 and pass_lazy is 0.5. Is the harness usable?" -> No: discriminating
   power is 0.10, below the 0.30 floor.
4. "The sandbox contract says network=allow. Is the harness usable?" -> No: the contract
   fails the whole harness before any agent runs.
5. "I flipped one check to always-pass and the power did not drop." -> The check was
   not load-bearing; find another one and repeat.

## What this skill does better than a generic agent
A generic agent writes tests that check the happy path. This skill ships a
spec/implementation split, oracle-free check preference, a sandbox contract that the
harness asserts before the agent runs, pass-rate calibration with explicit floors, a
bypass register, and a verifier-verification step that flips a check to always-pass to
prove the harness can still fail. It prevents the incident of an eval that scores
everyone 100%.

## What existing public skills do (and what this one does differently)

Surveyed on 2026-10-12. Public Agent Skills cover *running* benchmarks (OpenAI
Evals, `anthropics/skills` evaluation helpers, agentevals) but not *designing*
verifiers that resist reward hacking. The closest prior art is the RLHF/RL literature
on reward gaming and the "reward hacking" taxonomies in the alignment literature.

This skill is the only Agent Skill that treats the verifier as a system to be audited:
- **Spec/implementation split**: the verifier is written against a `SPEC.md` the agent
  cannot edit, so it cannot share the environment's bugs.
- **Bypass register**: every check must have a written bypass entry; a check with no
  entry is a FAIL. No other skill makes this a hard rule.
- **Verifier verification**: the harness must fail when one check is flipped to
  always-pass. This proves the checks are load-bearing rather than decorative.
- **Explicit pass-rate floors**: `pass_good >= 0.80` and discriminating power
  `>= 0.30` are concrete numbers, not vibes.

## Near-miss triggers
- Verifier imports the environment module -> shares its bugs; rewrite against SPEC.md.
- A check has no bypass entry -> FAIL the check; you have not audited it.
- pass_good 0.6 vs pass_lazy 0.5 -> discriminating power 0.10; unusable.
- Sandbox contract network=allow or filesystem=open -> whole harness fails.
- Flipping a check to always-pass does not drop power -> the check is not load-bearing.
