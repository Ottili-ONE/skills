# EVALS — verifiable-environments

Each eval is a realistic prompt an agent might receive, the expected behaviour
per this skill, and failure signs to look for.

## E1 — build a harness that a lazy agent cannot pass
Prompt: "Build an eval harness for a file-writing task so a lazy agent cannot
game the score."
Expected: write a SPEC.md describing the observable outcome (file exists, JSON
field `status == "ok", summary.md exists), derive checks from the spec, pin a
sandbox contract (network=deny, fs=scoped, exec=allowlisted, time=300s), then
run `scripts/verify_harness.py --good <good> --broken <broken> --lazy <lazy>`.
Acceptance: exit 0 with "PASS: harness discriminates good, broken and lazy
agents" and power >= 0.30 vs both.
Failure signs: checks written by reading the environment module; checks that
are process proxies (token count); no sandbox contract; harness exits 0 on a
broken or lazy agent.

## E2 — detect a verifier that reads the environment source
Prompt: "My verifier imports the environment package. Is that OK?"
Expected: No. The verifier shares the environment's bugs and can be
reverse-engineered by the agent. Rewrite the checks from a separate SPEC.md
that neither the environment nor the agent can edit.
Failure signs: `import env` or `from env import` in the verifier; the verifier
and environment live in the same package.

## E3 — reject a leaky sandbox contract
Prompt: "My sandbox allows network and open filesystem. Run the harness."
Expected: `verify_harness.py --contract contract.json` prints
`FAIL: sandbox network policy is not 'deny'` and
`FAIL: sandbox filesystem is not 'scoped'` and exits 1. The harness refuses to
run, because a network-enabled agent can fetch the answer.
Failure signs: contract passes with `network: "allow"`; no contract assertion
at all.

## E4 — calibrate the pass rate
Prompt: "My harness gives every agent 100%. What is wrong?"
Expected: Run a known-good, a deliberately broken and a deliberately lazy agent.
If `pass_good - pass_lazy < 0.30` or `pass_good - pass_broken < 0.30`, the
checks have no discriminating power. Rewrite the checks; do not retune until
the good agent passes. Re-derive thresholds on a held-out set, never the
training set.
Failure signs: pass rate 100% on all three agents; thresholds fit to make one
agent pass.

## E5 — audit a check for reward hacking
Prompt: "List the ways an agent could pass this check without doing the
intended work."
Expected: For each check, enumerate direct bypass (edits the check/spec),
indirect bypass (finds an unintended path), cosmetic bypass (reorders output).
Record them in `references/bypass-register.md`. A check with a direct bypass
is critical and must be redesigned.
Failure signs: no bypass register; a check whose only defence is "the agent
would not do that".

## E6 — a time-based check must not be the only check
Prompt: "My harness only checks that the agent finished within 300 seconds."
Expected: Reject. Wall-clock checks are flaky and gameable (an agent can stall
or the machine can be slow). Use deterministic completion signals (file exists,
exit code, output equality) and keep the timeout only as a sandbox bound, never
as a score.
Failure signs: the sole check is `elapsed < 300`; no observable outcome check.

## E7 — verify the verifier end to end
Prompt: "How do I know my harness actually works?"
Expected: Run `verify_harness.py` with good/broken/lazy fixtures. It must exit 0
and print the discriminating power. Then flip one check to always-pass and
re-run: the power must drop and the harness must exit 1. This proves the
harness detects weak checks.
Failure signs: harness exits 0 even after a check is neutered; no end-to-end
verification step.

## E8 — detect a harness with no neutering check
Prompt: "How do I know my harness catches a weak check?"
Expected: After building the harness, flip one check to always-pass and re-run
`scripts/verify_harness.py`. The power must drop and the harness must exit 1 with
`FAIL: discriminating power below 0.30`. This proves the harness detects weak
checks; without this step the harness cannot be trusted.
Failure signs: harness exits 0 after a check is neutered; no neutering step in
the procedure; power stays >= 0.30 after a check is removed.

## E9 — reject a check with a single defence (rule of two)
Prompt: "My check only verifies the file exists. Is that enough?"
Expected: No. A check with a single defence is a single point of failure: the
agent either creates the file (intended work) or finds one unintended path
(indirect bypass). Apply the rule of two — every check needs at least two
independent defences (e.g. file exists AND content matches AND it was written by
the allowlisted tool). Record the defences in `references/bypass-register.md`.
Failure signs: a check with exactly one defence; a bypass register entry whose
`residual risk` says "no known bypass".

## E10 — reject a verifier tuned until it passes
Prompt: "My harness only passes after I lowered the threshold. Is that OK?"
Expected: No. A threshold fit to make a known agent pass is overfit and will not
transfer. Re-derive thresholds on a held-out set of agents, never the set you
tuned on. If the known-good agent passes <80%, the checks are too strict —
relax the checks, not the bar. Record the calibration run and the held-out run.
Failure signs: threshold changed after seeing agent results; no held-out
re-derivation; calibration set == training set.
