# DESIGN: skr-journal-mapping

## Trigger description (SKILL.md description draft, <=1024 chars)
"Map German chart-of-accounts (SKR03 / SKR04) to automatic journals with correct tax keys, period locks, and GoBD-compliant retention. Use when an agent must generate journal entries from invoices, assign tax keys, lock periods for the tax return, or reconcile SKR03/SKR04 mappings."

## Procedure outline
1. **Identify the Kontenrahmen** - SKR03 (GmbH & Co. KG) or SKR04 (GmbH). The mapping differs per Kontenrahmen; pin the Kontenrahmen in config.
2. **Map account to tax key** - each account has a default Steuerschluessel (tax key): 19% for standard-rate revenue accounts, 7% for reduced-rate revenue, 0% for exports and intra-EU supplies, etc. Validate every mapping against the current UStG rates. Tax-key changes are the highest-error-rate area in German VAT (see ust-edge-cases SOURCES.md).
3. **Generate journal entries** - one entry per invoice line with: Konto (account), Betrag (amount), Steuerschluessel (tax key), Belegdatum (document date), Buchungsdatum (booking date). Validate mandatory fields per SKR rules.
4. **Period lock** - at month-end / year-end, lock the period so no new bookings can be added without an override approval record. The lock is a policy decision; the skill enforces it technically via a flag + audit log entry + notification to the tax advisor.
5. **Reconcile** - compare generated journals against source invoices; report mismatches as blocking errors until resolved by a human reviewer with documented evidence of review.
6. **Retain** - keep the journal and its source invoices for 8 years (vouchers) / 10 years (books) per BEG IV; record checksum and retrieval path.

## Scripts planned
- `scripts/map_skr.py` - given a Kontenrahmen (SKR03/SKR04) and an account number, outputs the default tax key and the recommended journal structure.
- `scripts/generate_journal.py` - given a list of invoice lines, produces a SKR-compliant journal entry set with tax keys.
- `scripts/period_lock.py` - locks a period, records the approval, and prevents further bookings until an override with evidence.

## Five eval prompts
1. "Map our SKR04 revenue account 4000 to a tax key." -> must say 19% (standard rate) for domestic revenue, with the caveat that intra-EU exports use 0% and the mapping must be re-verified against the current UStG rates.
2. "Generate a journal entry for a domestic B2B sale, EUR 1,200.00 net, 19% VAT, on account 4000." -> must produce a journal entry with account 4000, tax key 19%, and the correct amount split.
3. "Lock our December 2026 period." -> must set the lock flag, record the approval, and prevent further bookings until an override with evidence.
4. "Our journal says tax key 19% but the invoice says 7%. What do we do?" -> must flag this as a blocking mismatch, list the possible causes (reduced-rate item, wrong account mapping, wrong Steuerschluessel), and require human review before release.
5. "Reconcile our generated journals against the source invoices." -> must report mismatches as blocking errors until resolved by a human reviewer with documented evidence of review.

## What this skill does better than generic agents
- It encodes the *SKR-specific* account-to-tax-key mapping, not a generic "19% VAT" rule.
- It distinguishes SKR03 and SKR04 and pins the Kontenrahmen in config.
- It treats the period lock as a technical enforcement (flag + audit log + override), not a policy statement.
- It requires documented human review for mismatches, because wrong tax keys produce wrong returns.
