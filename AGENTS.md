
## R3 LIVE DIRECTIVES

(Operator/Willi may edit; every task and pass reads ONLY this section of AGENTS.md: `sed -n '/R3 LIVE DIRECTIVES/,$p' AGENTS.md`. It wins over plan text about workflow, never over the safety rules.)

- READ BUDGET: this section, then only the files named after READ: in your task (docs/r3-context/<job>.md and <job>.blueprint.md are pre-extracted for you). Never open blueprint files, other modules' code or whole directories. At most 6 read commands before your first write.
- WRITE FIRST: first commit within 12 commands; rhythm: write one file -> run its test -> commit. Skeleton before detail. A task without a commit is a failed task.
- COMMIT MARKER: every commit message starts with the task id from the task text, e.g. `hq-crm-parties-r3-07: ...`. Commit only your own paths: `git add <paths> && git commit -m "..." -- <paths>`.
- GIT GUARD: push, checkout, switch, restore, stash, clean, rebase, merge, pull, `add -A`, `add .`, `commit -a`, `reset --hard` are blocked technically (exit 126). Do not look for workarounds (no /usr/bin/git); never revert other people's files.
- LIVE JOURNEYS: only via `acc-lock <product> -- <command>` (hq, ld3, console, alran-core, alran-clients, apps); hold at most 20 minutes; never nest.
- OWNERSHIP: docs/R3_OWNERS.json lists who owns which paths; the most specific glob wins; for anything else write docs/requests/<job>-<n>.md (3 lines).
- FREEZE: @ottili versions stay unchanged unless the integrator announces the Freeze 4 bump in docs/STATUS_ALL.md. DEV_FIXTURE_ALIAS stays 1 until the Platform lane p1-registration-r3 reports green.
- RESEARCH: curl is allowed for research tasks; record URL + retrieval date in the SOURCES.md of your area; never fetch private/link-local addresses.
- LANGUAGE: English for code, docs, commits, issues; i18n catalogues carry DE and EN.
- Operator notes: all jobs run on one host (Biest); no soft or hard stop; web research via curl is allowed; SEARCH_ENDPOINT none.
