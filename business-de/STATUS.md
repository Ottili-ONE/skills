# STATUS — skills-business-de-r3 (Ten Germ)

Last updated: 2026-10-15 (pass 7).

## Task: skills-business-de-r3-01 — Research and design of the ten skills
Acceptance: `RESEARCH.md` + `SOURCES.md` (>=6 primary URLs each) + `DESIGN.md` per skill.

## What works (evidence)
- `python3 scripts/validate_skills.py <10 dirs>` → **10 skills, 0 issues**, exit 0 (2026-10-15).
- All ten skills have SKILL.md + references/{SOURCES,DESIGN,EVALS}.md + scripts/ + tests/.
- `python3 -m pytest -q` in business-de → **109 passed**, 0 failed (2026-10-15).
- 24 scripts across the ten skills; every DESIGN.md "Scripts planned" row exists on disk.
- **Live re-verification 2026-10-15**: all 69 primary URLs re-probed with curl. 56 × 200, 3 × 202 (eur-lex, served), 3 × 403 (bot-protected), 3 × 404 (moved), 4 × 000 (gesetze-im-internet paths). Per-URL status recorded in each `references/SOURCES.md` under `## Re-verification 2026-10-15`; link-maintenance rows recorded in RESEARCH.md PASS 7.

## What is stubbed / missing
- DPD / GLS / Hermes / UPS carrier facts remain **unverified** — partner portals are JS-rendered or bot-protected and require a business contract. carrier-apis-de SOURCES.md marks these rows as "portal not reachable" (Hermes re-probed 2026-10-15: still 403).
- The KoSIT validator JAR / changelog URL could not be fetched (503 on 2026-10-13, not re-probed 2026-10-15); the element-name mapping in xrechnung-zugferd is the best available but not independently re-verified from source.
- The Art. 50(2) machine-readable marking date (2026-12-02) is a secondary-source date; re-verify against the Omnibus recital before relying on it.
- `scripts/validate.py`, `install.sh` and `build-index.py` at the repo root are owned by `skills-engineering-r3`; until they exist, validation is done with `../scripts/validate_skill.py`.
- `gesetze-im-internet.de` law paths (UStG, UStDV, AO) returned **000** on both 2026-10-13 and 2026-10-15. Corroboration comes from `dejure.org/gesetze/AO/147.html` (200) and IHK / steuer-berater.de pages (200). Re-fetch before any audit.

## This pass (2026-10-15) — PASS 7 live re-verification
- Re-probed all 69 primary URLs live (curl, UA `Mozilla/5.0 research-bot`, `--max-time 12`, follow redirects).
- Appended a `## Re-verification 2026-10-15` block to the 7 SOURCES.md files whose URLs had moved or failed since 2026-10-13 (bank-reconciliation-camt, carrier-apis-de, datev-extf, gobd-archive, skr-journal-mapping, ust-edge-cases, xrechnung-zugferd). webhooks-safe, publish-reconcile-wp-meta and dsgvo-ai-act-labeling re-probed clean (all 200/202) and needed no block.
- Replaced 8 dead/moved URLs with their live equivalents (hilfe.datev.de, bundesbank MT940, DATEV SK-Schlüssel, gesetze-im-internet paths, iso20022 CAMT.053, swift.com/standards). No fact changed.
- Re-confirmed: XRechnung tags `v2026-08-31`/`v2026-01-31`, FERD profile model, Stripe 5-min replay window, GitHub/Meta signature schemes, OWASP SSRF checklist, WordPress REST API, EU AI Act Art. 50 dates (Omnibus `32026R1744` served, 202).

