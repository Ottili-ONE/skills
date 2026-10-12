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
4. "The sandbox contract sets network: allow. Can the harness run?" -> No: a leaky
   contract fails the whole harness regardless of check quality.
5. "I flipped one check to always-pass and the pass rate did not change." -> The check
   has no power; the verifier must exit 1.

## What this skill does better than a generic agent
A generic agent writes unit tests that pass on its own code. This skill separates spec
from implementation, mandates oracle-free observable checks, pins a sandbox contract,
requires a bypass register with severity levels, and calibrates pass rates against
good/broken/lazy agents. It prevents the common incident of a "verifier" that passes
every agent because the checks were written against the implementation and the agent
can read them.

## What existing public skills do (and what this one does differently)

Surveyed on 2026-10-12. `anthropics/skills` ships no evaluation-harness skill; the
closest content is `template-skill` (how to write a skill) and the SDKs behind
`openai/evals`, which is a harness library, not an agent skill. The Fastio 2026
directory lists `Code-Reviewer` and `Design Auditor` — judges of artefacts, not
verifiers of agent behaviour. `skills.cat` has no entry for verifiable environments.

This skill is the only one that treats the *verifier* as the thing that must be
proven, not assumed:
- **Harness contract is machine-readable**: `scripts/gen_fixtures.py --out <dir>`
  writes SPEC.md, contract.json, contract_broken.json, checks.json and
  checks_neutered.json plus good/broken/lazy agent dirs — a harness that cannot be
  fed a known-broken agent is unproven.
- **Reward hacking is named, not hand-waved**: the skill enumerates the actual
  bypass classes (finish-check decoration, environment-import, threshold gaming,
  oracle leakage, metric substitution) and requires each to be either covered by a
  check or entered in the bypass register with a justification.
- **Power is measured, not asserted**: `scripts/verify_harness.py` reports power
  against good/broken/lazy agents and exits non-zero when the harness cannot
  discriminate. Neutering a check must drop power, or the check was decorative.
- **Pass-rate calibration**: the pass rate on a known-good population is recorded
  as a baseline; a verifier whose pass rate drifts upward against that baseline is
  suspect, regardless of what the individual checks say.
- **Bypass register is machine-readable**: a legitimate exception is a JSON entry
  with a `reason` and a `reviewed_by` field, not a comment in a check. The register
  is auditable.

Public sources surveyed (2026-10-12, all HTTP 200):
| Source | What it has | Gap this skill fills |
|--------|-------------|---------------------|
| `github.com/openai/evals` | eval harnesses | no verifier-of-verifier, no power metric, no bypass register |
| `anthropics/skills` (template-skill) | skill authoring convention | not a verification harness |
| `Code-Reviewer` / `Design Auditor` (Fastio) | artefact judges | do not verify agent behaviour or resist reward hacking |
