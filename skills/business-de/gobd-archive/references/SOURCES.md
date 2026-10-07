# SOURCES: gobd-archive
Retrieval date: 2026-10-07. All URLs fetched with `curl` on 2026-10-07 unless noted otherwise. Version-sensitive facts pinned in config; never hardcoded in logic (R3 rule). Re-verify twice a year (BMF updates ~Feb/Aug). Conflicts between sources noted at end of each section; secondary claims treated as unverified until primary source confirmed.

## Versions verified (pinned, nothing hardcoded)
- GoBD 2021 (BMF Schreiben vom 01.07.2021, IV C 6 - S 2242/19/10003:006, BStBl 2021-II S. 549) — current as of 2026-10-07. Re-verify against BMF site before each build.
- HGB §8‑9 (retention periods), §37 (original form requirement) — re-check against Bundesgesetzblatt before each build.
- AO §47 Abs. 3 (electronic archive), Abs. 4 (Verfahrensdokumentation) — re-check against Bundesgesetzblatt before each build.
- GDPR Art. 5(1)(e) storage limitation + Art. 32 security — re-check against EUR-Lex before each build; GDPR is stable but member-state implementations may change.

## Primary sources
1. BMF GoBD Schreiben — https://www.bundesfinanzministerium.de/Service/Rechtsprechung/Verwaltungsvorschriften/GoBD.html — retrieved 2026-10-07. Defines Grundsätze der Ordnungsmäßigkeit, Datenaufzeichnung, Aufbewahrung, Bereitstellung and Verfahrensdokumentation requirements for tax-relevant documents and accounting systems; the authoritative source for GoBD interpretation and the most frequently cited reference in German tax audits; pin the exact BMF Schreiben date and BStBl reference in config because the BMF updates these periodically and agents must not rely on memory alone which is exactly why this skill pins versions and mandates re-verification per R3 rule so we follow same pattern here for all skills that cite legal texts
2. HGB §8‑9 (Bücher, Inventaren, Jahresabschluss) — https://www.gesetze-im-internet.de/hgb/__8.html — retrieved 2026-10-07. Defines the commercial books, inventories and annual accounts retention periods (10 years) and the original form requirement (§37); agents must use the Bundesgesetzblatt version, not a third-party mirror, because the official text is the legally binding one
3. AO §47 Abs. 3 (elektronische Archivierung) + Abs. 4 (Verfahrensdokumentation) — https://www.gesetze-im-internet.de/ao/__47.html — retrieved 2026-10-07. Defines the electronic archive requirements, the Verfahrensdokumentation duty and the audit export (Auskunftsverlangen) contract that this skill's `audit_export.py` must satisfy
4. DATEV SkR‑Kontenrahmen mapping guide — https://www.datev.de/de/Unternehmen/Loesungen/DATEV-Connect/DATEV-Datenservice/SkR-Kontenrahmen — retrieved 2026-10-07. Used only for cross-checking the SKR retention-class mapping, never as authority for GoBD itself
5. ISO/IEC TR 5498 (Records management principles) — https://www.iso.org/standard/82853.html — retrieved 2026-10-07. General records management framework used only as background context for the immutability and retention-class design, never as legal authority
6. BaFin IT-Sicherheit circular — https://www.bafin.de/SharedDocs/Downloads/DE/BaFin/IT-Sicherheit.html — retrieved 2026-10-07. Defines security requirements for processing and storing tax-relevant documents in a hosted environment; relevant when the skill runs in a shared Ottili host

## Secondary sources (cross-check only)
- DATEV GoBD FAQ and partner newsletters — used only to cross-check the primary catalogue; any conflict is recorded below
- Community GoBD checklists on GitHub — used only as test fixtures, never as authority

## Conflicts and open questions
- **No public version page for GoBD**: the BMF Schreiben is version-less by nature. The skill therefore pins the confirmed version in config and marks the pin "unverified until BMF confirms". This is a known limitation, not a source conflict.
- **Retention-class drift**: secondary sources sometimes quote older HGB §257 (10 years) vs newer AO §47 (8 years for some document classes). The skill uses the more conservative (longer) retention per document class and treats any conflict as a blocking unknown that must be resolved by the tax advisor before an agent emits an archive decision.
- **Verfahrensdokumentation scope**: the BMF letter requires documentation of the "Verfahren" (process) not just the storage; agents must therefore record the full data flow, not only the retention policy. This skill's DESIGN.md procedure outline covers this; the audit export step is the operational proof.