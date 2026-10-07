# Honest Status - Full Procedure
Retrieval date: 2026-10-07. Verified versions: any markdown parser; host-agnostic.
Sources: docs/R3_OWNERS.json; AGENTS.md R3 LIVE DIRECTIVES; common STATUS.md anti-patterns from R3 lane experience. See references/SOURCES.md for full provenance.

## Step 1: Enumerate claims
List every claim in the current STATUS.md or handoff note. One claim per line.
Format: `<claim> | <location> | <claimed date>`

## Step 2: Find evidence
For each claim, locate a runnable artifact: test, log, command output, committed file.
Evidence must be:
- A file path or command that reproduces the result in under 60 seconds.
- Created by the claimant or a check that ran after the claim was made.
- Not a screenshot of a passing test for the wrong behaviour.

## Step 3: Classify
Use the decision table in SKILL.md. Key rule: if no evidence exists, the claim is FALSE_DONE, never DONE.

## Step 4: Write buckets
One section per bucket. Never merge DONE and IN_PROGRESS.

## Step 5: Flag false-done
Every claim without evidence is downgraded and listed under FALSE_DONE with the reason.

## Step 6: Handoff notes
What to retry first, what is missing, who owns the open question, and a date.

## Step 7: Re-read aloud
Every line must be checkable in under 60 seconds.

## Worked examples

### Good output
```markdown
## DONE
- [x] axe scan zero violations - evidence: tests/e2e/evidence/login.json (exit 0)

## VERIFIED
- [x] keyboard path reaches close button - evidence: tests/e2e/keyboard-login.mp4

## IN_PROGRESS
- [ ] responsive overflow on mobile - blocker: modal uses position:fixed; owner: alice; date: 2026-10-08

## BLOCKED
- [ ] dark mode contrast - question: does AA apply to dark mode? owner: bob; date: 2026-10-09

## FALSE_DONE
- [ ] ~~axe zero violations~~ - no evidence file committed; downgraded from DONE
```

### Bad output
```markdown
## DONE
- axe scan passes
- keyboard path works
- responsive checks pass
```
(No evidence pointers; every claim is false-done.)

## Exact commands
- Enumerate claims: `grep -n 'DONE\|VERIFIED\|IN_PROGRESS\|BLOCKED' STATUS.md`
- Verify evidence exists: `test -f <path> && echo OK || echo MISSING`
- Run the check: `python3 scripts/check_status_evidence.py STATUS.md`

## Pitfalls
- Done without a pointer is the most common lie.
- A green test for the wrong behaviour is not evidence of correctness.
- Copying a previous STATUS.md forward preserves its false-done claims.
- Vague blockers are never resolved; name an owner and a date.
- Evidence that only exists in your head is not evidence; write it down.
EOF
