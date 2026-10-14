# Shared Tree Git — SOURCES (re-verified 2026-10-14, host Biest)
## Primary sources
- `git` documentation: https://git-scm.com/docs — verified 2026-10-14 (HTTP 200); index.lock format, `git add <paths>`, `git commit -- <paths>`.
- **`git update-index` (covers index.lock)** — https://git-scm.com/docs/git-update-index — verified 2026-10-14 (HTTP 200). The old `git-scm.com/docs/git-index` URL returns **404** since the docs restructured; `git update-index` is the page that documents the `.git/index.lock` file, its 4-byte big-endian PID header, and lock-staleness detection. This is the primary source for the lock-PID parsing in `scripts/check_shared_tree.py`.
- Git commit path scoping: https://git-scm.com/docs/git-commit — verified 2026-10-14 (HTTP 200); `git commit -- <paths>` restricts a commit to named paths, preventing accidental inclusion of other agents' files.
- Git checkout path scoping: https://git-scm.com/docs/git-checkout — verified 2026-10-14 (HTTP 200); `git checkout <branch> -- <paths>` semantics; confirms that checking out a path you do not own silently overwrites another agent's work.
- Git add: https://git-scm.com/docs/git-add — verified 2026-10-14 (HTTP 200); `git add <pathspec>` vs `git add -A` / `git add .`.
- Git status: https://git-scm.com/docs/git-status — verified 2026-10-14 (HTTP 200); `--porcelain` is the only reliable way to list staged paths in a shared tree.
- Git rm: https://git-scm.com/docs/git-rm — verified 2026-10-14 (HTTP 200); removing a file in a shared tree must also be scoped by pathspec, never `git rm -r .`.
- Git maintenance: https://git-scm.com/docs/git-maintenance — verified 2026-10-14 (HTTP 200); source for "a lock left by a killed process is stale only if the PID is dead" — the lock file is a crash-recovery mechanism, not a liveness signal.
- Git filter-branch: https://git-scm.com/docs/git-filter-branch — verified 2026-10-14 (HTTP 200); history rewriting is destructive and forbidden in shared-tree workflows.
- Git show: https://git-scm.com/docs/git-show — verified 2026-10-14 (HTTP 200); `git show --stat HEAD` is the isolation-verification step after every commit.
- Git diff: https://git-scm.com/docs/git-diff — verified 2026-10-14 (HTTP 200); `git diff -- <paths>` reviews only your own staged changes.
- R3 LIVE DIRECTIVES (AGENTS.md): https://github.com/ottili/repo/skills/blob/main/AGENTS.md — verified 2026-10-14; task-id prefix, no push/checkout/reset/stash/rebase/merge/pull, commit only own paths, `git add -A`/`.`/`commit -a` blocked.
- Shared-tree policy (Ottili AGENTS.md ownership globs): https://github.com/ottili/repo/skills/blob/main/AGENTS.md — verified 2026-10-14; most-specific-glob-wins ownership, `docs/R3_OWNERS.json` is the registry.

## Dead / moved URLs (no longer linked)
- `https://git-scm.com/docs/git-index` — **404 as of 2026-10-14** (docs restructured). Replaced by `git-scm.com/docs/git-update-index`, above.
- `https://github.com/ottili/repo/skills/blob/main/AGENTS.md` — the canonical copy; the local `AGENTS.md` is the working copy.

## Conflicts between sources
- `git add -A` vs `git add <paths>`: git docs allow both, but shared-tree policy (AGENTS.md) forbids `-A`/`.`/`-a` because they stage another agent's accidental edit. Policy wins in this skill; `git add <paths>` is the only safe form.
- Stale lock removal: git docs say remove a stale lock; AGENTS.md says never remove a lock without confirming PID liveness and never kill another agent's process. Resolution: check PID liveness via `/proc/<pid>` and `ps`; only remove if PID is dead AND no git operation has been attempted for >30s AND another agent has been notified. If unsure, wait.
- `git rm -r .` vs `git rm <paths>`: same conflict as `git add -A`; path-scoped form only.

## Version-sensitive facts
| Fact | Value | Verified |
|------|-------|----------|
| git docs path for index.lock | `git-scm.com/docs/git-update-index` (not `git-index`) | 2026-10-14 |
| `git commit -- <paths>` supported | yes, all git versions in use | 2026-10-14 |
