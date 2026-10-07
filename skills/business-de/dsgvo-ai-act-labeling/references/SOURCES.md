# SOURCES: dsgvo-ai-act-labeling
Retrieval date: 2026-10-07. All URLs fetched with `curl` on 2026-10-07 unless noted otherwise. Version-sensitive facts pinned in config; never hardcoded in logic (R3 rule). Re-verify against EUR-Lex before each build (GDPR is stable but member-state implementations may change; EU AI Act implementing acts are still being adopted). Conflicts between sources noted at end of each section; secondary claims treated as unverified until primary source confirmed.

## Versions verified (pinned, nothing hardcoded)
- GDPR Regulation (EU) 2016/679 — current as of 2026-10-07; re-check EUR-Lex before each build.
- EU AI Act Regulation (EU) 2024/1689 — current as of 2026-10-07; Article 5(4) human oversight requirement; Article 5(2) transparency obligation for high-risk AI systems.

## Primary sources
1. EUR-Lex GDPR text — https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R679 — retrieved 2026-10-07. The authoritative legal text for GDPR processing rules, consent, data subject rights and the processing register requirement (Art. 30). Pin the EUR-Lex CELEX number; the official text is binding, mirrors are not authoritative.
2. EUR-Lex EU AI Act text — https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689 — retrieved 2026-10-07. Defines the risk categories, transparency obligations and Article 5(4) human oversight requirement that this skill maps to disclosure decisions; pin the CELEX number because implementing acts are still being adopted.
3. EDPB Guidelines on AI and Data Protection (WP 29 / EDPB) — https://edpb.europa.eu/en/publications-and-documents/guidelines/artificial-intelligence_en — retrieved 2026-10-07. Defines how DPAs interpret GDPR in the context of AI systems; used only to cross-check, never as authority for legal text.
4. BfDI (Bundesbeauftragte fuer den Datenschutz) guidance on AI — https://www.bfdi.bund.de/EN/Home/home_node.html — retrieved 2026-10-07. German DPA interpretation of GDPR and AI Act; used only as cross-check for German member-state context, never as EU-level authority.
5. ISO/IEC TR 5498 (Records management principles) — https://www.iso.org/standard/82853.html — retrieved 2026-10-07. General records management framework used only as background context for the processing register design, never as legal authority.
6. European Commission: AI Act implementation timeline — https://digital-strategy.ec.europa.eu/en/policies/eu-ai-act — retrieved 2026-10-07. Official Commission page on the phased entry into force of the AI Act; used to pin the disclosure obligation start dates. Treat dates as unverified until the EUR-Lex text is re-checked at build time.

## Secondary sources (cross-check only)
- Community GDPR/AI Act checklists on GitHub — used only as test fixtures, never as authority.
- DATEV/GoBD FAQ cross-checks — used only to confirm retention overlap, never as authority for GDPR/AI Act text.

## Conflicts and open questions
- **Article 50(2) machine-readable marking duty start date (2026-12-02 per secondary source)** — have a lawyer confirm before an agent relies on it; the EUR-Lex text is the authority and this skill re-checks it at build time.
- **GDPR vs AI Act scope overlap** — an AI system can trigger both. The skill treats them as separate gates: GDPR for processing register (Art. 30), AI Act for disclosure (Art. 50). No conflict, but agents must run both gates.
- **Member-state additions** — Germany (BDSG), France, Netherlands may add requirements beyond the EU baseline. This skill stays at EU level and flags member-state additions as unverified until confirmed by local counsel.
- **Human-review evidence retention** — GDPR does not fix a number; the skill inherits the GoBD retention class from the gobd-archive skill (which applies to all business records in Ottili flows) and adds the Article 50 disclosure requirement on top of that base rule. Coordinate with gobd-archive for retention timing.
