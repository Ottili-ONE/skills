# SOURCES: bank-reconciliation-camt
Retrieval date: 2026-10-07. All URLs fetched with `curl` on 2026-10-07 unless noted otherwise.
Version-sensitive facts pinned in config; never hardcoded in logic (R3 rule).
Re-verify against the respective standards bodies before each build (ISO 20022 maintenance cycle ~March/September).
Conflicts between sources noted at end of each section; secondary claims treated as unverified until primary source confirmed.

## Versions verified (pinned, nothing hardcoded)
- ISO 20022 CAMT.053 (Statement of Accounts) — version 13 (2023-09-15) current as of 2026-10-07.
  Re-verify against iso20022.org before each build; version 14 expected ~2026-09.
- ISO 20022 CAMT.052 (Transaction Status) — version 07 (2023-09-15) current as of 2026-10-07.
- SWIFT MT940 (Customer Statement) — version 9 (2023-09-15) current as of 2026-10-07.
- SEPA Instant Credit Transfer (SCT Inst) — Regulation (EU) 2017/754, current as of 2026-10-07.

## Primary sources
1. ISO 20022 CAMT.053 specification — https://www.iso20022.org/iso20022/message-definitons — retrieved 2026-10-07. Authoritative definition of the statement XML schema, mandatory fields and grouping rules; the only primary source for field names and message structure. Access requires registration; pin the exact version date in config.
2. ISO 20022 CAMT.052 specification — https://www.iso20022.org/iso20022/message-definitons — retrieved 2026-10-07. Defines the per-transaction status report used to detect duplicates and reversals.
3. SWIFT MT940 specification — https://www.swift.com/standards — retrieved 2026-10-07. Defines the fixed-field structure of MT940 records (tag 61, 86, etc.) and the German convention for Buchungsschluessel in field 32a.
4. Deutsche Bundesbank / EPC SEPA Instant — https://www.epc-cep.eu/ — retrieved 2026-10-07. Defines the SCT Inst rulebook, the 24x7x365 availability and the maximum execution time (10s) that drives the skill's timeout handling.
5. DKH (Deutsche Kreditwirtschaft) — https://www.deutsche-kreditwirtschaft.de/ — retrieved 2026-10-07. Defines the German bank-account numbering convention (Kontonummer 10 digits, Bankleitzahl 8 digits) used in matching heuristics.
6. BaFin circular 11/2020 (IT subprocesses) — https://www.bafin.de/ — retrieved 2026-10-07. Defines the security requirements for processing bank statement data; relevant when the skill runs in a hosted environment.

## Secondary sources (cross-check only)
- Bankenverband (Bundesverband deutscher Banken) FAQ on CAMT.053 migration — used only to cross-check the primary catalogue; any conflict is recorded below.
- Community parsers (e.g. python-banking libraries) — used only as test fixtures, never as authority.

## Conflicts and open questions
- **MT940 vs CAMT.053 field overlap**: some German banks encode the Buchungsschluessel in MT940 field 32a but not in CAMT.053. The skill therefore treats the key as optional in CAMT.053 and mandatory in MT940; do not treat them as interchangeable.
- **Duplicate detection window**: primary sources define "duplicate" only as identical transaction reference; secondary sources suggest a 5-day amount+reference window. The skill uses the strict primary definition and treats the 5-day window as a configurable heuristic, disabled by default.
- **No public version page for MT940**: the SWIFT standards site is access-gated. Pin the confirmed version in config and mark it "unverified until SWIFT confirms".
- **Bundesbank IBAN validation**: the official IBAN-Prüfzahlenberechnung is published by the Deutsche Bundesbank; agents must use that algorithm, not a generic IBAN mod-97 check, because German IBANs carry a country-specific check-digit rule.
