# SOURCES: dsgvo-ai-act-labeling

Retrieval date: 2026-10-09 (all URLs re-fetched with `curl` on that date unless
noted). Version-sensitive facts are pinned in `config/versions.json` and
never hardcoded in logic (R3 rule). Re-check EUR-Lex before each build
(GDPR is stable but member-state implementations may change; EU AI Act
implementing acts are still being adopted). Conflicts between sources noted at
the end.

## Versions verified (pinned, nothing hardcoded)
- GDPR Regulation (EU) 2016/679 — current as of 2026-10-09; re-check EUR-Lex
  before each build. Article 30 processing register, Article 6 legal bases.
- EU AI Act Regulation (EU) 2024/1689 — current as of 2026-10-09. Article
  5(4) human oversight; Article 50 transparency obligations for certain AI
  systems.

## Primary sources (re-verified 2026-10-09)

| # | Source | URL | HTTP | Notes |
|---|---|---|---|---|
| 1 | EUR-Lex GDPR — ELI page | https://eur-lex.europa.eu/eli/reg/2016/679/oj | 200 | Authoritative entry point. The old `legal-content/EN/TXT/?uri=CELEX:32016R679` path returned 404 at re-verification; use the ELI page. Retrieved 2026-10-09. |
| 2 | EUR-Lex EU AI Act — ELI page | https://eur-lex.europa.eu/eli/reg/2024/1689/oj | 200 | CELEX 32024R1689 via ELI. Pin the ELI number; implementing acts are still being adopted. Retrieved 2026-10-09. |
| 3 | European Commission — AI Act implementation | https://digital-strategy.ec.europa.eu/en/policies/eu-ai-act | 200 | Phased entry into force; used to pin disclosure obligation dates. Dates treated as unverified until the EUR-Lex text is re-checked at build time. Retrieved 2026-10-09. |
| 4 | BfDI (German DPA) | https://www.bfdi.bund.de/EN/ | 200 | German DPA interpretation of GDPR and AI Act; cross-check only, never as EU-level authority. Retrieved 2026-10-09. |
| 5 | EDPB | https://edpb.europa.eu/edpb_en | 200 | EDPB homepage; the direct guidelines path (`our-work-guidelines_en`) returned 404 at re-verification. EDPB AI guidelines are therefore **unverified** at this retrieval and must be re-fetched at build time. Retrieved 2026-10-09. |
| 6 | OWASP Top Ten | https://owasp.org/www-project-top-ten/ | 200 | Security baseline; the `www-project-api-security/` path returned 404 at re-verification. Retrieved 2026-10-09. |

## Secondary sources (cross-check only)
- ISO/IEC TR 5498 — https://www.iso.org/standard/82853.html returned **403**
  at re-verification (2026-10-09). Records-management background only, never a
  legal authority. Marked unverified until the ISO page is reachable.
- Community GDPR/AI Act checklists on GitHub — used only as test fixtures,
  never as authority.
- DATEV/GoBD FAQ cross-checks — used only to confirm retention overlap, never
  as authority for GDPR/AI Act text.

## Conflicts and open questions
- **EDPB AI guidelines URL is stale.** The previously cited
  `edpb.europa.eu/en/publications-and-documents/guidelines/artificial-intelligence_en`
  returns 404 (2026-10-09). The EDPB homepage (`edpb_en`) is live. Re-fetch the
  AI guidelines at build time; do not cite the dead path.
- **ISO/IEC TR 5498 is behind a 403.** Treated as unverified background; the
  processing register design rests on Art. 30 GDPR, not on ISO.
- **Article 50(2) machine-readable marking duty start date (2026-12-02 per
  secondary source)** — have a lawyer confirm before an agent relies on it;
  the EUR-Lex text is the authority and this skill re-checks it at build time.
- **GDPR vs AI Act scope overlap** — an AI system can trigger both. The skill
  treats them as separate gates: GDPR for the processing register (Art. 30),
  AI Act for disclosure (Art. 50). No conflict, but agents must run both gates.
- **Member-state additions** — Germany (BDSG), France, the Netherlands may add
  requirements beyond the EU baseline. This skill stays at EU level and flags
  member-state additions as unverified until confirmed by local counsel.
- **Human-review evidence retention** — GDPR does not fix a number; the
  skill inherits the GoBD retention class from the `gobd-archive` skill (which
  applies to all business records in Ottili flows) and adds the Article 50
  disclosure requirement on top of that base rule.
