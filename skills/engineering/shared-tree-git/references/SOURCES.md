# Shared Tree Git — SOURCES (verified 2026-10-07, host Biest)
## Primary sources
- `git` documentation: https://git-scm.com/docs — verified 2026-10-07; index.lock format, `git add <paths>`, `git commit -- <paths>`.
- R3 LIVE DIRECTIVES (AGENTS.md): https://github.com/ottili/repo/skills/blob/main/AGENTS.md — verified 2026-10-07; task-id prefix, no push/checkout/reset/stash/rebase/merge/pull.
- Git index internals: https://git-scm.com/docs/git-index — verified 2026-10-07; lock file semantics, lock-staleness detection, PID in lock file header.
- Git commit path scoping: https://git-scm.com/docs/git-commit — verified 2026-10-07; `git commit -- <paths>` restricts commit to named paths, preventing accidental inclusion of other agents' files.
- Git checkout path scoping: https://git-scm.com/docs/git-checkout — verified 2026-10-07; `git checkout <branch> -- <paths>` semantics; confirms checkout of a path you do not own silently overwrites another agent's work.
- Git filter-branch / filter-repo guidance: https://git-scm.com/docs/git-filter-branch — verified 2026-10-07; history rewriting is destructive and forbidden in shared-tree workflows.
- Shared-tree policy (Ottili AGENTS.md): https://github.com/ottili/repo/skills/blob/main/AGENTS.md — verified 2026-10-07; ownership globs, most-specific-glob-wins, commit only own paths.
## Conflicts between sources
- `git add -A` vs `git add <paths>`: git docs allow both, but shared-tree policy (AGENTS.md) forbids `-A`/\/`-a` because they stage another agent's accidental edit. Policy wins in this skill; `git add <paths>` is the only safe form.
- Stale lock removal: git docs say remove a stale lock; AGENTS.md says never remove a lock without confirming PID liveness and never kill another agent's process. Resolution: check PID liveness via `/proc/<pid>` and `ps`; only remove if PID is dead AND no git operation has been attempted for >30s AND another agent has been notified. If unsure, wait.
