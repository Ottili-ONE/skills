# RESEARCH — skills-business-de-r3 (Ten German business & integration skills)

Retrieval date: 2026-10-12. This file records the ranked list, final names,
any replacement made, and the state of online research per skill.

## Ranked list (final names, in build order)

| # | Final name | Seed topic | Status | Sources | Design |
|---|---|---|---|---|---|
| 1 | xrechnung-zugferd | xrechnung-zugferd | done (2026-10-08) | 13 | done |
| 2 | gobd-archive | gobd-archive | done (2026-10-08) | 7 | done |
| 3 | datev-extf | datev-extf | done (2026-10-08) | 8 | done |
| 4 | skr-journal-mapping | skr-journal-mapping | done (2026-10-08) | 8 | done |
| 5 | ust-edge-cases | ust-edge-cases | done (2026-10-08) | 8 | done |
| 6 | bank-reconciliation-camt | bank-reconciliation-camt | done (2026-10-09) | 7 | done |
| 7 | carrier-apis-de | carrier-apis-de | **research 2026-10-12** | 8 | **this pass** |
| 8 | webhooks-safe | webhooks-safe | **research 2026-10-12** | 8 | **this pass** |
| 9 | publish-reconcile-wp-meta | publish-reconcile-wp-meta | **research 2026-10-12** | 8 | **this pass** |
| 10 | dsgvo-ai-act-labeling | dsgvo-ai-act-labeling | **research 2026-10-12** | 8 | **this pass** |

## Replacements made

None. All ten seed topics were kept verbatim because each maps to a concrete,
evidence-dense Ottili integration surface (e-invoicing compliance, GoBD
audit readiness, DATEV export, SKR03/04 tax journals, VAT edge cases, bank
reconciliation, carrier shipping, inbound webhooks, outbound publishing, and
GDPR/AI-Act labelling). No seed was judged redundant with another: the closest
pair (ust-edge-cases vs xrechnung-zugferd) is split by role — one is a *VAT
calculation decision procedure*, the other is an *invoice format validation*
procedure — and both are needed because a wrong VAT key and a rejected invoice
are different failures.

## What this job does better than generic agents

- **Primary-source grounding**: every fact carries a URL + retrieval date and a
  re-verification note; version-sensitive facts are pinned in
  `config/versions.json`, never hardcoded in logic.
- **Decision procedures with pass/fail criteria**: each skill ships a cascade
  (e.g. "amount+reference, then amount+counterparty, then amount±tolerance,
  then reference-only") instead of a soft recommendation.
- **Near-miss evals**: the EVALS.md files name the specific wrong answer a
  generic agent would give (e.g. "allocate two identical 100.00 entries to a
  200.00 open item and silently absorb the duplicate").
- **Copy-paste-safe commands**: scripts are deterministic, offline, and tested.

## Open items / blockers

- `scripts/validate.py` and the install/index scripts are owned by
  `skills-engineering-r3`; until they exist, validation is done by hand
  against the agentskills.io standard rules (see each SKILL.md verification
  section).
- Several `gesetze-im-internet.de` law pages 404'd on 2026-10-09/10 (UStG,
  UStDV, AO). Corroboration comes from IHK and steuer-berater.de pages that
  returned 200. Re-fetch before any audit.
- KoSIT validator JAR could not be fetched on 2026-10-09; the element-name
  mapping in xrechnung-zugferd is the best available but not independently
  re-verified from source.
