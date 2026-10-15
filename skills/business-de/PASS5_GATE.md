# PASS 5 gate report — skills-business-de-r3-05

Evals, validation, cross-links and handoff. Run 2026-10-15.

## Gates

| # | Command | Result |
|---|---|---|
| 1 | `python3 scripts/validate_skill.py <10 skill dirs>` | 10 ok, 0 issues |
| 2 | `python3 skills/business-de/scripts/run_evals.py` | 81 commands run, 0 failed |
| 3 | `python3 skills/business-de/scripts/audit_triggers_links.py` | 0 problems, acyclic, sinks: `gobd-archive` |
| 4 | `python3 -m pytest -q` (per skill) | 184 passed; the 32 failures are all `PermissionError` on `/tmp/*` files owned by the `zentralag` sandbox user (pre-existing, not this job's code) |
| 5 | every `references/EVALS.md` has >= 5 prompts + >= 3 near-misses | 10/10 |
| 6 | `skills/business-de/README.md` + `skills/business-de/HANDOFF.md` | both present |
| 7 | every SKILL.md < 500 lines | 10/10 (max 221) |

## What changed this pass

- Added the missing near-miss prompts: carrier-apis-de +3, datev-extf +3,
  dsgvo-ai-act-labeling +3, gobd-archive +3, publish-reconcile-wp-meta +3,
  skr-journal-mapping +3, webhooks-safe +3, xrechnung-zugferd +2. Each trap was
  grounded by running the script it describes against a real input.
- Re-verified every version pin in `config/versions.json` on 2026-10-15
  (record: `config/REVERIFY_2026-10-15.md`); fixed the dejure.org mirror
  (`https://dejure.org/gesetze/AO` is 200, the `.html` suffix 404s).
- Grounded every run-section command in shipped `evals_fixtures/`; added
  fixtures for datev-extf and gobd-archive.
- Corrected `README.md` script names to the shipped entry points.
