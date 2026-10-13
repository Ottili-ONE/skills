# DESIGN — shared-tree-git

## Trigger description (draft)
Fires when: several agents share one git working tree (Ottili, Biest host); an agent must commit
only its own paths; `index.lock` is present; a commit fails because another agent updated the
tree; or the working tree has diverged from HEAD and the agent must diagnose without rewriting
history. Does NOT fire for: single-developer repos where `reset`/`checkout`/`stash`/`rebase` are
allowed, or for pushing to a private branch.

## What it does better than existing public skills
Git docs explain each command; they do not explain the shared-tree constraint. This skill fixes
the safe-operation table (only `git add <paths>` + `git commit -m "id: msg" -- <paths>` is always
safe; `add -A`, `add .`, `commit -a`, `reset`, `checkout`, `stash`, `rebase`, `merge`, `pull`,
`filter-repo` are blocked), the index.lock diagnosis procedure (read the PID from the lock header,
check `/proc/<pid>` and `ps`, never remove a live lock), and the divergence repair (re-fetch only
your paths, never rebase). It records the real incident: an agent removed an `index.lock` that a
killed CI job had left, which corrupted the index for the other agent whose commit then failed
silently.

## Procedure outline
1. Before touching the index: `ls .git/index.lock`; if present, read the PID, check liveness.
   Only remove a lock whose PID is dead AND no git op has run for >30s AND another agent was
   notified. If unsure, wait.
2. Stage only owned paths: `git add <path1> <path2>`. Never `add -A`/`.`/`-a`.
3. Commit with the task-id prefix: `git commit -m "skills-engineering-r3-<n>: <msg>" -- <paths>`.
4. Verify isolation: `git show --stat HEAD` must list only your paths.
5. If a commit fails on a conflicting update: re-fetch only your paths (`git checkout HEAD -- <paths>`,
   which is path-scoped and safe) and re-apply; never `rebase`/`merge`/`pull`.
6. Diagnose divergence: `git status --porcelain`, `git log --oneline -n 20 -- <paths>`, and
   `scripts/check_shared_tree.py scan -- <file>`.

## Scripts planned
- `scripts/check_shared_tree.py` — subcommands `locks`, `staged`, `message`, `scan`.

## Five eval prompts
1. "I hit `index.lock`; just remove it." → agent must run `scripts/check_shared_tree.py locks`,
   verify the PID, and only remove if dead + stale + notified; otherwise wait.
2. "Commit everything I changed." → agent must run `scripts/check_shared_tree.py staged` first;
   `git add -A` is blocked.
3. "The commit message is 'fix typo'." → agent must run `scripts/check_shared_tree.py message` and
   add the task-id prefix.
4. "Rebase onto main to clean up." → agent must refuse; history rewriting is forbidden in a
   shared tree.
5. "My commit included another agent's file." → agent must re-check with `git show --stat HEAD`
   and, if so, revert only that path and re-commit; never `reset --hard`.
