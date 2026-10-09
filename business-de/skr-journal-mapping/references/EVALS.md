# skr-journal-mapping — EVALS

Five realistic prompts with expected behaviour and failure signs.

## 1. Prompt
> "Book this line: sale of goods, domestic, 19% VAT, EUR 100 net. Buyer pays EUR 119."

**Expected behaviour:** journal
```
S 1200 Bank 119.00 19
H 8000 Revenue 100.00 19
H 1570 USt 19.00 19
```
`scripts/journal_check.py` exits 0.

**Failure signs:** tax line missing (unbalanced or no tax account amount);
tax key 16/1 used instead of 19; debit ≠ credit.

## 2. Prompt
> "Is this journal valid? `[{account:1200,side:S,amount:100,tax_key:19},{account:8000,side:H,amount:100,tax_key:19}]`"

**Expected behaviour:** exit 0, "OK journal balanced, 2 lines".

**Failure signs:** exit 2 with "journal does not balance" or "unknown tax key".

## 3. Prompt
> "Map an intra-EU B2B supply (customer in France, 0% VAT)."

**Expected behaviour:** tax key **06/0**, account 4xxx revenue, no 1570 tax
line (0% rate). Reference the UStG §4a rule.

**Failure signs:** tax key 19 applied; a 1570 line with a 19% amount.

## 4. Prompt
> "Our ledger uses SKR03. Is account 1570 correct for the VAT line?"

**Expected behaviour:** SKR03 uses **1571** for USt (Soll), not 1570 (SKR04).
Flag the mismatch.

**Failure signs:** 1570 used in an SKR03 journal without noting the difference.

## 5. Prompt
> "A corrective entry was posted after the Monatsschluss. What do I do?"

**Expected behaviour:** refuse to close; require explicit unlock + re-lock cycle
and a documented reason; then re-run `scripts/period_lock_check.py`.

**Failure signs:** closing without the unlock cycle; no audit trail entry.
