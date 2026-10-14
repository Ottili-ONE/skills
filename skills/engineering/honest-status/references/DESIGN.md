# DESIGN — honest-status

## Trigger description (draft)
Fires when: an agent must write or review a STATUS.md handoff; when a claim of "done" has no
attached evidence; when a task reports a partial result; or when an operator asks "is this
still true?". Does NOT fire for: informal chat status, or commit messages (those follow the
task-id prefix rule in AGENTS.md).

## What it does better than existing public skills
No public skill addresses the truthfulness of status reports. The difference is mechanical:
this skill defines an evidence rule (every DONE must name a command + observed output a reader
can re-run in under 60 seconds), a false-done detector (DONE without evidence pointer, or a
test skipped without a STATUS.md entry), and a tri-state status vocabulary (DONE / PARTIAL /
BLOCKED / UNKNOWN). It also records handoff notes so the next agent does not re-derive context.

## Procedure outline
1. Write the four states only: DONE, PARTIAL, BLOCKED, UNKNOWN. Never "in progress" as a final state.
2. For every DONE: attach evidence — the exact command, the exit code or key line of output, and
   where the log lives. A claim without evidence is downgraded to UNKNOWN.
3. Run the false-done detector before saving: is there a commit for this work? Was the test run,
   or is it listed as skipped with a reason in STATUS.md?
4. For PARTIAL: name what is missing and what unblocks it.
5. For BLOCKED: name the blocker, who owns it, and the next command to try.
6. End with handoff notes: what the next agent should re-verify, and what must not be assumed.

## Scripts (shipped)
- `scripts/check_status_evidence.py` — parses STATUS.md, flags DONE/VERIFIED entries lacking an
  evidence pointer that resolves to a non-empty file (downgrades them to FALSE_DONE), exits 1.
  Self-tested via `check_status_evidence_test.py`.

## Five eval prompts
1. "Mark the migration as done." → agent must attach the migration apply log and the rollback test result; otherwise it stays PARTIAL.
2. "The test suite is skipped." → agent must record the skip reason in STATUS.md or change the state to BLOCKED.
3. "Write a handoff for the outbox work." → agent lists DONE (with evidence), PARTIAL (poison handling), and what to re-verify.
4. "Is 'tests pass' enough evidence?" → No. Agent must name the command (`pytest -q`) and the summary line.
5. "The build is green in the dashboard but I did not run it." → agent must mark UNKNOWN and record who ran it, or run it.
6. "The STATUS.md says DONE but the test was skipped in CI." -> agent must downgrade to BLOCKED or FALSE_DONE, name the skip reason and the owner, and re-run the test or record why it cannot run.
