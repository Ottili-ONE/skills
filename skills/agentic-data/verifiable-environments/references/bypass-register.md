# Bypass register — verifiable-environments

Every check gets a written bypass audit. A check whose bypass list is empty is
suspicious: it means nobody has thought about how to game it.

## Severity levels

| Severity | Meaning | Action |
|----------|---------|--------|
| critical | agent can edit the check, spec or harness | redesign the check |
| high | agent finds an unintended path to the outcome | close the path or add a second check |
| low | cosmetic: reorder, rename, reformat | document it; do not score on it |

## Template per check

```markdown
### <check name>
- observable outcome: <what it asserts>
- intended work: <what the agent must do>
- direct bypass: <how the agent edits the check/spec/harness> -> critical
- indirect bypass: <how the agent reaches the outcome without the work> -> high
- cosmetic bypass: <reorder/rename/reformat> -> low
- residual risk: <what is left uncaught>
```

## Rule of two
A check that has only one defence is a single point of failure. Every critical
or high bypass must be closed by a second, independent check.

## Worked examples

### output_file_exists
- observable outcome: `output.json` exists in the agent's output dir.
- intended work: the agent runs the tool that writes `output.json`.
- direct bypass: agent edits `checks.json` to remove the check -> critical. The
  checks file must live outside the agent's filesystem scope.
- indirect bypass: agent `touch output.json` -> high. The path is fixed, so the
  agent can create the file directly. Closed by `status_ok`, which requires real
  content; an empty file fails the JSON parse.
- cosmetic bypass: none.
- residual risk: a file with valid JSON but wrong content passes both checks;
  closed by `status_ok` asserting `status == "ok"`.

### status_ok
- observable outcome: `output.json` parses and `status == "ok"`.
- intended work: the agent produces a real output from the tool.
- direct bypass: agent edits `checks.json` -> critical (out-of-scope file).
- indirect bypass: agent writes `{"status": "ok"}` by hand -> high. Closed by
  `summary_file`, which requires a second artefact the agent must also fake, and
  by the sandbox contract (filesystem scoped, exec allowlisted) that makes
  hand-authoring the *only* path — which is why the bypass is recorded, not
  assumed impossible.
- cosmetic bypass: key order in the JSON -> low (JSON parse ignores it).
- residual risk: none remaining within the shipped three-check set.

### summary_file
- observable outcome: `summary.md` exists.
- intended work: the agent summarises the output.
- direct bypass: agent edits `checks.json` -> critical (out-of-scope file).
- indirect bypass: agent `touch summary.md` -> high. Closed by a minimum-length
  assertion (not in the shipped fixture, add it for real harnesses).
- cosmetic bypass: whitespace/heading style -> low.
- residual risk: a one-word summary passes. Add a min-length or keyword check
  before shipping this check for real.
