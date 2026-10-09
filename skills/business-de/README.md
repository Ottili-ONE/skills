# Ottili ONE — Business & Integration Skills (DE)

Ten Agent Skills for coding and operations agents working on the Ottili
platform. Each skill follows the open Agent Skills standard
(agentsskills.io): a folder with `SKILL.md` (portable YAML front matter),
optional `references/` (procedures, SOURCES, EVALS) and `scripts/`
(deterministic, offline, documented).

All facts are sourced from primary references (official docs, standards
bodies, source repositories) and recorded in each skill's
`references/SOURCES.md` with URL and retrieval date. Version-sensitive
facts are pinned in `config/versions.json` and read by the scripts —
nothing is hardcoded in logic.

## Install

```bash
# from the repository root
./scripts/install.sh skills/business-de
```

Or copy a single skill folder into your skills directory:

```bash
cp -r skills/business-de/xrechnung-zugferd ~/.skills/
```

## The ten skills

| Skill | One-line value |
| --- | --- |
| `xrechnung-zugferd` | Generate, validate and archive German e-invoices (XRechnung / ZUGFeRD / Factur-X) under EN 16931 and UStG §14. |
| `datev-extf` | Produce and validate DATEV EXTF Buchungsstapel (Formatversion 700/13) and Datenservices exports. |
| `gobd-archive` | GoBD-compliant retention, immutability, Verfahrensdokumentation and audit export (AO §147, effective 2025-01-01). |
| `skr-journal-mapping` | Map SKR03/SKR04 accounts to automatic journal entries with correct Steuerschluessel, period locks and retention. |
| `ust-edge-cases` | Decide USt edge cases: reverse charge (§3g), Kleinunternehmer, 06/0, intra-EU, tax-key validity. |
| `bank-reconciliation-camt` | Reconcile bank statements (camt.053) against Ottili items with match priority, reason codes and strict mode. |
| `carrier-apis-de` | Idempotent label creation, official tracking and cost reconciliation for DHL, DPD, GLS, Hermes, UPS. |
| `webhooks-safe` | HMAC verification, dedupe with TTL, per-stream order, replay windows, dead-letter queue and SSRF-safe outbound. |
| `publish-reconcile-wp-meta` | Idempotent publish to WordPress and Meta plus reconciliation of unknown results. |
| `dsgvo-ai-act-labeling` | GDPR processing register (Art. 30/6) and EU AI Act Art. 50 disclosure decisions with human-review evidence. |

## Related skills

- `skills/engineering/**` — engineering playbooks (test, security, docs).
- `skills/core/**` and `skills/curated/**` — general-purpose skills.

## Validation

```bash
python3 skills/business-de/scripts/validate_skills.py   # Agent-Skills rules
python3 skills/business-de/.../tests/...                # per-skill pytest
python3 scripts/validate.py                              # repository catalog
```
