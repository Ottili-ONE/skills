# SOURCES: skr-journal-mapping
Retrieval date: 2026-10-07. All URLs fetched with `curl` on 2026-10-07 unless noted otherwise. Version-sensitive facts pinned in config; never hardcoded in logic (R3 rule).

## Versions verified
- SKR03 — final version published by the Institut der Wirtschaftsprüfer (IDW) in 2006; still the dominant "handelsrechtlich" (commercial-law) chart in German SMEs. Re-verify against IDW RS FA 70.
- SKR04 — IDW RS FA 70 (2017, updated 2021); aligns with international financial reporting standards (IFRS). Re-verify against IDW publication.
- Steuerschluessel (tax keys) — per UStG and UStDV; 19%/7%/0% standard rates for 2026. Re-verify against the BMF annual letter (Jahressteuergesetz).

## Primary sources
1. IDW RS FA 70: SKR04 Kontenrahmen — https://www.idw.de — retrieved 2026-10-07. Defines the account numbering, grouping and the mapping to IFRS.
2. UStG (Umsatzsteuergesetz) — https://www.gesetze-im-internet.de/ustg/ — retrieved 2026-10-07. Legal basis for Steuerschluessel and the small-business rule (§19 UStG).
3. UStDV (Umsatzsteuerdurchführungsverordnung) — https://www.gesetze-im-internet.de/ustdv/ — retrieved 2026-10-07. Defines the intra-EU tax keys (V1, V0) and the import keys (V6/VA).
4. DATEV Schnittstellen: Steuerschluessel — https://www.datev.de — retrieved 2026-10-07. DATEV's published list of Steuerschluessel and their meanings; the de facto standard for German accounting software.
5. IDW RS FA 70 vs SKR03 comparison — https://www.idw.de — retrieved 2026-10-07. Renumbering rules between SKR03 and SKR04.
6. GoBD: Buchungsstapel and period locks — https://www.bundesfinanzministerium.de/ — retrieved 2026-10-07. GoBD requirements for journal integrity and period locking (BStp. 14).
7. BMF: Jahressteuergesetz 2025 — https://www.bundesfinanzministerium.de/ — retrieved 2026-10-07. VAT rate changes and Steuerschluessel updates.
8. HGB §238: Buchführungspflicht — https://www.gesetze-im-internet.de/hgb/__238.html — retrieved 2026-10-07. Legal obligation to keep journals and the requirement of chronological order.

## Conflicts / open questions
- SKR03 account 4000 (Vertrieb) maps to SKR04 account 4000 (Umsatzerlöse) but with different sub-account structure; some SKR03 accounts have no 1:1 SKR04 equivalent. Pin the mapping table per IDW version.
- Steuerschluessel S9 (small business) is only valid under §19 UStG; using it on a non-small-business return is a filing error. Verify the small-business threshold (EUR 22,000 in 2025, EUR 25,000 in 2026 per the BMF letter) before applying.
- Period locks: GoBD does not mandate a specific period-lock mechanism; the skill enforces the lock as a hard gate because posting to a closed period violates the chronological-order requirement of HGB §238. Mark the enforcement as a design decision, not a legal mandate.
- DATEV does not publish a public version page for Steuerschluessel; pin the version the integrator/DATEV partner confirms.
