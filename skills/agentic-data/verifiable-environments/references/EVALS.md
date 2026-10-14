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


## E11 — prove the harness detects a dead check
Prompt: "How do I prove my harness is not just reporting numbers?"
Expected: Generate fixtures with `scripts/gen_fixtures.py --out <dir>`, run
`scripts/verify_harness.py --checks checks.json --contract contract.json
--good good --broken broken --lazy lazy --neutered-checks checks_neutered.json
--json report.json`. It must exit 0 on the live run AND the neutered run must
drop power (the lazy agent, which writes output.json but no summary, now
passes every check). If power does not drop or the harness still exits 0, the
verifier is not verified. The procedure is in `references/neutering.md`.
Failure signs: harness exits 0 after a check is neutered; neutering all checks
instead of exactly one; a neutered check that is not actually always-pass.

## E13 — a check with one defence is a single point of failure
Prompt: "My check asserts that `summary.md` exists. Is that enough?"
Expected: No. Existence alone is one defence: the agent can `touch summary.md`
and pass without doing the intended work. Add a second independent defence
(content equality, a JSON field, a minimum word count, a keyword match, a
maximum length) and record both in the bypass register. Run
`scripts/verify_harness.py --bypass-audit SPEC.json REGISTER`; it rejects any
check with fewer than two defences with
`FAIL: check 'summary_file' has 1 defence(s); the rule of two requires >= 2
independent defences`.
Failure signs: a check with exactly one defence; the bypass-audit not run; a
check whose bypass register entry lists only one way to close the bypass.

## E12 — the bypass-audit catches a single-defence check
Prompt: "Audit my harness's checks against the bypass register."
Expected: `scripts/verify_harness.py --bypass-audit SPEC.json REGISTER.jsonl
--checks checks.json --contract contract.json --good good --broken broken
--lazy lazy`. Exit 0 only when every check has a register entry AND at least
two independent defences AND no check is `critical` severity. Exit 1 with a
per-check failure naming the missing defences.
Failure signs: the audit exiting 0 on a check with one defence; a check whose
register entry is missing; a `critical`-severity bypass that was not closed.


## E14 — reject a malformed check before it is run
Prompt: "My checks file has a check with `min_words: -5` and another with no
name. Does the harness catch it?"
Expected: Yes. `scripts/verify_harness.py --checks checks.json ...` validates the
shape of every check before running it: a missing `name`, a missing `path`, a
non-boolean `exists`, a negative `min_words`/`max_words`, a `keywords` list that
is empty, or a `json_field` without a `json_value` each produce a clear
`FAIL: check '<name>' ...` line and exit 1. The check never reaches the run
phase, so an opaque `KeyError` cannot occur.
Failure signs: the harness crashing with a traceback instead of a FAIL line;
a malformed check being silently treated as passing.

## E15 — the rule-of-two floor is configurable
Prompt: "My harness uses three defences per check. Can I require more?"
Expected: Yes, with `--min-defences N`. `scripts/verify_harness.py
--min-defences 3 ...` rejects any check with fewer than three independent
defences; `--min-defences 1` accepts a single-defence check. The default is 2
(the rule of two). Asking for 0 is rejected as out of range.
Failure signs: the floor being silently ignored; a `--min-defences 0` being
accepted.

## Near-miss prompts (trigger precision — these should NOT fire this skill)

## N1 — writing unit tests for ordinary software
Prompt: "Write unit tests for the `auth.py` module in my service."
Expected: No. That is ordinary software testing — pytest, fixtures, assertions. This skill is for *verifiers that resist reward hacking*: spec-derived checks the agent cannot edit, oracle-free tests, pass-rate calibration, bypass registers, sandboxing. A unit test for your own code is exactly the thing this skill warns about (the agent can edit both the code and the test).
Failure signs: treating `pytest` as a verifier; writing a check that imports the code under test.

## N2 — a benchmark that already has a leaderboard
Prompt: "Set up a benchmark for my agent using the existing MMLU leaderboard."
Expected: No. MMLU is a *fixed* benchmark with a known pass rate; this skill is for building *new* verifiable environments where the agent can game the score. Re-using an existing leaderboard adds no bypass audit and no calibration. Use the leaderboard's published numbers; do not re-run it as a verifier project.
Failure signs: running `verify_harness.py` against a frozen benchmark; writing a bypass register for a dataset nobody can edit.

## N3 — a checker that reads the agent's own log
Prompt: "My verifier reads the agent's trajectory log and checks it contains the word 'done'."
Expected: No. That is the *neutering* failure mode this skill exists to prevent: a check that reads the agent's own output is trivially satisfiable by writing the word "done" into the log. Every check must be derived from a spec the agent cannot edit (a `SPEC.md`, an oracle, a fixture). Route: rewrite the check against the spec, or neuter it with `scripts/verify_harness.py neuter`.
Failure signs: a check that greps the trajectory; a bypass register entry that reads "agent writes 'done'".
