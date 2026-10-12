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
| `bank-reconciliation-camt` | Parse CAMT.053/MT940 statements, match postings to open items, flag duplicates and unallocated differences. | `./install.sh bank-reconciliation-camt` |
| `carrier-apis-de` | German carrier APIs (DHL, DPD, GLS, Hermes, UPS): idempotent labels, official tracking, cost reconciliation. | `./install.sh carrier-apis-de` |
| `datev-extf` | Produce and validate DATEV EXTF 700/13 booking stacks, Datenservices and test fixtures. | `./install.sh datev-extf` |
| `dsgvo-ai-act-labeling` | GDPR processing-register entries and EU AI Act Article 50 disclosure decisions with human-review evidence. | `./install.sh dsgvo-ai-act-labeling` |
| `gobd-archive` | GoBD-compliant retention classes, immutability, Verfahrensdokumentation and audit-ready export. | `./install.sh gobd-archive` |
| `publish-reconcile-wp-meta` | Publish and reconcile WordPress/Meta posts with idempotency keys and field-by-field diff. | `./install.sh publish-reconcile-wp-meta` |
| `skr-journal-mapping` | Map SKR03/SKR04 accounts to journal lines, tax keys and period-lock rules. | `./install.sh skr-journal-mapping` |
| `ust-edge-cases` | German VAT edge cases: reverse charge, Kleinunternehmer, intra-EU B2B, OSS/IOSS, cent rounding. | `./install.sh ust-edge-cases` |
| `webhooks-safe` | Ingest webhooks safely: HMAC verification, dedupe, order preservation, dead-letter, SSRF allow-list. | `./install.sh webhooks-safe` |
| `xrechnung-zugferd` | Generate, validate and archive German e-invoices (XRechnung / ZUGFeRD / Factur-X) per EN 16931 and UStG §14. | `./install.sh xrechnung-zugferd` |

## Install hints

```bash
# from the repository root
./install.sh --list                 # show every skill
./install.sh <skill-name>           # install one skill into your agent
./install.sh --validate             # run the Agent-Skills validator
python3 skills/business-de/scripts/validate_skills.py   # the ten skills
cd skills/business-de && python3 -m pytest -q         # 131 tests
```

## Layout of one skill

```
<name>/
├── SKILL.md                 # front matter + instructions (<=500 lines)
├── scripts/                 # small, deterministic, offline, documented
├── references/
│   ├── SOURCES.md           # >=6 primary URLs + retrieval dates
│   ├── EVALS.md             # >=5 prompts + 3 near-miss prompts
│   ├── procedures.md        # long checklists pulled out of SKILL.md
│   └── DESIGN.md            # design rationale and known conflicts
└── tests/                   # pytest suite for the scripts
```

## Version pins

Pinned versions live in `config/versions.json` and are read from there at
runtime — never hardcode a version inside a script or SKILL.md. Re-verify the
pins on every spec bump and record the re-verification date in the skill's
`references/SOURCES.md`.
