# Pass-rate calibration — verifiable-environments

A verifier that cannot tell a good agent from a broken one is decoration. This
page records the three-agent calibration protocol and the numbers that decide
whether a harness is usable.

## The three agents

| Agent | Behaviour | What it proves |
|-------|-----------|----------------|
| Known-good | Does the intended work correctly | the upper bound of the harness |
| Deliberately broken | Fails the intended step on purpose | the harness can detect a real failure |
| Deliberately lazy | Does the minimum and stops | the harness cannot be satisfied by corner-cutting |

All three are *synthetic* agents run through the same harness, in the same
sandbox, with the same checks. They exist to calibrate the harness, never to
score a real agent.

## Thresholds

| Metric | Value | Meaning |
|--------|-------|---------|
| `pass_rate_good` | >= 0.80 | checks are not too strict |
| `power_vs_broken` = good - broken | >= 0.30 | harness detects real failure |
| `power_vs_lazy` = good - lazy | >= 0.30 | harness cannot be satisfied by laziness |
| Pass-rate drift window | 0-5 pts | noise |
| Pass-rate drift window | 6-20 pts | re-derive thresholds |
| Pass-rate drift window | >20 pts | verifier compromised, halt |

## Ordered calibration procedure

1. Run the known-good agent. Record `pass_rate_good`. If < 0.80, the checks are
   too strict — relax them, do not retune until the good agent passes.
2. Run the broken agent. Compute `power_vs_broken`. If < 0.30, the checks miss
   the failure mode — add an observable check for the failed step.
3. Run the lazy agent. Compute `power_vs_lazy`. If < 0.30, the checks reward
   corner-cutting — make the lazy agent's shortcut fail an observable check.
4. Re-derive thresholds on a **held-out** set. Never fit thresholds to the
   training set; that is the same error as tuning a model on its test set.
5. Flip one check to always-pass and re-run: `power` must drop and the harness
   must exit 1. If it still exits 0, the verifier is not verified.

## Decision table

| good | broken | lazy | Verdict |
|------|--------|------|---------|
| >=0.80 | <=good-0.30 | <=good-0.30 | usable |
| <0.80 | any | any | checks too strict, relax |
| any | >good-0.30 | any | missing broken detection, add check |
| any | any | >good-0.30 | rewards laziness, add check |
| any | any | any, after neutering a check | verifier not verified, halt |

## Near-miss triggers

- Calibrating until a *specific* agent passes -> overfit; the harness will not
  transfer to other agents.
- Using the training set as the calibration set -> inflated power.
- A lazy agent that scores 100% because "done" is the only check -> the harness
  has no discriminating power (pitfall P7).
- Re-running calibration after the harness has already been used to score real
  agents -> the thresholds are now fit to the population. Re-derive from the
  spec, not from the results.
