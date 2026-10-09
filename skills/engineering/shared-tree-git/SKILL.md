---
name: shared-tree-git
description: "Operates a shared git working tree where many agents commit concurrently: commits by path with the task-id prefix, never switches/resets/stashes, handles index.lock recovery, and diagnoses and repairs divergence without touching other agents' files."
license: MIT-compat
compatibility: "framework-agnostic; git CLI; Ottili shared-tree workflow"
metadata: {}
allowed-tools: []
---
# Shared Tree Git Skill — Quick Reference (body <500 lines; full procedure in references/shared-tree-git-procedure.md)

## When to use this skill (trigger)
- Multiple agents/lanes share one git working tree (Ottili, Biest host).
- You need to commit only your own paths with a task-id prefix.
- You hit `index.lock` and need to diagnose whether another agent holds it.
- Someone else's uncommitted change blocks your checkout/merge.
- You must verify your commit did not disturb other lanes.

## When NOT to use this skill
- Single-developer repos with normal git workflow.
- Repos where `git reset --hard`, `git checkout`, or `git stash` are permitted.
- Situations where you can simply push to a private branch.

## Decision table — git operation
| Operation | Safe? | When to pick | Pitfall |
|-----------|-------|-------------|---------|
| `git add <paths>` + `git commit -m "id: msg" -- <paths>` | Always safe | Every commit of your own paths | `git add -A` / `add .` / `commit -a` are blocked |
| `git status --porcelain` | Always safe | Check what you are about to commit | Does not tell you about lock holders |
| `git diff -- <paths>` | Always safe | Review your own staged changes | |
| `git log --oneline -n 20 -- <paths>` | Always safe | History of your own paths | Never rewrite history for others' paths |
| `git show --stat HEAD` | Always safe | Verify isolation of last commit | |
| `scripts/check_shared_tree.py` subcommands | Always safe | Pre-commit gate | |

## Numbered procedure (summary; full recipe in references/shared-tree-git-procedure.md)
1. **Check the lock** — `ls .git/index.lock` and `ps` to see who holds it; never remove a live lock.
2. **Stage only your paths** — `git add <your-paths>`; never `add -A`/`.`/`-a`/`.`.
3. **Commit with the task-id prefix** — `git commit -m "skills-engineering-r3-03: msg" -- <your-paths>`.
4. **Verify isolation** — `git show --stat HEAD` must list only your paths.
5. **Handle divergence** — if your commit fails due to a conflicting update, re-fetch only your paths and rebase mentally (never rebase/merge/pull).

## Pitfalls from research (real incidents)
- `index.lock` left by a killed CI job looks stale but is still live; removing it corrupts the index for the other agent ([git index docs](references/SOURCES.md#primary-sources)).
- `git add -A` stages another agent's accidental edit and your commit owns their file ([shared-tree policy](references/SOURCES.md#primary-sources)).
- A checkout of a path you do not own silently overwrites another agent's work ([git checkout semantics](references/SOURCES.md#primary-sources)).
- Committing with `--amend` rewrites history that another agent may have based work on ([history rewriting](references/SOURCES.md#primary-sources)).

## Near-miss trigger prompts (act on these immediately)
- "I hit index.lock" — run `scripts/check_shared_tree.py locks` before touching it.
- "I need to commit everything" — run `scripts/check_shared_tree.py staged` first.
- "The commit message is just a fix" — run `scripts/check_shared_tree.py message -- "<msg>"`.
- "I want to clean up this script" — run `scripts/check_shared_tree.py scan -- <file>`.

## Verification checklist (all must pass before you finish)
- [ ] No `index.lock` present, or held by a known process
- [ ] `git add` used explicit paths only
- [ ] Commit message starts with the task-id prefix
- [ ] `git show --stat HEAD` lists only your owned paths
- [ ] No `reset --hard`/`checkout`/`stash`/`rebase`/`merge`/`pull` run
