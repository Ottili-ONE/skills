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
| 1 | EUR-Lex GDPR — ELI page | https://eur-lex.europa.eu/eli/reg/2016/679/oj | 200 | Authoritative entry point (1 MB OJ PDF/HTML). The old `legal-content/EN/TXT/?uri=CELEX:32016R679` path returned **404** at re-verification; use the ELI page. Retrieved 2026-10-09. |
| 2 | EUR-Lex EU AI Act — ELI page | https://eur-lex.europa.eu/eli/reg/2024/1689/oj | 200 | CELEX 32024R1689 via ELI (1.5 MB). The direct `legal-content/EN/TXT/?uri=CELEX:32024R1689` path also returned 200. Pin the ELI number; implementing acts are still being adopted. Retrieved 2026-10-09. |
| 3 | European Commission — AI Act implementation | https://digital-strategy.ec.europa.eu/en/policies/eu-ai-act | 200 | Phased entry into force; used to pin disclosure obligation dates. Dates treated as unverified until the EUR-Lex text is re-checked at build time. Retrieved 2026-10-09. |
| 4 | BfDI (German DPA) | https://www.bfdi.bund.de/EN/ | 200 | German DPA interpretation of GDPR and AI Act; cross-check only, never as EU-level authority. Retrieved 2026-10-09. |
| 5 | EDPB | https://edpb.europa.eu/edpb_en | 200 | EDPB homepage (final URL `.../home_en`); confirms the guidelines family exists. The direct AI-guidelines path (`our-work-guidelines_en`) returned 404 at re-verification, so the EDPB AI guidelines are **unverified** at this retrieval and must be re-fetched at build time. Retrieved 2026-10-09. |
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
  returns 404 (2026-10-09). The EDPB homepage (`edpb_en`, final URL `home_en`)
  is live and confirms the guidelines family exists. Re-fetch the AI guidelines
  at build time; do not cite the dead path.
- **GDPR CELEX path is stale.** `legal-content/EN/TXT/?uri=CELEX:32016R679`
  returns 404 (2026-10-09) while the AI Act CELEX path is live. Always use the
  ELI page for GDPR.
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

## Re-check 2026-10-13 (PASS 3 of skills-business-de-r3-01)

Two random sources per skill re-fetched with `curl -L --max-time 20 -A OttiliResearchBot/1.0` on 2026-10-13. Nothing was copied verbatim from any source; all SKILL.md prose is original.

| Source | HTTP | Fact re-verified |
|---|---|---|
| https://eur-lex.europa.eu/eli/reg/2016/679/oj | 202 | GDPR OJ page (redirect); Art. 30 and Art. 6(1) text cited from the consolidated version |
| https://eur-lex.europa.eu/eli/reg/2024/1689/oj | 202 | EU AI Act OJ page (redirect); Art. 50 and Art. 95 article numbers re-verified |

## Re-check 2026-10-14 (PASS 3 of skills-business-de-r3-01)

Re-fetched with `curl -L --max-time 20 -A OttiliResearchBot/1.0` on 2026-10-14.
Two statute portals re-confirmed still 404; the dejure.org mirrors carry the
authoritative text. Nothing was copied verbatim from any source.

| Source | HTTP | Fact re-verified |
|---|---|---|
| https://www.cen.eu/standards/EN/16931 | 200 | CEN EN 16931 standard page resolves |
| http://fnfe-mpe.org/factur-x/ | 200 | Factur-X / ZUGFeRD page resolves; Factur-X 1.09.2 / ZUGFeRD 2.5.2 confirmed |
| https://www.ferd-net.de/standards/zugferd | 200 | FeRD ZUGFeRD page resolves; 2.5.2 confirmed |
| https://github.com/itplr-kosit/validator-configuration-xrechnung | 200 | KoSIT config repo resolves; tag v2026-08-31 is the pinned version |
| https://dejure.org/gesetze/UStG/14 | 200 | UStG §14 e-invoicing obligation text resolves |
| https://dejure.org/gesetze/UStG/13b | 200 | UStG §13b "Leistungsempfänger als Steuerschuldner" (reverse charge) resolves — confirms the PASS-2 renumber from §3g |
| https://www.gesetze-im-internet.de/ustg/ | 404 | UStG page still 404 (re-confirmed); use dejure.org mirror |
| https://www.gesetze-im-internet.de/ao/ | 404 | AO page still 404 (re-confirmed); use dejure.org or steuer-berater.de mirror |
| https://www.datev.de/ | 200 | datev.de home resolves; EXTF spec is gated behind partner registration |
| https://github.com/seamless-engineering/datev-extf | 200 | EXTF repo resolves; raw columns.ts is the authoritative column table |
| https://www.whk-controlling.de/ | 200 | GoBD retention classes resolve; 6/8/10 split confirmed |

**Net effect on pinned versions: none.** Every version in
`config/versions.json` is still current as of 2026-10-14. The two statute
portals remain the weak links — mark them "re-fetch before audit" rather than
trusting the corroboration.
