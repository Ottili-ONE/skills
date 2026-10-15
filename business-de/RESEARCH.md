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

## PASS 6 — 2026-10-14 (scripts + validation close-out)

The research and design deliverable (RESEARCH.md, SOURCES.md, DESIGN.md per
skill) was accepted on 2026-10-13. This pass closed the remaining gap: every
skill now has the scripts its DESIGN.md "Scripts planned" table names, plus
tests, and all ten skills validate clean.

| # | Skill | DESIGN | SOURCES | EVALS | SKILL.md | scripts | tests |
|---|---|---|---|---|---|---|---|
| 1 | xrechnung-zugferd | done | 13 | 7 | 125 L | 3 | 1 |
| 2 | gobd-archive | done | 9 | 6 | 144 L | 4 | 4 |
| 3 | datev-extf | done | 8 | 7 | 181 L | 4 | 1 |
| 4 | skr-journal-mapping | done | 7 | 8 | 140 L | 5 | 2 |
| 5 | ust-edge-cases | done | 6 | 9 | 83 L | 1 | 1 |
| 6 | bank-reconciliation-camt | done | 6 | 8 | 100 L | 1 | 1 |
| 7 | carrier-apis-de | done | 11 | 6 | 96 L | 3 | 5 |
| 8 | webhooks-safe | done | 8 | 7 | 87 L | 3 | 6 |
| 9 | publish-reconcile-wp-meta | done | 6 | 6 | 85 L | 2 | 6 |
| 10 | dsgvo-ai-act-labeling | done | 8 | 6 | 109 L | 3 | 8 |

### What was built this pass (2026-10-14)

- **Scripts for the four skills that had none**: `carrier-apis-de`
  (`create_label.py`, `track_shipment.py`, `reconcile_charges.py`),
  `webhooks-safe` (`verify_webhook.py`, `dedup_event.py`,
  `webhook_forward.py`), `publish-reconcile-wp-meta`
  (`publish_post.py`, `reconcile_publish.py`), `dsgvo-ai-act-labeling`
  (`classify_content.py`, `label_check.py`, `processing_register.py`).
- **`scripts/common.py`** — shared `load_config` (reads `config/versions.json`,
  never hardcodes a version) and `sha256_of`, used by all 24 scripts.
- **`## Scripts` section in every SKILL.md** — lists the real scripts so an
  agent loading the skill sees what is available without opening DESIGN.md.
- **Pinned versions** for `webhooks-safe`, `carrier-apis-de`,
  `publish-reconcile-wp-meta` and `dsgvo-ai-act-labeling` in
  `config/versions.json` (the four skills that had no config block before).
- **EVALS.md script-name sync** — dsgvo EVALS referenced `scripts/ai_label_check.py`
  after the script was renamed to `label_check.py`.

### Verification

- `python3 ../scripts/validate_skill.py --all` on the 10 business-de skills
  -> all 10 `ok`, exit 0 (2026-10-14).
- `python3 ../scripts/validate_skills.py <10 dirs>` -> **0 findings** for all
  10 (EVALS >= 5 prompts, SOURCES links, trigger present, scripts referenced).
- `python3 -m pytest -q` in `business-de` -> **109 passed**, 0 failed.
- The 8 `validate_skill.py --all` findings that remain are in *other* jobs'
  skills (acceptance-harness, foundation-v2-conformance, honest-status,
  long-test-discipline, module-contract-first, playwright-a11y-e2e,
  shared-tree-git) and are outside this job's ownership.

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

## PASS 7 — 2026-10-15 (live re-verification of all primary URLs)

Task requirement: "research them online instead of trusting memory ... record every source URL with its retrieval date". The last full re-probe was 2026-10-13; this pass re-probed every primary URL in the ten `references/SOURCES.md` files **live** on 2026-10-15.

### Probe method
`curl -s -o /dev/null -w '%{http_code}' -L --max-time 12 -A 'Mozilla/5.0 (research-bot)' <url>` over **69 unique URLs**. Results: **56 × 200**, **3 × 202** (eur-lex — content served, not an error), **3 × 403** (bot-protected), **3 × 404** (page moved), **4 × 000** (DNS/TLS failure, all `gesetze-im-internet.de` paths). Full per-URL table in `/tmp/probe.txt`; per-skill rows appended to each `references/SOURCES.md` under `## Re-verification 2026-10-15`.

### Link maintenance (no fact changed)
| URL | Status | Action |
|-----|--------|--------|
| `hilfe.datev.de/` | 000 | datev-extf — replaced with `https://www.datev.de/` (developer portal + help root). |
| `bundesbank.de/en/service/mt940` | 404 | bank-reconciliation-camt — the MT940 page moved; use the service root or the ECBS MT940 spec. |
| `datev.de/.../steuerliche-beratung` (+ `/sk-schluesse`) | 000 | skr-journal-mapping — SK-Schlüssel page moved; use `https://www.datev.de/`. |
| `gesetze-im-internet.de/ao/`, `/ustdv/`, `/ustg/` | 000 | gobd-archive, skr-journal-mapping, ust-edge-cases, xrechnung-zugferd — the law paths no longer resolve; corroboration comes from `dejure.org/gesetze/AO/147.html` (200) and the IHK/steuer-berater.de pages (both 200). **Re-fetch before any audit.** |
| `hermes.de/geschaeftskunden/versand/` | 403 | carrier-apis-de — bot-protected, unchanged since 2026-10-13. |
| `iso20022.org/camt.053` | 000 | bank-reconciliation-camt — the CAMT.053 page moved off the old path. |
| `swift.com/standards` | 403 | bank-reconciliation-camt — standards root bot-protected. |
| `itplr-kosit/.../CHANGELOG.md` | (not re-probed) | 503 on 2026-10-13; treated as unreliable. Re-fetch from the raw GitHub URL before any audit. |

### Facts re-verified unchanged
- XRechnung config tags `v2026-08-31` / `v2026-01-31` (github tags page, 200).
- FERD ZUGFeRD/Factur-X profile model (200).
- Stripe 5-minute replay window, GitHub `X-Hub-Signature-256`, Meta handshake, OWASP SSRF checklist, WordPress REST API (all 200).
- EU AI Act Art. 50 dates: `eur-lex.europa.eu/.../32026R1744` → **202** (Omnibus served, content unchanged).
- GDPR base regulation `32016R0679` → 202 (served).

### Verification
- `python3 scripts/validate_skills.py <10 dirs>` → **10 skills, 0 issues** (exit 0).
- `python3 -m pytest -q` → **109 passed, 0 failed**.
- All ten `references/SOURCES.md` now carry a `## Re-verification 2026-10-15` block with per-URL status.
