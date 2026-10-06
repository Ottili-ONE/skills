
## R3 LIVE DIRECTIVES

(Willi and the operator may edit this section at any time; every task and every pass re-reads it. It wins over the plan text about workflow and priorities, never over the SAFETY RULES of the plan.)

- Round: R3, started 2026-10-06/07. No scheduled stop (operator decision by Willi, 2026-10-06): the round runs until all jobs are finished. Round 4 follows.
- Commit marker: every commit message starts with the task id from the task text, for example `hq-crm-parties-r3-07: ...`. Watchdog and harvest read this marker.
- Ownership: docs/R3_OWNERS.json lists which job owns which paths; the integrator job merges it into OWNERS.md; the most specific glob wins. Never edit paths you do not own: write docs/requests/<job>-<n>.md instead.
- Freeze: @ottili package versions stay unchanged unless the integrator job announces the Freeze 4 bump in docs/STATUS_ALL.md.
- DEV_FIXTURE_ALIAS: stays 1 until the Platform lane p1-registration-r3 reports green in docs/m1/lanes/p1-registration/STATUS.md; then the integrator flips the default.
- Dev instance and worlds: use only the world configured in .env for your product; follow the acceptance-lock rules; never POST /__dev/reset; never create worlds; never restart shared services.
- Research: outbound web access via curl is allowed for research tasks. SEARCH_ENDPOINT: none configured yet (operator fills in). Record every source with URL and retrieval date in the SOURCES.md of your area; never fetch private or link-local addresses.
- Blueprints: ../ottili-planning/inputs/ (HQ v2.0 Core-Maximal wins over HQ v1.0). Facts verified online on 2026-10-06: ../ottili-planning/inputs/R3_VERIFIED_FACTS.md (re-verify before relying on them).
- Language: English for code, comments, documentation, commits and issues; i18n catalogues carry DE and EN.
- WRITE EARLY (operator, 2026-10-06 22:50 UTC): reading is not progress. After at most 15 shell commands of reading you MUST create or edit a file (apply_patch) in your owned paths, even a first draft, a failing test, or the task notes file. Never only read and run tests in a pass. Then `git add <your files>` and `git commit -m "<task-id>: <what changed>"` as soon as a small step works; repeat per step. If a test fails because of something outside your paths, write docs/requests/<job>-<n>.md and continue with the next step. Do not loop on the same command: after 2 identical failures change approach.
- Operator notes: all jobs run on one host (Biest); no soft or hard stop; web research via curl is allowed; SEARCH_ENDPOINT none.
