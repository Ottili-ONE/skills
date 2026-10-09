# bank-reconciliation-camt — SOURCES

Retrieval date: 2026-10-09.

| # | Source | URL | Retrieved | Verified version | Notes |
|---|---|---|---|---|---|
| 1 | Wikipedia — Camt-Format (de) | https://de.wikipedia.org/wiki/Camt-Format | 2026-10-09 | last edited 2025 | **200 OK**. Confirms: camt.053 replaces MT940, camt.052 replaces MT942, camt.054 replaces MT900/910; SEPA mandatory since 2014; SWIFT Nov 2025 closed the MT→ISO 20022 migration for cross-border payments, **no fixed deprecation for MT940 reporting**; EBICS transmission per DFÜ-Abkommen Anlage 3. |
| 2 | Wikipedia — MT940 (en) | https://en.wikipedia.org/wiki/MT940 | 2026-10-09 | last edited 2025-05-16 | **200 OK**. Confirms MT940 is the SWIFT standard for end-of-day account statements; long-term replacement by ISO 20022. |
| 3 | ISO 20022 — camt.053 | https://www.iso20022.org/camt.053 | 2026-10-09 | — | **403** (access-restricted). The message definition is cited from the de.wikipedia Camt-Format article and the DFÜ-Abkommen. |
| 4 | SWIFT — standards | https://www.swift.com/standards | 2026-10-09 | — | **403** (access-restricted). |
| 5 | Bundesbank — MT940 | https://www.bundesbank.de/en/service/mt940 | 2026-10-09 | — | **404** at retrieval. |
| 6 | R3_VERIFIED_FACTS.md | ../ottili-planning/inputs/R3_VERIFIED_FACTS.md | 2026-10-06 | — | starting point, re-verified 2026-10-09. |

**Conflict note:** no conflicts among the 200-OK sources. The ISO/SWIFT/Bundesbank
pages were unreachable; the camt.053 namespace and field model are taken from
the de.wikipedia article and the DFÜ-Abkommen. Re-fetch before audit.
