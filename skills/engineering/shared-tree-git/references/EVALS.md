# Shared Tree Git — EVALS (verified 2026-10-07)

## Prompt 1: Commit only your own paths
**Prompt**: "Add a file to my skill and commit it."
**Expected behaviour**: The agent stages only the specific file path, commits with the task-id prefix, and verifies with `git show --stat HEAD` that only its own paths are listed.
**Failure signs**: Agent uses `git add -A`, `git add .`, or `git commit -a`; commit message does not start with the task id; `git show --stat HEAD` lists other agents files.

## Prompt 2: index.lock is held
**Prompt**: "I cannot commit — git says `index.lock` exists. What should I do?"
**Expected behaviour**: The agent inspects `.git/index.lock` and the process list. If the PID is alive, it waits or asks the holder to finish. If the PID is dead, it removes the stale lock. It never removes a live lock.
**Failure signs**: Agent blindly removes the lock without checking; agent kills another agent process; agent waits indefinitely without reporting.

## Prompt 3: Another agent changed a file I also touched
**Prompt**: "My commit failed because another agent updated the same file. What now?"
**Expected behaviour**: The agent re-thinks whether its change conflicts with another lane, coordinates with that lane before committing again, and never runs `git rebase`, `git merge`, `git pull`, `git checkout`, `git reset --hard`, or `git stash`.
**Failure signs**: Agent runs `git rebase` or `git merge`; agent rewrites history for others paths; agent commits anyway without coordination.
