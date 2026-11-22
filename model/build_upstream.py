"""Build the upstream and power-supplier series.

Outputs (data/processed):
  equipment_vendors.csv  Chip-equipment revenue by fiscal year ($B): ASML
                         (calendar year, EUR converted at ECB annual average
                         rates), Applied Materials (FY ends Oct), Lam Research
                         and KLA (FY ends Jun).
  power_suppliers.csv    Revenue ($B) for listed power and cooling suppliers
                         to data centers: GE Vernova, Vertiv, Eaton.
  networking_vendors.csv Corning Optical Communications segment rows
                         (from Corning 10-K segment tables) are upserted.
  roce_by_layer.csv      "Chip equipment" row inserted as the first layer,
                         same method as the other layers: aggregate operating
                         income over aggregate capital employed (total assets
                         minus current liabilities), latest 10-K/20-F.

Inputs: EDGAR company facts cached in data/raw/edgar/upstream/ (fetched with
model/edgar.py), plus the figures below that the structured data lacks.

Run from the project root:  python model/build_upstream.py
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "edgar" / "upstream"
PROC = ROOT / "data" / "processed"

EQUIP = {"ASML": 937966, "Applied Materials": 6951, "Lam Research": 707549,
         "KLA": 319201}
POWER = {"GE Vernova": 1996810, "Vertiv": 1674101, "Eaton": 1551182}
FY_END = {"ASML": "Dec", "Applied Materials": "Oct", "Lam Research": "Jun",
          "KLA": "Jun"}
# ECB reference rate, annual average USD per EUR (2025 approximate)
EURUSD = {2019: 1.1195, 2020: 1.1422, 2021: 1.1827, 2022: 1.0530,
          2023: 1.0813, 2024: 1.0824, 2025: 1.13}
# Not yet in a 10-K: Applied Materials FY2026 (8-K, 12 Nov 2026)
EXTRA_REV = {("Applied Materials", 2026): (34.45, "8-K Q4 FY2026 release")}
# Vertiv 2026 net sales guidance midpoint ($14.45-14.85B, Oct-2026)
POWER_GUIDE = {("Vertiv", 2026): (14.65, "2026 guidance $14.45-14.85B (Oct-2026)")}
# Corning Optical Communications segment net sales, $M (10-K segment tables)
CORNING_OC = {2021: 4349, 2022: 5023, 2023: 4012, 2024: 4657, 2025: 6274}

REV = ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues",
       "Revenue"]


def facts(cik: int) -> dict:
    return json.loads((RAW / f"{cik}.json").read_text())["facts"]


def annual(f: dict, tags: list[str], flow: bool = True) -> tuple[dict, str]:
    """{fiscal-year-end year: value $B} from 10-K/20-F, first tag with data
    after 2024; returns the currency too."""
    for tax in ("us-gaap", "ifrs-full"):
        for t in tags:
            units = f.get(tax, {}).get(t, {}).get("units", {})
            if not units:
                continue
            cur = "USD" if "USD" in units else next(iter(units))
            out = {}
            for u in units[cur]:
                if u.get("form") not in ("10-K", "20-F"):
                    continue
                if flow:
                    if not u.get("start"):
                        continue
                    days = (dt.date.fromisoformat(u["end"])
                            - dt.date.fromisoformat(u["start"])).days
                    if not 350 <= days <= 380:
                        continue
                elif u.get("start"):
                    continue
                out.setdefault(int(u["end"][:4]), u["val"] / 1e9)
            if out and max(out) >= 2025:
                return out, cur
    return {}, "USD"


def op_income(name: str, f: dict) -> dict:
    oi, _ = annual(f, ["OperatingIncomeLoss"])
    if oi:
        return oi
    # KLA stopped tagging operating income: revenue less cost of revenue,
    # R&D and SG&A
    rev, _ = annual(f, REV)
    parts = [annual(f, [t])[0] for t in ("CostOfRevenue",
             "ResearchAndDevelopmentExpense",
             "SellingGeneralAndAdministrativeExpense")]
    return {y: rev[y] - sum(p[y] for p in parts)
            for y in rev if all(y in p for p in parts)}


def fx(name: str, cur: str, y: int) -> float:
    return EURUSD[y] if cur == "EUR" else 1.0


def build_equipment() -> None:
    rows, roce = [], {"oi": 0.0, "ce": 0.0, "parts": []}
    rev_by = {}
    for name, cik in EQUIP.items():
        f = facts(cik)
        rev, cur = annual(f, REV)
        for y, v in sorted(rev.items()):
            if y >= 2020:
                rows.append((name, y, round(v * fx(name, cur, y), 2),
                             "reported", f"FY ends {FY_END[name]}"
                             + ("; EUR at ECB annual average" if cur == "EUR"
                                else "")))
        rev_by[name] = {y: v * fx(name, cur, y) for y, v in rev.items()
                        if y >= 2020}
        for (co, y), (v, note) in EXTRA_REV.items():
            if co == name and y not in rev:
                rows.append((name, y, v, "reported", note))
        # ROCE on the latest annual report
        oi = op_income(name, f)
        assets, _ = annual(f, ["Assets"], flow=False)
        cl, _ = annual(f, ["LiabilitiesCurrent"], flow=False)
        y = max(set(oi) & set(assets) & set(cl))
        r = fx(name, cur, y)
        roce["oi"] += oi[y] * r
        roce["ce"] += (assets[y] - cl[y]) * r
        roce["parts"].append(f"{name} {oi[y] / (assets[y] - cl[y]) * 100:.0f}"
                             f" (FY{y})")
    pd.DataFrame(rows, columns=["company", "year", "revenue_b", "source_type",
                                "note"]).to_csv(PROC / "equipment_vendors.csv",
                                                index=False)
    tot = {y: sum(rev_by[c][y] for c in EQUIP) for y in (2022, 2025)}
    growth = ((tot[2025] / tot[2022]) ** (1 / 3) - 1) * 100
    pct = roce["oi"] / roce["ce"] * 100
    print(f"Equipment ROCE {pct:.1f}% ({'; '.join(roce['parts'])}), "
          f"growth {growth:.1f}%")

    rl = pd.read_csv(PROC / "roce_by_layer.csv")
    rl = rl[rl["layer"] != "Chip equipment"]
    rl["order"] = range(2, len(rl) + 2)
    new = {"layer": "Chip equipment", "order": 1, "roce_pct": round(pct, 1),
           "growth_pct": round(growth), "players": "ASML, Applied Materials, "
           "Lam Research, KLA", "source_type": "computed",
           "note": " / ".join(roce["parts"]) + "; oligopoly suppliers to "
           "every fab; Tokyo Electron excluded (no SEC filings)",
           "growth_basis": "3-yr revenue CAGR 2022-2025 (fiscal years; ASML "
           "converted to USD)"}
    rl = pd.concat([pd.DataFrame([new]), rl]).sort_values("order")
    rl.to_csv(PROC / "roce_by_layer.csv", index=False)


def build_power() -> None:
    rows = []
    for name, cik in POWER.items():
        rev, _ = annual(facts(cik), REV)
        rows += [(name, y, round(v, 2), "reported", "10-K")
                 for y, v in sorted(rev.items()) if y >= 2020]
        rows += [(co, y, v, "guidance", note)
                 for (co, y), (v, note) in POWER_GUIDE.items() if co == name]
    pd.DataFrame(rows, columns=["company", "year", "revenue_b", "source_type",
                                "note"]).to_csv(PROC / "power_suppliers.csv",
                                                index=False)


def build_corning() -> None:
    nv = pd.read_csv(PROC / "networking_vendors.csv")
    nv = nv[nv["company"] != "Corning Optical"]
    add = pd.DataFrame([("Corning Optical", y, round(v / 1000, 2), "reported",
                         "Optical Communications segment (10-K)" if y == 2021
                         else "") for y, v in CORNING_OC.items()],
                       columns=nv.columns)
    pd.concat([nv, add]).to_csv(PROC / "networking_vendors.csv", index=False)


if __name__ == "__main__":
    build_equipment()
    build_power()
    build_corning()
    for f in ("equipment_vendors.csv", "power_suppliers.csv"):
        print(pd.read_csv(PROC / f).pivot(index="year", columns="company",
                                          values="revenue_b").to_string())
