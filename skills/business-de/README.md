# business-de — German business & integration skills

Ten Agent Skills for coding and operations agents working on the Ottili
platform. Each skill follows the open Agent Skills standard (agentskills.io):
a folder `<name>/` with `SKILL.md` (YAML front matter), optional
`scripts/`, `references/` and `assets/`. Long material lives in
`references/` and is linked one level deep from `SKILL.md` (progressive
disclosure). Every skill is researched from primary sources (official
documentation, standards bodies, source repositories, postmortems); see each
`references/SOURCES.md` for the URLs and retrieval dates.

## The ten skills

| Skill | One-line value | Install |
|---|---|---|
| `bank-reconciliation-camt` | Parse CAMT.053/MT940 statements, match postings to open items with multi-key heuristics, detect duplicates and unallocated differences, and validate IBANs with the Bundesbank Pruefzahlenberechnung. | `./install.sh bank-reconciliation-camt` |
| `carrier-apis-de` | German carrier APIs (DHL, DPD, GLS, Hermes, UPS): idempotent labels, official tracking only, cost reconciliation. | `./install.sh carrier-apis-de` |
| `datev-extf` | Produce and validate DATEV EXTF 700/13 booking stacks, Datenservices and test fixtures. | `./install.sh datev-extf` |
| `dsgvo-ai-act-labeling` | GDPR processing-register entries and EU AI Act Article 50 disclosure decisions with human-review evidence. | `./install.sh dsgvo-ai-act-labeling` |
| `gobd-archive` | GoBD-compliant retention classes, immutability, Verfahrensdokumentation and audit-ready export. | `./install.sh gobd-archive` |
| `publish-reconcile-wp-meta` | Publish and reconcile WordPress/Meta posts with idempotency keys and field-by-field diff. | `./install.sh publish-reconcile-wp-meta` |
| `skr-journal-mapping` | Map SKR03/SKR04 accounts to journal lines, tax keys and period-lock rules. | `./install.sh skr-journal-mapping` |
| `ust-edge-cases` | German VAT edge cases: reverse charge, Kleinunternehmer, intra-EU B2B, OSS/IOSS, cent rounding. | `./install.sh ust-edge-cases` |
| `webhooks-safe` | Ingest inbound webhooks safely: HMAC verification, dedupe with TTL, per-stream order, replay windows, dead-letter, SSRF allow-list. | `./install.sh webhooks-safe` |
| `xrechnung-zugferd` | Generate, validate and archive German e-invoices (XRechnung / ZUGFeRD / Factur-X) compliant with EN 16931 and UStG §14. | `./install.sh xrechnung-zugferd` |

## Layout

```
skills/business-de/
├── README.md                 <- this file
├── HANDOFF.md                <- what to re-verify and what to build next
├── config/
│   ├── versions.json         <- every pinned version (read it, never hardcode)
│   └── REVERIFY_2026-10-14.md <- live re-verification record
├── scripts/
│   ├── validate_skills.py    <- the standard's rules
│   ├── run_evals.py          <- execute every EVALS.md command
│   ├── audit_triggers_links.py <- trigger + cross-link graph audit
│   └── common.py             <- shared config loader
└── <skill-name>/
    ├── SKILL.md              <- front matter + procedure + decision tables
    ├── scripts/              <- small, deterministic, offline
    ├── references/           <- DESIGN.md, procedures.md, SOURCES.md, EVALS.md
    ├── evals_fixtures/       <- the inputs the EVALS run-sections use
    └── tests/                <- pytest suite
```

## Version-pin rule

Every version (EN 16931, Factur-X, KoSIT validator, EXTF 700/13, SKR04, UStG
rates, camt.053 namespace, retention classes) is pinned in
`config/versions.json` and **never hardcoded** in scripts or `SKILL.md`.
Re-verify on every spec bump and record the run in
`config/REVERIFY_2026-10-14.md` and the skill's `references/SOURCES.md`.

## Cross-link contract

Every skill's `## Related skills` section names its siblings by folder name.
The graph is acyclic by construction: `gobd-archive` is the pure retention
sink and links to nobody; every other skill links to it for its retention
class. Audit it yourself:

```bash
python3 skills/business-de/scripts/audit_triggers_links.py
```

## Install hints

```bash
# from the repository root
./install.sh --list                 # show every skill
./install.sh <skill-name>           # install one skill into your agent
./install.sh --validate             # run the Agent-Skills validator
```

## Re-running the quality gate

```bash
python3 skills/business-de/scripts/validate_skills.py   # must be 0 issues
python3 skills/business-de/scripts/run_evals.py         # every EVALS.md command must exit 0
python3 skills/business-de/scripts/audit_triggers_links.py  # acyclic, no trigger gaps
cd skills/business-de && python3 -m pytest -q           # full pytest suite
```

Gate status at PASS 4 (2026-10-14): validator 10/10 skills, 0 issues;
`run_evals.py` 74 commands, 0 failed; trigger/link audit 0 problems.
