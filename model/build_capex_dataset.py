"""
Rebuild data/processed/hyperscaler_capex.csv from primary sources.

- Alphabet: extracted & cross-validated from 10-K PDFs in data/raw/alphabet
  (see model/extract_capex2.py). Values hard-coded here with page citations.
- Microsoft / Amazon / Meta: pulled from SEC EDGAR XBRL company-concept API
  (data/raw/edgar/*.json), using the *as-originally-reported* annual value
  (the filing whose own fiscal year matches the period end).

Capex concept = cash purchases of property & equipment, kept consistent across
companies for comparability:
  - us-gaap:PaymentsToAcquirePropertyPlantAndEquipment (MSFT, META, Alphabet)
  - us-gaap:PaymentsToAcquireProductiveAssets          (AMZN)

Run: .venv\\Scripts\\python model\\build_capex_dataset.py
"""
import csv
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDGAR = ROOT / "data" / "raw" / "edgar"
OUT = ROOT / "data" / "processed" / "hyperscaler_capex.csv"

# --- Alphabet: extracted from 10-K PDFs, cross-validated across filings ------ #
ALPHABET = [
    # fy, capex_usd_m, source_doc, page
    (2018, 25139, "2020.pdf", 59),
    (2019, 23548, "2020.pdf", 59),
    (2020, 22281, "2020.pdf", 59),
    (2021, 24640, "2021.pdf", 54),
    (2022, 31485, "2022.pdf", 52),
    (2023, 32251, "2023.pdf", 56),
    (2024, 52535, "2024.pdf", 57),
    (2025, 91447, "2025.pdf", 53),
]

# --- EDGAR config per company ----------------------------------------------- #
EDGAR_COS = {
    "Microsoft": {
        "file": "microsoft_capex.json",
        "fy_end_month": 6,
        "note": "Cash purchases of PP&E (excl. finance leases); FY ends Jun 30 "
                "- not calendar-aligned",
    },
    "Amazon": {
        "file": "amazon_capex.json",
        "fy_end_month": 12,
        "note": "Purchases of PP&E incl. fulfilment/logistics - AWS is a subset; "
                "apply AI-share haircut",
    },
    "Meta": {
        "file": "meta_capex.json",
        "fy_end_month": 12,
        "note": "Purchases of PP&E; as-originally-reported (minor later "
                "reclassifications exist)",
    },
    "Oracle": {
        "file": "oracle_capex.json",
        "fy_end_month": 5,
        "note": "Capital expenditures (cash); FY ends May 31 - not "
                "calendar-aligned",
    },
}

# Quarterly series uses EDGAR XBRL for all five (Alphabet included).
QUARTERLY_FILES = {
    "Alphabet": "alphabet_capex.json",
    "Microsoft": "microsoft_capex.json",
    "Amazon": "amazon_capex.json",
    "Meta": "meta_capex.json",
    "Oracle": "oracle_capex.json",
}

QOUT = ROOT / "data" / "processed" / "hyperscaler_capex_quarterly.csv"


def edgar_annual(path: Path):
    """Return {end_year: (val_usd_m, accession)} using as-originally-reported."""
    d = json.loads(path.read_text())
    out = {}
    for r in d["units"]["USD"]:
        if r.get("form") != "10-K":
            continue
        try:
            s = date.fromisoformat(r["start"])
            e = date.fromisoformat(r["end"])
        except (KeyError, ValueError):
            continue
        if not (350 <= (e - s).days <= 380):
            continue
        y = e.year
        original = r.get("fy") == y          # filing's own fiscal year
        if y not in out or original:
            out[y] = (round(r["val"] / 1e6), r["accn"])
    return out


def edgar_quarterly(path: Path, since_year: int = 2020):
    """Derive discrete quarterly capex from cumulative (YTD) cash-flow values.

    10-Q cash-flow figures are year-to-date, so quarters are obtained by
    differencing consecutive YTD periods that share a fiscal-year start;
    the first period of each fiscal year is taken as-is.
    """
    d = json.loads(path.read_text())
    periods = {}
    for r in d["units"]["USD"]:
        if r.get("form") not in ("10-Q", "10-K"):
            continue
        try:
            s = date.fromisoformat(r["start"])
            e = date.fromisoformat(r["end"])
        except (KeyError, ValueError):
            continue
        days = (e - s).days
        if not (80 <= days <= 380):
            continue
        # keep the latest-filed value per (start, end)
        periods[(s, e)] = r["val"]

    by_start = {}
    for (s, e), val in periods.items():
        by_start.setdefault(s, []).append((e, val))

    quarters = []
    for s, ends in by_start.items():
        ends.sort()
        prev_val = 0.0
        for e, val in ends:
            q_val = val - prev_val
            prev_val = val
            quarters.append((e, q_val))

    out = {}
    for e, q_val in quarters:
        if e.year >= since_year and q_val > 0:
            out[e] = round(q_val / 1e6)
    return out


def main():
    rows = []
    for fy, capex, doc, page in ALPHABET:
        rows.append(dict(
            company="Alphabet", fiscal_year=fy, capex_usd_m=capex,
            fy_end_month=12, source_type="10-K (extracted)",
            source_doc=doc, source_page=page,
            note="Purchases of property and equipment; cross-validated across filings",
        ))

    for company, cfg in EDGAR_COS.items():
        data = edgar_annual(EDGAR / cfg["file"])
        for y in sorted(data):
            if y < 2018:
                continue
            val, accn = data[y]
            rows.append(dict(
                company=company, fiscal_year=y, capex_usd_m=val,
                fy_end_month=cfg["fy_end_month"],
                source_type="10-K (EDGAR XBRL)",
                source_doc=accn, source_page="",
                note=cfg["note"],
            ))

    cols = ["company", "fiscal_year", "capex_usd_m", "fy_end_month",
            "source_type", "source_doc", "source_page", "note"]
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUT.relative_to(ROOT)}")

    qrows = []
    for company, fname in QUARTERLY_FILES.items():
        q = edgar_quarterly(EDGAR / fname)
        for end in sorted(q):
            qrows.append(dict(
                company=company, period_end=end.isoformat(),
                capex_usd_m=q[end], source_type="10-Q/10-K (EDGAR XBRL)",
            ))
    qcols = ["company", "period_end", "capex_usd_m", "source_type"]
    with QOUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=qcols)
        w.writeheader()
        w.writerows(qrows)
    print(f"Wrote {len(qrows)} quarterly rows to {QOUT.relative_to(ROOT)}")

    for c in ["Alphabet", "Microsoft", "Amazon", "Meta", "Oracle"]:
        cr = [r for r in rows if r["company"] == c]
        latest = max(cr, key=lambda r: r["fiscal_year"])
        print(f"  {c}: {len(cr)} yrs, latest FY{latest['fiscal_year']} "
              f"${latest['capex_usd_m']/1000:,.1f}B")


if __name__ == "__main__":
    main()
