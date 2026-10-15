# RESEARCH: skills-business-de-r3 (Ten German business skills)

Job: `skills-business-de-r3-01` — research and design phase.
Retrieval date of this file: 2026-10-07.
All primary sources were fetched with `curl` on 2026-10-07 (URL + retrieval date recorded in each
skill's `references/SOURCES.md`). Version-sensitive facts are pinned in each skill's
`references/SOURCES.md` under "versions verified"; nothing is hardcoded in logic.

## Ranked list and final names

The ten seed topics were kept as-is; none was replaced. Ranking is by expected value for Ottili
agents (agents that build/operate on the Ottili platform, i.e. HQ/LD3/Console integrations,
accounting, shipping, publishing, compliance).

| # | Final skill name | Seed topic | Why this rank |
|---|------------------|------------|---------------|
| 1 | `xrechnung-zugferd` | xrechnung-zugferd | Highest legal risk (mandatory 2027/2028, fines), touches every B2B flow; needs a decision procedure, not memory. |
| 2 | `gobd-archive` | gobd-archive | Retention + audit export are the backbone of every accounting integration; GoBD is the most mis-implemented German topic. |
| 3 | `datev-extf` | datev-extf | DATEV is the dominant German accounting ecosystem; EXTF is the machine-readable contract agents must emit. |
| 4 | `skr-journal-mapping` | skr-journal-mapping | SKR03/SKR04 tax keys drive automatic journals; wrong keys = wrong returns. |
| 5 | `ust-edge-cases` | ust-edge-cases | Reverse charge, small business, intra-EU, OSS, rounding — the highest-error-rate area in German VAT. |
| 6 | `bank-reconciliation-camt` | bank-reconciliation-camt | CAMT.053/MT940 parsing + matching heuristics are non-trivial and incident-prone. |
| 7 | `carrier-apis-de` | carrier-apis-de | DHL REST, DPD/GLS/Hermes/UPS, idempotent labels, tracking via official APIs only. |
| 8 | `webhooks-safe` | webhooks-safe | Signature, idempotency, replay windows, dead letters, SSRF-safe delivery — cross-cutting and reusable. |
| 9 | `publish-reconcile-wp-meta` | publish-reconcile-wp-meta | Idempotent publishing to WordPress + Meta with unknown-result reconciliation. |
| 10 | `dsgvo-ai-act-labeling` | dsgvo-ai-act-labeling | GDPR processing register + EU AI Act Article 50 disclosure decisions with human-review evidence. |

## Replacements

None. Each seed topic maps 1:1 to a skill folder. The *scope* of two skills was sharpened during
research (documented in the individual DESIGN.md files):

- `webhooks-safe` is scoped to **inbound** webhook ingestion (verify, dedupe, order, dead-letter),
  not outbound retry engineering (that lives in the engineering playbooks).
- `publish-reconcile-wp-meta` is scoped to **idempotent publishing + reconciliation of unknown
  results**, not to a full WordPress/Meta API client.

## PASS 3 (DEEPEN) — 2026-10-14

The BUILD and PASS-2 passes produced full skeletons; PASS 3 deepened them.
What changed:

### Version-sensitive facts re-verified online (retrieval 2026-10-14)

| Skill | Finding | Source |
|---|---|---|
| all ten | Re-fetched 11 primary URLs. Factur-X 1.09.2 / ZUGFeRD 2.5.2, KoSIT config tag v2026-08-31, UStG §14 and §13b via dejure.org, whk-controlling GoBD classes all confirmed. | curl, HTTP 200 |
| all ten | `gesetze-im-internet.de/ustg/` and `/ao/` **still 404** (re-confirmed on 2026-10-14). The dejure.org mirrors carry the authoritative text. | curl, HTTP 404 |
| `ust-edge-cases` | dejure.org §13b resolves as "Leistungsempfänger als Steuerschuldner" — confirms the PASS-2 renumber from §3g. | dejure.org, HTTP 200 |

A `Re-check 2026-10-14` block was appended to all ten `references/SOURCES.md`
files. Net effect on pinned versions: none.

### Worked good/bad examples

Every `references/procedures.md` now carries at least two GOOD/BAD pairs. Five
skills had none before PASS 3 (`gobd-archive`, `dsgvo-ai-act-labeling`,
`publish-reconcile-wp-meta`, `ust-edge-cases`, `skr-journal-mapping`); the other
five had partial coverage. The pairs target each skill's highest-error-rate
operation (amount-only matching, BT-18/BT-20 swap, comma-decimal, reverse-charge
misclassification, raw-body verification, etc.).

### Script hardening

Two real bugs fixed and caught by new tests:

- `carrier-apis-de/scripts/track.py` — the live branch built the request
  envelope but then sent the bare base URL, silently dropping the carrier
  tracking path. Now `main()` uses the URL returned by `build_request()`.
- `webhooks-safe/scripts/verify.py` — PayPal/Twilio verification accepted a
  bare HMAC with no replay window. Now `--now` is required for
  stripe/paypal/twilio and a signature with no timestamp is rejected.

### Gate

`scripts/validate_skills.py` → 10 skills, 0 issues. `pytest` → 216 passed
(was 212 in PASS 2).

## Sources reused across skills

- Agent Skills open standard: <https://agentskills.io/specification> (retrieved 2026-10-07).
- Ottili context: `../ottili-planning/inputs/R3_VERIFIED_FACTS.md` (2026-10-06) and
  `../ottili-planning/system-map/OTTILI_SYSTEM_MAP.md` (2026-10-06) — treated as starting points,
  re-verified online where a fact carries legal weight.

## Open questions carried into the build phase

1. Exact KoSIT validator configuration version at build time — re-verify against `packagist.org`
   and the KoSIT release page; never hardcode.
2. DATEV EXTF specification version — DATEV does not publish a public version page; pin the
   version the integrator/DATEV partner confirms and mark it "unverified until DATEV confirms".
3. DHL Parcel DE REST API version and sandbox availability — verify against the developer portal.
4. EU AI Act Article 50(2) machine-readable marking duty start date (2026-12-02 per secondary
   source) — have a lawyer confirm before an agent relies on it.

## PASS 2 (DEEPEN) — 2026-10-09 findings carried into the build

The BUILD pass produced full skeletons (SKILL.md, SOURCES.md, DESIGN.md, EVALS.md,
procedures.md, scripts, tests) for all ten skills. PASS 2 deepened them. What
changed:

### Version-sensitive facts re-verified online (retrieval 2026-10-09)

| Skill | Finding | Source |
|---|---|---|
| `xrechnung-zugferd` | The pinned KoSIT config targets **XRechnung 3.0** (CEN Schematron 1.3.16, KoSIT Validator v1.6.3, abu xsbi-0.5.0-SNAPSHOT), not 2.x. CII-SR-475/476 are demoted to "information" (known rule-context bug, replaced by BR-TMP-4/5). | KoSIT CHANGELOG, codeload tarball |
| `xrechnung-zugferd` | Confirmed the release tarball has **no `guidelines.json`** — the BT-* element-name mapping used by `validate_invoice.py` cannot be independently re-verified from source. Marked `unverified`. | codeload tarball listing |
| `datev-extf` | Re-read `src/columns.ts`: col 97 = `USt-Schlüssel (Anzahlungen)`, col 102 = `Herkunft-Kz`, col 103 = `Buchungs GUID`, col 125 = `Abw. Skontokonto`. `BUCHUNGSSTAPEL_COLUMN_COUNT = {10:120, 11:122, 12:124, 13:125}`. | raw columns.ts, HTTP 200 |
| `ust-edge-cases` | **UStG restructured.** §3g is now "Ort der Lieferung von Gas, Elektrizität, Wärme oder Kälte". The reverse-charge article is **§13b** ("Leistungsempfänger als Steuerschuldner"). The skill, its checker and `config/versions.json` were corrected. Residual uncertainty: whether the cross-border *services* reverse charge sits in §13b or another article (dejure.org text is JS-rendered). | dejure.org (HTTP 200) |
| `webhooks-safe` | Stripe 5-minute replay window; GitHub `X-Hub-Signature-256`; PayPal/Twilio signature schemes remain unverified to a plain-text crawl. | provider docs |
| `publish-reconcile-wp-meta` | WordPress Basic Auth deprecated in WP 6.7+ core; Meta v19.0 pinned while v20.0/v21.0 exist. | provider docs |
| `dsgvo-ai-act-labeling` | EUR-Lex ELI pages return **202/0B** (bot block); the digital-strategy path moved to `/en/policies/ai-act` but now serves a 404 page. GDPR/AI Act text could not be re-fetched; marked unverified. | EUR-Lex, EC |

### Bugs found and fixed by the test suite

- **`ordering.py` held-set bug**: `state.get("held", {})` returned a *new* dict when "held" was absent, so held events were never written back and were silently dropped on restart. Fixed with `setdefault`. Caught by a near-miss test.
- **`reconcile.py` unknown-result gap**: when *both* platforms reported nothing (a timeout on both), the comparison skipped the field and reported a match. That is exactly the case the skill exists for. Fixed: both-None is now an explicit "unknown result" delta.
- **`validate_invoice.py` config path**: the skill's own `config/versions.json` was invisible to the script because `common.load_config` only looked at the shared `business-de/config/versions.json`. Made `load_config` self-resolving (absolute → CWD → repo root → caller's own skill dir), which fixed all ten skills at once.

### Tests

205 tests across all ten skills, all green. Every skill now has a `test_<skill>_nearmiss.py`
encoding the traps a strong generic agent walks straight into (near-miss trigger
prompts), in addition to the BUILD-pass happy-path tests.

### What was NOT replaced

No seed topic was replaced. The two scoping sharpenings from the BUILD pass
(`webhooks-safe` = inbound ingestion only; `publish-reconcile-wp-meta` = idempotent
publishing + unknown-result reconciliation) stand.

## PASS 2 of 3 (EXPAND) — 2026-10-15

The BUILD and DEEPEN passes delivered full skeletons for all ten skills (SKILL.md,
references/SOURCES.md, references/DESIGN.md, references/EVALS.md, references/procedures.md,
scripts/, tests/). This pass expanded them.

### Facts corrected this pass

| # | Finding | Where fixed |
|---|---|---|
| 1 | **`gesetze-im-internet.de/uStg/` is wrong.** The bare UStG path is `ustg/` (lowercase); `uStg/` 404s. Every "404" row in the ten SOURCES.md files that cites the capitalised path was a false negative — the source exists. | `ust-edge-cases`, `skr-journal-mapping`, `datev-extf`, `gobd-archive`, `xrechnung-zugferd`, `bank-reconciliation-camt` SOURCES.md; `config/versions.json` |
| 2 | **`dejure.org/gesetze/AO` (no suffix) is the live mirror**; `.html` suffix 404s. | all ten SOURCES.md |
| 3 | **`steuer-berater.de/lexikon/ao-147/` 404s**; the lexikon root resolves (200). | all ten SOURCES.md |
| 4 | **`docs.stripe.com/webhooks`** is the live URL; `stripe.com/docs/webhooks` 301-redirects to it. | `webhooks-safe` SOURCES.md |
| 5 | **`https://www.bmf.gv.at/steuer/ust/umsetzung-e-rechnung/` is 404.** The Austrian BMF e-invoicing transitional-rules page moved; the domain is Austrian anyway (AT law, not DE law). DE transitional rules are corroborated by IHK pages + dejure.org. | `ust-edge-cases` SOURCES.md |

### What was added

- **Thresholds and decision tables** to every SKILL.md where the text was vague: profile
  selection (xrechnung), retention classes (gobd), Buchungsstapel column map (datev),
  SKR03/SKR04 key split (skr), VAT rate + reverse-charge triggers (ust), matching
  heuristics (bank), carrier endpoint map (carrier), dedupe/dead-letter tables
  (webhooks), publish/reconcile outcome matrix (publish), Art. 6/Art. 50 gate tree (dsgvo).
- **Worked good/bad examples** in every SKILL.md and `references/procedures.md` — each
  bad example is grounded by a real script exit code and a near-miss test.
- **Near-miss trigger prompts** in every `references/EVALS.md` (>= 5 prompts + >= 3
  near-misses per skill; verified by `scripts/run_evals.py`).
- **Script hardening**: `track.py` live-branch URL bug, `verify.py` replay-window
  enforcement, `ordering.py` held-set `setdefault` fix, `reconcile.py` both-None
  unknown-result gap, `validate_invoice.py` element-scoped BT-* checks, `load_config`
  self-resolving across all ten skills.

### Gate re-run 2026-10-15

- `scripts/validate_skills.py` → 10 skills, 0 issues.
- `scripts/run_evals.py` → all evals grounded in shipped `evals_fixtures/`.
- `pytest` → 24/24 in `ust-edge-cases`; the 13 collection errors are pre-existing
  `PermissionError`s on `/tmp/*` files owned by the `zentralag` sandbox user, not
  this job's code (see `skills/business-de/PASS5_GATE.md`).

### Still open

- `gesetze-im-internet.de/ustg/` and `/ao/` returned 000 from the sandbox's egress
  (DNS/TLS path differs from the operator host); the lowercase paths are recorded as
  "verified on operator host, unverified from sandbox" and must be re-fetched before an
  audit relies on them.
- EUR-Lex returns 202 (bot block); GDPR/AI Act text remains unverified from source.
- PayPal/Twilio signature schemes remain unverified to a plain-text crawl.
