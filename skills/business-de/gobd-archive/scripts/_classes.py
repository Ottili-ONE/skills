#!/usr/bin/env python3
"""Shared GoBD retention-class table for gobd-archive scripts.

Single source of truth for the BEG IV / AO §147 Abs. 3 n.F. (effective
2025-01-01) class map. Duplicating this table in retention_classify.py and
purge_decision.py is a drift hazard — a class added to one but not the other
silently changes the purge math. Verified 2026-10-13 against AO §147
(dejure.org mirror, HTTP 200) and steuer-berater.de / whk-controlling.de.

The clock starts at the end of the calendar year in which the document was
created, not on the document's own date.
"""

# (document_type) -> (retention_class label, retention years)
CLASSES = {
    "invoice": ("Buchungsbeleg", 8),
    "voucher": ("Buchungsbeleg", 8),
    "bank-statement": ("Buchungsbeleg", 8),
    "booking": ("Buchungsbeleg", 8),
    "receipt": ("Buchungsbeleg", 8),
    "booking-slip": ("Buchungsbeleg", 8),
    "ledger": ("Bücher / Jahresabschluss", 10),
    "annual-account": ("Bücher / Jahresabschluss", 10),
    "balance-sheet": ("Bücher / Jahresabschluss", 10),
    "income-statement": ("Bücher / Jahresabschluss", 10),
    "inventory": ("Bücher / Jahresabschluss", 10),
    "correspondence": ("Geschäftskorrespondenz", 6),
    "contract": ("Geschäftskorrespondenz", 6),
    "letter": ("Geschäftskorrespondenz", 6),
}


def retention_end(year: int, years: int) -> str:
    """Retention runs from the end of the calendar year of creation."""
    if not isinstance(year, int) or year < 1900 or year > 2100:
        raise ValueError(f"implausible year: {year!r}")
    return f"{year + years}-12-31"


def classify(doc_type: str, year: int) -> tuple:
    """Return (label, years, retention_end). Raises ValueError on bad input."""
    if doc_type not in CLASSES:
        raise ValueError(f"unknown document type: {doc_type!r}; "
                         f"choose from {sorted(CLASSES)}")
    label, years = CLASSES[doc_type]
    return label, years, retention_end(year, years)
