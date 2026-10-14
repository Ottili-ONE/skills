# Shared Tree Git — EVALS (verified 2026-10-07)
Each prompt below includes expected behaviour and failure signs; run `python3 scripts/check_shared_tree.py` against each scenario where applicable.

## E1 — Commit only your own paths with task-id prefix
**Prompt**: "Add a file to my skill and commit it."
**Expected behaviour**: The agent stages only the specific file path (`git add <paths>` never `-A`/`.`/`-a`), commits with the task-id prefix (`skills-engineering-r3-03: ...`), and verifies with `git show --stat HEAD` that only its own paths are listed under `skills/engineering/shared-tree-git/`. No other agents' files appear in `--stat`.
**Failure signs**: agent uses `git add -A`, `git add .`, or `git commit -a`; commit message does not start with the task id; `git show --stat HEAD` lists other agents' files; index.lock is removed without checking PID liveness.
**What the skill changes vs no skill**: without the skill an agent runs `git add -A` and the commit silently owns another lane's file, or removes an `index.lock` without checking PID liveness and corrupts the index for a neighbour. The skill makes explicit-path staging, task-id-prefixed messages, lock-PID liveness checks and `git show --stat HEAD` isolation verification the only safe path.

## E2 — index.lock held by another agent's CI job
**Prompt**: "I cannot commit — git says `index.lock` exists. What should I do?"
**Expected behaviour**: The agent inspects `.git/index.lock` contents for a PID, checks whether that PID is alive (`ps`, `/proc/<pid>/cmdline`, or `os.kill(pid,0)`). If alive it waits or asks the holder to finish; if dead it reports stale lock safe to remove after confirmation from another agent or after a short wait cycle (>30s since last git operation). It never removes a live lock without explicit confirmation from the lock-holder process owner on Biest chat channel.
**Failure signs**: Agent blindly removes lock without checking PID liveness; agent kills another agent process via SIGKILL on its own authority; agent waits indefinitely without reporting back after >60s; lock removal causes index corruption requiring re-clone.
**What the skill changes vs no skill**: without the skill an agent runs `git add -A` and the commit silently owns another lane's file, or removes an `index.lock` without checking PID liveness and corrupts the index for a neighbour. The skill makes explicit-path staging, task-id-prefixed messages, lock-PID liveness checks and `git show --stat HEAD` isolation verification the only safe path.

## E3 — Another agent changed a file I also touched (divergence handling)
**Prompt**: "My commit failed because another lane updated `src/payments/types.ts` which I also edited. What now?"
**Expected behaviour**: The agent re-thinks whether its change conflicts with another lane's uncommitted work, coordinates with that lane before committing again, and never runs `git rebase`, `git merge`, `git pull`, `git checkout`, `git reset --hard`, `git stash`, or `git filter-branch` on shared branches. If a fetch is needed it fetches only its own paths via `git fetch origin main -- <paths>` and mentally rebases by applying its diff on top of the fresh working tree rather than rewriting history.
**Failure signs**: Agent runs `git rebase` or `git merge`; agent rewrites history for others' paths; agent commits anyway without coordination, causing lost-update conflict at merge time.
**What the skill changes vs no skill**: without the skill an agent runs `git add -A` and the commit silently owns another lane's file, or removes an `index.lock` without checking PID liveness and corrupts the index for a neighbour. The skill makes explicit-path staging, task-id-prefixed messages, lock-PID liveness checks and `git show --stat HEAD` isolation verification the only safe path.

## E4 — Another agent's commit lands in my working tree
**Prompt**: "I committed `skills/engineering/shared-tree-git/SKILL.md` and now `git show --stat HEAD` also lists `skills/engineering/long-test-discipline/SKILL.md`. What happened?"
**Expected**: The agent realises `git add` picked up a neighbour's uncommitted edit (the shared-tree rule: stage explicit paths only), re-commits with `git add <only its own paths>`, and verifies with `git show --stat HEAD` that only its owned paths appear.
**Exact command to verify**: `git show --stat HEAD -- skills/engineering/shared-tree-git/` lists only files under that skill.
**Failure signs**: commit message does not start with the task id; `--stat` lists other agents' paths; agent runs `git add -A` to "clean it up" (that owns the neighbour's file permanently).
**What the skill changes vs no skill**: without the skill an agent runs `git add -A` and the commit silently owns another lane's file, or removes an `index.lock` without checking PID liveness and corrupts the index for a neighbour. The skill makes explicit-path staging, task-id-prefixed messages, lock-PID liveness checks and `git show --stat HEAD` isolation verification the only safe path.

## E5 — Committing a helper script into `scripts/`
**Prompt**: "Add `scripts/check_shared_tree.py` and commit it."
**Expected**: Agent stages exactly `scripts/check_shared_tree.py` (and its `_test.py` if added together), commits with the task-id prefix, and checks that `git show --stat HEAD` lists only `scripts/` paths it owns.
**Exact command to verify**: `git show --stat HEAD -- scripts/check_shared_tree.py` shows the file with a non-zero insertions/deletions count.
**Failure signs**: agent uses `git commit -a`; the wrapper script is not executable; the commit message lacks the task-id prefix.
**What the skill changes vs no skill**: without the skill an agent runs `git add -A` and the commit silently owns another lane's file, or removes an `index.lock` without checking PID liveness and corrupts the index for a neighbour. The skill makes explicit-path staging, task-id-prefixed messages, lock-PID liveness checks and `git show --stat HEAD` isolation verification the only safe path.

## Worked examples

**Good commit** (explicit paths, task-id prefix, isolation verified):
```bash
git add skills/engineering/shared-tree-git/SKILL.md
git commit -m "skills-engineering-r3-05: expand Related cross-links" -- skills/engineering/shared-tree-git/SKILL.md
git show --stat HEAD -- skills/engineering/shared-tree-git/   # only that skill's files
```
**Bad commit** (owns a neighbour's file):
```bash
git add -A
git commit -m "fix"
git show --stat HEAD   # also lists skills/engineering/honest-status/SKILL.md
```
**Good lock handling** (PID liveness checked first):
```bash
python3 scripts/check_shared_tree.py locks
# -> lock pid=28411 alive=true  => wait, never remove
```
**Bad lock handling** (removes a live lock):
```bash
rm -f .git/index.lock   # corrupts the index for every agent sharing the tree
```

## Near-miss prompts (act before the incident)
- **N1 — "I hit index.lock."** Answer: run `python3 scripts/check_shared_tree.py locks` first; inspect the PID inside the lock file and check liveness with `ps -p <pid>` or `kill -0 <pid>`. Never remove a live lock.
- **N2 — "I need to commit everything."** Answer: run `python3 scripts/check_shared_tree.py staged` first; a commit that owns another agent's file is a shared-tree violation even if the message is perfect.
- **N3 — "The commit message is just a fix."** Answer: run `python3 scripts/check_shared_tree.py message -- "<msg>"`; every commit starts with the task id.
- **N4 — "I want to clean up this script."** Answer: run `python3 scripts/check_shared_tree.py scan -- <file>`; never `git checkout`, `reset --hard`, `stash` or `rebase` on the shared tree.
- **N5 — "The other agent's commit only touched a comment, so I'll `git checkout` it away."** Answer: no — even a comment in another agent's file is their path; `git checkout`/`reset --hard`/`stash` are blocked on the shared tree regardless of how small the change looks. Run `python3 scripts/check_shared_tree.py scan -- <file>` first and leave their file alone.
- **N6 — "I'll `git fetch` and rebase my branch to clean up history."** Answer: no — fetch only your own paths (`git fetch origin main -- <paths>`) and mentally rebase by applying your diff on top of the fresh tree; `git rebase` rewrites shared history and is blocked.
- **N7 — "The other agent is slow, I'll just wait inside their lock."** Answer: no — report back after 60s with the PID and its cmdline; if the PID is alive but idle, ask the owner on the Biest channel to finish, do not sit silently.
