# Shared Tree Git — Full Procedure

Retrieval date: 2026-10-13. Host: Biest. Verified versions: git 2.4x (CLI semantics stable since 2.0).
Sources: `references/SOURCES.md`. Evals: `references/EVALS.md`.
Helper: `scripts/check_shared_tree.py` (offline, deterministic; `--help` for subcommands).

## 0. Invariants
1. Never `push`, `checkout`, `switch`, `restore`, `stash`, `clean`, `rebase`, `merge`, `pull`,
   `add -A`, `add .`, `commit -a`, or `reset --hard` — these are blocked technically (exit 126) and
   forbidden by policy.
2. Commit only your owned paths, with the task-id prefix `<lane>-<product>-r3-<n>: <msg>`.
3. Never touch another lane's files, even if they look wrong. Report to the owner instead.
4. Never remove an `index.lock` without confirming PID liveness and notifying the holder.

## Step 1 — Check the index lock
| State | Action | Pitfall |
|-------|--------|---------|
| No lock | Proceed | — |
| Lock + live PID | Wait; ask the holder | Removing a live lock corrupts the index |
| Lock + dead PID (>30 min old) | Remove after `ps`/`/proc/<pid>` confirm | Removing a live lock = corruption |
| Lock + unknown PID, <5 min old | Wait; do not remove | Removing mid-write = corruption |

Threshold: if a lock has been present >60 min with no matching process on Biest, escalate to the
lane owner rather than removing it yourself.

Near-miss trigger: "two agents hit index.lock at the same time" — both must serialize via the
`locks` check; never remove concurrently.

## Step 2 — Stage only your paths
```bash
git add <your-paths>
git diff --cached --name-only
```
Verify every staged path starts with your owned prefix.

Worked example (good): `git add skills/engineering/shared-tree-git/SKILL.md scripts/check_shared_tree.py`
then verify each line starts with `skills/engineering/`.

Worked example (bad): the developer runs `git add -A`, which stages another agent's accidental edit
in `scripts/build-index.py`. The commit now owns their file and CI runs their untested code.

Detection pattern: staged paths outside the owned prefix = automatic abort; re-stage only yours.

Near-miss trigger: "I'm about to commit everything" — run
`python3 scripts/check_shared_tree.py staged` first; abort if any path is outside the prefix.

## Step 3 — Commit with the task-id prefix
```bash
git commit -m "skills-engineering-r3-03: msg" -- <your-paths>
```
Prefix format: `<lane>-<product>-r3-<n>: <msg>`.

Worked example (good): `"skills-engineering-r3-03: add near-miss triggers to shared-tree-git SKILL.md"`
commits only the listed paths with the correct prefix.

Worked example (bad): `"fix stuff"` without a prefix — untraceable in the shared tree; blocks the audit
trail.

Common trap #1: `--amend` rewrites history that another agent may have based work on. Never amend in a
shared tree unless you are certain no one else pulled the commit.

Common trap #2: `-a` stages tracked files regardless of ownership. Always use explicit paths or `--`.

Threshold: if a commit touches >5 paths outside your prefix, abort and investigate why they appeared
in your working tree.

Near-miss trigger: "I want to amend to fix the message" — amending is history rewriting; use a new
commit instead and leave the old one for the audit trail.

## Step 4 — Verify isolation
```bash
git show --stat HEAD
```
Must list ONLY your owned paths plus new files under your prefix. If other agents' files appear,
revert immediately (`git revert HEAD`) and investigate how they got staged.

Near-miss trigger: "my commit includes someone else's file" — revert immediately, re-stage only yours,
recommit with the correct prefix, and report the incident to the lane owner in the same PR description.

## Step 5 — Handle divergence
If a commit fails due to a conflicting update from another lane, do NOT rebase/merge/pull.
Fetch only your paths mentally (read their diff), decide whether yours still applies, and recommit
on top after pulling their changes through the normal lane process.

| Situation | Safe action | Forbidden action | Pitfall |
|-----------|-------------|------------------|---------|
| Divergent update on owned path | Re-fetch mentally, recommit on top after lane pull | rebase / merge / pull / reset --hard / stash / checkout | silently overwrites their work or rewrites history they depend on |
| Unrelated conflict outside owned path | Ignore it completely; never touch it | touch it at all | Never touch another lane's files even if they look wrong |

## Offline verification helper
Run before every commit chain:
```bash
python3 scripts/check_shared_tree.py --cwd . locks
python3 scripts/check_shared_tree.py --cwd . staged
python3 scripts/check_shared_tree.py --cwd . message -- "<msg>"
python3 scripts/check_shared_tree.py scan -- scripts/<your-script>.sh
```

## Verification checklist (all must pass before merge)
- [ ] `index.lock` either absent or held by a live PID
- [ ] `git diff --cached --name-only` lists only owned paths
- [ ] Commit message starts with `<lane>-<product>-r3-<n>:`
- [ ] `git show --stat HEAD` lists only owned paths
- [ ] No `--amend`, no `-a`, no `add -A`, no `reset --hard`, no `checkout`, no `stash`, no `rebase/merge/pull`
