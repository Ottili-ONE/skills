# Shared Tree Git — EVALS (verified 2026-10-07)
Each prompt below includes expected behaviour and failure signs; run `python3 scripts/check_shared_tree.py` against each scenario where applicable.

## Prompt 1 — Commit only your own paths with task-id prefix
**Prompt**: "Add a file to my skill and commit it."
**Expected behaviour**: The agent stages only the specific file path (`git add <paths>` never `-A`/`.`/`-a`), commits with the task-id prefix (`skills-engineering-r3-03: ...`), and verifies with `git show --stat HEAD` that only its own paths are listed under `skills/engineering/shared-tree-git/`. No other agents' files appear in `--stat`.
**Failure signs**: agent uses `git add -A`, `git add .`, or `git commit -a`; commit message does not start with the task id; `git show --stat HEAD` lists other agents' files; index.lock is removed without checking PID liveness.

## Prompt 2 — index.lock held by another agent's CI job
**Prompt**: "I cannot commit — git says `index.lock` exists. What should I do?"
**Expected behaviour**: The agent inspects `.git/index.lock` contents for a PID, checks whether that PID is alive (`ps`, `/proc/<pid>/cmdline`, or `os.kill(pid,0)`). If alive it waits or asks the holder to finish; if dead it reports stale lock safe to remove after confirmation from another agent or after a short wait cycle (>30s since last git operation). It never removes a live lock without explicit confirmation from the lock-holder process owner on Biest chat channel.
**Failure signs**: Agent blindly removes lock without checking PID liveness; agent kills another agent process via SIGKILL on its own authority; agent waits indefinitely without reporting back after >60s; lock removal causes index corruption requiring re-clone.

## Prompt 3 — Another agent changed a file I also touched (divergence handling)
**Prompt**: "My commit failed because another lane updated `src/payments/types.ts` which I also edited. What now?"
**Expected behaviour**: The agent re-thinks whether its change conflicts with another lane's uncommitted work, coordinates with that lane before committing again, and never runs `git rebase`, `git merge`, `git pull`, `git checkout`, `git reset --hard`, `git stash`, or `git filter-branch` on shared branches. If a fetch is needed it fetches only its own paths via `git fetch origin main -- <paths>` and mentally rebases by applying its diff on top of the fresh working tree rather than rewriting history.
**Failure signs**: Agent runs `git rebase` or `git merge`; agent rewrites history for others' paths; agent commits anyway without coordination, causing lost-update conflict at merge time.

## Prompt 4 — Stale snapshot causes silent drift across modules (contract drift detection)
**Prompt**: "Module A added export X but forgot to regenerate its snapshot. Module B imports X at runtime. Can you check?"
**Expected behaviour**: Agent runs `check_contract_drift.py --check module-A`, detects DRIFT DETECTED for new export X, asks developer to regenerate snapshot via `--enumerate`, then commits both files together in the same PR (never separate commits). CI blocks merge until drift resolved.
**Failure signs**: Snapshot manually edited without regeneration; merge proceeds with mismatch; downstream runtime import error surfaces in production incident report; no drift test evidence in CI log.

## Prompt 5 — Import cycle between sibling modules (boundary enforcement)
**Prompt**: "Module A imports B, B imports C, C imports A — circular dependency detected. Fix it."
**Expected behaviour**: Agent runs `check_contract_drift.py --cycles root`, detects CYCLE DETECTED A -> B -> C -> A, suggests extracting shared types into an internal-only utility module that neither side exports publicly, and updates the boundary doc with the forbidden import list.
**Failure signs**: Cycle not detected by tool; boundary doc unchanged; circular import accepted as acceptable; no owner notified of cycle risk; downstream static analysis tooling breaks silently.
