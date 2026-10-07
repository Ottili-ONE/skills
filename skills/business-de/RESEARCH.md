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
