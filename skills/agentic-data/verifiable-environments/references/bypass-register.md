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

## Worked examples

### check: `output.json exists and status == "ok"`
- direct bypass: agent writes `{"status": "ok"}` to the path -> high (the path is
  fixed, but the agent can still write the file directly). Mitigation: the check
  also asserts the file was produced by the tool (mtime after run start, or a
  content hash the tool emitted).
- indirect bypass: agent runs a no-op command that creates the file -> high.
  Mitigation: assert on content derived from the tool's real output.
- cosmetic bypass: none.

### check: `summary.md exists`
- direct bypass: agent `touch summary.md` -> high. Mitigation: assert minimum
  length and that it references the real output.
- indirect bypass: agent writes a one-word file -> low. Mitigation: min length.
- cosmetic bypass: none.

## Rule of two
A check that has only one defence is a single point of failure. Every critical
or high bypass must be closed by a second, independent check.
