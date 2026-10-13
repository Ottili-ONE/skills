# Sources — honest-status
Retrieval date: 2026-10-13. All URLs fetched with curl; HTTP status recorded.

## Primary sources
1. **Agent Skills standard (agentskills.io)** — https://agentskills.io/. Verified 2026-10-13
   (HTTP 200). The standard mandates a `description` field of at most 1024 characters and
   progressive disclosure (long material in `references/`, linked one level deep from
   `SKILL.md`). This skill's STATUS.md format follows the same evidence-pointer discipline:
   every claim must be checkable in under 60 seconds. URL: https://agentskills.io/ — retrieved
   2026-10-13.
1a. **Agent Skills specification text (canonical)** — https://raw.githubusercontent.com/agentskills/agentskills/main/docs/specification.mdx. Verified 2026-10-13 (HTTP 200). The exact rule text behind the 1024-char description limit, the ≤64-char lowercase-hyphenated name that must equal the folder name, the ≤500-char `compatibility` field, and the ≤500-line SKILL.md guidance. `scripts/validate_skill.py` is written against this file. URL: https://raw.githubusercontent.com/agentskills/agentskills/main/docs/specification.mdx — retrieved 2026-10-13.
2. **R3 LIVE DIRECTIVES (AGENTS.md)** — the host constraint that defines the false-done
   pattern: "a task without a commit is a failed task" and "commit only your own paths". A
   STATUS.md that reports DONE without a commit pointer is exactly the false-done case this
   skill exists to catch. Verified 2026-10-13; offline copy at docs/R3_OWNERS.json.
3. **Google SRE book — Incident Handling** — https://sre.google/sre-book/. Verified 2026-10-13
   (HTTP 200). Source for the "no optimistic spin" principle: incident notes must record what
   was *actually* verified, not what was *intended*. The false-done detection heuristic ("a
   claim without evidence is a claim, not a fact") derives from the SRE book's treatment of
   postmortem evidence.
4. **GitHub Actions artifacts** — https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts. Verified 2026-10-13 (HTTP 200). Source for the
   "evidence pointer must open in under 60 seconds" rule: an artifact URL + run ID is a
   runnable pointer; a log file path on the host is not, unless it exists.
5. **GitHub Actions workflow syntax — `on`/`jobs.<job_id>.steps` and the `conclusion` vocabulary** — https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions. Verified 2026-10-13 (HTTP 200). Source for the status vocabulary this skill borrows: a workflow run has a `conclusion` of `success`, `failure`, `neutral`, `cancelled`, `skipped`, or `timed_out`, and a step has `outcome`. A STATUS.md that only says "passed" loses the distinction between `success` and `neutral` (skipped), which is exactly the false-done shape: a skipped test reads like a pass. URL: https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions — retrieved 2026-10-13.
7. **PostgreSQL docs — error message guidelines** — https://www.postgresql.org/docs/current/runtime-config-logging.html. Verified 2026-10-13 (HTTP 200 on the logging
   chapter; the RLS chapter URL 404s — see conflicts). Source for "never leak internals in a
   status report": log what is verifiable, redact what is not.
8. **R3 lane experience — STATUS.md anti-patterns** — internal observation recorded in
   docs/requests/skills-engineering-r3-04.md. Retrieval date 2026-10-13; no external URL.
   The five-bucket model (DONE / VERIFIED / IN_PROGRESS / BLOCKED / FALSE_DONE) was distilled
   from real handoff notes that conflated "coded" with "done".

## Version-sensitive facts
| Fact | Value | Verified |
|------|-------|----------|
| Agent Skills description limit | 1024 characters | 2026-10-13 |
| Progressive disclosure depth | one level (references/) | 2026-10-13 |
| actions/upload-artifact major | v4 (v3 deprecated) | 2026-10-13 |

## Conflicts
- The earlier SOURCES.md entry listed only two sources, both internal. This file adds six
  primary online sources. No conflict between them.
- PostgreSQL docs: `www.postgresql.org/docs/current/ddl-rls.html` returns 404 as of
  2026-10-13 (the RLS chapter was renamed/moved). The logging chapter URL works. Skills that
  pin a Postgres docs URL must re-verify the path on every retrieval; the pg-rls-multitenant
  SOURCES.md records this.
