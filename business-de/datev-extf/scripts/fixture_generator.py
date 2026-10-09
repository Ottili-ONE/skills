#!/usr/bin/env python3
"""Generate deterministic DATEV EXTF test fixtures: a valid Buchungsstapel and a
deliberately broken one for negative testing. Runnable offline.

Usage:
    python3 fixture_generator.py --out-dir ./fixtures
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from common import load_config  # noqa: E402


# Line 2 of a DATEV Buchungsstapel: the 125-column heading row, copied verbatim
# from DATEV's Musterdaten (Formatversion 13) as corroborated by
# seamless-engineering/datev-extf src/columns.ts (EXTF_AS_OF 2026-09-25).
HEADING_ROW = [
    "Umsatz (ohne Soll/Haben-Kz)", "Soll/Haben-Kennzeichen", "WKZ Umsatz",
    "Kurs", "Basis-Umsatz", "WKZ Basis-Umsatz", "Konto",
    "Gegenkonto (ohne BU-Schlüssel)", "BU-Schlüssel", "Belegdatum",
    "Belegfeld 1", "Belegfeld 2", "Skonto", "Buchungstext", "Postensperre",
    "Diverse Adressnummer", "Geschäftspartnerbank", "Sachverhalt",
    "Zinssperre", "Beleglink", "Beleginfo - Art 1", "Beleginfo - Inhalt 1",
    "Beleginfo - Art 2", "Beleginfo - Inhalt 2", "Beleginfo - Art 3",
    "Beleginfo - Inhalt 3", "Beleginfo - Art 4", "Beleginfo - Inhalt 4",
    "Beleginfo - Art 5", "Beleginfo - Inhalt 5", "Beleginfo - Art 6",
    "Beleginfo - Inhalt 6", "Beleginfo - Art 7", "Beleginfo - Inhalt 7",
    "Beleginfo - Art 8", "Beleginfo - Inhalt 8", "KOST1 - Kostenstelle",
    "KOST2 - Kostenstelle", "Kost-Menge", "EU-Land u. UStID (Bestimmung)",
    "EU-Steuersatz (Bestimmung)", "Abw. Versteuerungsart", "Sachverhalt L+L",
    "Funktionsergänzung L+L", "BU 49 Hauptfunktionstyp",
    "BU 49 Hauptfunktionsnummer", "BU 49 Funktionsergänzung",
    "Zusatzinformation - Art 1", "Zusatzinformation- Inhalt 1",
    "Zusatzinformation - Art 2", "Zusatzinformation- Inhalt 2",
    "Zusatzinformation - Art 3", "Zusatzinformation- Inhalt 3",
    "Zusatzinformation - Art 4", "Zusatzinformation- Inhalt 4",
    "Zusatzinformation - Art 5", "Zusatzinformation- Inhalt 5",
    "Zusatzinformation - Art 6", "Zusatzinformation- Inhalt 6",
    "Zusatzinformation - Art 7", "Zusatzinformation- Inhalt 7",
    "Zusatzinformation - Art 8", "Zusatzinformation- Inhalt 8",
    "Zusatzinformation - Art 9", "Zusatzinformation- Inhalt 9",
    "Zusatzinformation - Art 10", "Zusatzinformation- Inhalt 10",
    "Zusatzinformation - Art 11", "Zusatzinformation- Inhalt 11",
    "Zusatzinformation - Art 12", "Zusatzinformation- Inhalt 12",
    "Zusatzinformation - Art 13", "Zusatzinformation- Inhalt 13",
    "Zusatzinformation - Art 14", "Zusatzinformation- Inhalt 14",
    "Zusatzinformation - Art 15", "Zusatzinformation- Inhalt 15",
    "Zusatzinformation - Art 16", "Zusatzinformation- Inhalt 16",
    "Zusatzinformation - Art 17", "Zusatzinformation- Inhalt 17",
    "Zusatzinformation - Art 18", "Zusatzinformation- Inhalt 18",
    "Stück", "Gewicht", "Zahlweise", "Forderungsart", "Veranlagungsjahr",
    "Zugeordnete Fälligkeit", "Skontotyp", "Auftragsnummer", "Buchungstyp",
    "USt-Schlüssel (Anzahlungen)", "EU-Land (Anzahlungen)",
    "Sachverhalt L+L (Anzahlungen)", "EU-Steuersatz (Anzahlungen)",
    "Erlöskonto (Anzahlungen)", "Herkunft-Kz", "Buchungs GUID",
    "KOST-Datum", "SEPA-Mandatsreferenz", "Skontosperre",
    "Gellschaftername", "Beteiligtennummer", "Identifikationsnummer",
    "Zeichnernummer", "Postensperre bis",
    "Bezeichnung SoBil-Sachverhalt", "Kennzeichen SoBil-Buchung",
    "Festschreibung", "Leistungsdatum", "Datum Zuord. Steuerperiode",
    "Fälligkeit", "Generalumkehr (GU)", "Steuersatz", "Land",
    "Abrechnungsreferenz", "BVV-Position", "EU-Land u. UStID (Ursprung)",
    "EU-Steuersatz (Ursprung)", "Abw. Skontokonto",
]


def header(label):
    return [
        "EXTF", "700", "21", "Buchungsstapel", "13", "20261008",
        "", "", "", "", "29098", "55003", "20260101", "4",
        "20260601", "20260630", label, "", "1", "EUR", "", "", "",
        "03", "", "", "", "", "", "", "",
    ]


def booking(amount, side, account, beleg, text):
    row = [""] * 125
    row[0] = amount
    row[1] = side
    row[6] = account
    row[9] = beleg
    row[13] = text
    row[124] = "19"
    return row


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default="./fixtures")
    ap.add_argument("--config", default="config/versions.json")
    args = ap.parse_args()

    pinned = load_config(args.config)["datev-extf"]
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    import csv
    valid_path = out / "buchungsstapel-valid.csv"
    broken_path = out / "buchungsstapel-broken.csv"

    with valid_path.open("w", encoding="cp1252", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(header("Fixture 06/2026"))
        w.writerow(HEADING_ROW)
        w.writerow(booking("1200", "S", "4000", "0206", "Netto+19%"))
        w.writerow(booking("500", "S", "4200", "0306", "Netto+7%"))

    with broken_path.open("w", encoding="cp1252", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(header("Fixture-broken 06/2026"))
        w.writerow(HEADING_ROW)
        # dot instead of comma, and a malformed Belegdatum
        w.writerow(booking("12.50", "S", "4000", "2026601", "Netto+19%"))

    print(json.dumps({
        "ok": True,
        "out_dir": str(out),
        "valid": str(valid_path),
        "broken": str(broken_path),
        "pinned_versionsnummer": pinned["extf_schema"]["version"].split("/")[0],
        "broken_fixtures": [
            {"file": str(broken_path),
             "expected_errors": [
                 "amount uses a dot; DATEV expects a comma",
                 "Belegdatum must be YYYYMMDD",
             ]},
        ],
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
