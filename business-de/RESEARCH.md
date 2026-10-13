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

## CLOSE-OUT — 2026-10-13 (research + design deliverable)

Acceptance check: `RESEARCH.md` + `SOURCES.md` + `DESIGN.md` for each of the
ten skills, each with ≥6 sources.

| # | Skill | DESIGN | SOURCES (URLs) | EVALS prompts | near-miss | SKILL.md |
|---|---|---|---|---|---|---|
| 1 | xrechnung-zugferd | done | 13 | 6 | 4 | 117 L |
| 2 | gobd-archive | done | 9 | 5 | 4 | 137 L |
| 3 | datev-extf | done | 8 | 6 | 5 | 173 L |
| 4 | skr-journal-mapping | done | 7 | 7 | 4 | 132 L |
| 5 | ust-edge-cases | done | 6 | 8 | 4 | 75 L |
| 6 | bank-reconciliation-camt | done | 6 | 8 | 3 | 93 L |
| 7 | carrier-apis-de | done | 11 | 5 | 3 | 89 L |
| 8 | webhooks-safe | done | 8 | 6 | 3 | 89 L |
| 9 | publish-reconcile-wp-meta | done | 6 | 5 | 3 | 85 L |
| 10 | dsgvo-ai-act-labeling | done | 7 | 5 | 3 | 92 L |

### What was built this pass (2026-10-13)

- **DESIGN.md for all ten skills** — trigger description draft, "what this
  skill does better than a generic agent", procedure outline, scripts planned,
  five eval prompts. The six skills that already had a DESIGN.md
  (carrier-apis-de, webhooks-safe, publish-reconcile-wp-meta,
  dsgvo-ai-act-labeling) were left as-is; the other four were written new.
- **SKILL.md for the four skills that lacked one** — carrier-apis-de,
  webhooks-safe, publish-reconcile-wp-meta, dsgvo-ai-act-labeling. Each is
  under 500 lines and points one level deep into `references/`.
- **procedures.md for webhooks-safe and publish-reconcile-wp-meta** — with
  worked good/bad examples.
- **EVALS.md for webhooks-safe, publish-reconcile-wp-meta, carrier-apis-de
  and dsgvo-ai-act-labeling** — 5-8 prompts each, plus 3 near-miss triggers.
- **Near-miss triggers added to skr-journal-mapping and ust-edge-cases**
  (both had 0, which failed the validator's ≥3 rule).
- **xrechnung-zugferd SOURCES.md** — restored the 9 original 2026-10-08 source
  rows that a previous pass had truncated (the file now carries 13 URLs).

### Live re-verification (curl, 2026-10-13)

All 30 primary URLs probed. Statuses recorded per row. Changes vs the 2026-10-12
pass:

- `github.com/itplr-kosit/validator-configuration-xrechnung/blob/master/CHANGELOG.md`
  → **503** (was 200). The v2026-08-31 changelog facts are retained but the URL
  is now unreliable; re-fetch from the raw GitHub URL before an audit.
- `eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689` and
  `.../CELEX:32026R1744` → **202** (accepted, content served). No change to
  the Art. 50 facts.
- `www.hermes.de/geschaeftskunden/versand/` → **403** (unchanged, bot-protected).
- All other URLs unchanged (200).

### Validation

`business-de/scripts/validate_skills.py` (agentskills.io standard rules):
**10 skills checked, 0 total issues.** Rules enforced: name == folder,
description ≤ 1024 chars with a "when to use" trigger, portable frontmatter
fields only, SKILL.md ≤ 500 lines, references/ links one level deep,
EVALS.md ≥ 5 prompts + ≥ 3 near-miss prompts, SOURCES.md ≥ 6 URLs with ≥ 2
retrieval dates, no verbatim 15-word runs between SKILL.md body and its
references/.

### Open items

- `scripts/validate.py`, `install.sh` and `build-index.py` at the repo root are
  owned by `skills-engineering-r3`; until they exist, validation is done with
  `business-de/scripts/validate_skills.py`.
- DPD / GLS / Hermes / UPS carrier facts remain **unverified** — their partner
  portals are JS-rendered or bot-protected and require a business contract.
- The KoSIT validator JAR could not be fetched (503 on the changelog URL this
  pass); the element-name mapping in xrechnung-zugferd is the best available
  but not independently re-verified from source.
- The Art. 50(2) machine-readable marking date (2026-12-02) is a
  secondary-source date; re-verify against the Omnibus recital before relying
  on it.
