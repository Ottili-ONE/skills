---
name: honest-status
description: "Writing a STATUS.md that stays true: separates done/verified/in-progress/blocked, detects false-done claims, records evidence pointers, and writes handoff notes so the next agent does not repeat work. Use when asked to report status, write a handoff, audit a STATUS.md, or decide whether a task is really finished."
license: MIT-compat
compatibility: "framework-agnostic; text; any host"
metadata: {}
allowed-tools: []
---
# Honest Status Skill — Quick Reference (body <500 lines; full procedure in references/honest-status-procedure.md)

## When to use this skill (trigger)
- You are asked to write STATUS.md, a handoff note, or a progress report.
- You must decide whether a task is really DONE or merely "coded".
- A previous agent claimed something is finished and you need to audit it.
- You need evidence pointers that a human or another agent can actually open.

## When NOT to use this skill
- Writing a changelog or release notes (use the project's release process).
- Informal chat updates (use the chat thread).
- Status reports that are reviewed in the same session with no persistence need.

## Decision table — status bucket
| Bucket | Meaning | Required evidence |
|--------|---------|-------------------|
| DONE | Implemented AND verified by a runnable check | test/log/commit pointer |
| VERIFIED | A check ran and passed, but the change is not yet integrated | check output pointer |
| IN_PROGRESS | Work exists but the check has not passed yet | current diff pointer + blocker |
| BLOCKED | Cannot proceed without an external answer | open question + owner |
| FALSE_DONE | Claimed done but no evidence exists | flag, downgrade to IN_PROGRESS |

## Numbered procedure (summary; full recipe in references/honest-status-procedure.md)
1. **Enumerate claims** — list every claim in the current STATUS.md or handoff.
2. **Find evidence** — for each claim, locate a runnable artifact (test, log, command output).
3. **Classify** — DONE / VERIFIED / IN_PROGRESS / BLOCKED / FALSE_DONE using the decision table.
4. **Write the buckets** — one section per bucket; never merge DONE and IN_PROGRESS.
5. **Flag false-done** — any claim without evidence is downgraded and listed under FALSE_DONE.
6. **Add handoff notes** — what to retry first, what is missing, who owns the open question.
7. **Re-read aloud** — every line must be checkable in under 60 seconds.

## Pitfalls from research
- "Done" without a pointer is the most common lie; always require a runnable artifact.
- A green test for the wrong behaviour is not evidence of correctness.
- Copying a previous STATUS.md forward preserves its false-done claims.
- Vague blockers ("investigate later") are never resolved; name an owner and a date.
- Evidence that only exists in your head is not evidence; write it down.

## Verification checklist (all must pass before you finish)
- [ ] Every DONE entry has a runnable evidence pointer.
- [ ] No IN_PROGRESS entry is listed as DONE.
- [ ] FALSE_DONE claims are explicitly flagged and downgraded.
- [ ] BLOCKED entries name an owner and a concrete next question.
- [ ] Handoff notes tell the next agent what to retry first.
