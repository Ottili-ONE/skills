# Shared Tree Git — Full Procedure (verified 2026-10-07)

## 1. Check the lock before touching git
```bash
ls -la .git/index.lock 2>/dev/null && ps aux | grep -v grep | grep git || echo "no lock"
```
If `.git/index.lock` exists and the PID is alive, wait or ask the holder to finish. Never remove a live lock — removing it corrupts the index for the other agent. If the PID is dead, the lock is stale and safe to remove: `rm .git/index.lock`.

## 2. Stage only your paths
Always use explicit paths:
```bash
git add skills/engineering/shared-tree-git/SKILL.md -- skills/engineering/shared-tree-git/SKILL.md
```
Never use `git add -A`, `git add .`, or `git commit -a` — these stage other agents changes and your commit owns their file.

## 3. Commit with the task-id prefix
```bash
git commit -m "skills-engineering-r3-03: add shared-tree-git procedure" -- skills/engineering/shared-tree-git/SKILL.md
```
The message must start with the task id (e.g., `skills-engineering-r3-03:`). The `-- <paths>` at the end limits the commit to those paths only.

## 4. Verify isolation
After committing, run:
```bash
git show --stat HEAD
```
The output must list only your owned paths. If it lists other agents files, you staged too much — revert immediately (but do not rewrite history for others).

## 5. Handle divergence
If your commit fails because another agent updated a file you also touched, re-fetch only your paths mentally (never rebase/merge/pull). Ask yourself: "Did I change something that conflicts with another lane?" If yes, coordinate with that lane before committing again.
Never run `git checkout`, `git reset --hard`, `git stash`, `git rebase`, `git merge`, or `git pull` in a shared tree — these rewrite history or switch branches and disturb other agents work.
NEVER rewrite history for others paths — even if you think it is safe, it breaks their work tree silently.
EVERY commit must list only your owned paths in `--stat`.
