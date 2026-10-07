# DESIGN: skr-journal-mapping

## Trigger description (SKILL.md description draft, <=1024 chars)
"Map German SKR03/SKR04 account keys (Kontenrahmen) to Ottili journal lines and tax keys: SKR03 vs SKR04 differences, tax keys (Steuerschluessel), automatic journal generation and period locks. Use when an agent must translate a ledger account into a journal entry, pick the correct Steuerschluessel, generate an automatic journal, or detect a period-lock conflict. Not for general accounting policy or non-German chart of accounts."

## Procedure outline
1. **Identify the Kontenrahmen** — SKR03 (handelsrechtlich) or SKR04 (idW RSFA kompatibel). The choice changes the account numbering and the tax keys.
2. **Map the account** — given a ledger account, output the SKR03/SKR04 number, the tax key (Steuerschluessel) and the side (Soll/Haben).
3. **Pick the tax key** — 19% Inland => S1 (or V0/Vorsteuer), 7% => S2, 0% => S3; export (EU) => V1; import => V6/VA; small business => S9. Use the pinned tax-key table; never guess.
4. **Generate the automatic journal** — emit the journal with the correct Buchungsschluessel and the period (Monat/Jahr).
5. **Check period locks** — a journal for a closed period must not be posted; detect and reject with a clear error.
6. **Reconcile** — compare the generated journal against the source ledger; log the mapping.

## Scripts planned
- `scripts/skr_map.py` — maps a ledger account to SKR03/SKR04 number + tax key.
- `scripts/journal_emit.py` — emits an automatic journal from a mapping.
- `scripts/period_check.py` — checks whether a period is locked before posting.

## Five eval prompts
1. "Map a domestic sales account (EUR 1,000, 19% VAT) to SKR04." -> must output the SKR04 number, the Steuerschluessel and the journal sides.
2. "What is the difference between SKR03 and SKR04 for account 4000?" -> must name the renumbering rule and which standard each follows.
3. "Generate an automatic journal for an EU export sale." -> must use the EU tax key (V1) and the correct Buchungsschluessel.
4. "We want to post to period 2026-03, which is closed." -> must reject and name the period-lock rule.
5. "Pin the tax-key table we use." -> must read config, never hardcode, and record the retrieval date.

## What this skill does better than generic agents
- Distinguishes SKR03 from SKR04 with a decision table instead of conflating them.
- Encodes the Steuerschluessel table with the import/export keys, which generic agents get wrong.
- Treats period locks as a hard gate, not a soft warning.
