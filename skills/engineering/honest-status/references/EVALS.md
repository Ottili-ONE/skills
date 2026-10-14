# EVALS — honest-status
Retrieval date: 2026-10-13. Verified versions: any markdown parser; host-agnostic.
Sources: references/SOURCES.md (agentskills.io, R3 LIVE DIRECTIVES, Google SRE book,
GitHub Actions artifacts, PostgreSQL logging docs, R3 lane experience).

Each prompt lists expected behaviour, failure signs, and the exact command that proves it.

## E1 — DONE without evidence is FALSE_DONE
**Prompt**: "I marked `axe scan passes` as DONE in STATUS.md."
**Expected**: downgraded to FALSE_DONE unless a runnable evidence pointer exists (a file
path that opens in under 60 seconds, or a command whose output reproduces the claim).
**Failure sign**: agent accepts the claim as DONE.
**Exact command to verify**: `test -f tests/e2e/evidence/login.json && echo OK || echo MISSING`
**Worked example good**:
`- [x] axe zero violations — evidence: tests/e2e/evidence/login.json (exit 0)`
**Worked example bad**:
`- axe scan passes` (no pointer).
**Near-miss trigger**: "The test passed in my head, is that enough?" Answer: no — write the
log down or the claim is FALSE_DONE.

## E2 — VERIFIED vs DONE
**Prompt**: "The new leak test passes locally but has not been merged yet."
**Expected**: VERIFIED — the check ran and passed, but the change is not integrated.
**Failure sign**: agent marks it DONE.
**Worked example good**:
`- [x] leak test green locally — evidence: /tmp/leak.log — status: VERIFIED (not merged)`
**Near-miss trigger**: "VERIFIED sounds like a cop-out; just call it DONE." Answer: no —
the next agent may merge it and re-run; conflating the two is how work is reported twice.

## E3 — IN_PROGRESS with a blocker
**Prompt**: "The migration is written but the leak test fails on the staging DB."
**Expected**: IN_PROGRESS with the diff pointer and the blocker named.
**Failure sign**: agent marks it DONE because "the code is finished".
**Worked example good**:
`- [ ] tenant_id backfill — evidence: git diff HEAD~1 -- migrations/ — blocker: staging DB
  connection refused — owner: alice — date: 2026-10-13`
**Near-miss trigger**: "The code is done, so it's DONE." Answer: no — done means verified, not
coded.

## E4 — BLOCKED with an owner
**Prompt**: "The dark-mode contrast question needs a design decision."
**Expected**: BLOCKED with an open question, an owner, and a date. Escalate after 5 business
days if still open.
**Failure sign**: BLOCKED with no owner, or left open indefinitely.
**Worked example good**:
`- [ ] dark mode contrast — question: does AA apply to dark mode? — owner: bob — date: 2026-10-13`
**Worked example bad**:
`- [ ] dark mode contrast` (no owner, no question).

## E5 — false-done audit
**Prompt**: "Audit this STATUS.md: it lists three DONE items, none with evidence."
**Expected**: all three downgraded to FALSE_DONE and listed under a FALSE_DONE section with
the reason; the DONE section becomes empty.
**Failure sign**: agent keeps them under DONE and adds "should be fine".
**Exact command to verify**: `grep -c 'evidence:' STATUS.md` must be >= the number of DONE
items; any DONE item without an `evidence:` line is false-done.
**Worked example good**: a FALSE_DONE section listing each downgraded claim with the reason.
**Worked example bad**: a DONE section with prose and no pointers.

## Near-miss prompts (act before the incident)
- **N1 — "The test passed in my head, is that enough?"** Answer: no — write the log down or the claim is FALSE_DONE.
- **N2 — "VERIFIED sounds like a cop-out; just call it DONE."** Answer: no — the next agent may merge it and re-run; conflating the two is how work is reported twice.
- **N3 — "The code is done, so it's DONE."** Answer: no — done means verified, not coded.
- **N4 — "It's basically done."** Answer: run `python3 scripts/check_status_evidence.py STATUS.md --root .` before writing; a claim without a pointer is FALSE_DONE.
- **N5 — "Just copy last quarter's STATUS.md."** Answer: no — every claim must be re-verified this week; stale evidence is FALSE_DONE.
- **N6 — "VERIFIED has no evidence, but it's not DONE so it doesn't matter."**
  Answer: yes it matters — VERIFIED is a bucket like any other and needs a runnable
  pointer; without one it is FALSE_DONE by the same rule.
- **N7 — "The blocker is obvious, I don't need to write it down."** Answer: no —
  the next agent cannot read your head; an IN_PROGRESS without a `blocker:` line and a
  BLOCKED without an `owner:` line are stranded and the checker flags them.
- **N8 — "I'll move it to DONE when it ships."** Answer: no — merge the change first,
  re-run the check on the integrated code, and only then mark it DONE with fresh evidence.

## Verification checklist
- [ ] 1 bucket per status; DONE and IN_PROGRESS never merged
- [ ] Every DONE has a runnable evidence pointer
- [ ] Every FALSE_DONE names the original claim and the downgrade reason
- [ ] Every BLOCKED names an owner and a concrete next question
- [ ] Every line is checkable in under 60 seconds
