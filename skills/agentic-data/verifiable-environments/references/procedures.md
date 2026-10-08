# Procedures — verifiable-environments

Verified 2026-10-09. Version-sensitive facts: sandbox APIs change; pin the API
revision you tested against and re-verify on upgrade.

## 0. The core invariant
A verifier is trustworthy only if a *rational but lazy* agent cannot reach a
pass without doing the intended work. Every check must be derived from a spec
that the agent cannot edit, and every bypass must be written down.

## 1. Spec-first verifier authoring
1. Write a one-page `SPEC.md` describing the *intended* outcome in observable
   terms: which files exist, which commands exit 0, which outputs match a
   canonical form.
2. The verifier imports `SPEC.md` (or reads it) and nothing from the
   environment package. If the environment module is importable from the
   verifier, the verifier shares the environment's bugs and can be
   reverse-engineered.
3. Keep the spec in a separate directory from the environment code, e.g.
   `evals/specs/` vs `env/`.

## 2. Check ordering (strongest to weakest)
1. **Observable outcome** — file at path, exit code, stdout equality. Preferred.
2. **Hidden state** — legitimate only for state with no observable side effect
   (e.g. an in-memory flag). Must be justified in a comment.
3. **Process proxy** — token count, number of tool calls, latency. Never score
   on these alone; a proxy is trivially faked.

## 3. Pass-rate calibration
- Run a known-good agent through the harness; record `pass_rate_good`.
- Run a deliberately broken agent; record `pass_rate_broken`.
- Run a deliberately lazy agent (stops after the first trivial check);
  record `pass_rate_lazy`.
- A usable harness has `pass_rate_good - pass_rate_lazy >= 0.3` and
  `pass_rate_good - pass_rate_broken >= 0.3`. If not, the checks have no
  discriminating power — rewrite, do not retune until the good agent passes.
- Re-derive thresholds on a held-out set. Never fit to the training set.

## 4. Reward-hacking audit (run per check)
For each check, answer: *can the agent reach this outcome without the intended
work?*
- Direct bypass: agent edits the check file, the spec, or the harness.
- Indirect bypass: agent finds an unintended path (e.g. writes the answer file
  directly instead of running the tool).
- Cosmetic bypass: agent reorders output, changes whitespace, renames keys.
Record the bypasses in `references/bypass-register.md`. A check with a direct
bypass is critical and must be redesigned.

## 5. Sandbox contract (pinned)
| Element   | Default        | Leak if set otherwise |
|-----------|----------------|-----------------------|
| Network   | deny           | agent fetches the answer |
| Filesystem| scoped tmpdir  | agent reads other runs |
| Exec      | allowlisted    | agent installs tools |
| Time      | bounded (300s) | agent stalls for credit |
| Secrets   | none exposed   | agent exfiltrates keys |

Pin the contract in a JSON file the harness reads at startup; the verifier
asserts the contract is active before any agent runs.

## 6. Verify the verifier
1. Run the harness on a *broken* agent (fails the intended step). Expect
   `pass_rate_broken < pass_rate_good - 0.3`.
2. Run the harness on a *lazy* agent (does the minimum). Expect
   `pass_rate_lazy < pass_rate_good - 0.3`.
3. If either scores within 0.3 of the good agent, the harness is broken — fix
   the checks, not the agents.

## Worked examples

Good — observable outcome check:
```python
def check_output_file():
    out = Path("/tmp/run/output.json")
    return out.exists() and json.loads(out.read_text())["status"] == "ok"
```

Bad — process proxy that can be faked:
```python
def check_tokens_used():
    return len(agent.trace) > 500  # agent writes 500 no-op tool calls
```

Good — sandbox assertion:
```python
def assert_sandbox():
    assert not net_enabled(), "network must be disabled"
    assert fs_root() == scoped_tmp(), "filesystem must be scoped"
```
