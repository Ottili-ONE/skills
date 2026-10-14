# Verifier Design — verifiable-environments

Verified 2026-10-14. This page turns the SKILL.md invariant into a concrete,
ordered design procedure with thresholds and a decision table for choosing check
types. A verifier is trustworthy only if a *rational but lazy* agent cannot reach
a pass without doing the intended work.

## 0. The invariant, restated
Every check is derived from a spec the agent cannot edit, and every bypass is
written down. If you cannot write the bypass for a check, you have not audited
it. A check with no bypass-register entry is a FAIL, not a safe check.

## 1. Design order (do not reorder)
1. Write the **spec** first (`SPEC.md`), in observable terms. The verifier reads
   the spec; it never imports the environment module.
2. Enumerate the **intended work** the agent must perform (the tool it must run,
   the file it must produce).
3. For each piece of intended work, write **checks** from strongest to weakest
   (see the check-type table below).
4. For each check, write the **bypass register entry** before the check ships.
5. **Calibrate** with three agents (good / broken / lazy) and record the numbers.
6. **Verify the verifier** by neutering one check and re-running: power must
   drop and the harness must exit 1.

## 2. Check-type decision table (strongest to weakest)
| Rank | Type | Example | Fakes if |
|------|------|---------|----------|
| 1 | Observable outcome | file exists AND content equals canonical | agent `touch`es the file or writes a literal |
| 2 | Hidden state | in-memory flag with no side effect | agent edits the verifier (critical, out of scope) |
| 3 | Process proxy | token count, tool-call count | agent loops a no-op tool (never score alone) |

**Rule**: prefer type 1. Type 2 is legitimate only when the state has no
observable side effect, and must carry a comment justifying it. Type 3 is never
a check by itself.

## 3. Thresholds (do not retune to make an agent pass)
| Metric | Threshold | Action if violated |
|--------|-----------|--------------------|
| `pass_good - pass_lazy` | >= 0.30 | rewrite checks; do not retune |
| `pass_good - pass_broken` | >= 0.30 | rewrite checks; do not retune |
| `min(pass_good - pass_lazy, pass_good - pass_broken)` | >= 0.30 | harness has no discriminating power |
| `pass_good` | >= 0.80 | checks too strict; relax them |
| Defences per check | >= 2 | add a second defence (rule of two) |
| Bypass-register entries | 1 per check | the check is unaudited |
| `spec_ref` per check | must be a literal substring of SPEC.md | the check was not derived from the spec |
| Pass-rate drift | 0-5 pts noise; 6-20 re-derive; >20 halt | verifier compromised |

## 4. Bypass register template (one entry per check)
```markdown
### <check name>
- observable outcome: <what it asserts>
- intended work: <what the agent must do>
- direct bypass: <how the agent edits the check/spec/harness> -> critical
- indirect bypass: <how the agent reaches the outcome without the work> -> high
- cosmetic bypass: <reorder/rename/reformat> -> low
- residual risk: <what is left uncaught>
```
A row that says "no known bypass" is a check nobody has audited. Write the
bypass even when you think it is impossible.

## 5. Worked examples

### Good — file-copy task, three defences
Checks: `file_exists` AND `content_equals` AND `written_by_allowlisted_tool`.
1. Known-good agent copies the file: passes all three.
2. Broken agent copies nothing: fails all three.
3. Lazy agent writes an empty file: fails `content_equals` and
   `written_by_allowlisted_tool`.
4. `pass_good=1.0, pass_broken=0.0, pass_lazy=0.0`, power = 1.0 >= 0.30.
5. Neuter `content_equals` to always-pass: lazy agent now passes 2/3, power
   drops to 0.33, harness exits 1.

### Bad — "did the agent finish?" as the only check
Broken and lazy agents both "finish"; pass rate is 100% for every agent, so
`pass_good - pass_lazy = 0.0`. The harness has no discriminating power and must
be redesigned, not retuned.

### Bad — verifier that imports the environment module
`from environment import run_checks`. The verifier shares the environment's
bugs, can be reverse-engineered, and has no bypass-register entry. Rewrite it
against a spec.
